from __future__ import annotations

import logging
from typing import Any

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


def make_custom_chat_openai(**kwargs: Any) -> Any:
  from langchain_openai import ChatOpenAI

  llm = ChatOpenAI(**kwargs)
  object.__setattr__(llm, "provider", "openai")
  return llm


class LLMProvider:
  """
  Central provider abstraction for resolving LLM models, clients, and readiness.
  """

  @classmethod
  def is_openai_configured(cls) -> bool:
    return cls.get_resolved_provider() == "openai"

  @classmethod
  def get_resolved_provider(cls) -> str:
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "auto":
      if settings.OPENAI_BASE_URL or settings.OPENAI_API_KEY:
        return "openai"
      if settings.ANTHROPIC_API_KEY:
        return "anthropic"
      return "openai"
    return provider

  @classmethod
  def get_provider_name(cls) -> str:
    resolved = cls.get_resolved_provider()
    return "openai-compatible" if resolved == "openai" else "anthropic"

  @classmethod
  def get_model_name(cls, stage: str = "general") -> str:
    if cls.get_resolved_provider() == "openai":
      return settings.OPENAI_MODEL_NAME or "gpt-4o"
    return "claude-3-7-sonnet-20250219"

  @classmethod
  def validate_configuration(cls) -> tuple[str, str]:
    resolved = cls.get_resolved_provider()
    if resolved == "openai":
      if not settings.OPENAI_BASE_URL and not settings.OPENAI_API_KEY:
        return "MISCONFIGURED", "Neither OPENAI_BASE_URL nor OPENAI_API_KEY is configured"
      return "CONFIGURED", "OpenAI configuration syntax valid"
    elif resolved == "anthropic":
      if not settings.ANTHROPIC_API_KEY:
        return "MISCONFIGURED", "ANTHROPIC_API_KEY is not configured"
      return "CONFIGURED", "Anthropic API key present"
    return "MISCONFIGURED", f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}"

  @classmethod
  async def probe_connectivity(cls) -> tuple[bool, str, str]:
    status, reason = cls.validate_configuration()
    if status != "CONFIGURED":
      return False, status, reason

    resolved = cls.get_resolved_provider()
    model = cls.get_model_name("probe")

    try:
      if resolved == "openai":
        client = AsyncOpenAI(
          base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
          api_key=settings.OPENAI_API_KEY or "dummy",
          timeout=10.0,
        )
        res = await client.chat.completions.create(
          model=model,
          messages=[{"role": "user", "content": "Respond with OK"}],
          max_tokens=10,
        )
        text = res.choices[0].message.content or ""
        if text:
          return True, "READY", f"Probe succeeded ({model})"
        return False, "UNREACHABLE", "Empty probe response"
      else:
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=10.0)
        res = await client.messages.create(
          model=model,
          max_tokens=10,
          messages=[{"role": "user", "content": "Respond with OK"}],
        )
        if res.content and res.content[0].text:
          return True, "READY", f"Probe succeeded ({model})"
        return False, "UNREACHABLE", "Empty probe response"
    except Exception as exc:
      err_str = str(exc)
      if "401" in err_str or "auth" in err_str.lower() or "api_key" in err_str.lower():
        return False, "AUTH_FAILED", f"Authentication failed: {err_str}"
      if "404" in err_str or "model" in err_str.lower():
        return False, "MODEL_NOT_FOUND", f"Model error: {err_str}"
      return False, "UNREACHABLE", f"Probe exception: {err_str}"

  @classmethod
  def get_async_client(cls, stage: str = "general") -> Any:
    provider = cls.get_provider_name()
    model = cls.get_model_name(stage)
    logger.info("llm_stage=%s provider=%s model=%s", stage, provider, model)

    if cls.get_resolved_provider() == "openai":
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

    if cls.get_resolved_provider() == "openai":
      return make_custom_chat_openai(
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

    if cls.get_resolved_provider() == "openai":
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
