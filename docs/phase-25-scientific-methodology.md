# AASI Phase 25 Scientific Methodology: Autonomous Decision & Diagnostics

**Document Version:** 25.1.0  
**Governing Standard:** ASME V&V 20-2009 / AIAA S-071A-1999  
**Core Doctrine:** Absolute Anti-Fabrication Rule & Provenance Integrity  

---

## 1. Overview

This document specifies the mathematical models, decision criteria, diagnostic algorithms, and discrepancy formulations underlying the **AASI Autonomous Scientific Execution Platform**.

---

## 2. Aerodynamic Similarity & Distance Metric Formulation

To decide whether a query can be answered from verified existing CFD or requires a new simulation, AASI evaluates a composite aerodynamic distance $D(\mathbf{x}, \mathbf{x}_i)$ in normalized feature space:

$$\mathbf{x} = \big[ \theta_{\text{geom}},\ \alpha,\ \log_{10}(Re),\ M \big]^T$$

The composite distance between target condition $\mathbf{x}_{\text{target}}$ and candidate dataset case $\mathbf{x}_i$ is given by:

$$D = \sqrt{w_g d_g^2 + w_\alpha d_\alpha^2 + w_{Re} d_{Re}^2 + w_M d_M^2}$$

where:
- **Geometry Distance ($d_g$):**
  $$d_g = \begin{cases} 
  0.0 & \text{if identical profile} \\
  0.2 + 0.4 \frac{|\Delta m|}{9} + 0.4 \frac{|\Delta t|}{30} & \text{if NACA 4-digit family} \\
  0.8 & \text{if distinct airfoil family (e.g. supercritical RAE 2822 vs NACA)}
  \end{cases}$$
- **Angle of Attack Distance ($d_\alpha$):**
  $$d_\alpha = \frac{|\alpha_{\text{target}} - \alpha_i|}{15^\circ}$$
- **Reynolds Number Distance ($d_{Re}$):**
  $$d_{Re} = \frac{|\log_{10}(Re_{\text{target}}) - \log_{10}(Re_i)|}{2.0}$$
- **Mach Number Distance ($d_M$):**
  $$d_M = \frac{|M_{\text{target}} - M_i|}{0.3}$$
- Weights: $w_g = 1.5, w_\alpha = 1.0, w_{Re} = 0.5, w_M = 0.5$.

---

## 3. Fidelity Decision Logic

The **Fidelity Decision Engine** (`backend/agent/decision_engine.py`) determines solver routing using two empirical dimensions:
1. **Best Database Distance ($D_{\min}$):**
   - $D_{\min} < 0.05 \implies \text{Match Quality: HIGH}$
   - $0.05 \le D_{\min} < 0.20 \implies \text{Match Quality: MEDIUM}$
   - $D_{\min} \ge 0.20 \implies \text{Match Quality: LOW / NONE}$
2. **Surrogate Epistemic Uncertainty ($\sigma_{\text{epistemic}}$):**
   Evaluated via conformal interval width and Mahalanobis distance in latent space:
   - $\sigma_{\text{epistemic}} < 0.12 \implies \text{Uncertainty: LOW}$
   - $0.12 \le \sigma_{\text{epistemic}} < 0.25 \implies \text{Uncertainty: MEDIUM}$
   - $\sigma_{\text{epistemic}} \ge 0.25 \implies \text{Uncertainty: HIGH}$

### Decision Rules:
$$\text{Fidelity}(\mathbf{x}) = \begin{cases}
\text{DATABASE\_MATCH} & \text{if } D_{\min} < 0.05 \land \sigma_{\text{epistemic}} < 0.12 \\
\text{SURROGATE\_INFERENCE} & \text{if } D_{\min} < 0.20 \land \sigma_{\text{epistemic}} < 0.25 \\
\text{NEW\_CFD\_REQUIRED} & \text{if } D_{\min} \ge 0.20 \lor \sigma_{\text{epistemic}} \ge 0.25 \lor |\alpha| > 12^\circ \\
\text{MULTI\_FIDELITY\_COMPARISON} & \text{if user explicitly requests validation}
\end{cases}$$

---

## 4. Analytical Physics & Multi-Fidelity Discrepancy Formulation

### 4.1 Thin Airfoil Potential Flow
For low-speed incompressible flow, the analytical reference lift coefficient is given by thin airfoil theory:

$$C_{L,\text{analytical}} = 2\pi (\alpha - \alpha_0)$$

where the zero-lift angle $\alpha_0$ is evaluated from camber distribution $y_c(x)$:

$$\alpha_0 = -\frac{1}{\pi} \int_0^\pi \frac{dy_c}{dx} (\cos\theta - 1) d\theta$$

For symmetric airfoils (NACA 0012), $\alpha_0 = 0^\circ$. For cambered airfoils (NACA 4412), $\alpha_0 \approx -4.0^\circ$.

### 4.2 Multi-Fidelity Discrepancy
For each aerodynamic quantity $Q \in \{C_L, C_D, C_M\}$, the discrepancy $\delta$ between high-fidelity live CFD and lower-fidelity estimates is defined as:

$$\delta_{\text{CFD-Surr}} = Q_{\text{LIVE\_CFD}} - Q_{\text{SURROGATE}}$$
$$\delta_{\text{CFD-Ana}} = Q_{\text{LIVE\_CFD}} - Q_{\text{ANALYTICAL}}$$

---

## 5. CFD Error Diagnostics Signature Rules

The diagnostic engine inspects solver stdout logs, mesh logs, and force histories using deterministic pattern signatures:

| Error Class | Deterministic Signature / Evidence | Root Cause |
| :--- | :--- | :--- |
| **`MISSING_SOLVER`** | `command not found` or `not recognized` | Solver binary absent from PATH |
| **`FLOATING_POINT_FAILURE`** | `Floating point exception` or residual `= nan` | Matrix singularity or divide-by-zero |
| **`DIVERGENCE`** | Residual $R_p > 10.0$ or $> 100.0$ in last 10 iter | Under-relaxation or severe mesh skew |
| **`RESIDUAL_STAGNATION`** | $R_p > 10^{-2}$ for $> 300$ iter and $|\Delta R_p| < 10^{-4}$ | Solver tolerance or grid limit reached |
| **`MESH_QUALITY_FAILURE`** | `skewness > 4` or `non-orthogonality > 70` | Boundary layer hyperbolic clustering error |
| **`INVALID_BOUNDARY_CONDITION`** | `patch not found` or `incompatible dimensions` | Mismatch between `0/` fields and `polyMesh` |
| **`PHYSICS_GATE_VIOLATION`** | $C_D \le 0.0$ or surface $C_p > 1.05$ | Physical law violation |

---

## 6. Non-Mutating Repair Candidate Derivation

When a simulation fails, AASI refuses to overwrite the existing directory or silently alter parameters. Instead, the repair engine synthesizes a new candidate configuration:

1. **Original Integrity:** The original case directory and its manifest are locked as immutable records with status `FAILED`.
2. **Candidate Synthesis:** Modifications are applied to relaxation factors, discretization schemes, or mesh grading parameters.
3. **Cryptographic Sealing:**
   $$\text{Hash}_{\text{candidate}} = \text{SHA-256}\Big(\text{Hash}_{\text{original}} \parallel r \parallel \text{JSON}(\text{modifications})\Big)$$
4. **Retry Bound:**
   $$r \le 3$$
   If $r > 3$, the pipeline halts and transitions to **`HUMAN_REVIEW_REQUIRED`**.
