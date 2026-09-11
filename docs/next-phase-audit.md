# AASI Next-Phase Technical Reality Audit

**Date:** September 11, 2026  
**Auditor:** Autonomous Aerospace Scientific Intelligence (AASI) Core Architecture Team  
**Audit Basis:** Verified codebase at commit `ab2c892` (275 passing tests, Next.js build passing)  
**Strict Classification Standard:** Every major capability is classified as exactly one of:
* `REAL` — Functionally working, mathematically/computationally executed, independently verifiable.
* `PARTIALLY_REAL` — Substantive real logic exists, but key boundary contracts, integrations, or validation depth are incomplete.
* `STATIC_SEED` — Deterministic, offline curated data; not connected to live external APIs or streaming feeds.
* `METADATA_ONLY` — Structural definitions, schemas, or descriptors exist; no underlying raw data or execution.
* `SCAFFOLD` — Code structure, classes, and method signatures exist, but internal logic is stubbed, templated, or non-functional.
* `MOCK` — Synthetic/hardcoded responses returned to simulate functionality.
* `UNAVAILABLE` — Declared in vision/catalog but not implemented or executable on this host.
* `USER_EXECUTED` — Intentionally engineered to generate standalone, self-contained packages for external execution by the user/cluster.
* `REMOTE_REQUIRED` — Requires external HPC, cloud infrastructure, or multi-GPU environments not available on local workstation.

---

## 1. Executive Matrix of Core Capabilities

| Subsystem / Capability | Classification | Current Code Path | Verifiable Reality & Limitations |
| :--- | :--- | :--- | :--- |
| **FastAPI Core Architecture** | `REAL` | `backend/main.py` | Fully operational REST server with strict typing, CORS, route validation, and error contracts. |
| **Deterministic Orbital Solvers** | `REAL` | `backend/tools/orbit.py` | Operational Astropy-backed Keplerian/vis-viva solvers, Hohmann transfers, and escape velocity. |
| **Deterministic Rocket Solvers** | `REAL` | `backend/tools/rocket.py` | Operational Tsiolkovsky rocket equation and multi-stage mass-ratio calculations. |
| **Dimensional & Unit Conversions** | `REAL` | `backend/tools/units.py`, `backend/physics/dimensional.py` | Operational Pint-backed dimensional analysis, SI conversions, and isentropic flow state math. |
| **Agent Calculation Intent** | `PARTIALLY_REAL` | `backend/agent.py` | Deterministic regex-based intent parsing maps queries to tools; not true LLM tool-calling. |
| **LLM Inference Interface** | `PARTIALLY_REAL` | `backend/agent.py` | Connects via HTTP to local Ollama runtime; fails cleanly when Ollama is unreachable. |
| **Scientific RAG / Hybrid Retrieval** | `PARTIALLY_REAL` | `backend/knowledge/retriever.py` | Real hybrid FAISS + BM25 ranking; limited to local seed corpus, not broad literature. |
| **Embedding Engine** | `SCAFFOLD` | `backend/knowledge/embeddings.py` | 384-dim bag-of-words hash with aerospace keyword boost; NOT a true semantic neural embedding model. |
| **Scientific Knowledge Graph** | `STATIC_SEED` | `backend/graph/service.py` | In-memory directed graph of 13 entities and 8 relations; not a dynamic graph database. |
| **Scientific Resolution Cascade** | `PARTIALLY_REAL` | `backend/science/engine.py` | 8-level deterministic cascade with target validation; skips directly when intermediate levels lack data. |
| **NASA Source Adapter** | `STATIC_SEED` | `backend/sources/nasa.py` | Curated index of 4 authentic reports; SHA-256 is of metadata strings, not downloaded PDF bytes. |
| **ISRO Source Adapter** | `METADATA_ONLY` | `backend/sources/isro.py` | Curated metadata index of public missions (Chandrayaan-3); no live API connector. |
| **ESA Source Adapter** | `METADATA_ONLY` | `backend/sources/esa.py` | Curated metadata index of ESA missions (JUICE, Gaia); no direct TAP/OData download. |
| **SpaceX Source Guardrail** | `REAL` | `backend/sources/spacex.py` | Rule-based classifier refusing non-public proprietary queries; permits only public domain information. |
| **Current Information Service** | `STATIC_SEED` | `backend/sources/current_info.py` | Historical 2023–2024 milestones; dynamic `age_days` and explicit `STALE_STATIC_SEED` labels; `is_live=False`. |
| **Authentic Airfoil Dataset** | `REAL` | `data/datasets/authentic_airfoils/` | 1,008 raw polar records across 7 airfoils (`naca0012`, `naca2412`, etc.) with geometric coordinate sets. |
| **Dataset Factory Catalog** | `METADATA_ONLY` | `backend/datasets/catalog.py` | 8 verified manifests (UIUC, NREL S809, CRM, etc.); metadata and license records exist, raw data files not downloaded. |
| **Dataset Versioning & Audit** | `REAL` | `backend/datasets/versioning.py`, `backend/datasets/audit.py` | Cryptographic SHA-256 provenance manifests, immutability checks, and strict geometry-isolated splits. |
| **AeroSurrogateV1 Architecture** | `REAL` | `backend/physics_ai/models.py` | Trainable NumPy dual-stream MLP (13,763 params) with analytical backpropagation and AdamW optimizer. |
| **AeroSurrogateV1 Weights & Inference** | `REAL` | `data/checkpoints/aero_surrogate_v1.npz`, `backend/physics_ai/inference.py` | Verified 79 KB checkpoint loaded with SHA-256 checksum; fails closed with HTTP 503 if missing. |
| **Epistemic Uncertainty Engine** | `PARTIALLY_REAL` | `backend/physics_ai/uncertainty.py` | Mahalanobis distance + training manifold k-NN density; heuristic interval, not fully calibrated conformal band. |
| **Physics Invariant Verification** | `REAL` | `backend/physics_ai/validation.py`, `backend/physics/constraints.py` | Monotonicity ($dC_L/d\alpha > 0$), symmetry ($C_L(0) \approx 0$), and drag positivity ($C_D > 0$). |
| **Multi-Fidelity Resolver** | `PARTIALLY_REAL` | `backend/multifidelity/resolver.py` | 5-tier priority query cascade; backed by authentic experiment cache and trained surrogate. |
| **Surface Cp Field Surrogate** | `REAL` | `backend/physics_ai/field/surrogate.py` | 45-point chordwise pressure distribution estimation and numerical trapezoidal integration for drag. |
| **Active Learning 2.0 Engine** | `PARTIALLY_REAL` | `backend/physics_ai/active_learning.py` | 4 acquisition strategies (`COST_AWARE`, `UNCERTAINTY`, etc.) and 2D coverage canvas; heuristic cost estimates. |
| **OpenFOAM User-Case Generator** | `USER_EXECUTED` | `backend/compute/user_provided.py` | Generates complete, self-contained `aasi_case/` decks (`blockMeshDict`, `controlDict`, scripts, manifest) for external user execution. |
| **OpenFOAM Sandboxed Solver** | `SCAFFOLD` | `backend/simulation/adapters/openfoam.py` | Template generator; local execution requires external OpenFOAM binary (typically unavailable on native Windows). |
| **SU2 Solver Adapter** | `MOCK` | `backend/simulation/adapters/su2.py` | Generates `case.cfg`; non-dry-run returns `SOLVER_UNAVAILABLE`. |
| **XFOIL Solver Adapter** | `MOCK` | `backend/simulation/adapters/xfoil.py` | Generates `xfoil.in`; non-dry-run returns `SOLVER_UNAVAILABLE`. |
| **Local Compute Backend** | `PARTIALLY_REAL` | `backend/compute/local.py` | Correctly invokes `SimulationRunner.run_case()`; gracefully returns failure diagnostics when local binaries are missing. |
| **Remote Slurm Backend** | `SCAFFOLD` | `backend/compute/remote.py` | Generates bash Slurm submit scripts and SSH commands; no active network dispatch or job monitoring. |
| **CFD Quality Control Engine** | `REAL` | `backend/simulation/quality_control.py` | Automated ASME V&V 20 log auditor: residual convergence ($< 10^{-4}$), force stability ($< 1\%$), drag positivity. |
| **ASME V&V 20 GCI Calculator** | `REAL` | `backend/validation/grid_convergence.py` | 3-mesh Richardson extrapolation, observed order of accuracy $p$, and fine/medium GCI indices. |
| **Model Retraining Pipeline** | `PARTIALLY_REAL` | `backend/research/retraining.py` | Trains candidate weights on versioned datasets; operates in-process on CPU. |
| **4-Gate Model Promotion** | `REAL` | `backend/research/promotion.py` | Strict gatekeeper: Loss Convergence $\to$ Benchmark Non-Regression $\to$ Physics Invariants $\to$ GCI Audit. |
| **Scientific Report Generator** | `REAL` | `backend/research/report_generator.py` | Compiles peer-review Markdown and LaTeX reports with benchmark comparisons and error distributions. |
| **Next.js 14 Frontend** | `REAL` | `frontend/app/page.tsx` | Production Next.js UI with live Research Loop dashboard, multi-fidelity explorer, GCI calculator, and audit drawer. |

---

## 2. Deep-Dive Sectional Audits

### 2.1 Deterministic Tooling & Mathematical Solvers
* **Status:** `REAL`
* **Assessment:** The mathematical solvers in `backend/tools/` (orbit, rocket, math_utils, units) represent solid, reproducible engineering implementations. Units are normalized via Pint; orbital equations rely on Astropy planetary ephemerides and standard celestial gravitational parameters ($\mu$); rocket equations compute stage mass fractions accurately.
* **Limitations:** Formula scope is domain-specific (Keplerian orbits, 1D ideal rocket equation, standard atmosphere 1976). Advanced perturbations ($J_2$, atmospheric drag on orbits, non-ideal nozzle expansion) are not modeled.

### 2.2 LLM Orchestration & Reasoning
* **Status:** `PARTIALLY_REAL`
* **Assessment:** `backend/agent.py` establishes clean communication with Ollama. However, tool selection is performed by a deterministic regex parser (`detect_calculation_intent`), not by dynamic LLM function calling.
* **Truth Requirement:** The agent must never claim autonomous reasoning or general AI planning when executing regex pattern matching.

### 2.3 Scientific Retrieval & Knowledge Graph
* **Status:** `PARTIALLY_REAL` (Retrieval) / `STATIC_SEED` (Graph)
* **Assessment:** Hybrid search (FAISS dense + BM25 lexical) is structurally sound, but relies on `FastDeterministicEmbeddingProvider`, which is a 384-dimensional MD5 token-hash bag-of-words rather than a semantic transformer. The knowledge graph is an in-memory dictionary of 13 entities.
* **Truth Requirement:** The system must not claim deep semantic understanding of literature until a genuine, lightweight open-weight embedding model is incorporated.

### 2.4 External Source Federation & Current Information
* **Status:** `STATIC_SEED` & `METADATA_ONLY`
* **Assessment:** Phase 0 correctly corrected the declared `access_method` to `STATIC_SEED` and `METADATA_ONLY`. NASA, ISRO, and ESA search offline dictionaries. `current_info` tracks 5 historical events with dynamic age and `STALE_STATIC_SEED` labels.
* **Truth Requirement:** AASI must continue to forbid claiming real-time satellite telemetry or live NASA NTRS API connections until genuine, authenticated connectors are active.

### 2.5 Physics-AI Surrogate & Model Governance
* **Status:** `REAL`
* **Assessment:** `AeroSurrogateV1` is a genuine vectorized NumPy MLP with analytical gradients. Weights are verified against an on-disk checkpoint with SHA-256 hashing. Missing checkpoints fail closed (`ModelUnavailableError` / HTTP 503).
* **Limitations:** The model is an MLP over 64 flattened coordinate pairs, not a Fourier Neural Operator (FNO) or Mesh-GNN in the continuum function-space sense.
* **Truth Requirement:** Label internally as a geometry-conditioned aerodynamic surrogate, avoiding exaggerated "neural operator" claims.

### 2.6 Simulation Fabric & User Execution
* **Status:** `USER_EXECUTED` (User Case Generator) / `MOCK` (SU2/XFOIL)
* **Assessment:** The `USER_EXECUTED` path (`aasi_case/`) is the correct architecture for constrained developer workstations. The generated decks include directory layouts, initial fields, and scripts. However, SU2 and XFOIL adapters are mock generators that refuse non-dry-run execution.
* **Truth Requirement:** Focus exclusively on making OpenFOAM user execution 100% complete, reproducible, and verifiable. Keep SU2/XFOIL documented as non-operational scaffolds.

---

## 3. Reality Gaps & Critical Mandates for the Next Phase

1. **Provenance Integrity:**
   * Distinguish metadata descriptor hashes from true raw downloaded file hashes.
   * Introduce a unified `SourceDocument` and `DocumentFragment` data model with byte-level cryptographic tracking.
2. **Real Source Connectors:**
   * Transition from static dictionaries to at least one real, rate-limited public connector (e.g. arXiv API or NASA Open Data).
3. **Formal Model Lifecycle:**
   * Implement explicit lifecycle states (`REGISTERED`, `DATASET_READY`, `TRAINED`, `VALIDATED`, `PRODUCTION`).
4. **Hardware-Aware Task Routing:**
   * Build a runtime capability detector (CPU, RAM, GPU, VRAM, WSL, OpenFOAM) that routes tasks to `LOCAL_SAFE`, `USER_EXECUTED`, or `UNAVAILABLE`.
5. **OpenFOAM-First Reproducibility:**
   * Pin case generation to one documented OpenFOAM version and one canonical benchmark (NACA 0012 subsonic RANS).
