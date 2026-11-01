---
name: computational-fluid-dynamics
description: CFD workflow automation, structured/unstructured meshing (y+ wall spacing, boundary layer inflation), OpenFOAM/SU2 solver setup, turbulence modeling (Spalart-Allmaras, k-omega SST), residual convergence monitoring, and force integration.
---

# Computational Fluid Dynamics (CFD) Skill

## 1. Grid Generation & Near-Wall Resolution
- **First Cell Height ($y^+$ calculation)**:
  - Friction velocity: $u_\tau = \sqrt{\tau_w / \rho}$, where $\tau_w = \frac{1}{2}\rho U_\infty^2 C_f$.
  - Schlichting skin friction estimate: $C_f \approx (2\log_{10}(Re) - 0.65)^{-2.3}$.
  - Target first cell distance: $\Delta y = \frac{y^+ \mu}{\rho u_\tau}$.
  - Guidelines: $y^+ \le 1.0$ for low-Reynolds RANS (resolving viscous sublayer without wall functions); $30 \le y^+ \le 300$ for standard wall functions.
- **Inflation Layer Growth**:
  - Growth ratio $r \le 1.15$–$1.20$ to maintain low numerical truncation error.
  - Number of layers: sufficiently large to cover boundary layer thickness $\delta(x) \approx 0.37 x / Re_x^{0.2}$.

## 2. Solver Physics & Boundary Conditions
- **Governing Equations**: Incompressible / Compressible Reynolds-Averaged Navier-Stokes (RANS).
- **Turbulence Closures**:
  - **Spalart-Allmaras (SA)**: 1-equation model, highly robust for external attached aerodynamic flows.
  - **Menter SST $k$-$\omega$**: 2-equation blending $k$-$\omega$ in boundary layer and $k$-$\epsilon$ in freestream. Standard for adverse pressure gradients and separation onset.
- **Convergence Criteria**:
  - Normalized residuals ($p, U, k, \omega, \tilde{\nu}$) drop below $10^{-5}$ or exhibit asymptotic flatness over $\ge 500$ iterations.
  - Integral aerodynamic forces ($C_L, C_D$) oscillate within $\pm 0.0001$ over 200 consecutive iterations.

## 3. Solver Adapters & Case Directory Structure
- **OpenFOAM**: `0/` (field initializations: `U`, `p`, `nut`, `k`, `omega`), `constant/` (`transportProperties`, `turbulenceProperties`, `polyMesh/`), `system/` (`controlDict`, `fvSchemes`, `fvSolution`).
- **SU2**: `case.cfg` declarative configuration file, `.su2` mesh format, `history.csv` residual output parsing.

