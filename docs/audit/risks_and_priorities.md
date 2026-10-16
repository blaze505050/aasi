# AASI Risks & Priorities — Phase A Audit

**Date:** 2026-10-16
**Commit:** `5b0a5da`
**Method:** Risk assessment from repository audit, test baseline, and architecture review

---

## Risk Classification

| Severity | Definition |
|---|---|
| 🔴 **CRITICAL** | Blocks scientific credibility, correctness, or security |
| 🟠 **HIGH** | Significantly impacts usability, reliability, or commercial viability |
| 🟡 **MEDIUM** | Reduces quality or developer velocity |
| 🟢 **LOW** | Cosmetic, non-blocking, or improvement opportunity |

---

## Risks Ordered by Priority

### 🔴 CRITICAL — Must Fix Before Any Release

#### R1: [RESOLVED] Trained Surrogate Checkpoint Availability
- **Status:** ✅ VERIFIED & RESOLVED
- **Resolution:** `data/checkpoints/aero_surrogate_v1.npz` (79,344 bytes) is present in the repository, cryptographically verified with SHA-256 (`bc549596...`), and passes all 7 lifecycle and model verification tests in `test_model_lifecycle_milestone_d.py`.
- **Phase:** B (Verified)

#### R2: Authentication Not Enforced on Routes
- **Impact:** All API endpoints are publicly accessible without authentication. Any user can generate databases, run simulations, access investigation data, and invoke compute-heavy operations.
- **Root Cause:** `main.py` route handlers lack auth dependency injection despite `SecurityManager` existing
- **Mitigation:** Add FastAPI `Depends()` with auth middleware to sensitive routes. Separate public (health, docs) from protected (compute, data) endpoints.
- **Effort:** 4-8 hours
- **Phase:** F

#### R3: Monolithic `main.py` (3,040 lines) with Duplicated Routes
- **Impact:** Routes are defined in both `main.py` AND `api/routes_*.py`, creating:
  - Maintenance burden (changes in one place may not be reflected in the other)
  - Import time overhead
  - Risk of inconsistent behavior
- **Mitigation:** Consolidate all routes into `api/routes_*.py` modules. Reduce `main.py` to FastAPI app creation, middleware, and router registration.
- **Effort:** 4-6 hours (careful migration)
- **Phase:** B

#### R4: [RESOLVED] R² Divide-by-Zero in Benchmark Metrics
- **Status:** ✅ RESOLVED
- **Resolution:** Fixed in `backend/physics_ai/benchmark_models.py:68-71` by using safe boolean masking (`valid_mask = ss_tot > 1e-9`) before division, eliminating `RuntimeWarning: divide by zero`.
- **Phase:** B (Resolved)

---

### 🟠 HIGH — Should Fix Before Commercial Use

#### R5: [RESOLVED] AeroDB Persistence Across Server Restarts
- **Status:** ✅ RESOLVED
- **Resolution:** Implemented `backend/storage/aerodb_store.py` (`AeroDatabaseStore`) using SQLite ACID storage (`data/aasi_aerodb.db`). `AerodynamicDatabaseEngine.generate_aero_db()` automatically writes each sweep to disk; `get_aero_db()` and `list_aero_dbs()` seamlessly query SQLite on cache misses. Verified with integration tests.
- **Phase:** B/E (Resolved)

#### R6: No CORS Restrictions for Development
- **Impact:** CORS allows `http://localhost:3000` which is appropriate for dev but the production CORS is configured via env vars. Docker-compose uses a default secret key.
- **Mitigation:** Ensure production deployment enforces strict CORS and unique secret keys.
- **Effort:** 1-2 hours
- **Phase:** F

#### R7: [RESOLVED] Default Secret Key in Docker Compose
- **Status:** ✅ RESOLVED
- **Resolution:** Replaced fallback in `docker-compose.yml` with fail-closed expression `${AASI_SECRET_KEY:?Error: AASI_SECRET_KEY must be set in environment}`.
- **Phase:** F (Resolved)

#### R8: JSON State Files Without Concurrency Protection
- **Impact:** `epistemic_memory.json` (253 KB), `merkle_lineage.json` (462 KB), and other state files are read/written without file locking. Concurrent requests could corrupt data.
- **Mitigation:** Use SQLite for all persistent state, or implement file locking.
- **Effort:** 4-8 hours
- **Phase:** F

#### R9: No Frontend Tests
- **Impact:** 33 React components (total ~500 KB of TSX) have zero automated tests.
- **Mitigation:** Add Jest + React Testing Library for critical components. Start with `AeroDbPanel`, `InvestigationWorkspace`, `InteractivePolarPlot`.
- **Effort:** 8-16 hours
- **Phase:** G

#### R10: CI Workflow Depends on Missing CLI
- **Impact:** GitHub Actions workflow calls `aasi cert verify` and `aasi audit verify` commands that depend on `sdk/python` package which may not be properly installed.
- **Mitigation:** Verify SDK installation in CI. Add `pip install -e sdk/python` step or use `pytest` directly.
- **Effort:** 2-4 hours
- **Phase:** G

---

### 🟡 MEDIUM — Should Address During Development

#### R11: Panel Solver Post-Stall Model Unvalidated
- **Impact:** Empirical stall tapering (`exp(-0.15 * excess)`) and separation drag penalty are heuristic approximations without validation against wind tunnel data.
- **Mitigation:** Add comparison test cases against NACA TN series data for NACA 0012 and Clark-Y in stall regime. Document validity limits.
- **Effort:** 4-8 hours
- **Phase:** C

#### R12: PhysicsNeMo Directory Contains Only README
- **Impact:** `training/physicsnemo/README.md` exists but no training recipes, models, or configurations.
- **Mitigation:** Either populate with actual PhysicsNeMo content or remove directory and update documentation.
- **Effort:** 1 hour (cleanup) or 20+ hours (implementation)
- **Phase:** E

#### R13: Three.js Dependency for 3D Visualization
- **Impact:** `three` (0.186.1) adds significant bundle size for a feature that may not be critical for the core airfoil analysis workflow.
- **Mitigation:** Consider lazy-loading the 3D component. Ensure it doesn't block the core UX.
- **Effort:** 2-4 hours
- **Phase:** E

#### R14: Subprocess Execution Security
- **Impact:** `simulation/executor.py` executes OpenFOAM via `subprocess.run`. While the code uses argument lists (not shell strings), the input validation and sandboxing need deeper review.
- **Mitigation:** Review subprocess invocations for injection risks. Ensure per-job isolation, cleanup, and resource limits.
- **Effort:** 4-8 hours
- **Phase:** F

#### R15: No Database Migration Strategy
- **Impact:** SQLite databases in `data/` have no schema versioning or migration mechanism. Schema changes could break existing data.
- **Mitigation:** Add Alembic or manual schema versioning for SQLite databases.
- **Effort:** 4-8 hours
- **Phase:** F

#### R16: [RESOLVED] Redis Dependency Synchronization
- **Status:** ✅ RESOLVED
- **Resolution:** Added `redis>=5.0.0,<6.0.0` to `backend/requirements.txt` to synchronize with Docker Compose stack.
- **Phase:** B (Resolved)

---

### 🟢 LOW — Improvement Opportunities

#### R17: Deprecation Warnings in Test Infrastructure
- **Impact:** `httpx` deprecation warnings from Starlette test client.
- **Mitigation:** Upgrade to `httpx2` or pin compatible versions.
- **Effort:** 30 minutes

#### R18: [RESOLVED] Binary Document in Root
- **Status:** ✅ RESOLVED
- **Resolution:** Identified `Document (1).docx` as the Phase 21 Master Engineering Directive and organized it under `docs/directives/phase-21-master-engineering-directive.docx`, leaving repository root clean.
- **Phase:** B (Resolved)

#### R19: Large Component Files
- **Impact:** `InvestigationWorkspace.tsx` (84 KB), `ModelZooExplorer.tsx` (44 KB) are very large single components.
- **Mitigation:** Decompose into smaller sub-components for maintainability.
- **Effort:** 8-16 hours per component

#### R20: Model Zoo File Size
- **Impact:** `cognitive/model_zoo.py` is 84 KB — likely contains hardcoded model configurations that should be data files.
- **Mitigation:** Extract configurations to JSON/YAML files.
- **Effort:** 4-8 hours

---

## Priority Matrix

| Phase | Risk IDs | Focus |
|---|---|---|
| **B: Correctness & Security Fixes** | R1, R3, R4, R16 | Fix critical code issues |
| **C: Surrogate Evaluation** | R1, R11 | Train model, validate panel solver |
| **D: Airfoil Workflow** | R5 | Complete end-to-end workflow |
| **E: Visualization & Reports** | R12, R13, R19 | Polish and persistence |
| **F: Hardening** | R2, R6, R7, R8, R14, R15 | Security and reliability |
| **G: CI & Documentation** | R9, R10 | Quality gates |
| **H: Commercial Readiness** | All remaining | Full assessment |

---

## Immediate Action Items (Phase B)

1. **Train AeroSurrogateV1** with existing authentic airfoil data → save checkpoint
2. **Fix R² divide-by-zero** in `benchmark_models.py:69`
3. **Begin main.py decomposition** — move inline route handlers to `api/routes_*.py`
4. **Verify Redis dependency** — confirm Docker-only or add to requirements
5. **Create recovery point** — `git tag audit-baseline-v1`
6. **Run frontend type check** — `cd frontend && npx tsc --noEmit`
