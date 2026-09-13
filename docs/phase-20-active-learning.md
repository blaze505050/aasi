# AASI Phase 20: Active Learning & Case Staging Specification

**Document ID:** AASI-SPEC-PHASE20-AL-001  
**Status:** Canonical Active Learning Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule

---

## 1. The Active Discovery Feedback Loop

Traditional passive learning samples parameters uniformly or relies on existing static datasets. AASI Phase 20 introduces active scientific experimentation:
$$\text{Train Surrogate} \longrightarrow \text{Uncertainty & OOD Sweep} \longrightarrow \text{Rank Candidates} \longrightarrow \text{Stage OpenFOAM Case Deck} \longrightarrow \text{User / External Execution} \longrightarrow \text{Ingest Validated CFD} \longrightarrow \text{Retrain}$$

---

## 2. Acquisition Scoring Formulation

Candidates are scored using a weighted multi-objective acquisition function:
$$\text{Score}(x) = w_u \cdot \tilde{\sigma}(x) + w_d \cdot \tilde{d}_{\text{OOD}}(x) + w_v \cdot \tilde{\text{Div}}(x)$$
where:
- $\tilde{\sigma}(x) \in [0, 1]$: Epistemic standard deviation normalized across the candidate grid.
- $\tilde{d}_{\text{OOD}}(x) \in [0, 1]$: Geometric and parametric distance to nearest training case.
- $\tilde{\text{Div}}(x) \in [0, 1]$: Parameter space diversity measure preventing redundant acquisitions at nearby angles of attack.
Default weights: $w_u = 0.45$, $w_d = 0.35$, $w_v = 0.20$.

---

## 3. Case Staging & Solver Execution Gate

For the top candidate experiment:
1. An OpenFOAM case directory is generated in `data/cases/staged/<candidate_id>/`.
2. Required files are created: `0/`, `constant/`, `system/controlDict`, `Allrun`, and `case_manifest.json`.
3. If local execution is requested:
   - Probing native PATH returns `SOLVER_UNAVAILABLE`.
   - The engine fail-closed, setting `execution_status = USER_EXECUTED_REQUIRED`.
   - Zero synthetic force coefficients or fabricated convergence logs are generated.
