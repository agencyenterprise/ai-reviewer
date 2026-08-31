"""The Langfuse model price catalog, fetched and cached for cost calculation.

Read straight off the REST endpoint rather than through the Langfuse SDK's typed
client. The SDK validates a whole page into `PaginatedModels`, so one record the
installed SDK version cannot parse discards every model on that page -- which is
exactly how cost silently vanished from the UI when Langfuse Cloud added
`pricing_tiers` fields that SDK 4.2.0 rejected. Parsing per record here means a
shape we do not recognise costs us that one model, not the catalog.
"""

import asyncio
import logging
import re
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from lib.config.env import config

logger = logging.getLogger(__name__)

_MODELS_PATH = "/api/public/models"
_PAGE_SIZE = 100
# The catalog gains entries as Langfuse adds models, so a long-lived process has
# to look again; without this a model published after boot is never priced.
_SUCCESS_TTL_SECONDS = 3600.0
# A failed fetch is cached only briefly. Caching it for the process lifetime is
# what turned one bad deploy-day response into days of missing cost.
_FAILURE_RETRY_SECONDS = 300.0
_FETCH_TIMEOUT_SECONDS = 5.0
# Backstop against a `meta.totalItems` that never lets the page loop finish.
_MAX_PAGES = 100


class ModelPricing(BaseModel):
    """One model's per-token rates, keyed by Langfuse's usage-type names."""

    model_name: str
    prices: dict[str, Decimal] = Field(default_factory=dict)


# One compiled match pattern paired with the rates it selects.
CatalogEntry = tuple[re.Pattern[str], ModelPricing]


class _CachedCatalog(BaseModel):
    """Compiled match patterns, and the monotonic deadline for refetching them."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entries: list[CatalogEntry] = Field(default_factory=list)
    expires_at: float

    def is_fresh(self) -> bool:
        return time.monotonic() < self.expires_at


_CACHE: Optional[_CachedCatalog] = None
_CACHE_LOCK = asyncio.Lock()


def _is_configured() -> bool:
    return all(
        [config.LANGFUSE_PUBLIC_KEY, config.LANGFUSE_SECRET_KEY, config.LANGFUSE_HOST]
    )


def _parse_prices(raw_prices: Any, model_name: str) -> dict[str, Decimal]:
    """Read `{usage_type: {"price": float}}`, dropping entries that aren't numbers."""
    if not isinstance(raw_prices, dict):
        return {}

    prices: dict[str, Decimal] = {}
    for usage_type, entry in raw_prices.items():
        price = entry.get("price") if isinstance(entry, dict) else None
        if price is None:
            continue
        try:
            rate = Decimal(str(price))
        except (InvalidOperation, ValueError):
            rate = None
        # `Decimal` happily accepts "NaN" and "Infinity", and json.loads parses
        # the bare NaN/Infinity literals, so a non-finite rate can reach us. It
        # would poison every total it touches and serialize as invalid JSON,
        # breaking the whole response rather than just this model's cost.
        if rate is None or not rate.is_finite():
            logger.warning(
                "skipping unusable Langfuse price %r for %s/%s",
                price,
                model_name,
                usage_type,
            )
            continue
        prices[str(usage_type)] = rate
    return prices


def _parse_record(record: Any) -> Optional[CatalogEntry]:
    """Compile one catalog record, or return None if it is unusable."""
    if not isinstance(record, dict):
        return None

    match_pattern = record.get("matchPattern")
    model_name = record.get("modelName")
    if not isinstance(match_pattern, str) or not isinstance(model_name, str):
        return None

    prices = _parse_prices(record.get("prices"), model_name)
    if not prices:
        # A model with no readable price cannot contribute to a cost, and keeping
        # it would only shadow a later pattern that can. Langfuse's oldest entries
        # (gpt-3.5-turbo, gemini-1.5-*) have an empty `prices` and only the
        # deprecated top-level `inputPrice`/`outputPrice`. Those are deliberately
        # not read: some of them are priced per CHARACTER, so treating them as
        # per-token rates would invent numbers rather than omit them.
        return None

    try:
        pattern = re.compile(match_pattern)
    except re.error as e:
        logger.warning(
            "skipping invalid Langfuse model pattern %r: %s", match_pattern, e
        )
        return None

    return pattern, ModelPricing(model_name=model_name, prices=prices)


async def _fetch_page(client: httpx.AsyncClient, page: int) -> tuple[list[Any], int]:
    """Return one page of raw records plus the catalog's reported total size."""
    response = await client.get(
        _MODELS_PATH, params={"page": page, "limit": _PAGE_SIZE}
    )
    response.raise_for_status()
    payload = response.json()
    records = payload.get("data") or []
    total_items = (payload.get("meta") or {}).get("totalItems") or 0
    return list(records), int(total_items)


async def _fetch_all_records() -> list[Any]:
    host = (config.LANGFUSE_HOST or "").rstrip("/")
    auth = (config.LANGFUSE_PUBLIC_KEY or "", config.LANGFUSE_SECRET_KEY or "")
    records: list[Any] = []

    async with httpx.AsyncClient(base_url=host, auth=auth) as client:
        for page in range(1, _MAX_PAGES + 1):
            page_records, total_items = await _fetch_page(client, page)
            records.extend(page_records)
            if not page_records or len(records) >= total_items:
                break

    return records


def _compile(records: list[Any]) -> list[CatalogEntry]:
    entries = [entry for entry in map(_parse_record, records) if entry is not None]
    skipped = len(records) - len(entries)
    if skipped:
        logger.warning(
            "skipped %d of %d Langfuse model records that could not be read",
            skipped,
            len(records),
        )
    logger.info("loaded %d model price entries from Langfuse", len(entries))
    return entries


async def _load(stale: Optional[_CachedCatalog]) -> _CachedCatalog:
    """Refetch the catalog, falling back to `stale` if the fetch fails.

    `stale` is the expired entry this load is replacing. Prices change rarely, so
    serving them past their deadline while Langfuse is unreachable beats dropping
    cost from every assessment for the length of the cooldown.
    """
    if not _is_configured():
        logger.info("Langfuse not configured; cost calculation disabled")
        return _CachedCatalog(entries=[], expires_at=float("inf"))

    try:
        records = await asyncio.wait_for(
            _fetch_all_records(), timeout=_FETCH_TIMEOUT_SECONDS
        )
    except Exception as e:
        kept = stale.entries if stale else []
        # Logged at error level because the only user-visible symptom is cost
        # quietly missing from every assessment.
        logger.error(
            "Failed to load Langfuse model pricing (%s: %s); "
            "%s until the next retry in %ds",
            type(e).__name__,
            e,
            (
                f"serving {len(kept)} stale price entries"
                if kept
                else "cost calculation is off"
            ),
            int(_FAILURE_RETRY_SECONDS),
        )
        return _CachedCatalog(
            entries=kept, expires_at=time.monotonic() + _FAILURE_RETRY_SECONDS
        )

    # An empty catalog here is a successful answer, not a failure, so it replaces
    # whatever we were holding.
    return _CachedCatalog(
        entries=_compile(records), expires_at=time.monotonic() + _SUCCESS_TTL_SECONDS
    )


async def get_catalog() -> list[CatalogEntry]:
    """The cached price catalog, refetched once its entry has gone stale."""
    global _CACHE
    cached = _CACHE
    if cached is not None and cached.is_fresh():
        return cached.entries

    async with _CACHE_LOCK:
        cached = _CACHE
        if cached is not None and cached.is_fresh():
            return cached.entries
        _CACHE = await _load(cached)
        return _CACHE.entries
