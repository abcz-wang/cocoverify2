"""OpenAI-compatible LLM client helpers for cocoverify2."""

from __future__ import annotations

from contextlib import contextmanager
import ipaddress
import os
from typing import Any
from urllib.parse import urlparse

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.errors import ConfigurationError


class LLMClient:
    """Thin wrapper around an OpenAI-compatible chat completion endpoint."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return raw text content from the configured LLM backend."""
        if self.config.provider.lower() != "openai":
            raise ConfigurationError(
                f"Unsupported LLM provider for cocoverify2 v1: {self.config.provider!r}. Only 'openai' is supported."
            )

        last_error: Exception | None = None
        attempts = max(1, int(self.config.max_retries) + 1)
        for _ in range(attempts):
            try:
                with _proxy_environment(self.config):
                    response = self._create_openai_client().chat.completions.create(
                        model=self.config.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=float(self.config.temperature),
                        timeout=float(self.config.timeout_seconds),
                    )
                return _extract_response_text(response)
            except Exception as exc:  # pragma: no cover - exercised through mocks
                last_error = exc
        raise RuntimeError(f"LLM request failed after {attempts} attempt(s): {last_error}")

    def _create_openai_client(self) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency-level path
            raise RuntimeError("The openai package is required for cocoverify2 hybrid LLM mode.") from exc
        return OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)


def _extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        raise RuntimeError("LLM response did not include any choices.")
    message = getattr(choices[0], "message", None)
    if message is None:
        raise RuntimeError("LLM response did not include a message payload.")
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(getattr(item, "text", "")))
        return "\n".join(part for part in parts if part).strip()
    return str(content or "")


@contextmanager
def _proxy_environment(config: LLMConfig):
    if config.trust_env:
        yield
        return

    if not config.disable_proxies and not _should_disable_proxy(config.base_url):
        yield
        return

    proxy_names = (
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "all_proxy",
        "ALL_PROXY",
        "no_proxy",
        "NO_PROXY",
    )
    previous = {name: os.environ.get(name) for name in proxy_names}
    try:
        for name in proxy_names:
            os.environ.pop(name, None)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _should_disable_proxy(base_url: str | None) -> bool:
    if not base_url:
        return False
    parsed = urlparse(str(base_url))
    host = (parsed.hostname or "").strip()
    if not host:
        return False
    if host in {"localhost", "127.0.0.1"}:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "." not in host
    return bool(address.is_private or address.is_loopback or address.is_link_local)
