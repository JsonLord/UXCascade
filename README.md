---
title: UXCascade
sdk: docker
app_port: 7860
---

# UXCascade

**UXCascade: Scalable Usability Testing with Simulated User Agents**

[![arXiv](https://img.shields.io/badge/arXiv-2601.15777-b31b1b.svg)](https://arxiv.org/abs/2601.15777)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This repository is an implementation of the system described in:

> **UXCascade: Scalable Usability Testing with Simulated User Agents**
> Steffen Holter, Eunyee Koh, Mustafa Doga Dogan, Gromit Yeuk-Yin Chan
> *arXiv:2601.15777 [cs.HC], 2026*
> https://arxiv.org/abs/2601.15777

---

## Overview

UX evaluation bottlenecks are growing as AI-assisted workflows let designers generate interface variations faster than they can be reviewed. UXCascade addresses this by simulating diverse user persona agents on a target web interface and aggregating their usability feedback into a structured, interactive analysis tool.

The core workflow follows five stages:

```
① Explore  — review agent goals and task outcomes
② Observe  — inspect trait-based behavioral distributions
③ Isolate  — drill into specific usability issues and their root causes
④ Propose  — generate targeted HTML fixes via a chat interface
⑤ Evaluate — re-simulate a single step to assess the impact of a fix
```

Key components:

| Agent | Role |
|---|---|
| **Simulation Agent** | Drives a live browser session as a persona-grounded user |
| **Tagging Agent** | Labels each reasoning step with a cognitive intent tag |
| **Issue Detector** | Extracts structured usability issues from think-aloud traces |
| **Editor Agent** | Generates DOM-level HTML patches from natural-language instructions |
| **Preview Agent** | Re-runs one simulation step on the patched HTML to evaluate the fix |

---

## Features

### Experiment Setup

Define the target URL, persona trait dimensions (e.g. age group, tech literacy, device type), and task goals. UXCascade automatically generates all trait combinations and spins up one LLM agent per persona–goal pair, running them in parallel against the live interface.

Each agent navigates the site as that persona, recording every action, screenshot, and reasoning step. The result is a rich, multi-perspective dataset of how different types of users experience the same UI — without recruiting a single human participant.

### Issue Analysis

Filter and triage usability issues by severity (S1–S4) across all agent runs. Each issue includes the affected element, root cause, suggested fix, and UPT taxonomy codes — with a one-click path to the fix workflow.

![Issue Analysis](assets/analysis.png)

### Step-by-Step Agent Journey

Replay any agent's browsing session step by step. Each step shows the agent's on-screen action, annotated reasoning, and behavioral tags — making it easy to spot exactly where and why a user gets stuck.

![Step-by-Step Journey](assets/step_journey.png)

### AI-Powered Fix Generation

Describe a UI change in plain language. The Editor Agent translates the instruction into precise DOM-level patches (CSS selector + action + value) and shows a live preview of the modified interface.

![Fix Generation](assets/fix_issue.png)

### Fix Evaluation

After applying a patch, the Preview Agent re-runs the affected simulation step and produces a Difference Report — comparing the agent's action before and after, and estimating whether the issue was resolved.

![Fix Evaluation](assets/evaluate.png)

---

## System Architecture

```
┌─────────────────────────────┐
│     Experiment Setup        │
│  Persona Traits + Goals     │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│     Simulation Phase        │
│  browser-use Agent          │
│  Raw HTML / Actions /       │
│  Screenshots / Reasoning    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│     Annotation Phase        │
│  Tagging Agent              │
│  Issue Detector Agent       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│     Refinement Phase        │
│  Editor Agent → DOM patches │
│  Preview Agent → re-sim     │
└─────────────────────────────┘
```

The frontend is built with **React 19 + TypeScript + Vite**, and the backend with **FastAPI + Python 3.13**.
Storage uses **PostgreSQL** for structured data and **MinIO / S3-compatible storage** for screenshots.

---

## Deployment to Hugging Face Docker Spaces

UXCascade can be deployed as a single application container on Hugging Face Docker Spaces listening on port `7860`.

### Required Environment Variables & Secrets

In your Hugging Face Space settings under **Variables** and **Secrets**, set the following:

#### Secrets (Sensitive Credentials)
- `DATABASE_URL`: PostgreSQL connection string (e.g. `postgresql://user:password@host:5432/dbname`)
- `ANTHROPIC_API_KEY`: API key for Anthropic Claude LLM models
- `MINIO_SECRET_KEY`: Access key secret for S3/MinIO storage

#### Variables (Public Configuration)
- `MINIO_ENDPOINT`: S3/MinIO endpoint URL (e.g. `https://s3.amazonaws.com` or custom MinIO endpoint)
- `MINIO_ACCESS_KEY`: S3/MinIO access key ID
- `MINIO_BUCKET`: Storage bucket name (default: `screenshots`)
- `MINIO_PUBLIC_URL`: Public URL accessible by browser clients to view stored screenshots
- `PORT`: Application port (default: `7860`)

---

## Quick Start (Local Docker Compose)

The easiest way to get everything running locally:

```bash
git clone https://github.com/your-org/UXCascade.git
cd UXCascade
```

Copy the backend environment file and fill in your API keys:

```bash
cp backend/.env.sample backend/.env
# Edit backend/.env and set ANTHROPIC_API_KEY
```

Start all services (PostgreSQL, MinIO, backend, frontend):

```bash
docker compose up --build -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 |

---

## Citation

If you use this implementation in your research, please cite the original paper:

```bibtex
@article{holter2026uxcascade,
  title   = {UXCascade: Scalable Usability Testing with Simulated User Agents},
  author  = {Holter, Steffen and Koh, Eunyee and Dogan, Mustafa Doga and Chan, Gromit Yeuk-Yin},
  journal = {arXiv preprint arXiv:2601.15777},
  year    = {2026},
  url     = {https://arxiv.org/abs/2601.15777}
}
```
---

## License

This implementation is released under the [MIT License](LICENSE).

The paper itself is published under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).
