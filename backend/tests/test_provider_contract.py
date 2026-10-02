import anyio
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.llm_provider import LLMProvider
from main import app

client = TestClient(app)


def test_provider_contract_validation(monkeypatch):
  monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
  monkeypatch.setattr(settings, "OPENAI_BASE_URL", "")
  status, reason = LLMProvider.validate_configuration()
  assert status == "MISCONFIGURED"
  assert "OPENAI_BASE_URL" in reason

  monkeypatch.setattr(settings, "LLM_PROVIDER", "anthropic")
  monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
  status, reason = LLMProvider.validate_configuration()
  assert status == "MISCONFIGURED"
  assert "ANTHROPIC_API_KEY" in reason


def test_readiness_endpoint_503_when_unready(monkeypatch):
  monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
  monkeypatch.setattr(settings, "OPENAI_BASE_URL", "")

  response = client.get("/ready")
  assert response.status_code == 503
  data = response.json()
  assert data["status"] == "not_ready"
  assert data["llm"]["code"] == "MISCONFIGURED"


def test_run_blocking_when_unready(monkeypatch):
  monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
  monkeypatch.setattr(settings, "OPENAI_BASE_URL", "")

  response = client.post("/api/experiments/dummy-id/run")
  assert response.status_code == 503
  data = response.json()
  assert data["detail"]["code"] == "LLM_MISCONFIGURED"
