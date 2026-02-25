from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TraitConfigIn(BaseModel):
  name: str
  key: str
  values: list[str]


class ExperimentCreate(BaseModel):
  name: str
  target_url: str
  traits: list[TraitConfigIn] = Field(default_factory=list)
  goals: list[str] = Field(default_factory=list)


class ExperimentUpdate(BaseModel):
  name: str | None = None
  target_url: str | None = None
  status: (
    Literal[
      "created",
      "running",
      "annotating",
      "completed",
      "failed",
    ]
    | None
  ) = None
  traits: list[TraitConfigIn] | None = None
  goals: list[str] | None = None


class ExperimentSummary(BaseModel):
  id: str
  name: str
  target_url: str
  status: str
  agent_count: int
  created_at: datetime
  updated_at: datetime


class ExperimentDetail(BaseModel):
  id: str
  name: str
  target_url: str
  status: str
  agent_count: int
  traits: list[TraitConfigIn]
  goals: list[str]
  created_at: datetime
  updated_at: datetime


class IssueSummary(BaseModel):
  id: str
  type: str
  element: str
  reason: str
  fix: str
  upt_codes: list[str]
  upt_explanation: str
  severity: int
  agent_run_id: str
  step: int
  goal: str


class IssueDetail(BaseModel):
  issue: IssueSummary
  snapshot: dict
  surrounding_steps: list[dict]


class GoalSummary(BaseModel):
  goal: str
  agent_count: int
  success_count: int
  success_rate: float
  issue_count: int


class TraitDistribution(BaseModel):
  trait_key: str
  trait_value: str
  agent_count: int
  success_rate: float
  issues: list[IssueSummary] = Field(default_factory=list)


class FixPatchIn(BaseModel):
  selector: str
  action: str
  value: str | None = None
  name: str | None = None
  rationale: str


class FixCreate(BaseModel):
  """Calls the Editor Agent to automatically generate patches (request body for POST /fixes)."""

  issue_id: str
  instruction: str
  snapshot_step: int | None = None  # If omitted, uses Issue.step


class FixSummary(BaseModel):
  id: str
  experiment_id: str
  issue_id: str
  instruction: str
  status: str
  notes: str
  created_at: datetime


class FixDetail(BaseModel):
  fix: FixSummary
  patches: list[FixPatchIn]
  evaluations: list[dict]


class FixAgentResponse(BaseModel):
  """Response for POST /fixes (includes EditorAgent output)."""

  id: str
  status: str
  patches: list[FixPatchIn]
  notes: str


class EvaluationCreate(BaseModel):
  agent_run_id: str
  step: int
  action_changed: bool
  issue_resolved: bool | None
  summary: str
  before_action: dict
  after_action: dict


class EvaluationSummary(BaseModel):
  id: str
  fix_id: str
  agent_run_id: str
  step: int
  action_changed: bool
  issue_resolved: bool | None
  summary: str
  before_action: dict
  after_action: dict
  created_at: datetime


# ── Runs ─────────────────────────────────────────────────────────────────────


class RunResponse(BaseModel):
  message: str
  experiment_id: str


# ── Journeys ─────────────────────────────────────────────────────────────────


class JourneyNode(BaseModel):
  id: str
  label: str


class JourneyLink(BaseModel):
  source: str
  target: str
  value: int


class JourneyResponse(BaseModel):
  nodes: list[JourneyNode]
  links: list[JourneyLink]
