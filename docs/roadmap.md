# AASI Technical Roadmap & Operational Status

## 1. Verified Operational Status (REAL vs. DERIVED vs. STAGED vs. PLANNED)

As of September 2026, AASI has evolved into an independently verifiable scientific computation pipeline. The following matrix honestly summarizes verified operational capabilities versus planned future modules:

| Subsystem | Verified Operational Capabilities (REAL / DERIVED / REFERENCED) | Staged for User/External Execution | Planned Future Enhancements |
|:---|:---|:---|:---|
| **Scientific Evidence Ledger** | • Atomic `EvidenceRecord` Pydantic model with cryptographic SHA-256 digests.<br>• Bi-directional graph traversal: `Conclusion` $\rightarrow$ `Validation` $\rightarrow$ `Computation` $\rightarrow$ `Input` $\rightarrow$ `Source`.<br>• Cumulative Merkle-root fingerprinting (`compute_ledger_fingerprint`).<br>• Fail-closed handling on missing links (`INSUFFICIENT_EVIDENCE`). | Staging of external solver outputs via `POST /api/compute/artifacts/ingest`. | Distributed ledger synchronization for multi-institutional aerospace consortia. |
| **Scientific Conclusion Engine** | • 7-Tier hierarchical conclusion levels (`INSUFFICIENT_EVIDENCE`, `ANALYTICAL_ONLY`, `SURROGATE_SUPPORTED`, `EXPERIMENTALLY_SUPPORTED`, `CFD_SUPPORTED`, `MULTI_SOURCE_VALIDATED`, `RESEARCH_GRADE`).<br>• Inviolable promotion gates: surrogate alone cannot claim experimental or CFD backing.<br>• Strict separation of statistical agreement ($R^2$, RMSE) from physical validity (drag positivity, lift monotonicity, zero-lift angle). | Promotion to `RESEARCH_GRADE` upon ingestion of converged multi-grid CFD study. | Automated peer-review rebuttal generation for PhD dissertation defenses. |
| **Reproducibility Bundle** | • Export of self-contained `aasi_research_run_<id>/` folder and `.zip` archive.<br>• 12 canonical descriptors (`research_question.json`, `sources.json`, `citations.json`, `dataset_manifest.json`, `input_parameters.json`, `computation_manifest.json`, `solver_information.json`, `validation_results.json`, `provenance.json`, `conclusion.json`, `README.md`, `hashes.sha256`).<br>• Raw authentic Selig coordinate file export (`geometry/naca0012.dat`).<br>• REST API endpoints: `GET /api/research/runs/{run_id}/bundle` & `GET /api/research/runs/{run_id}/export`. | External cluster execution of bundled OpenFOAM `Allrun` script. | Automated Zenodo / Dataverse DOI publishing integration. |
| **Aerodynamic Computation** | • **`DERIVED`**: Exact thin-airfoil theory potential flow calculations ($dC_L/d\alpha = 2\pi/\text{rad} \approx 0.10966/^\circ$).<br>• **`SURROGATE`**: Verified forward inference of `AeroSurrogateV1` across 11 angle-of-attack points with epistemic uncertainty intervals.<br>• **`REAL`**: Authentic Selig coordinate parsing and 8-stage lifecycle validation. | • Complete OpenFOAM `simpleFoam` case deck generation (`0/`, `constant/`, `system/`, `Allrun`). Staged as `USER_EXECUTED_REQUIRED`. | Live execution on remote HPC clusters via authenticated Slurm dispatch. |
| **Validation & Benchmarks** | • Multi-source comparison against authoritative NASA TM-4083 wind-tunnel polar and NASA Langley TMR CFD verification benchmarks.<br>• Statistical metrics (MAE, RMSE, $R^2$) evaluated separately from physical validity gates.<br>• ASME V&V 20 multi-grid Richardson extrapolation and Grid Convergence Index ($GCI$) calculator. | Multi-grid CFD result ingestion for experimental vs numerical validation. | Wind tunnel wall interference and blockage correction modules. |
| **Hardware Discipline** | • Native lightweight developer node detection (4-core CPU, 8GB RAM, no GPU required).<br>• Fail-closed hardware routing: analytical and surrogate inference on CPU; heavy 3D CFD routed to `USER_EXECUTED` or `REMOTE`. | Execution of large-scale RANS / LES solvers on cluster resources. | Dynamic cloud spot-instance orchestration. |
| **Frontend Epistemic UI** | • Real-time host hardware telemetry.<br>• Epistemic badges rendered across comparison tables (`DERIVED`, `REFERENCED`, `SURROGATE`, `USER_EXECUTED`).<br>• Conclusion level indicator and 1-click "Download Reproducibility Bundle (.zip)" button.<br>• Interactive Evidence Ledger and provenance graph inspector. | External execution workflow monitoring. | WebGL 3D flow visualization for OpenFOAM surface pressure fields. |

---

## 2. Quantitative Verification Baseline

- **Pytest Automated Tests:** **342 passed, 0 failing** (100% pass rate across entire test suite, including 10 new adversarial scientific integrity tests).
- **Next.js Production Build:** **Compiled successfully** with zero TypeScript or lint errors.
- **Branch:** Clean working tree on branch `main` synchronized with `origin/main`.

---

## 3. Guiding Scientific Commitment

> AASI will never return a simulated number as experimental data, never extrapolate a surrogate beyond its validated hypercube, never hide solver divergence, and never claim connectivity to proprietary internal databases.
