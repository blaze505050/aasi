---
name: scientific-code-review
description: Reviews AASI code changes for scientific correctness, unit consistency, numerical stability, and proper epistemic classification. Use when modifying physics engine, surrogate models, or validation logic.
---

# Scientific Code Review Skill

## Purpose
Ensures every code change to AASI's scientific modules maintains correctness, reproduciblity, and honest epistemic classification.

## Checklist for Every Scientific Change

### 1. Physical Correctness
- [ ] All equations reference a specific textbook, paper, or standard (e.g., Katz & Plotkin, ASME V&V 20)
- [ ] Units are explicit in variable names or comments (e.g., `alpha_rad`, `reynolds`, `mach`)
- [ ] Physical constants use authoritative values (NIST, IAU) not hand-typed approximations
- [ ] Domain of validity is documented and enforced (e.g., Mach < 0.8 for Prandtl-Glauert)
- [ ] Edge cases are handled (e.g., `p == 0` for symmetric airfoils, `Re == 0`)

### 2. Numerical Stability
- [ ] No division by zero without guards (use `np.clip`, `max()`, or explicit checks)
- [ ] Matrix operations use `np.linalg.solve` not `np.linalg.inv` where possible
- [ ] Floating point comparisons use tolerances (not `==`)
- [ ] Large/small number operations use log-space or normalization
- [ ] Verify `np.where` guards don't produce warnings before the guard evaluates

### 3. Epistemic Classification
- [ ] Every output is labeled: CALCULATED | PREDICTED | ESTIMATED | ASSUMED | UNVERIFIED
- [ ] Surrogate predictions carry OOD status: IN_DOMAIN | EXTRAPOLATION | OUT_OF_DOMAIN
- [ ] Panel solver results are labeled "VERIFIED_PANEL_VISCOUS" not "CFD"
- [ ] Never label a surrogate prediction as "experimental" or "validated"
- [ ] Uncertainty bounds are honestly reported (calibrated vs uncalibrated)

### 4. Reproducibility
- [ ] Random seeds are explicitly set and documented
- [ ] Deterministic behavior verified: same inputs → same outputs
- [ ] Configuration captured in output (model version, code revision)
- [ ] SHA-256 checksums for model weights

### 5. Data Integrity
- [ ] No geometry leakage between train/test splits
- [ ] Dataset provenance documented (source, license, retrieval date)
- [ ] Preprocessing steps are deterministic and recorded
- [ ] No silent data fabrication or interpolation without disclosure
