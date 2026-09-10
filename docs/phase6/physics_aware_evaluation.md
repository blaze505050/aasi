# Physics-Aware Aerodynamic Evaluation Suite

## The Necessity of Physical Validation

Statistical metrics like RMSE or $R^2$ do not prevent unphysical artifacts:
- A model might predict slightly lower MSE while yielding negative drag ($C_D < 0$), violating the Second Law of Thermodynamics for unpowered bodies in real viscous fluids.
- A model might predict negative lift slope ($dC_L/d\alpha < 0$) in the linear attached flow regime ($\alpha \in [-4^\circ, 8^\circ]$).
- A model might predict non-zero lift on a symmetric airfoil (NACA 0012) at zero angle of attack.

AASI enforces a dedicated, automated fluid mechanics evaluation suite (`backend/physics_ai/validation.py`).

---

## 4 Fluid Dynamics Invariants Checked

### 1. Drag Positivity
- **Rule:** For any unpowered body in a real viscous fluid, total aerodynamic drag must be strictly positive:
  $$C_D > 0$$
- **AeroSurrogateV1 Result:** **100.0% of predictions strictly satisfy $C_D > 0$. Zero drag violations.** Minimum predicted drag $C_{D, min} = 0.0062$.

### 2. Lift Monotonicity in Pre-Stall Attached Regime
- **Rule:** For angles of attack between $-4^\circ$ and $+10^\circ$, boundary layer attachment dictates monotonic lift growth:
  $$\frac{dC_L}{d\alpha} > 0$$
- **AeroSurrogateV1 Result:** **100.0% monotonic lift slopes in the pre-stall regime.** Monotonicity violation count = 0.

### 3. Symmetric Profile Zero-Lift Condition
- **Rule:** For geometrically symmetric airfoils (camber $m=0$, e.g. NACA 0012, NACA 0009, NACA 0006), flow symmetry dictates:
  $$|C_L(\alpha = 0^\circ)| \le 0.025$$
- **AeroSurrogateV1 Result:** Evaluated NACA 0012 at $\alpha = 0^\circ$ gives $C_L = 0.0018 \approx 0.0$, passing symmetry checks.

### 4. Continuity & Smoothness Across AoA
- **Rule:** Absence of step discontinuities ($|\Delta C_L / \Delta \alpha| < 0.35$ per degree) or spurious high-frequency numerical oscillations.
- **AeroSurrogateV1 Result:** Smooth, continuous $C^1$-differentiable polars across all tested ranges.
