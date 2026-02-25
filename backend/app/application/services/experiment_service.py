from __future__ import annotations

from app.domain.entities.experiment import Experiment
from app.domain.repositories.experiment_repository import IExperimentRepository
from app.domain.value_objects.persona import TraitConfig


class ExperimentService:
  """
  Application service responsible for managing the lifecycle of Experiments.

  Provides CRUD operations and execution triggers.
  The actual simulation execution is handled by SimulationRunner in the infrastructure layer.
  """

  def __init__(self, experiment_repo: IExperimentRepository) -> None:
    self._repo = experiment_repo

  async def create(
    self,
    name: str,
    target_url: str,
    traits: list[TraitConfig],
    goals: list[str],
  ) -> Experiment:
    """Creates a new experiment and persists it."""
    experiment = Experiment(
      name=name,
      target_url=target_url,
      traits=traits,
      goals=goals,
    )
    await self._repo.save(experiment)
    return experiment

  async def get(self, experiment_id: str) -> Experiment | None:
    return await self._repo.find_by_id(experiment_id)

  async def list_all(self) -> list[Experiment]:
    return await self._repo.find_all()

  async def delete(self, experiment_id: str) -> None:
    await self._repo.delete(experiment_id)

  async def mark_running(self, experiment: Experiment) -> None:
    experiment.start()
    await self._repo.save(experiment)

  async def mark_annotating(self, experiment: Experiment) -> None:
    experiment.mark_annotating()
    await self._repo.save(experiment)

  async def mark_completed(self, experiment: Experiment) -> None:
    experiment.complete()
    await self._repo.save(experiment)

  async def mark_failed(self, experiment: Experiment) -> None:
    experiment.fail()
    await self._repo.save(experiment)
