from __future__ import annotations

import os

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = os.path.dirname(os.path.abspath(__file__))


def _normalize_db_url(url: str) -> str:
  """Normalizes the URL to the asyncpg or sqlite driver prefix."""
  if url.startswith("sqlite+aiosqlite://"):
    return url
  if url.startswith("sqlite://"):
    return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
  if url.startswith("postgresql+asyncpg://"):
    return url
  if url.startswith("postgresql://"):
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)
  if url.startswith("postgres://"):
    return url.replace("postgres://", "postgresql+asyncpg://", 1)
  return url


class Settings(BaseSettings):
  # ── App ──────────────────────────────────────────────────────────────────
  ENV: str = "dev"

  # ── Database ─────────────────────────────────────────────────────────────
  DATABASE_URL: str = ""
  DB_HOST: str = "localhost"
  DB_PORT: int = 5432
  DB_USER: str = "postgres"
  DB_PASSWORD: str = "postgres"
  DB_NAME: str = "uxcascade"

  # ── LLM Configuration (Supports Anthropic and OpenAI-Compatible APIs) ─────
  ANTHROPIC_API_KEY: str = Field(default="")
  OPENAI_API_KEY: str = Field(default="")
  OPENAI_BASE_URL: str = Field(default="")
  OPENAI_MODEL_NAME: str = Field(default="gpt-4o")

  # ── Evidence / Screenshot Storage ─────────────────────────────────────────
  STORAGE_BACKEND: str = "local"  # "local" or "s3"
  MINIO_ENDPOINT: str = "http://localhost:9000"
  MINIO_ACCESS_KEY: str = "minioadmin"
  MINIO_SECRET_KEY: str = "minioadmin"
  MINIO_BUCKET: str = "screenshots"
  MINIO_PUBLIC_URL: str = "http://localhost:9000"

  # ── Concurrency & Browser-use ─────────────────────────────────────────────
  SIMULATION_MAX_CONCURRENCY: int = 1
  BROWSER_HEADLESS: bool = True

  model_config = SettingsConfigDict(
    env_file=f"{_HERE}/../../.env",
    env_file_encoding="utf-8",
    extra="ignore",
  )

  @model_validator(mode="after")
  def _resolve_database_url(self) -> Settings:
    if self.DATABASE_URL:
      self.DATABASE_URL = _normalize_db_url(self.DATABASE_URL)
    else:
      self.DATABASE_URL = "sqlite+aiosqlite:////app/uxcascade.db"
    return self


settings = Settings()
