# Training Recipe & Optimization Details

## Training Configuration (`TR-AERO-SURROGATE-V1-001`)

- **Dataset:** `DATASET-AUTHENTIC-AIRFOILS-V1` (1,008 authentic samples, 7 airfoils)
- **Split Policy:** Geometry-level holdout (Train: 432 samples, Val: 144 samples, Test: 180 samples, OOD: 90 samples)
- **Random Seed:** `42` (strictly enforced across random, numpy, and initialization)
- **Epochs:** `150`
- **Batch Size:** `32`
- **Initial Learning Rate:** `0.003`
- **Learning Rate Schedule:** Cosine Annealing decay down to `1e-4`
  $$\eta_t = \eta_{min} + \frac{1}{2}(\eta_{max} - \eta_{min})\left(1 + \cos\left(\frac{t}{T}\pi\right)\right)$$
- **Optimizer:** Decoupled Weight Decay AdamW ($\beta_1 = 0.9$, $\beta_2 = 0.999$, $\epsilon = 10^{-8}$, $\lambda = 10^{-4}$)
- **Loss Function:** Weighted multi-target MSE
  $$\mathcal{L} = 1.0 \times \text{MSE}(C_L) + 5.0 \times \text{MSE}(C_D) + 2.0 \times \text{MSE}(C_M)$$
- **Hardware:** Local Windows CPU (single thread / vectorized NumPy)
- **Total Training Time:** `1.85 seconds`
- **Checkpoints Generated:**
  - `data/training_runs/TR-AERO-SURROGATE-V1-001/checkpoints/aero_surrogate_v1.npz`
  - `data/checkpoints/aero_surrogate_v1.npz`
  - SHA-256 Checksum: `bc549596f676c5d336fe33333845c53c6d2c170bce2eb964516c51dc8f4ee433`

---

## Convergence Trajectory

- **Epoch 1:** Train Loss = 1.9641, Val Loss = 1.1289
- **Epoch 10:** Train Loss = 0.0198, Val Loss = 0.0181
- **Epoch 50:** Train Loss = 0.0035, Val Loss = 0.0047
- **Epoch 100:** Train Loss = 0.0006, Val Loss = 0.0019
- **Epoch 150:** Train Loss = 0.0004, Val Loss = 0.0018 (Stable, no divergence or overfitting).
