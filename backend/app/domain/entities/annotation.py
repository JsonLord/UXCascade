from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class Issue(BaseModel):
  """
  A usability issue. Output of the Issue Detector conforming to the UPT taxonomy.
  """

  model_config = ConfigDict(frozen=True)

  id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  type: str  # e.g. "scroll_incorrect_area"
  element: str  # affected UI element (CSS selector or description)
  reason: str
  fix: str
  upt_codes: list[str]  # e.g. ["A1", "C2"]
  upt_explanation: str
  severity: int  # Nielsen severity: 0–4


class StepAnnotation(BaseModel):
  """
  Annotation result for a single step.
  Combines the Tagging Agent's tags and the Issue Detector's issues.
  """

  model_config = ConfigDict(frozen=True)

  agent_run_id: str
  step: int
  tags: list[str] = Field(default_factory=list)
  issues: list[Issue] = Field(default_factory=list)


class TraitDistribution(BaseModel):
  """Distribution of success rate and issues for a specific trait value."""

  model_config = ConfigDict(frozen=True)

  trait_key: str
  trait_value: str
  agent_count: int
  success_rate: float
  issues: list[Issue] = Field(default_factory=list)


class GoalSummary(BaseModel):
  """
  Aggregated summary of all agent runs for a single goal.
  Serves as the entry point for the analysis view.
  """

  model_config = ConfigDict(frozen=True)

  experiment_id: str
  goal: str
  agent_count: int
  success_count: int
  success_rate: float
  issue_count: int
  trait_distributions: list[TraitDistribution] = Field(default_factory=list)
