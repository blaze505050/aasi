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

## Current Status: Phase 6 — Real Physics AI & Aerodynamic Surrogate

AASI has completed **Phase 6**, achieving genuine, measurable, and scientifically validated **Physics Intelligence** through `AeroSurrogateV1`:

```
                            ┌─────────────────────────────────────────┐
                            │          AASI Scientific Agent          │
                            │      (LLM Context & Orchestrator)       │
                            └────────────────────┬────────────────────┘
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          ▼                                      ▼                                      ▼
┌──────────────────────────────┐       ┌──────────────────────────────┐       ┌──────────────────────────────┐
│  LAYER A: KNOWLEDGE & SOURCES│       │  LAYER B: REAL PHYSICS AI    │       │  LAYER C: SIMULATION & COMP  │
│ ──────────────────────────── │       │ ──────────────────────────── │       │ ──────────────────────────── │
│ • 15 Scientific Disciplines  │       │ • AeroSurrogateV1 (Trained)  │       │ • ASME V&V 20 GCI Engine     │
│ • NASA NTRS & NACA Connectors│       │   (CL, CD, CM with bounds)   │       │ • Richardson Extrapolation   │
│ • ISRO / ESA Public Registrie│       │ • Epistemic Uncertainty OOD  │       │ • Multi-Backend Dispatch     │
│ • Strict SpaceX Claim Refusal│       │ • Leakage-Free Geometry Split│       │ • Standalone aasi_case/ Deck │
│ • Dynamic Current Events     │       │ • Dataset Authenticity Audit │       │ • Artifact Ingestion Service │
│ • 16-Entity Knowledge Graph  │       │ • Physics Sanity Invariants  │       │ • SHA-256 Checksum Integrity │
│ • Scientific Resolution L0-L7│       │ • Interactive SVG Polars     │       │ • OpenFOAM / SU2 Solvers     │
└──────────────────────────────┘       └──────────────────────────────┘       └──────────────────────────────┘
```

  - Authentic public registries: NASA NTRS, NACA, ISRO public releases, ESA open archive.
  - Strict corporate guardrail: Rejection of proprietary claims regarding SpaceX or commercial databases.
  - Dynamic temporal separation: `CURRENT_INFORMATION` (launches, mission updates, space weather) tagged with ISO timestamps.
  - Semantic Knowledge Graph: 16 scientific entity types linked by 10 directed relations.
- **Layer B (Physics AI & Dataset Factory):**
  - Curated open dataset factory (AirfRANS, NASA CRM, Abbott & von Doenhoff polars) with 2 GB quota.
  - `GeometryLevelSplitter`: Guarantees **0% geometry leakage** by strictly partitioning at the airfoil profile level.
  - `OODSplitter`: Generates out-of-domain evaluation splits (high AoA stall, transonic shock).
  - PhysicsNeMo exportable GPU recipes for AeroGraphNet (GNN) and 2D Fourier Neural Operator (FNO-2D).
  - `PhysicsModelRegistry`: Versioned surrogates with validity envelopes and SHA-256 weight hashes.
  - Physical monotonicity gates: Rejects surrogates violating pre-stall lift monotonicity ($dC_L/d\alpha > 0$) or symmetry.
  - Active learning engine: Sweeps parameter space and ranks simulation candidates in high-uncertainty regimes.
- **Layer C (Deterministic Engineering & Standalone User CFD):**
  - Standalone `aasi_case/` generator: Writes complete OpenFOAM dictionary decks (`0/`, `constant/`, `system/`), mesh files (`blockMeshDict`), shell runners (`run.sh`, `clean.sh`), and the mandatory 14-section `README.md`.
  - Artifact ingestion service: Parses OpenFOAM `forceCoeffs.dat`, SU2 CSV, or XFOIL polars, verifies physical bounds ($C_D > 0, |C_L| \le 3.5$), and records SHA-256 provenance hashes.
  - 8-level deterministic scientific resolution hierarchy with strict epistemic classification.

---

## Architecture Documentation

For in-depth architectural and mathematical specifications, see:
- [docs/phase6/README.md](docs/phase6/README.md) — Phase 6 Real Physics-AI Architecture & Validation
- [docs/model-cards/aero_surrogate_v1.md](docs/model-cards/aero_surrogate_v1.md) — AeroSurrogateV1 Standardized Model Card
- [docs/architecture.md](docs/architecture.md) — System Architecture & Tri-Layer Framework
- [docs/knowledge-federation.md](docs/knowledge-federation.md) — 15 Disciplines, Authentic Sources & Current Events
- [docs/dataset-factory.md](docs/dataset-factory.md) — Open Physics Datasets & Leakage-Free Geometry Splitting
- [docs/physics-ai-training.md](docs/physics-ai-training.md) — PhysicsNeMo Foundation, Registry & Active Learning
- [docs/user-executed-cfd.md](docs/user-executed-cfd.md) — Standalone Case Deck Generation & Artifact Ingestion
- [docs/scientific-resolution.md](docs/scientific-resolution.md) — Deterministic Resolution Hierarchy & Epistemic Tags
- [docs/validation.md](docs/validation.md) — Test Suite & Physical Validation Benchmarks


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
