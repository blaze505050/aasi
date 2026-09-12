# AASI Phase Reality Audit: Independent Scientific Reproducibility, Real Solver Execution & Experimental Validation

**Audit Date**: September 12, 2026  
**Auditor**: AASI Autonomous Scientific Integrity Core  
**Standard**: *Master Engineering Directive: Independent Scientific Reproducibility, Real Solver Execution & Experimental Validation*  

---

## 1. Reality Audit Framework & Epistemic Taxonomy

Every subsystem and execution path in AASI is classified according to its true operational state:
- **`REAL_EXECUTED`**: Computation genuinely executed on the host (e.g. thin-airfoil theory, surrogate inference, geometry parsing, bundle packaging).
- **`REAL_IMPORTED`**: Authentic external data files downloaded, verified by SHA-256, and read from disk (e.g. `naca0012.dat`, `airfoil_geometries.json`).
- **`DERIVED`**: Mathematically computed from fundamental physical governing equations (e.g. potential flow $2\pi/\text{rad}$).
- **`REFERENCED`**: Authoritative empirical wind tunnel or CFD benchmarks digitized from published literature (e.g. NASA TM-4083, NASA TMR).
- **`SURROGATE`**: ML/surrogate model evaluation with epistemic uncertainty quantification within verified training envelope.
- **`USER_EXECUTED_REQUIRED`**: Full case generation completed, but local solver is absent or requires HPC cluster resources.
- **`SCAFFOLD`**: Architectural interface or solver wrapper awaiting external environment or execution runner.
- **`MOCK`**: Quarantined test harness stubs strictly isolated from scientific evidence.
- **`UNAVAILABLE`**: Method, model, or data source does not exist locally and cannot be honestly executed.

---

## 2. Complete Repository Reality Audit Matrix

| Subsystem / Path | Source Files | Epistemic Classification | Genuinely Operates | Merely Prepares / Scaffolds | Actions for Next Phase |
|---|---|---|---|---|---|
| **Research Question & Hypothesis** | `backend/research/models.py`<br>`backend/research/service.py` | **`REAL_EXECUTED`** | Question formulation, quantitative hypothesis, flow conditions, SHA-256 binding. | None | Add state machine tracking (`QUESTION_VALIDATED`). |
| **Literature Evidence** | `backend/sources/`<br>`backend/research/service.py` | **`REFERENCED`** | Digitized peer-reviewed NASA citations, DOI/NTRS links, public domain licenses. | Dynamic API live queries (fallback to static index). | Distinguish file hash vs metadata hash vs fragment hash. |
| **Dataset Ingestion** | `backend/datasets/pipeline.py`<br>`data/datasets/authentic_airfoils/` | **`REAL_IMPORTED`** & **`REAL_EXECUTED`** | Reads authentic Selig `.dat` files, executes 8-stage cryptographic lifecycle. | Remote chunked multi-GB wind tunnel scraping. | Add dataset tamper-detection tests. |
| **Analytical Computation** | `backend/research/service.py` | **`DERIVED`** | Exact thin-airfoil potential flow theory ($dC_L/d\alpha = 2\pi/\text{rad} \approx 0.10966/^\circ, \alpha_0 = 0^\circ$). | None | Isolate from numerical CFD metrics. |
| **Surrogate Computation** | `backend/physics_ai/inference.py`<br>`backend/physics_ai/models.py` | **`SURROGATE`** | `AeroSurrogateV1` polynomial/ridge forward evaluation with dual epistemic uncertainty bounds. | Large neural FNO/DeepONet models (honestly marked `MODEL_UNAVAILABLE`). | Enforce out-of-envelope rejection. |
| **OpenFOAM CFD Generation** | `backend/simulation/case_generator.py`<br>`backend/compute/user_provided.py` | **`REAL_EXECUTED`** (Generation)<br>**`USER_EXECUTED_REQUIRED`** (Solver) | Generates full OpenFOAM directory tree (`0/`, `constant/`, `system/`, `Allrun`) with SHA-256 file hashes. | Does not automatically run `simpleFoam` on host without solver check. | Implement real solver execution contract with timeout, divergence detection, and residual parsing. |
| **CFD Convergence Analysis** | `backend/compute/artifacts.py` | **`REAL_EXECUTED`** (when ingested)<br>**`SCAFFOLD`** (real-time monitoring) | Parses `forceCoeffs.dat` and residuals when output is ingested via API. | Real-time process monitoring of live `simpleFoam` stdout. | Implement formal convergence detector: residual drop $\ge 10^{-4}$, force coefficient leveling, mass balance. |
| **Grid Convergence (ASME V&V 20)** | `backend/compute/artifacts.py` | **`REAL_EXECUTED`** (on 3 grids)<br>**`SCAFFOLD`** (flagship run) | Computes observed order $p$, Richardson extrapolation, and $GCI$ if fine/med/coarse grids supplied. | Flagship NACA 0012 run does not yet execute all 3 grids automatically. | Build canonical 3-grid NACA 0012 study; return `GCI_STATUS = INSUFFICIENT_DATA` if incomplete. |
| **Validation Comparison** | `backend/physics/benchmark.py` | **`REAL_EXECUTED`** | Compares surrogate against NASA TM-4083 wind tunnel polar & NASA TMR CFD. | Does not yet compute full 5-tier uncertainty budget. | Add structured `UncertaintyAssessment` (input, model, numerical, measurement). |
| **Evidence Ledger** | `backend/research/evidence_ledger.py` | **`REAL_EXECUTED`** | Stores `EvidenceRecord` DAG, backward graph traversal, Merkle root. | Orphan detection and cyclic graph audits. | Add `ledger.verify_integrity()` diagnostics. |
| **Conclusion Engine** | `backend/research/conclusion_engine.py` | **`REAL_EXECUTED`** | 7-tier conclusion levels with fail-closed promotion rules. | Machine-checked verification of reproduction bundles. | Implement `ReproducibilityVerifier` with `POST /api/research/reproduce/verify`. |
| **Reproducibility Bundle** | `backend/research/bundle.py` | **`REAL_EXECUTED`** | Exports 12 canonical JSON files, `hashes.sha256`, raw geometry, and OpenFOAM deck into `.zip`. | Machine-readable `reproduce.json` and `REPRODUCE.md` instructions. | Add `reproduce.json`, `REPRODUCE.md`, and automated bundle verifier. |

---

## 3. Honest Language & Downgrade Directives

In accordance with Section 2 of the engineering directive, the following terminology corrections are strictly enforced:
1. **"Autonomous"**: Refers strictly to autonomous workflow planning and data routing. When external computation is required, state must be `USER_EXECUTED_REQUIRED`.
2. **"Validated"**: Strictly differentiated between **`STATISTICALLY_CORRELATED`** ($R^2$, RMSE) and **`PHYSICALLY_VALIDATED`** (governing invariant satisfaction, drag positivity, grid convergence).
3. **"CFD Support"**: A generated case deck is `CASE_GENERATED`, never `CFD_VALIDATED`. Only converged solver outputs with residual history justify `CFD_SUPPORTED`.
4. **"Research-Grade"**: Reserved exclusively for Level 6 synthesis requiring multi-grid ASME V&V 20 CFD + wind-tunnel validation + surrogate agreement. Flagship run without local CFD execution remains at Level 5 (`MULTI_SOURCE_VALIDATED`).
