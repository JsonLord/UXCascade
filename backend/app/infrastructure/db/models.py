from __future__ import annotations

import uuid

from sqlalchemy import (
  Boolean,
  Column,
  DateTime,
  ForeignKey,
  Index,
  Integer,
  Numeric,
  SmallInteger,
  Table,
  Text,
  UniqueConstraint,
  func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.infrastructure.db.base import Base


class Experiment(Base):
  __tablename__ = "experiments"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(Text, nullable=False)
  target_url = Column(Text, nullable=False)
  status = Column(Text, nullable=False)
  created_at = Column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
  )

  __table_args__ = (
    Index("idx_experiments_status", "status"),
    Index("idx_experiments_created_at", "created_at"),
  )


class TraitConfig(Base):
  __tablename__ = "trait_configs"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  experiment_id = Column(
    UUID(as_uuid=True),
    ForeignKey("experiments.id", ondelete="CASCADE"),
    nullable=False,
  )
  name = Column(Text, nullable=False)
  key = Column(Text, nullable=False)
  values = Column(ARRAY(Text), nullable=False)

  __table_args__ = (
    UniqueConstraint(
      "experiment_id",
      "key",
      name="uq_trait_configs_experiment_key",
    ),
    Index("idx_trait_configs_experiment_id", "experiment_id"),
  )


class ExperimentGoal(Base):
  __tablename__ = "experiment_goals"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  experiment_id = Column(
    UUID(as_uuid=True),
    ForeignKey("experiments.id", ondelete="CASCADE"),
    nullable=False,
  )
  goal = Column(Text, nullable=False)

  __table_args__ = (
    UniqueConstraint(
      "experiment_id",
      "goal",
      name="uq_experiment_goals_experiment_goal",
    ),
    Index("idx_experiment_goals_experiment_id", "experiment_id"),
  )


class AgentRun(Base):
  __tablename__ = "agent_runs"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  experiment_id = Column(
    UUID(as_uuid=True),
    ForeignKey("experiments.id", ondelete="CASCADE"),
    nullable=False,
  )
  persona_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
  persona_traits = Column(JSONB, nullable=False)
  goal = Column(Text, nullable=False)
  status = Column(Text, nullable=False)
  success = Column(Boolean, nullable=True)
  created_at = Column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  completed_at = Column(DateTime(timezone=True), nullable=True)

  __table_args__ = (
    Index("idx_agent_runs_experiment_id", "experiment_id"),
    Index("idx_agent_runs_status", "status"),
    Index("idx_agent_runs_goal", "goal"),
    Index(
      "idx_agent_runs_persona_traits_gin",
      "persona_traits",
      postgresql_using="gin",
    ),
  )


class EventSnapshot(Base):
  __tablename__ = "event_snapshots"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  agent_run_id = Column(
    UUID(as_uuid=True),
    ForeignKey("agent_runs.id", ondelete="CASCADE"),
    nullable=False,
  )
  step = Column(Integer, nullable=False)
  timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  raw_html = Column(Text, nullable=False)
  screenshot = Column(Text, nullable=False)
  tab_metadata = Column(JSONB, nullable=False)
  reasoning = Column(Text, nullable=False)
  prompt = Column(Text, nullable=False)
  action = Column(JSONB, nullable=False)
  action_result = Column(Text, nullable=False)
  errors = Column(ARRAY(Text), nullable=False, server_default="{}")

  __table_args__ = (
    UniqueConstraint(
      "agent_run_id",
      "step",
      name="uq_event_snapshots_run_step",
    ),
    Index("idx_event_snapshots_agent_run_id", "agent_run_id"),
  )


class StepAnnotation(Base):
  __tablename__ = "step_annotations"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  agent_run_id = Column(
    UUID(as_uuid=True),
    ForeignKey("agent_runs.id", ondelete="CASCADE"),
    nullable=False,
  )
  step = Column(Integer, nullable=False)
  tags = Column(ARRAY(Text), nullable=False, server_default="{}")

  __table_args__ = (
    UniqueConstraint(
      "agent_run_id",
      "step",
      name="uq_step_annotations_run_step",
    ),
    Index("idx_step_annotations_agent_run_id", "agent_run_id"),
  )


class Issue(Base):
  __tablename__ = "issues"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  experiment_id = Column(
    UUID(as_uuid=True),
    ForeignKey("experiments.id", ondelete="CASCADE"),
    nullable=False,
  )
  agent_run_id = Column(
    UUID(as_uuid=True),
    ForeignKey("agent_runs.id", ondelete="CASCADE"),
    nullable=False,
  )
  step = Column(Integer, nullable=False)
  goal = Column(Text, nullable=False)
  type = Column(Text, nullable=False)
  element = Column(Text, nullable=False)
  reason = Column(Text, nullable=False)
  fix = Column(Text, nullable=False)
  upt_codes = Column(ARRAY(Text), nullable=False, server_default="{}")
  upt_explanation = Column(Text, nullable=False)
  severity = Column(SmallInteger, nullable=False)

  __table_args__ = (
    Index("idx_issues_experiment_id", "experiment_id"),
    Index("idx_issues_agent_run_id", "agent_run_id"),
    Index("idx_issues_goal", "goal"),
    Index("idx_issues_severity", "severity"),
    Index(
      "idx_issues_upt_codes_gin",
      "upt_codes",
      postgresql_using="gin",
    ),
  )


class GoalSummary(Base):
  __tablename__ = "goal_summaries"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  experiment_id = Column(
    UUID(as_uuid=True),
    ForeignKey("experiments.id", ondelete="CASCADE"),
    nullable=False,
  )
  goal = Column(Text, nullable=False)
  agent_count = Column(Integer, nullable=False)
  success_count = Column(Integer, nullable=False)
  success_rate = Column(Numeric(5, 4), nullable=False)
  issue_count = Column(Integer, nullable=False)

  __table_args__ = (
    UniqueConstraint(
      "experiment_id",
      "goal",
      name="uq_goal_summaries_experiment_goal",
    ),
    Index("idx_goal_summaries_experiment_id", "experiment_id"),
  )


class TraitDistribution(Base):
  __tablename__ = "trait_distributions"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  goal_summary_id = Column(
    UUID(as_uuid=True),
    ForeignKey("goal_summaries.id", ondelete="CASCADE"),
    nullable=False,
  )
  trait_key = Column(Text, nullable=False)
  trait_value = Column(Text, nullable=False)
  agent_count = Column(Integer, nullable=False)
  success_rate = Column(Numeric(5, 4), nullable=False)

  __table_args__ = (
    UniqueConstraint(
      "goal_summary_id",
      "trait_key",
      "trait_value",
      name="uq_trait_distributions_summary_key_value",
    ),
    Index("idx_trait_distributions_summary_id", "goal_summary_id"),
  )


trait_distribution_issues = Table(
  "trait_distribution_issues",
  Base.metadata,
  Column(
    "trait_distribution_id",
    UUID(as_uuid=True),
    ForeignKey("trait_distributions.id", ondelete="CASCADE"),
    primary_key=True,
  ),
  Column(
    "issue_id",
    UUID(as_uuid=True),
    ForeignKey("issues.id", ondelete="CASCADE"),
    primary_key=True,
  ),
)


class Fix(Base):
  __tablename__ = "fixes"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  experiment_id = Column(
    UUID(as_uuid=True),
    ForeignKey("experiments.id", ondelete="CASCADE"),
    nullable=False,
  )
  issue_id = Column(
    UUID(as_uuid=True),
    ForeignKey("issues.id", ondelete="CASCADE"),
    nullable=False,
  )
  instruction = Column(Text, nullable=False)
  status = Column(Text, nullable=False)
  notes = Column(Text, nullable=False, server_default="")
  created_at = Column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )

  __table_args__ = (
    Index("idx_fixes_experiment_id", "experiment_id"),
    Index("idx_fixes_issue_id", "issue_id"),
  )


class HtmlPatch(Base):
  __tablename__ = "html_patches"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  fix_id = Column(
    UUID(as_uuid=True),
    ForeignKey("fixes.id", ondelete="CASCADE"),
    nullable=False,
  )
  selector = Column(Text, nullable=False)
  action = Column(Text, nullable=False)
  value = Column(Text, nullable=True)
  name = Column(Text, nullable=True)
  rationale = Column(Text, nullable=False)

  __table_args__ = (Index("idx_html_patches_fix_id", "fix_id"),)


class EvaluationResult(Base):
  __tablename__ = "evaluation_results"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  fix_id = Column(
    UUID(as_uuid=True),
    ForeignKey("fixes.id", ondelete="CASCADE"),
    nullable=False,
  )
  agent_run_id = Column(
    UUID(as_uuid=True),
    ForeignKey("agent_runs.id", ondelete="CASCADE"),
    nullable=False,
  )
  step = Column(Integer, nullable=False)
  action_changed = Column(Boolean, nullable=False)
  issue_resolved = Column(Boolean, nullable=True)
  summary = Column(Text, nullable=False)
  before_action = Column(JSONB, nullable=False)
  after_action = Column(JSONB, nullable=False)
  created_at = Column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )

  __table_args__ = (
    Index("idx_evaluation_results_fix_id", "fix_id"),
    Index("idx_evaluation_results_agent_run_id", "agent_run_id"),
  )
