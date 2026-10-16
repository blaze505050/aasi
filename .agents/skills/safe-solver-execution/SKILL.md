---
name: safe-solver-execution
description: Safe execution patterns for external CFD solvers (OpenFOAM, SU2, XFOIL). Use when modifying simulation execution, subprocess handling, or adding new solver integrations.
---

# Safe Solver Execution Skill

## Purpose
Ensures AASI's external solver execution is safe, sandboxed, and honest about results.

## Pre-Execution Checklist

1. **Detect solver availability** — use `shutil.which()` not hardcoded paths
2. **Check version** — log solver version for reproducibility
3. **Validate inputs** — verify geometry, conditions, and mesh parameters before execution
4. **Create isolated job directory** — never share directories between jobs
5. **Generate deterministic configuration** — same inputs → same configs
6. **Set resource limits** — timeout, memory limit, disk quota

## Execution Rules

### Subprocess Safety
```python
# ✅ CORRECT: Use argument lists
subprocess.run(["simpleFoam", "-case", case_dir], timeout=1800, ...)

# ❌ WRONG: Shell string construction
subprocess.run(f"simpleFoam -case {case_dir}", shell=True, ...)
```

### Output Handling
- Capture stdout, stderr, exit code, runtime
- Parse residuals and force coefficients from logs
- Verify convergence status (exit code 0 ≠ physical convergence)
- Check mass balance, residual levels, force history oscillation
- Preserve input deck and execution manifest

### Fail-Closed Rules
- Solver not found → return `SOLVER_UNAVAILABLE` (not an error)
- Solver crashed → return `SOLVER_DIVERGED` with diagnostic info
- Solver timed out → return `SOLVER_TIMEOUT` with partial results
- Unconverged → return `UNCONVERGED` (never label as validated)
- Missing output files → return appropriate error

### Never Do
- Never claim a successful simulation if the solver failed
- Never label an incomplete run as validated
- Never claim mesh adequacy solely because the solver completed
- Never execute user-supplied arbitrary code
- Never run without timeout limits
- Never trust solver output without convergence checks

## Cleanup
- Remove temporary files after extraction
- Preserve essential artifacts (log, mesh, solution)
- Record disk usage and runtime
