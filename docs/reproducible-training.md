# AASI Reproducible Training Protocol & The Seven Reproducibility Questions

## The Seven Reproducibility Questions
To guarantee complete scientific provenance and auditability, AASI requires that any trained model can answer the following seven questions deterministically from its signed `TrainingReproducibilityManifest`:

### Question 1: What exact dataset version, commit, and split was used?
- **Answer**: The exact dataset identifier (e.g. `DATASET-AIRFRANS-1K`), dataset content SHA-256 hash, and geometry-level split partition seed (e.g. `split_seed: 42`, 80/10/10 geometry separation). Recorded in `dataset_provenance` of the manifest.

### Question 2: What were the exact normalizer parameters, and were they fit only on the training set?
- **Answer**: Normalizer mean vector ($\mu$) and standard deviation scale vector ($\sigma$) are stored directly in the manifest. The normalizer is strictly fitted on the training split using `fit_transform()`. Evaluation geometries are transformed using `transform()` with frozen statistics. Verified by `test_normalizer_isolated_to_training_set`.

### Question 3: What was the random seed, and does re-running with that seed produce bit-identical or statistically indistinguishable weights?
- **Answer**: Random seed is recorded (e.g. `seed: 42`), governing `torch.manual_seed()`, `np.random.seed()`, and `random.seed()`. Re-running on identical CPU architecture produces identical weight tensors and identical checkpoint SHA-256 hashes (`test_deterministic_cpu_training_reproducibility`).

### Question 4: What are the hardware and software environments (OS, Python, PyTorch, CUDA, GPU model, driver version)?
- **Answer**: Recorded dynamically in `environment` block of manifest: OS (`Windows 11` / `Linux`), Python version (`3.11.x`), PyTorch version (`2.2.x`), CUDA runtime version / device type (`Local CPU` / `NVIDIA A100`), NumPy, and Scikit-learn versions.

### Question 5: What is the model checkpoint SHA-256 hash, and does it match the hash computed at training completion?
- **Answer**: At the end of training, the model weights file (`.pt` or serialized artifact) is hashed using SHA-256 and stored in `model_checkpoint_sha256`. At load time, AASI recomputes the SHA-256 hash; if any byte differs, `ModelChecksumMismatchError` is raised and the model is quarantined (`test_altered_checkpoint_fails_verification`).

### Question 6: What physical constraints were verified, on what test set, and what were the exact numerical margins?
- **Answer**: The manifest records the `physics_verification_report` containing:
  - Drag non-negativity margin: $\min(C_D) > 0.0001$
  - Lift slope monotonicity: $\min(\partial C_L / \partial \alpha) > 0$
  - Stagnation pressure bound: $\max(C_p) \le 1.02$
  - Statistical error bounds: $C_L \text{ RMSE} \le 0.05, C_D \text{ RMSE} \le 0.01$

### Question 7: What are the model's known failure modes, out-of-domain boundaries, and recommended epistemic label?
- **Answer**: Explicitly defined in `operational_envelope` and `known_failure_modes`:
  - Mach bounds: $[0.1, 0.6]$ (incompressible/subsonic regime; transonic shocks not modeled)
  - Reynolds bounds: $[2.0 \times 10^5, 2.0 \times 10^6]$
  - Angle of attack bounds: $[-6.0^\circ, 12.0^\circ]$ (linear attached regime; post-stall unseparated)
  - Default epistemic label: `SURROGATE — VERIFIED DOMAIN` inside envelope; `OUT OF DOMAIN` outside envelope.

---

## Capability Status Classification Matrix
| Reproducibility Component | Classification | Implementation | Audit Test |
| :--- | :--- | :--- | :--- |
| **Reproducibility Manifest Generator** | `REAL IMPLEMENTED` | Captures environment, data hashes, normalizer parameters, metrics. | `test_training_reproducibility_manifest_captures_all_fields` |
| **Tamper-Detection Auditor** | `REAL IMPLEMENTED` | Hashes manifest payload; detects any modification or post-hoc editing. | `test_manifest_tampering_fails_verification` |
| **Hardware Governance Pre-Flight** | `REAL IMPLEMENTED` | Enforces 15 GB disk space reserve and RAM safety limits. | `test_hardware_governance_blocks_low_disk` |
| **Seven Questions REST Endpoint** | `REAL IMPLEMENTED` | `GET /api/models/reproducibility/{run_id}` delivers JSON answers. | Active (`backend/main.py`) |

---

## Hardware Pre-Flight Verification Rule
```python
if free_disk_gb < 15.0:
    return ResourceCheckResult(
        can_proceed=False,
        status="RESOURCE_LIMITED",
        reason=f"Insufficient free disk space: {free_disk_gb:.1f} GB available, 15.0 GB required."
    )
```
This fails closed before any large dataset or checkpoint is written to disk.
