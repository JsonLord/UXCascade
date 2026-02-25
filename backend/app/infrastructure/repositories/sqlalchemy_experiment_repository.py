from __future__ import annotations

import uuid as _uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models
from app.domain.entities.experiment import Experiment
from app.domain.repositories.experiment_repository import IExperimentRepository
from app.domain.value_objects.enums import ExperimentStatus
from app.domain.value_objects.persona import TraitConfig


def _row_to_entity(
  row: models.Experiment,
  traits: list[models.TraitConfig],
  goals: list[models.ExperimentGoal],
) -> Experiment:
  return Experiment(
    id=str(row.id),
    name=row.name,
    target_url=row.target_url,
    status=ExperimentStatus(row.status),
    traits=[TraitConfig(name=t.name, key=t.key, values=list(t.values)) for t in traits],
    goals=[g.goal for g in goals],
    created_at=row.created_at,
    updated_at=row.updated_at,
  )


async def _load_related(
  session: AsyncSession, experiment_id: Any
) -> tuple[list[models.TraitConfig], list[models.ExperimentGoal]]:
  traits = (
    (
      await session.execute(
        select(models.TraitConfig).where(
          models.TraitConfig.experiment_id == experiment_id
        )
      )
    )
    .scalars()
    .all()
  )
  goals = (
    (
      await session.execute(
        select(models.ExperimentGoal).where(
          models.ExperimentGoal.experiment_id == experiment_id
        )
      )
    )
    .scalars()
    .all()
  )
  return list(traits), list(goals)


class SQLAlchemyExperimentRepository(IExperimentRepository):
  """
  PostgreSQL (asyncpg + SQLAlchemy async) implementation of the Experiment repository.
  Uses ORM models from app.db.models and handles mapping to domain entities.
  """

  def __init__(self, session: AsyncSession) -> None:
    self._session = session

  async def save(self, experiment: Experiment) -> None:
    exp_id = _uuid.UUID(experiment.id)
    row = (
      await self._session.execute(
        select(models.Experiment).where(models.Experiment.id == exp_id)
      )
    ).scalar_one_or_none()

    if row is None:
      row = models.Experiment(
        id=exp_id,
        name=experiment.name,
        target_url=experiment.target_url,
        status=experiment.status.value,
      )
      self._session.add(row)
      await self._session.flush()
    else:
      row.name = experiment.name
      row.target_url = experiment.target_url
      row.status = experiment.status.value

    # Replace traits
    await self._session.execute(
      delete(models.TraitConfig).where(models.TraitConfig.experiment_id == exp_id)
    )
    self._session.add_all(
      [
        models.TraitConfig(
          experiment_id=exp_id,
          name=t.name,
          key=t.key,
          values=t.values,
        )
        for t in experiment.traits
      ]
    )

    # Replace goals
    await self._session.execute(
      delete(models.ExperimentGoal).where(models.ExperimentGoal.experiment_id == exp_id)
    )
    self._session.add_all(
      [models.ExperimentGoal(experiment_id=exp_id, goal=g) for g in experiment.goals]
    )
    await self._session.commit()

  async def find_by_id(self, experiment_id: str) -> Experiment | None:
    exp_id = _uuid.UUID(experiment_id)
    row = (
      await self._session.execute(
        select(models.Experiment).where(models.Experiment.id == exp_id)
      )
    ).scalar_one_or_none()
    if row is None:
      return None
    traits, goals = await _load_related(self._session, exp_id)
    return _row_to_entity(row, traits, goals)

  async def find_all(self) -> list[Experiment]:
    rows = (
      (
        await self._session.execute(
          select(models.Experiment).order_by(models.Experiment.created_at.desc())
        )
      )
      .scalars()
      .all()
    )
    result = []
    for row in rows:
      traits, goals = await _load_related(self._session, row.id)
      result.append(_row_to_entity(row, traits, goals))
    return result

  async def find_by_status(self, status: ExperimentStatus) -> list[Experiment]:
    rows = (
      (
        await self._session.execute(
          select(models.Experiment).where(models.Experiment.status == status.value)
        )
      )
      .scalars()
      .all()
    )
    result = []
    for row in rows:
      traits, goals = await _load_related(self._session, row.id)
      result.append(_row_to_entity(row, traits, goals))
    return result

  async def delete(self, experiment_id: str) -> None:
    exp_id = _uuid.UUID(experiment_id)
    await self._session.execute(
      delete(models.Experiment).where(models.Experiment.id == exp_id)
    )
    await self._session.commit()
