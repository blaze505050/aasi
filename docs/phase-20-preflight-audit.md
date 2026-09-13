# AASI Phase 20 Preflight Reality Audit

**Document ID:** AASI-AUDIT-PHASE20-PREFLIGHT-001  
**Status:** Preflight Capability & Reality Assessment  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule (Zero synthetic placeholders, zero unearned model promotion, fail-closed governance)

---

## 1. Executive Summary

In preparation for executing **Phase 20 (Physics-AI Generalization, Geometry-Aware Surrogates, Calibrated Uncertainty & Active Scientific Experimentation)**, this audit evaluates the exact state of the AASI codebase as of git commit `6a0b23d`.

The central scientific question of Phase 20 is:
> **"Can AASI learn aerodynamic behavior that transfers to genuinely unseen geometries and flow conditions while correctly identifying when its predictions are unreliable?"**

The baseline established in Phase 19 ($R^2_{\text{train}} = 0.8904$, Geometry-OOD $R^2 = -7.777$, empirical coverage = 50.0% $\to$ `UNCERTAINTY_NOT_CALIBRATED`, min $C_D = 0.0109 > 0$, max $C_p = 0.985 \le 1.0$, determinism: `BIT_IDENTICAL_DETERMINISTIC`) serves as the official reference benchmark.

---

## 2. Capability Classification (9-Tier Taxonomy)

Every subsystem in the repository has been audited and classified according to the 9-tier taxonomy:

| Subsystem / Capability | Current Implementation | Phase 20 Classification | Operational Reality |
| :--- | :--- | :--- | :--- |
| **Hardware Governance Guard** | `backend/physics_ai/governance.py` | `REAL_EXECUTED` | Dynamically halts operations if free disk space falls below 15.0 GB safety threshold. |
| **AirfRANS 14-Case Canonical Benchmark** | `data/manifests/airfrans_phase19_manifest.json` | `REAL_IMPORTED` | 14 authentic OpenFOAM simpleFoam cases across 7 airfoils signed with SHA-256 (`55187185...`). |
| **Authentic Wind-Tunnel Polars** | `data/datasets/authentic_airfoils/` | `REAL_IMPORTED` | 1,008 authentic experimental wind-tunnel measurements ($C_L, C_D, C_m$) from Abbott & von Doenhoff (NACA-TR-824). |
| **Airfoil Coordinate Profiles** | `data/datasets/authentic_airfoils/` | `REAL_IMPORTED` | Authentic upper/lower coordinates for NACA 0012, 0009, 0006, 2412, 4412, Clark Y, RAE 2822. |
| **OpenFOAM simpleFoam Execution** | `backend/simulation/adapters/` | `USER_EXECUTED_REQUIRED` | Native solver binary unavailable in Windows PATH; generates complete case decks and reports `SOLVER_UNAVAILABLE`. |
| **AeroSurrogate Ridge Baseline** | `backend/physics_ai/reproduction_campaign.py` | `REAL_EXECUTED` | Analytical SVD $L_2$ regression, isolated standardization, deterministic seeding. |
| **Two-Run Reproducibility Verifier**| `backend/research/verifier.py` | `REAL_COMPUTED` | Bitwise comparison of Run A vs Run B yields max absolute weight delta `0.0`. |
| **Independent Reproduction Bundle** | `data/reproduction_bundles/PHASE19-RUN-001/` | `REAL_EXECUTED` | 18 descriptors, full SHA-256 tree, verified with `verify_reproduction_bundle()`. |
| **Geometry-OOD Generalization** | `backend/physics_ai/splits.py` | `REAL_COMPUTED` | Geometry-isolated split ($R^2 = -7.777$ on held-out NACA 6409/4415); honest negative score. |
| **Uncertainty Quantification** | `backend/physics_ai/uncertainty.py` | `DERIVED` | Closed-form Bayesian posterior covariance; audited coverage 50.0% $\to$ `UNCERTAINTY_NOT_CALIBRATED`. |
| **Active Learning Candidates** | `backend/physics_ai/active_learning.py` | `REAL_COMPUTED` | Uncertainty and parameter-space coverage sampling; stages CFD decks for execution. |
| **Adversarial Integrity Test Suite**| `tests/test_phase19_real_execution_integrity.py` | `REAL_EXECUTED` | 16 fail-closed adversarial integrity tests (400 passed, 0 failed). |
| **Phase 19 Frontend Cockpit** | `frontend/app/page.tsx` | `REAL_EXECUTED` | Dedicated interactive dashboard with capability badges and two-run runner. |

---

## 3. Existing Architecture & Subsystems

1. **`backend/physics_ai/`**:
   - `geometry.py`: Contains `AirfoilGeometryProcessor` with arc-length resampling and NACA 4-digit coordinate generation.
   - `models.py`: Contains `AeroSurrogateV1`, a vectorized NumPy neural network with separate geometry encoder and condition encoder.
   - `reproduction_campaign.py`: Orchestrates Phase 19 Run A vs Run B two-run reproduction campaign.
   - `governance.py`: Hardware inspection, OS metadata, and 15.0 GB reserve threshold enforcement.
   - `splits.py`: Geometry-separated partitioning and data leakage detection.
   - `validation.py`: Physical law enforcement ($C_D \ge 0$, $\partial C_L / \partial \alpha > 0$, $C_p \le 1.0$).
   - `uncertainty.py`: Mahalanobis distance, nearest-neighbor density, epistemic tagging.
   - `active_learning.py`: Candidate generation, acquisition strategies, and coverage maps.
2. **`backend/research/`**:
   - `evidence_ledger.py`: Cryptographic Directed Acyclic Graph (DAG) linking datasets, runs, checkpoints, and claims.
   - `bundle.py`: Assembles self-contained reproduction bundles.
   - `verifier.py`: Audits bundles for bit-identical reproducibility and tamper detection.
3. **`data/`**:
   - `data/datasets/authentic_airfoils/`: Contains authentic experimental polars (1,008 samples) and coordinate profiles for 7 airfoils.
   - `data/manifests/airfrans_phase19_manifest.json`: 14 authentic OpenFOAM CFD simulation cases.
   - `data/reproduction_bundles/PHASE19-RUN-001/`: Reference Phase 19 reproduction bundle.

---

## 4. Existing Scientific Limitations

1. **Representation Limit of Phase 19 Baseline:**
   The Phase 19 feature vector $[\alpha, Re, t/c, m, p, \alpha^2]$ relies solely on bulk scalar descriptors. It lacks local curvature, camber line distribution, and leading/trailing edge geometry, which causes domain collapse ($R^2 = -7.777$) when evaluated on high-camber or non-standard profiles (e.g. NACA 6409).
2. **Overconfidence of Linear Covariance:**
   Bayesian linear posterior covariance produces a nominal 95% confidence interval that only covers 50% of held-out test points under distribution shift. The model is severely overconfident.
3. **Absence of Conformal Prediction:**
   Existing uncertainty metrics lack finite-sample distribution-free coverage guarantees.
4. **CFD Solver Execution Gate:**
   Native OpenFOAM is offline on Windows 11 host. While case generation is 100% authentic and complete, CFD runs cannot execute natively without user/WSL2 action.

---

## 5. Missing Components Required for Phase 20

To satisfy the Phase 20 Master Engineering Directive, the following new components must be engineered:
1. **Geometry-Aware Representation Engine (`backend/physics_ai/geometry_representation.py`):**
   - Standardization to unit chord, consistent arc-length sampling, and upper/lower surface coordinate extraction.
   - Cryptographic SHA-256 geometry identity hashing.
   - 4 experimental representations: Representation A (descriptors), Representation B (coordinate vector), Representation C (surface profiles), Representation D (hybrid).
   - Quantitative contour distance metrics: Hausdorff, contour Fréchet, Euclidean, and parameter Mahalanobis.
2. **Modular Model Benchmark Suite (`backend/physics_ai/benchmark_models.py`):**
   - Standard interface (`fit`, `predict`, `save`, `load`, `hash`, `evaluate`).
   - Implementations: Ridge, Polynomial Ridge, Random Forest, Gradient Boosting, MLP, Geometry-Aware MLP, Physics-Constrained Surrogate, and Ensemble.
   - 4-level target hierarchy: Level 1 ($C_L, C_D, C_m$), Level 2 ($C_p(x)$), Level 3 ($C_f(x)$), Level 4 (Integrated coefficients).
3. **Quantitative OOD Engine (`backend/physics_ai/ood_engine.py`):**
   - 7-tier evaluation taxonomy: In-Distribution, Geometry-OOD, Reynolds-OOD, AoA-OOD, Joint-OOD, Thickness-OOD, Camber-OOD.
   - Distance-to-training-distribution gating with explicit mathematical criteria.
4. **Uncertainty Calibration Engine & Hard Gate (`backend/physics_ai/calibration.py`):**
   - Methods: Bayesian linear, Bootstrap ensemble, Residual quantiles, Conformal prediction ($1 - \alpha$).
   - Metrics: Empirical coverage, ECE, interval sharpness, Winkler score.
   - Hard gate: Only tags `UNCERTAINTY_CALIBRATED` if empirical coverage is within nominal bounds.
5. **Active Learning Feasibility Engine (`backend/physics_ai/active_experimentation.py`):**
   - Candidate ranking combining uncertainty, OOD distance, and parameter diversity.
   - Automated OpenFOAM case staging with fail-closed acquisition status (`USER_EXECUTED_REQUIRED`).
6. **Persistent Experiment Registry (`backend/research/experiment_registry.py`):**
   - Immutable registry (`AASI-P20-EXP-XXX`) capturing datasets, geometry hashes, splits, configs, metrics, DAG ancestry, and checkpoint digests.
   - Strict 6-stage model promotion pipeline.
7. **Phase 20 Campaign Runner (`backend/physics_ai/phase20_campaign.py`):**
   - Orchestrates the 4 primary Phase 20 experiments:
     - P20-E001: Central Model & Representation Benchmark.
     - P20-E002: Physics Constraint Loss Ablation.
     - P20-E003: Uncertainty Calibration Benchmark.
     - P20-E004: Active Learning Feasibility Study.
8. **Phase 20 REST API Endpoints & Adversarial Testing Suite:**
   - Mount Phase 20 endpoints in `backend/main.py`.
   - Implement $\ge 20$ adversarial fail-closed tests in `tests/test_phase20_scientific_integrity.py`.
9. **Frontend Scientific Laboratory:**
   - Dedicated `🧪 PHASE 20 — SCIENTIFIC GENERALIZATION LAB` view in `frontend/app/page.tsx`.
10. **Scientific Report & Documentation:**
    - `docs/phase-20-scientific-report.md` answering the 15 scientific questions.
    - Architectural, methodology, and module-specific documentation.

---

## 6. Hardware Constraints & Execution Safety

- **Operating System:** Windows 11 Build 26200 AMD64
- **Physical Memory:** 8.16 GB Total (~0.5 - 1.0 GB Available during peak load)
- **Host Disk:** 118.28 GB Total, 94.73 GB Used, **23.55 GB Available**
- **Safety Reserve:** 15.0 GB minimum free disk required at all times.
- **Available Headroom:** $\approx 8.55 \text{ GB}$.
- **Compute Rules:**
  - Zero heavy unbatched GPU allocations.
  - Zero multi-gigabyte raw dataset downloads.
  - Fail-closed execution for offline CFD solvers (`USER_EXECUTED_REQUIRED`).
  - CPU-vectorized NumPy, SciPy, and Scikit-Learn implementations for maximum portability and bitwise determinism.

---

## 7. Recommended Implementation Order

1. **Work Package 1:** Preflight Audit & Architectural Documentation (Complete).
2. **Work Package 2:** Geometry-Aware Representation Engine (`backend/physics_ai/geometry_representation.py`).
3. **Work Package 3:** Modular Model Benchmark Suite (`backend/physics_ai/benchmark_models.py`).
4. **Work Package 4:** Quantitative OOD Engine & Epistemic Uncertainty Calibration (`backend/physics_ai/ood_engine.py`, `backend/physics_ai/calibration.py`).
5. **Work Package 5:** Active Learning Loop & Persistent Experiment Registry (`backend/physics_ai/active_experimentation.py`, `backend/research/experiment_registry.py`).
6. **Work Package 6:** Phase 20 Campaign Runner (Experiments P20-E001 through P20-E004).
7. **Work Package 7:** REST API Endpoints & Adversarial Testing Suite (`tests/test_phase20_scientific_integrity.py`).
8. **Work Package 8:** Frontend Scientific Generalization Lab in `frontend/app/page.tsx`.
9. **Work Package 9:** Scientific Report, Walkthrough, and Final Verification.
