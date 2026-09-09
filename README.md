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
## Current Status: Phase 4 — Scientific Result Resolution + Simulation Fabric

AASI has established a deterministic **8-level scientific result resolution hierarchy** and a secure **simulation execution fabric** (Phase 4), building upon its Phase 2 engineering tools and Phase 3 knowledge & dataset foundation:

### Core Architecture Principle: LLM $\neq$ CFD Solver $\neq$ Numerical Truth
AASI is **not** an LLM that fabricates numerical engineering quantities when no dataset exists. It is an orchestrating scientific assistant that enforces strict epistemic classification and deterministic resolution:

```
Natural Language Engineering Query
               │
               ▼
Level 0: Query Normalization & Completeness Audit (Mach, Re, AoA, flow regime, geometry)
               │
               ▼
Level 1: Scientific Dataset Registry Query
               │
               ▼
Level 2: Official Experimental Database (NASA TN-D-628 wind-tunnel polars)
               │
               ▼
Level 3: Validated CFD Benchmark Database (OpenFOAM RANS, y+ < 1, residual convergence)
               │
               ▼
Level 4: Validated Physics AI Surrogate Models (AeroGraphNet within declared envelope)
               │
               ▼
Level 5: Analytical / Numerical Engineering Solvers (Astropy, RocketPy, SymPy)
               │
               ▼
Level 6: Simulation Execution Fabric (OpenFOAM simpleFoam case generator, dry-run mode)
               │
               ▼
Level 7: Parameter Clarification Request (Never fabricates numbers; prompts for missing conditions)
```

### Phase 4 Capabilities
- **Deterministic 8-Level Resolution Hierarchy**:
  - All quantitative questions pass through `ScientificResolutionEngine` before LLM synthesis.
  - Normalized flow conditions: Mach, Reynolds, AoA, flow regime, Pint-based unit conversions, and geometry canonicalization.
- **Epistemic Classification System**:
  - Explicit tags on every result: `OFFICIAL_EXPERIMENT`, `VALIDATED_CFD`, `SURROGATE_PREDICTION`, `ANALYTICAL_RESULT`, `LOCAL_CFD`, `DEMO_DATA`, `NO_RESULT`.
- **Multi-Source Conflict Resolution & Physical Reconciliation**:
  - Detects differences between experimental and computational data points.
  - Automatically reconciles discrepancies through physical aerodynamic phenomena (boundary layer tripping, wind tunnel wall blockage, eddy-viscosity damping).
- **Physics AI Surrogate Registry & Domain Envelope Enforcement**:
  - `SurrogateRegistry` evaluates physics models strictly within declared valid parameter envelopes.
  - Rejects out-of-domain queries with `SURROGATE_OUT_OF_DOMAIN`.
- **Simulation Execution Fabric & Security Sandbox**:
  - Probes host and WSL2 for OpenFOAM, SU2, XFOIL, XFLR5 without pretending uninstalled solvers are available.
  - Secure sandbox: executable allowlisting (`simpleFoam`, `blockMesh`, `SU2_CFD`, `xfoil`), working-directory isolation under `data/simulations/{case_id}/`, timeouts, and path traversal protection.
  - `DRY_RUN` mode generates authenticated case decks (`0/`, `constant/`, `system/`), validates boundary conditions, and outputs cryptographically signed manifests `EXP-{case_id}.manifest.json`.
- **Reproducible Artifact Manifests**:
  - SHA-256 hashes of all input files, mesh dictionaries, commands, and outputs.

---

## Architecture Overview

```
User ──► Next.js Frontend ──► FastAPI ──► AASI Agent ──► 8-Level Scientific Resolution Engine
                                                            ├── Level 0: Query Normalization
                                                            ├── Level 1: Dataset Registry
                                                            ├── Level 2: Official Experiments (NASA TN-D-628)
                                                            ├── Level 3: Validated CFD (OpenFOAM RANS)
                                                            ├── Level 4: Surrogate Registry (AeroGraphNet)
                                                            ├── Level 5: Analytical Solvers (Astropy, RocketPy)
                                                            ├── Level 6: Simulation Fabric (Sandboxed OpenFOAM)
                                                            └── Level 7: Parameter Clarification
```

For complete architectural details, see:
- [docs/architecture.md](docs/architecture.md) — System Architecture & Data Flow
- [docs/scientific-resolution.md](docs/scientific-resolution.md) — Resolution Hierarchy & Epistemic Tags
- [docs/simulation-architecture.md](docs/simulation-architecture.md) — Simulation Execution Fabric & Sandbox
- [docs/solver-adapters.md](docs/solver-adapters.md) — OpenFOAM, SU2, XFOIL, XFLR5 Adapters
- [docs/validation.md](docs/validation.md) — Test Suite & Physical Validation Benchmarks
- [docs/phase4-validation.md](docs/phase4-validation.md) — Phase 4 Acceptance Criteria Checklist

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn, HTTPX, Pytest
- **Knowledge & Retrieval**: FAISS (`faiss-cpu`), PyPDF, Dense Semantic Embeddings
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
- Knowledge Sources: `http://localhost:8000/api/knowledge/sources`
- Knowledge Documents: `http://localhost:8000/api/knowledge/documents`
- Physical Datasets: `http://localhost:8000/api/knowledge/datasets`
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
# Run full unit and integration test suite (141 tests)
python -m pytest tests/ -v
```

---

## Development Roadmap

- [x] **Phase 0**: Foundation, project layout, Git setup, environment management.
- [x] **Phase 1**: Basic AI intelligence pipeline (Frontend → FastAPI → Agent → Ollama → Response).
- [x] **Phase 2**: Real engineering tool intelligence (Astropy orbit tools, RocketPy propulsion sizing, SymPy symbolic verification, execution traces).
- [x] **Phase 3**: Scientific Knowledge + Dataset Foundation (NASA NTRS/NACA ingestion, FAISS vector indexing, provenance-first schemas, CFD data models, condition lookup, prompt-injection defense).
- [ ] **Phase 4**: Physics AI Models & Neural Surrogates (PINN, PINO, FNO, GNN training & inference).
- [ ] **Phase 5**: Simulation Engines & Autonomous Scientific Research Loops (OpenFOAM, SU2, XFOIL integration).

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
