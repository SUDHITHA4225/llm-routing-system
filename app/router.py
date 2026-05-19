"""Intent classification and prompt routing core logic."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.llm_client import LLMClient, build_llm_client
from app.prompts import CLARIFICATION_QUESTION, INTENT_PROMPTS, SUPPORTED_INTENTS


CLASSIFIER_SYSTEM_PROMPT = (
    "Your task is to classify the user's intent. "
    "Allowed labels: code, data, writing, career, unclear. "
    "Respond with exactly one JSON object with keys: intent (string), confidence (float between 0.0 and 1.0). "
    "Do not include any explanation or extra keys."
)

MANUAL_OVERRIDE_PATTERN = re.compile(r"^@(code|data|writing|career)\b\s*", re.IGNORECASE)


@dataclass
class IntentResult:
    intent: str
    confidence: float


def _safe_default_intent() -> IntentResult:
    return IntentResult(intent="unclear", confidence=0.0)


def _get_default_llm_client() -> LLMClient:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    demo_mode = os.getenv("ROUTER_DEMO_MODE", "false").lower() == "true"
    return build_llm_client(api_key=api_key, model=model, demo_mode=demo_mode)


def _parse_classifier_json(raw: str) -> IntentResult:
    if not raw:
        return _safe_default_intent()

    cleaned = raw.strip()
    # Recover JSON if wrapped in markdown fences.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return _safe_default_intent()

    intent = str(payload.get("intent", "unclear")).lower().strip()
    confidence_raw = payload.get("confidence", 0.0)

    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.0

    if intent not in SUPPORTED_INTENTS:
        return _safe_default_intent()

    confidence = max(0.0, min(1.0, confidence))
    return IntentResult(intent=intent, confidence=confidence)


def classify_intent(
    message: str,
    llm_client: LLMClient | None = None,
    confidence_threshold: float = 0.7,
) -> dict:
    """Classify user intent with safe fallbacks.

    Supports optional manual overrides using prefixes like '@code'.
    """
    client = llm_client or _get_default_llm_client()

    override = MANUAL_OVERRIDE_PATTERN.match(message.strip())
    if override:
        return {"intent": override.group(1).lower(), "confidence": 1.0}

    raw = client.chat(
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        user_message=message,
        temperature=0.0,
        max_tokens=80,
        force_json=True,
    )
    result = _parse_classifier_json(raw)

    if result.intent != "unclear" and result.confidence < confidence_threshold:
        safe = _safe_default_intent()
        return {"intent": safe.intent, "confidence": safe.confidence}

    return {"intent": result.intent, "confidence": result.confidence}


def route_and_respond(
    message: str,
    intent: dict,
    llm_client: LLMClient | None = None,
) -> str:
    """Route to a specialized persona or ask for clarification."""
    client = llm_client or _get_default_llm_client()
    intent_label = str(intent.get("intent", "unclear")).lower().strip()

    if intent_label == "unclear":
        return CLARIFICATION_QUESTION

    prompt = INTENT_PROMPTS.get(intent_label)
    if not prompt:
        return CLARIFICATION_QUESTION

    return client.chat(
        system_prompt=prompt,
        user_message=message,
        temperature=0.2,
        max_tokens=600,
    )


def append_route_log(
    *,
    log_path: Path,
    intent: IntentResult,
    user_message: str,
    final_response: str,
) -> None:
    """Append one JSON object per line for observability."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "intent": intent.intent,
        "confidence": intent.confidence,
        "user_message": user_message,
        "final_response": final_response,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")


def handle_message(
    *,
    message: str,
    llm_client: LLMClient,
    log_path: Path,
    confidence_threshold: float = 0.7,
) -> dict:
    """End-to-end helper for one user request."""
    intent_dict = classify_intent(message, llm_client, confidence_threshold)
    intent = IntentResult(
        intent=intent_dict["intent"],
        confidence=float(intent_dict["confidence"]),
    )
    final_response = route_and_respond(message, intent_dict, llm_client)
    append_route_log(
        log_path=log_path,
        intent=intent,
        user_message=message,
        final_response=final_response,
    )
    return {
        "intent": intent.intent,
        "confidence": intent.confidence,
        "response": final_response,
    }


def intent_to_dict(intent: IntentResult) -> dict:
    """Utility for structured outputs where needed."""
    return asdict(intent)
