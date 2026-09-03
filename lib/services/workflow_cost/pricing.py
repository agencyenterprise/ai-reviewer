import logging
import re
from decimal import Decimal
from typing import Iterable, Optional

from lib.services.workflow_cost.breakdown import (
    CostBreakdown,
    ModelCostBreakdown,
    UsageRecord,
)
from lib.services.workflow_cost.catalog import CatalogEntry, ModelPricing, get_catalog

logger = logging.getLogger(__name__)


# OpenAI reports the deployed snapshot in response metadata, not the alias that
# was requested: asking for `gpt-5.6-terra` comes back as
# `gpt-5.6-terra-2026-07-09-global-aaif`. Langfuse's managed price entries match
# the bare alias only, so the snapshot name prices nothing. Anchoring on the date
# keeps a genuinely different variant (`gpt-5.6-terra-mini`) from being priced
# as the base model.
_SNAPSHOT_SUFFIX = re.compile(r"-\d{4}-\d{2}-\d{2}(-.*)?$")


def _first_match(name: str, models: list[CatalogEntry]) -> Optional[ModelPricing]:
    for pattern, model in models:
        if pattern.fullmatch(name):
            return model
    return None


def _match_model(name: str, models: list[CatalogEntry]) -> Optional[ModelPricing]:
    """Price `name` directly, or by its alias once a dated snapshot suffix is removed."""
    model = _first_match(name, models)
    if model is not None:
        return model

    alias = _SNAPSHOT_SUFFIX.sub("", name, count=1)
    if alias == name:
        return None
    model = _first_match(alias, models)
    if model is not None:
        logger.debug("priced snapshot %r as its alias %r", name, alias)
    return model


def _rate(prices: dict[str, Decimal], *keys: str) -> Decimal:
    for k in keys:
        price = prices.get(k)
        if price is not None:
            return price
    return Decimal("0")


def _cost_for_record(
    record: UsageRecord, models: list[CatalogEntry]
) -> ModelCostBreakdown | None:
    model = _match_model(record.model_name, models)
    if model is None:
        logger.warning(
            "Langfuse has no pricing for model %r; skipping cost calc",
            record.model_name,
        )
        return None

    prices = model.prices
    input_rate = _rate(prices, "input")
    output_rate = _rate(prices, "output")
    # Fall back to input rate when no cache_read price is published.
    cache_read_rate = _rate(prices, "input_cache_read", "input_cached_tokens", "input")

    input_cost = input_rate * record.input_tokens
    output_cost = output_rate * record.output_tokens
    cache_read_cost = cache_read_rate * record.cache_read_tokens

    return ModelCostBreakdown(
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        cache_read_tokens=record.cache_read_tokens,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        cache_read_cost_usd=cache_read_cost,
        total_cost_usd=input_cost + output_cost + cache_read_cost,
    )


def _accumulate(target: ModelCostBreakdown, addition: ModelCostBreakdown) -> None:
    target.input_tokens += addition.input_tokens
    target.output_tokens += addition.output_tokens
    target.cache_read_tokens += addition.cache_read_tokens
    target.input_cost_usd += addition.input_cost_usd
    target.output_cost_usd += addition.output_cost_usd
    target.cache_read_cost_usd += addition.cache_read_cost_usd
    target.total_cost_usd += addition.total_cost_usd


async def compute_cost(records: Iterable[UsageRecord]) -> CostBreakdown | None:
    """Aggregate UsageRecords into a CostBreakdown using Langfuse pricing.

    Returns None when no records can be priced (no input or all models unknown).
    """
    records_list = list(records)
    if not records_list:
        return None

    models = await get_catalog()
    if not models:
        return None

    breakdown = CostBreakdown()
    has_any = False
    for record in records_list:
        per_model = _cost_for_record(record, models)
        if per_model is None:
            continue
        has_any = True

        bucket = breakdown.by_model.setdefault(record.model_name, ModelCostBreakdown())
        _accumulate(bucket, per_model)
        bucket.request_count += 1

        breakdown.total_input_tokens += per_model.input_tokens
        breakdown.total_output_tokens += per_model.output_tokens
        breakdown.total_cache_read_tokens += per_model.cache_read_tokens
        breakdown.input_cost_usd += per_model.input_cost_usd
        breakdown.output_cost_usd += per_model.output_cost_usd
        breakdown.cache_read_cost_usd += per_model.cache_read_cost_usd
        breakdown.total_cost_usd += per_model.total_cost_usd
        breakdown.request_count += 1

    return breakdown if has_any else None
