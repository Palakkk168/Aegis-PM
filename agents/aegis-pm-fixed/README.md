# Aegis PM

Aegis PM is a production-oriented autonomous AI Project Manager built on Google ADK, Gemini 2.0 Flash, FastAPI, ChromaDB, Redis, and Postgres.

## Project Layout

```text
/aegis-pm
  /agents
  /api
  /core
  /memory
  /observability
  /tools
  /workflows
  config.py
  main.py
  requirements.txt
  .env.example
  README.md
  PRD.md
  ARCHITECTURE.md
  EXECUTION_WALKTHROUGH.md
```

## Setup

1. Create a Python 3.11+ virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in credentials.
4. Start Redis and Postgres locally or point to managed instances.
5. Run the API:
   `python main.py`

## API

- `POST /projects`
- `GET /projects/{id}`
- `GET /projects/{id}/report`
- `POST /projects/{id}/pause`
- `POST /projects/{id}/resume`
- `GET /metrics`
- `GET /health`

## Example Request

```json
{
  "user_id": "founder_1",
  "goal": "Launch AI SaaS in 30 days",
  "deadline_days": 30,
  "metadata": {
    "slack_channel": "#exec"
  }
}
```

## Runtime Notes

- Google ADK sessions are keyed by `project_id`
- ChromaDB collections are namespaced per project
- Redis holds structured `ProjectState`
- Postgres stores decision history used by the risk engine
- Tool calls are real HTTP integrations and require valid credentials
