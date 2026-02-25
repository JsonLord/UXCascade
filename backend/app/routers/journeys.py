from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.infrastructure.db.crud import get_agent_run_steps, get_journeys
from app.infrastructure.db.database import get_session

router = APIRouter(tags=["journeys"])


@router.get("/{experiment_id}/journeys", response_model=schemas.JourneyResponse)
async def get_journeys_api(
  experiment_id: str,
  mode: Literal["page_navigation", "goal_steps"] = "page_navigation",
  session: AsyncSession = Depends(get_session),
) -> schemas.JourneyResponse:
  """
  Returns agent journey data for the Sankey diagram.

  Query params:
    mode=page_navigation  Aggregates transitions between page URLs (default)
    mode=goal_steps       Aggregates transitions by action type
  """
  data = await get_journeys(session, experiment_id, mode=mode)
  return schemas.JourneyResponse(
    nodes=[schemas.JourneyNode(**n) for n in data["nodes"]],
    links=[schemas.JourneyLink(**l) for l in data["links"]],
  )


@router.get("/{experiment_id}/agent-run-steps")
async def get_agent_run_steps_api(
  experiment_id: str,
  session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
  """
  Returns all agent runs associated with the experiment and their step list
  (for the journey timeline).

  Paper Figure 1 Agent Journey tab: returns individual agent reasoning traces
  together with screenshots, actions, and reasoning text.
  """
  return await get_agent_run_steps(session, experiment_id)
