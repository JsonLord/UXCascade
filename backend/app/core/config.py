from __future__ import annotations

import os

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = os.path.dirname(os.path.abspath(__file__))


def _normalize_db_url(url: str) -> str:
  """Normalizes the URL to the asyncpg driver prefix."""
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
  # DATABASE_URL takes precedence if set; otherwise constructed from DB_* fields.
  # Docker: DATABASE_URL=postgresql://postgres:postgres@db:5432/uxcascade
  # Local: specify DB_HOST etc. individually in .env
  DATABASE_URL: str = ""
  DB_HOST: str = "localhost"
  DB_PORT: int = 5432
  DB_USER: str = "postgres"
  DB_PASSWORD: str = "postgres"
  DB_NAME: str = "uxcascade"

  # ── Anthropic ─────────────────────────────────────────────────────────────
  ANTHROPIC_API_KEY: str = Field(default="")

  # ── MinIO / Object Storage ────────────────────────────────────────────────
  MINIO_ENDPOINT: str = "http://localhost:9000"
  MINIO_ACCESS_KEY: str = "minioadmin"
  MINIO_SECRET_KEY: str = "minioadmin"
  MINIO_BUCKET: str = "screenshots"
  # Public URL that the browser can reach (differs from internal endpoint in Docker)
  MINIO_PUBLIC_URL: str = "http://localhost:9000"

  # ── Browser-use ───────────────────────────────────────────────────────────
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
      self.DATABASE_URL = (
        f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
        f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
      )
    return self


settings = Settings()
