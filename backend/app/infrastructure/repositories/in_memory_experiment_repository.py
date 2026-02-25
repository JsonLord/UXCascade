from __future__ import annotations

from app.domain.entities.experiment import Experiment
from app.domain.repositories.experiment_repository import IExperimentRepository
from app.domain.value_objects.enums import ExperimentStatus


class InMemoryExperimentRepository(IExperimentRepository):
  """In-memory repository for development and testing. Replace with SQLite/PostgreSQL in production."""

  def __init__(self) -> None:
    self._store: dict[str, Experiment] = {}

  async def save(self, experiment: Experiment) -> None:
    self._store[experiment.id] = experiment

  async def find_by_id(self, experiment_id: str) -> Experiment | None:
    return self._store.get(experiment_id)

  async def find_all(self) -> list[Experiment]:
    return list(self._store.values())

  async def find_by_status(self, status: ExperimentStatus) -> list[Experiment]:
    return [e for e in self._store.values() if e.status == status]

  async def delete(self, experiment_id: str) -> None:
    self._store.pop(experiment_id, None)
