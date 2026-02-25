from __future__ import annotations

import json

from app.agents.base import BaseAgent

# ─────────────────────────── Prompt ───────────────────────────────────────
# Full reproduction of the TAGGING_PROMPT from paper Appendix C.3.

_TAGGING_PROMPT_TEMPLATE = """\
You are a tagging assistant for persona-driven usability tests.

Given a sequence of reasoning traces from a single test run,
return a JSON array where each element is an array of up to
{n_tags} concise semantic tags for the corresponding
step.

Tags should describe the user's underlying cognitive intent, not
the low-level UI action.

Do NOT describe physical interactions such as "click button" or
"scroll page".
Use consistent phrasing across runs when behavior and intent are
similar.

Baseline cognitive intent types for guidance:
- Explore and browse
- Search and locate
- Select and decide
- Input and submit
- Confirm and complete
- Adjust or undo
- Learn and understand
- Troubleshoot or fix

=== Output Requirements ===
- Return only a JSON array of arrays.
- Exactly one inner array per step.
- Each inner array contains up to {n_tags} tags.
- Return exactly {n_steps} arrays.

=== Example ===
INPUT:
["The user scrolls through the main product list to see what's\
  available.",
 "They sort items by price and look for the cheapest option.",
 "They add the chosen product to their cart to prepare for\
  checkout."]

OUTPUT:
[["browse product options"],
 ["locate cheapest product"],
 ["select item for purchase"]]
"""


class TaggingAgent(BaseAgent):
  """
  Agent that generates cognitive intent tags from simulation reasoning traces.

  Design decisions (paper 5.1.2 / Appendix C.3):
    - Post-hoc analysis after simulation (not called during simulation)
    - LLM: claude-haiku-4-5 (fast, low-cost, JSON output task)
    - temperature=0 (deterministic, reproducibility-focused)
    - Maximum number of tags: N_TAGS=3
  """

  model = "claude-haiku-4-5-20251001"
  N_TAGS: int = 3

  async def run(self, reasoning_steps: list[str]) -> list[list[str]]:
    """
    Accept a sequence of reasoning steps and return an array of cognitive
    intent tags for each step.

    Parameters
    ----------
    reasoning_steps:
        List of think-aloud texts returned by AgentRun.get_reasoning_steps()

    Returns
    -------
    list[list[str]]
        Array of the same length as reasoning_steps. Each element contains
        up to N_TAGS tag strings.
    """
    if not reasoning_steps:
      return []

    system = _TAGGING_PROMPT_TEMPLATE.format(
      n_tags=self.N_TAGS,
      n_steps=len(reasoning_steps),
    )
    user_content = json.dumps(reasoning_steps, ensure_ascii=False)
    raw = await self._call(
      system=system,
      user=user_content,
      temperature=0.0,
    )
    result: list[list[str]] = json.loads(self._extract_json(raw))

    # Validate the step count
    if len(result) != len(reasoning_steps):
      # If the LLM returned a different number of arrays, pad or trim
      if len(result) < len(reasoning_steps):
        result += [[] for _ in range(len(reasoning_steps) - len(result))]
      else:
        result = result[: len(reasoning_steps)]

    return result
