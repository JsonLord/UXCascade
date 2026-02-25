from __future__ import annotations

import uuid as _uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models
from app.domain.entities.annotation import GoalSummary, Issue, StepAnnotation, TraitDistribution
from app.domain.repositories.annotation_repository import IAnnotationRepository


def _issue_row_to_entity(row: models.Issue) -> Issue:
  return Issue(
    id=str(row.id),
    type=row.type,
    element=row.element,
    reason=row.reason,
    fix=row.fix,
    upt_codes=list(row.upt_codes or []),
    upt_explanation=row.upt_explanation,
    severity=row.severity,
  )


class SQLAlchemyAnnotationRepository(IAnnotationRepository):
  """
  PostgreSQL implementation of the StepAnnotation + GoalSummary repository.
  """

  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def save_step_annotation(self, annotation: StepAnnotation) -> None:
    run_id = _uuid.UUID(annotation.agent_run_id)

    row = (
      await self._session.execute(
        select(models.StepAnnotation)
        .where(models.StepAnnotation.agent_run_id == run_id)
        .where(models.StepAnnotation.step == annotation.step)
      )
    ).scalar_one_or_none()

    if row is None:
      row = models.StepAnnotation(
        agent_run_id=run_id,
        step=annotation.step,
        tags=annotation.tags,
      )
      self._session.add(row)
    else:
      row.tags = annotation.tags

    await self._session.flush()

    if annotation.issues:
      # Fetch experiment_id and goal from AgentRun
      agent_run_row = (
        await self._session.execute(
          select(models.AgentRun).where(models.AgentRun.id == run_id)
        )
      ).scalar_one_or_none()

      if agent_run_row:
        await self._session.execute(
          delete(models.Issue)
          .where(models.Issue.agent_run_id == run_id)
          .where(models.Issue.step == annotation.step)
        )
        for issue in annotation.issues:
          self._session.add(
            models.Issue(
              id=_uuid.UUID(issue.id),
              experiment_id=agent_run_row.experiment_id,
              agent_run_id=run_id,
              step=annotation.step,
              goal=agent_run_row.goal,
              type=issue.type,
              element=issue.element,
              reason=issue.reason,
              fix=issue.fix,
              upt_codes=issue.upt_codes,
              upt_explanation=issue.upt_explanation,
              severity=issue.severity,
            )
          )

    await self._session.commit()

  async def find_annotations_by_run(self, agent_run_id: str) -> list[StepAnnotation]:
    run_id = _uuid.UUID(agent_run_id)
    rows = (
      (
        await self._session.execute(
          select(models.StepAnnotation)
          .where(models.StepAnnotation.agent_run_id == run_id)
          .order_by(models.StepAnnotation.step)
        )
      )
      .scalars()
      .all()
    )
    result = []
    for row in rows:
      issue_rows = (
        (
          await self._session.execute(
            select(models.Issue)
            .where(models.Issue.agent_run_id == run_id)
            .where(models.Issue.step == row.step)
          )
        )
        .scalars()
        .all()
      )
      result.append(
        StepAnnotation(
          agent_run_id=str(row.agent_run_id),
          step=row.step,
          tags=list(row.tags or []),
          issues=[_issue_row_to_entity(i) for i in issue_rows],
        )
      )
    return result

  async def save_goal_summary(self, summary: GoalSummary) -> None:
    exp_id = _uuid.UUID(summary.experiment_id)

    row = (
      await self._session.execute(
        select(models.GoalSummary)
        .where(models.GoalSummary.experiment_id == exp_id)
        .where(models.GoalSummary.goal == summary.goal)
      )
    ).scalar_one_or_none()

    if row is None:
      row = models.GoalSummary(
        experiment_id=exp_id,
        goal=summary.goal,
        agent_count=summary.agent_count,
        success_count=summary.success_count,
        success_rate=summary.success_rate,
        issue_count=summary.issue_count,
      )
      self._session.add(row)
      await self._session.flush()
    else:
      row.agent_count = summary.agent_count
      row.success_count = summary.success_count
      row.success_rate = summary.success_rate
      row.issue_count = summary.issue_count
      await self._session.flush()

    summary_id = row.id

    # Delete existing distributions (join rows also deleted via cascade)
    await self._session.execute(
      delete(models.TraitDistribution).where(
        models.TraitDistribution.goal_summary_id == summary_id
      )
    )

    for dist in summary.trait_distributions:
      dist_row = models.TraitDistribution(
        goal_summary_id=summary_id,
        trait_key=dist.trait_key,
        trait_value=dist.trait_value,
        agent_count=dist.agent_count,
        success_rate=dist.success_rate,
      )
      self._session.add(dist_row)
      await self._session.flush()

      for issue in dist.issues:
        await self._session.execute(
          models.trait_distribution_issues.insert().values(
            trait_distribution_id=dist_row.id,
            issue_id=_uuid.UUID(issue.id),
          )
        )

    await self._session.commit()

  async def find_goal_summaries_by_experiment(
    self, experiment_id: str
  ) -> list[GoalSummary]:
    exp_id = _uuid.UUID(experiment_id)
    rows = (
      (
        await self._session.execute(
          select(models.GoalSummary).where(
            models.GoalSummary.experiment_id == exp_id
          )
        )
      )
      .scalars()
      .all()
    )
    result = []
    for row in rows:
      dist_rows = (
        (
          await self._session.execute(
            select(models.TraitDistribution).where(
              models.TraitDistribution.goal_summary_id == row.id
            )
          )
        )
        .scalars()
        .all()
      )
      distributions = []
      for dist in dist_rows:
        issue_ids = (
          (
            await self._session.execute(
              select(models.trait_distribution_issues.c.issue_id).where(
                models.trait_distribution_issues.c.trait_distribution_id == dist.id
              )
            )
          )
          .scalars()
          .all()
        )
        issue_rows = (
          (
            await self._session.execute(
              select(models.Issue).where(models.Issue.id.in_(issue_ids))
            )
          )
          .scalars()
          .all()
        )
        distributions.append(
          TraitDistribution(
            trait_key=dist.trait_key,
            trait_value=dist.trait_value,
            agent_count=dist.agent_count,
            success_rate=float(dist.success_rate),
            issues=[_issue_row_to_entity(i) for i in issue_rows],
          )
        )
      result.append(
        GoalSummary(
          experiment_id=str(row.experiment_id),
          goal=row.goal,
          agent_count=row.agent_count,
          success_count=row.success_count,
          success_rate=float(row.success_rate),
          issue_count=row.issue_count,
          trait_distributions=distributions,
        )
      )
    return result
