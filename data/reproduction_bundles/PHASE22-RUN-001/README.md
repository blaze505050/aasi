# AASI Phase 22 Cryptographic Reproduction Bundle: PHASE22-RUN-001
Generated: 2026-09-13T20:22:51.309157+00:00
Governing Rule: Absolute Anti-Fabrication Rule

## Contents
- environment_manifest.json: Host hardware, OS, solver detection.
- experiment_manifest.json: P22-E001 experiment definition and parameters.
- case/: Canonical OpenFOAM case deck dictionaries.
- mesh/: Mesh definition files.
- solver_logs/: Real solver text execution logs.
- residual_history/: Extracted residual and continuity drops.
- force_coefficients/: Extracted CL, CD, CM and stabilization stats.
- field_metadata/: Continuous surface Cp and spatial field statistics.
- dataset_record.json: Authenticated CFD observation added to training dataset.
- model_before/ & model_after/: Surrogate metadata before and after CFD retraining.
- evaluation_before.json & evaluation_after.json: Frozen test set evaluation results.
- provenance_dag.json: Merkle DAG linking inputs to scientific verdict.
- hashes.sha256: SHA-256 checksums of all bundled assets.
