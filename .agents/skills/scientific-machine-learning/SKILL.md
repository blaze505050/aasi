---
name: scientific-machine-learning
description: Scientific Machine Learning (SciML): Physics-Informed Neural Networks (PINNs), Fourier Neural Operators (FNOs), deep surrogate modeling, active learning, and epistemic uncertainty quantification.
---

# Scientific Machine Learning (SciML) Skill

## 1. Physics-Informed Neural Networks (PINNs)
- **Loss Formulation**:
  $$\mathcal{L}(\theta) = w_{data}\mathcal{L}_{data} + w_{pde}\mathcal{L}_{pde} + w_{bc}\mathcal{L}_{bc}$$
- **Automatic Differentiation**: Compute exact differential operators $\nabla u, \nabla^2 u$ using backpropagation graphs without mesh discretization error.
- **Navier-Stokes Residuals**:
  $$R_u = u\frac{\partial u}{\partial x} + v\frac{\partial u}{\partial y} + \frac{1}{\rho}\frac{\partial p}{\partial x} - \nu \nabla^2 u = 0$$
  $$R_v = u\frac{\partial v}{\partial x} + v\frac{\partial v}{\partial y} + \frac{1}{\rho}\frac{\partial p}{\partial y} - \nu \nabla^2 v = 0$$
  $$R_{mass} = \frac{\partial u}{\partial x} + \frac{\partial v}{\partial y} = 0$$

## 2. Neural Operators (FNO, DeepONet, Transolver)
- **Mesh-Independent Operators**: Map input geometry functions / boundary conditions to continuous field distributions ($u(x, y), p(x, y)$).
- **Fourier Neural Operator (FNO)**: Parameterizes integral kernel in Fourier frequency space using FFT / iFFT spectral convolutions.
- **Inference Time**: $< 50\text{ ms}$ on modern hardware compared to hours for 3D RANS.

## 3. Epistemic Uncertainty & Out-Of-Domain (OOD) Protection
- **Ensemble Variance / Deep Gaussian Processes**: Quantify epistemic uncertainty $\sigma_{epistemic}^2$ from model disagreement.
- **Convex Hull & Mahalanobis Distance**: Track training distribution distance in $(\alpha, Re, M, t/c)$ space.
- **Automatic Fallback Protocol**: When query distance exceeds $D_{threshold}$ or $\sigma > \sigma_{max}$, refuse raw surrogate prediction and escalate to high-fidelity solver case staging.

