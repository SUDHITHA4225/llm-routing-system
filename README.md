# LLM Intent-Based Prompt Routing Service

A Python-based FastAPI application that leverages a two-stage LLM workflow to intelligently classify and route user requests.

The system first identifies the user's intent (e.g., code, data, writing, career, or unclear) and then forwards the request to a dedicated expert persona prompt to generate a specialized response.

The application includes structured JSON parsing, fallback handling for uncertain classifications, manual intent overrides, confidence-based routing, and request observability through JSONL logging.

## Key Features

* Modular expert prompts maintained in `app/prompts.py`
* Intelligent `classify_intent(message)` function with structured JSON response parsing
* Context-aware `route_and_respond(message, intent)` for expert persona routing
* Automatic clarification questions for ambiguous or unclear user inputs
* Persistent append-only request logging using `route_log.jsonl`
* Robust malformed JSON handling with safe fallback behavior
* Confidence threshold support to reduce incorrect routing
* Manual routing override using `@intent` prefixes
* Comprehensive unit tests covering core functionalities
* Containerized deployment using Docker and Docker Compose

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

## Local Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your API key:

```bash
Copy-Item .env.example .env
```

Set:

```env
OPENAI_API_KEY=your_api_key_here
```

### 4. Start the application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If a live API key is unavailable, enable demo mode:

```env
ROUTER_DEMO_MODE=true
```

This enables a deterministic local demo client to simulate intent classification, response routing, CLI interactions, API responses, and JSONL logs without requiring external API access.

## API Endpoints

### Health Check

**GET** `/health`

### Route Request

**POST** `/route`

Request body:

```json
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

## Docker Deployment

Build and start the application using Docker Compose:

```bash
docker-compose up --build
```

The service will be accessible at:

```text
http://localhost:8000
```

## CLI Support (Optional)

Launch the interactive CLI interface:

```bash
python -m app.cli
```

Run a single message directly:

```bash
python -m app.cli --message "@code fix this bug: for i in range(10) print(i)"
```

When `ROUTER_DEMO_MODE=true`, the CLI works without an active API key.

## Core Functions

### `classify_intent(message, llm_client=None, confidence_threshold=0.7)`

* Sends requests to an LLM using a strict intent-classification prompt
* Parses structured JSON responses:

```json
{
  "intent": "string",
  "confidence": 0.0
}
```

* Gracefully handles malformed outputs by returning:

```json
{
  "intent": "unclear",
  "confidence": 0.0
}
```

### `route_and_respond(message, intent, llm_client=None)`

* Routes requests to the corresponding expert persona
* Returns clarification prompts when the detected intent is unclear

### `handle_message(...)`

* Manages the complete workflow:

  * Intent classification
  * Response routing
  * Request logging

## Logging

Each request appends a structured JSON record to `route_log.jsonl`, including:

* `intent`
* `confidence`
* `user_message`
* `final_response`
* `timestamp`

## Testing

Run all test cases:

```bash
pytest -q
```

The test suite validates:

* Structured classifier JSON parsing
* Malformed JSON fallback behavior
* Confidence threshold routing
* Unclear intent clarification handling
* JSONL log schema validation
* Handling of 15 predefined sample messages

## Architecture Overview

* A lightweight classifier prompt minimizes cost during intent detection
* Expert persona prompts improve response quality through domain specialization
* Manual override support enables direct routing using prefixes such as `@code`
* Confidence thresholds help reduce misclassification for ambiguous queries
