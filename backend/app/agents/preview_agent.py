from __future__ import annotations

import uuid

from app.agents.base import BaseAgent
from app.agents.ports import BrowserPort
from app.agents.simulation_agent import BEHAVIOR_PROMPT
from app.domain.entities.experiment import AgentRun
from app.domain.entities.fix import EvaluationResult
from app.domain.value_objects.action import Action


class PreviewAgent(BaseAgent):
  """
  Agent that re-simulates a single step using a fixed HTML snapshot and
  evaluates whether the issue has been resolved.

  Design decisions (paper 5.1.3 / Appendix C.4):
    LLM sycophancy mitigation:
      Rather than asking the LLM directly whether the fix is good, the agent
      re-executes the next action and compares whether it changed.
      The primary basis for evaluation is the action comparison,
      not an LLM-generated summary.

    LLM: claude-sonnet-4-6, temperature=0
    Constraint: Limited to re-simulation of a single agent at a single step
  """

  _SUMMARY_SYSTEM = (
    "You are a UX evaluation assistant. Provide concise, factual summaries."
  )

  def __init__(self, browser_port: BrowserPort) -> None:
    self._browser = browser_port

  async def run(
    self,
    fix_id: str,
    agent_run: AgentRun,
    step: int,
    fixed_html: str,
  ) -> EvaluationResult:
    """
    Re-execute the given step with the fixed HTML and return an EvaluationResult
    comparing it against the original action.

    Parameters
    ----------
    fix_id:
        ID of the Fix being evaluated
    agent_run:
        The original simulation run (holds prompt history, persona, and snapshots)
    step:
        Step number to re-simulate
    fixed_html:
        HTML with EditorAgent-generated patches already applied via apply_patches()

    Returns
    -------
    EvaluationResult
        Evaluation result containing action_changed, issue_resolved, and
        before/after action comparison
    """
    original_snapshot = agent_run.get_snapshot_at_step(step)
    if original_snapshot is None:
      raise ValueError(f"Step {step} not found in agent_run {agent_run.id}")
    original_action = original_snapshot.action

    behavior_prompt = BEHAVIOR_PROMPT.format(persona=agent_run.persona.to_text())
    prompt_history = agent_run.get_prompt_history()

    # Re-run one step using the fixed snapshot via browser-use
    re_sim_step = await self._browser.run_single_step_with_html(
      fixed_html=fixed_html,
      prompt_history=prompt_history,
      persona=agent_run.persona,
      behavior_prompt=behavior_prompt,
    )

    new_action = Action(
      type=re_sim_step.action_type,
      selector=re_sim_step.action_selector,
      value=re_sim_step.action_value,
    )

    # Determine whether the action changed (action_changed is the primary indicator of issue_resolved)
    action_changed = original_action != new_action
    issue_reason = ""
    if original_snapshot.errors:
      issue_reason = "; ".join(original_snapshot.errors)

    # Generate a natural-language summary (used as supplementary information)
    summary = await self._generate_summary(
      original_action=original_action,
      new_action=new_action,
      issue_reason=issue_reason,
    )

    return EvaluationResult(
      id=str(uuid.uuid4()),
      fix_id=fix_id,
      agent_run_id=agent_run.id,
      step=step,
      action_changed=action_changed,
      issue_resolved=action_changed,  # Action change is used as the resolution indicator
      summary=summary,
      before_action=original_action,
      after_action=new_action,
    )

  async def _generate_summary(
    self,
    original_action: Action,
    new_action: Action,
    issue_reason: str,
  ) -> str:
    """Generate a natural-language summary from the before/after action comparison."""
    prompt = (
      f"Original issue: {issue_reason}\n"
      f"Action before fix: {original_action.model_dump()}\n"
      f"Action after fix: {new_action.model_dump()}\n\n"
      "Briefly describe the effect of the fix in 1-2 sentences."
    )
    return await self._call(
      system=self._SUMMARY_SYSTEM,
      user=prompt,
      temperature=0.0,
    )
