from __future__ import annotations

import json
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path

from browser_use import Agent as BrowserUseAgent, ChatAnthropic
from browser_use.agent.views import AgentOutput
from browser_use.browser.views import BrowserStateSummary

from app.agents.ports import BrowserPort, StepData
from app.domain.value_objects.persona import Persona
from app.infrastructure.storage_service import get_storage_service


class BrowserUseAdapter(BrowserPort):
  """
  Concrete implementation of BrowserPort using the browser-use framework.

  SimulationAgent and PreviewAgent only see the BrowserPort interface, making it
  easy to swap this for another browser implementation (direct Playwright, headless mock, etc.).

  LLM settings:
    - Simulation: temperature=1.0 (for action diversity)
    - Preview single-step re-run: temperature=0.0

  Callback strategy:
    register_new_step_callback(BrowserStateSummary, AgentOutput, step_n)
      → Called before action execution. Records screenshot, reasoning, and next action.
    on_step_end(agent)
      → Called after action execution. Retrieves the latest step result from agent.history
        and fetches [data-index] element bboxes from Playwright to pass to StorageService.
  """

  _SIMULATION_TEMPERATURE: float = 1.0
  _PREVIEW_TEMPERATURE: float = 0.0
  _LLM_MODEL: str = "claude-sonnet-4-6"

  def _make_llm(self, temperature: float, system_prompt: str) -> ChatAnthropic:
    """
    Create a ChatAnthropic instance to pass to browser-use.
    behavior_prompt is passed as override_system_message to the Agent,
    so only the base LLM is configured here.
    """
    from app.core.config import settings
    return ChatAnthropic(
      model=self._LLM_MODEL,
      temperature=temperature,
      api_key=settings.ANTHROPIC_API_KEY,
    )

  async def run_simulation(
    self,
    url: str,
    task: str,
    behavior_prompt: str,
    max_steps: int,
    on_step: Callable[[StepData], Awaitable[None]],
  ) -> bool:
    """
    Run a simulation using the browser-use Agent.

    Collects pre-action data via register_new_step_callback,
    then completes the StepData with action results in the on_step_end hook.
    """
    llm = self._make_llm(self._SIMULATION_TEMPERATURE, behavior_prompt)

    # Shared state dict across steps
    pending: dict = {}
    step_counter: list[int] = [0]

    def _on_new_step(
      browser_state: BrowserStateSummary,
      agent_output: AgentOutput,
      step_n: int,
    ) -> None:
      """Before action execution: record screenshot, reasoning, and action type."""
      action_name, action_selector, action_value = _extract_action(agent_output)
      pending.update(
        {
          "step": step_n,
          "screenshot_b64": browser_state.screenshot or "",
          "url": browser_state.url,
          "title": browser_state.title,
          "reasoning": (
            agent_output.thinking
            or agent_output.evaluation_previous_goal
            or agent_output.next_goal
            or ""
          ),
          "action_type": action_name,
          "action_selector": action_selector,
          "action_value": action_value,
          "errors": list(browser_state.browser_errors),
        }
      )
      step_counter[0] = step_n

    async def _on_step_end(agent: BrowserUseAgent) -> None:
      """After action execution: collect HTML, annotated screenshot URL, and result to complete StepData."""
      if not pending:
        return

      # Fetch HTML and [data-index] element bboxes from Playwright
      raw_html, elements = await _get_page_data(agent)

      # Delegate annotation and upload to StorageService
      screenshot_url = await get_storage_service().save_step_screenshot_async(
        pending["screenshot_b64"], elements
      )

      # Retrieve the latest execution result from history
      action_result = ""
      errors: list[str] = list(pending.get("errors", []))
      if agent.history.history:
        latest = agent.history.history[-1]
        if latest.result:
          last_result = latest.result[-1]
          action_result = last_result.extracted_content or ""
          if last_result.error:
            errors.append(last_result.error)

      step_data = StepData(
        step=pending["step"],
        html=raw_html,
        screenshot=screenshot_url,
        reasoning=pending["reasoning"],
        full_prompt=pending.get("full_prompt", ""),
        action_type=pending["action_type"],
        action_selector=pending["action_selector"],
        action_value=pending["action_value"],
        action_result=action_result,
        errors=errors,
        tab_url=pending["url"],
        tab_title=pending["title"],
      )
      pending.clear()
      await on_step(step_data)

    agent = BrowserUseAgent(
      task=task,
      llm=llm,
      override_system_message=behavior_prompt,
      register_new_step_callback=_on_new_step,
    )

    result = await agent.run(
      max_steps=max_steps,
      on_step_end=_on_step_end,
    )

    return result.is_successful() is True

  async def run_single_step_with_html(
    self,
    fixed_html: str,
    prompt_history: list[dict],  # noqa: ARG002  # unused in current version (reserved for future use)
    persona: Persona,
    behavior_prompt: str,
  ) -> StepData:
    """
    Serve fixed HTML as a temporary file and re-simulate a single step.

    prompt_history is kept as an argument for future use via browser-use's
    injected_agent_state, but is not yet implemented in the current version.
    """
    llm = self._make_llm(self._PREVIEW_TEMPERATURE, behavior_prompt)

    # Write fixed HTML to a temporary file and serve via file:// URL
    with tempfile.NamedTemporaryFile(
      suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as f:
      f.write(fixed_html)
      html_path = Path(f.name)

    file_url = html_path.as_uri()
    captured: dict = {}

    def _on_new_step(
      browser_state: BrowserStateSummary,
      agent_output: AgentOutput,
      step_n: int,
    ) -> None:
      if captured:  # only record the first step
        return
      action_name, action_selector, action_value = _extract_action(agent_output)
      captured.update(
        {
          "step": step_n,
          "screenshot_b64": browser_state.screenshot or "",
          "url": browser_state.url,
          "title": browser_state.title,
          "reasoning": (
            agent_output.thinking or agent_output.evaluation_previous_goal or ""
          ),
          "action_type": action_name,
          "action_selector": action_selector,
          "action_value": action_value,
          "errors": list(browser_state.browser_errors),
        }
      )

    raw_html_holder: list[str] = [""]
    action_result_holder: list[str] = [""]
    screenshot_url_holder: list[str] = [""]
    stop_flag: list[bool] = [False]

    async def _should_stop() -> bool:
      """Stop after one step has been executed."""
      if stop_flag[0]:
        return True
      stop_flag[0] = True
      return False

    async def _on_step_end(agent: BrowserUseAgent) -> None:
      raw_html_holder[0], elements = await _get_page_data(agent)
      screenshot_url_holder[0] = await get_storage_service().save_step_screenshot_async(
        captured.get("screenshot_b64", ""), elements
      )
      if agent.history.history:
        latest = agent.history.history[-1]
        if latest.result and latest.result[-1].extracted_content:
          action_result_holder[0] = latest.result[-1].extracted_content

    agent = BrowserUseAgent(
      task=f"Navigate to {file_url} and observe the page.",
      llm=llm,
      override_system_message=behavior_prompt,
      register_new_step_callback=_on_new_step,
      register_should_stop_callback=_should_stop,
    )

    await agent.run(
      max_steps=1,
      on_step_end=_on_step_end,
    )

    # Delete temporary file
    try:
      html_path.unlink()
    except OSError:
      pass

    if not captured:
      # Fallback when capture fails
      return StepData(
        step=1,
        html=fixed_html,
        screenshot="",
        reasoning="",
        full_prompt="",
        action_type="navigate",
        action_selector=None,
        action_value=file_url,
        action_result="preview simulation failed",
        errors=["No step data captured"],
      )

    return StepData(
      step=captured["step"],
      html=raw_html_holder[0] or fixed_html,
      screenshot=screenshot_url_holder[0],
      reasoning=captured["reasoning"],
      full_prompt="",
      action_type=captured["action_type"],
      action_selector=captured["action_selector"],
      action_value=captured["action_value"],
      action_result=action_result_holder[0],
      errors=captured["errors"],
      tab_url=captured["url"],
      tab_title=captured["title"],
    )


# ─────────────── Helper functions ───────────────────────────────────────────


def _extract_action(
  agent_output: AgentOutput,
) -> tuple[str, str | None, str | None]:
  """
  Extract action name, selector, and value from AgentOutput.action[0].

  ActionModel is dynamically generated, so it is converted to a dict via model_dump().
  Examples:
    {"click": {"index": 5}} → ("click", None, None)
    {"input_text": {"index": 2, "text": "hello"}} → ("type", None, "hello")
    {"go_to_url": {"url": "https://..."}} → ("navigate", None, "https://...")
  """
  if not agent_output.action:
    return ("navigate", None, None)

  action_dict = agent_output.action[0].model_dump(exclude_none=True, mode="json")
  if not action_dict:
    return ("navigate", None, None)

  action_name = next(iter(action_dict.keys()))
  params: dict = action_dict.get(action_name) or {}

  selector: str | None = None
  value: str | None = None

  if "index" in params:
    selector = f"[data-index='{params['index']}']"
  if "text" in params:
    value = str(params["text"])
  elif "url" in params:
    value = str(params["url"])
  elif "query" in params:
    value = str(params["query"])
  elif "value" in params:
    value = str(params["value"])

  return (action_name, selector, value)


async def _get_page_data(
  agent: BrowserUseAgent,
) -> tuple[str, list[dict]]:
  """
  Fetch HTML and bounding boxes of [data-index] elements from the Playwright page.

  Returns
  -------
  (raw_html, elements)
      elements: [{index, tag, x, y, width, height}, ...] only elements within the viewport
  """
  try:
    page = await agent.browser_session.get_current_page()
    if page is None:
      return "", []

    raw_html = await page.evaluate(
      "() => document.documentElement.outerHTML"
    )

    elements_json = await page.evaluate("""
      () => Array.from(document.querySelectorAll('[data-index]'))
        .map(el => {
          const rect = el.getBoundingClientRect();
          return {
            index: el.getAttribute('data-index'),
            tag: el.tagName.toLowerCase(),
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          };
        })
        .filter(el => el.width > 2 && el.height > 2
                   && el.x >= 0 && el.y >= 0)
    """)
    elements: list[dict] = json.loads(elements_json) if elements_json else []

    return raw_html, elements

  except Exception:
    return "", []
