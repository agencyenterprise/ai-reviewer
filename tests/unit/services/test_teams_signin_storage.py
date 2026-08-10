"""Tests for the sign-in storage the Agents SDK writes through.

The bug this exists for is invisible on one machine. A sign-in spans two requests --
the message that posts the Sign in card, then the ``signin/*`` invoke that completes
it -- and production runs Uvicorn with ``--workers 4``. With the SDK's ``MemoryStorage``
the second request usually lands on a worker that has never heard of the flow, so the
parked question is lost and first-time sign-in fails perhaps three times in four. A
single-process dev server never shows it, and no test that shares a process would
either, which is why the property asserted here is *where* the state lives rather than
that a round trip works.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from microsoft_agents.hosting.core.storage import StoreItem

from lib.services.microsoft.teams import storage as signin_storage


class Item(StoreItem):
    """The shape the SDK stores: something that round-trips through JSON."""

    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    def store_item_to_json(self) -> dict[str, Any]:
        return self.value

    @staticmethod
    def from_json_to_store_item(json_data: Any) -> "Item":
        return Item(json_data)


def session_returning(row: Any) -> Any:
    """An async session whose one query yields ``row``."""

    result = MagicMock()
    result.scalar_one_or_none.return_value = row

    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


class TestWhereSignInStateLives:
    def test_it_is_not_the_sdk_memory_storage(self) -> None:
        """The whole point. In-process state cannot span four workers."""

        from microsoft_agents.hosting.core import MemoryStorage

        assert not isinstance(signin_storage.sign_in_storage(), MemoryStorage)

    def test_the_bot_actually_builds_with_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Asserted on the built object, not on source text: what matters is the
        storage the SDK ends up holding, since that is what spans the two requests."""

        from lib.config.env import config
        from lib.services.microsoft.teams import bot

        monkeypatch.setattr(config, "TEAMS_BOT_APP_ID", "11111111-2222-3333-4444-555555555555")
        monkeypatch.setattr(config, "TEAMS_BOT_APP_PASSWORD", "a-secret")
        monkeypatch.setattr(bot, "bot", bot._Bot())
        bot.bot._build()

        assert bot.bot._authorization is not None
        held = bot.bot._authorization._storage
        assert isinstance(held, signin_storage.PostgresSignInStorage), (
            f"the SDK is holding {type(held).__name__}, which cannot span workers"
        )


class TestReadingAndWriting:
    @pytest.mark.asyncio
    async def test_a_missing_key_reads_as_nothing(self) -> None:
        """A flow the SDK has not started yet, or one already completed."""

        with patch.object(
            signin_storage, "AsyncSessionLocal", lambda: session_returning(None)
        ):
            key, item = await signin_storage.PostgresSignInStorage()._read_item(
                "conv/user", target_cls=Item
            )

        assert (key, item) == (None, None)

    @pytest.mark.asyncio
    async def test_a_stored_value_comes_back_through_the_target_class(self) -> None:
        row = MagicMock(value={"parked": "the question"})
        with patch.object(
            signin_storage, "AsyncSessionLocal", lambda: session_returning(row)
        ):
            key, item = await signin_storage.PostgresSignInStorage()._read_item(
                "conv/user", target_cls=Item
            )

        assert key == "conv/user"
        assert item is not None and item.value == {"parked": "the question"}

    @pytest.mark.asyncio
    async def test_writing_upserts_so_a_retried_turn_does_not_collide(self) -> None:
        """The Connector retries, and a retry must rewrite rather than fail."""

        session = session_returning(None)
        with patch.object(signin_storage, "AsyncSessionLocal", lambda: session):
            await signin_storage.PostgresSignInStorage()._write_item(
                "conv/user", Item({"parked": "the question"})
            )

        session.execute.assert_awaited_once()
        session.commit.assert_awaited_once()
        statement = str(session.execute.await_args[0][0]).lower()
        assert "on conflict" in statement, "a retried turn would otherwise raise"

    @pytest.mark.asyncio
    async def test_writing_stamps_a_time_for_sweeping_abandoned_flows(self) -> None:
        session = session_returning(None)
        with patch.object(signin_storage, "AsyncSessionLocal", lambda: session):
            await signin_storage.PostgresSignInStorage()._write_item(
                "conv/user", Item({"parked": "q"})
            )

        values = session.execute.await_args[0][0].compile().params
        assert isinstance(values["updated_at"], datetime)

    @pytest.mark.asyncio
    async def test_deleting_a_completed_flow_commits(self) -> None:
        session = session_returning(None)
        with patch.object(signin_storage, "AsyncSessionLocal", lambda: session):
            await signin_storage.PostgresSignInStorage()._delete_item("conv/user")

        assert "delete" in str(session.execute.await_args[0][0]).lower()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_the_bulk_operations_come_from_the_sdk_base(self) -> None:
        """``AsyncStorageBase`` builds read/write/delete from the single-item hooks."""

        store = signin_storage.PostgresSignInStorage()
        row = MagicMock(value={"a": 1})
        with patch.object(
            signin_storage, "AsyncSessionLocal", lambda: session_returning(row)
        ):
            found = await store.read(["one", "two"], target_cls=Item)

        assert set(found) == {"one", "two"}
