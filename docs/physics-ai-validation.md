# AASI Physics-AI Physical Constraint Verification & Validation

## Foundational Physical Invariants
A model that achieves zero loss on training data but violates fundamental physical conservation laws is aerodynamically invalid and must be rejected prior to deployment. AASI implements four automated physical verification gates:

1. **Non-Negative Drag**: The total aerodynamic drag coefficient must remain strictly positive for any viscous flow past an unpowered body ($C_D > 0$). Negative drag implies an unphysical thrust-generating airfoil violating the second law of thermodynamics.
2. **Monotonic Lift Slope**: For subsonic attached flow below the stall angle ($\alpha < \alpha_{stall}$), the sectional lift curve slope must be strictly positive:
   $$\frac{\partial C_L}{\partial \alpha} > 0$$
3. **Stagnation Pressure Coefficient Bound**: In steady subsonic flow, the maximum surface pressure coefficient cannot exceed the total pressure recovery factor:
   $$C_p \le 1.0 \quad \left(\text{compressible: } C_{p,max} = \frac{2}{\gamma M_\infty^2}\left[\left(1 + \frac{\gamma-1}{2}M_\infty^2\right)^{\frac{\gamma}{\gamma-1}} - 1\right]\right)$$
   A surface pressure coefficient $C_p > 1.05$ indicates numerical divergence or unphysical energy creation.
4. **Boundary-Layer Asymptotics**: Wall shear stress $\tau_w$ must approach laminar/turbulent skin-friction correlations along attached flat boundaries ($C_f \propto Re_x^{-1/2}$ or $Re_x^{-1/5}$) and reverse sign at separation points.

---

## Capability Status Classification Matrix
| Physical Gate | Classification | Implementation | Audit Test |
| :--- | :--- | :--- | :--- |
| **Drag Non-Negativity Auditor** | `REAL IMPLEMENTED` | Checks $C_D > 0$ across all evaluation operating conditions. | `test_negative_drag_fails_promotion` |
| **Lift Monotonicity Auditor** | `REAL IMPLEMENTED` | Verifies $\partial C_L / \partial \alpha > 0$ in the linear regime $-4^\circ \le \alpha \le 8^\circ$. | `test_non_monotonic_lift_slope_fails_promotion` |
| **Surface Stagnation Auditor** | `REAL IMPLEMENTED` | Checks $C_{p,max} \le 1.0$ (within numerical tolerance $\le 1.05$). | `test_surface_cp_stagnation_exceeded_fails_promotion` |
| **Skin Friction Sign Check** | `REAL IMPLEMENTED` | Validates $C_f \ge 0$ upstream of separation. | Active (`backend/physics_ai/validation.py`) |
| **Global Continuity & Momentum Residuals** | `DERIVED` | Evaluates mass flux divergence $\nabla \cdot (\rho \mathbf{u})$ on CFD meshes. | Active (`backend/simulation/`) |

---

## Promotion Gate Audit Workflow
```
                    ┌────────────────────────────────┐
                    │   Candidate Model Checkpoint   │
                    └───────────────┬────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │             Automated Physical Law Audit               │
       ├────────────────────────────────────────────────────────┤
       │ 1. Evaluate on linear polar: α ∈ [-4°, 0°, 4°, 8°]     │
       │    Check: ∂CL/∂α > 0                                   │
       │                                                        │
       │ 2. Evaluate drag at all evaluation points              │
       │    Check: CD > 0.0001                                  │
       │                                                        │
       │ 3. Evaluate surface pressure Cp distribution           │
       │    Check: max(Cp) ≤ 1.02                               │
       │                                                        │
       │ 4. Evaluate regression residuals on held-out test split│
       │    Check: CL RMSE < 0.05, CD RMSE < 0.01               │
       └────────────────────────────┬───────────────────────────┘
                                    │
                    [Did any physical gate fail?]
                                    ├──► YES ──► Status: FAILED_VERIFICATION / TRAINED_UNVERIFIED
                                    │            Action: Generate rejection report with violation details
                                    │            Block: Ineligible for active model deployment
                                    └──► NO  ──► Status: VERIFIED
                                                 Action: Sign reproducibility manifest with SHA-256 hash
                                                 Enable: Active deployment to inference API
```

---

## Failure Modes & Safe Degraded States
When an audit failure occurs:
- The model weights remain quarantined in `scratch/` or an unverified directory.
- The lifecycle status is locked to `TRAINED_UNVERIFIED`.
- An audit entry detailing the physical law violation is appended to `reports/model_audit_trail.json`.
- The user interface highlights the failing physical gate in bold red with exact numerical violation values.
