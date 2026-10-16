# AASI Baseline Test Report — Phase A Audit

**Date:** 2026-10-16
**Commit:** `5b0a5da` (main branch, clean working tree)
**Environment:** Python 3.12.10, Windows 11, pytest 8.4.2

---

## Test Execution Summary

| Metric | Value |
|---|---|
| **Command** | `.\.venv\Scripts\python.exe -m pytest tests/ --tb=line -q` |
| **Total Tests** | 946 |
| **Passed** | 946 |
| **Failed** | 0 |
| **Skipped** | 0 |
| **Errors** | 0 |
| **Warnings** | 8 |
| **Duration** | 118.89s (1 min 58 sec) |
| **Exit Code** | 0 |

## Result: ✅ ALL 946 TESTS PASS

---

## Warnings (8 total)

### 1. Starlette httpx deprecation (2 warnings)
```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
```
**Severity:** LOW — Deprecation in test infrastructure, not production code.

### 2. scikit-learn ill-conditioned matrix (2 warnings)
```
LinAlgWarning: An ill-conditioned matrix detected: slice 0 has rcond = 3.748149246613351e-17.
```
**Location:** `test_model_lifecycle_milestone_d.py::test_deterministic_cpu_training_reproducibility`
**Severity:** MEDIUM — Ridge regression baseline encountering near-singular data. May indicate insufficient training data diversity or feature scaling issues.

### 3. NumPy runtime warnings in benchmarking (3 warnings)
```
RuntimeWarning: invalid value encountered in divide
RuntimeWarning: divide by zero encountered in divide
```
**Location:** `backend/physics_ai/benchmark_models.py:69` in R² calculation
**Severity:** MEDIUM — Division by zero when `ss_tot` is near zero (constant target). The `np.where` guard exists but triggers the warning before the guard.

---

## Test Distribution by Module

| Test File Category | File Count | Approximate Test Count |
|---|---|---|
| Phase scientific integrity (19-29) | 15 | ~300 |
| Core physics (panel, aerodb, tools) | 8 | ~40 |
| Agent & investigation | 12 | ~80 |
| Cognitive & hypothesis | 6 | ~40 |
| Dataset & splitting | 8 | ~50 |
| Knowledge & RAG | 5 | ~30 |
| Simulation & CFD | 5 | ~30 |
| Evidence & reconciliation | 5 | ~40 |
| Security & auth | 3 | ~20 |
| Model lifecycle & training | 6 | ~40 |
| Compute & hardware | 4 | ~30 |
| Commercial & compliance | 3 | ~30 |
| API contracts | 5 | ~30 |
| Benchmarks | 1 | ~4 |
| End-to-end | 5 | ~20 |
| Other | ~10 | ~60 |

---

## Test Quality Assessment

### Strengths
1. **Comprehensive coverage**: 946 tests across 102 files is substantial
2. **Adversarial testing**: `test_final_scientific_integrity.py` includes 15 adversarial test cases (forged logs, mutation attacks, replay protection)
3. **Scientific integrity checks**: Tests verify anti-fabrication rules, data leakage prevention, and epistemic classification
4. **API contract tests**: FastAPI TestClient-based integration tests for all major endpoints
5. **Phase-by-phase regression**: Each development phase has its own integrity test suite

### Concerns
1. **No trained model checkpoint**: All surrogate inference tests must use mock data or skip model loading — meaning the ML prediction path is never truly tested end-to-end
2. **No external solver tests**: OpenFOAM, SU2, and XFOIL are optional and likely not available on the test machine — simulation execution tests must mock solver availability
3. **No Ollama-dependent tests**: Chat agent tests likely mock the LLM; real agent behavior is untested
4. **R² calculation warnings**: Benchmark metrics code encounters edge cases with constant targets
5. **No performance benchmarks**: No test verifies response time, throughput, or resource usage
6. **No frontend tests**: TypeScript components have no unit or integration tests
7. **No load tests**: No concurrent request testing

### Missing Test Categories
- Frontend component tests (Jest/Testing Library)
- TypeScript type checking (should be in CI)
- API response time benchmarks
- Concurrent request safety
- File upload edge cases
- Authentication/authorization integration
- Database migration tests
- Memory leak detection
- Cross-browser compatibility

---

## Blockers and Dependencies

| Dependency | Available | Impact on Tests |
|---|---|---|
| Python 3.12 | ✅ | Full test suite runs |
| NumPy, SciPy, SymPy | ✅ | Physics computations work |
| scikit-learn | ✅ | Baseline comparisons (Ridge) |
| FastAPI/TestClient | ✅ | API tests pass |
| Ollama | ❌ Not running | Chat/agent tests likely mock this |
| OpenFOAM | ❌ Not on Windows | CFD execution tests mock this |
| SU2 | ❌ Not available | Simulation tests mock this |
| XFOIL | ❌ Not available | May not be tested |
| Trained checkpoint | ❌ Not in repo | Surrogate inference path untested |
| Node.js/npm | ✅ | Frontend build not tested by pytest |

---

## Recommendations

1. **HIGH: Train and save a checkpoint** — enables end-to-end surrogate testing
2. **HIGH: Add frontend type checking** to CI (`npx tsc --noEmit`)
3. **MEDIUM: Fix R² divide-by-zero warning** in `benchmark_models.py:69`
4. **MEDIUM: Add integration tests with live Ollama** (marked as optional/slow)
5. **LOW: Upgrade httpx** to resolve deprecation warnings
6. **LOW: Add pytest markers** for slow, integration, requires-solver test categories
