# Experiment Planning & Information-Gain Engine

## 1. Multi-Criteria Utility Formulation
In AASI, experiments are ranked by deterministic utility rather than arbitrary heuristics:
$$U(E_i) = \frac{\Delta I(H; E_i) \cdot S(E_i)}{C(E_i) \cdot (1 + R(E_i))}$$

Where:
- $\Delta I(H; E_i)$: Expected information gain in bits (Shannon entropy reduction).
- $S(E_i)$: Scientific significance of the determination ($[0.0, 1.0]$).
- $C(E_i)$: Computational cost index ($1.0$ for panel, $8.0$ for RANS, $20.0$ for LES).
- $R(E_i)$: Execution risk ($[0.0, 1.0]$, accounting for solver divergence and mesh skewness).

## 2. Discrimination Power
A candidate experiment must differentiate between competing hypotheses ($H_1$ and $H_2$). For example:
- **Panel Method:** Rapid attached flow baseline; low cost, high pre-stall utility.
- **RANS CFD:** Resolves boundary layer profiles and recirculation bubbles; medium cost, high separation utility.
- **Wind-Tunnel Benchmark:** Audited historical ground truth; near-zero risk, highest discrimination.
