import anyio
from unittest.mock import AsyncMock, patch
import pytest
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.llm_provider import LLMProvider
from app.agents.tagging_agent import TaggingAgent


def test_provider_selection_openai(monkeypatch):
  monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
  monkeypatch.setattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
  monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test-key")

  assert LLMProvider.get_resolved_provider() == "openai"
  assert LLMProvider.get_provider_name() == "openai-compatible"

  client = LLMProvider.get_async_client(stage="test")
  assert isinstance(client, AsyncOpenAI)


def test_provider_selection_anthropic(monkeypatch):
  monkeypatch.setattr(settings, "LLM_PROVIDER", "anthropic")
  monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-ant-test")

  assert LLMProvider.get_resolved_provider() == "anthropic"
  assert LLMProvider.get_provider_name() == "anthropic"

  client = LLMProvider.get_async_client(stage="test")
  assert isinstance(client, AsyncAnthropic)


def test_agents_do_not_instantiate_anthropic_when_openai_configured(monkeypatch):
  monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
  monkeypatch.setattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
  monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test-key")

  async def run_test():
    with patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock) as mock_openai:
      mock_openai.return_value.choices = [
        type("Choice", (), {"message": type("Message", (), {"content": "```json\n[]\n```"})()})()
      ]

      tagging = TaggingAgent()
      res = await tagging._call("system", "user")

      assert mock_openai.called
      assert res == "```json\n[]\n```"

  anyio.run(run_test)
