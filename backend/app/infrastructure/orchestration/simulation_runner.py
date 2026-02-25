from __future__ import annotations

import asyncio
import logging
from typing import Any

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
  Orchestrator that runs all agents associated with an experiment in parallel.

  Follows the SimulationRunner spec in design/architecture/data-flow.md:
    Uses PersonaMatrix.generate(traits) to produce all persona × goal combinations,
    then executes them concurrently via asyncio.gather().
    Each agent task has its own independent DB session to avoid session conflicts.
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
    self._run_repo = (
      agent_run_repo  # used for the initial save of pending runs (main session)
    )
    self._session_factory = session_factory
    self._ws_manager = ws_manager

  async def run(self, experiment: Experiment) -> None:
    """
    Run simulations for all persona × goal combinations in the experiment in parallel.

    Parameters
    ----------
    experiment:
        The experiment entity to execute
    """
    experiment.start()
    await self._experiment_repo.save(experiment)

    personas = PersonaMatrix(experiment.traits).generate()

    tasks = []
    for persona in personas:
      # Inject the URL into the persona so SimulationAgent can access it
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
            self._run_single_agent(experiment=experiment, agent_run=agent_run)
          )
        )

    # Run all agents in parallel (exceptions are captured via return_exceptions)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log any per-task exceptions
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

    if has_error:
      experiment.fail()
    else:
      experiment.mark_annotating()
    await self._experiment_repo.save(experiment)

  async def _run_single_agent(
    self,
    experiment: Experiment,
    agent_run: AgentRun,
  ) -> None:
    """
    Execute a single agent in its own independent DB session.

    Each task has its own session to avoid concurrent session conflicts.
    """
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
