# AASI Multi-Dataset Physics Model Training Specification

## Executive Summary & Epistemic Boundaries
The AASI Multi-Dataset Physics-AI Training Engine provides deterministic, verifiable, and physics-constrained training of aerodynamic surrogate models across heterogeneous CFD and experimental datasets.

In accordance with the AASI Scientific Integrity Directive, this document classifies all data sources and modeling layers:
- **Numerical CFD (AirfRANS, NASA TMR 2D)**: `REAL IMPLEMENTED` & `DERIVED` numerical data. Synthesized from Reynolds-Averaged Navier-Stokes solvers (OpenFOAM simpleFoam, CFL3D, FUN3D).
- **Experimental Ground Truth (NASA LTPT, UIUC Wind Tunnel)**: `REFERENCED` experimental data. Never equated with numerical CFD.
- **Neural Surrogates (AeroRidge, AeroGraphNet, FNO)**: `SURROGATE` machine-learning approximations bounded by strict domain envelopes.

---

## Capability Status Classification Matrix
| Component | Classification | Description | Implementation Status |
| :--- | :--- | :--- | :--- |
| **AirfRANS Ingestion Adapter** | `REAL IMPLEMENTED` | Parses AirfRANS dataset, surface pressures, wall shear stress, boundary layer profiles. | Active (`AirfRANSAdapter`) |
| **NASA TMR 2D Verification Adapter** | `REAL IMPLEMENTED` | Ingests NASA Langley TMR verification benchmarks (NACA 0012, Flat Plate, 2D bump). | Active (`NASATMR2DDatasetAdapter`) |
| **11-Stage Dataset Lifecycle Manager** | `REAL IMPLEMENTED` | Fail-closed acquisition from discovery to training readiness. | Active (`DatasetAcquisitionManager`) |
| **Flow Condition Normalizer** | `REAL IMPLEMENTED` | StandardScaler isolated strictly to training set geometries. | Active (`FlowConditionNormalizer`) |
| **Physics-Informed Loss Functions** | `REAL IMPLEMENTED` | Penalty terms for negative drag, stagnation violations, non-monotonic lift. | Active (`backend/physics_ai/training.py`) |
| **Full MeshGraphNet / 3D GNN** | `RESOURCE LIMITED` | Requires multi-GPU HPC cluster (>15 GB VRAM) for 3D volumetric fields. | Architectural Scaffold Ready |
| **Local Client-Side OpenFOAM** | `USER EXECUTED` | Automated case directory generation executed on user's machine. | Active (`backend/simulation/adapters/`) |

---

## Dataset Acquisition Contract (11 Stages)
Every dataset ingested into the AASI ecosystem must progress through an immutable 11-stage verification contract before any training data reaches the optimizer:

```
[DISCOVERED]
     │
     ▼
[LICENSE_VERIFIED] ────► Fail-Closed Check: Permissive Open-Access License (CC-BY, Apache-2.0, Public Domain)
     │
     ▼
[SOURCE_VERIFIED]  ────► Official DOI / Institutional Source Verification (Inria, NASA Langley TMR)
     │
     ▼
[DOWNLOAD_REQUESTED]
     │
     ▼
[DOWNLOADED]
     │
     ▼
[HASH_VERIFIED]    ────► Cryptographic SHA-256 Checksum Validation against Manifest
     │
     ▼
[PARSED]           ────► Format Ingestion (.h5, .vtu, .csv, structured Tecplot)
     │
     ▼
[SCHEMA_VALIDATED] ────► Mandatory Variables ($x, y, z, p, \tau_w, U, V, W, \nu_t, C_p, C_f$)
     │
     ▼
[PHYSICS_VALIDATED]───► Sanity Checks ($C_p \le 1.0$, $C_D > 0$, Reynolds/Mach Bound Verification)
     │
     ▼
[SPLIT_VALIDATED]  ────► Geometry-Level Separation; Zero Sample/Leakage Overlap
     │
     ▼
[READY_FOR_TRAINING]
```

Any stage failure halts execution immediately with a descriptive status code (`LICENSE_RESTRICTED`, `INTEGRITY_COMPROMISED`, `SCHEMA_MISMATCH`, or `DATA_LEAKAGE_DETECTED`).

---

## Training Architecture & Pipeline
```
┌──────────────────────────────────────────────────────────┐
│              Hardware Governance Pre-Flight              │
│       RAM ≥ 1.0 GB  |  Disk Reserve ≥ 15.0 GB Free       │
└────────────────────────────┬─────────────────────────────┘
                             │ (PASSED)
                             ▼
┌──────────────────────────────────────────────────────────┐
│              Geometry-Level Train/Val/Test Split          │
│       80% Train Airfoils | 10% Val | 10% Test Airfoils   │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│             Training-Only Feature Normalizer             │
│        Fit ONLY on Train Geometries (fit_transform)       │
│        Transform Validation & Test (transform ONLY)      │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│             Deterministic Training Execution             │
│        Fixed Seed (torch.manual_seed, np.random.seed)    │
│        Deterministic Backprop / CPU/GPU Optimizer         │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│             Physics-Gate Promotion Audit                 │
│   1. Lift Slope: ∂CL/∂α > 0 (pre-stall)                  │
│   2. Drag Non-Negativity: CD > 0                         │
│   3. Stagnation Bound: Cp ≤ 1.0                          │
│   4. Metric Gate: CL RMSE < 0.05, CD RMSE < 0.01         │
└────────────────────────────┬─────────────────────────────┘
                             │ (ALL GATES PASSED)
                             ▼
┌──────────────────────────────────────────────────────────┐
│        Signed Reproducibility Manifest & Artifact        │
│          Status: VERIFIED / VERIFIED_PRODUCTION           │
│           Cryptographic Model Checksum Generated         │
└──────────────────────────────────────────────────────────┘
```

---

## Storage & Computational Budgeting
Local development environments enforce fail-closed hardware protection:
- If available system disk space falls below **15 GB**, dataset acquisition and model training abort with `RESOURCE_LIMITED`.
- Memory usage is checked prior to tensor allocation to prevent operating system thrashing or kernel panics.
