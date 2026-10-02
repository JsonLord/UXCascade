#!/usr/bin/env bash
set -e

if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL provided ($DATABASE_URL), running alembic upgrade head..."
    /app/.venv/bin/alembic upgrade head || echo "Alembic migration warning/failed, continuing..."
else
    echo "DATABASE_URL not set. Defaulting to local SQLite at /app/uxcascade.db..."
fi

PORT="${PORT:-7860}"
echo "Starting FastAPI app on port ${PORT}..."
exec /app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port "${PORT}"
