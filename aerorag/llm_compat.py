"""Variant-aware Azure GPT-5 client built on the raw `openai` SDK.

We bypass `langchain_openai.ChatOpenAI` because it drops `reasoning_content`
(LangChain issue #34328, "won't fix"). Instead we call the raw OpenAI client
and hand-build a `langchain_core.messages.AIMessage` that preserves
`reasoning_content` in `additional_kwargs` — important for the agentic graph,
where the next node may want to inspect the reasoning.

Variant matrix (May 2026, Microsoft Foundry docs):
    gpt-5         (reasoning) — temperature rejected; max_completion_tokens; reasoning_effort top-level
    gpt-5-chat                — temperature=1.0 only
    gpt-5.1       (reasoning) — temperature rejected
    gpt-5.1-chat              — temperature NOT supported (strip)
    gpt-5.4                   — treated as chat-style (temperature=1.0 default)
    gpt-5.5                   — temperature supported per OpenAI guidance

Override LLM_TEMPERATURE in .env if you want to override the default.
"""
from __future__ import annotations

import json
import os
from typing import Any, Iterable

from openai import OpenAI


class GPT5Client:
    """Thin wrapper around `openai.OpenAI` for Azure Foundry GPT-5 deployments."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        deployment: str | None = None,
        api_version: str | None = None,
        max_completion_tokens: int | None = None,
        temperature: float | None = None,
    ) -> None:
        self.base_url = base_url or os.environ["AZURE_OPENAI_LLM_BASE_URL"]
        self.api_key = api_key or os.environ["AZURE_OPENAI_LLM_API_KEY"]
        self.deployment = deployment or os.environ["AZURE_OPENAI_LLM_DEPLOYMENT"]
        self.api_version = api_version or os.environ.get(
            "AZURE_OPENAI_LLM_API_VERSION", "2025-04-01-preview"
        )
        self.max_completion_tokens = int(
            max_completion_tokens
            if max_completion_tokens is not None
            else os.environ.get("LLM_MAX_COMPLETION_TOKENS", 8192)
        )
        self.temperature = float(
            temperature if temperature is not None
            else os.environ.get("LLM_TEMPERATURE", 1.0)
        )

        # Azure Foundry v1 endpoints (URL contains /openai/v1) use OpenAI-style
        # path versioning and reject ?api-version=...; legacy Azure OpenAI URLs
        # (.../openai/deployments/...) still need it as a query param.
        client_kwargs: dict = {"base_url": self.base_url, "api_key": self.api_key}
        if "/openai/v1" not in self.base_url:
            client_kwargs["default_query"] = {"api-version": self.api_version}
        self._client = OpenAI(**client_kwargs)

    # ------------------------------------------------------------------
    # variant helpers
    # ------------------------------------------------------------------
    @property
    def variant(self) -> str:
        d = self.deployment.lower()
        if "5.1-chat" in d:
            return "5.1-chat"
        if "5-chat" in d:
            return "5-chat"
        if "5.5" in d:
            return "5.5"
        if "5.4" in d:
            return "5.4"
        if "5.1" in d:
            return "5.1"
        return "5"

    def _temperature_for_request(self) -> float | None:
        """Return the temperature value to actually send, or None to omit."""
        v = self.variant
        # Reasoning variants: omit temperature entirely.
        if v in ("5", "5.1"):
            return None
        # 5.1-chat: not supported, strip.
        if v == "5.1-chat":
            return None
        # 5-chat, 5.4: only 1.0 accepted; honor user value if 1.0 else clamp.
        if v in ("5-chat", "5.4"):
            return 1.0
        # 5.5: accepts arbitrary temperature.
        return self.temperature

    # ------------------------------------------------------------------
    # main entry points
    # ------------------------------------------------------------------
    def chat(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        reasoning_effort: str | None = None,  # low | medium | high
        stream: bool = False,
    ):
        kwargs: dict[str, Any] = {
            "model": self.deployment,
            "messages": messages,
            "max_completion_tokens": self.max_completion_tokens,
        }
        temp = self._temperature_for_request()
        if temp is not None:
            kwargs["temperature"] = temp
        if reasoning_effort and self.variant in ("5", "5.1", "5.4", "5.5"):
            kwargs["reasoning_effort"] = reasoning_effort
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        if stream:
            kwargs["stream"] = True

        return self._client.chat.completions.create(**kwargs)

    @staticmethod
    def to_aimessage(response):
        """Convert an OpenAI ChatCompletion response to a LangChain AIMessage,
        preserving reasoning_content (and tool_calls) in canonical form."""
        from langchain_core.messages import AIMessage

        choice = response.choices[0]
        msg = choice.message
        content = msg.content or ""

        additional_kwargs: dict[str, Any] = {}
        for key in ("reasoning_content", "reasoning"):
            value = getattr(msg, key, None)
            if value:
                additional_kwargs[key] = value

        tool_calls: list[dict] = []
        raw_tcs = getattr(msg, "tool_calls", None) or []
        for tc in raw_tcs:
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            tool_calls.append({
                "name": tc.function.name,
                "args": args,
                "id": tc.id,
                "type": "tool_call",
            })

        return AIMessage(
            content=content,
            additional_kwargs=additional_kwargs,
            tool_calls=tool_calls,  # type: ignore[arg-type]
            response_metadata={
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "usage": response.usage.model_dump() if response.usage else {},
            },
        )

    @staticmethod
    def usage(response) -> dict:
        u = response.usage
        if not u:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        return u.model_dump()
