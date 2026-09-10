# PhysicsNeMo Training Foundation & Physics-AI Model Registry

## Overview
AASI Phase 5 provides an enterprise-grade training and evaluation foundation for neural operators and physics surrogates. Built to respect developer workstation hardware constraints:
1. **Zero Mandatory Local CUDA/GPU:** Model registry, verification engines, and active learning algorithms execute entirely on the CPU with zero external GPU dependencies.
2. **Exportable Training Recipes:** Complete, standalone training scripts for Google Colab, AWS EC2, or institutional HPC GPU clusters are provided in `training/physicsnemo/`.
3. **Physical Monotonicity & Symmetry Audits:** Surrogates are rejected if they violate fundamental fluid mechanics principles.

---

## Supported Neural Operator Architectures

### 1. AeroGraphNet (Graph Neural Network)
- **Application:** Pressure distribution ($C_p$) and velocity fields over unstructured 2D/3D surface meshes.
- **Mesh Invariance:** Message passing between mesh nodes allows evaluation across varying boundary layer resolutions without grid re-interpolation.
- **Input Dimensions:** 3 node coordinates $(x, y, z)$, 1 surface normal $(\hat{n})$, 3 flow scalars $(M, Re, \alpha)$.
- **Output:** Surface pressure coefficient $C_p$, skin friction coefficient $C_f$, integrated lift $C_L$, and drag $C_D$.
- **Recipe:** `training/physicsnemo/aerographnet_recipe.py`.

### 2. 2D Fourier Neural Operator (FNO-2D)
- **Application:** Continuous full-field velocity $(u, v)$ and pressure $(p)$ field prediction.
- **Resolution Invariance:** Parameterizes the solution operator in Fourier space; can be evaluated at arbitrary grid resolution without retraining.
- **Input Channels:** 4 (coordinate grid $x, y$, signed distance field $\text{SDF}$, freestream velocity).
- **Output Channels:** 3 (Cartesian velocities $u, v$, static pressure $p$).
- **Recipe:** `training/physicsnemo/fno_airfoil_recipe.py`.

---

## `PhysicsModelRegistry` & Cryptographic Versioning
Every surrogate registered in AASI is cataloged with strict metadata:
- `model_name`: Canonical identifier (e.g. `AeroGraphNet-NACA0012-v1`, `FNO2D-Subsonic-Airfoil-v1`)
- `parameter_count`: Number of trainable parameters
- `validity_envelope`: Explicit bounds for Mach, Reynolds, and Angle of Attack
- `checksum`: Cryptographic SHA-256 hash of model weights
- **Silent Overwrite Prevention:** Attempting to register a model with an existing `model_id` without incrementing the version string raises an explicit error.

---

## Physical Validation & Monotonicity Gates
Traditional ML metrics (MSE, $R^2$) are insufficient for engineering surrogates. `PhysicsValidator` evaluates:
1. **Lift Curve Monotonicity ($dC_L / d\alpha > 0$):**
   In the linear pre-stall regime ($\alpha \in [-4^\circ, 10^\circ]$ for conventional airfoils), lift must increase monotonically with angle of attack:
   $$\frac{\partial C_L}{\partial \alpha} > 0$$
   Any negative lift slope in this regime triggers a physical failure flag.
2. **Symmetry Sanity for Symmetric Airfoils:**
   For a symmetric airfoil (such as NACA 0012) at zero angle of attack:
   $$|C_L(\alpha = 0^\circ)| \le 0.02$$
   Non-zero lift at $\alpha = 0^\circ$ indicates unphysical bias.
3. **Relative & Absolute Error Tolerances:**
   Evaluated against verified wind tunnel benchmarks (NASA TN-D-628, Abbott & von Doenhoff).

---

## Active Learning & Epistemic Uncertainty Sampling
To minimize the number of expensive CFD runs needed to train an accurate surrogate, `ActiveLearningEngine` implements iterative uncertainty sampling:
1. Sweeps parameter space over candidate $(M, Re, \alpha)$ grids.
2. Evaluates geometric distance to existing training data points.
3. **Physics-Informed Uncertainty Amplification:**
   Uncertainty scores are heavily weighted in physical transition zones:
   - High angle of attack ($\alpha \ge 12^\circ$): stall onset and massive separation.
   - Transonic speeds ($M \ge 0.70$): shock wave formation and boundary layer interaction.
4. Outputs ranked candidate points $(rank_1, rank_2, \dots)$ for targeted simulation case generation.
