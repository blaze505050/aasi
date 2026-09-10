# 05 - Continuous Retraining & 4-Gate Model Promotion

The continuous learning pipeline guarantees that newly trained surrogate models improve accuracy while strictly preserving physical consistency and avoiding regression on historical benchmarks.

## 1. Immutable Dataset Factory & Versioning

Datasets are versioned using semantic standards:
- **`AERO-AIRFOIL-V1.0`**: Baseline training corpus (3,024 authentic experimental records).
- **`AERO-AIRFOIL-V2.0`**: Augmented corpus incorporating verified CFD results generated from active learning loops.

Each dataset version contains:
- `records`: List of aerodynamic records with fidelity tags.
- `provenance_hash`: SHA-256 fingerprint computed from record signatures.
- `quality_score`: Composite metric evaluating residual convergence and experimental error bounds.

## 2. Model Retraining Pipeline

The retraining service fine-tunes existing weights or trains updated architectures:
1. Loads the target dataset version (`AERO-AIRFOIL-V2.0`).
2. Applies geometry-level leakage-free train/validation/test splits.
3. Optimizes physics-aware loss functions (MSE + drag positivity penalty + $C_{L,\alpha}$ linearity constraint).
4. Emits `AeroSurrogateV2` weights alongside full training history and validation metrics.

## 3. Standard Benchmark Suite

Before any model can be promoted, it is evaluated against a fixed benchmark test suite:
- **NACA 0012**: Symmetric benchmark ($M \in [0.1, 0.3]$, $\alpha \in [-4^\circ, 14^\circ]$).
- **NACA 2412**: Moderately cambered benchmark ($M = 0.15$, $\alpha \in [0^\circ, 12^\circ]$).
- **NACA 4412**: High-camber benchmark ($M = 0.15$, $\alpha \in [0^\circ, 10^\circ]$).

## 4. 4-Gate Promotion Protocol

A candidate model must pass four sequential gates before receiving the `ACTIVE` production badge:

```
[EXPERIMENTAL]
      │
      ▼ (Passes training loss convergence: MSE < 0.05)
[ BENCHMARK  ]
      │
      ▼ (Benchmark Non-Regression: MAE within 5% of incumbent on standard suite)
[ VALIDATED  ]
      │
      ▼ (Physics Positivity: CD > 0 across 100% of test points; GCI compatible)
[   ACTIVE   ] ──▶ Replaces previous incumbent in production routing
```

1. **Gate 1: Loss Convergence**
   - Training and validation loss must plateau with no divergence: $\mathcal{L}_{\text{val}} \le 0.05$.
2. **Gate 2: Benchmark Non-Regression**
   - Candidate model mean absolute error on benchmark airfoils must not degrade by more than $5\%$ relative to the active model.
3. **Gate 3: Physical Conservation & Positivity**
   - Total drag coefficient $C_D$ must be positive for all test cases ($C_D > 0$).
   - Lift slope $dC_L/d\alpha > 0$ across the linear regime ($\alpha \in [-4^\circ, 8^\circ]$).
4. **Gate 4: ASME V&V 20 Compatibility**
   - Model epistemic uncertainty bands must encompass the ASME V&V 20 numerical uncertainty intervals calculated from fine grid convergence studies.
