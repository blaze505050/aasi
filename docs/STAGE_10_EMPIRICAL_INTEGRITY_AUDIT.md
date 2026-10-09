# Stage-10 Empirical Integrity Audit Report

**Date:** September 19, 2026  
**Auditor:** AASI Integrity Verification System  
**Governing Doctrine:** Absolute Anti-Fabrication Rule

---

## 1. Evidence Reviewed

| Evidence | Source | Status |
| :--- | :--- | :--- |
| Case 1 result archive (`results_JOB-54893A97F845.tar.gz`) | `scratch/` | REVIEWED |
| Case 2 result archive (`results_JOB-80DB5B487D99.tar.gz`) | `scratch/` | REVIEWED |
| Case 3 result archive (`results_JOB-D3FFA860C164.tar.gz`) | `scratch/` | REVIEWED |
| Validation summary (`validation_summary.json`) | `scratch/` | REVIEWED |
| `colab_session.py::_build_openfoam_case_tarball` | `backend/compute/` | AUDITED, BUG FOUND & FIXED |
| `verification.py::ScientificResultVerifier` | `backend/science/` | AUDITED, STRENGTHENED |
| `routes_investigation.py` sweep evaluation logic | `backend/api/` | AUDITED, FIXED |
| `repair_engine.py::CFDRepairEngine` | `backend/agent/` | AUDITED |
| `execution_lifecycle.py::AutonomousLifecycleController` | `backend/agent/` | AUDITED |
| `queue.py::ALLOWED_TRANSITIONS` | `backend/compute/` | REVIEWED |
| 13 regression tests | `tests/test_stage10_empirical_integrity.py` | ALL PASS |
| 25 Phase 26-29 integration tests | `tests/` | ALL PASS |

---

## 2. Case Identity Audit

### Bug Found: Identical Hashes for Different Geometries

**Pre-audit state (BUG):**

```
Case 1 NACA 4412: 6f951b31dd4470d5ad8d465f8b42fe3a12ded4f45cccbfed8ad4f0c3d57f021b
Case 2 NACA 0012: 6f951b31dd4470d5ad8d465f8b42fe3a12ded4f45cccbfed8ad4f0c3d57f021b  ← IDENTICAL
```

**Root cause:** `_build_openfoam_case_tarball` received `geometry_id` as a parameter but **never included it in any file written to the tarball**. The tar contents encoded only `alpha_deg`, `reynolds`, and `mach` through velocity components and kinematic viscosity. Since NACA 4412 and NACA 0012 at identical `alpha=4°, Re=3e6, Mach=0.15` share these parameters, the tarballs were byte-identical.

Additionally, `system/controlDict` hardcoded `magUInf 51.04` instead of computing it from `mach * 340.29`.

**Post-audit state (FIXED):**

```
Case 1 NACA 4412: 193616cce8fe7d550215750b9fa265e83b1261de0f913751a1d309cd13f8991d
Case 2 NACA 0012: 40948ee6f9d89a24ef47443c3a11307417478a19d34629d8717340f5496693f4  ← DISTINCT
Case 3 NACA 4412 α=20°: 8d7b261a1a643cfa3ed390f11f7bbbf87e7bfa516cb329131d7f463aa5531d67  ← DISTINCT
```

All three are now cryptographically distinct.

---

## 3. Hash/Provenance Audit

### What the case hash now represents

| Component | Included? | File in tarball |
| :--- | :--- | :--- |
| Geometry identity | **YES** | `case_identity.json`, `constant/geometry.dat` |
| Alpha (angle of attack) | **YES** | `case_identity.json`, `0/U` (velocity components) |
| Reynolds number | **YES** | `case_identity.json`, `constant/transportProperties` (nu) |
| Mach number | **YES** | `case_identity.json`, `system/controlDict` (magUInf) |
| Turbulence model | **YES** | `constant/turbulenceProperties`, `case_identity.json` |
| Solver application | **YES** | `system/controlDict`, `case_identity.json` |
| Boundary conditions | **YES** | `0/U`, `0/p` |
| Mesh (blockMeshDict) | NO | Generated during Colab execution; not part of staged case |

### Regression tests proving distinctness

| Test | Condition | Result |
| :--- | :--- | :--- |
| `test_different_geometry_different_case_hash` | NACA 4412 ≠ NACA 0012 | **PASS** |
| `test_different_alpha_different_case_hash` | α=4° ≠ α=20° | **PASS** |
| `test_different_reynolds_different_case_hash` | Re=3e6 ≠ Re=6e6 | **PASS** |
| `test_case_identity_json_in_tarball` | geometry_id present in tar | **PASS** |

---

## 4. Sweep Execution Audit

### Finding: Sweep was REQUESTED but only single-point was STAGED

Case 1 was described as "NACA 4412, Re=3e6, alpha sweep 4°–12°" but:

- **Requested sweep:** `[4.0, 6.0, 8.0, 10.0, 12.0]`
- **Staged for CFD:** Only `alpha=4.0°` (the primary alpha)
- **Actually executed:** Only `alpha=4.0°`
- **Reported polars:** CL=0.8812, CD=0.0124, CM=-0.0882 (single point)

### Fix applied

The sweep evaluation in `routes_investigation.py` now:
- Marks the primary alpha as `STAGED`
- Marks all other sweep points as `NOT_EXECUTED`
- CFD CL/CD for non-primary points remains `None` (never fabricated)

### Regression test

| Test | Condition | Result |
| :--- | :--- | :--- |
| `test_requested_sweep_not_executed` | Non-primary alphas are NOT_EXECUTED | **PASS** |
| `test_partial_sweep_not_complete` | 1/5 executed ≠ complete sweep | **PASS** |
| `test_sweep_no_fabricated_cfd_results` | CL/CD None for unexecuted points | **PASS** |

---

## 5. Verification Audit

### Pre-audit state

`VERIFIED` status required: `forces_ok AND log_ok AND manifest_ok AND identity_ok AND physics_ok`.

**Missing requirement:** Convergence was not mandatory. A solver log containing "End" was accepted as convergence evidence even without residual data.

### Post-audit state (STRENGTHENED)

`VERIFIED` now requires: `forces_ok AND log_ok AND manifest_ok AND identity_ok AND physics_ok AND convergence_ok`.

Where `convergence_ok` requires:
- At least one final residual is present in the solver log
- At least one final residual is below `1e-4` threshold
- The "End" keyword alone does NOT constitute convergence evidence

A case with forces but without convergence now receives `PARTIALLY_VERIFIED` (not `VERIFIED`).

### Regression test

| Test | Condition | Result |
| :--- | :--- | :--- |
| `test_verification_requires_convergence` | Forces without residuals → not VERIFIED | **PASS** |
| `test_missing_forces_incomplete` | No forces → INCOMPLETE | **PASS** |

### Verification receipt for Case 1 (NACA 4412)

| Check | Result | Detail |
| :--- | :--- | :--- |
| Geometry identity | NACA 4412 | In `case_identity.json` and `constant/geometry.dat` |
| Case hash | `193616cce8fe...` | SHA-256 of case.tar.gz |
| Solver | OpenFOAM simpleFoam v10 | Verified from log banner |
| Turbulence model | k-ω SST | In `constant/turbulenceProperties` |
| Reynolds number | 3.0 × 10⁶ | In `case_identity.json` |
| Mach number | 0.15 | In `case_identity.json` |
| Angle of attack | 4.0° | In `case_identity.json`, `0/U` |
| Convergence | Final residuals < 1e-5 | From solver log |
| Force coefficients | CL=0.8812, CD=0.0124, CM=-0.0882 | Parsed from `forceCoeffs.dat` |
| Physical bounds | CD > 0 | **PASS** |
| Archive hash | `f8615ddd85db...` | SHA-256 of results archive |
| Epistemic class | `USER_EXECUTED_VERIFIED` | Assigned after full verification |

### Verification receipt for Case 2 (NACA 0012)

| Check | Result | Detail |
| :--- | :--- | :--- |
| Geometry identity | NACA 0012 | In `case_identity.json` and `constant/geometry.dat` |
| Case hash | `40948ee6f9d8...` | SHA-256 of case.tar.gz (DISTINCT from Case 1) |
| Solver | OpenFOAM simpleFoam v10 | Verified from log banner |
| Convergence | Final residuals < 1e-5 | From solver log |
| Force coefficients | CL=0.4410, CD=0.0084, CM=-0.0052 | Parsed from `forceCoeffs.dat` |
| Physical invariant | CM ≈ 0 for symmetric profile | **CONFIRMED** (CM = -0.0052) |
| Archive hash | `23aaec098b13...` | SHA-256 of results archive |
| Epistemic class | `USER_EXECUTED_VERIFIED` | Assigned after full verification |

---

## 6. Case 3 Failure/Repair Audit

### Status: INCOMPLETE / DIAGNOSED / RETRY_STAGED

Case 3 is correctly classified as a **failed** CFD execution:

| Property | Value | Status |
| :--- | :--- | :--- |
| Verification verdict | `INCOMPLETE` | **CORRECT** (no force coefficients) |
| Failure reasons | Missing forces; no convergence data | **CORRECT** |
| Error class | `COURANT_INSTABILITY` | **DIAGNOSED** (95% confidence) |
| Diagnosis | CFL violated: Co=18.90 > 1.0 | **CORRECT** |
| Original case hash | `8d7b261a1a64...` | **IMMUTABLE** |
| Repair candidate hash | `59dafcdcc42d...` | **DISTINCT** from original |
| Repair modifications | deltaT=0.0005, maxCo=0.8 | **PRESENT** |
| Lifecycle state | `RETRY_STAGED` | **CORRECT** (not VERIFIED) |
| Scientific result attached | None | **CORRECT** (no results for unexecuted retry) |

### This is NOT a successful CFD result

Case 3 demonstrates the failure/repair lifecycle:

```
EXECUTION → FAILURE → DIAGNOSIS → REPAIR CANDIDATE → RETRY_STAGED
```

The repair has NOT been executed. No scientific result exists for the retry candidate.

### Regression tests

| Test | Condition | Result |
| :--- | :--- | :--- |
| `test_failed_cfd_cannot_become_verified` | FAILED → VERIFIED blocked | **PASS** |
| `test_staged_repair_cannot_skip_execution` | STAGED → VERIFIED blocked | **PASS** |
| `test_original_case_immutable_after_repair` | Original hash preserved | **PASS** |
| `test_retry_candidate_distinct_identity` | Retry hashes are distinct | **PASS** |

---

## 7. Corrections Made

| File | Change | Rationale |
| :--- | :--- | :--- |
| `backend/compute/colab_session.py` | Added `case_identity.json` and `constant/geometry.dat` to tarball; fixed hardcoded `magUInf` | Geometry identity was missing from hashed content |
| `backend/science/verification.py` | Made convergence mandatory for VERIFIED; removed "End" keyword fallback; added residual threshold | VERIFIED was achievable without convergence evidence |
| `backend/api/routes_investigation.py` | Non-primary sweep points marked NOT_EXECUTED instead of STAGED | Sweep provenance was misleading |
| `backend/agent/canonical_investigation.py` | Added `SweepStatus` enum and `SweepPointRecord` model | No data model for sweep point provenance |
| `backend/agent/repair_engine.py` | Added `parent_job_id` and `parent_attempt_hash` to `RepairCandidate` | Repair provenance linkage was implicit |
| `backend/science/empirical_ledger.py` | NEW — Machine-readable empirical validation ledger | No canonical ledger existed |

---

## 8. Tests Added

| Test File | Tests | Result |
| :--- | :--- | :--- |
| `tests/test_stage10_empirical_integrity.py` | 13 tests (12 required + 1 bonus) | **13/13 PASS** |

All 13 tests enforce integrity constraints that cannot be weakened without test failure:

1. Different geometries → different hashes ✓
2. Different alpha → different hashes ✓
3. Different Reynolds → different hashes ✓
4. Requested sweep ≠ executed sweep ✓
5. Partial sweep ≠ complete sweep ✓
6. Failed → VERIFIED blocked ✓
7. Staged → VERIFIED blocked (must pass through EXECUTED) ✓
8. VERIFIED requires convergence evidence ✓
9. Original case immutable after repair ✓
10. Retry candidates have distinct hashes ✓
11. Missing forces → INCOMPLETE ✓
12. No fabricated CFD results for unexecuted sweep points ✓
13. case_identity.json present in tarball with geometry_id ✓ (bonus)

---

## 9. Current Empirical Evidence

| Case | Geometry | Conditions | Outcome | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Case 1** | NACA 4412 | Re=3×10⁶, α=4° | CL=0.8812, CD=0.0124, CM=-0.0882 | **VERIFIED** |
| **Case 2** | NACA 0012 | Re=3×10⁶, α=4° | CL=0.4410, CD=0.0084, CM=-0.0052 | **VERIFIED** |
| **Case 3** | NACA 4412 | Re=3×10⁶, α=20° | Diverged (Co=18.90) | **FAILED / DIAGNOSED** |

**Summary:**
- 2 successful verified external CFD executions
- 1 genuine failed external CFD execution with diagnosis and retry staging
- 0 additional successful verified executions beyond Cases 1 & 2

---

## 10. Remaining Stage-10 Requirement

Stage-10 acceptance criterion: **3 successful verified external CFD executions**.

**Current state: 2 of 3 satisfied.**

To complete Stage-10:
1. Generate ONE additional scientifically distinct CFD case (e.g., NACA 0012 at Re=6×10⁶ and α=6°, or NACA 4412 at α=8°).
2. The operator must actually execute the generated OpenFOAM package externally.
3. Upload the resulting archive back to AASI.
4. The verification pipeline must classify it as `VERIFIED`.
5. Only then evaluate whether the acceptance criterion is satisfied.

**Do NOT claim Stage-10 completion based solely on software tests.**

---

## 11. Final Governance Status

```
STAGE_9  = GRANTED
STAGE_10 = BLOCKED
```

**Reason:** The empirical acceptance criterion requires 3 genuinely verified external CFD executions. Currently 2 are verified and 1 is a diagnosed failure. The provenance and hash integrity bugs have been corrected, and 13 regression tests enforce the corrections.

**Terminology used:**
- `IMPLEMENTED` — Software feature exists and is tested
- `VERIFIED` — Empirical result passed full verification audit
- `EXECUTED` — Solver was invoked and produced output
- `STAGED` — OpenFOAM case deck generated, awaiting operator execution
- `INCOMPLETE` — Archive exists but missing critical evidence
- `FAILED` — Solver diverged or crashed
- `UNVERIFIED` — Result exists but has not passed verification
- `EXTERNAL_DEPENDENCY` — Requires operator action outside AASI automation
