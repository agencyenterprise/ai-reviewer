import uuid
from datetime import datetime

from sqlalchemy import select
from sqlmodel import col

from lib.config.database import get_async_db_session
from lib.models.app_config import AppConfig


async def get_config(key: str) -> str | None:
    """Return the value for a config key, or None if not set."""
    async with get_async_db_session() as session:
        stmt = select(AppConfig).where(col(AppConfig.key) == key)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        return row.value if row else None


async def get_all_configs() -> list[AppConfig]:
    """Return all config rows, ordered by key."""
    async with get_async_db_session() as session:
        stmt = select(AppConfig).order_by(col(AppConfig.key))
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def upsert_config(
    key: str, value: str, description: str | None, user_id: uuid.UUID
) -> AppConfig:
    """Create or update a config row. Returns the saved row."""
    async with get_async_db_session() as session:
        stmt = select(AppConfig).where(col(AppConfig.key) == key)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.value = value
            if description is not None:
                row.description = description
            row.updated_by = user_id
            row.updated_at = datetime.utcnow()
        else:
            row = AppConfig(
                key=key,
                value=value,
                description=description or "",
                updated_by=user_id,
            )
            session.add(row)

        await session.commit()
        await session.refresh(row)
        return row


async def delete_config(key: str) -> bool:
    """Delete a config row. Returns True if the row existed."""
    async with get_async_db_session() as session:
        stmt = select(AppConfig).where(col(AppConfig.key) == key)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await session.delete(row)
        await session.commit()
        return True
