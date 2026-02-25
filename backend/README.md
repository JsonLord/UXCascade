# Backend Setup

## Overview

FastAPI application managed with [uv](https://docs.astral.sh/uv/).

## Requirements

- [uv](https://docs.astral.sh/uv/) >= 0.6

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Getting Started

### Create virtual environment and install dependencies

```bash
uv sync --all-groups
```

### Database & migrations

The backend uses async PostgreSQL. Set `DATABASE_URL` or rely on Docker Compose.

```bash
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```

### Start development server

```bash
uv run uvicorn main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).
Interactive docs (Swagger UI) are at [http://localhost:8000/docs](http://localhost:8000/docs).

## Available Commands

### Application

| Command | Description |
|---------|-------------|
| `uv run uvicorn main:app --reload` | Start dev server with auto-reload |
| `uv add <package>` | Add a runtime dependency |
| `uv add --dev <package>` | Add a dev dependency |
| `uv remove <package>` | Remove a dependency |
| `uv sync` | Sync environment with `pyproject.toml` |

### Linting & Formatting (indent: 2 spaces)

| Command | Description |
|---------|-------------|
| `uv run ruff check .` | Lint with ruff |
| `uv run ruff check --fix .` | Lint and auto-fix |
| `uv run ruff format .` | Format with ruff |
| `uv run ruff format --check .` | Check formatting without writing |

### Type Checking

| Command | Description |
|---------|-------------|
| `uv run ty check` | Type-check with ty (Astral) |

## Tech Stack

### Runtime

- **FastAPI** 0.132
- **Uvicorn** 0.41 (ASGI server)
- **Python** >= 3.13
- **uv** (package and environment manager)

### Dev Tools

| Tool | Package | Description |
|------|---------|-------------|
| ruff | `ruff` | Fast linter + formatter (Rust-based, indent: 2 spaces) |
| ty | `ty` | Fast type checker (Rust-based, Astral, beta) |
