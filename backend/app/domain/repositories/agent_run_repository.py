from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.experiment import AgentRun
from app.domain.entities.snapshot import EventSnapshot


class IAgentRunRepository(ABC):
  """
  Repository interface (Port) for the AgentRun aggregate.
  This repository is also responsible for appending EventSnapshots.
  """

  @abstractmethod
  async def save(self, agent_run: AgentRun) -> None:
    """Save an AgentRun (create or update)."""
    ...

  @abstractmethod
  async def find_by_id(self, agent_run_id: str) -> AgentRun | None:
    """Retrieve an AgentRun by ID."""
    ...

  @abstractmethod
  async def find_by_experiment_id(self, experiment_id: str) -> list[AgentRun]:
    """Retrieve all AgentRuns associated with an experiment ID."""
    ...

  @abstractmethod
  async def append_snapshot(self, agent_run_id: str, snapshot: EventSnapshot) -> None:
    """Append an EventSnapshot to an AgentRun."""
    ...
