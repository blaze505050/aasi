# AASI Real Scientific Execution, Evidence Integrity & Independent Reproducibility Manual

**Governing Standard**: *AASI Master Engineering Directive — Next Phase*  
**Scope**: Epistemic boundaries, execution taxonomy, Evidence Ledger architecture, and independent replication protocol.

---

## 1. Scientific Execution Taxonomy

AASI strictly differentiates the epistemic status of every calculated value, ingested dataset, simulation result, and scientific claim. Under no circumstance will a surrogate prediction, synthetic approximation, or citation be promoted into experimental or numerical ground truth.

| Epistemic Status | Operational Definition | Local Hardware Execution | Example in Flagship Run |
|---|---|---|---|
| **`REAL`** | Genuinely downloaded, disk-read, parsed, and cryptographically verified data or calculations. | CPU (Standard Node) | Ingestion of authentic Selig airfoil coordinates (`data/datasets/authentic_airfoils/naca0012.dat`), 8-stage lifecycle validation, cryptographic SHA-256 fingerprinting. |
| **`DERIVED`** | Numerically computed directly from first-principles governing physics equations without empirical fitting. | CPU (Standard Node) | Exact Thin-Airfoil potential theory: $dC_L/d\alpha = 2\pi/\text{rad} \approx 0.10966/^\circ$, $\alpha_0 = 0.0^\circ$. |
| **`REFERENCED`** | Authoritative empirical or benchmark numerical data digitized directly from verified peer-reviewed publications or NASA technical reports. | Read from disk / HTTP GET | NASA TM-4083 wind-tunnel polars (Ladson 1988), NASA Langley Turbulence Modeling Resource (TMR) 2D RANS benchmark (Rumsey 2014), Abbott & von Doenhoff (1959). |
| **`SURROGATE`** | Inferred by a validated machine learning model with quantified epistemic uncertainty and out-of-domain detection. | CPU / Portable NumPy | `AeroSurrogateV1` forward inference with polynomial/ridge feature mapping and dual-envelope uncertainty bounds. |
| **`SIMULATED`** | Actually computed by a locally executed numerical solver (Navier-Stokes / Euler). | Local solver installation required | Grid-converged OpenFOAM `simpleFoam` or SU2 run with ASME V&V 20 grid convergence index. |
| **`USER_EXECUTED_REQUIRED` / `UNAVAILABLE`** | Computation is fully staged (valid directory tree, mesh dictionary, boundary conditions, Allrun script) but cannot be executed on the lightweight developer node. | External HPC / Cluster | OpenFOAM simpleFoam case deck generated in `data/cases/`. Staged honestly without fabricating CFD coefficients. |
| **`DEMONSTRATION`** | Synthetic or mock paths for deterministic UI unit testing. | Isolated test harness | Quarantined strictly; forbidden from entering any `EvidenceLedger` or scientific conclusion. |

---

## 2. Evidence Ledger & Backward Provenance Traversal

Every research run in AASI maintains an immutable, machine-readable `EvidenceLedger` (`backend/research/evidence_ledger.py`).

### Atomic Evidence Record Model
Each piece of scientific evidence is captured as an `EvidenceRecord`:
- `evidence_id`: Unique identifier (e.g. `ev-stage-1-question`, `ev-stage-4-comp-analytical`).
- `run_id`: Bound research campaign ID.
- `evidence_type`: `QUESTION`, `LITERATURE_CITATION`, `SURFACE_COORDINATES`, `ANALYTICAL_DERIVATION`, `SURROGATE_INFERENCE`, `CFD_CASE_DECK`, `EXPERIMENTAL_BENCHMARK`, `VALIDATION_COMPARISON`, `RESEARCH_CONCLUSION`.
- `source` & `source_identifier`: Exact origin (DOI, NASA report, file path).
- `input_hash` & `output_hash`: Cryptographic SHA-256 digests.
- `provenance_chain`: Explicit parent `evidence_id`s forming a Directed Acyclic Graph (DAG).
- `epistemic_status`: Enum from Section 1.
- `reproducibility_status`: `DETERMINISTIC`, `STATISTICALLY_REPRODUCIBLE`, `EXTERNAL_VERIFIED`.
- `license`: Verification of public domain or scientific license.

### Bi-directional Graph Traversal
Any scientific claim or conclusion must be verifiable backwards to root inputs:
$$\text{Conclusion} \longrightarrow \text{Validation} \longrightarrow \text{Computation} \longrightarrow \text{Input} \longrightarrow \text{Dataset / Source}$$

```python
# Backward chain traversal algorithm in backend/research/evidence_ledger.py
is_valid, visited, missing = ledger.verify_backward_chain("ev-stage-7-conclusion")
if not is_valid:
    # Fail closed immediately
    verdict = "INSUFFICIENT_EVIDENCE"
```

If any link in the chain is broken, missing, or unverified, the conclusion engine refuses to promote the run and caps the verdict at `INSUFFICIENT_EVIDENCE`.

---

## 3. Scientific Conclusion Hierarchy & Fail-Closed Promotion Rules

The final verdict emitted by `ScientificPromotionGate` (`backend/research/conclusion_engine.py`) cannot exceed the level justified by its evidence backing:

```
Level 6: RESEARCH_GRADE             ── [Requires multi-grid CFD + Wind-Tunnel + Surrogate]
   ▲
Level 5: MULTI_SOURCE_VALIDATED     ── [Synthesis of >=2 independent real/derived sources]
   ▲
Level 4: CFD_SUPPORTED              ── [Grid-converged Navier-Stokes / ASME V&V 20]
   ▲
Level 3: EXPERIMENTALLY_SUPPORTED   ── [Direct empirical wind-tunnel polar]
   ▲
Level 2: SURROGATE_SUPPORTED        ── [Verified ML surrogate inference within envelope]
   ▲
Level 1: ANALYTICAL_ONLY            ── [Classical thin-airfoil or potential theory]
   ▲
Level 0: INSUFFICIENT_EVIDENCE      ── [Missing links, unverified weights, failed gates]
```

### Inviolable Promotion Invariants
1. **Surrogate Cap**: A surrogate prediction alone can NEVER exceed `SURROGATE_SUPPORTED`. It cannot claim `EXPERIMENTALLY_SUPPORTED` or `CFD_SUPPORTED`.
2. **Analytical Cap**: An analytical derivation alone can NEVER exceed `ANALYTICAL_ONLY`.
3. **Citation Cap**: A literature reference alone can NEVER become `EXPERIMENTALLY_VERIFIED` without numerical validation comparison.
4. **Research-Grade Invariant**: Promotion to `RESEARCH_GRADE` strictly requires real ingested CFD results with ASME V&V 20 fine/medium/coarse grid convergence ($GCI < 5\%$) corroborated by experimental reference data.
5. **Statistical vs. Physical Separation**: High statistical correlation ($R^2 \ge 0.95$) does NOT confer physical validity. Any violation of physical invariants (e.g. $C_D \le 0$, negative lift slope in attached flow, or unverified extrapolation) forces the run to fail closed as `INSUFFICIENT_EVIDENCE`.

---

## 4. Reproducibility Bundle Specification

Every completed research run exports a complete, self-contained reproducibility bundle (`aasi_research_run_<id>/` and `.zip`) via `ResearchBundleExporter` (`backend/research/bundle.py`):

1. `research_question.json`: Formal aerodynamic problem statement, testable hypothesis, geometry, and flow conditions.
2. `sources.json`: External authoritative repositories, NASA NTRS IDs, and retrieval protocols.
3. `citations.json`: Complete BibTeX and formatted citations.
4. `dataset_manifest.json`: Ingested coordinate data, Selig format verification, and 8-stage lifecycle log.
5. `input_parameters.json`: Explicit Mach, Reynolds, AoA sweep points, and fluid properties.
6. `computation_manifest.json`: Governing equations, surrogate architecture, weights hash, and case deck parameters.
7. `solver_information.json`: OpenFOAM simpleFoam case configuration, turbulence model (`kOmegaSST`), and mesh setup.
8. `validation_results.json`: Physical metrics (slope error, symmetry, zero-lift angle) vs. statistical metrics ($R^2$, RMSE, MAE).
9. `provenance.json`: Full serialized `EvidenceLedger` with parent-child graph and Merkle root.
10. `conclusion.json`: Formal scientific verdict, conclusion level, regimes of validity, and honest limitations.
11. `README.md`: Step-by-step replication guide for independent researchers and peer reviewers.
12. `hashes.sha256`: Cryptographic SHA-256 checksums of every file in the bundle.
- `geometry/naca0012.dat`: Raw authentic Selig coordinate file.

### API Endpoints
- `GET /api/research/runs/{run_id}/bundle`: Returns JSON manifest of all bundle files and verification status.
- `GET /api/research/runs/{run_id}/export`: Streams `aasi_research_run_<run_id>.zip` for download.

---

## 5. Hardware Routing & Operational Boundaries

AASI maintains strict hardware discipline:
- **Local CPU Execution**: Analytical thin-airfoil theory, surrogate inference, geometry parsing, dataset validation, and reproducibility bundle generation run natively on 4-core, 8 GB RAM developer workstations without requiring external software or a GPU.
- **Heavy CFD Execution**: Local solvers not present in the system environment (`shutil.which("simpleFoam") == None`) are reported honestly as `USER_EXECUTED_REQUIRED`. Complete OpenFOAM decks are synthesized into `data/cases/` ready for remote cluster execution via `./Allrun`.
