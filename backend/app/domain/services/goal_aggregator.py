from __future__ import annotations

from collections import defaultdict

from app.domain.entities.annotation import (
  GoalSummary,
  Issue,
  StepAnnotation,
  TraitDistribution,
)
from app.domain.entities.experiment import AgentRun, Experiment


class GoalAggregator:
  """
  Domain service that aggregates all AgentRun results and produces GoalSummary objects.

  Also generates TraitDistribution for trait-centric analysis,
  enabling quantification of which trait values caused users to encounter issues most.
  """

  def aggregate(
    self,
    experiment: Experiment,
    runs: list[AgentRun],
    annotations: dict[str, list[StepAnnotation]],
  ) -> list[GoalSummary]:
    """
    Generates a list of GoalSummary objects from the AgentRuns and annotations
    associated with an experiment.

    Parameters
    ----------
    experiment:
        The experiment entity to aggregate
    runs:
        All AgentRuns associated with the experiment
    annotations:
        Mapping of agent_run_id -> StepAnnotation[]
    """
    # Group AgentRuns by goal
    runs_by_goal: dict[str, list[AgentRun]] = defaultdict(list)
    for run in runs:
      runs_by_goal[run.goal].append(run)

    summaries: list[GoalSummary] = []
    for goal, goal_runs in runs_by_goal.items():
      summaries.append(
        self._summarize_goal(
          experiment_id=experiment.id,
          goal=goal,
          runs=goal_runs,
          annotations=annotations,
          trait_keys=[t.key for t in experiment.traits],
        )
      )

    return summaries

  def _summarize_goal(
    self,
    experiment_id: str,
    goal: str,
    runs: list[AgentRun],
    annotations: dict[str, list[StepAnnotation]],
    trait_keys: list[str],
  ) -> GoalSummary:
    agent_count = len(runs)
    success_count = sum(1 for r in runs if r.success is True)
    success_rate = success_count / agent_count if agent_count > 0 else 0.0

    all_issues: list[Issue] = []
    for run in runs:
      for annotation in annotations.get(run.id, []):
        all_issues.extend(annotation.issues)

    trait_distributions = self._compute_trait_distributions(
      runs=runs,
      annotations=annotations,
      trait_keys=trait_keys,
    )

    return GoalSummary(
      experiment_id=experiment_id,
      goal=goal,
      agent_count=agent_count,
      success_count=success_count,
      success_rate=success_rate,
      issue_count=len(all_issues),
      trait_distributions=trait_distributions,
    )

  def _compute_trait_distributions(
    self,
    runs: list[AgentRun],
    annotations: dict[str, list[StepAnnotation]],
    trait_keys: list[str],
  ) -> list[TraitDistribution]:
    """Computes the distribution for each trait key × trait value combination."""
    distributions: list[TraitDistribution] = []

    for trait_key in trait_keys:
      # Group by trait value
      by_value: dict[str, list[AgentRun]] = defaultdict(list)
      for run in runs:
        value = run.persona.traits.get(trait_key)
        if value is not None:
          by_value[value].append(run)

      for trait_value, value_runs in by_value.items():
        count = len(value_runs)
        success_count = sum(1 for r in value_runs if r.success is True)
        rate = success_count / count if count > 0 else 0.0

        issues: list[Issue] = []
        for run in value_runs:
          for annotation in annotations.get(run.id, []):
            issues.extend(annotation.issues)

        distributions.append(
          TraitDistribution(
            trait_key=trait_key,
            trait_value=trait_value,
            agent_count=count,
            success_rate=rate,
            issues=issues,
          )
        )

    return distributions
