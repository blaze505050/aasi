# AASI Repository Inventory — Phase A Audit

**Auditor:** Antigravity IDE (Claude Opus 4.6)
**Date:** 2026-10-16
**Commit:** `5b0a5da` (main, clean working tree)
**Method:** Direct file inspection, `git log`, and dependency analysis

---

## 1. Repository Overview

| Metric | Value |
|---|---|
| **Root Files** | 10 |
| **Top-Level Directories** | 16 |
| **License** | MIT (Copyright © 2025 AASI Contributors) |
| **Python Version** | 3.12 |
| **Backend Framework** | FastAPI + Pydantic v2 + Uvicorn |
| **Frontend Framework** | Next.js 14 (App Router) + React 18 + TypeScript 5.6 |
| **LLM Integration** | Ollama (qwen2.5:0.5b default) |
| **Commit Count (last 20)** | 20+ phases of development visible |
| **Test Files** | 102 test files + 1 benchmark directory |
| **Documentation Files** | 99 markdown files in `docs/` |
| **Backend `main.py` Size** | 3,040 lines / 127 KB |

---

## 2. Directory Structure

### Root Level
```
.env.example               — Production environment template
.github/workflows/          — CI (1 workflow: aerodynamic certification)
.gitignore                 — Standard Python/Node ignore rules
AASI Launch Plan From Repo to Revenue.md — Business planning document
AASI_MVP_Master_Plan/      — MVP planning artifacts
Document (1).docx          — Unknown document (binary)
LICENSE                    — MIT License
NACA0012_ASME_VV20_Certification.pdf — Verification certification (4.7 KB)
README.md                  — 243 lines, comprehensive technical README
aasi_runner_workspace/     — Runner workspace artifacts
backend/                   — FastAPI backend (30 subdirectories, 6 files)
data/                      — Data stores, databases, checkpoints, datasets
docker-compose.yml         — 3-service Docker stack (backend, frontend, Redis)
docs/                      — Extensive documentation (99 files, 8 subdirectories)
frontend/                  — Next.js frontend application
run_aasi.bat               — Windows launcher
run_aasi.py                — Unified cross-platform launcher (7.3 KB)
runner/                    — Task runner infrastructure
scratch/                   — Scratch/temp artifacts
scripts/                   — Utility scripts (3 files)
sdk/                       — Python SDK
tests/                     — Test suite (102 files, 2 subdirectories)
training/                  — PhysicsNeMo training recipes
```

### Backend Module Inventory (30 subdirectories)

| Module | Files | Key Classes/Functions | Purpose |
|---|---|---|---|
| `agent/` | 20 files | `AASIAgent`, `ScientificAnswer`, `InvestigationGraph`, `Orchestrator` | Agent orchestration, investigation lifecycle, scientific resolution |
| `api/` | 25 route files | `api_router`, `api_v1_router` | REST API route definitions (aerodb, auth, cognitive, commercial, compute, etc.) |
| `auth/` | 7 files | `SecurityManager`, `GovernanceGuard` | PBKDF2 auth, session tokens, API keys, SSO |
| `cfd/` | — | — | CFD integration (to verify) |
| `cognitive/` | 12 files | `HypothesisEngine`, `ModelZoo` (84 KB!), `CognitiveOrchestrator` | AI reasoning, hypothesis generation, model zoo |
| `compliance/` | — | — | Compliance modules (to verify) |
| `compute/` | — | — | Compute routing, hardware matrix |
| `config.py` | 1 file | `Settings`, `AASI_SYSTEM_PROMPT` | Pydantic-based settings |
| `dataset/` | 9 files | `catalog`, `ingestion`, `object_store`, `provenance` | Dataset management, CAS, ingestion pipeline |
| `datasets/` | — | — | Separate datasets module (authentic parsers) |
| `deployment/` | — | — | Deployment configuration |
| `export/` | — | — | Export formats (DATCOM, S/HABP, 6-DOF CSV) |
| `graph/` | — | — | Knowledge graph |
| `knowledge/` | 15 files | `RAG`, `VectorStore`, `Retriever`, `Reranker`, `SeedCorpus` | Scientific knowledge retrieval with FAISS |
| `llm/` | — | — | LLM integration layer |
| `main.py` | 3,040 lines | FastAPI `app`, 80+ route handlers | **Monolithic entry point** |
| `multifidelity/` | — | — | Multi-fidelity modeling |
| `observability/` | — | — | Observability/monitoring |
| `physics/` | 17 files | `AerodynamicPanelSolver`, `AirfoilParser`, `AeroDBEngine`, `ModelRegistry`, `Benchmark` | Core physics engine (panel method, airfoil geometry, aero database) |
| `physics_ai/` | 38 files | `AeroSurrogateV1`, `Training`, `Inference`, `Splits`, `Uncertainty`, `Validation` | ML surrogate models, training, inference, OOD detection |
| `research/` | — | — | Research investigation modules |
| `science/` | — | — | Science resolution engine |
| `scientific_compiler/` | 3 files | `Compiler`, `DAG` | Scientific query compilation to DAGs |
| `scientific_language/` | — | — | AML language parsing |
| `scientific_runtime/` | — | — | Runtime execution engine |
| `simulation/` | 14 files | `SimulationExecutor`, `GridStudy`, `Sandbox`, `Parsers` | CFD simulation management (OpenFOAM, SU2) |
| `sources/` | — | — | Federated source connectors (NASA, arXiv, ISRO, ESA) |
| `storage/` | — | — | Storage abstraction |
| `tools/` | 7 files | `ToolRegistry`, `MathUtils`, `Orbit`, `Rocket`, `Units` | Engineering tool registry |
| `training/` | — | — | Training infrastructure |
| `validation/` | 2 files | `GridConvergence` (ASME V&V 20) | Grid convergence index computation |

### Frontend Component Inventory (33 components)

| Component | Size | Purpose |
|---|---|---|
| `InvestigationWorkspace.tsx` | 84 KB | Main workspace (largest component) |
| `ModelZooExplorer.tsx` | 44 KB | Model registry browser |
| `ThreeDimensionalPressureMesh.tsx` | 34 KB | 3D pressure visualization (Three.js) |
| `ConnectedPipelineWorkspace.tsx` | 33 KB | Pipeline execution workspace |
| `AuthModal.tsx` | 31 KB | Authentication UI |
| `CognitiveBrainWorkspace.tsx` | 30 KB | Cognitive AI workspace |
| `CommercialBillingPanel.tsx` | 26 KB | Commercial billing UI |
| `AeroDbPanel.tsx` | 24 KB | Aerodynamic database panel |
| `EnterpriseOverviewModal.tsx` | 24 KB | Enterprise features modal |
| `AirfoilOptimizationStudio.tsx` | 23 KB | Airfoil optimization studio |
| `InteractivePolarPlot.tsx` | 21 KB | Polar plot visualization |
| `ReportExportModal.tsx` | 20 KB | Report generation/export |
| `FlightCertificationModal.tsx` | 19 KB | Certification modal |
| `AerodynamicFlowfieldVisualizer.tsx` | 16 KB | Flow field visualization |
| `ScientificResultPanel.tsx` | 16 KB | Scientific results display |
| `MissionControlSidebar.tsx` | 14 KB | Navigation sidebar |
| `EnterpriseTelemetryDashboard.tsx` | 15 KB | Enterprise telemetry |
| `AuditTrailModal.tsx` | 14 KB | Audit trail viewer |
| `InvestigationComparisonPanel.tsx` | 12 KB | Investigation comparison |
| `OnboardingGuideModal.tsx` | 12 KB | Onboarding guide |
| `HypothesisCardDeck.tsx` | 11 KB | Hypothesis cards |
| `SurrogateInferencePanel.tsx` | 10 KB | Surrogate inference UI |
| `ComputeFabricPanel.tsx` | 10 KB | Compute fabric panel |
| `CommandPaletteModal.tsx` | 10 KB | Command palette |
| `MemoryLedgerPanel.tsx` | 9 KB | Memory/history ledger |
| `InvestigationStatusBar.tsx` | 9 KB | Status bar |
| `ColabExecutionPanel.tsx` | 9 KB | Google Colab execution |
| `ExperimentPlannerPanel.tsx` | 8 KB | Experiment planning |
| `EvidenceTierBadge.tsx` | 7 KB | Evidence tier badges |
| `ChatPanel.tsx` | 7 KB | Chat interface |
| `ExecutionTimeline.tsx` | 7 KB | Execution timeline |
| `AerodynamicKpiCards.tsx` | 6 KB | KPI cards |
| `AirfoilVisualizer.tsx` | 11 KB | Airfoil geometry visualization |

### Data Directory

| Path | Type | Purpose |
|---|---|---|
| `data/airfoils/` | 5 .dat + 1 .csv | Curated benchmark airfoil profiles (NACA0012, RAE2822, Clark-Y, Eppler E387, UAV) |
| `data/datasets/` | Directory | Dataset storage (authentic airfoils, etc.) |
| `data/checkpoints/` | Directory | Model weight checkpoints |
| `data/training_runs/` | Directory | Training run artifacts |
| `data/aasi_investigations.db` | 1.2 MB SQLite | Investigation state database |
| `data/aasi_commercial.db` | 49 KB SQLite | Commercial/billing database |
| `data/aasi_audit_log.db` | 82 KB SQLite | Audit log database |
| `data/cognitive_memory.json` | 61 KB | Cognitive AI memory |
| `data/epistemic_memory.json` | 253 KB | Epistemic memory state |
| `data/scientific_memory.json` | 77 KB | Scientific memory state |
| `data/merkle_lineage.json` | 462 KB | Merkle DAG provenance chain |
| `data/empirical_ledger.json` | 4.7 KB | Empirical evidence ledger |

### Dependencies

**Backend (requirements.txt):**
```
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.30.0,<1.0.0
pydantic>=2.8.0,<3.0.0
pydantic-settings>=2.4.0,<3.0.0
httpx>=0.27.0,<1.0.0
pytest>=8.3.0,<9.0.0
pytest-asyncio>=0.24.0,<1.0.0
numpy>=1.26.0
scipy>=1.12.0
sympy>=1.12
pint>=0.23
astropy>=6.0.0
rocketpy>=1.13.0
faiss-cpu>=1.15.0
pypdf>=6.18.0
```

**Frontend (package.json):**
```json
{
  "next": "^14.2.15",
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "three": "^0.186.1",
  "@types/three": "^0.186.0",
  "lucide-react": "^1.48.0",
  "typescript": "^5.6.2"
}
```

### CI/CD

- **Workflow:** `.github/workflows/aasi_aerodynamic_certification.yml`
- **Trigger:** Push to `main`/`release/**`, PR to `main`
- **Steps:** Install deps → Launch backend → Health check → ASME V&V 20 verification → Cryptographic audit → Polar sweep
- **Issue:** References `aasi` CLI commands that may depend on uninstalled SDK

### Docker

- 3-service `docker-compose.yml`: backend, frontend, Redis
- Backend Dockerfile: `backend/deployment/Dockerfile.backend`
- Frontend Dockerfile: `frontend/Dockerfile`

---

## 3. Key Observations

1. **Monolithic `main.py`**: The backend entry point is 3,040 lines with 80+ route handlers defined inline. This should be refactored into the existing `api/routes_*.py` modular structure.

2. **Extensive Feature Surface**: 33 frontend components, 25 API route modules, 30 backend subdirectories — extremely broad feature surface for an early-stage project.

3. **Model Zoo (84 KB)**: `cognitive/model_zoo.py` is a very large file that requires detailed inspection for actual vs. documented models.

4. **Pure NumPy ML**: `AeroSurrogateV1` is implemented in pure NumPy with manual backpropagation — admirable for portability but limits model capacity and training speed.

5. **No PyTorch/TensorFlow dependency**: All ML is self-contained in NumPy, which is a deliberate design choice for zero-DLL deployment.

6. **PhysicsNeMo**: `training/physicsnemo/` contains only a `README.md` — no actual training recipes or model code.

7. **Multiple State Files**: Several JSON files in `data/` store persistent state (memory, lineage, ledger) without clear migration or versioning strategy.

8. **SDK**: `sdk/python/` exists but contents need verification. CI workflow references `aasi cert verify` and `aasi audit verify` commands.

9. **Security Infrastructure**: PBKDF2-HMAC-SHA256 password hashing, HMAC session tokens, API key management, rate limiting configuration — all present but need depth verification.

10. **Docker Composition**: Uses Redis for job queuing but the backend code doesn't clearly reference Redis as a hard dependency in `requirements.txt`.
