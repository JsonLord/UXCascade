from __future__ import annotations

import uuid as _uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.fix import EvaluationResult, Fix
from app.domain.repositories.fix_repository import IFixRepository
from app.domain.value_objects.action import Action, HtmlPatch
from app.domain.value_objects.enums import PatchAction
from app.infrastructure.db import models


async def _load_patches(session: AsyncSession, fix_id: _uuid.UUID) -> list[HtmlPatch]:
  rows = (
    (
      await session.execute(
        select(models.HtmlPatch).where(models.HtmlPatch.fix_id == fix_id)
      )
    )
    .scalars()
    .all()
  )
  return [
    HtmlPatch(
      selector=r.selector,
      action=PatchAction(r.action),
      value=r.value,
      name=r.name,
      rationale=r.rationale,
    )
    for r in rows
  ]


def _fix_row_to_entity(row: models.Fix, patches: list[HtmlPatch]) -> Fix:
  return Fix(
    id=str(row.id),
    experiment_id=str(row.experiment_id),
    issue_id=str(row.issue_id),
    instruction=row.instruction,
    patches=patches,
    status=row.status,
    notes=row.notes or "",
    created_at=row.created_at,
  )


def _eval_row_to_entity(row: models.EvaluationResult) -> EvaluationResult:
  before = row.before_action or {}
  after = row.after_action or {}
  return EvaluationResult(
    id=str(row.id),
    fix_id=str(row.fix_id),
    agent_run_id=str(row.agent_run_id),
    step=row.step,
    action_changed=row.action_changed,
    issue_resolved=row.issue_resolved,
    summary=row.summary,
    before_action=Action(
      type=before.get("type", "navigate"),
      selector=before.get("selector"),
      value=before.get("value"),
    ),
    after_action=Action(
      type=after.get("type", "navigate"),
      selector=after.get("selector"),
      value=after.get("value"),
    ),
    created_at=row.created_at,
  )


class SQLAlchemyFixRepository(IFixRepository):
  """
  PostgreSQL implementation of the Fix + EvaluationResult repository.
  """

  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def save_fix(self, fix: Fix) -> None:
    fix_id = _uuid.UUID(fix.id)
    row = (
      await self._session.execute(select(models.Fix).where(models.Fix.id == fix_id))
    ).scalar_one_or_none()

    if row is None:
      row = models.Fix(
        id=fix_id,
        experiment_id=_uuid.UUID(fix.experiment_id),
        issue_id=_uuid.UUID(fix.issue_id),
        instruction=fix.instruction,
        status=fix.status,
        notes=fix.notes,
        created_at=fix.created_at,
      )
      self._session.add(row)
      await self._session.flush()
    else:
      row.status = fix.status
      row.notes = fix.notes
      await self._session.flush()

    # Replace patches
    await self._session.execute(
      delete(models.HtmlPatch).where(models.HtmlPatch.fix_id == fix_id)
    )
    self._session.add_all(
      [
        models.HtmlPatch(
          fix_id=fix_id,
          selector=p.selector,
          action=p.action.value,
          value=p.value,
          name=p.name,
          rationale=p.rationale,
        )
        for p in fix.patches
      ]
    )
    await self._session.commit()

  async def find_fix_by_id(self, fix_id: str) -> Fix | None:
    fid = _uuid.UUID(fix_id)
    row = (
      await self._session.execute(select(models.Fix).where(models.Fix.id == fid))
    ).scalar_one_or_none()
    if row is None:
      return None
    patches = await _load_patches(self._session, fid)
    return _fix_row_to_entity(row, patches)

  async def find_fixes_by_experiment(self, experiment_id: str) -> list[Fix]:
    exp_id = _uuid.UUID(experiment_id)
    rows = (
      (
        await self._session.execute(
          select(models.Fix).where(models.Fix.experiment_id == exp_id)
        )
      )
      .scalars()
      .all()
    )
    result = []
    for row in rows:
      patches = await _load_patches(self._session, row.id)
      result.append(_fix_row_to_entity(row, patches))
    return result

  async def save_evaluation(self, evaluation: EvaluationResult) -> None:
    self._session.add(
      models.EvaluationResult(
        id=_uuid.UUID(evaluation.id),
        fix_id=_uuid.UUID(evaluation.fix_id),
        agent_run_id=_uuid.UUID(evaluation.agent_run_id),
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
    )
    await self._session.commit()

  async def find_evaluations_by_fix(self, fix_id: str) -> list[EvaluationResult]:
    fid = _uuid.UUID(fix_id)
    rows = (
      (
        await self._session.execute(
          select(models.EvaluationResult).where(models.EvaluationResult.fix_id == fid)
        )
      )
      .scalars()
      .all()
    )
    return [_eval_row_to_entity(r) for r in rows]
