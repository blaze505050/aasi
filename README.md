# AASI — Autonomous Aerospace Scientific Intelligence

> **An experimental AI research assistant for aerospace engineering and space science.**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Astropy](https://img.shields.io/badge/Astropy-6.0+-orange.svg)](https://www.astropy.org/)
[![RocketPy](https://img.shields.io/badge/RocketPy-1.13+-red.svg)](https://rocketpy.org/)
[![SymPy](https://img.shields.io/badge/SymPy-1.14+-darkblue.svg)](https://www.sympy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Technical & Responsible Framing

> **Notice:**  
> **AASI is not an AGI or ASI system.** It is an experimental aerospace-focused AI application built using open-source software and open-weight models.
>
> The long-term vision is autonomous scientific research and engineering assistance, but the current implementation is an educational and research prototype. AASI does not possess superintelligence, nor is it an engineering certification authority.
>
> **Core Architectural Principle: LLM $\neq$ Calculator**  
> Large Language Models are used for natural language understanding, intent recognition, parameter extraction, and explanatory synthesis. Verified open-source engineering libraries (`Astropy`, `RocketPy`, `SymPy`, `Scipy`) execute all actual mathematical computations. AASI never allows the language model to invent or fabricate calculations.

---

## Current Status: Phase 2 — Engineering Tool Intelligence

AASI has evolved from a conversational prototype (Phases 0 & 1) into a tool-using engineering assistant (Phase 2):

### Capabilities
- **Orbital Mechanics Tool (`orbit`)**:
  - Precision two-body Keplerian calculations backed by Astropy constants.
  - Circular orbital velocity, orbital period, escape velocity.
  - Planar Hohmann transfer Delta-v requirements ($\Delta v_1, \Delta v_2, \Delta v_{total}$) and transfer duration.
  - Multi-body support (Earth, Moon, Mars, Sun).
- **Rocket Propulsion Tool (`rocket`)**:
  - Ideal Tsiolkovsky rocket equation ($\Delta v = g_0 I_{sp} \ln(m_0/m_f)$).
  - Required mass ratio and propellant fraction for target Delta-v.
  - Preliminary propellant mass estimation.
  - Standard SI gravity constants ($g_0 = 9.80665\text{ m/s}^2$).
- **Symbolic Mathematics & Verification (`math`)**:
  - SymPy-backed symbolic algebra and analytical equation solving.
  - Independent numerical verification layer re-computing results from first principles.
- **Execution Tracing**: Transparent, user-safe execution traces displayed in the UI without exposing internal chain-of-thought.
- **Dynamic Tool Registry**: Extensible catalog accessible via `GET /api/tools`.
- **Hardware-Aware Local Execution**: Configured by default for lightweight local models (e.g. `qwen2.5:0.5b`) running via Ollama.
- **Deterministic Engineering Benchmarks**: 33 automated tests and physics benchmarks with documented tolerances.

---

## Architecture Overview

```
User ──► Next.js Frontend ──► FastAPI ──► AASI Agent ──► Tool Selection
                                                            ├── orbit.py (Astropy)
                                                            ├── rocket.py (RocketPy)
                                                            └── math_utils.py (SymPy)
                                                            │
                                                            ▼
                                                     Exact Computation
                                                            │
                                                            ▼
                                                   LLM Synthesis (Ollama)
                                                            │
                                                            ▼
                                              Trace + Results + Explanation
```

For complete architectural details, see [docs/architecture.md](docs/architecture.md).

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn, HTTPX, Pytest
- **Scientific Libraries**: Astropy, RocketPy, SymPy, SciPy, NumPy, Pint
- **Frontend**: Next.js (App Router), TypeScript, React, Vanilla CSS
- **Runtime**: Ollama (e.g., `qwen2.5:0.5b`, `qwen2.5:3b`)
- **Version Control**: Git & GitHub

---

## Getting Started

### 1. Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** & npm
- **Ollama**: [Download and install Ollama](https://ollama.com/)

### 2. Ollama Setup

Start the Ollama daemon and pull the lightweight model:

```bash
# Start Ollama service (if not running)
ollama serve

# Pull the lightweight model (recommended for laptops)
ollama pull qwen2.5:0.5b
```

### 3. Backend Setup

```powershell
# From project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run backend
python -m uvicorn backend.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/api/health`
- Tool Catalog: `http://localhost:8000/api/tools`
- Swagger Docs: `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Running the Automated Tests & Benchmarks

The automated test suite runs completely offline without requiring a GPU or active model:

```powershell
# Run full unit and integration test suite
python -m pytest tests/ -v

# Run deterministic engineering benchmarks
python -m pytest tests/benchmarks/ -v
```

---

## Development Roadmap

- [x] **Phase 0**: Foundation, project layout, Git setup, environment management.
- [x] **Phase 1**: Basic AI intelligence pipeline (Frontend → FastAPI → Agent → Ollama → Response).
- [x] **Phase 2**: Real engineering tool intelligence (Astropy orbit tools, RocketPy propulsion sizing, SymPy symbolic verification, execution traces).
- [ ] **Phase 3**: Aerospace scientific literature retrieval & RAG (NASA NTRS, ArXiv, AIAA papers).
- [ ] **Phase 4**: Multi-agent verification engine & dimensional auditing.
- [ ] **Phase 5**: Autonomous scientific research loops and simulation parameter sweeps.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
