from __future__ import annotations

import re
from abc import ABC

from anthropic import AsyncAnthropic


class BaseAgent(ABC):
  """
  Base class for all agents that call the LLM directly.

  Conforms to the common conventions described in design/agents/overview.md:
    - Model: claude-sonnet-4-6
    - Shares a single async Anthropic client
    - _call() executes a two-turn prompt with system and user roles
  """

  _client: AsyncAnthropic | None = None
  model: str = "claude-sonnet-4-6"

  @classmethod
  def _get_client(cls) -> AsyncAnthropic:
    if cls._client is None:
      from app.core.config import settings
      cls._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return cls._client

  async def _call(
    self,
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 4096,
  ) -> str:
    """
    Call the Anthropic API and return the assistant's response text.

    Parameters
    ----------
    system:
        System prompt (defines the agent's role and constraints)
    user:
        User content (the concrete input to the agent)
    temperature:
        Sampling temperature. Simulation=1.0, Annotation/Refinement=0.0
    max_tokens:
        Maximum number of output tokens
    """
    response = await self._get_client().messages.create(
      model=self.model,
      max_tokens=max_tokens,
      temperature=temperature,
      system=system,
      messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text  # type: ignore[union-attr]

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
