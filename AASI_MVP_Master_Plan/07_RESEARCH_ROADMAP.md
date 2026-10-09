# AASI — Long-Term Research Roadmap

## Tier 1 — Aerodynamics
- airfoils
- wings
- turbulence sensitivity
- mesh studies
- optimization
- aeroelasticity

## Tier 2 — Aerospace systems
- propulsion
- thermal
- structures
- flight dynamics
- trajectory analysis

## Tier 3 — Space
- orbital mechanics
- spacecraft thermal
- re-entry
- launch trajectory analysis
- mission design

## Tier 4 — Digital twins
- telemetry ingestion
- model-vs-reality comparison
- anomaly detection
- predictive maintenance
- experimental feedback

## Strong research direction

The most interesting research question is not simply “AI that runs CFD.”

It is:

> Can an autonomous agent reduce the number of expensive aerospace simulations needed to answer a scientific question while maintaining evidence quality?

Possible evaluations:

1. Random experiment selection vs AASI-selected experiments.
2. LLM-only reasoning vs tool/evidence-assisted reasoning.
3. Failure-memory enabled vs disabled.
4. Multi-fidelity routing vs always-CFD.
5. Literature reproduction and discrepancy diagnosis.

The long-term architecture remains the same:

**Question → Hypothesis → Experiment → Compute → Verify → Compare → Learn → Next Experiment**

New scientific domains become new physics/tool providers.
