from __future__ import annotations

import re
from abc import ABC

from app.core.llm_provider import LLMProvider


class BaseAgent(ABC):
  """
  Base class for all agents that call the LLM directly.

  Delegates provider detection, client instantiation, and execution
  to LLMProvider.
  """

  async def _call(
    self,
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 4096,
  ) -> str:
    """
    Call the configured LLM API (OpenAI-compatible or Anthropic) via LLMProvider.
    """
    stage = getattr(self, "stage", "direct")
    return await LLMProvider.call_text_llm(
      system=system,
      user=user,
      temperature=temperature,
      max_tokens=max_tokens,
      stage=stage,
    )

  @staticmethod
  def _extract_json(text: str) -> str:
    """
    Extract the JSON string inside a fenced code block from an LLM response.
    If no fence is found, return the text as-is.
    """
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
      return match.group(1).strip()
    return text.strip()
