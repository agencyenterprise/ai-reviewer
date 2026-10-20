"""Integration tests for PostgresKeyValueStore.

Hits the real Postgres used by the rest of the test suite (same DATABASE_URL).
Verifies the FastMCP AsyncKeyValue contract: round-trip, TTL expiry + lazy
cleanup, batch ops, collection isolation, and upsert-overwrites semantics.
Expired rows are written with an ``expires_at`` in the past rather than by
sleeping past a short TTL, so the expiry tests don't depend on timing.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from key_value.aio.errors import DecryptionError
from key_value.aio.protocols.key_value import AsyncKeyValue
from sqlalchemy import delete, select
from sqlmodel import col

from lib.api.mcp.auth import _build_client_storage
from lib.api.mcp.postgres_kv_store import PostgresKeyValueStore
from lib.config.database import get_async_db_session
from lib.models.mcp_oauth_kv import MCPOAuthKV


@pytest_asyncio.fixture
async def collection():
    """Unique collection per test so parallel runs don't interfere."""
    name = f"test-{uuid.uuid4().hex[:12]}"
    yield name

    async with get_async_db_session() as session:
        await session.execute(
            delete(MCPOAuthKV).where(col(MCPOAuthKV.collection) == name)
        )
        await session.commit()


@pytest_asyncio.fixture
async def store():
    return PostgresKeyValueStore()


async def _insert_expired(collection: str, key: str, value: dict) -> None:
    """Write a row whose ``expires_at`` has already passed."""
    now = datetime.now(UTC)
    async with get_async_db_session() as session:
        session.add(
            MCPOAuthKV(
                collection=collection,
                key=key,
                value=value,
                created_at=now - timedelta(minutes=10),
                expires_at=now - timedelta(minutes=5),
            )
        )
        await session.commit()


async def _stored_row(collection: str, key: str) -> MCPOAuthKV | None:
    async with get_async_db_session() as session:
        return (
            await session.execute(
                select(MCPOAuthKV).where(
                    col(MCPOAuthKV.collection) == collection,
                    col(MCPOAuthKV.key) == key,
                )
            )
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_round_trip(store, collection):
    await store.put(
        "k1", {"client_id": "abc", "scopes": ["a", "b"]}, collection=collection
    )
    got = await store.get("k1", collection=collection)
    assert got == {"client_id": "abc", "scopes": ["a", "b"]}


@pytest.mark.asyncio
async def test_get_missing_returns_none(store, collection):
    assert await store.get("nope", collection=collection) is None


@pytest.mark.asyncio
async def test_delete_returns_true_only_when_row_existed(store, collection):
    await store.put("k", {"v": 1}, collection=collection)
    assert await store.delete("k", collection=collection) is True
    assert await store.delete("k", collection=collection) is False
    assert await store.get("k", collection=collection) is None


@pytest.mark.asyncio
async def test_upsert_overwrites_value_and_ttl(store, collection):
    await store.put("k", {"v": 1}, collection=collection, ttl=60)
    await store.put("k", {"v": 2}, collection=collection)  # no TTL this time
    value, ttl = await store.ttl("k", collection=collection)
    assert value == {"v": 2}
    assert ttl is None


@pytest.mark.asyncio
async def test_put_with_ttl_stores_its_expiry(store, collection):
    await store.put("k", {"v": 1}, collection=collection, ttl=60)

    value, ttl = await store.ttl("k", collection=collection)
    assert value == {"v": 1}
    assert ttl is not None and 50 < ttl <= 60


@pytest.mark.asyncio
async def test_ttl_expiry_returns_none_and_cleans_up(store, collection):
    await _insert_expired(collection, "k", {"v": "expired"})

    # Expired read returns None and lazily deletes the row.
    assert await store.get("k", collection=collection) is None
    assert await _stored_row(collection, "k") is None


@pytest.mark.asyncio
async def test_ttl_of_expired_entry_is_none_and_cleans_up(store, collection):
    await _insert_expired(collection, "k", {"v": "expired"})

    assert await store.ttl("k", collection=collection) == (None, None)
    assert await _stored_row(collection, "k") is None


@pytest.mark.asyncio
async def test_put_replaces_an_expired_entry(store, collection):
    """A client re-registering under an expired key gets a live entry back."""
    await _insert_expired(collection, "k", {"v": "old"})

    await store.put("k", {"v": "new"}, collection=collection)

    assert await store.ttl("k", collection=collection) == ({"v": "new"}, None)


@pytest.mark.asyncio
async def test_collection_isolation(store):
    col_a = f"a-{uuid.uuid4().hex[:8]}"
    col_b = f"b-{uuid.uuid4().hex[:8]}"
    try:
        await store.put("same-key", {"v": "A"}, collection=col_a)
        await store.put("same-key", {"v": "B"}, collection=col_b)

        assert await store.get("same-key", collection=col_a) == {"v": "A"}
        assert await store.get("same-key", collection=col_b) == {"v": "B"}
    finally:
        async with get_async_db_session() as session:
            await session.execute(
                delete(MCPOAuthKV).where(col(MCPOAuthKV.collection).in_([col_a, col_b]))
            )
            await session.commit()


@pytest.mark.asyncio
async def test_batch_put_get_delete(store, collection):
    keys = ["a", "b", "c"]
    values = [{"v": 1}, {"v": 2}, {"v": 3}]

    await store.put_many(keys, values, collection=collection)

    got = await store.get_many(keys + ["missing"], collection=collection)
    assert got == [{"v": 1}, {"v": 2}, {"v": 3}, None]

    deleted = await store.delete_many(["a", "c", "missing"], collection=collection)
    assert deleted == 2

    got = await store.get_many(keys, collection=collection)
    assert got == [None, {"v": 2}, None]


@pytest.mark.asyncio
async def test_batch_put_with_ttl_stores_expiry_on_every_row(store, collection):
    await store.put_many(
        ["a", "b"], [{"v": 1}, {"v": 2}], collection=collection, ttl=60
    )

    entries = await store.ttl_many(["a", "b"], collection=collection)
    assert [value for value, _ in entries] == [{"v": 1}, {"v": 2}]
    assert all(ttl is not None and 50 < ttl <= 60 for _, ttl in entries)


@pytest.mark.asyncio
async def test_batch_get_skips_expired_rows_and_deletes_only_those(store, collection):
    await store.put("live", {"v": "live"}, collection=collection)
    await _insert_expired(collection, "stale", {"v": "stale"})

    got = await store.get_many(["stale", "live", "missing"], collection=collection)

    assert got == [None, {"v": "live"}, None]
    assert await _stored_row(collection, "stale") is None
    assert await _stored_row(collection, "live") is not None


@pytest.mark.asyncio
async def test_batch_ops_with_no_keys_are_no_ops(store, collection):
    await store.put("k", {"v": 1}, collection=collection)

    await store.put_many([], [], collection=collection)
    assert await store.get_many([], collection=collection) == []
    assert await store.delete_many([], collection=collection) == 0

    assert await store.get("k", collection=collection) == {"v": 1}


@pytest.mark.asyncio
async def test_cull_removes_expired_rows(store, collection):
    await store.put("fresh", {"v": 1}, collection=collection, ttl=60)
    await store.put("forever", {"v": 2}, collection=collection)
    await _insert_expired(collection, "stale", {"v": 3})

    await store.cull()

    assert await store.get("fresh", collection=collection) == {"v": 1}
    assert await store.get("forever", collection=collection) == {"v": 2}
    # Read the table directly: a store read would delete the row itself.
    assert await _stored_row(collection, "stale") is None


# --- The encrypted client storage the MCP OAuth providers use ---


def _client_storage(auth_secret: str) -> AsyncKeyValue:
    mock_config = MagicMock()
    mock_config.AUTH_SECRET = auth_secret
    with patch("lib.api.mcp.auth.config", mock_config):
        return _build_client_storage()


@pytest.mark.asyncio
async def test_client_storage_encrypts_values_at_rest(collection):
    storage = _client_storage("test-auth-secret-for-kdf")

    await storage.put("client", {"client_secret": "s3cret"}, collection=collection)

    assert await storage.get("client", collection=collection) == {
        "client_secret": "s3cret"
    }
    row = await _stored_row(collection, "client")
    assert row is not None
    assert "s3cret" not in str(row.value)


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    raises=DecryptionError,
    reason=(
        "Bug: _build_client_storage keeps FernetEncryptionWrapper's default "
        "raise_on_decryption_error=True, so after AUTH_SECRET rotates every "
        "stored registration raises DecryptionError instead of reading as a "
        "miss and sending the client through re-registration, as FastMCP's "
        "own default storage does."
    ),
)
async def test_client_storage_reads_entries_from_a_rotated_secret_as_missing(
    collection,
):
    old = _client_storage("test-auth-secret-before-rotation")
    new = _client_storage("test-auth-secret-after-rotation")
    await old.put("client", {"client_id": "abc"}, collection=collection)

    assert await new.get("client", collection=collection) is None
