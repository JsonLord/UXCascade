from __future__ import annotations

import asyncio

from app.agents.issue_detector_agent import IssueDetectorAgent
from app.agents.tagging_agent import TaggingAgent
from app.domain.entities.annotation import StepAnnotation
from app.domain.entities.experiment import AgentRun
from app.domain.repositories.annotation_repository import IAnnotationRepository


class AnnotationService:
  """
  Application service that orchestrates the annotation pipeline use cases.

  Runs TaggingAgent and IssueDetectorAgent in parallel and generates
  a StepAnnotation per step, then persists it.

  Design decisions (paper 5.1.2):
    - Post-hoc analysis after simulation
    - Both agents receive the same AgentRun as input
    - asyncio.gather() for parallel execution to reduce latency
  """

  def __init__(
    self,
    tagging_agent: TaggingAgent,
    issue_detector: IssueDetectorAgent,
    annotation_repo: IAnnotationRepository,
  ) -> None:
    self._tagger = tagging_agent
    self._detector = issue_detector
    self._repo = annotation_repo

  async def annotate_run(self, agent_run: AgentRun) -> None:
    """
    Runs annotation for a single AgentRun and saves the result to the DB.

    Runs TaggingAgent (tagging) and IssueDetectorAgent (issue detection) in parallel.
    """
    snapshots = agent_run.event_snapshots
    if not snapshots:
      return

    reasoning_steps = agent_run.get_reasoning_steps()

    # Run the two agents in parallel
    tags_result, issues_result = await asyncio.gather(
      self._tagger.run(reasoning_steps),
      self._detector.run(snapshots),
    )

    # Generate and save a StepAnnotation for each step
    for i, snapshot in enumerate(snapshots):
      tags = tags_result[i] if i < len(tags_result) else []
      issues = issues_result[i] if i < len(issues_result) else []

      annotation = StepAnnotation(
        agent_run_id=agent_run.id,
        step=snapshot.step,
        tags=tags,
        issues=issues,
      )
      await self._repo.save_step_annotation(annotation)
