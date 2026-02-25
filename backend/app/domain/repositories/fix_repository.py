from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.fix import EvaluationResult, Fix


class IFixRepository(ABC):
  """Repository interface (Port) for Fix and EvaluationResult."""

  @abstractmethod
  async def save_fix(self, fix: Fix) -> None:
    """Save a Fix."""
    ...

  @abstractmethod
  async def find_fix_by_id(self, fix_id: str) -> Fix | None:
    """Retrieve a Fix by ID."""
    ...

  @abstractmethod
  async def find_fixes_by_experiment(self, experiment_id: str) -> list[Fix]:
    """Retrieve all Fixes associated with an experiment ID."""
    ...

  @abstractmethod
  async def save_evaluation(self, evaluation: EvaluationResult) -> None:
    """Save an EvaluationResult."""
    ...

  @abstractmethod
  async def find_evaluations_by_fix(self, fix_id: str) -> list[EvaluationResult]:
    """Retrieve all EvaluationResults associated with a Fix ID."""
    ...
