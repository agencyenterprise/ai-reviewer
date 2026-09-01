from decimal import Decimal

import pytest

from lib.config.env import config
from lib.services.workflow_cost import catalog


def _record(name: str, *, pattern: str | None = None, **overrides) -> dict:
    record = {
        "modelName": name,
        "matchPattern": pattern if pattern is not None else f"(?i)^{name}$",
        "prices": {"input": {"price": 2e-06}, "output": {"price": 1.2e-05}},
    }
    record.update(overrides)
    return record


@pytest.fixture(autouse=True)
def _clear_cache(monkeypatch):
    """Every test starts with an unloaded catalog and Langfuse configured."""
    monkeypatch.setattr(catalog, "_CACHE", None)
    monkeypatch.setattr(config, "LANGFUSE_HOST", "https://langfuse.example")
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", "sk")
    yield
    monkeypatch.setattr(catalog, "_CACHE", None)


def _stub_fetch(monkeypatch, records: list, calls: list | None = None) -> None:
    async def _fake_fetch() -> list:
        if calls is not None:
            calls.append(1)
        return records

    monkeypatch.setattr(catalog, "_fetch_all_records", _fake_fetch)


def _stub_failing_fetch(monkeypatch, calls: list | None = None) -> None:
    async def _fake_fetch() -> list:
        if calls is not None:
            calls.append(1)
        raise RuntimeError("langfuse is down")

    monkeypatch.setattr(catalog, "_fetch_all_records", _fake_fetch)


class TestParsing:
    def test_unrecognised_fields_do_not_discard_a_record(self):
        """The regression guard: an unknown `pricingTiers` shape cost us the catalog."""
        record = _record(
            "gpt-5.6-terra",
            pricingTiers=[{"conditions": [{"key": "speed", "operator": "in"}]}],
            somethingLangfuseAddedLater={"nested": ["shapes"]},
        )
        entry = catalog._parse_record(record)
        assert entry is not None
        _, model = entry
        assert model.model_name == "gpt-5.6-terra"
        assert model.prices["input"] == Decimal("2e-06")

    def test_one_bad_record_does_not_take_the_others_with_it(self):
        records = [
            _record("good-one"),
            _record("bad-regex", pattern="^(unclosed"),
            {"modelName": "no-pattern", "prices": {"input": {"price": 1e-06}}},
            {"matchPattern": "^no-name$", "prices": {"input": {"price": 1e-06}}},
            _record("no-prices", prices={}),
            "not-even-a-dict",
            _record("good-two"),
        ]
        entries = catalog._compile(records)
        assert [model.model_name for _, model in entries] == ["good-one", "good-two"]

    def test_unparseable_price_drops_only_that_usage_type(self):
        record = _record(
            "half-priced",
            prices={"input": {"price": 2e-06}, "output": {"price": "not-a-number"}},
        )
        entry = catalog._parse_record(record)
        assert entry is not None
        _, model = entry
        assert model.prices == {"input": Decimal("2e-06")}

    @pytest.mark.parametrize(
        "bad_price", [float("nan"), float("inf"), "NaN", "Infinity"]
    )
    def test_non_finite_prices_are_dropped(self, bad_price):
        """`Decimal` takes NaN/Infinity, and json.loads parses the bare literals.

        A non-finite rate would poison every total it touches and serialize as
        invalid JSON, breaking the response rather than just this model's cost.
        """
        record = _record(
            "poisoned",
            prices={"input": {"price": 2e-06}, "output": {"price": bad_price}},
        )
        entry = catalog._parse_record(record)
        assert entry is not None
        _, model = entry
        assert model.prices == {"input": Decimal("2e-06")}

    def test_a_model_priced_only_non_finitely_is_skipped(self):
        assert (
            catalog._parse_record(
                _record("all-nan", prices={"input": {"price": float("nan")}})
            )
            is None
        )


class TestCaching:
    @pytest.mark.asyncio
    async def test_catalog_is_cached_between_calls(self, monkeypatch):
        calls: list = []
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")], calls)

        assert len(await catalog.get_catalog()) == 1
        assert len(await catalog.get_catalog()) == 1
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_catalog_is_refetched_once_the_ttl_expires(self, monkeypatch):
        calls: list = []
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")], calls)
        now = 1000.0
        monkeypatch.setattr(catalog.time, "monotonic", lambda: now)

        await catalog.get_catalog()
        now += catalog._SUCCESS_TTL_SECONDS + 1
        await catalog.get_catalog()

        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_failed_fetch_is_retried_rather_than_disabling_cost(
        self, monkeypatch
    ):
        """The blackout bug: a single failure used to switch cost off for good."""
        calls: list = []
        _stub_failing_fetch(monkeypatch, calls)
        now = 1000.0
        monkeypatch.setattr(catalog.time, "monotonic", lambda: now)

        assert await catalog.get_catalog() == []

        # Still inside the cooldown: no second request.
        now += catalog._FAILURE_RETRY_SECONDS - 1
        assert await catalog.get_catalog() == []
        assert len(calls) == 1

        # Past it, and Langfuse is answering again.
        now += 2
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")])
        assert len(await catalog.get_catalog()) == 1

    @pytest.mark.asyncio
    async def test_a_failed_refresh_keeps_serving_the_last_good_prices(
        self, monkeypatch
    ):
        """Losing Langfuse for a moment must not blank out cost we already have."""
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")])
        now = 1000.0
        monkeypatch.setattr(catalog.time, "monotonic", lambda: now)
        assert len(await catalog.get_catalog()) == 1

        now += catalog._SUCCESS_TTL_SECONDS + 1
        _stub_failing_fetch(monkeypatch)
        entries = await catalog.get_catalog()
        assert [model.model_name for _, model in entries] == ["gpt-5.6-terra"]
        assert catalog._CACHE is not None
        assert catalog._CACHE.expires_at == now + catalog._FAILURE_RETRY_SECONDS

    @pytest.mark.asyncio
    async def test_an_empty_successful_response_replaces_the_old_catalog(
        self, monkeypatch
    ):
        """Unlike a failure, an empty answer is Langfuse telling us something."""
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")])
        now = 1000.0
        monkeypatch.setattr(catalog.time, "monotonic", lambda: now)
        assert len(await catalog.get_catalog()) == 1

        now += catalog._SUCCESS_TTL_SECONDS + 1
        _stub_fetch(monkeypatch, [])
        assert await catalog.get_catalog() == []

    @pytest.mark.asyncio
    async def test_a_wholly_unreadable_response_counts_as_a_failure(self, monkeypatch):
        """Records that all fail to parse mean a schema change, not an empty catalog."""
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")])
        now = 1000.0
        monkeypatch.setattr(catalog.time, "monotonic", lambda: now)
        assert len(await catalog.get_catalog()) == 1

        now += catalog._SUCCESS_TTL_SECONDS + 1
        _stub_fetch(monkeypatch, [{"everythingRenamed": True} for _ in range(50)])
        entries = await catalog.get_catalog()

        assert [model.model_name for _, model in entries] == ["gpt-5.6-terra"]
        assert catalog._CACHE is not None
        assert catalog._CACHE.expires_at == now + catalog._FAILURE_RETRY_SECONDS

    @pytest.mark.asyncio
    async def test_a_first_load_that_reads_nothing_retries_soon(self, monkeypatch):
        now = 1000.0
        monkeypatch.setattr(catalog.time, "monotonic", lambda: now)
        _stub_fetch(monkeypatch, [{"everythingRenamed": True}])

        assert await catalog.get_catalog() == []
        assert catalog._CACHE is not None
        assert catalog._CACHE.expires_at == now + catalog._FAILURE_RETRY_SECONDS

    @pytest.mark.asyncio
    async def test_unconfigured_langfuse_never_calls_out(self, monkeypatch):
        monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", None)
        calls: list = []
        _stub_fetch(monkeypatch, [_record("gpt-5.6-terra")], calls)

        assert await catalog.get_catalog() == []
        assert calls == []
        assert catalog._CACHE is not None
        assert catalog._CACHE.expires_at == float("inf")


class TestFetching:
    @pytest.mark.asyncio
    async def test_pages_until_every_record_is_in_hand(self, monkeypatch):
        pages = {
            1: ([_record(f"model-{i}") for i in range(100)], 150),
            2: ([_record(f"model-{i}") for i in range(100, 150)], 150),
        }

        async def _fake_page(client, page: int):
            return pages[page]

        monkeypatch.setattr(catalog, "_fetch_page", _fake_page)
        records = await catalog._fetch_all_records()
        assert len(records) == 150

    @pytest.mark.asyncio
    async def test_stops_on_an_empty_page_even_if_the_total_disagrees(
        self, monkeypatch
    ):
        """A totalItems the pages never reach must not spin forever."""

        async def _fake_page(client, page: int):
            return ([_record("only-model")], 9999) if page == 1 else ([], 9999)

        monkeypatch.setattr(catalog, "_fetch_page", _fake_page)
        records = await catalog._fetch_all_records()
        assert len(records) == 1
