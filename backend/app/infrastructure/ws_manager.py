from __future__ import annotations

from fastapi import WebSocket

from app.infrastructure.event_bus import IWebSocketManager


class FastAPIWebSocketManager(IWebSocketManager):
  """
  Real-time notification manager using FastAPI WebSockets.

  Manages active WebSocket connections per experiment ID and
  delivers broadcast calls from EventBus to all connected clients.
  """

  def __init__(self) -> None:
    self._connections: dict[str, list[WebSocket]] = {}

  async def connect(self, experiment_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    self._connections.setdefault(experiment_id, []).append(websocket)

  def disconnect(self, experiment_id: str, websocket: WebSocket) -> None:
    conns = self._connections.get(experiment_id, [])
    if websocket in conns:
      conns.remove(websocket)

  async def broadcast(self, experiment_id: str, message: dict) -> None:
    dead: list[WebSocket] = []
    for ws in self._connections.get(experiment_id, []):
      try:
        await ws.send_json(message)
      except Exception:
        dead.append(ws)
    for ws in dead:
      self.disconnect(experiment_id, ws)


# Singleton shared across the entire application
ws_manager = FastAPIWebSocketManager()
