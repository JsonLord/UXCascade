from __future__ import annotations

import json
import uuid

from app.agents.base import BaseAgent
from app.domain.entities.annotation import Issue
from app.domain.entities.snapshot import EventSnapshot

# ─────────────────────────── Prompt ───────────────────────────────────────
# Full reproduction of the ISSUE_DETECTION_PROMPT from paper Appendix C.3.

_ISSUE_DETECTION_PROMPT_TEMPLATE = """\
You are an expert usability analyst and designer. You will
receive logs from an autonomous browser agent.

For each simulation step:
1. Identify every distinct usability issue, error, or point of
   friction.
2. If the step executed perfectly, return an empty list for that
   step.

For every issue you report, include these fields:
- type: A concise label such as "scroll_incorrect_area",
        "link_not_found", "form_validation_error".
- element: The specific UI element affected.
- reason: A brief, actionable explanation.
- fix: A concise, actionable recommendation.
- upt_codes: One or more codes from the Usability Problem
  Taxonomy (UPT).
- upt_explanation: A short explanation of why the UPT code(s)
  were chosen.
- issue_severity: Nielsen severity rating (integer 0-4).

=== USABILITY PROBLEM TAXONOMY (UPT) ===

A. Visualness
   A1: Layout & Structure
   A2: Visual Clarity
   A3: Information Presentation
   A4: Feedback Visibility

B. Language
   B1: Terminology & Labels
   B2: Clarity & Precision
   B3: Instructions & Guidance
   B4: Error Messages

C. Manipulation
   C1: Control Availability & Discoverability
   C2: Affordances
   C3: Responsiveness
   C4: Precision & Ease of Input

D. Task-Mapping
   D1: Sequence Support
   D2: Navigation & Wayfinding
   D3: Goal Alignment

E. Task-Facilitation
   E1: Error Prevention
   E2: Error Recovery & Undo
   E3: Adaptability & Efficiency
   E4: Support for Deviations

=== OUTPUT REQUIREMENTS (STRICT JSON OBJECT) ===
Return a single JSON object with this exact shape:
{{
  "version": "1.0",
  "expected_steps": {expected_len},
  "steps": [
    {{ "step": 1, "issues": [] }},
    ...
  ]
}}

- Always output a JSON object.
- Always include exactly {expected_len} steps.
- For steps without issues, set "issues": [].
- Output only the JSON object.
"""


class IssueDetectorAgent(BaseAgent):
  """
  Agent that extracts usability issues from a sequence of EventSnapshots
  produced by a simulation.

  Design decisions (paper 5.1.2 / Appendix C.3):
    - Structured output conforming to UPT (Usability Problem Taxonomy)
    - LLM: claude-sonnet-4-6 (detailed UPT-compliant analysis required)
    - temperature=0 (deterministic)
  """

  async def run(self, snapshots: list[EventSnapshot]) -> list[list[Issue]]:
    """
    Accept a sequence of EventSnapshots and return a per-step list of Issues.

    Parameters
    ----------
    snapshots:
        List of snapshots retrieved from AgentRun.event_snapshots

    Returns
    -------
    list[list[Issue]]
        Array of the same length as snapshots. Each element is the list of
        Issues detected at that step.
    """
    if not snapshots:
      return []

    steps_input = [
      {
        "step": s.step,
        "reasoning": s.reasoning,
        "action": s.action.model_dump(),
        "result": s.action_result,
        "errors": s.errors,
      }
      for s in snapshots
    ]
    user_content = json.dumps(steps_input, ensure_ascii=False)
    system = _ISSUE_DETECTION_PROMPT_TEMPLATE.format(expected_len=len(snapshots))

    raw = await self._call(
      system=system,
      user=user_content,
      temperature=0.0,
      max_tokens=8192,
    )
    parsed: dict = json.loads(self._extract_json(raw))

    result: list[list[Issue]] = []
    for step_data in parsed["steps"]:
      issues = [
        Issue(
          id=str(uuid.uuid4()),
          type=i["type"],
          element=i["element"],
          reason=i["reason"],
          fix=i["fix"],
          upt_codes=i["upt_codes"],
          upt_explanation=i["upt_explanation"],
          severity=i["issue_severity"],
        )
        for i in step_data.get("issues", [])
      ]
      result.append(issues)

    # Verify step count consistency
    if len(result) != len(snapshots):
      if len(result) < len(snapshots):
        result += [[] for _ in range(len(snapshots) - len(result))]
      else:
        result = result[: len(snapshots)]

    return result
