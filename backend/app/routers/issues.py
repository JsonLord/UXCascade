from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import schemas
from app.infrastructure.db.crud import get_issue_detail, list_issues
from app.infrastructure.db.database import get_session

router = APIRouter(tags=["issues"])


@router.get(
  "/{experiment_id}/issues",
  response_model=list[schemas.IssueSummary],
)
async def list_issues_api(
  experiment_id: str,
  goal: str | None = None,
  trait_key: str | None = Query(default=None, alias="trait_key"),
  trait_value: str | None = Query(default=None, alias="trait_value"),
  upt_category: str | None = Query(default=None, alias="upt_category"),
  session: AsyncSession = Depends(get_session),
) -> list[schemas.IssueSummary]:
  return await list_issues(
    session,
    experiment_id=experiment_id,
    goal=goal,
    trait_key=trait_key,
    trait_value=trait_value,
    upt_category=upt_category,
  )


@router.get(
  "/{experiment_id}/issues/{issue_id}",
  response_model=schemas.IssueDetail,
)
async def get_issue_detail_api(
  experiment_id: str,
  issue_id: str,
  session: AsyncSession = Depends(get_session),
) -> schemas.IssueDetail:
  result = await get_issue_detail(
    session, experiment_id=experiment_id, issue_id=issue_id
  )
  if not result:
    raise HTTPException(status_code=404, detail="Issue not found")
  return schemas.IssueDetail(**result)
