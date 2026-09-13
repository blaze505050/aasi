# AASI Phase 19: Complete Reality Audit & Capability Classification

## 1. Executive Summary
In strict compliance with the **Absolute Anti-Fabrication Rule** of the Phase 19 Master Engineering Directive, every subsystem, engine, adapter, and endpoint in the AASI repository has been audited against physical hardware and active disk state.

No capability is classified as `REAL_EXECUTED` merely because source code exists. If a solver or dataset cannot be run locally without external compute or user execution, it is explicitly classified as `USER_EXECUTED_REQUIRED` or `RESOURCE_LIMITED`.

---

## 2. Definitive Capability Classification Taxonomy
- `REAL_EXECUTED`: Fully executed on local hardware during the current benchmark campaign with verified outputs, hashes, and execution logs.
- `REAL_IMPORTED`: Authoritative data files or verified experimental records present on local disk with verified checksums.
- `REAL_COMPUTED`: Computed locally via direct mathematical / numerical algorithms (e.g. analytical solvers, matrix inverses, numerical integrals).
- `DERIVED`: Computed from first principles or post-processed from primary simulation/experimental data.
- `REFERENCED`: Verified literature values or benchmark experimental tables with DOI citations (never equated with numerical CFD).
- `SURROGATE`: Machine-learning approximation with declared hypercube bounds and epistemic uncertainty labels.
- `SCAFFOLD`: Fully typed, validated interface awaiting external hardware deployment or execution.
- `USER_EXECUTED_REQUIRED`: Requires external solver execution on the user's host/cluster (e.g. OpenFOAM `simpleFoam`).
- `RESOURCE_LIMITED`: Requires hardware resources (e.g. > 15 GB disk or discrete CUDA GPU) beyond the current machine budget.

---

## 3. Subsystem-by-Subsystem Audit Matrix

| Subsystem / Feature | Location | Classification | Audit Evidence & Hardware Reality |
| :--- | :--- | :--- | :--- |
| **NASA LTPT Experimental Polar** | `backend/datasets/adapters/naca0012.py` | `REFERENCED` | NASA TM-4083 wind tunnel measurements ($Re = 2\times 10^6 - 6\times 10^6$). Curated literature, not numerical CFD. |
| **AirfRANS Ingestion Adapter** | `backend/datasets/adapters/airfrans.py` | `REAL_IMPORTED` | Authoritative metadata & canonical 14-case simulation records with SHA-256 digests. |
| **Full 24.5 GB AirfRANS Dataset** | `backend/datasets/adapters/airfrans.py` | `RESOURCE_LIMITED` | Full 1,000-mesh download (~42.8 GB uncompressed) exceeds local 23.55 GB disk; safely halted by 15 GB reserve rule. |
| **AirfRANS Phase 19 Manifest** | `data/manifests/airfrans_phase19_manifest.json` | `REAL_IMPORTED` | Cryptographically signed 14-case representative benchmark subset. |
| **NASA TMR 2D Adapter** | `backend/datasets/adapters/tmr2d.py` | `REAL_IMPORTED` | NASA Langley TMR verification benchmarks (NACA 0012, Flat Plate, 2D bump, L1-L5 grids). |
| **11-Stage Dataset Lifecycle Manager**| `backend/datasets/acquisition.py` | `REAL_EXECUTED` | 11-stage acquisition state machine executed and verified with fail-closed gate checks. |
| **OpenFOAM simpleFoam Execution** | `backend/simulation/adapters/` | `USER_EXECUTED_REQUIRED` | Native Windows PATH has no `simpleFoam.exe`; WSL detached. Case decks generated for local user run. Zero fabricated CFD numbers. |
| **OpenFOAM Case Deck Generator** | `backend/simulation/` | `REAL_COMPUTED` | Deterministic generation of complete `0/`, `constant/`, `system/`, and `Allrun` files. |
| **Physics-AI Training Engine** | `backend/physics_ai/training.py` | `REAL_EXECUTED` | Deterministic CPU Ridge/Surrogate training executed on real acquired records. Weights hashed to SHA-256. |
| **Deep Neural Operator (FNO-2D / GNN)**| `backend/physics/model_registry.py` | `SCAFFOLD` | PyTorch DLL missing MSVC redistributable; architecture typed as scaffold. |
| **Geometry Leakage Prevention** | `backend/physics_ai/splits.py` | `REAL_EXECUTED` | `verify_split_leakage()` strictly enforces $\mathcal{G}_{train} \cap \mathcal{G}_{test} = \emptyset$. |
| **Normalizer Isolation** | `backend/physics_ai/training.py` | `REAL_EXECUTED` | `fit_transform()` strictly isolated to training split geometries; test transformed with frozen statistics. |
| **Physics Promotion Gate Auditor** | `backend/physics_ai/validation.py` | `REAL_EXECUTED` | Blocks promotion if $C_D \le 0$, $\partial C_L/\partial \alpha \le 0$, or $C_p > 1.0$. |
| **Cross-Dataset Generalization Engine**| `backend/physics/generalization.py` | `REAL_EXECUTED` | `ScientificCompatibilityContract` rejects unphysical comparisons with `COMPARISON_NOT_VALID`. |
| **5-Tier OOD Evaluator** | `backend/physics_ai/splits.py` | `REAL_EXECUTED` | Evaluates In-Distribution, Geometry-OOD, Reynolds-OOD, AoA-OOD, Joint-OOD; returns `INSUFFICIENT_EVIDENCE` when data lacking. |
| **Uncertainty Calibration Engine** | `backend/physics_ai/uncertainty.py` | `REAL_EXECUTED` | Flags uncalibrated models as `UNCERTAINTY_NOT_CALIBRATED`; reports empirical coverage on held-out splits. |
| **Evidence Ledger DAG** | `backend/research/evidence_ledger.py`| `REAL_EXECUTED` | Directed Acyclic Graph tracking inputs $\rightarrow$ computation $\rightarrow$ validation $\rightarrow$ conclusion. |
| **Independent Reproduction Verifier** | `backend/research/verifier.py` | `REAL_EXECUTED` | Automated verifier checking file hashes, environment matches, and metric consistency. |
| **Hardware Governance Pre-Flight** | `backend/physics_ai/governance.py` | `REAL_EXECUTED` | Pre-flight check enforcing 15.0 GB minimum free disk space reserve and RAM safety. |

---

## 4. Integrity Prohibitions Enforced
1. Under no circumstances will unexecuted CFD simulations display fabricated forces, drag polars, or surface pressure distributions.
2. Under no circumstances will uncalibrated surrogates display narrow 95% confidence intervals without the `UNCERTAINTY_NOT_CALIBRATED` warning tag.
3. Under no circumstances will an unverified model be promoted to `VERIFIED` without passing all physical constraint tests.
4. Under no circumstances will numerical RANS simulations be labeled as experimental measurements.
