#!/usr/bin/env bash
set -e

if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL provided ($DATABASE_URL), running alembic upgrade head..."
    uv run alembic upgrade head || echo "Alembic migration warning/failed, continuing..."
else
    echo "DATABASE_URL not set. Defaulting to local SQLite at /app/uxcascade.db..."
    # Note: Alembic in this project is configured specifically for PostgreSQL asyncpg dialect.
    # When using SQLite, SQLAlchemy create_all is called dynamically at startup by the app.
fi

PORT="${PORT:-7860}"
echo "Starting FastAPI app on port ${PORT}..."
exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT}"
