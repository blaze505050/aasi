# AASI 2.0 — 00. Repository Audit & Baseline

**Audit Date**: 2026-10-25  
**Version**: AASI 2.0-Alpha  
**Authoritative Repository**: `github.com/blaze505050/aasi` at commit `964f970`  
**Governing Doctrine**: Absolute Anti-Fabrication Rule (Fail-Closed)

---

## 1. Directory Structure

```
AASI/
├── .agents/skills/            # 6 Built-in aerospace validation and review skills
├── backend/
│   ├── agent/                 # Investigation state machine, controller, planner
│   ├── api/                   # 25+ FastAPI router endpoints (REST API)
│   ├── auth/                  # Bearer tokens & session credentials
│   ├── cfd/                   # OpenFOAM meshing, boundary conditions, case templates
│   ├── cognitive/             # Epistemic memory, model zoo, inquiry mesh
│   ├── compliance/            # ASME V&V 20 and NASA-STD-7009B alignment
│   ├── compute/               # Compute provider routing (Local, Colab, WSL, Remote)
│   ├── config.py              # Application settings and environment bounds
│   ├── dataset/               # CFD catalog, metadata stores, dataset factory
│   ├── export/                # DATCOM, NASA S/HABP, 6-DOF simulation tables
│   ├── governor/              # ResourceMonitor, SafetyGovernor, KillSwitch, Budgets
│   ├── harness/               # TaskHarness, ToolBus, ToolProtocol, Core Skills
│   ├── main.py                # FastAPI ASGI application entry point (3,100+ lines)
│   ├── modules/               # Airfoil 2D, VLM 3D, and multidisciplinary modules
│   ├── physics/               # Vortex panel solver, boundary layer, benchmarks
│   ├── physics_ai/            # AeroSurrogateV1 neural & ridge surrogate models
│   ├── research/              # Reproduction verifiers, governance auditors
│   ├── runner/                # Local runner agent, capabilities detector, sandbox
│   ├── science/               # Epistemic kernel, Merkle lineage DAG, evidence store
│   ├── scientific_compiler/   # DAG runtime scheduler, task compiler
│   ├── scientific_language/   # AML lexer, AST parser, validator, serializer
│   └── tools/                 # Engineering calculators (rocket, orbit, math, units)
├── data/                      # NACA coordinates, scientific memory, Merkle nodes
├── docs/                      # Scientific reports, architecture maps, audits
├── frontend/                  # Next.js 14 React UI (Tailwind CSS, Lucide, KaTeX)
├── runner/                    # Standalone runner daemon package
├── sdk/                       # Python client SDK for AASI API
└── tests/                     # 108+ pytest test suites covering physics, API, & harness
```

---

## 2. Backend & Frontend Entry Points

- **Backend API**: `backend/main.py:app` — FastAPI application mounting `/api/*` and `/api/v1/*` routers. Started via `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
- **Frontend Web UI**: `frontend/` — Next.js 14 App Router on Node 20+, connecting to backend REST endpoints. Started via `npm run dev` or Vercel edge deployment.
- **Local Runner Daemon**: `runner/cli.py` — Background workstation worker that polls persistent jobs and dispatches OpenFOAM/Python solvers in an isolated sandbox.

---

## 3. Persistence & Provenance Architecture

- **Primary Databases**: SQLite3 (`aasi.db`) for investigation states, jobs, user credentials, and experiment runs.
- **Scientific Memory**: JSON-backed vector and keyword epistemic memory (`data/scientific_memory.json`, `data/epistemic_memory.json`).
- **Merkle Lineage Tree**: Directed acyclic graph (`data/merkle_lineage.json`) recording every investigation step, computational code checksum, solver input, output, and parent link with SHA-256 signatures.

---

## 4. Test Baseline & Regression Verification

- **Baseline Test Suite**: 108 test files in `tests/` covering panel solvers, ASME V&V 20 grid convergence, aerodynamic database generation, Merkle lineage, and API routes.
- **Phase 1 Validation**: 22/22 dedicated tests passing cleanly in `tests/test_governor_security.py` and `tests/test_agent_harness_integration.py`.
