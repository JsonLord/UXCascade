from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.agents.simulation_agent import SimulationAgent
from app.domain.entities.experiment import AgentRun, Experiment
from app.domain.entities.snapshot import EventSnapshot
from app.domain.repositories.agent_run_repository import IAgentRunRepository
from app.domain.repositories.experiment_repository import IExperimentRepository
from app.domain.services.persona_matrix import PersonaMatrix
from app.infrastructure.event_bus import IWebSocketManager

logger = logging.getLogger(__name__)


class SimulationRunner:
  """
  Orchestrator that runs all agents associated with an experiment with bounded concurrency.
  """

  def __init__(
    self,
    simulation_agent: SimulationAgent,
    experiment_repo: IExperimentRepository,
    agent_run_repo: IAgentRunRepository,
    session_factory: Any,
    ws_manager: IWebSocketManager,
  ) -> None:
    self._agent = simulation_agent
    self._experiment_repo = experiment_repo
    self._run_repo = agent_run_repo
    self._session_factory = session_factory
    self._ws_manager = ws_manager
    self._semaphore = asyncio.Semaphore(settings.SIMULATION_MAX_CONCURRENCY)

  async def run(self, experiment: Experiment) -> None:
    experiment.start()
    await self._experiment_repo.save(experiment)

    personas = PersonaMatrix(experiment.traits).generate()

    tasks = []
    for persona in personas:
      persona.traits["_url"] = experiment.target_url

      for goal in experiment.goals:
        agent_run = AgentRun(
          experiment_id=experiment.id,
          persona=persona,
          goal=goal,
        )
        await self._run_repo.save(agent_run)

        tasks.append(
          asyncio.create_task(
            self._run_single_agent_bounded(experiment=experiment, agent_run=agent_run)
          )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check runs and step count to prevent zero-step completed experiments
    all_runs = await self._run_repo.find_by_experiment_id(experiment.id)
    total_snapshots = sum(len(r.event_snapshots) for r in all_runs)
    successful_runs = sum(1 for r in all_runs if r.success is True)

    has_error = False
    for i, result in enumerate(results):
      if isinstance(result, Exception):
        has_error = True
        logger.exception(
          "Agent task %d/%d failed for experiment %s",
          i + 1,
          len(results),
          experiment.id,
          exc_info=result,
        )

    if has_error or total_snapshots == 0 or successful_runs == 0:
      logger.warning(
        "Experiment %s failed: total_snapshots=%d successful_runs=%d/%d",
        experiment.id,
        total_snapshots,
        successful_runs,
        len(all_runs),
      )
      experiment.fail()
    else:
      experiment.mark_annotating()

    await self._experiment_repo.save(experiment)

  async def _run_single_agent_bounded(
    self,
    experiment: Experiment,
    agent_run: AgentRun,
  ) -> None:
    async with self._semaphore:
      logger.info(
        "active_browser_runs=1 queued_browser_runs=0 max_observed_concurrency=%d",
        settings.SIMULATION_MAX_CONCURRENCY,
      )
      await self._run_single_agent(experiment, agent_run)

  async def _run_single_agent(
    self,
    experiment: Experiment,
    agent_run: AgentRun,
  ) -> None:
    from app.infrastructure.event_bus import EventBus
    from app.infrastructure.repositories.sqlalchemy_agent_run_repository import (
      SQLAlchemyAgentRunRepository,
    )

    async with self._session_factory() as session:
      run_repo = SQLAlchemyAgentRunRepository(session)
      event_bus = EventBus(ws_manager=self._ws_manager, agent_run_repo=run_repo)

      agent_run.start()
      await run_repo.save(agent_run)

      async def _emit_snapshot(snapshot: EventSnapshot) -> None:
        await event_bus.emit(experiment.id, agent_run.id, snapshot)

      try:
        success = await self._agent.run(
          agent_run=agent_run,
          on_snapshot=_emit_snapshot,
        )
        agent_run.complete(success=success)
      except Exception as exc:
        logger.exception(
          "AgentRun %s failed (experiment=%s goal=%r): %s",
          agent_run.id,
          experiment.id,
          agent_run.goal,
          exc,
        )
        agent_run.fail()
        raise
      finally:
        await run_repo.save(agent_run)
