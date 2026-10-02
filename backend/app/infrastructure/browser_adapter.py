from __future__ import annotations

import json
import tempfile
import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from browser_use import Agent as BrowserUseAgent
from browser_use.browser.config import BrowserConfig
from browser_use.agent.views import AgentOutput
from browser_use.browser.views import BrowserStateSummary

from app.agents.ports import BrowserPort, StepData
from app.core.config import settings
from app.core.llm_provider import LLMProvider
from app.domain.value_objects.persona import Persona
from app.infrastructure.storage_service import get_storage_service

os.environ["ANONYMIZED_TELEMETRY"] = "false"


class BrowserUseAdapter(BrowserPort):
  """
  Concrete implementation of BrowserPort using browser-use with clean browser profile
  and persona behavior prompt override.
  """

  _SIMULATION_TEMPERATURE: float = 1.0
  _PREVIEW_TEMPERATURE: float = 0.0

  def _make_llm(self, temperature: float, system_prompt: str, stage: str = "simulation"):
    return LLMProvider.make_browser_llm(temperature=temperature, stage=stage)

  def _make_browser_config(self) -> BrowserConfig:
    return BrowserConfig(
      headless=settings.BROWSER_HEADLESS,
      extra_chromium_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )

  async def run_simulation(
    self,
    url: str,
    task: str,
    behavior_prompt: str,
    max_steps: int,
    on_step: Callable[[StepData], Awaitable[None]],
  ) -> bool:
    llm = self._make_llm(self._SIMULATION_TEMPERATURE, behavior_prompt, stage="simulation")
    browser_config = self._make_browser_config()

    pending: dict = {}
    step_counter: list[int] = [0]

    def _on_new_step(
      browser_state: BrowserStateSummary,
      agent_output: AgentOutput,
      step_n: int,
    ) -> None:
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
      if not pending:
        return

      raw_html, elements = await _get_page_data(agent)

      screenshot_url = await get_storage_service().save_step_screenshot_async(
        pending["screenshot_b64"], elements
      )

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
      browser_config=browser_config,
      override_system_message=behavior_prompt,
      register_new_step_callback=_on_new_step,
    )

    try:
      result = await agent.run(
        max_steps=max_steps,
        on_step_end=_on_step_end,
      )
      return result.is_successful() is True
    finally:
      try:
        if hasattr(agent, "browser_session") and agent.browser_session:
          await agent.browser_session.close()
      except Exception:
        pass

  async def run_single_step_with_html(
    self,
    fixed_html: str,
    prompt_history: list[dict],
    persona: Persona,
    behavior_prompt: str,
  ) -> StepData:
    llm = self._make_llm(self._PREVIEW_TEMPERATURE, behavior_prompt, stage="preview")
    browser_config = self._make_browser_config()

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
      if captured:
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
      browser_config=browser_config,
      override_system_message=behavior_prompt,
      register_new_step_callback=_on_new_step,
      register_should_stop_callback=_should_stop,
    )

    try:
      await agent.run(
        max_steps=1,
        on_step_end=_on_step_end,
      )
    finally:
      try:
        if hasattr(agent, "browser_session") and agent.browser_session:
          await agent.browser_session.close()
      except Exception:
        pass
      try:
        html_path.unlink()
      except OSError:
        pass

    if not captured:
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


def _extract_action(
  agent_output: AgentOutput,
) -> tuple[str, str | None, str | None]:
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
  try:
    page = await agent.browser_session.get_current_page()
    if page is None:
      return "", []

    raw_html = await page.evaluate("() => document.documentElement.outerHTML")

    elements_json = await page.evaluate("""
      () => Array.from(document.querySelectorAll('[data-index]'))
        .map(el => {
          const rect = el.getAttribute('data-index') ? {
            index: el.getAttribute('data-index'),
            tag: el.tagName.toLowerCase(),
            x: Math.round(el.getBoundingClientRect().x),
            y: Math.round(el.getBoundingClientRect().y),
            width: Math.round(el.getBoundingClientRect().width),
            height: Math.round(el.getBoundingClientRect().height),
          } : null;
          return rect;
        })
        .filter(el => el && el.width > 2 && el.height > 2 && el.x >= 0 && el.y >= 0)
    """)
    elements: list[dict] = json.loads(elements_json) if elements_json else []

    return raw_html, elements

  except Exception:
    return "", []
