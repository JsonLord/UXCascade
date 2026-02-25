from __future__ import annotations

from collections import defaultdict

from app.domain.entities.annotation import GoalSummary, StepAnnotation
from app.domain.repositories.annotation_repository import IAnnotationRepository


class InMemoryAnnotationRepository(IAnnotationRepository):
  """In-memory repository for development and testing."""

  def __init__(self) -> None:
    self._annotations: dict[str, list[StepAnnotation]] = defaultdict(list)
    self._goal_summaries: dict[str, list[GoalSummary]] = defaultdict(list)

  async def save_step_annotation(self, annotation: StepAnnotation) -> None:
    self._annotations[annotation.agent_run_id].append(annotation)

  async def find_annotations_by_run(self, agent_run_id: str) -> list[StepAnnotation]:
    return list(self._annotations.get(agent_run_id, []))

  async def save_goal_summary(self, summary: GoalSummary) -> None:
    self._goal_summaries[summary.experiment_id].append(summary)

  async def find_goal_summaries_by_experiment(
    self, experiment_id: str
  ) -> list[GoalSummary]:
    return list(self._goal_summaries.get(experiment_id, []))
