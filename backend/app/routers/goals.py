from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.infrastructure.db.crud import list_goal_summaries, list_trait_distributions
from app.infrastructure.db.database import get_session

router = APIRouter(tags=["goals"])


@router.get(
  "/{experiment_id}/goals",
  response_model=list[schemas.GoalSummary],
)
async def list_goals_api(
  experiment_id: str,
  session: AsyncSession = Depends(get_session),
) -> list[schemas.GoalSummary]:
  return await list_goal_summaries(session, experiment_id)


@router.get(
  "/{experiment_id}/goals/{goal}/traits",
  response_model=list[schemas.TraitDistribution],
)
async def list_trait_distributions_api(
  experiment_id: str,
  goal: str,
  session: AsyncSession = Depends(get_session),
) -> list[schemas.TraitDistribution]:
  return await list_trait_distributions(session, experiment_id, goal)
