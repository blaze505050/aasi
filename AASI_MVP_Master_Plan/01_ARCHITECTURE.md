# AASI — Complete Architecture

## System

```text
AASI Web UI
    |
    v
FastAPI Control Plane
    |
    +--> Inquiry / Hypothesis / Planning
    +--> Method & Fidelity Selection
    +--> Compute Router
    +--> Verification
    +--> Comparison / Discrepancy
    +--> Scientific Memory
    +--> Next-Experiment Engine
    +--> Provenance
    |
    +--> AASI Local Runner
    |       +--> OpenFOAM
    |       +--> Python
    |       +--> MPI / CUDA detection
    |
    +--> Remote execution
            +--> Google Colab
            +--> future HPC
```

## The AI brain

The brain is a coordinated stack, not one LLM:

- **Language/reasoning layer:** interprets questions, generates hypotheses and explanations.
- **Physics layer:** equations, dimensional analysis, aerospace domain knowledge.
- **Deterministic tools:** NumPy, SciPy, OpenFOAM and other scientific solvers.
- **Evidence layer:** decides what was actually computed and verified.
- **Memory:** stores validated evidence, failures and assumptions.
- **Planner:** determines what should happen next.

The LLM must never manufacture numerical results.

## Investigation graph

```text
Question
  ↓
Hypothesis
  ↓
Experiment
  ↓
Method
  ↓
Execution
  ↓
Artifact
  ↓
Verification
  ↓
Evidence
  ↓
Comparison
  ↓
Conclusion
  ↓
Next Experiment
```

Every node should have stable IDs and provenance.

## Local Runner

The browser must not directly execute arbitrary commands.

```text
Browser → AASI API → explicitly installed Local Runner → allowlisted solver
```

Runner requirements:

- explicit installation
- authenticated session
- allowlisted executables
- fixed scientific workspace
- timeout/resource limits
- no arbitrary shell input
- artifact-only return
- explicit user approval at execution boundary

Capability response should include OpenFOAM version, CPU, RAM, Python, MPI, CUDA and supported solvers.

## Compute Router

Inputs:
- estimated cells
- timestep count
- memory
- solver
- parallelism
- local capabilities

Outputs:
- `LOCAL`
- `COLAB`
- `REMOTE_FUTURE`
- `UNAVAILABLE`

Every choice must include an explanation.

## Colab fallback

AASI generates a notebook containing:

1. environment setup
2. exact case retrieval
3. solver execution
4. log capture
5. residual extraction
6. force extraction
7. execution manifest
8. SHA-256 packaging
9. upload-ready result archive

The notebook must never declare a result VERIFIED. AASI verifies the uploaded archive afterward.

## Scientific artifact

```text
investigation/
├── question.json
├── hypotheses.json
├── plan.json
├── case/
├── execution/
├── results/
├── verification/
├── provenance/
└── report.md
```

## Verification

```text
Upload
 ↓
Archive safety
 ↓
Identity check
 ↓
Solver-log authenticity
 ↓
Residual convergence
 ↓
Numerical stability
 ↓
Force stabilization
 ↓
Physical plausibility
 ↓
Provenance
 ↓
VERIFIED / FAILED / INCOMPLETE
```

## Repository target

```text
AASI/
├── backend/
│   ├── api/
│   ├── auth/
│   ├── core/
│   ├── investigation/
│   ├── planner/
│   ├── physics/
│   ├── compute/
│   ├── verification/
│   ├── memory/
│   ├── provenance/
│   └── storage/
├── runner/
│   ├── detector/
│   ├── sandbox/
│   ├── executors/
│   └── protocol/
├── frontend/
├── scientific/
│   ├── equations/
│   ├── reference_data/
│   ├── benchmarks/
│   └── models/
├── notebooks/
├── experiments/
├── tests/
└── docs/
```
