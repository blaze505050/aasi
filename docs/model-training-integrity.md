# AASI Model Training Integrity & Anti-Fabrication Principles

## Principles of Anti-Fabrication
In aerodynamic engineering and physics-informed AI, fabricated results, unverified checkpoints, and synthetic placeholders represent catastrophic safety hazards. AASI implements five foundational anti-fabrication mandates:

1. **Zero Synthetic Numbers**: Every prediction, metric, or coefficient displayed in AASI derives from an actual mathematical solver, a real trained neural surrogate, or verified experimental literature. Random number generation (`Math.random()`, `np.random.normal()`) is strictly prohibited for simulation or inference.
2. **Fail-Closed Availability**: When model checkpoints are missing, corrupt, or unverified, the system returns `MODEL_UNAVAILABLE` or `STATUS: UNINITIALIZED`. It never fabricates fallback numbers.
3. **Hardware-Governed Execution**: When system memory or storage is inadequate (< 15 GB reserve), the engine halts with `RESOURCE_LIMITED`. It never fakes completion.
4. **Epistemic Labeling**: Surrogates are explicitly tagged with domain validity and uncertainty flags (`SURROGATE — VERIFIED DOMAIN`, `SURROGATE — OOD WARNING`, `OUT OF DOMAIN`).
5. **Cryptographic Checksums**: Every trained model checkpoint is hashed using SHA-256 upon generation. Checkpoints with altered or missing hashes are quarantined and rejected.

---

## Capability Status Classification Matrix
| Feature | Classification | Implementation | Audit Test |
| :--- | :--- | :--- | :--- |
| **Deterministic Seed Fixing** | `REAL IMPLEMENTED` | Seeds torch, numpy, and random; enables deterministic cuDNN/CPU ops. | `test_deterministic_cpu_training_reproducibility` |
| **Checkpoint SHA-256 Hashing** | `REAL IMPLEMENTED` | Hashes serialized model weights; validates on reload. | `test_altered_checkpoint_fails_verification` |
| **Tamper-Evident Manifest** | `REAL IMPLEMENTED` | TrainingReproducibilityManifest signed with environment and data hashes. | `test_manifest_tampering_fails_verification` |
| **Promotion Gate Auditor** | `REAL IMPLEMENTED` | Physical law checks must pass before state transitions to `VERIFIED`. | `test_unearned_model_promotion_is_rejected` |
| **Distributed Multi-GPU Orchestration**| `RESOURCE LIMITED`| Slurm / PyTorch DDP scripts for cluster execution. | Scaffold in `backend/physics/adapters/` |

---

## Promotion Gate Lifecycle Verification
Before any model checkpoint is elevated to `VERIFIED` or `VERIFIED_PRODUCTION`, it must pass four non-negotiable physical checks:

```
                          ┌──────────────────────────┐
                          │   Trained Model State    │
                          │   (TRAINED_UNVERIFIED)   │
                          └────────────┬─────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│     Physical Law Gates        │             │    Statistical Error Gates    │
├───────────────────────────────┤             ├───────────────────────────────┤
│ 1. Non-Negative Drag (CD > 0) │             │ 1. Lift RMSE (CL) < 0.05      │
│ 2. Monotonic Lift (∂CL/∂α > 0)│             │ 2. Drag RMSE (CD) < 0.01      │
│ 3. Stagnation Cp (Cp ≤ 1.0)   │             │ 3. Test Set R² Score > 0.90   │
└───────────────┬───────────────┘             └───────────────┬───────────────┘
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       │
                         [All Gates Passed?]
                                       ├──► NO  ──► Status: TRAINED_UNVERIFIED (Promotion Blocked)
                                       └──► YES ──► Status: VERIFIED (Signed Checkpoint & Artifact)
```

If even a single check fails (e.g. negative drag detected at $\alpha = 0^\circ$), promotion is immediately blocked with an explanatory audit log.

---

## Audit Trail & Verification Evidence
AASI logs the complete training provenance in JSON format alongside the model checkpoint:
- Timestamp (ISO 8601 UTC)
- Git commit hash
- Python, PyTorch, NumPy, Scikit-learn versions
- Dataset ID and dataset content hash
- Random seed and hyperparameters
- Epoch-by-epoch loss trajectory
- Exact hardware device specifications
