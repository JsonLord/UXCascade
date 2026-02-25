from __future__ import annotations

from app.agents.editor_agent import EditorAgent
from app.agents.preview_agent import PreviewAgent
from app.domain.entities.fix import EvaluationResult, Fix
from app.domain.repositories.agent_run_repository import IAgentRunRepository
from app.domain.repositories.fix_repository import IFixRepository
from app.utils.dom_patcher import apply_patches


class RefinementService:
  """
  Application service that orchestrates Fix and Evaluation use cases.

  Design decisions (paper 5.1.3):
    Editor Agent generates HTML patches → apply_patches() applies them to the DOM
    → Preview Agent runs a one-step re-simulation → EvaluationResult is produced
  """

  def __init__(
    self,
    editor_agent: EditorAgent,
    preview_agent: PreviewAgent,
    agent_run_repo: IAgentRunRepository,
    fix_repo: IFixRepository,
  ) -> None:
    self._editor = editor_agent
    self._preview = preview_agent
    self._run_repo = agent_run_repo
    self._fix_repo = fix_repo

  async def create_fix(
    self,
    experiment_id: str,
    issue_id: str,
    agent_run_id: str,
    step: int,
    instruction: str,
    target: str = "",
    policy: str = "",
  ) -> Fix:
    """
    Generates a Fix from a natural-language fix instruction and saves it to the DB.

    Parameters
    ----------
    experiment_id:
        ID of the target experiment
    issue_id:
        ID of the Issue to fix
    agent_run_id:
        ID of the AgentRun from which to retrieve the HTML snapshot
    step:
        Step number to fix
    instruction:
        Natural-language fix instruction
    target:
        Target specification such as a CSS selector (if omitted, the LLM decides automatically)
    policy:
        Optional constraints
    """
    agent_run = await self._run_repo.find_by_id(agent_run_id)
    if agent_run is None:
      raise ValueError(f"AgentRun {agent_run_id} not found")

    snapshot = agent_run.get_snapshot_at_step(step)
    if snapshot is None:
      raise ValueError(f"Step {step} not found in AgentRun {agent_run_id}")
    if not snapshot.raw_html:
      raise ValueError(
        f"HTML snapshot for step {step} was not captured during simulation. "
        "Re-run the simulation to collect HTML snapshots."
      )

    editor_result = await self._editor.run(
      html=snapshot.raw_html,
      target=target,
      instruction=instruction,
      policy=policy,
    )

    fix = Fix(
      experiment_id=experiment_id,
      issue_id=issue_id,
      instruction=instruction,
    )
    fix.apply_editor_result(
      status=editor_result.status,
      patches=editor_result.patches,
      notes=editor_result.notes,
    )
    await self._fix_repo.save_fix(fix)
    return fix

  async def evaluate_fix(
    self,
    fix_id: str,
    agent_run_id: str,
    step: int,
  ) -> EvaluationResult:
    """
    Evaluates a Fix. Runs a one-step re-simulation with the patched HTML and
    compares whether the action changed to produce an EvaluationResult.

    To guard against sycophancy, the LLM is not asked directly "did it improve?"
    but instead the actual action change is used as the basis for judgment.
    """
    fix = await self._fix_repo.find_fix_by_id(fix_id)
    if fix is None:
      raise ValueError(f"Fix {fix_id} not found")

    agent_run = await self._run_repo.find_by_id(agent_run_id)
    if agent_run is None:
      raise ValueError(f"AgentRun {agent_run_id} not found")

    snapshot = agent_run.get_snapshot_at_step(step)
    if snapshot is None:
      raise ValueError(f"Step {step} not found in AgentRun {agent_run_id}")

    # Apply patches to the HTML to produce the fixed snapshot
    fixed_html = apply_patches(snapshot.raw_html, fix.patches)

    evaluation = await self._preview.run(
      fix_id=fix_id,
      agent_run=agent_run,
      step=step,
      fixed_html=fixed_html,
    )

    await self._fix_repo.save_evaluation(evaluation)
    return evaluation
