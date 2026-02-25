from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.snapshot import EventSnapshot
from app.domain.value_objects.enums import ExperimentStatus, RunStatus
from app.domain.value_objects.persona import Persona, TraitConfig


class AgentRun(BaseModel):
  """
  Record of a single agent execution. One run per persona × goal combination.
  Accumulates EventSnapshots during simulation.
  """

  model_config = ConfigDict(frozen=False)

  id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  experiment_id: str
  persona: Persona
  goal: str
  status: RunStatus = RunStatus.PENDING
  success: bool | None = None
  event_snapshots: list[EventSnapshot] = Field(default_factory=list)
  created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
  completed_at: datetime | None = None

  def start(self) -> None:
    self.status = RunStatus.RUNNING

  def complete(self, *, success: bool) -> None:
    self.status = RunStatus.COMPLETED
    self.success = success
    self.completed_at = datetime.now(timezone.utc)

  def fail(self) -> None:
    self.status = RunStatus.FAILED
    self.completed_at = datetime.now(timezone.utc)

  def add_snapshot(self, snapshot: EventSnapshot) -> None:
    self.event_snapshots.append(snapshot)

  def get_reasoning_steps(self) -> list[str]:
    """Returns the sequence of reasoning texts used as input to the annotation agent."""
    return [s.reasoning for s in self.event_snapshots]

  def get_snapshot_at_step(self, step: int) -> EventSnapshot | None:
    return next((s for s in self.event_snapshots if s.step == step), None)

  def get_prompt_history(self) -> list[dict]:
    """
    Prompt history for the PreviewAgent to reconstruct the original context.
    Each step's full prompt is listed as a user role message.
    """
    return [{"role": "user", "content": s.prompt} for s in self.event_snapshots]


class Experiment(BaseModel):
  """
  Experiment entity. Bundles a URL with persona traits and goals,
  and manages state transitions from simulation through annotation to completion.
  """

  model_config = ConfigDict(frozen=False)

  id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  name: str
  target_url: str
  status: ExperimentStatus = ExperimentStatus.CREATED
  traits: list[TraitConfig] = Field(default_factory=list)
  goals: list[str] = Field(default_factory=list)
  created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
  updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

  def _touch(self) -> None:
    self.updated_at = datetime.now(timezone.utc)

  def start(self) -> None:
    self.status = ExperimentStatus.RUNNING
    self._touch()

  def mark_annotating(self) -> None:
    self.status = ExperimentStatus.ANNOTATING
    self._touch()

  def complete(self) -> None:
    self.status = ExperimentStatus.COMPLETED
    self._touch()

  def fail(self) -> None:
    self.status = ExperimentStatus.FAILED
    self._touch()
