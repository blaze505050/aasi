# Hypothesis Engine & Adversarial Scientific Critic

## 1. Structured Hypothesis Specification
Every scientific hypothesis in AASI is represented by `StructuredHypothesis`:
- `hypothesis_id`: Unique identifier
- `title`: Concise physical title
- `statement`: Physical causal claim
- `mechanism`: Governing aerodynamic mechanism
- `predictions`: Quantifiable predicted variables ($C_L, C_D, C_M$, shock location)
- `falsification_criteria`: Explicit numerical conditions compelling rejection
- `competing_with`: Mutually exclusive competing hypotheses
- `status`: `PROPOSED`, `UNTESTED`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `REJECTED`

## 2. Adversarial Scientific Critic
The `ScientificCritic` attacks proposed hypotheses across 9 dimensions:
1. Assumptions audited
2. Vulnerability & failure mode detection
3. Physical conservation law conflict (e.g. negative drag, circulation limit)
4. Regime applicability limits
5. Model extrapolation risk (flagging steady RANS in post-stall or high transonic)
6. Occam's razor / simpler physical explanation
7. Falsifying observation clarity
8. Alternative hypotheses consideration
9. Overall critique verdict (`TENABLE_REQUIRES_EVIDENCE`, `SEVERELY_CONSTRAINED`, `HIGH_EXTRAPOLATION_RISK`)
