# Aerospace World Model Specification

## 1. Concept & Purpose
The `AerospaceWorldModel` is the central, persistent, versioned state of the AASI Cognitive Engine. It is explicitly **not a vector database**; it is a structured physical ontology that captures:
1. **Investigation Framing:** Objective, target quantities, tolerance, active continuum regimes.
2. **Physical System State:** Normalized airfoil geometry, fluid environment, and freestream operating conditions ($\alpha, Re, M, q_\infty$).
3. **Cognitive & Epistemic State:** Explicit assumptions, hypotheses, evidence, experiments, simulations, contradictions, decisions, and recognized unknowns.
4. **Cryptographic Lineage:** SHA-256 Merkle-dag hashing linking each snapshot to its parent version.

## 2. Invariants
- **Non-Fact Principle:** Hypotheses are testable conjectures, never facts.
- **Explicit Unknowns:** The world model explicitly declares unmeasured or unmodeled physical quantities in `unknowns`.
- **Truth Semantics:** Every assertion carries `source`, `status`, `timestamp`, and `epistemic_tier`. An assertion in a lower tier (e.g. `MODEL_GENERATED`) can never overwrite a higher tier (e.g. `NUMERICAL_AUDITED` or `EMPIRICAL_BENCHMARK`).
