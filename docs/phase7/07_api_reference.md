# 07 - Phase 7 REST API Reference

The following endpoints are mounted in `backend/main.py`:

## 1. Multi-Fidelity Endpoints

### `POST /api/multifidelity/resolve`
Resolves aerodynamic coefficients across the 5-tier fidelity cascade.
- **Request Body**: `MultiFidelityQuery` (`geometry`, `mach`, `reynolds`, `aoa_deg`, `quantity`)
- **Response**: `MultiFidelityResult` (value, uncertainty, resolution_tier, provenance, metadata)

### `GET /api/multifidelity/discrepancy`
Evaluates discrepancy between high and low fidelity predictions.
- **Query Params**: `high_val`, `low_val`, `quantity`
- **Response**: `DiscrepancyResult` (absolute_discrepancy, relative_discrepancy, bias_estimate)

### `GET /api/multifidelity/calibration`
Audits uncertainty calibration and empirical coverage against test data.
- **Query Params**: `quantity` (`CL`, `CD`, `CM`)
- **Response**: `UncertaintyCalibrationMetrics` (coverage_1sigma, coverage_2sigma, calibration_error)

### `GET /api/multifidelity/statistics`
Returns inventory count of registered datasets across all 5 tiers.

---

## 2. Active Learning Endpoints

### `POST /api/active-learning/candidates`
Generates optimal sampling points using prescribed acquisition strategies.
- **Request Body**: `ActiveLearningRequest` (`geometry`, `reynolds`, `n_candidates`, `strategy`)
- **Response**: List of candidate specifications with acquisition scores and estimated costs.

### `POST /api/active-learning/coverage-map`
Produces 2D parameter density projections and void identification.
- **Request Body**: `CoverageMapRequest` (`plane`, `n_bins_x`, `n_bins_y`)
- **Response**: 2D grid matrix with cell density, sample points, and coverage fraction.

---

## 3. Simulation & Quality Control Endpoints

### `POST /api/simulation/plan`
Generates a canonical `CFDJobSpec` for high-fidelity execution.
- **Request Body**: Flight condition and solver preferences.
- **Response**: Machine-readable `CFDJobSpec` JSON.

### `POST /api/simulation/quality-control`
Performs ASME V&V 20 residual and force stability checks on raw simulation output.
- **Request Body**: Simulation log text or force history.
- **Response**: `QCResult` with pass/fail verdict, max residual, and stability metrics.

---

## 4. Research Loop & Model Promotion Endpoints

### `GET /api/research/objectives`
Lists active aerodynamic research objectives and their status.

### `GET /api/research/datasets/versions`
Retrieves dataset version history (`AERO-AIRFOIL-V1.0`, `V2.0`, etc.).

### `POST /api/research/retrain`
Triggers fine-tuning or continuous retraining of surrogate models.
- **Request Body**: `RetrainRequest` (`dataset_version`, `epochs`, `learning_rate`)
- **Response**: `RetrainSummary` with loss progression and new model artifact paths.

### `GET /api/research/benchmarks/evaluate`
Runs evaluation against fixed NACA benchmark suite.
- **Response**: Benchmark comparison table and non-regression score.

### `POST /api/research/promote`
Executes 4-gate model promotion protocol.
- **Request Body**: `PromotionRequest` (`candidate_model_id`, `target_tier`)
- **Response**: Promotion decision report with status of all 4 gates.

### `GET /api/research/report/{objective_id}`
Compiles peer-review scientific report in Markdown or LaTeX.
- **Query Params**: `format` (`markdown` or `latex`)
- **Response**: Formatted document text ready for export.
