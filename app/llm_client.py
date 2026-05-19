"""LLM client interfaces and OpenAI-backed implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI


class LLMClient(Protocol):
    """Protocol for chat-style LLM clients used by the router."""

    def chat(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        max_tokens: int = 300,
        force_json: bool = False,
    ) -> str:
        """Return assistant text content for a single-turn chat."""


@dataclass
class OpenAIChatClient:
    """OpenAI Chat Completions wrapper."""

    api_key: str
    model: str

    def __post_init__(self) -> None:
        self._client = OpenAI(api_key=self.api_key)

    def chat(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        max_tokens: int = 300,
        force_json: bool = False,
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if force_json:
            kwargs["response_format"] = {"type": "json_object"}

        result = self._client.chat.completions.create(**kwargs)
        content = result.choices[0].message.content
        return content or ""


@dataclass
class DemoChatClient:
    """Deterministic offline client for local demos and submission walkthroughs."""

    model: str = "demo-router"

    def chat(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
        max_tokens: int = 300,
        force_json: bool = False,
    ) -> str:
        del temperature, max_tokens
        if force_json:
            return json.dumps(self._classify(user_message))
        return self._generate(system_prompt, user_message)

    def _classify(self, message: str) -> dict:
        text = message.lower()
        if any(token in text for token in ["python", "sql", "bug", "function", "code", "sort", "query", "print("]):
            return {"intent": "code", "confidence": 0.91}
        if any(token in text for token in ["average", "mean", "median", "dataset", "data", "pivot table", "numbers", "chart"]):
            return {"intent": "data", "confidence": 0.89}
        if any(token in text for token in ["paragraph", "rewrite", "professional", "writing", "verbose", "sentence", "awkward"]):
            return {"intent": "writing", "confidence": 0.9}
        if any(token in text for token in ["resume", "cover letter", "job interview", "career", "career advice"]):
            return {"intent": "career", "confidence": 0.9}
        return {"intent": "unclear", "confidence": 0.35}

    def _generate(self, system_prompt: str, message: str) -> str:
        text = message.strip()
        prompt_lower = system_prompt.lower()
        if "software engineer" in prompt_lower:
            return (
                "Use Python's sorted with a key function. For example: "
                "sorted(items, key=lambda item: item['field']). "
                "If keys may be missing, guard with item.get('field') and validate input before sorting."
            )
        if "data analyst" in prompt_lower:
            return (
                "This looks like a basic descriptive-statistics question. Start with the mean, median, and range, then check for outliers. "
                "A bar chart or box plot would help visualize spread depending on whether you care more about exact values or distribution."
            )
        if "writing coach" in prompt_lower:
            return (
                "The main issue is likely clarity rather than grammar alone. Tighten filler phrases, replace passive constructions with direct verbs, "
                "and shorten long sentences so each sentence carries one idea."
            )
        if "career advisor" in prompt_lower:
            return (
                "Before I give advice, clarify your target role, years of experience, and timeline. "
                "Then prioritize one concrete next step such as updating a resume, practicing interviews, or targeting a specific role category."
            )
        return f"Demo response for: {text}"


def build_llm_client(api_key: str, model: str, demo_mode: bool = False) -> LLMClient:
    """Build a real or demo client based on environment configuration."""
    normalized_key = (api_key or "").strip()
    if demo_mode or not normalized_key or normalized_key.startswith("dummy_key_"):
        return DemoChatClient()
    return OpenAIChatClient(api_key=normalized_key, model=model)
