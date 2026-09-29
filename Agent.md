# Agent Deployment Instructions & Best Practices

This document provides guidelines and instructions for agents maintaining or deploying this space on Hugging Face Docker Spaces.

## 1. Space Overview
- **Profile:** `Leon4gr45`
- **Space:** `rowboat`
- **Full Identifier:** `Leon4gr45/rowboat`
- **Port:** `7860`

## 2. Mandatory Endpoints & API Documentation
- **`/health`**: Returns HTTP 200 `{"status": "ok"}` for Hugging Face health checks.
- **`/api-docs`**: OpenAPI/Swagger interface listing all backend endpoints (`https://Leon4gr45-rowboat.hf.space/api-docs`).

### Key Endpoints
- `GET /health` - Health check
- `GET /api/experiments` - List all experiments
- `POST /api/experiments` - Create a new experiment
- `GET /api/experiments/{id}` - Get experiment details
- `POST /api/experiments/{id}/run` - Run experiment simulation
- `GET /api/experiments/{id}/issues` - List usability issues
- `POST /api/experiments/{id}/fixes` - Generate UI fix
- `WS /api/ws/experiments/{id}` - Real-time simulation event stream

## 3. Database & Storage Configuration
- Local SQLite database resides at `/app/uxcascade.db` by default (or external PostgreSQL via `DATABASE_URL`).
- All local database files and SQLite assets must be stored in `/app` directory.

## 4. OpenAI-Compatible API Support
The system supports OpenAI-compatible LLM endpoints:
- `OPENAI_BASE_URL`: Custom API base URL (e.g., `https://api.openai.com/v1`)
- `OPENAI_API_KEY`: API Key
- `OPENAI_MODEL_NAME`: Target model (e.g., `gpt-4o`)

## 5. Deployment Commands & Log Monitoring
To push update to the space using `hf` CLI:

```bash
HF_TOKEN="<TOKEN>" hf upload Leon4gr45/rowboat . . --repo-type=space
```

To monitor build logs:
```bash
curl -N -H "Authorization: Bearer <TOKEN>" "https://huggingface.co/api/spaces/Leon4gr45/rowboat/logs/build"
```

To monitor runtime logs:
```bash
curl -N -H "Authorization: Bearer <TOKEN>" "https://huggingface.co/api/spaces/Leon4gr45/rowboat/logs/run"
```
