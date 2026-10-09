# AASI — Copy/Paste Antigravity Prompts

Use one prompt at a time. Do not ask the coding agent to implement the whole roadmap in one pass.

## Prompt 1 — Audit

Read the entire existing AASI repository. Do not modify code. Map the existing investigation state machine, empirical ledger, provenance, verification, next-experiment engine, frontend and exact extension points for a Local Runner. Identify regression risks.

## Prompt 2 — Local Runner

Implement an explicit AASI Local Runner. It must detect OpenFOAM, Python, MPI, CUDA, CPU and RAM. Use an allowlisted executable model, fixed workspace, time/resource limits, authentication, explicit approval and structured artifact return. Never permit arbitrary shell commands. Add tests.

## Prompt 3 — Compute Router

Implement a deterministic compute router that chooses LOCAL, COLAB, REMOTE_FUTURE or UNAVAILABLE from case requirements and detected capabilities. Include an explanation for every decision. Do not claim exact runtime predictions.

## Prompt 4 — Colab

Implement reproducible Colab notebook generation. The notebook must set up the environment, retrieve the exact case, execute it, capture logs/residuals/forces, create a manifest and SHA-256 archive, and produce an upload-ready result. The notebook must never declare VERIFIED.

## Prompt 5 — Hypotheses

Implement structured scientific hypotheses containing statement, evidence basis, assumptions, prediction, candidate test and status. Hypotheses must never be represented as established facts.

## Prompt 6 — Planner

Implement candidate experiment generation with question, parameters, method, expected information, cost estimate, dependencies and rationale. Start with a transparent heuristic. Do not claim mathematically optimal experiment selection.

## Prompt 7 — Evidence

Implement comparison between analytical, reference, surrogate, CFD and experimental evidence. Calculate discrepancies with units and provenance. Never fabricate uncertainty.

## Prompt 8 — Memory

Implement scientific memory for verified results, failures, assumptions, environments and provenance. Add similarity retrieval over geometry/Re/Mach/AoA/solver/target quantity. Verified evidence must have higher trust than model-generated text.

## Prompt 9 — Surrogate

Implement a lightweight scikit-learn surrogate workflow with train/validation separation and extrapolation warnings. Never label surrogate predictions as CFD. Add tests.

## Prompt 10 — Closed Loop

Implement:

`interpret → hypothesize → plan → method → compute → execute/stage → verify → compare → remember → next experiment`

Bound the loop. Never execute unlimited experiments autonomously. Stop for sufficient evidence, user approval, failure, missing dependency or unresolved uncertainty.

## Prompt 11 — UI

Integrate hypotheses, plan, compute destination, verification, comparison and next experiment into the existing scientific workspace. Do not create dashboard bloat. All legitimate researcher operations must be accessible from the UI.

## Prompt 12 — Acceptance

Run full backend/scientific tests, frontend build, browser acceptance, Local Runner tests, notebook-generation tests, provenance tests, negative-path tests and mobile tests. Verify:

`STAGED != EXECUTED`
`EXECUTED != VERIFIED`
`FAILED != SUCCESS`

Do not add new features during this audit.
