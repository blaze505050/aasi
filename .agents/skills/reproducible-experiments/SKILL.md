---
name: reproducible-experiments
description: Ensures all AASI scientific experiments are reproducible with recorded seeds, configs, checksums, and environment snapshots. Use when running training, benchmarks, or validation campaigns.
---

# Reproducible Experiments Skill

## Purpose
Every AASI experiment must be independently reproducible by a different person on a different machine.

## Required Recording for Every Experiment

| Element | How to Record | Storage |
|---|---|---|
| **Dataset version** | SHA-256 of dataset files | `metrics.json` |
| **Geometry split IDs** | List of geometry names per partition | `split_manifest.json` |
| **Code revision** | `git rev-parse HEAD` | `metrics.json` |
| **Configuration** | Full hyperparameter dict | `config.json` |
| **Random seeds** | All seeds (NumPy, Python random) | `config.json` |
| **Dependency versions** | `pip freeze` output | `environment.txt` |
| **Model version** | Model ID + version string | `metrics.json` |
| **Weight checksum** | SHA-256 of saved weights | `metrics.json` |
| **Hardware** | CPU model, RAM, GPU (if any) | `environment.json` |
| **Metrics** | Per-coefficient, per-partition | `metrics.json` |
| **Artifacts** | Loss curves, prediction plots | `artifacts/` |

## Experiment Directory Structure

```
data/training_runs/TR-<MODEL>-<VERSION>-<SEQ>/
├── config.json           # Full training configuration
├── metrics.json          # All evaluation metrics
├── split_manifest.json   # Geometry assignments per partition
├── environment.json      # Hardware and software versions
├── environment.txt       # pip freeze output
├── checkpoints/
│   └── model.npz         # Saved model weights
├── artifacts/
│   ├── loss_curve.json   # Training loss history
│   └── predictions.json  # Test set predictions
└── README.md             # Human-readable experiment summary
```

## Verification Procedure

To reproduce an experiment:
1. Check out the recorded git revision
2. Install the recorded dependency versions
3. Load the recorded dataset with the same split seed
4. Run training with the recorded configuration
5. Compare output metrics — they should match within floating-point tolerance

## Critical Rules

- Never fabricate metrics to make a release look successful
- Never report metrics on the validation set as "test" metrics
- Never omit per-coefficient breakdowns
- Always include baseline comparisons
- Record even failed experiments (they inform future work)
