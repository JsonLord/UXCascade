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
Storage uses **PostgreSQL** for structured data and **MinIO** for screenshots.

---

## Requirements

| Component | Version |
|---|---|
| Node.js | >= 20.19 (or 22+) — Node 18 is **not** supported |
| pnpm | >= 10 |
| Python | >= 3.13 |
| uv | >= 0.6 |
| Docker + Docker Compose | for the recommended setup |

---

## Quick Start (Docker)

The easiest way to get everything running:

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
docker compose up --build
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
