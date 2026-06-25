"""Anthropic structured-output wrapper + an injectable generator protocol.

The real generator uses the Anthropic SDK with the project defaults (model
claude-opus-4-8, adaptive thinking, effort=high) and messages.parse() so the
model's output validates against a Pydantic generation view by construction.
Tests inject a fake generator, so nothing here requires network.
"""

from __future__ import annotations

import os
from typing import Protocol, TypeVar

from pydantic import BaseModel

from .. import config

T = TypeVar("T", bound=BaseModel)


class StructuredGenerator(Protocol):
    def parse(self, system: str, user: str, schema: type[T]) -> T: ...


class AnthropicGenerator:
    """Real generator. Lazily constructs the SDK client so importing this module
    never requires a key; the key is only needed when .parse() is called."""

    def __init__(self, model: str | None = None):
        self.model = model or config.MODEL
        self._client = None

    def _client_or_raise(self):
        if self._client is None:
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set — generation requires an API key. "
                    "Set it in the environment, or run the LLM-free demo (resolve + "
                    "hand-authored content + render)."
                )
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def parse(self, system: str, user: str, schema: type[T]) -> T:
        client = self._client_or_raise()
        resp = client.messages.parse(
            model=self.model,
            max_tokens=config.MAX_TOKENS,
            thinking=config.THINKING,
            output_config={**config.OUTPUT_CONFIG},
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
        )
        out = resp.parsed_output
        if out is None:
            raise RuntimeError(
                f"structured generation returned no parsed output "
                f"(stop_reason={resp.stop_reason})"
            )
        return out


def default_generator() -> StructuredGenerator:
    return AnthropicGenerator()
