# AASI — MVP Master Package

AASI (Autonomous Aerospace Scientific Intelligence) is being evolved from a verified aerospace investigation workspace into a closed-loop scientific investigation platform.

## North-star

**Question → Understand → Hypothesize → Plan → Compute → Verify → Compare → Learn → Decide → Next Experiment**

AASI should not claim “perfect physics.” Its AI provides physics-grounded reasoning; deterministic scientific tools and external evidence provide computation and verification; unverified claims never become scientific facts.

## MVP goal

A user gives AASI a real aerospace question. AASI should be able to:

1. Interpret it.
2. Extract parameters and assumptions.
3. Form hypotheses.
4. Choose an appropriate fidelity/method.
5. Detect available local compute through an explicitly installed AASI Runner.
6. Run OpenFOAM locally when available.
7. Otherwise generate a reproducible Google Colab notebook.
8. Ingest returned results.
9. Verify the computation and provenance.
10. Compare against analytical, database, surrogate, prior AASI, or experimental evidence.
11. Diagnose discrepancies and failures.
12. Preserve validated knowledge.
13. Recommend the most informative next experiment.
14. Let the user stage that experiment.

## Ten MVP capabilities

1. Local/Remote Compute Agent
2. Automatic Compute Router
3. Scientific Experiment Planner
4. Multi-Fidelity Investigation
5. Simulation–Experiment Reconciliation
6. Active Experiment Selection
7. Failure → Repair → Learn
8. Literature → Reproduction
9. Scientific Memory
10. Closed-Loop Investigator

## Critical truth rules

`PLANNED != STAGED != EXECUTED != VERIFIED`

`FAILED != SUCCESS`

A failed experiment remains immutable. A staged Colab job is not an executed simulation. An executed simulation is not verified until the verification pipeline passes.

## MVP boundary

Prove the loop first on aerospace aerodynamics/CFD. Do not attempt autonomous rocket design, unrestricted shell execution, physical hardware control, or every aerospace discipline simultaneously.

## Product principle

Build a **scientific engine with an AI interface**, not an AI interface pretending to be a scientific engine.
