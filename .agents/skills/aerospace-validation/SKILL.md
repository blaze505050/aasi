---
name: aerospace-validation
description: Validates aerodynamic calculations against reference data and physical constraints. Use when verifying panel solver results, surrogate predictions, or new physics implementations.
---

# Aerospace Validation Skill

## Purpose
Provides reference data, physical constraints, and validation procedures for AASI aerodynamic computations.

## Reference Cases for NACA 0012

### Thin Airfoil Theory Baselines
| Parameter | Value | Source |
|---|---|---|
| CL_α (inviscid, 2D) | 2π rad⁻¹ ≈ 0.1097 deg⁻¹ | Thin airfoil theory |
| CL at α=0° | 0.0 (symmetric) | Geometry |
| CM_c/4 at α=0° | 0.0 (symmetric) | Geometry |

### NASA Langley LTPT Data (Re = 3×10⁶, M = 0.15)
| α (deg) | CL | CD | Source |
|---|---|---|---|
| 0 | 0.000 | 0.0065 | Abbott & von Doenhoff (1959) |
| 4 | 0.44 | 0.0075 | Abbott & von Doenhoff (1959) |
| 8 | 0.85 | 0.012 | Abbott & von Doenhoff (1959) |
| 12 | 1.15 | 0.025 | Approximate from literature |

### Validation Procedure
1. **Compute** panel solver result for NACA 0012 at reference conditions
2. **Compare** CL with thin airfoil theory (expect within 10% for α < 8°)
3. **Compare** CD with experimental data (expect within 30% for panel method)
4. **Verify** symmetry: CL(0°) ≈ 0.0 for symmetric profiles
5. **Check** CL_α slope: should be ≈ 0.10-0.11 per degree for thin subsonic airfoils
6. **Verify** drag positivity: CD > 0 always
7. **Check** stall behavior: CL should decrease above ~12-15° for NACA 0012

## Physical Constraint Checks

### Universal Constraints (Always Valid)
- CD > 0 for unpowered bodies in real fluid
- CL(α=0°) = 0 for symmetric airfoils (±0.02 tolerance)
- CL changes sign through α = α₀ₗ

### Regime-Dependent (Verify Domain)
- dCL/dα > 0 **only** in attached pre-stall flow (typically α < 10-15°)
- CL monotonicity breaks at stall — DO NOT enforce above α_stall
- CM_α < 0 for static stability about aerodynamic center
- Prandtl-Glauert correction only valid for M < M_crit ≈ 0.7-0.8

### Invalid Assumptions to Avoid
- "CL always increases with α" — FALSE above stall
- "CD always increases with α" — approximately true but non-monotonic near CL_min
- "Panel method == CFD" — FALSE, panel method is inviscid + corrections
- "Surrogate prediction == experimental data" — FALSE, model prediction with uncertainty
