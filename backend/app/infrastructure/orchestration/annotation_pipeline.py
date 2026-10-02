from __future__ import annotations

import asyncio

from app.application.services.annotation_service import AnnotationService
from app.domain.entities.experiment import Experiment
from app.domain.repositories.agent_run_repository import IAgentRunRepository
from app.domain.repositories.annotation_repository import IAnnotationRepository
from app.domain.repositories.experiment_repository import IExperimentRepository
from app.domain.services.goal_aggregator import GoalAggregator


class AnnotationPipeline:
  """
  Pipeline that batch-processes annotations after all simulations have completed.
  """

  MAX_CONCURRENT: int = 5

  def __init__(
    self,
    annotation_service: AnnotationService,
    goal_aggregator: GoalAggregator,
    experiment_repo: IExperimentRepository,
    agent_run_repo: IAgentRunRepository,
    annotation_repo: IAnnotationRepository,
  ) -> None:
    self._annotation_service = annotation_service
    self._goal_aggregator = goal_aggregator
    self._experiment_repo = experiment_repo
    self._run_repo = agent_run_repo
    self._annotation_repo = annotation_repo

  async def run(self, experiment: Experiment) -> None:
    # Do not transition or process if simulation previously marked experiment as failed
    if experiment.status.value == "failed":
      return

    runs = await self._run_repo.find_by_experiment_id(experiment.id)

    sem = asyncio.Semaphore(self.MAX_CONCURRENT)

    async def _annotate_with_limit(run) -> None:
      async with sem:
        await self._annotation_service.annotate_run(run)

    await asyncio.gather(*[_annotate_with_limit(r) for r in runs])

    await self._aggregate_and_save(experiment, runs)

    experiment.complete()
    await self._experiment_repo.save(experiment)

  async def _aggregate_and_save(
    self,
    experiment: Experiment,
    runs,
  ) -> None:
    annotations_map = {}
    for run in runs:
      annotations = await self._annotation_repo.find_annotations_by_run(run.id)
      annotations_map[run.id] = annotations

    summaries = self._goal_aggregator.aggregate(
      experiment=experiment,
      runs=runs,
      annotations=annotations_map,
    )

    for summary in summaries:
      await self._annotation_repo.save_goal_summary(summary)
