"""
Self-tests for agents.base.BaseAgent (#6).
Tests model config (#7), retry logic (#2), skill chain delegation (#9),
and the system prompt builder — all without real Claude API calls.
"""
import time
import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

import anthropic
from agents.base import BaseAgent, MODEL, MAX_RETRIES, RETRY_BASE_DELAY


# ── Concrete test subclass ────────────────────────────────────────────────────

class EchoAgent(BaseAgent):
    """Minimal concrete agent for testing — system prompt is its own name."""
    def _create_system_prompt(self) -> str:
        return f"You are {self.name}."


# ── Construction / model config (#7) ─────────────────────────────────────────

def test_default_model_is_global_constant():
    agent = EchoAgent("Tester", [])
    assert agent.model == MODEL


def test_custom_model_overrides_default():
    agent = EchoAgent("Tester", [], model="claude-haiku-4-5-20251001")
    assert agent.model == "claude-haiku-4-5-20251001"


def test_none_model_falls_back_to_default():
    agent = EchoAgent("Tester", [], model=None)
    assert agent.model == MODEL


def test_workspace_stored():
    ws = Path("/tmp/workspace")
    agent = EchoAgent("Tester", [], workspace=ws)
    assert agent.workspace == ws


def test_roles_stored():
    roles = ["do X", "do Y"]
    agent = EchoAgent("Tester", roles)
    assert agent.roles == roles


def test_system_prompt_text_populated():
    agent = EchoAgent("MyAgent", [])
    assert "MyAgent" in agent._system_prompt_text


# ── _build_system ─────────────────────────────────────────────────────────────

def test_build_system_has_cache_control():
    agent = EchoAgent("A", [])
    system = agent._build_system()
    assert system[0]["cache_control"] == {"type": "ephemeral"}


def test_build_system_appends_memory_when_set():
    agent = EchoAgent("A", [])
    agent.memory_context = "## Memory\n- past decision"
    system = agent._build_system()
    assert len(system) == 2
    assert "past decision" in system[1]["text"]


def test_build_system_no_memory_by_default():
    agent = EchoAgent("A", [])
    assert len(agent._build_system()) == 1


# ── _retry_call (#2) ─────────────────────────────────────────────────────────

def test_retry_call_succeeds_first_try():
    agent = EchoAgent("A", [])
    fn = MagicMock(return_value="ok")
    result = agent._retry_call(fn)
    assert result == "ok"
    fn.assert_called_once()


def test_retry_call_retries_on_429(monkeypatch):
    """Should retry MAX_RETRIES times on 429 then succeed."""
    agent = EchoAgent("A", [])
    monkeypatch.setattr(time, "sleep", lambda _: None)  # skip actual sleeping

    err = anthropic.APIStatusError(
        message="rate limited",
        response=MagicMock(status_code=429, headers={}),
        body={},
    )
    # Fail twice with 429, then succeed
    fn = MagicMock(side_effect=[err, err, "success"])
    result = agent._retry_call(fn)
    assert result == "success"
    assert fn.call_count == 3


def test_retry_call_exhausts_and_raises(monkeypatch):
    """After MAX_RETRIES+1 attempts, re-raise the last 429."""
    agent = EchoAgent("A", [])
    monkeypatch.setattr(time, "sleep", lambda _: None)

    err = anthropic.APIStatusError(
        message="rate limited",
        response=MagicMock(status_code=429, headers={}),
        body={},
    )
    fn = MagicMock(side_effect=[err] * (MAX_RETRIES + 1))
    with pytest.raises(anthropic.APIStatusError):
        agent._retry_call(fn)
    assert fn.call_count == MAX_RETRIES + 1


def test_retry_call_retries_on_529(monkeypatch):
    """529 (overloaded) should also trigger retry."""
    agent = EchoAgent("A", [])
    monkeypatch.setattr(time, "sleep", lambda _: None)

    err = anthropic.APIStatusError(
        message="overloaded",
        response=MagicMock(status_code=529, headers={}),
        body={},
    )
    fn = MagicMock(side_effect=[err, "recovered"])
    result = agent._retry_call(fn)
    assert result == "recovered"


def test_retry_call_does_not_retry_non_rate_limit(monkeypatch):
    """Non-429/529 API errors should NOT be retried."""
    agent = EchoAgent("A", [])
    monkeypatch.setattr(time, "sleep", lambda _: None)

    err = anthropic.APIStatusError(
        message="not found",
        response=MagicMock(status_code=404, headers={}),
        body={},
    )
    fn = MagicMock(side_effect=err)
    with pytest.raises(anthropic.APIStatusError):
        agent._retry_call(fn)
    fn.assert_called_once()  # No retry


def test_retry_call_delay_increases(monkeypatch):
    """Verify exponential backoff: delay should be RETRY_BASE_DELAY * 2^attempt."""
    agent = EchoAgent("A", [])
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda d: sleep_calls.append(d))

    err = anthropic.APIStatusError(
        message="rate limited",
        response=MagicMock(status_code=429, headers={}),
        body={},
    )
    fn = MagicMock(side_effect=[err, err, err, "ok"])
    agent._retry_call(fn)

    assert len(sleep_calls) == 3
    assert sleep_calls[0] == RETRY_BASE_DELAY * 1   # 2^0
    assert sleep_calls[1] == RETRY_BASE_DELAY * 2   # 2^1
    assert sleep_calls[2] == RETRY_BASE_DELAY * 4   # 2^2


# ── think() ──────────────────────────────────────────────────────────────────

def test_think_uses_agent_model():
    """think() must pass self.model to the API, not the hardcoded constant."""
    agent = EchoAgent("A", [], model="claude-haiku-4-5-20251001")

    fake_response = MagicMock()
    fake_response.content = [MagicMock(type="text", text="hello")]

    with patch("agents.base._client") as mock_client:
        mock_client.messages.create.return_value = fake_response
        agent.think("What is 1+1?")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"


def test_think_appends_to_messages():
    agent = EchoAgent("A", [])
    fake_response = MagicMock()
    fake_response.content = [MagicMock(type="text", text="reply")]

    with patch("agents.base._client") as mock_client:
        mock_client.messages.create.return_value = fake_response
        agent.think("Hello")

    assert len(agent.messages) == 2
    assert agent.messages[0] == {"role": "user", "content": "Hello"}
    assert agent.messages[1] == {"role": "assistant", "content": "reply"}


# ── invoke_skill_chain (#9) ───────────────────────────────────────────────────

def test_invoke_skill_chain_delegates_to_registry():
    agent = EchoAgent("A", [])
    expected = {"s1": "out1", "s2": "out2"}

    with patch("skills.registry.SkillRegistry.chain", return_value=expected) as mock_chain:
        result = agent.invoke_skill_chain(["s1", "s2"], "my task")

    mock_chain.assert_called_once_with(["s1", "s2"], "my task", workspace=None)
    assert result == expected


def test_invoke_skill_chain_passes_workspace():
    ws = Path("/some/workspace")
    agent = EchoAgent("A", [], workspace=ws)

    with patch("skills.registry.SkillRegistry.chain", return_value={}) as mock_chain:
        agent.invoke_skill_chain(["s1"], "task")

    mock_chain.assert_called_once_with(["s1"], "task", workspace=ws)


# ── AbstractBase enforcement ──────────────────────────────────────────────────

def test_cannot_instantiate_base_agent_directly():
    with pytest.raises(TypeError):
        BaseAgent("Direct", [])  # type: ignore[abstract]
