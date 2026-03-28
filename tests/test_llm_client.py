"""Unit tests for the OpenAI-compatible LLM client wrapper."""

from __future__ import annotations

from types import SimpleNamespace

from cocoverify2.core.config import LLMConfig
from cocoverify2.llm.client import LLMClient


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
