from __future__ import annotations

import logging
from typing import Any

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class CustomChatOpenAIWrapper:
  """
  LangChain/browser-use compatible wrapper for ChatOpenAI that ensures
  the .provider attribute is present without tripping Pydantic extra field checks.
  """

  def __init__(self, **kwargs: Any) -> None:
    from langchain_openai import ChatOpenAI

    self._llm = ChatOpenAI(**kwargs)
    self.provider = "openai"

  def __getattr__(self, name: str) -> Any:
    return getattr(self._llm, name)


class LLMProvider:
  """
  Central provider abstraction for resolving LLM models and clients across all agents.
  """

  @staticmethod
  def is_openai_configured() -> bool:
    return bool(settings.OPENAI_BASE_URL or settings.OPENAI_API_KEY)

  @classmethod
  def get_provider_name(cls) -> str:
    return "openai-compatible" if cls.is_openai_configured() else "anthropic"

  @classmethod
  def get_model_name(cls, stage: str = "general") -> str:
    if cls.is_openai_configured():
      return settings.OPENAI_MODEL_NAME or "gpt-4o"
    return "claude-3-7-sonnet-20250219"

  @classmethod
  def get_async_client(cls, stage: str = "general") -> Any:
    provider = cls.get_provider_name()
    model = cls.get_model_name(stage)
    logger.info(
      "llm_stage=%s provider=%s model=%s",
      stage,
      provider,
      model,
    )

    if cls.is_openai_configured():
      return AsyncOpenAI(
        base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
        api_key=settings.OPENAI_API_KEY or "dummy",
      )

    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

  @classmethod
  def make_browser_llm(cls, temperature: float = 1.0, stage: str = "simulation") -> Any:
    provider = cls.get_provider_name()
    model = cls.get_model_name(stage)
    logger.info(
      "llm_stage=%s provider=%s model=%s temperature=%.1f",
      stage,
      provider,
      model,
      temperature,
    )

    if cls.is_openai_configured():
      return CustomChatOpenAIWrapper(
        model=model,
        temperature=temperature,
        api_key=settings.OPENAI_API_KEY or "dummy",
        base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
      )

    from browser_use import ChatAnthropic

    return ChatAnthropic(
      model=model,
      temperature=temperature,
      api_key=settings.ANTHROPIC_API_KEY,
    )

  @classmethod
  async def call_text_llm(
    cls,
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    stage: str = "direct",
  ) -> str:
    provider = cls.get_provider_name()
    model = cls.get_model_name(stage)
    logger.info(
      "llm_stage=%s provider=%s model=%s temperature=%.1f",
      stage,
      provider,
      model,
      temperature,
    )

    client = cls.get_async_client(stage=stage)

    if cls.is_openai_configured():
      response = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
          {"role": "system", "content": system},
          {"role": "user", "content": user},
        ],
      )
      return response.choices[0].message.content or ""
    else:
      response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
      )
      return response.content[0].text  # type: ignore[union-attr]
