# AASI Phase 6: Real Physics AI & Aerodynamic Surrogate

## Executive Overview

Phase 6 marks the transition of **AASI (Autonomous Aerospace Scientific Intelligence)** from structural dataset preparation to genuine, measurable, and scientifically validated **Physics Intelligence**.

For the first time, AASI establishes an unyielding epistemological separation across three distinct pillars:
1. **Language Intelligence (LLMs / Agents)**: Orchestrating, parsing scientific queries, qualitative synthesis, literature retrieval.
2. **Physics Intelligence (Neural Surrogates / AeroSurrogateV1)**: Fast, deterministic numerical inference with bounded epistemic uncertainty and strict out-of-distribution (OOD) routing.
3. **Numerical Truth (Solvers & Authentic Datasets)**: High-order CFD (RANS/LES), wind tunnel measurements, and cryptographic benchmark manifests.

AASI explicitly rejects "demo physics", fabricated numbers, and ungrounded LLM hallucination of aerodynamic polars.

---

## Core Deliverables Summary

| Pillar | Implementation | Key Verification Metric |
| :--- | :--- | :--- |
| **Dataset Authenticity Audit** | `backend/datasets/audit.py` | 100% honest audit; `DATASET-AUTHENTIC-AIRFOILS-V1` VERIFIED (1,008 samples on disk); uninstalled sets marked `METADATA_ONLY`. |
| **Geometry Representation** | `backend/physics_ai/geometry.py` | 64-point equidistant arc-length spline resampling; unit chord normalization $(x/c, y/c)$; analytical NACA 4-digit generation. |
| **Leakage-Free Splitting** | `backend/physics_ai/splits.py` | 0% geometry leakage ($\text{Geom}_{train} \cap \text{Geom}_{test} = \emptyset$); separate geometry-OOD and condition-OOD partitions. |
| **AeroSurrogateV1 Model** | `backend/physics_ai/models.py` | Dual-stream geometry (128→64→32) + condition (3→32→16) residual GELU neural operator (13,763 parameters). Pure CPU execution via vectorized NumPy AdamW. |
| **Baseline Benchmark** | `backend/physics_ai/baselines.py` | Decisively beats Ridge regression ($C_D$ $R^2 = 0.9250$ vs Ridge $R^2 = -30.71$). |
| **Physics Sanity Validation** | `backend/physics_ai/validation.py` | 100% positive drag ($C_D > 0$), 100% lift slope monotonicity in pre-stall linear regime, $|C_L(0)| \le 0.025$ for symmetric airfoils. |
| **Epistemic Uncertainty Engine** | `backend/physics_ai/uncertainty.py` | Mahalanobis feature distance + nearest-neighbor density score; automatic routing to `IN_DOMAIN`, `NEAR_BOUNDARY`, or `SURROGATE_OUT_OF_DOMAIN`. |
| **Grid Convergence (ASME V&V 20)** | `backend/validation/grid_convergence.py` | Roache Richardson extrapolation, observed order $p$, $GCI_{fine} = 2.52\%$, and asymptotic range verification. |
| **Scientific Hierarchy Level 4** | `backend/science/engine.py` | Level 4 routes directly to `AeroSurrogateV1` when in-domain; out-of-envelope queries gracefully escalate without hallucinations. |
| **Physics AI Lab Dashboard** | `frontend/app/page.tsx` | Real-time parameter sliders ($M, Re, \alpha$), live coefficient readouts, interactive SVG polar curves ($C_L(\alpha), C_D(\alpha)$), live audit table, and GCI calculator. |
| **Zero Regression Testing** | `tests/` | **238/238 tests passing** (211 legacy Phase 1–5 tests + 27 Phase 6 tests). |

---

## Directory Organization

```
AASI/
├── backend/
│   ├── datasets/
│   │   ├── audit.py             # Dataset Authenticity Audit Service
│   │   ├── audit_models.py      # Pydantic schemas for audit
│   │   └── catalog.py           # Catalog registering authentic airfoils v1
│   ├── physics_ai/
│   │   ├── schemas.py           # Data contracts & prediction schemas
│   │   ├── geometry.py          # Coordinate resampling, chord normalization & features
│   │   ├── normalization.py     # Flow condition & target scalers
│   │   ├── features.py          # Unified feature extractor
│   │   ├── targets.py           # Target loss processor
│   │   ├── dataset.py           # In-memory dataset with per-sample provenance
│   │   ├── splits.py            # Zero-leakage geometry splitter
│   │   ├── baselines.py         # Ridge, Random Forest & MLP baselines
│   │   ├── models.py            # AeroSurrogateV1 vectorized neural operator
│   │   ├── training.py          # Pure CPU AdamW training runner
│   │   ├── metrics.py           # MAE, RMSE, R2, physics violation metrics
│   │   ├── validation.py        # Fluid dynamics rule validator
│   │   ├── uncertainty.py       # Epistemic distance & density quantification
│   │   ├── provenance.py        # Environment & git commit capture
│   │   ├── checkpoints.py       # Checkpoint manager with SHA-256 digests
│   │   ├── inference.py         # AerodynamicInferenceEngine
│   │   └── service.py           # PhysicsAIService singleton
│   ├── validation/
│   │   └── grid_convergence.py  # ASME V&V 20 Richardson Extrapolation & GCI
│   ├── physics/
│   │   └── model_registry.py    # Registered models with operational envelopes
│   └── science/
│       ├── engine.py            # Level 4 surrogate resolution integration
│       └── surrogates.py        # Operational envelope validation
├── data/
│   ├── datasets/authentic_airfoils/ # 7 real geometries, 1,008 authentic samples
│   ├── checkpoints/                 # Production aero_surrogate_v1.npz & manifest
│   └── training_runs/               # TR-AERO-SURROGATE-V1-001 run artifacts
├── docs/phase6/                     # Complete 13-part Phase 6 documentation
├── frontend/app/                    # Physics AI Lab UI with SVG polar plot
└── tests/                           # Complete test suite (238 passing)
```
