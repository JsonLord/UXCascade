from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.action import Action, TabMetadata


class EventSnapshot(BaseModel):
  """
  An event snapshot emitted at each simulation step.
  An immutable record containing perception, reasoning, action, and errors.
  """

  model_config = ConfigDict(frozen=True)

  agent_run_id: str
  step: int
  timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

  # Perception
  raw_html: str
  screenshot: str  # base64 PNG
  tab_metadata: TabMetadata

  # Reasoning
  reasoning: str  # think-aloud text
  prompt: str  # full prompt sent to the LLM

  # Action
  action: Action
  action_result: str

  # Errors
  errors: list[str] = Field(default_factory=list)
