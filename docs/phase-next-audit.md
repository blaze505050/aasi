# AASI Flagship Research Pipeline: Comprehensive Epistemic Audit

**Audit Date**: September 12, 2026  
**Auditor**: AASI Autonomous Scientific Integrity Core  
**Governing Standard**: *AASI Master Engineering Directive: Real Scientific Execution, Evidence Integrity & Independent Reproducibility*  

---

## 1. Executive Summary

A comprehensive architectural and computational audit of the AASI repository was performed across the complete flagship research workflow:
$$\text{Question} \longrightarrow \text{Evidence} \longrightarrow \text{Data Discovery/Acquisition} \longrightarrow \text{Data Validation} \longrightarrow \text{Computation} \longrightarrow \text{Validation} \longrightarrow \text{Provenance} \longrightarrow \text{Conclusion} \longrightarrow \text{Presentation}$$

Every stage of the flagship NACA 0012 pipeline (`ResearchRunOrchestrator.execute_flagship_naca0012`) was scrutinized against the epistemic classification standards:
- **`REAL`**: Genuinely downloaded/parsed data or genuinely executed computation.
- **`DERIVED`**: Numerically calculated from real physical inputs.
- **`REFERENCED`**: Authoritative external values from verified scientific sources.
- **`SIMULATED`**: Actually computed by a verified numerical solver.
- **`SURROGATE`**: Inferred by a validated machine learning model with uncertainty bounds.
- **`PARTIALLY REAL`**: Mix of real calculation/ingestion and hard-coded or static linkages.
- **`MOCK`**: Hard-coded values or stubs pretending to be live execution.
- **`SCAFFOLD`**: Architectural structure ready for execution, awaiting input or external runner.
- **`UNAVAILABLE` / `USER_EXECUTED_REQUIRED`**: Operation cannot be executed locally and requires external infrastructure or user intervention.
- **`DEMONSTRATION`**: Deterministic demonstration path strictly isolated from scientific evidence.

---

## 2. Stage-by-Stage Detailed Epistemic Audit

| Pipeline Stage | Implementation Component | Epistemic Classification | Actual Behavior | Scientific Gap / Action Required |
|---|---|---|---|---|
| **1. Research Question & Hypothesis** | `backend/research/service.py:220-251` | **REAL** | Instantiates formal aerodynamic research question for NACA 0012 ($Re=3.0\times 10^6, M=0.15, \alpha \in [-4^\circ, 16^\circ]$) with testable quantitative hypothesis. Computes SHA-256 hash. | Fully functional. Must be bound into the unified `EvidenceLedger`. |
| **2. Literature Evidence Retrieval** | `backend/research/service.py:252-295`<br>`backend/sources/` | **PARTIALLY REAL** | Cites verified authoritative publications (NASA TM-4083, Abbott Dover 1959, NASA Langley TMR 2014) with report IDs and public domain licenses. Live search adapters (`nasa.py`, `arxiv.py`, `semantic_scholar.py`) exist with fail-closed timeouts. However, the flagship run statically instantiates these citations rather than dynamically querying or recording them in an immutable ledger. | Ingest citations into the `EvidenceLedger` with source identifiers, hashes, and retrieval timestamps. |
| **3. Dataset Discovery & Acquisition** | `backend/research/service.py:297-327`<br>`data/datasets/` | **PARTIALLY REAL** | Uses an in-memory Selig coordinate string constant (`NACA0012_COORDINATES`) rather than loading authentic airfoil coordinates directly from disk (`data/datasets/authentic_airfoils/airfoil_geometries.json` or `.dat` file). | Replace in-memory string with authentic file loader from `data/datasets/authentic_airfoils/` with file path and SHA-256 provenance tracking. |
| **4. Dataset Validation & Ingestion** | `backend/datasets/pipeline.py`<br>`backend/datasets/validator.py` | **REAL** | Strictly executes the 8-stage cryptographic lifecycle (`DISCOVERED` $\rightarrow$ `LICENSE_VERIFIED` $\rightarrow$ `DOWNLOADED` $\rightarrow$ `HASH_VERIFIED` $\rightarrow$ `PARSED` $\rightarrow$ `VALIDATED` $\rightarrow$ `SPLIT` $\rightarrow$ `READY_FOR_TRAINING`). Checks Selig format, chord normalization, thickness ratio (12% $\pm$ 0.5%), leading/trailing edge sanity, and licensing. Fails closed on any corruption or proprietary license. | Fully operational and real. |
| **5. Multi-Modal Computation** | `backend/research/service.py:329-384`<br>`backend/physics/benchmark.py`<br>`backend/simulation/case_generator.py` | **REAL** (Analytical & Surrogate)<br>**SCAFFOLD / USER_EXECUTED_REQUIRED** (CFD) | - **Analytical**: Exact Thin-Airfoil Potential Theory ($dC_L/d\alpha = 2\pi/\text{rad} \approx 0.10966/^\circ, \alpha_0 = 0^\circ$). **DERIVED**.<br>- **Surrogate**: Real forward evaluation of `AeroSurrogateV1` across 11 AoA points using polynomial/ridge regression and epistemic uncertainty quantification. **SURROGATE**.<br>- **CFD Deck**: Generates valid OpenFOAM directory tree (`0/`, `constant/`, `system/`, `Allrun`, `blockMeshDict`) with cryptographic file hashes. Correctly marks status `USER_EXECUTED_REQUIRED` without fabricating CFD output. | Ensure epistemic tags (`DERIVED`, `SURROGATE`, `UNAVAILABLE`) are permanently attached to every computed number. Never allow surrogate predictions to masquerade as CFD. |
| **6. Aerodynamic Validation** | `backend/physics/benchmark.py`<br>`backend/research/benchmarks.py` | **REAL** | Evaluates comparative physical metrics: MAE, RMSE, lift-curve slope discrepancy vs. thin-airfoil theory ($<3\%$), reflectional symmetry error ($<0.05$), and zero-lift angle. Compares surrogate predictions against authoritative NASA TM-4083 experimental wind tunnel polar and NASA Langley TMR CFD verification data. | Clarify distinction between **statistical agreement** (R², RMSE) and **physical validity** (monotonicity, drag positivity, stall separation physics). Distinguish `REFERENCED` NASA experimental data from local `SIMULATED` data. |
| **7. Provenance & Chain of Custody** | `backend/research/service.py:406-432` | **PARTIALLY REAL** | Hashes question, evidence, dataset, model checkpoint, computation, and validation into a 64-character composite SHA-256 fingerprint. However, it is stored as a flat dictionary without backwards graph traversal. | Build `EvidenceLedger` with bidirectional traversal: Conclusion $\rightarrow$ Validation $\rightarrow$ Computation $\rightarrow$ Input $\rightarrow$ Source. Flag any broken link as `INSUFFICIENT_EVIDENCE`. |
| **8. Scientific Conclusion Engine** | `backend/research/service.py:434-476` | **PARTIALLY REAL** | Emits honest regime-bounded conclusion (`HYPOTHESIS_CONFIRMED_WITH_REGIME_LIMITS`) noting high confidence in linear range ($-4^\circ \le \alpha \le 8^\circ$) and widening uncertainty in stall regime ($\alpha \ge 12^\circ$). Explicitly declares CFD as `USER_EXECUTED_REQUIRED`. However, lacks formal conclusion levels and strict promotion rules. | Implement hierarchical scientific conclusion levels (`INSUFFICIENT_EVIDENCE`, `ANALYTICAL_ONLY`, `SURROGATE_SUPPORTED`, `MULTI_SOURCE_VALIDATED`, `RESEARCH_GRADE`). Enforce strict promotion gates. |
| **9. Reproducibility Bundle** | N/A | **SCAFFOLD / MISSING** | The existing system generates Markdown and LaTeX summary reports, but cannot generate a self-contained, machine-readable reproducibility bundle (`aasi_research_run_<id>/` and `.zip`) containing the 12 canonical JSON descriptors, OpenFOAM case deck, and `hashes.sha256`. | Implement `backend/research/bundle.py` to package and serve complete reproducibility bundles via REST API. |
| **10. Frontend Epistemic Presentation** | `frontend/app/page.tsx`<br>`frontend/components/ResearchPipelineView.tsx` | **PARTIALLY REAL** | Interactive UI displays the 7-stage pipeline, flow conditions, polar charts, and composite SHA-256 fingerprint. However, it does not visually distinguish between `DERIVED`, `REFERENCED`, and `SURROGATE` data points with dedicated badges, and lacks a 1-click "Download Reproducibility Bundle" button. | Add epistemic badges to comparison tables and introduce Reproducibility Bundle download action. |

---

## 3. Truth-Preserving Gaps & Resolution Strategy

### Gap A: Evidence Ledger & Bi-directional Traversal
- **Problem**: Current provenance is a flat dictionary of hashes rather than an immutable ledger of typed records.
- **Solution**: Create `backend/research/evidence_ledger.py` with `EvidenceRecord` and `EvidenceLedger`. Implement recursive backward traversal from conclusions to raw inputs. Mark conclusions incomplete if any link is broken.

### Gap B: Dataset Provenance in Flagship Run
- **Problem**: `execute_flagship_naca0012` uses a hard-coded coordinate string in `service.py`.
- **Solution**: Load authentic NACA 0012 coordinates from `data/datasets/authentic_airfoils/airfoil_geometries.json` (or local file), record disk path, file hash, and UIUC/NASA source in the `EvidenceLedger`.

### Gap C: Scientific Conclusion Hierarchy
- **Problem**: Flat verdict strings lack formal epistemic promotion levels.
- **Solution**: Implement conclusion levels:
  1. `INSUFFICIENT_EVIDENCE`
  2. `ANALYTICAL_ONLY`
  3. `SURROGATE_SUPPORTED`
  4. `EXPERIMENTALLY_SUPPORTED`
  5. `CFD_SUPPORTED`
  6. `MULTI_SOURCE_VALIDATED`
  7. `RESEARCH_GRADE`
  Enforce fail-closed promotion rules: surrogate predictions alone cannot claim `EXPERIMENTALLY_SUPPORTED` or `CFD_SUPPORTED`; research-grade requires multi-grid CFD (ASME V&V 20) + experimental reference + verified surrogate.

### Gap D: Reproducibility Bundle Export
- **Problem**: No automated mechanism to export a complete, machine-readable archive for peer review or independent replication.
- **Solution**: Implement `ResearchBundleExporter` generating `aasi_research_run_<id>.zip` with 12 canonical JSON files, `hashes.sha256`, OpenFOAM case files, and `README.md`.

### Gap E: Adversarial Integrity Test Suite
- **Problem**: Existing tests verify happy paths and basic validation gates, but lack targeted attacks on scientific integrity (corrupted datasets, missing checkpoints, forged hashes, out-of-domain evaluation, illegitimate conclusion promotion).
- **Solution**: Implement `tests/test_scientific_adversarial_integrity.py` with tests designed to break scientific integrity, confirming AASI fails closed with `INSUFFICIENT_EVIDENCE` or explicit error.
