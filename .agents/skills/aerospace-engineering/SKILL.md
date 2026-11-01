---
name: aerospace-engineering
description: First-principles aerospace vehicle design, subsonic/transonic aerodynamics, stability and control derivatives, atmospheric modeling (US Standard 1976), and flight mechanics equations.
---

# Aerospace Engineering Skill

## 1. Aerodynamic Fundamentals
- **Thin Airfoil Theory**:
  - Lift slope: $C_{L_\alpha} = 2\pi \approx 0.1097\text{ deg}^{-1}$ (inviscid, incompressible).
  - Aerodynamic center: $x_{ac} = c/4$.
  - Zero-lift angle of attack: $\alpha_{0L} = -\frac{1}{\pi}\int_0^\pi \frac{dz}{dx}(\cos\theta - 1)d\theta$.
- **Finite Wing Theory (Vortex Lattice & Trefftz Plane)**:
  - Induced drag coefficient: $C_{D_i} = \frac{C_L^2}{\pi AR e}$.
  - Finite wing lift slope: $C_{L_\alpha, 3D} = \frac{C_{L_\alpha, 2D}}{1 + \frac{C_{L_\alpha, 2D}}{\pi AR e}}$.
  - Helmbold-Keune formulation for low aspect ratio / sweep.
- **Compressibility Corrections**:
  - Prandtl-Glauert ($M < 0.7$): $C_p = \frac{C_{p,0}}{\sqrt{1 - M_\infty^2}}$, $C_L = \frac{C_{L,0}}{\sqrt{1 - M_\infty^2}}$.
  - Karman-Tsien: $C_p = \frac{C_{p,0}}{\sqrt{1 - M_\infty^2} + \frac{M_\infty^2}{1 + \sqrt{1 - M_\infty^2}}\frac{C_{p,0}}{2}}$.

## 2. Atmospheric & Flight Mechanics
- **US Standard Atmosphere (1976)**:
  - Troposphere ($h \le 11,000\text{ m}$): $T = T_0 - L\cdot h$, $p = p_0 (1 - L h/T_0)^{g/(RL)}$.
  - Speed of sound: $a = \sqrt{\gamma R T}$ ($\gamma=1.4$, $R=287.05\text{ J/(kg K)}$).
  - Dynamic viscosity: Sutherland's law $\mu(T) = \mu_0 \left(\frac{T}{T_0}\right)^{1.5} \frac{T_0 + S}{T + S}$ ($S = 110.4\text{ K}$).
- **Stability Derivatives & Flight Controls**:
  - Static margin: $SM = -\frac{dC_m}{dC_L} = \frac{x_{np} - x_{cg}}{\bar{c}}$ ($SM > 0$ for passive longitudinal stability).
  - Damping derivatives: $C_{m_q}, C_{L_q}, C_{n_r}, C_{l_p}$.
  - Autopilot card decks: USAF DATCOM, NASA S/HABP, JSBSim 6-DoF XML (`<fdm_config>`), PX4/ArduPilot tuning parameters.

