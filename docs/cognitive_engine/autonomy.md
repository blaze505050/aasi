# Autonomy Levels & Human Governance

## 1. Explicit Autonomy Tiers
AASI strictly respects human oversight through 6 explicit autonomy levels:

- **Level 0 (Passive / Answer Only):** Responds only to direct queries using existing cached data; never plans or executes tools.
- **Level 1 (Analyze & Recommend):** Evaluates physical regime and recommends potential investigation directions.
- **Level 2 (Plan Experiments):** Generates hypotheses, criticizes them, and designs discriminating experiment plans. Halts before staging or executing.
- **Level 3 (Stage Cases & Notebooks):** Emits OpenFOAM dictionaries, meshing scripts, or Colab packages. Awaits human launch.
- **Level 4 (Safe Computational Execution):** Autonomously executes rapid, safe local deterministic tools (panel solvers, ASME V&V 20 calculations). Halts before expensive cluster dispatch.
- **Level 5 (Full Closed-Loop Scientific Investigation):** Bounded autonomous execution across the complete 16-step scientific loop, with mandatory halting conditions and safety reserves.

## 2. Invariants
- Any destructive, external cluster, or financial-cost operation strictly requires human approval regardless of autonomy level.
- The user can pause, stop, branch, or override assumptions at any point.
