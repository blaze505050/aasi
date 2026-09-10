# Frontend User Guide: Physics AI Lab

## Overview

The **PHYSICS AI LAB** is a dedicated interactive workbench within the AASI dashboard (accessed via the `PHYSICS-AI LAB` tab in the research drawer or full panel).

It allows aerospace engineers to interactively explore trained neural operators, generate real-time polar sweeps, audit local datasets for authenticity, and perform grid convergence calculations.

---

## Interactive Modules

### 1. Real-Time Airfoil Inference
- **Profile Selector:** Choose between symmetric profiles (NACA 0012, 0009, 0006), cambered wings (NACA 2412, 4412), general aviation (Clark Y), or supercritical profiles (RAE 2822).
- **Flow Sliders & Inputs:**
  - Mach number ($0.05$ to $0.40$)
  - Reynolds number ($5\times 10^5$ to $6\times 10^6$)
  - Angle of Attack ($-8^\circ$ to $+18^\circ$)
- **Readout Displays:**
  - $C_L$ (Lift) in cyan with bounded $\pm \sigma_{CL}$
  - $C_D$ (Drag) in amber with bounded $\pm \sigma_{CD}$
  - $C_M$ (Pitching Moment) in purple
- **Domain & Epistemic Badges:**
  - Green `IN_DOMAIN` badge indicates high confidence supported by the training manifold.
  - Amber `EXTRAPOLATION_NEAR_BOUNDARY` warns that flow is approaching separation or high Mach.
  - Red `SURROGATE_OUT_OF_DOMAIN` indicates conditions exceed the operational envelope.

### 2. Live Aerodynamic Polar Curves ($C_L(\alpha)$ & $C_D(\alpha)$)
- Click **GENERATE POLAR** to execute an automated sweep from $-4^\circ$ to $+14^\circ$.
- Interactive SVG chart shows:
  - Solid cyan curve: Lift coefficient $C_L$ vs $\alpha$
  - Dashed amber curve: Drag coefficient $C_D \times 10$ vs $\alpha$
  - Hover over any data point to inspect $(AoA, C_L, C_D)$ values
  - Monotonicity check badge confirms zero negative slopes in the attached pre-stall regime.

### 3. Dataset Authenticity Audit Table
- Real-time disk inspection card.
- Displays `VERIFIED` datasets on disk with sample counts.
- Displays `METADATA_ONLY` records with honest warnings.
- Click **REFRESH AUDIT** to re-scan disk storage.

### 4. Grid Convergence Index (ASME V&V 20) Calculator
- Enter 3 grid solutions ($f_1$ fine, $f_2$ medium, $f_3$ coarse) and refinement ratios ($r_{21}, r_{32}$).
- Or click **LOAD NACA 0012 BENCHMARK** to populate reference CFD mesh data.
- Click **COMPUTE GCI & OBSERVED ORDER p** to obtain:
  - Observed Apparent Order of Convergence ($p$)
  - Zero-grid Richardson Extrapolated value ($f_{ext}$)
  - Fine grid uncertainty ($\text{GCI}_{fine} \%$)
  - Asymptotic range validation check.
