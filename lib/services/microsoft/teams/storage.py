"""The Agents SDK's storage, shared across workers.

The SDK keeps an in-progress sign-in here: the flow's state, and the question parked
to be replayed once a token arrives. Both are written by the request that posts the
Sign in card and read by the later ``signin/*`` invoke -- a *different request*, which
in production usually lands on a *different process*, since Uvicorn is launched with
``--workers 4``. The SDK's own ``MemoryStorage`` cannot span that, so first-time
sign-in would fail about three times in four, and only once deployed: a single-process
dev server never shows it.

One short transaction per operation, no locks. Concurrent writes to the same key are
serialised by the primary key via ``ON CONFLICT DO UPDATE``. Volume is a few rows per
sign-in, so there is no sweeper -- the SDK expires a flow after about a minute and
deletes its own entries as the flow completes.

No tokens pass through here. The refresh token stays in the Bot Framework token
service; what is stored is flow bookkeeping and the pending activity.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from microsoft_agents.hosting.core import Storage
from microsoft_agents.hosting.core.storage import AsyncStorageBase, StoreItem
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import col

from lib.config.database import AsyncSessionLocal
from lib.models.microsoft_teams_signin_state import MicrosoftTeamsSignInState

logger = logging.getLogger(__name__)


class PostgresSignInStorage(AsyncStorageBase):
    """Sign-in state in Postgres rather than in one worker's memory.

    ``AsyncStorageBase`` implements the bulk ``read``/``write``/``delete`` in terms of
    the three single-item hooks below, so only those are needed.
    """

    async def _read_item(
        self, key: str, *, target_cls: type[Any], **kwargs: Any
    ) -> tuple[str | None, Any | None]:
        async with AsyncSessionLocal() as session:
            row = (
                await session.execute(
                    select(MicrosoftTeamsSignInState).where(
                        col(MicrosoftTeamsSignInState.key) == key
                    )
                )
            ).scalar_one_or_none()

        if row is None:
            return None, None
        return key, target_cls.from_json_to_store_item(row.value)

    async def _write_item(self, key: str, value: StoreItem) -> None:
        payload = value.store_item_to_json()
        now = datetime.now(timezone.utc)
        statement = (
            pg_insert(MicrosoftTeamsSignInState)
            .values(key=key, value=payload, updated_at=now)
            # A retried turn rewrites the same key rather than colliding with itself.
            .on_conflict_do_update(
                index_elements=[MicrosoftTeamsSignInState.key],
                set_={"value": payload, "updated_at": now},
            )
        )
        async with AsyncSessionLocal() as session:
            await session.execute(statement)
            await session.commit()

    async def _delete_item(self, key: str) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(MicrosoftTeamsSignInState).where(
                    col(MicrosoftTeamsSignInState.key) == key
                )
            )
            await session.commit()


def sign_in_storage() -> Storage:
    """The storage the bot's ``Authorization`` should use.

    A function rather than a module-level instance so importing this module does not
    imply a database connection, which matters for tests and for a deployment that
    does not run the bot.
    """

    return PostgresSignInStorage()
