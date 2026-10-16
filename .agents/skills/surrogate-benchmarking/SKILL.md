---
name: surrogate-benchmarking
description: Benchmarking procedures for AeroSurrogateV1 including baseline comparisons, per-coefficient metrics, and OOD evaluation. Use when training, evaluating, or comparing surrogate models.
---

# Surrogate Benchmarking Skill

## Purpose
Defines the standard evaluation protocol for AeroSurrogateV1 and future surrogate models.

## Mandatory Metrics (Report Separately for CL, CD, CM)

| Metric | Formula | Purpose |
|---|---|---|
| **MAE** | mean(|y_pred - y_true|) | Absolute prediction error |
| **RMSE** | sqrt(mean((y_pred - y_true)²)) | Error with outlier sensitivity |
| **Bias** | mean(y_pred - y_true) | Systematic over/under-prediction |
| **Max Error** | max(|y_pred - y_true|) | Worst-case scenario |
| **R²** | 1 - SS_res/SS_tot | Variance explained (guard div-by-zero) |

## Baseline Models (Always Compare)

1. **Constant Mean Predictor**: Predicts training set mean — the trivial baseline
2. **Ridge Regression**: Linear model on geometry + condition features
3. **Panel Solver (Deterministic)**: The physics-based deterministic alternative

## Evaluation Partitions

| Partition | Purpose | Method |
|---|---|---|
| Training Set | Learning (not for final metrics) | GeometryLevelSplitter |
| Validation Set | Hyperparameter tuning only | GeometryLevelSplitter |
| Test Set (In-Domain) | Final metrics | Unseen geometries, similar conditions |
| OOD Geometry | Generalization to new profiles | Entirely new airfoil families |
| OOD Condition | Extrapolation to new conditions | High-AoA (>12°) or high-Mach (>0.3) |
| OOD Combined | Hardest evaluation | New geometry at extreme conditions |

## Critical Rules

- **NEVER use a single aggregate score** — always report per-coefficient metrics
- **NEVER use validation set for final evaluation** — that's the test set
- **CD prediction is typically the hardest** — drag is an order of magnitude smaller than lift
- **R² on CD can be misleading** — small variance makes R² unstable; use MAE instead
- **Always report sample counts** — N_train, N_test, N_ood
- **Report runtime** — inference time per point and total evaluation time

## Benchmark Command

```bash
python -m pytest tests/benchmarks/ -v --tb=short
python -c "from backend.physics_ai.training import SurrogateTrainer; SurrogateTrainer().run()"
```

## Result Format

Save machine-readable results to `data/training_runs/TR-<id>/metrics.json`:
```json
{
  "model_id": "AERO_SURROGATE_V1",
  "model_version": "1.0.0",
  "timestamp": "2026-10-16T22:00:00Z",
  "weights_checksum": "sha256:...",
  "dataset_version": "...",
  "split_seed": 42,
  "metrics": {
    "test_in_domain": { "cl_mae": ..., "cd_mae": ..., "cm_mae": ..., ... },
    "test_ood_geometry": { ... },
    "test_ood_condition": { ... }
  },
  "baselines": {
    "constant_mean": { ... },
    "ridge_regression": { ... }
  }
}
```
