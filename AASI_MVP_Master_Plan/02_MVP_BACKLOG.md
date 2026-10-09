# AASI MVP — Implementation Backlog

Work one milestone at a time. After each milestone: tests → diff audit → browser test. Do not expand scope before the current milestone is stable.

## M0 — Freeze current system

- Preserve current empirical ledger and Stage-10 validation.
- Correct stale documentation only.
- Tag a release candidate.
- Record current test/browser baselines.

**Acceptance:** no regression.

## M1 — Local Runner

Implement an explicitly installed local agent that reports:

- OpenFOAM and version
- Python
- CPU/RAM
- MPI
- CUDA
- supported solvers

Security:
- allowlist
- fixed workspace
- resource limits
- timeout
- no arbitrary shell commands
- explicit approval
- structured artifacts

## M2 — Compute Router

Choose local vs Colab using deterministic resource estimates and explain the choice.

## M3 — Colab fallback

Generate `AASI_Colab_<JOB>.ipynb` containing environment setup, exact case retrieval, execution, logs, forces, residuals, manifest and SHA-256 result packaging.

## M4 — Hypothesis Engine

For each hypothesis store:

- statement
- evidence basis
- assumptions
- prediction
- candidate test
- status

Hypotheses must not be displayed as established facts.

## M5 — Experiment Planner

Generate candidate experiments with:

- question
- changed parameters
- method
- expected information
- cost estimate
- reason
- dependencies

Start with a transparent information-value heuristic. Do not claim mathematical optimality unless implemented.

## M6 — Evidence Reconciliation

Compare analytical, database, surrogate, CFD and experimental evidence.

Report absolute/relative differences and provenance. Never fabricate uncertainty.

## M7 — Scientific Memory

Store validated cases, parameters, methods, environments, results, uncertainties, provenance, failures and conclusions.

Verified evidence gets priority over model-generated claims.

## M8 — Active-learning surrogate

Start with scikit-learn. Separate training and validation data. Warn on extrapolation. Never label predictions as CFD.

## M9 — Literature reproduction

Start with public aerospace papers/datasets. Extract setup, construct reproduction plan, execute where feasible and produce a discrepancy/reproduction report.

## M10 — Closed-loop orchestrator

Implement:

`interpret → hypothesize → plan → method → compute → execute/stage → verify → compare → remember → next experiment`

Bound the loop. Stop for sufficient evidence, approval, failure, missing dependency or uncertainty.

## M11 — UI integration

Keep the existing single scientific workspace. Add:

- hypotheses
- investigation plan
- compute destination
- verification
- comparison
- next experiment

No dashboard bloat.

## M12 — Final acceptance

Demonstrate:

`Question → Hypotheses → Plan → Local/Colab → Execution → Verification → Comparison → Memory → Next Experiment`

This is the MVP completion criterion.
