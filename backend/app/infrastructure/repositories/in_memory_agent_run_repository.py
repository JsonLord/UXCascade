from __future__ import annotations

from app.domain.entities.experiment import AgentRun
from app.domain.entities.snapshot import EventSnapshot
from app.domain.repositories.agent_run_repository import IAgentRunRepository


class InMemoryAgentRunRepository(IAgentRunRepository):
  """In-memory repository for development and testing."""

  def __init__(self) -> None:
    self._store: dict[str, AgentRun] = {}

  async def save(self, agent_run: AgentRun) -> None:
    self._store[agent_run.id] = agent_run

  async def find_by_id(self, agent_run_id: str) -> AgentRun | None:
    return self._store.get(agent_run_id)

  async def find_by_experiment_id(self, experiment_id: str) -> list[AgentRun]:
    return [r for r in self._store.values() if r.experiment_id == experiment_id]

  async def append_snapshot(self, agent_run_id: str, snapshot: EventSnapshot) -> None:
    run = self._store.get(agent_run_id)
    if run is not None:
      run.add_snapshot(snapshot)
