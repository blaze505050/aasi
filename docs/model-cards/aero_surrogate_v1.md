# Model Card: AeroSurrogateV1

## Model Details

- **Model Name:** `AeroSurrogateV1`
- **Model Version:** `1.0.0`
- **Model Family:** Lightweight Neural Operator / Aerodynamic Surrogate
- **Date of Release:** September 2026
- **License:** MIT Open Source
- **Developers:** AASI Engineering Core Team
- **Framework:** Pure CPU Vectorized NumPy Neural Operator (Zero external C++ DLL dependencies)
- **Parameters:** 13,763 trainable weights
- **Cryptographic Checksum (SHA-256):** `bc549596f676c5d336fe33333845c53c6d2c170bce2eb964516c51dc8f4ee433`

---

## Intended Use

- **Primary Intended Use:** Rapid aerodynamic coefficient estimation ($C_L, C_D, C_M$) for 2D subsonic airfoils in conceptual aircraft design, interactive trade studies, and flight envelope exploration.
- **Out-of-Scope Uses:**
  - Transonic / supersonic shock wave modeling ($M > 0.40$).
  - Post-stall deep separation hysteresis ($|\alpha| > 18^\circ$).
  - 3D finite wing induced drag or aeroelastic flutter calculations.
  - Life-critical flight certification without full CFD / flight test verification.

---

## Operational Validity Envelope

| Parameter | Calibrated In-Domain Range | Near-Boundary Flag | Out-of-Domain (Rejected) |
| :--- | :--- | :--- | :--- |
| **Mach Number ($M$)** | $0.05 \le M \le 0.35$ | $0.35 < M \le 0.40$ | $M > 0.40$ |
| **Reynolds Number ($Re$)** | $5.0 \times 10^5 \le Re \le 5.0 \times 10^6$ | $5.0 \times 10^6 < Re \le 6.0 \times 10^6$ | $Re < 5\times 10^5$ or $Re > 6\times 10^6$ |
| **Angle of Attack ($\alpha$)** | $-6.0^\circ \le \alpha \le 12.0^\circ$ | $12.0^\circ < |\alpha| \le 18.0^\circ$ | $|\alpha| > 18.0^\circ$ |

---

## Training Data & Zero-Leakage Split

- **Dataset:** `DATASET-AUTHENTIC-AIRFOILS-V1` (1,008 authentic samples)
- **Training Geometries:** `clark_y`, `naca0009`, `naca4412` (432 samples)
- **Validation Geometries:** `naca0006` (144 samples)
- **Test Geometries:** `naca0012`, `naca2412` (180 samples, completely held out)
- **OOD Geometries:** `rae2822` (90 samples)
- **Geometry Leakage:** **0.0% (Strict Isolation)**

---

## Performance & Metrics

- **Test Set Lift ($C_L$) RMSE:** `0.1349` ($R^2 = 0.9495$)
- **Test Set Drag ($C_D$) RMSE:** `0.00134` ($R^2 = 0.9250$)
- **Validation Set Lift ($C_L$) RMSE:** `0.0231` ($R^2 = 0.9987$)
- **Validation Set Drag ($C_D$) RMSE:** `0.00142` ($R^2 = 0.9994$)
- **Inference Latency:** `0.45 ms / evaluation` on single CPU core.

---

## Physical Validation Invariants

- **Drag Positivity ($C_D > 0$):** **100% Satisfied. 0 Violations.**
- **Lift Slope Monotonicity ($dC_L/d\alpha > 0$):** **100% Satisfied in pre-stall range.**
- **Zero-Lift Symmetry ($|C_L(0)| \le 0.025$ on symmetric profiles):** **Satisfied ($C_L(0) = 0.0018$).**
- **Discontinuities / Oscillations:** **0 Detected.**

---

## Checkpoint Artifacts

- Weight Archive: `data/checkpoints/aero_surrogate_v1.npz`
- Manifest Sidecar: `data/checkpoints/aero_surrogate_v1.manifest.json`
- Full Training Run Directory: `data/training_runs/TR-AERO-SURROGATE-V1-001/`
