from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.infrastructure.db.crud import (
  create_experiment,
  delete_experiment,
  get_experiment,
  list_experiments,
  update_experiment,
)
from app.infrastructure.db.database import get_session

router = APIRouter(tags=["experiments"])


@router.get("/", response_model=list[schemas.ExperimentSummary])
async def list_experiments_api(
  session: AsyncSession = Depends(get_session),
) -> list[schemas.ExperimentSummary]:
  return await list_experiments(session)


@router.post(
  "/",
  response_model=schemas.ExperimentDetail,
  status_code=status.HTTP_201_CREATED,
)
async def create_experiment_api(
  payload: schemas.ExperimentCreate,
  session: AsyncSession = Depends(get_session),
) -> schemas.ExperimentDetail:
  experiment = await create_experiment(
    session,
    name=payload.name,
    target_url=payload.target_url,
    traits=[t.model_dump() for t in payload.traits],
    goals=payload.goals,
  )
  result = await get_experiment(session, str(experiment.id))
  return schemas.ExperimentDetail(**result)


@router.get("/{experiment_id}", response_model=schemas.ExperimentDetail)
async def get_experiment_api(
  experiment_id: str,
  session: AsyncSession = Depends(get_session),
) -> schemas.ExperimentDetail:
  result = await get_experiment(session, experiment_id)
  if not result:
    raise HTTPException(status_code=404, detail="Experiment not found")
  return schemas.ExperimentDetail(**result)


@router.put("/{experiment_id}", response_model=schemas.ExperimentDetail)
async def update_experiment_api(
  experiment_id: str,
  payload: schemas.ExperimentUpdate,
  session: AsyncSession = Depends(get_session),
) -> schemas.ExperimentDetail:
  result = await update_experiment(
    session,
    experiment_id=experiment_id,
    name=payload.name,
    target_url=payload.target_url,
    status=payload.status,
    traits=[t.model_dump() for t in payload.traits]
    if payload.traits is not None
    else None,
    goals=payload.goals,
  )
  if not result:
    raise HTTPException(status_code=404, detail="Experiment not found")
  return schemas.ExperimentDetail(**result)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment_api(
  experiment_id: str,
  session: AsyncSession = Depends(get_session),
) -> None:
  deleted = await delete_experiment(session, experiment_id)
  if not deleted:
    raise HTTPException(status_code=404, detail="Experiment not found")
