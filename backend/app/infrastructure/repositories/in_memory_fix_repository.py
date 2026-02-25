from __future__ import annotations

from collections import defaultdict

from app.domain.entities.fix import EvaluationResult, Fix
from app.domain.repositories.fix_repository import IFixRepository


class InMemoryFixRepository(IFixRepository):
  """In-memory repository for development and testing."""

  def __init__(self) -> None:
    self._fixes: dict[str, Fix] = {}
    self._evaluations: dict[str, list[EvaluationResult]] = defaultdict(list)

  async def save_fix(self, fix: Fix) -> None:
    self._fixes[fix.id] = fix

  async def find_fix_by_id(self, fix_id: str) -> Fix | None:
    return self._fixes.get(fix_id)

  async def find_fixes_by_experiment(self, experiment_id: str) -> list[Fix]:
    return [f for f in self._fixes.values() if f.experiment_id == experiment_id]

  async def save_evaluation(self, evaluation: EvaluationResult) -> None:
    self._evaluations[evaluation.fix_id].append(evaluation)

  async def find_evaluations_by_fix(self, fix_id: str) -> list[EvaluationResult]:
    return list(self._evaluations.get(fix_id, []))
