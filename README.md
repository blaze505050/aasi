# AASI — Autonomous Aerospace Scientific Intelligence

> **An experimental AI research assistant for aerospace engineering and space science.**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Technical & Responsible Framing

> **Notice:**  
> **AASI is not an AGI or ASI system.** It is an experimental aerospace-focused AI application built using open-source software and open-weight models.
>
> The long-term vision is autonomous scientific research and engineering assistance, but the current implementation is a conventional AI application built using an open-weight language model, software tools, and retrieval. AASI does not possess superintelligence, nor is it an engineering certification authority.

---

## What is AASI?

AASI is designed to assist aerospace students, researchers, and engineers in exploring technical concepts, formulating problems, deriving physical relations, and structuring engineering workflows across:
- Orbital mechanics & astrodynamics
- Rocket propulsion & trajectory modeling
- Fluid dynamics & atmospheric aerodynamics
- Spacecraft systems engineering & mission design

---

## Current Status: Phase 0 & Phase 1

This repository currently implements **Phase 0 (Project Foundation)** and **Phase 1 (Basic AI Intelligence)**:

### Current Capabilities
- **Decoupled Architecture**: High-performance FastAPI backend communicating with an open-weight LLM runtime via an asynchronous agent layer.
- **Local Model Execution**: Direct integration with Ollama for running open-weight models (e.g. Qwen 2.5 series) privately on local hardware without sending telemetry or prompts to third parties.
- **Engineered System Prompt**: Enforces technical transparency, explicit statement of assumptions and units, acknowledgement of uncertainty, and clear distinction between reasoning and computation.
- **Health & Diagnostic Probing**: Real-time inspection of backend health and Ollama connectivity at `/api/health`.
- **Interactive Developer UI**: Responsive Next.js TypeScript interface with live status indicators, markdown chat streaming, and session controls.

### Current Limitations (Phases 0 & 1)
- **No External Computational Tools Yet**: AASI cannot currently execute live numerical solvers, orbital propagators, or CFD runs.
- **No Scientific RAG / Document Retrieval**: Responses rely entirely on parametric weights of the underlying open-weight model; scientific paper indexing is scheduled for a later phase.
- **Not for Safety-Critical Systems**: Outputs must never be used as flight-critical decisions without external mathematical validation and human sign-off.

---

## Architecture Overview

```
User ──► Next.js Frontend ──► FastAPI Backend ──► AASI Agent Layer ──► Ollama (Local LLM) ──► Response
```

For complete architectural details, see [docs/architecture.md](docs/architecture.md).

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn, HTTPX, Pytest
- **Frontend**: Next.js (App Router), TypeScript, React, Vanilla CSS
- **Runtime**: Ollama (Open-weight models, e.g., `qwen2.5:3b`, `qwen2.5:7b`)
- **Version Control**: Git

---

## Getting Started

### 1. Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** & npm
- **Ollama**: [Download and install Ollama](https://ollama.com/)

### 2. Ollama Setup

Start the Ollama daemon and pull a lightweight model (e.g., Qwen 2.5):

```bash
# Start Ollama service (if not already running)
ollama serve

# Pull the default recommended model
ollama pull qwen2.5:3b
```

### 3. Backend Setup

```powershell
# In PowerShell (from project root)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# (Optional) Customize environment
cp backend/.env.example backend/.env

# Launch backend server
uvicorn backend.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.  
Health check: `http://localhost:8000/api/health`  
Interactive Swagger docs: `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## Running the Automated Tests

The test suite validates API contracts and error handling without needing a GPU or running Ollama instance (using mock HTTP responses):

```powershell
# From project root with venv activated
python -m pytest tests/ -v
```

---

## Development Roadmap

- [x] **Phase 0**: Foundation, project layout, Git setup, environment management.
- [x] **Phase 1**: Basic AI intelligence pipeline (Frontend → FastAPI → Agent → Ollama → Response).
- [ ] **Phase 2**: Scientific calculator & symbolic math tool integrations (SymPy, Pint).
- [ ] **Phase 3**: Orbital mechanics tool integration (Astropy, Poliastro).
- [ ] **Phase 4**: Rocketry & propulsion analysis tools (RocketPy).
- [ ] **Phase 5**: Aerospace RAG (NASA Technical Reports, ArXiv papers, aerospace standards).
- [ ] **Phase 6**: Verification engine & autonomous scientific research loops.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
