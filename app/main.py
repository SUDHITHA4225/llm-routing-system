"""FastAPI entrypoint for the LLM prompt router service."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.llm_client import build_llm_client
from app.router import handle_message

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ROUTER_DEMO_MODE = os.getenv("ROUTER_DEMO_MODE", "false").lower() == "true"
ROUTER_CONFIDENCE_THRESHOLD = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD", "0.7"))
ROUTE_LOG_PATH = Path(os.getenv("ROUTE_LOG_PATH", "route_log.jsonl"))

app = FastAPI(title="LLM Prompt Router", version="1.0.0")


class RouteRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input text")


class RouteResponse(BaseModel):
    intent: str
    confidence: float
    response: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/route", response_model=RouteResponse)
def route(req: RouteRequest) -> dict:
    client = build_llm_client(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        demo_mode=ROUTER_DEMO_MODE,
    )
    return handle_message(
        message=req.message,
        llm_client=client,
        log_path=ROUTE_LOG_PATH,
        confidence_threshold=ROUTER_CONFIDENCE_THRESHOLD,
    )
