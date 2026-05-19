# LLM-Powered Prompt Router

A Python FastAPI service that uses a two-step LLM flow:
1. Classify user intent (`code`, `data`, `writing`, `career`, `unclear`)
2. Route to a specialized expert persona prompt to generate a response

It includes safe JSON parsing, confidence threshold fallback, manual intent override, and JSONL route logging.

## Features

- Distinct expert prompts stored in `app/prompts.py`
- `classify_intent(message)` with structured JSON output parsing
- `route_and_respond(message, intent)` with specialized persona routing
- Mandatory `unclear` intent clarification question behavior
- `route_log.jsonl` append-only observability log
- Malformed classifier output handling with safe fallback
- Optional confidence threshold and manual `@intent` override
- Unit tests covering core requirements
- Dockerized deployment using `Dockerfile` and `docker-compose.yml`

## Project Structure

```text
.
├── app
│   ├── __init__.py
│   ├── cli.py
│   ├── llm_client.py
│   ├── main.py
│   ├── prompts.py
│   └── router.py
├── tests
│   ├── test_router.py
│   └── test_sample_messages.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
└── route_log.jsonl
```

## Setup (Local)

1. Create and activate a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
4. Run the API.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If you do not have a live API key yet, set `ROUTER_DEMO_MODE=true` in `.env`. The app will use a deterministic local demo client so you can still see classified intents, routed responses, CLI output, API output, and JSONL logs.

## API Usage

### Health

```http
GET /health
```

### Route

```http
POST /route
Content-Type: application/json

{
  "message": "how do i sort a list of objects in python?"
}
```

Example response:

```json
{
  "intent": "code",
  "confidence": 0.94,
  "response": "..."
}
```

## Docker

Build and run with Docker Compose:

```powershell
docker-compose up --build
```

Service is available at `http://localhost:8000`.

## CLI (Optional)

You can run a simple interactive router UI in the terminal:

```powershell
C:/Users/SRI/AppData/Local/Python/pythoncore-3.14-64/python.exe -m app.cli
```

Single message mode:

```powershell
C:/Users/SRI/AppData/Local/Python/pythoncore-3.14-64/python.exe -m app.cli --message "@code fxi thsi bug pls: for i in range(10) print(i)"
```

If `ROUTER_DEMO_MODE=true`, the CLI works without a real OpenAI key.

## Core Functions

- `app/router.py:classify_intent(message, llm_client=None, confidence_threshold=0.7)`
  - Calls LLM with a strict classifier prompt.
  - Parses JSON output into `{"intent": "string", "confidence": float}`.
  - Handles malformed output gracefully by returning `{"intent": "unclear", "confidence": 0.0}`.

- `app/router.py:route_and_respond(message, intent, llm_client=None)`
  - Routes to matching expert prompt.
  - If intent is `unclear`, returns a clarification question.

- `app/router.py:handle_message(...)`
  - Orchestrates classify -> route -> log.

## Logging

Every request appends one JSON object line to `route_log.jsonl` including:

- `intent`
- `confidence`
- `user_message`
- `final_response`

A `timestamp` field is also included.

## Testing

Run all tests:

```powershell
pytest -q
```

Tests verify:

- Classifier JSON parsing
- Malformed JSON fallback
- Confidence threshold behavior
- `unclear` clarification response
- JSONL logging schema
- Provided set of 15 sample messages handling

## Design Notes

- Classifier prompt is short and constrained for low-cost intent detection.
- Persona prompts are concise and specialized for higher quality generation.
- Manual override allows direct routing with prefixes, e.g. `@code fix this bug`.
- Confidence threshold prevents overconfident misrouting on ambiguous inputs.
