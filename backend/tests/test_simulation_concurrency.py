import anyio
import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.config import settings
from app.infrastructure.orchestration.simulation_runner import SimulationRunner
from app.domain.entities.experiment import Experiment, ExperimentStatus
from app.domain.entities.snapshot import EventSnapshot
from app.domain.value_objects.persona import TraitConfig
from app.domain.value_objects.action import Action, TabMetadata


def test_simulation_concurrency_bounded():
  async def run_test():
    settings.SIMULATION_MAX_CONCURRENCY = 2

    active_count = 0
    max_active = 0
    lock = asyncio.Lock()

    async def mock_run_agent(agent_run, on_snapshot):
      nonlocal active_count, max_active
      async with lock:
        active_count += 1
        if active_count > max_active:
          max_active = active_count

      # Emit mock snapshot
      snap = EventSnapshot(
        agent_run_id=agent_run.id,
        step=1,
        raw_html="<html></html>",
        screenshot="",
        tab_metadata=TabMetadata(url="https://example.com", title="Example"),
        reasoning="Exploring",
        prompt="",
        action=Action(type="navigate", value="https://example.com"),
        action_result="success",
        errors=[],
      )
      await on_snapshot(snap)

      await asyncio.sleep(0.05)
      async with lock:
        active_count -= 1
      return True

    sim_agent = MagicMock()
    sim_agent.run = AsyncMock(side_effect=mock_run_agent)

    exp_repo = AsyncMock()

    # Mock run_repo to return runs with event_snapshots
    mock_run = MagicMock()
    mock_run.success = True
    mock_run.event_snapshots = [1]
    run_repo = AsyncMock()
    run_repo.find_by_experiment_id.return_value = [mock_run]

    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock()
    session_factory.return_value.__aexit__ = AsyncMock()
    ws_manager = AsyncMock()

    runner = SimulationRunner(
      simulation_agent=sim_agent,
      experiment_repo=exp_repo,
      agent_run_repo=run_repo,
      session_factory=session_factory,
      ws_manager=ws_manager,
    )

    exp = Experiment(
      id="test-exp-concurrency",
      name="Concurrency Test",
      target_url="https://example.com",
      status=ExperimentStatus.CREATED,
      traits=[TraitConfig(name="T1", key="t1", values=["v1", "v2", "v3", "v4"])],
      goals=["G1", "G2"],
    )

    await runner.run(exp)

    assert max_active <= 2
    assert exp.status in (ExperimentStatus.ANNOTATING, ExperimentStatus.COMPLETED)

  anyio.run(run_test)
