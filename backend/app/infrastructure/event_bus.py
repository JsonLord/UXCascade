from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from app.domain.entities.snapshot import EventSnapshot
from app.domain.repositories.agent_run_repository import IAgentRunRepository


class IWebSocketManager(ABC):
  """Abstract interface for WebSocket broadcasting."""

  @abstractmethod
  async def broadcast(self, experiment_id: str, message: dict) -> None:
    """Send a message to all connected clients for the given experiment."""
    ...


class EventBus:
  """
  Event bus that mediates real-time notification of simulation progress.

  Injected into SimulationRunner as the on_snapshot callback. On each step it:
    1. Persists the EventSnapshot to the DB (AgentRunRepository)
    2. Notifies the frontend via WebSocket

  Follows the EventBus pattern described in design/agents/simulation.md.
  """

  def __init__(
    self,
    ws_manager: IWebSocketManager,
    agent_run_repo: IAgentRunRepository,
  ) -> None:
    self._ws = ws_manager
    self._repo = agent_run_repo

  async def emit(
    self,
    experiment_id: str,
    agent_run_id: str,
    snapshot: EventSnapshot,
  ) -> None:
    """
    Persist the snapshot to the DB and notify via WebSocket.

    Parameters
    ----------
    experiment_id:
        Routing key for WebSocket broadcast
    agent_run_id:
        ID of the AgentRun to append the snapshot to
    snapshot:
        The event snapshot to emit
    """
    # 1. Persist to DB first to prevent data loss from notification failures
    await self._repo.append_snapshot(agent_run_id, snapshot)

    # 2. Notify via WebSocket (only lightweight metadata is sent)
    await self._ws.broadcast(
      experiment_id,
      {
        "type": "agent_step",
        "agent_run_id": agent_run_id,
        "step": snapshot.step,
        "tab_url": snapshot.tab_metadata.url,
      },
    )


class InMemoryWebSocketManager(IWebSocketManager):
  """
  In-memory WebSocket manager for testing and development.
  Messages are enqueued but not actually sent.
  """

  def __init__(self) -> None:
    self._queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()

  async def broadcast(self, experiment_id: str, message: dict) -> None:
    await self._queue.put((experiment_id, message))

  async def drain(self) -> list[tuple[str, dict]]:
    """Drain the queue and return all messages (for use in tests)."""
    messages: list[tuple[str, dict]] = []
    while not self._queue.empty():
      messages.append(self._queue.get_nowait())
    return messages
