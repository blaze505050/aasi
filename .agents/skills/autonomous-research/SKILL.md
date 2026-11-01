---
name: autonomous-research
description: Autonomous aerospace scientific discovery loop: hypothesis formulation, falsification criteria, automated experiment staging, multi-fidelity evidence reconciliation, and reproducible scientific report synthesis.
---

# Autonomous Scientific Research Skill

## 1. The Autonomous Discovery Loop
1. **Inquiry Formulation**: Parse the aerospace engineering problem into clear physical objectives (e.g. lift-to-drag ratio maximization, stall onset prediction, shock buffet boundary).
2. **Epistemic World Model Update**: Query existing assertions, historical experimental polars, and surrogate bounds.
3. **Competing Hypothesis Generation**: Formulate at least 2 distinct physical hypotheses with testable predictions and rigorous falsification criteria.
4. **Discriminating Experiment Design**: Select computational methods (potential flow panel solver, RANS CFD, high-speed surrogate) that can definitively confirm or refute the hypotheses.
5. **Execution & Evidence Ingestion**: Run solvers safely under resource budgets, capturing solver logs, residual convergence, and force polars.
6. **Multi-Fidelity Reconciliation**: Compare results across fidelity tiers, quantify discrepancies, and detect boundary layer or transonic breakdown.
7. **Report & Next Experiment Generation**: Generate publication-grade, self-contained Markdown/PDF dossiers with clear actionable recommendations.

## 2. Evidence Classification Standard
Every data point in the research ledger MUST be labeled with its exact epistemic source:
- `DATABASE_REAL`: Physical experimental wind tunnel or flight test measurement from published peer-reviewed literature.
- `LIVE_CFD`: Executed Navier-Stokes simulation that converged to residual tolerances on the current host.
- `SURROGATE`: Fast neural operator or regression model prediction with documented uncertainty intervals.
- `ANALYTICAL`: Closed-form first-principles equation (thin airfoil theory, vortex lattice, Karman-Tsien).
- `USER_PROVIDED`: Raw coordinates or test inputs uploaded by the operator.
- `STAGED`: Complete solver input deck generated and validated for execution, but awaiting compute dispatch.
- `NOT_EXECUTED`: Hypothetical condition or pending task.

