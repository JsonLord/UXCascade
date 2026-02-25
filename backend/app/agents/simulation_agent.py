from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.agents.ports import BrowserPort, StepData
from app.domain.entities.experiment import AgentRun
from app.domain.entities.snapshot import EventSnapshot
from app.domain.value_objects.action import Action, TabMetadata
from app.domain.value_objects.persona import Persona

# ─────────────────────────────── Prompts ──────────────────────────────────
# Use the complete prompts from paper Appendix C.2 as-is.

TASK_PROMPT = """\
You are a usability tester.

Visit the {site_name} website ({site_url}) and, using your
current persona and behavior information (provided
separately), identify information relevant to that
persona's needs.

Focus areas: {focus_bullets}

While exploring, keep the following in mind and reflect at every step
in your reasoning:
- Which pieces of relevant information can you find easily, and
  where do you get stuck?
- Is anything you expected to see missing or hard to locate?
- How satisfied are you with the site's findability for your
  persona's needs?
- Do you have any suggestions or wishes that would make the site
  more useful for someone like you?

Important:
If a link makes you leave the {site_name} website, go back to the
last page you were on and continue there.
"""

BEHAVIOR_PROMPT = """\
You are a usability tester whose singular focus is to experience
a website exactly as a real user would through the lens of
the given persona.

**Persona (THE most important input):**
{persona}

---

1. **Embody the Persona Above All Else**
- Fully internalize this persona's background, goals,
  motivations, and pain-points.
- Speak and think strictly in the first person: "As this persona
  I want...", "I'm looking for...", "I feel confused
  when...".
- At every step, check: "Am I reacting as this persona would?"

2. **Step-by-Step Page Walk-Through**
- Scroll from top to bottom, section by section.
- For each element (headings, text, images, buttons, forms,
  links, etc.), state:
  1. **What I (the persona) see**
  2. **What I expect it to do**
  3. **How it aligns (or conflicts) with my persona's goals**

3. **Pinpoint Usability Issues for This Persona**
- Highlight broken links, vague labels, poor contrast, slow
  loads, missing cues, etc.
- For each issue, explain **why it matters to this persona**
  which goal it blocks or which expectation it breaks.

4. **Persona-Driven Questions**
- After each page section, list the questions this persona would
  ask: "Where can I find..?", "Why does this
  element..?", "Is there a way to..?"
- Only propose questions that match the persona's knowledge level
  and objectives.

5. **Transparent, Persona-Anchored Reasoning**
- At each observation, think aloud in first person: "I'm curious
  if...", "I'd expect to to...", "That feels misleading
  because...".
- Always tie reasoning back to the persona's profile: "As
  someone who values X, I'm concerned that..."

---

**Begin by summarizing the persona in your own words**, then
proceed to review the page from the top, strictly in the
persona's voice.
"""

PERSONA_PROMPT = """\
The following features describes your persona and your
characteristics:
{persona_features}
"""


class SimulationAgent:
  """
  Simulation agent that operates a website while embodying a persona on top of
  the browser-use framework, emitting an EventSnapshot at each step.

  Browser-specific implementation is delegated to BrowserPort, so this class
  does not depend directly on browser-use.

  LLM: claude-sonnet-4-6, temperature=1.0 (for behavioral diversity)
  Maximum steps: 25 (paper setting)
  """

  MAX_STEPS: int = 25
  TEMPERATURE: float = 1.0

  def __init__(self, browser_port: BrowserPort) -> None:
    self._browser = browser_port

  async def run(
    self,
    agent_run: AgentRun,
    on_snapshot: Callable[[EventSnapshot], Awaitable[None]],
  ) -> bool:
    """
    Execute the simulation and call on_snapshot for each step.

    Parameters
    ----------
    agent_run:
        The AgentRun entity to execute (contains experiment URL, persona, and goal)
    on_snapshot:
        Async callback invoked on each step completion.
        Handles DB persistence and WebSocket notification via EventBus.

    Returns
    -------
    bool
        Whether the goal is considered achieved (success flag of browser-use's done action)
    """
    # Extract site_name from the experiment URL
    site_name = self._extract_site_name(agent_run.persona)
    behavior_prompt = BEHAVIOR_PROMPT.format(persona=agent_run.persona.to_text())
    task = TASK_PROMPT.format(
      site_name=site_name,
      site_url=self._get_experiment_url(agent_run),
      focus_bullets=f"- {agent_run.goal}",
    )

    step_counter = 0

    async def on_step(step_data: StepData) -> None:
      nonlocal step_counter
      step_counter += 1
      snapshot = self._to_event_snapshot(agent_run.id, step_data)
      agent_run.add_snapshot(snapshot)
      await on_snapshot(snapshot)

    success = await self._browser.run_simulation(
      url=self._get_experiment_url(agent_run),
      task=task,
      behavior_prompt=behavior_prompt,
      max_steps=self.MAX_STEPS,
      on_step=on_step,
    )
    return success

  def _to_event_snapshot(self, agent_run_id: str, step: StepData) -> EventSnapshot:
    action_type = self._map_action_type(step.action_type)
    return EventSnapshot(
      agent_run_id=agent_run_id,
      step=step.step,
      raw_html=step.html,
      screenshot=step.screenshot or "",
      tab_metadata=TabMetadata(url=step.tab_url, title=step.tab_title),
      reasoning=step.reasoning,
      prompt=step.full_prompt,
      action=Action(
        type=action_type,
        selector=step.action_selector,
        value=step.action_value,
      ),
      action_result=step.action_result,
      errors=step.errors,
    )

  @staticmethod
  def _map_action_type(
    browser_action: str,
  ) -> str:
    """Map a browser-use action name to the domain Action.type."""
    name = browser_action.lower()
    if "click" in name:
      return "click"
    if "scroll" in name:
      return "scroll"
    if "input" in name or "type" in name or "fill" in name:
      return "type"
    if "navigate" in name or "go_to" in name or "url" in name:
      return "navigate"
    return "click"  # fallback

  @staticmethod
  def _extract_site_name(persona: Persona) -> str:  # noqa: ARG004
    """Retrieve the site_name from the persona (intended to be derived from the experiment URL)."""
    return "the website"

  @staticmethod
  def _get_experiment_url(agent_run: AgentRun) -> str:
    """AgentRun does not hold a URL directly, so the URL is retrieved from persona traits.
    Ideally this should come from the Experiment entity, but embedding it in a trait is
    also a viable design. This method is planned to be changed so that SimulationRunner
    passes the URL separately when calling it.
    """
    # NOTE: The URL is provided externally by SimulationRunner at AgentRun creation time,
    # so this implementation uses agent_run.persona.traits["_url"] as a provisional approach.
    return agent_run.persona.traits.get("_url", "")
