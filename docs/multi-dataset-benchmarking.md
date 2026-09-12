# AASI Multi-Dataset Aerodynamic Benchmarking Standard

**Document ID**: `STD-MULTI-DATASET-BENCHMARK-01`  
**Governing Standard**: AASI Multi-Fidelity Scientific Verification Standard  
**Last Updated**: 2026-09-12  

---

## 1. Executive Summary

Aerodynamic surrogates and physics-informed models cannot be deemed validated by scoring against a single dataset. In practical engineering, models frequently fit numerical solver artifacts (e.g. artificial dissipation in a specific RANS code) or experimental tunnel biases (e.g. sidewall boundary layer displacement).

AASI enforces a **multi-ground-truth benchmarking architecture**:
1. **Experimental Ground Truth**: NASA Langley Low-Turbulence Pressure Tunnel (`DATASET-NACA-0012-LTPT`, NASA TM-4083).
2. **Computational RANS Ground Truth**: AirfRANS OpenFOAM `simpleFoam` with Spalart-Allmaras closure (`DATASET-AIRFRANS-1K`, NeurIPS 2022).

---

## 2. Multi-Dataset Comparison Methodology

The `MultiDatasetBenchmarkEngine` processes aerodynamic predictions across both datasets simultaneously:
- **Case Matching**: Matches prediction queries $(geometry, \alpha, M, Re)$ against authentic dataset cases within tolerance ($\Delta \alpha \le 1.5^\circ$, $\Delta \log_{10}(Re) \le 0.5$).
- **Metric Decomposition**:
  - $\Delta C_L = C_{L,\text{pred}} - C_{L,\text{dataset}}$
  - $\Delta C_D = C_{D,\text{pred}} - C_{D,\text{dataset}}$
  - Root Mean Square Error (RMSE) on $C_L$ and $C_D$.
  - Percentage of predictions falling within the expanded 95% confidence uncertainty band ($U_{95}$).
- **Cross-Dataset Bias Tracking**:
  - Computes $\Delta_{\text{CFD-EXP}} = C_{L,\text{AirfRANS}} - C_{L,\text{LTPT}}$.
  - The Spalart-Allmaras model known bias in near-stall regimes ($\alpha \ge 12^\circ$) produces slightly higher attached lift than experimental measurements. A valid model must not blindly interpolate between contradictory data points without tagging turbulence closure discrepancy.

---

## 3. Scientific Consistency Rating

The engine computes an overall **Scientific Consistency Score** $S \in [0.0, 1.0]$:
$$S = \max\left(0, 1 - \frac{\text{RMSE}_{C_L,\text{combined}}}{0.15}\right)$$
- $S \ge 0.90$: Excellent fidelity across both wind tunnel and CFD data.
- $0.75 \le S < 0.90$: Acceptable engineering accuracy; minor stall discrepancy.
- $S < 0.75$: Discrepancy exceeds uncertainty threshold; flags model retraining requirement.

---

## 4. Reproducibility & Audit Trail

Every multi-dataset benchmark execution generates a persistent `MultiDatasetBenchmarkResult` containing:
- Unique cryptographic benchmark ID.
- Exact lists of evaluated dataset cases and flight conditions.
- Formal GUM uncertainty assessment budget.
- Automatic integration with the AASI Research Evidence Ledger DAG.
