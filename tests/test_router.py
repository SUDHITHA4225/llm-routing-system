from __future__ import annotations

import json
from pathlib import Path

from app.router import classify_intent, handle_message, route_and_respond


class FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls = []

    def chat(self, **kwargs) -> str:
        self.calls.append(kwargs)
        if not self.responses:
            return ""
        return self.responses.pop(0)


def test_classify_intent_parses_json_successfully() -> None:
    llm = FakeLLM(['{"intent":"code","confidence":0.93}'])
    result = classify_intent("how to sort in python", llm)
    assert result["intent"] == "code"
    assert result["confidence"] == 0.93


def test_classify_intent_handles_malformed_json() -> None:
    llm = FakeLLM(["intent: code"])  # malformed on purpose
    result = classify_intent("help", llm)
    assert result["intent"] == "unclear"
    assert result["confidence"] == 0.0


def test_classify_intent_uses_threshold() -> None:
    llm = FakeLLM(['{"intent":"writing","confidence":0.45}'])
    result = classify_intent("please review my paragraph", llm, confidence_threshold=0.7)
    assert result["intent"] == "unclear"
    assert result["confidence"] == 0.0


def test_manual_override_prefix() -> None:
    llm = FakeLLM([])
    result = classify_intent("@code fix this bug", llm)
    assert result["intent"] == "code"
    assert result["confidence"] == 1.0


def test_route_unclear_returns_question() -> None:
    llm = FakeLLM([])
    response = route_and_respond("hey", {"intent": "unclear", "confidence": 0.0}, llm)
    assert "clarify" in response.lower() or "help" in response.lower()


def test_handle_message_logs_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "route_log.jsonl"
    llm = FakeLLM(
        [
            '{"intent":"data","confidence":0.88}',
            "Use a histogram to inspect the distribution and compute mean and median.",
        ]
    )

    result = handle_message(
        message="what is average of 1 2 3",
        llm_client=llm,
        log_path=log_path,
    )

    assert result["intent"] == "data"
    assert log_path.exists()

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert set(["intent", "confidence", "user_message", "final_response"]).issubset(record)
    assert record["intent"] == "data"
