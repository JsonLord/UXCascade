from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.annotation import (
  GoalSummary,
  StepAnnotation,
)


class IAnnotationRepository(ABC):
  """
  Repository interface (Port) for StepAnnotation and GoalSummary.
  """

  @abstractmethod
  async def save_step_annotation(self, annotation: StepAnnotation) -> None:
    """Save a StepAnnotation."""
    ...

  @abstractmethod
  async def find_annotations_by_run(self, agent_run_id: str) -> list[StepAnnotation]:
    """Retrieve all StepAnnotations associated with an AgentRun ID."""
    ...

  @abstractmethod
  async def save_goal_summary(self, summary: GoalSummary) -> None:
    """Save a GoalSummary."""
    ...

  @abstractmethod
  async def find_goal_summaries_by_experiment(
    self, experiment_id: str
  ) -> list[GoalSummary]:
    """Retrieve all GoalSummaries associated with an experiment ID."""
    ...
