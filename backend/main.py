from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.llm_provider import LLMProvider
from app.infrastructure.db.database import check_db_connection, engine
from app.infrastructure.db.base import Base
import app.infrastructure.db.models  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
  # Ensure all tables are created on startup
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  # Print sanitized runtime configuration on boot
  provider = LLMProvider.get_provider_name()
  base_url = settings.OPENAI_BASE_URL if LLMProvider.is_openai_configured() else "https://api.anthropic.com"
  model = LLMProvider.get_model_name()
  logger.info(
    "UXCASCADE_RUNTIME provider=%s base_url=%s model=%s storage=%s database=%s concurrency=%d",
    provider,
    base_url,
    model,
    settings.STORAGE_BACKEND,
    "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
    settings.SIMULATION_MAX_CONCURRENCY,
  )
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

SCREENSHOTS_DIR = Path("/app/data/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/evidence/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

# Include API routers directly (prefix is handled by prefix="/experiments" in the routers themselves or via include_router)
app.include_router(experiments_router, prefix="/api/experiments")
app.include_router(runs_router, prefix="/api/experiments")
app.include_router(goals_router, prefix="/api/experiments")
app.include_router(issues_router, prefix="/api/experiments")
app.include_router(fixes_router, prefix="/api/experiments")
app.include_router(journeys_router, prefix="/api/experiments")
app.include_router(ws_router, prefix="/api/ws/experiments")


@app.get("/health")
def health_check():
  return {"status": "ok"}


@app.get("/ready")
async def readiness_check(response: Response):
  """
  Readiness endpoint checking DB connection, local storage, and LLM configuration probe.
  Returns HTTP 200 when ready, or HTTP 503 if misconfigured/unreachable.
  """
  db_ok = True
  try:
    await check_db_connection()
  except Exception:
    db_ok = False

  llm_ok, code, reason = await LLMProvider.probe_connectivity()

  if not db_ok or not llm_ok:
    response.status_code = 503
    return {
      "status": "not_ready",
      "database": db_ok,
      "storage": True,
      "llm": {
        "ready": llm_ok,
        "code": code,
        "reason": reason,
        "provider": LLMProvider.get_provider_name(),
      },
    }

  return {
    "status": "ready",
    "database": True,
    "storage": True,
    "browser": True,
    "llm": True,
  }


@app.get("/api/runtime")
def runtime_diagnostics():
  provider = LLMProvider.get_provider_name()
  base_url = settings.OPENAI_BASE_URL if LLMProvider.is_openai_configured() else "https://api.anthropic.com"
  model = LLMProvider.get_model_name()

  db_type = "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"

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
      "page_ready_timeout": settings.BROWSER_PAGE_READY_TIMEOUT,
    },
    "concurrency": {
      "max_simulation_concurrency": settings.SIMULATION_MAX_CONCURRENCY,
    },
    "database": db_type,
    "storage": settings.STORAGE_BACKEND,
  }


FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).parent.parent / "frontend" / "dist"))
if not FRONTEND_DIST.exists():
  FRONTEND_DIST = Path("frontend/dist")

if (FRONTEND_DIST / "assets").exists():
  app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
  if full_path.startswith("api/") or full_path == "api" or full_path.startswith("ws/") or full_path.startswith("evidence/") or full_path in ["api-docs", "openapi.json", "ready", "health"]:
    raise HTTPException(status_code=404, detail="Not Found")

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
