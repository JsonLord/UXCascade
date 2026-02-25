from __future__ import annotations

from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import models


async def create_experiment(
  session: AsyncSession,
  *,
  name: str,
  target_url: str,
  status: str = "created",
  traits: list[dict[str, Any]] | None = None,
  goals: list[str] | None = None,
) -> models.Experiment:
  experiment = models.Experiment(
    name=name,
    target_url=target_url,
    status=status,
  )
  session.add(experiment)
  await session.flush()

  trait_rows = []
  for trait in traits or []:
    trait_rows.append(
      models.TraitConfig(
        experiment_id=experiment.id,
        name=trait["name"],
        key=trait["key"],
        values=trait["values"],
      )
    )

  goal_rows = []
  for goal in goals or []:
    goal_rows.append(models.ExperimentGoal(experiment_id=experiment.id, goal=goal))

  session.add_all(trait_rows + goal_rows)
  await session.commit()
  await session.refresh(experiment)
  return experiment


async def list_experiments(session: AsyncSession) -> list[dict[str, Any]]:
  agent_counts = (
    select(
      models.AgentRun.experiment_id,
      func.count(models.AgentRun.id).label("agent_count"),
    )
    .group_by(models.AgentRun.experiment_id)
    .subquery()
  )

  stmt = (
    select(
      models.Experiment,
      func.coalesce(agent_counts.c.agent_count, 0),
    )
    .outerjoin(agent_counts, models.Experiment.id == agent_counts.c.experiment_id)
    .order_by(models.Experiment.created_at.desc())
  )
  rows = (await session.execute(stmt)).all()

  results = []
  for experiment, agent_count in rows:
    results.append(
      {
        "id": str(experiment.id),
        "name": experiment.name,
        "target_url": experiment.target_url,
        "status": experiment.status,
        "agent_count": agent_count,
        "created_at": experiment.created_at,
        "updated_at": experiment.updated_at,
      }
    )
  return results


async def get_experiment(
  session: AsyncSession, experiment_id: str
) -> dict[str, Any] | None:
  stmt = select(models.Experiment).where(models.Experiment.id == experiment_id)
  experiment = (await session.execute(stmt)).scalar_one_or_none()
  if not experiment:
    return None

  agent_count_stmt = select(func.count(models.AgentRun.id)).where(
    models.AgentRun.experiment_id == experiment.id
  )
  agent_count = (await session.execute(agent_count_stmt)).scalar_one()

  traits_stmt = select(models.TraitConfig).where(
    models.TraitConfig.experiment_id == experiment.id
  )
  goals_stmt = select(models.ExperimentGoal).where(
    models.ExperimentGoal.experiment_id == experiment.id
  )

  traits = (await session.execute(traits_stmt)).scalars().all()
  goals = (await session.execute(goals_stmt)).scalars().all()

  return {
    "id": str(experiment.id),
    "name": experiment.name,
    "target_url": experiment.target_url,
    "status": experiment.status,
    "agent_count": agent_count,
    "traits": [{"name": t.name, "key": t.key, "values": t.values} for t in traits],
    "goals": [g.goal for g in goals],
    "created_at": experiment.created_at,
    "updated_at": experiment.updated_at,
  }


async def update_experiment(
  session: AsyncSession,
  *,
  experiment_id: str,
  name: str | None = None,
  target_url: str | None = None,
  status: str | None = None,
  traits: list[dict[str, Any]] | None = None,
  goals: list[str] | None = None,
) -> dict[str, Any] | None:
  stmt = select(models.Experiment).where(models.Experiment.id == experiment_id)
  experiment = (await session.execute(stmt)).scalar_one_or_none()
  if not experiment:
    return None

  if name is not None:
    experiment.name = name
  if target_url is not None:
    experiment.target_url = target_url
  if status is not None:
    experiment.status = status

  if traits is not None:
    await session.execute(
      delete(models.TraitConfig).where(
        models.TraitConfig.experiment_id == experiment.id
      )
    )
    session.add_all(
      [
        models.TraitConfig(
          experiment_id=experiment.id,
          name=trait["name"],
          key=trait["key"],
          values=trait["values"],
        )
        for trait in traits
      ]
    )

  if goals is not None:
    await session.execute(
      delete(models.ExperimentGoal).where(
        models.ExperimentGoal.experiment_id == experiment.id
      )
    )
    session.add_all(
      [models.ExperimentGoal(experiment_id=experiment.id, goal=goal) for goal in goals]
    )

  await session.commit()
  return await get_experiment(session, experiment_id)


async def delete_experiment(session: AsyncSession, experiment_id: str) -> bool:
  stmt = select(models.Experiment.id).where(models.Experiment.id == experiment_id)
  exists = (await session.execute(stmt)).scalar_one_or_none()
  if not exists:
    return False
  await session.execute(
    delete(models.Experiment).where(models.Experiment.id == experiment_id)
  )
  await session.commit()
  return True


async def list_goal_summaries(
  session: AsyncSession, experiment_id: str
) -> list[dict[str, Any]]:
  stmt = select(models.GoalSummary).where(
    models.GoalSummary.experiment_id == experiment_id
  )
  summaries = (await session.execute(stmt)).scalars().all()
  return [
    {
      "goal": s.goal,
      "agent_count": s.agent_count,
      "success_count": s.success_count,
      "success_rate": float(s.success_rate),
      "issue_count": s.issue_count,
    }
    for s in summaries
  ]


async def list_trait_distributions(
  session: AsyncSession, experiment_id: str, goal: str
) -> list[dict[str, Any]]:
  summary_stmt = select(models.GoalSummary).where(
    models.GoalSummary.experiment_id == experiment_id,
    models.GoalSummary.goal == goal,
  )
  summary = (await session.execute(summary_stmt)).scalar_one_or_none()
  if not summary:
    return []

  stmt = (
    select(models.TraitDistribution, models.Issue)
    .select_from(models.TraitDistribution)
    .outerjoin(
      models.trait_distribution_issues,
      models.trait_distribution_issues.c.trait_distribution_id
      == models.TraitDistribution.id,
    )
    .outerjoin(
      models.Issue,
      models.Issue.id == models.trait_distribution_issues.c.issue_id,
    )
    .where(models.TraitDistribution.goal_summary_id == summary.id)
    .order_by(models.TraitDistribution.trait_key, models.TraitDistribution.trait_value)
  )
  rows = (await session.execute(stmt)).all()

  results: dict[str, dict[str, Any]] = {}
  for dist, issue in rows:
    key = str(dist.id)
    if key not in results:
      results[key] = {
        "trait_key": dist.trait_key,
        "trait_value": dist.trait_value,
        "agent_count": dist.agent_count,
        "success_rate": float(dist.success_rate),
        "issues": [],
      }

    if issue is not None:
      results[key]["issues"].append(
        {
          "id": str(issue.id),
          "type": issue.type,
          "element": issue.element,
          "reason": issue.reason,
          "fix": issue.fix,
          "upt_codes": issue.upt_codes,
          "upt_explanation": issue.upt_explanation,
          "severity": issue.severity,
          "agent_run_id": str(issue.agent_run_id),
          "step": issue.step,
          "goal": issue.goal,
        }
      )

  return list(results.values())


async def list_issues(
  session: AsyncSession,
  *,
  experiment_id: str,
  goal: str | None = None,
  trait_key: str | None = None,
  trait_value: str | None = None,
  upt_category: str | None = None,
) -> list[dict[str, Any]]:
  stmt = select(models.Issue).where(models.Issue.experiment_id == experiment_id)

  if goal:
    stmt = stmt.where(models.Issue.goal == goal)

  if trait_key and trait_value:
    stmt = stmt.join(
      models.AgentRun, models.AgentRun.id == models.Issue.agent_run_id
    ).where(models.AgentRun.persona_traits[trait_key].astext == trait_value)

  if upt_category:
    stmt = stmt.where(models.Issue.upt_codes.any(f"{upt_category}%"))

  stmt = stmt.order_by(models.Issue.severity.desc())
  issues = (await session.execute(stmt)).scalars().all()

  return [
    {
      "id": str(issue.id),
      "type": issue.type,
      "element": issue.element,
      "reason": issue.reason,
      "fix": issue.fix,
      "upt_codes": issue.upt_codes,
      "upt_explanation": issue.upt_explanation,
      "severity": issue.severity,
      "agent_run_id": str(issue.agent_run_id),
      "step": issue.step,
      "goal": issue.goal,
    }
    for issue in issues
  ]


async def get_issue_detail(
  session: AsyncSession, *, experiment_id: str, issue_id: str
) -> dict[str, Any] | None:
  issue_stmt = select(models.Issue).where(
    models.Issue.experiment_id == experiment_id,
    models.Issue.id == issue_id,
  )
  issue = (await session.execute(issue_stmt)).scalar_one_or_none()
  if not issue:
    return None

  snapshot_stmt = select(models.EventSnapshot).where(
    models.EventSnapshot.agent_run_id == issue.agent_run_id,
    models.EventSnapshot.step == issue.step,
  )
  snapshot = (await session.execute(snapshot_stmt)).scalar_one_or_none()

  if snapshot:
    snapshot_payload = {
      "step": snapshot.step,
      "screenshot": snapshot.screenshot,
      "reasoning": snapshot.reasoning,
      "raw_html": snapshot.raw_html,
    }
  else:
    snapshot_payload = None

  surrounding_stmt = (
    select(models.EventSnapshot)
    .where(
      models.EventSnapshot.agent_run_id == issue.agent_run_id,
      models.EventSnapshot.step >= issue.step - 2,
      models.EventSnapshot.step <= issue.step + 2,
    )
    .order_by(models.EventSnapshot.step)
  )
  surrounding = (await session.execute(surrounding_stmt)).scalars().all()
  surrounding_payload = [
    {
      "step": s.step,
      "reasoning": s.reasoning,
      "action": s.action,
    }
    for s in surrounding
  ]

  return {
    "issue": {
      "id": str(issue.id),
      "type": issue.type,
      "element": issue.element,
      "reason": issue.reason,
      "fix": issue.fix,
      "upt_codes": issue.upt_codes,
      "upt_explanation": issue.upt_explanation,
      "severity": issue.severity,
      "agent_run_id": str(issue.agent_run_id),
      "step": issue.step,
      "goal": issue.goal,
    },
    "snapshot": snapshot_payload,
    "surrounding_steps": surrounding_payload,
  }


async def create_fix(
  session: AsyncSession,
  *,
  experiment_id: str,
  issue_id: str,
  instruction: str,
  status: str,
  notes: str,
  patches: list[dict[str, Any]],
) -> models.Fix:
  fix = models.Fix(
    experiment_id=experiment_id,
    issue_id=issue_id,
    instruction=instruction,
    status=status,
    notes=notes,
  )
  session.add(fix)
  await session.flush()

  patch_rows = [
    models.HtmlPatch(
      fix_id=fix.id,
      selector=patch["selector"],
      action=patch["action"],
      value=patch.get("value"),
      name=patch.get("name"),
      rationale=patch["rationale"],
    )
    for patch in patches
  ]
  session.add_all(patch_rows)
  await session.commit()
  await session.refresh(fix)
  return fix


async def list_fixes(session: AsyncSession, experiment_id: str) -> list[dict[str, Any]]:
  stmt = select(models.Fix).where(models.Fix.experiment_id == experiment_id)
  fixes = (await session.execute(stmt)).scalars().all()
  return [
    {
      "id": str(fix.id),
      "experiment_id": str(fix.experiment_id),
      "issue_id": str(fix.issue_id),
      "instruction": fix.instruction,
      "status": fix.status,
      "notes": fix.notes,
      "created_at": fix.created_at,
    }
    for fix in fixes
  ]


async def get_fix_detail(
  session: AsyncSession, *, experiment_id: str, fix_id: str
) -> dict[str, Any] | None:
  stmt = select(models.Fix).where(
    models.Fix.experiment_id == experiment_id,
    models.Fix.id == fix_id,
  )
  fix = (await session.execute(stmt)).scalar_one_or_none()
  if not fix:
    return None

  patches_stmt = select(models.HtmlPatch).where(models.HtmlPatch.fix_id == fix.id)
  evaluations_stmt = select(models.EvaluationResult).where(
    models.EvaluationResult.fix_id == fix.id
  )
  patches = (await session.execute(patches_stmt)).scalars().all()
  evaluations = (await session.execute(evaluations_stmt)).scalars().all()

  return {
    "fix": {
      "id": str(fix.id),
      "experiment_id": str(fix.experiment_id),
      "issue_id": str(fix.issue_id),
      "instruction": fix.instruction,
      "status": fix.status,
      "notes": fix.notes,
      "created_at": fix.created_at,
    },
    "patches": [
      {
        "selector": patch.selector,
        "action": patch.action,
        "value": patch.value,
        "name": patch.name,
        "rationale": patch.rationale,
      }
      for patch in patches
    ],
    "evaluations": [
      {
        "id": str(ev.id),
        "fix_id": str(ev.fix_id),
        "agent_run_id": str(ev.agent_run_id),
        "step": ev.step,
        "action_changed": ev.action_changed,
        "issue_resolved": ev.issue_resolved,
        "summary": ev.summary,
        "before_action": ev.before_action,
        "after_action": ev.after_action,
        "created_at": ev.created_at,
      }
      for ev in evaluations
    ],
  }


async def create_evaluation(
  session: AsyncSession,
  *,
  fix_id: str,
  agent_run_id: str,
  step: int,
  action_changed: bool,
  issue_resolved: bool | None,
  summary: str,
  before_action: dict,
  after_action: dict,
) -> models.EvaluationResult:
  evaluation = models.EvaluationResult(
    fix_id=fix_id,
    agent_run_id=agent_run_id,
    step=step,
    action_changed=action_changed,
    issue_resolved=issue_resolved,
    summary=summary,
    before_action=before_action,
    after_action=after_action,
  )
  session.add(evaluation)
  await session.commit()
  await session.refresh(evaluation)
  return evaluation


async def get_issue_by_id(
  session: AsyncSession, issue_id: str
) -> models.Issue | None:
  return (
    await session.execute(select(models.Issue).where(models.Issue.id == issue_id))
  ).scalar_one_or_none()


def _url_label(url: str) -> str:
  """Extract only the path from a URL to use as a label."""
  try:
    parsed = urlparse(url)
    return parsed.path or url
  except Exception:
    return url


async def get_journeys(
  session: AsyncSession,
  experiment_id: str,
  mode: str = "page_navigation",
) -> dict[str, Any]:
  """
  Return agent journey data for the Sankey diagram.

  mode=page_navigation: Aggregates page transitions to generate nodes and links.
  mode=goal_steps:      Aggregates transitions by action type.
  """
  # Fetch AgentRun IDs for the experiment
  run_ids = (
    (
      await session.execute(
        select(models.AgentRun.id).where(
          models.AgentRun.experiment_id == experiment_id
        )
      )
    )
    .scalars()
    .all()
  )
  if not run_ids:
    return {"nodes": [], "links": []}

  # Fetch EventSnapshots ordered by run and step
  rows = (
    (
      await session.execute(
        select(
          models.EventSnapshot.agent_run_id,
          models.EventSnapshot.step,
          models.EventSnapshot.tab_metadata,
          models.EventSnapshot.action,
        )
        .where(models.EventSnapshot.agent_run_id.in_(run_ids))
        .order_by(
          models.EventSnapshot.agent_run_id,
          models.EventSnapshot.step,
        )
      )
    )
    .all()
  )

  if mode == "goal_steps":
    # Use action type as node and aggregate transitions
    key_fn = lambda r: (r.action or {}).get("type", "unknown")  # noqa: E731
  else:
    # Default: use page URL as node
    key_fn = lambda r: (r.tab_metadata or {}).get("url", "")  # noqa: E731

  # Build node key sequences per run
  runs: dict[str, list[str]] = defaultdict(list)
  for row in rows:
    runs[str(row.agent_run_id)].append(key_fn(row))

  # Count consecutive distinct node pairs as links
  link_counts: dict[tuple[str, str], int] = defaultdict(int)
  for seq in runs.values():
    for i in range(len(seq) - 1):
      src, tgt = seq[i], seq[i + 1]
      if src != tgt:
        link_counts[(src, tgt)] += 1

  node_ids: set[str] = set()
  for src, tgt in link_counts:
    node_ids.add(src)
    node_ids.add(tgt)

  nodes = [
    {"id": nid, "label": _url_label(nid) if mode != "goal_steps" else nid}
    for nid in sorted(node_ids)
  ]
  links = [
    {"source": src, "target": tgt, "value": cnt}
    for (src, tgt), cnt in sorted(link_counts.items(), key=lambda x: -x[1])
  ]
  return {"nodes": nodes, "links": links}


async def get_agent_run_steps(
  session: AsyncSession,
  experiment_id: str,
) -> list[dict[str, Any]]:
  """
  Return agent runs and their step lists for the given experiment.

  Used to display individual agent reasoning traces for the Agent Journey tab
  (cf. Figure 1 in the paper).
  Each step includes a screenshot URL, reasoning text, and action information.
  """
  runs_stmt = (
    select(models.AgentRun)
    .where(models.AgentRun.experiment_id == experiment_id)
    .order_by(models.AgentRun.created_at)
  )
  runs = (await session.execute(runs_stmt)).scalars().all()
  if not runs:
    return []

  run_ids = [run.id for run in runs]

  steps_stmt = (
    select(models.EventSnapshot)
    .where(models.EventSnapshot.agent_run_id.in_(run_ids))
    .order_by(models.EventSnapshot.agent_run_id, models.EventSnapshot.step)
  )
  all_steps = (await session.execute(steps_stmt)).scalars().all()

  steps_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
  for snap in all_steps:
    action = snap.action or {}
    tab = snap.tab_metadata or {}
    steps_by_run[str(snap.agent_run_id)].append(
      {
        "step": snap.step,
        "screenshot": snap.screenshot,
        "reasoning": snap.reasoning,
        "action_type": action.get("type", ""),
        "action_value": action.get("value"),
        "tab_url": tab.get("url", ""),
        "tab_title": tab.get("title", ""),
      }
    )

  return [
    {
      "run_id": str(run.id),
      "goal": run.goal,
      "persona_traits": run.persona_traits or {},
      "status": run.status,
      "steps": steps_by_run.get(str(run.id), []),
    }
    for run in runs
  ]
