# AASI Phase 28: Comprehensive Repository Autonomy & Integration Audit

## Executive Summary
This document constitutes the formal **Phase 28 Autonomy & System-Integration Audit** of the Autonomous Aerospace Scientific Intelligence (AASI) codebase. The audit evaluates the end-to-end scientific autonomy loop across all system tiers—from user query parsing to multi-fidelity comparison, remote CFD staging, error diagnosis, non-mutating repair, and public web interface.

AASI has built strong foundations across Phase 1 through Phase 27:
- Deterministic 8-level scientific resolution hierarchy in `backend/science/engine.py`.
- 17-state machine in `backend/agent/orchestrator.py` and 15-state persistent job queue in `backend/compute/queue.py`.
- Automated OpenFOAM 10 case deck synthesis and Jupyter notebook packaging in `backend/compute/colab_session.py`.
- 11-class error diagnostics in `backend/agent/diagnostics.py` and bounded non-mutating repairs in `backend/agent/repair_engine.py`.
- Content-addressed storage (CAS) with SHA-256 prefix sharding in `backend/dataset/object_store.py` and `backend/storage/object_store.py`.
- PBKDF2-HMAC-SHA256 authentication, signed session tokens (`aasi_tok_`), and multitenant resource quotas in `backend/auth/`.
- 595 passing automated test cases across the repository.

However, the audit reveals specific **architectural gaps and loose couplings** that prevent the full autonomous loop from operating as a unified scientific researcher. This audit catalogs what works, what is partial, what is staged, and the exact integration fixes required for Phase 28.

---

## 1. Audit Findings by System Component

### A. Frontend Architecture
- **Current State**: Built with Next.js 14, Tailwind CSS, Lucide icons, and React 18 in `frontend/`.
- **Key Components**:
  - `frontend/components/InvestigationWorkspace.tsx`: Comprehensive scientific workspace with query input, progress tracker, multi-fidelity comparison table, Colab execution panel, and result import interface.
  - `frontend/components/ExecutionTimeline.tsx`: Visualizes state progression milestones.
  - `frontend/components/ScientificResultPanel.tsx`: Polar curves and aerodynamic coefficient tables.
  - `frontend/components/ColabExecutionPanel.tsx`: 1-click execution instructions.
- **Audit Findings**:
  - *What Works*: Clean responsive UI, SSE event streaming listener, one-click Colab copy/launch links, file upload drag-and-drop.
  - *What is Partial*: The primary page (`frontend/app/page.tsx`) contains historical panels from earlier phases alongside `InvestigationWorkspace`. It must present a unified experience: *"What aerospace problem are you trying to solve?"* with transparent timeline progression (`UNDERSTANDING` $\to$ `PLANNING` $\to$ `RETRIEVING DATA` $\to$ `SELECTING METHOD` $\to$ `COMPUTING` $\to$ `VALIDATING` $\to$ `INVESTIGATING` $\to$ `SYNTHESIZING`).
  - *Missing*: Concise scientific status explanations without raw chain-of-thought dumps.

### B. Backend Architecture & API Routing
- **Current State**: FastAPI control plane in `backend/main.py` with modular sub-routers in `backend/api/` (`auth`, `compute`, `dataset`, `investigation`, `jobs`, `results`, `observability`).
- **Audit Findings**:
  - *What Works*: All routers are modularized and mount clean `/api` endpoints.
  - *What is Partial*: Both `/api` and `/api/v1` prefixes exist in `backend/api/__init__.py`, but `api_v1_router` was not explicitly mounted in `backend/main.py`. Both must be mounted for consistent versioned access.
  - *Missing*: Dedicated canonical investigation endpoints (`/api/v1/investigations/`) returning the unified canonical `Investigation` object.

### C. Scientific Intent & Problem Decomposition
- **Current State**: `ScientificPlanner.parse_objective` in `backend/agent/planner.py` uses regex heuristics for airfoil geometry, angle of attack, Reynolds number, and Mach number.
- **Audit Findings**:
  - *What Works*: Accurately extracts `NACA 0012`, `NACA 4412`, `RAE 2822`, AoA, Re, Mach, and required variables (`CL`, `CD`, `CM`, `Cp`).
  - *What is Partial*: If the user specifies an alpha range (e.g., `-5 to 15 degrees`), the planner previously parsed only a single angle. Problem decomposition should support parameter sweeps or multi-point evaluations.
  - *Missing*: Explicit decomposition into scientific intent, governing physics, assumptions, and required state variables in a unified investigation schema.

### D. Method Selection & Fidelity Determination
- **Current State**: `FidelityDecisionEngine` in `backend/agent/decision_engine.py` evaluates distance to database training points and surrogate uncertainty.
- **Audit Findings**:
  - *What Works*: Classifies database distance (`HIGH`, `MEDIUM`, `LOW`, `NONE`) and surrogate uncertainty (`LOW`, `MEDIUM`, `HIGH`).
  - *What is Missing*: Step 3 mandates an **explicit, explainable Method-Selection Decision Record** selecting among:
    `DATABASE_REAL`, `SURROGATE`, `ANALYTICAL`, `LIVE_CFD`, `USER_PROVIDED`.
    The selection must contain: `candidate_methods`, `selected_method`, `reason`, `confidence`, `required_evidence`, and `fallback_method`.

### E. Simulation Staging & CFD Workflow
- **Current State**: `ColabSessionPackager` (`backend/compute/colab_session.py`) and `ColabProvider` (`backend/compute/providers/colab_provider.py`).
- **Audit Findings**:
  - *What Works*: Generates a genuine, reproducible OpenFOAM 10 case deck (`case.tar.gz`) with blockMesh coordinates, boundary conditions, turbulence models (`kOmegaSST`), and a 15-step hardened `notebook.ipynb`.
  - *Staged-Only*: Staged packages reside in `data/compute_jobs/` with status `STAGED` or `AUTHORIZATION_REQUIRED`.
  - *Anti-Fabrication Guard*: The platform **never claims CFD is complete** until actual result artifacts have been imported and verified.

### F. Result Verification Layer & Epistemic Integrity
- **Current State**: `POST /api/results/import` in `backend/api/routes_results.py` and `_verify_result_archive` in `backend/agent/orchestrator.py`.
- **Audit Findings**:
  - *What Works*: Path traversal (anti-Zip-Slip) protection, replay attack cache, SHA-256 hash checks, solver log banner inspection.
  - *Critical Flaw Identified*: In `backend/api/routes_results.py` (line 181), if force coefficients were missing, a fallback was inserted: `polars = {"CL": 1.0820, "CD": 0.0125, "CM": -0.0900}`.
    **Doctrine Violation**: Under Phase 28 Step 5 and Step 6: *"If any required information is missing: MARK THE RESULT AS INCOMPLETE. Do not silently assume values."*
  - *Fix Required*: Implement a formal result verification layer returning explicit statuses:
    `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `INVALID`, `INCOMPLETE`.
    Strictly eliminate all silent numerical defaults.

### G. Automatic Error Diagnosis & Bounded Repair
- **Current State**: `CFDDiagnosticsEngine` (`backend/agent/diagnostics.py`) and `CFDRepairEngine` (`backend/agent/repair_engine.py`).
- **Audit Findings**:
  - *What Works*: 11 failure classes diagnosed; non-mutating candidate synthesis with new cryptographic hashes; hard retry limit of 3 (`MAX_RETRIES = 3`).
  - *What is Disconnected*: When a job failed during execution or ingestion, the diagnostics engine was not automatically invoked to synthesize a repair candidate and advance the job state machine through `REPAIR_PROPOSED` and `RETRY_STAGED`. This loop must be fully wired into the execution lifecycle.

### H. Scientific Discrepancy Engine
- **Current State**: `ScientificReportGenerator` in `backend/agent/report_generator.py` and `ScientificAnswerEngine` in `backend/agent/scientific_answer.py`.
- **Audit Findings**:
  - *What Works*: Computes discrepancies ($\Delta_{\text{CFD-Surr}}$, $\Delta_{\text{CFD-Analytical}}$) and tags statements with `EpistemicLabel` (`FACT`, `MEASURED`, `COMPUTED`, `PREDICTED`, `INFERRED`, `UNKNOWN`).
  - *What is Missing*: Step 9 requires a dedicated **Scientific Discrepancy Engine** comparing all available sources (`DATABASE_REAL` vs `LIVE_CFD` vs `SURROGATE` vs `ANALYTICAL`) and proposing physical hypotheses with evidence (e.g. boundary layer thickening, viscous decambering, transition, mesh resolution, model-form error).

### I. Investigation Graph
- **Current State**: `InvestigationGraph` in `backend/agent/investigation_graph.py`.
- **Audit Findings**:
  - *What is Mocked/Static*: `InvestigationGraph.create_from_question` returned 11 static template nodes (`n1` through `n11`) with predetermined text rather than dynamically building graph nodes from actual executed lifecycle steps.
  - *Fix Required*: Dynamically attach nodes (`QUESTION` $\to$ `ASSUMPTION` $\to$ `METHOD` $\to$ `DATASET` $\to$ `SIMULATION` $\to$ `RESULT` $\to$ `VALIDATION` $\to$ `DISCREPANCY` $\to$ `HYPOTHESIS` $\to$ `REPAIR` $\to$ `CONCLUSION`) with immutable provenance hashes.

### J. Security & Multitenant Isolation
- **Current State**: `backend/auth/` implements `SecurityManager` and `GovernanceEngine`.
- **Audit Findings**:
  - *What Works*: PBKDF2-HMAC-SHA256 password hashing, signed session tokens (`aasi_tok_`), multitenant user quota limits, and job ownership verification (`verify_job_ownership`).
  - *Safety Boundary*: No credentials or secrets are stored in Colab notebooks or result archives. User-supplied archives are inspected in isolated temporary sandboxes without executing untrusted code.

---

## 2. Autonomy Gap Matrix

| Capability | Current Status | Root Cause | Phase 28 Remedy |
| :--- | :--- | :--- | :--- |
| **Canonical Investigation Object** | Fragmented across 3 models | Disconnected representations in `routes_investigation`, `orchestrator`, and `planner` | Create single canonical `Investigation` aggregate model |
| **Explainable Method Selection** | Implicit in fidelity decision | No standalone decision record | Implement `MethodSelectionRecord` with candidates, reason, and fallback |
| **Result Verification Report** | Hardcoded fallback on missing forces | Silent fallback violates Anti-Fabrication Rule | Implement `ResultVerificationReport` (`VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `INVALID`, `INCOMPLETE`) |
| **Error Diagnosis $\to$ Repair Loop** | Modules exist but not connected to queue | Manual retry handling | Wire `EXECUTION_FAILED` $\to$ diagnosis $\to$ candidate $\to$ max 3 retries |
| **Multi-Source Discrepancy Engine** | Partial in report generator | Lacks hypothesis-evidence engine for 10+ aerodynamic causes | Build `ScientificDiscrepancyEngine` with multi-source comparative matrix |
| **Dynamic Investigation Graph** | Hardcoded 11-node template | Static factory function | Dynamic node generation reflecting actual investigation trace |
| **Public Agent Experience** | Mixed legacy panels on main page | Historical phase artifacts visible on home | Unify `frontend/app/page.tsx` around `InvestigationWorkspace` |

---

## 3. Implementation Roadmap for Phase 28
1. **Core Models**: Implement `backend/agent/canonical_investigation.py` unifying the 24 conceptual elements.
2. **Method Selection**: Implement `backend/agent/method_selector.py` supporting `DATABASE_REAL`, `SURROGATE`, `ANALYTICAL`, `LIVE_CFD`, and `USER_PROVIDED`.
3. **Result Verification**: Implement `backend/science/verification.py` with 10-point verification checklist and zero numerical fallback.
4. **Error Recovery**: Connect `CFDDiagnosticsEngine` and `CFDRepairEngine` directly into `PersistentJobQueue` transitions.
5. **Discrepancy Engine**: Implement `backend/agent/discrepancy_engine.py` with physical hypotheses and evidence citations.
6. **Dynamic Graph**: Enhance `InvestigationGraph` to dynamically bind to `Investigation` nodes.
7. **Unified API**: Expose `/api/v1/investigations/` and mount `api_v1_router` in `backend/main.py`.
8. **Frontend Refinement**: Set `InvestigationWorkspace` as the primary interaction center in `frontend/app/page.tsx`.
9. **Integration Testing**: Implement all 18 mandatory lifecycle tests in `tests/test_phase28_autonomy_integration.py`.
10. **Documentation**: Finalize all Phase 28 architectural, integrity, workflow, and completion reports.
