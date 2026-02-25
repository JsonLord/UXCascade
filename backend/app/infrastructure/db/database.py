from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)

from app.core.config import settings

DATABASE_URL: str = settings.DATABASE_URL

engine: AsyncEngine = create_async_engine(
  DATABASE_URL,
  pool_pre_ping=True,
  pool_size=5,
  max_overflow=10,
)

async_session = async_sessionmaker(
  bind=engine,
  expire_on_commit=False,
  class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
  async with async_session() as session:
    yield session


async def check_db_connection() -> None:
  async with engine.connect() as connection:
    await connection.execute(text("SELECT 1"))
