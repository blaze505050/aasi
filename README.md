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
## Current Status: Phase 3 — Scientific Knowledge + Dataset Foundation

AASI has established a **provenance-first scientific knowledge and dataset foundation** (Phase 3) building upon its Phase 2 engineering tool intelligence:

### Core Architecture Principle: LLM $\neq$ Knowledge Omniscience
AASI is **not** an LLM trained on all aerospace knowledge. It is an orchestrating scientific assistant that grounds its reasoning in:
1. **Verified Literature & Technical Reports** (NASA NTRS, historical NACA reports, arXiv) with cryptographic provenance.
2. **Physical Datasets & Reference Results** (Wind tunnel measurements, peer-reviewed CFD benchmarks).
3. **Engineering Libraries & Solvers** (Astropy, RocketPy, SymPy) that execute actual calculations.
4. **Physics AI Neural Surrogates** (Abstract interfaces preparing for Phase 4 PINN/FNO models).

### Phase 3 Capabilities
- **Provenance-First Schema & Integrity**:
  - Cryptographic SHA-256 checksums, publishing organizations, report numbers, authors, publication years, source URLs, and license categories.
  - Unattributed scientific facts are never admitted to the knowledge base.
- **Scientific Object Taxonomy**:
  - Distinct types for `DOCUMENT`, `DATASET`, `EXPERIMENT`, `SIMULATION`, `SURROGATE`, `ANALYTICAL_RESULT`, and `RETRIEVED_REFERENCE` to prevent false equivalences (e.g. wind tunnel measurements $\neq$ simulation $\neq$ analytical equation).
- **Source Registry & Adapters**:
  - `NASA_NTRS`, `NACA`, `ARXIV`, `ESA`, `ISRO`, `OPEN_DATASETS`.
  - Transparent documentation of unautomated sources (e.g. ESA / ISRO portal restrictions).
- **Structure-Aware Chunking & Equation Preservation**:
  - Preserves section hierarchies, page numbers, and tables.
  - Extracts mathematical formulas in LaTeX and plain text with identified physical variables and units.
- **FAISS Vector Index & Hybrid Retrieval**:
  - Inner-product cosine similarity in 384-dimensional dense space.
  - Lexical scoring prioritizing exact aerospace identifiers ("NACA 0012", "Mach 0.3", "Re=500000", "RANS", "AoA").
  - Metadata filtering by organization, discipline, and year range.
- **Physical Dataset Registry & CFD Data Schema**:
  - `CFDDataModel`: Mach, Reynolds, AoA, turbulence models, $C_L, C_D, C_M, C_p$, mesh, and solver metadata.
  - `query_conditions`: Search experimental databases by flight conditions.
- **Numerical Question Resolution Hierarchy**:
  - Questions like *"What is the drag coefficient of NACA 0012 at Mach 0.3, Re=500000, AoA=8°?"* query verified databases and return exact reference data points ($C_D = 0.0142 \pm 0.0005$) with provenance, never fabricating numbers.
- **Adversarial & Prompt-Injection Quarantine**:
  - Untrusted document inputs are sanitized and quarantined in `<UNTRUSTED_REFERENCE_DATA>` XML blocks to prevent prompt-injection attacks.
- **Scientific Research UI**:
  - Interactive Research Catalog drawer with document search, cryptographic provenance inspection, and flow condition queries.

---

## Architecture Overview

```
User ──► Next.js Frontend ──► FastAPI ──► AASI Agent ──► Result-Resolution Hierarchy
                                                            ├── 1. Condition Search (Dataset Registry)
                                                            │     └── Exact Match? ──► Return Reference + Provenance
                                                            ├── 2. Engineering Tools (orbit, rocket, math)
                                                            │     └── Applicable? ──► Compute + SymPy Verify
                                                            └── 3. Hybrid Literature RAG (NASA/NACA/FAISS)
                                                                  └── Retrieved Passages ──► Grounded Answer + Citations
```

For complete architectural details, see [docs/architecture.md](docs/architecture.md) and [docs/knowledge/architecture.md](docs/knowledge/architecture.md).

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
