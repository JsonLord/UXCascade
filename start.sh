#!/usr/bin/env bash
set -e

echo "Running database migrations..."
uv run alembic upgrade head || echo "Alembic migration warning/failed, continuing if DB already up to date"

PORT="${PORT:-7860}"
echo "Starting FastAPI app on port ${PORT}..."
exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT}"
