from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.api.deps import get_fix_repo, get_refinement_service
from app.application.services.refinement_service import RefinementService
from app.infrastructure.db.crud import get_fix_detail, get_issue_by_id, list_fixes
from app.infrastructure.db.database import get_session
from app.infrastructure.repositories.sqlalchemy_fix_repository import (
  SQLAlchemyFixRepository,
)

router = APIRouter(tags=["fixes"])


@router.post(
  "/{experiment_id}/fixes",
  response_model=schemas.FixAgentResponse,
  status_code=status.HTTP_201_CREATED,
)
async def create_fix_api(
  experiment_id: str,
  payload: schemas.FixCreate,
  session: AsyncSession = Depends(get_session),
  service: Annotated[RefinementService, Depends(get_refinement_service)] = ...,
) -> schemas.FixAgentResponse:
  """
  Calls the Editor Agent to generate HTML patches and create a Fix.

  If snapshot_step is omitted, uses the step associated with the Issue.
  """
  issue = await get_issue_by_id(session, payload.issue_id)
  if not issue:
    raise HTTPException(status_code=404, detail="Issue not found")

  step = payload.snapshot_step if payload.snapshot_step is not None else issue.step

  try:
    fix = await service.create_fix(
      experiment_id=experiment_id,
      issue_id=payload.issue_id,
      agent_run_id=str(issue.agent_run_id),
      step=step,
      instruction=payload.instruction,
    )
  except ValueError as e:
    raise HTTPException(status_code=422, detail=str(e))

  return schemas.FixAgentResponse(
    id=fix.id,
    status=fix.status,
    patches=[
      schemas.FixPatchIn(
        selector=p.selector,
        action=p.action.value,
        value=p.value,
        name=p.name,
        rationale=p.rationale,
      )
      for p in fix.patches
    ],
    notes=fix.notes,
  )


@router.get(
  "/{experiment_id}/fixes",
  response_model=list[schemas.FixSummary],
)
async def list_fixes_api(
  experiment_id: str,
  session: AsyncSession = Depends(get_session),
) -> list[schemas.FixSummary]:
  return await list_fixes(session, experiment_id)


@router.get(
  "/{experiment_id}/fixes/{fix_id}",
  response_model=schemas.FixDetail,
)
async def get_fix_detail_api(
  experiment_id: str,
  fix_id: str,
  session: AsyncSession = Depends(get_session),
) -> schemas.FixDetail:
  result = await get_fix_detail(session, experiment_id=experiment_id, fix_id=fix_id)
  if not result:
    raise HTTPException(status_code=404, detail="Fix not found")
  return schemas.FixDetail(**result)


@router.post(
  "/{experiment_id}/fixes/{fix_id}/evaluate",
  response_model=schemas.EvaluationSummary,
)
async def evaluate_fix_api(
  experiment_id: str,
  fix_id: str,
  service: Annotated[RefinementService, Depends(get_refinement_service)] = ...,
  fix_repo: Annotated[SQLAlchemyFixRepository, Depends(get_fix_repo)] = ...,
  session: AsyncSession = Depends(get_session),
) -> schemas.EvaluationSummary:
  """
  Calls the Preview Agent to evaluate the impact of a fix.

  Automatically resolves the agent_run_id and step from the Issue linked to the Fix,
  then runs a re-simulation.
  """
  fix = await fix_repo.find_fix_by_id(fix_id)
  if not fix:
    raise HTTPException(status_code=404, detail="Fix not found")

  issue = await get_issue_by_id(session, fix.issue_id)
  if not issue:
    raise HTTPException(status_code=404, detail="Issue not found")

  evaluation = await service.evaluate_fix(
    fix_id=fix_id,
    agent_run_id=str(issue.agent_run_id),
    step=issue.step,
  )

  return schemas.EvaluationSummary(
    id=evaluation.id,
    fix_id=evaluation.fix_id,
    agent_run_id=evaluation.agent_run_id,
    step=evaluation.step,
    action_changed=evaluation.action_changed,
    issue_resolved=evaluation.issue_resolved,
    summary=evaluation.summary,
    before_action={
      "type": evaluation.before_action.type,
      "selector": evaluation.before_action.selector,
      "value": evaluation.before_action.value,
    },
    after_action={
      "type": evaluation.after_action.type,
      "selector": evaluation.after_action.selector,
      "value": evaluation.after_action.value,
    },
    created_at=evaluation.created_at,
  )
