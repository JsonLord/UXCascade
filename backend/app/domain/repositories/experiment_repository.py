from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.experiment import Experiment
from app.domain.value_objects.enums import ExperimentStatus


class IExperimentRepository(ABC):
  """
  Repository interface (Port) for the Experiment aggregate.
  Independent of the persistence mechanism (SQLite / JSON / PostgreSQL, etc.).
  """

  @abstractmethod
  async def save(self, experiment: Experiment) -> None:
    """Save an Experiment (create or update)."""
    ...

  @abstractmethod
  async def find_by_id(self, experiment_id: str) -> Experiment | None:
    """Retrieve an Experiment by ID."""
    ...

  @abstractmethod
  async def find_all(self) -> list[Experiment]:
    """Retrieve all Experiments."""
    ...

  @abstractmethod
  async def find_by_status(self, status: ExperimentStatus) -> list[Experiment]:
    """Retrieve all Experiments with the specified status."""
    ...

  @abstractmethod
  async def delete(self, experiment_id: str) -> None:
    """Delete an Experiment."""
    ...
