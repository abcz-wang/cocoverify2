"""Unit tests for the OpenAI-compatible LLM client wrapper."""

from __future__ import annotations

import os
from types import SimpleNamespace

from cocoverify2.core.config import LLMConfig
from cocoverify2.llm.client import LLMClient, _proxy_environment


class _FakeChatCompletions:
    def __init__(self, responses):
        self._responses = list(responses)

    def create(self, **kwargs):
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _FakeOpenAIClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeChatCompletions(responses))


def _response_with_content(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_llm_client_returns_string_content(monkeypatch) -> None:
    client = LLMClient(LLMConfig())
    fake_client = _FakeOpenAIClient([_response_with_content('{"ok": true}')])
    monkeypatch.setattr(client, "_create_openai_client", lambda: fake_client)

    result = client.complete(system_prompt="system", user_prompt="user")

    assert result == '{"ok": true}'


def test_llm_client_retries_then_succeeds(monkeypatch) -> None:
    client = LLMClient(LLMConfig(max_retries=1))
    fake_client = _FakeOpenAIClient([RuntimeError("boom"), _response_with_content('{"ok": true}')])
    monkeypatch.setattr(client, "_create_openai_client", lambda: fake_client)

    result = client.complete(system_prompt="system", user_prompt="user")

    assert result == '{"ok": true}'


def test_llm_client_handles_list_content(monkeypatch) -> None:
    client = LLMClient(LLMConfig())
    fake_client = _FakeOpenAIClient(
        [
            _response_with_content(
                [
                    {"text": '{"answer": '},
                    {"text": '"done"}'},
                ]
            )
        ]
    )
    monkeypatch.setattr(client, "_create_openai_client", lambda: fake_client)

    result = client.complete(system_prompt="system", user_prompt="user")

    assert result == '{"answer": \n"done"}'


def test_proxy_environment_clears_proxy_vars_when_explicitly_disabled(monkeypatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example")
    config = LLMConfig(base_url="http://10.200.108.4:8001/v1", disable_proxies=True, trust_env=False)

    with _proxy_environment(config):
        assert "HTTP_PROXY" not in os.environ
        assert "HTTPS_PROXY" not in os.environ

    assert os.environ["HTTP_PROXY"] == "http://proxy.example"
    assert os.environ["HTTPS_PROXY"] == "http://proxy.example"


def test_proxy_environment_keeps_proxy_vars_when_trust_env_is_enabled(monkeypatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example")
    config = LLMConfig(base_url="http://10.200.108.4:8001/v1", disable_proxies=True, trust_env=True)

    with _proxy_environment(config):
        assert os.environ["HTTP_PROXY"] == "http://proxy.example"
