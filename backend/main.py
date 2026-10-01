from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.llm_provider import LLMProvider
from app.infrastructure.db.database import engine
from app.infrastructure.db.base import Base
import app.infrastructure.db.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
  # Ensure all tables are created on startup (e.g. for SQLite or unmigrated databases)
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  yield


from app.routers import (
  experiments_router,
  fixes_router,
  goals_router,
  issues_router,
  journeys_router,
  runs_router,
  ws_router,
)

app = FastAPI(
  title="UXCascade API",
  docs_url="/api-docs",
  openapi_url="/openapi.json",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Mount evidence screenshots directory for local storage backend
SCREENSHOTS_DIR = Path("/app/data/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/evidence/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

# Mount API routers under /api and / for backwards compatibility
for prefix_base in ["/api", ""]:
  app.include_router(experiments_router, prefix=f"{prefix_base}/experiments")
  app.include_router(runs_router, prefix=f"{prefix_base}/experiments")
  app.include_router(goals_router, prefix=f"{prefix_base}/experiments")
  app.include_router(issues_router, prefix=f"{prefix_base}/experiments")
  app.include_router(fixes_router, prefix=f"{prefix_base}/experiments")
  app.include_router(journeys_router, prefix=f"{prefix_base}/experiments")
  app.include_router(ws_router, prefix=f"{prefix_base}/ws/experiments")


@app.get("/health")
def health_check():
  return {"status": "ok"}


@app.get("/api/runtime")
def runtime_diagnostics():
  """Read-only runtime diagnostics endpoint (sanitized configuration)."""
  provider = LLMProvider.get_provider_name()
  base_url = settings.OPENAI_BASE_URL if LLMProvider.is_openai_configured() else "https://api.anthropic.com"
  model = LLMProvider.get_model_name()

  db_type = "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
  storage_backend = getattr(settings, "STORAGE_BACKEND", "local")

  return {
    "llm": {
      "provider": provider,
      "base_url": base_url,
      "models": {
        "simulation": model,
        "tagging": model,
        "issue_detection": model,
        "editor": model,
        "preview": model,
      },
    },
    "browser": {
      "engine": "chromium",
      "headless": settings.BROWSER_HEADLESS,
    },
    "concurrency": {
      "max_simulation_concurrency": getattr(settings, "SIMULATION_MAX_CONCURRENCY", 1),
    },
    "database": db_type,
    "storage": storage_backend,
  }


FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).parent.parent / "frontend" / "dist"))
if not FRONTEND_DIST.exists():
  FRONTEND_DIST = Path("frontend/dist")

if (FRONTEND_DIST / "assets").exists():
  app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
  # Ensure API routes, docs, evidence, or ws routes return 404 JSON instead of index.html
  if full_path.startswith("api/") or full_path == "api" or full_path.startswith("ws/") or full_path.startswith("evidence/") or full_path == "api-docs" or full_path == "openapi.json":
    raise HTTPException(status_code=404, detail="Not Found")

  # Check if requested path is a static file in FRONTEND_DIST or serve index.html for SPA
  if FRONTEND_DIST.exists():
    file_path = FRONTEND_DIST / full_path
    if full_path and file_path.is_file():
      return FileResponse(file_path)

    index_path = FRONTEND_DIST / "index.html"
    if index_path.is_file():
      return FileResponse(index_path)

  if full_path == "":
    return {"message": "UXCascade backend"}

  raise HTTPException(status_code=404, detail="Not Found")
