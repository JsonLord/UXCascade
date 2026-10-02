from __future__ import annotations

import logging

from fastapi import (
  APIRouter,
  BackgroundTasks,
  Depends,
  HTTPException,
  WebSocket,
  WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.core.llm_provider import LLMProvider
from app.infrastructure.db.crud import get_experiment
from app.infrastructure.db.database import async_session, get_session
from app.infrastructure.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["runs"])
ws_router = APIRouter(tags=["ws"])


# ── POST /experiments/{id}/run ────────────────────────────────────────────────


@router.post(
  "/{experiment_id}/run", status_code=202, response_model=schemas.RunResponse
)
async def run_experiment(
  experiment_id: str,
  background_tasks: BackgroundTasks,
  session: AsyncSession = Depends(get_session),
) -> schemas.RunResponse:
  """
  Launches the simulation as a background task.

  First validates LLM configuration and connectivity, blocking run with HTTP 503
  if the LLM is unready/misconfigured.
  """
  status, reason = LLMProvider.validate_configuration()
  if status != "CONFIGURED":
    raise HTTPException(
      status_code=503,
      detail={
        "code": f"LLM_{status}",
        "provider": LLMProvider.get_provider_name(),
        "reason": reason,
      },
    )

  row = await get_experiment(session, experiment_id)
  if not row:
    raise HTTPException(status_code=404, detail="Experiment not found")

  background_tasks.add_task(_simulate_and_annotate, experiment_id)
  return schemas.RunResponse(message="Simulation started", experiment_id=experiment_id)


async def _simulate_and_annotate(experiment_id: str) -> None:
  """
  The full simulation + annotation flow executed in the background.
  """
  from app.agents.issue_detector_agent import IssueDetectorAgent
  from app.agents.simulation_agent import SimulationAgent
  from app.agents.tagging_agent import TaggingAgent
  from app.application.services.annotation_service import AnnotationService
  from app.domain.services.goal_aggregator import GoalAggregator
  from app.infrastructure.browser_adapter import BrowserUseAdapter
  from app.infrastructure.orchestration.annotation_pipeline import AnnotationPipeline
  from app.infrastructure.orchestration.simulation_runner import SimulationRunner
  from app.infrastructure.repositories.sqlalchemy_agent_run_repository import (
    SQLAlchemyAgentRunRepository,
  )
  from app.infrastructure.repositories.sqlalchemy_annotation_repository import (
    SQLAlchemyAnnotationRepository,
  )
  from app.infrastructure.repositories.sqlalchemy_experiment_repository import (
    SQLAlchemyExperimentRepository,
  )

  async with async_session() as session:
    experiment_repo = SQLAlchemyExperimentRepository(session)
    agent_run_repo = SQLAlchemyAgentRunRepository(session)
    annotation_repo = SQLAlchemyAnnotationRepository(session)

    experiment = await experiment_repo.find_by_id(experiment_id)
    if not experiment:
      return

    browser_port = BrowserUseAdapter()
    sim_agent = SimulationAgent(browser_port=browser_port)
    runner = SimulationRunner(
      sim_agent,
      experiment_repo,
      agent_run_repo,
      session_factory=async_session,
      ws_manager=ws_manager,
    )

    try:
      # ── Phase 1: Simulation ──────────────────────────────────────────────
      await runner.run(experiment)

      await ws_manager.broadcast(
        experiment_id,
        {"type": "status_change", "status": experiment.status.value},
      )

      # Skip annotation if simulation failed
      if experiment.status.value != "annotating":
        return

      # ── Phase 2: Annotation ──────────────────────────────────────────────
      annotation_service = AnnotationService(
        tagging_agent=TaggingAgent(),
        issue_detector=IssueDetectorAgent(),
        annotation_repo=annotation_repo,
      )
      pipeline = AnnotationPipeline(
        annotation_service=annotation_service,
        goal_aggregator=GoalAggregator(),
        experiment_repo=experiment_repo,
        agent_run_repo=agent_run_repo,
        annotation_repo=annotation_repo,
      )

      await pipeline.run(experiment)

      await ws_manager.broadcast(
        experiment_id,
        {"type": "status_change", "status": "completed"},
      )

    except Exception as exc:
      logger.exception("Experiment %s failed: %s", experiment_id, exc)

      try:
        experiment.fail()
        await experiment_repo.save(experiment)
      except Exception:
        logger.exception("Failed to mark experiment %s as failed", experiment_id)

      await ws_manager.broadcast(
        experiment_id,
        {"type": "error", "message": str(exc)},
      )


# ── WS /ws/experiments/{id} ───────────────────────────────────────────────────


@ws_router.websocket("/{experiment_id}")
async def ws_experiment(experiment_id: str, websocket: WebSocket) -> None:
  await ws_manager.connect(experiment_id, websocket)
  try:
    while True:
      await websocket.receive_text()
  except WebSocketDisconnect:
    ws_manager.disconnect(experiment_id, websocket)
