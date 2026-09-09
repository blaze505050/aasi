# AASI System Architecture

## Overview

**AASI (Autonomous Aerospace Scientific Intelligence)** is an experimental AI research assistant designed specifically for aerospace engineering, space science, and related computational disciplines.

> **Important Framing:**
> AASI is **not** an AGI, ASI, or superintelligence system. It is a domain-adapted AI assistant constructed with standard software engineering practices, open-weight language models, and structured orchestration.

---

## Current Architecture (Phase 0 & Phase 1)

In Phases 0 and 1, AASI establishes a robust, decoupled, and runnable baseline pipeline:

```
[ User ]
   │
   ▼
[ Next.js Frontend ] (TypeScript, React, Polished Developer Prototype)
   │
   │  HTTP / JSON (REST)
   ▼
[ FastAPI Backend ] (Validation via Pydantic, CORS, Logging)
   │
   ▼
[ AASI Agent Layer ] (System prompt conditioning, error handling, health probing)
   │
   │  HTTP (Ollama REST API: /api/chat & /api/tags)
   ▼
[ Ollama Runtime ] (Local model engine)
   │
   ▼
[ Open-Weight LLM ] (e.g. Qwen 2.5 series)
   │
   ▼
[ Structured Response ] ──► Back to User Interface
```

### Component Details

1. **Frontend (`frontend/`)**:
   - Built with Next.js and TypeScript.
   - Provides a clean, technical interface for researchers and engineers.
   - Features real-time backend/Ollama connection status, model indicators, error messaging, conversation history, and quick resets.

2. **Backend Gateway (`backend/main.py`)**:
   - Built with FastAPI and Uvicorn.
   - Enforces schema validation using Pydantic (`ChatRequest`, `ChatResponse`, `HealthResponse`).
   - Implements `/api/health` for monitoring system connectivity without exposing internal credentials.
   - Implements `/api/chat` for conversational interactions.

3. **AASI Agent Layer (`backend/agent.py`)**:
   - Decoupled from the HTTP transport layer.
   - Injects the domain-specific AASI system prompt (clarifying assumptions, stating uncertainties, disclaiming certification authority, and distinguishing model reasoning from verified calculations).
   - Asynchronously communicates with Ollama via `httpx.AsyncClient`.
   - Distinguishes network failures, missing models, and timeout events.

4. **Model Runtime (`Ollama`)**:
   - Runs locally on the host machine.
   - Serves open-weight models (e.g., `qwen2.5:3b`, `qwen2.5:7b`).
   - No proprietary API keys or external cloud dependencies required for inference.

---

## Future Architecture (Upcoming Phases)

Future phases will incrementally evolve AASI from a basic conversational assistant into an integrated scientific computing and research partner.

Planned architectural expansions include:

```
                          ┌───────────────────────────┐
                          │   AASI Scientific Agent   │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│  Scientific Tools   │      │   Retrieval & RAG   │      │ Verification Engine │
│ ─────────────────── │      │ ─────────────────── │      │ ─────────────────── │
│ • Orbital Mechanics │      │ • ArXiv & NASA NTRS │      │ • Dimensional Check │
│ • RocketPy Engine   │      │ • AIAA Papers       │      │ • Unit Sanity Tests │
│ • Aerodynamics / CFD│      │ • Vector DB Index   │      │ • Cross-Model Audit │
│ • Thermal Analysis  │      │ • Formula Parsing   │      │ • Code Sandbox      │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │ Autonomous Research Loops │
                          │ • Hypothesis formulation  │
                          │ • Iterative simulation    │
                          │ • Report generation       │
                          └───────────────────────────┘
```

### Planned Capabilities (Not implemented in Phase 0/1):

1. **Aerospace Computational Tools**:
   - **Orbital Mechanics**: Integrations with Astropy/Poliastro for ephemeris, delta-v budgets, and transfer orbits.
   - **Propulsion & Trajectory**: RocketPy simulations for solid/liquid motor performance and flight trajectories.
   - **Aerodynamics & CFD**: OpenFOAM or low-order panel methods for aerodynamic coefficients ($C_L, C_D, C_M$).

2. **Scientific Knowledge Retrieval (RAG)**:
   - Ingestion of peer-reviewed aerospace literature, NASA Technical Reports Server (NTRS), and engineering standards.
   - Grounded citations with direct document and equation links.

3. **Verification & Audit Subsystems**:
   - Unit and dimensional consistency validation (e.g. Pint / SymPy).
   - Multi-agent review passes to verify scientific reasoning before delivering engineering outputs.

4. **Autonomous Scientific Research Loops**:
   - Multi-step experimental planning, parameter sweeping, and automated synthetic report synthesis.
