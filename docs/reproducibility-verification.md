# AASI Independent Scientific Reproducibility Verification Protocol

## 1. Directive & Core Mission
Governing Directive: **Real Scientific Execution, Evidence Integrity & Independent Reproducibility.**

The AASI Reproducibility Verifier (`backend/research/verifier.py`) acts as an automated, independent peer-review auditor. Given any research run bundle or directory, it executes an 8-point automated compliance audit to prove or disprove scientific reproducibility without human intervention.

---

## 2. The 8-Point Reproducibility Audit

```
┌──────────────────────────────────────────────────────────────┐
│             8-Point Automated Reproducibility Audit          │
├──────────────────────────────────────────────────────────────┤
│ 1. Bit-for-Bit SHA-256 Checksum Verification                 │
│    - Recomputes SHA-256 of every file in the bundle.         │
│    - Compares against hashes.sha256 manifest.                │
│    - Immediate REPRODUCTION_FAILED if 1 byte differs.        │
├──────────────────────────────────────────────────────────────┤
│ 2. Canonical File Descriptor Presence Check                  │
│    - Verifies presence of all 14 canonical descriptors:      │
│      research_question.json, sources.json, citations.json,   │
│      dataset_manifest.json, input_parameters.json,          │
│      geometry.json, computation_spec.json,                   │
│      surrogate_metrics.json, validation_results.json,        │
│      uncertainty_assessment.json, grid_convergence.json,     │
│      provenance.json, conclusion.json, reproduce.json.       │
├──────────────────────────────────────────────────────────────┤
│ 3. Airfoil Geometry (.dat) Coordinate Integrity              │
│    - Checks Selig standard format (x, y) coordinates.        │
│    - Validates leading edge (0, 0) and trailing edge (1, y). │
├──────────────────────────────────────────────────────────────┤
│ 4. 8-Stage Dataset Lifecycle Verification                    │
│    - Ensures dataset passed to READY_FOR_TRAINING.           │
├──────────────────────────────────────────────────────────────┤
│ 5. Physical Validation & Statistical Metrics Consistency     │
│    - Confirms R^2, RMSE, MAE, and slope errors parse cleanly.│
├──────────────────────────────────────────────────────────────┤
│ 6. Cryptographic Evidence Ledger DAG Traversal               │
│    - Reconstructs backward DAG traversal:                    │
│      Conclusion -> Validation -> Computation -> Dataset.     │
│    - Audits for cycles, orphans, and broken parent links.    │
│    - Verifies composite Merkle root hash.                    │
├──────────────────────────────────────────────────────────────┤
│ 7. Formal Promotion Gate Verdict Soundness                   │
│    - Asserts conclusion level matches evidence strength.     │
├──────────────────────────────────────────────────────────────┤
│ 8. Machine-Readable Reproduction Contract Validation         │
│    - Verifies reproduce.json environment & execution steps.  │
│    - Checks REPRODUCE.md human instructions.                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Verification API & Verification Statuses

The platform exposes an automated verification endpoint:
```http
POST /api/research/reproduce/verify
Content-Type: application/json

{
  "run_id": "RUN-NACA0012-1726000000"
}
```

### Possible Status Verdicts:
1. `VERIFIED_REPRODUCIBLE`: All 8 checks passed; bit-for-bit checksums identical, Merkle root verified, GCI and 5-tier uncertainty present.
2. `PARTIALLY_REPRODUCIBLE`: Descriptors present, but external CFD requires user host execution.
3. `REPRODUCTION_FAILED`: Tampering detected (hash mismatch) or corrupt descriptor.
4. `INSUFFICIENT_REPRODUCTION_DATA`: Incomplete bundle missing mandatory descriptors.
