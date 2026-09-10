# 02 - Multi-Fidelity Scientific Fabric

The Multi-Fidelity Scientific Fabric arbitrates between heterogeneous sources of aerodynamic data to ensure maximum physical rigor and predictive fidelity.

## 1. 5-Tier Priority Cascade

When queried for an aerodynamic condition $(\text{geometry}, M, Re, \alpha)$, the `MultiFidelityResolver` queries sources in strict priority order:

1. **Tier 1: OFFICIAL_EXPERIMENT**
   - High-precision authentic wind tunnel measurements (e.g. NASA Langley TR-4074, Abbott & von Doenhoff).
   - Epistemic uncertainty: $\pm 1-2\%$ due to instrument calibration and tunnel wall corrections.
2. **Tier 2: VALIDATED_CFD**
   - Direct numerical simulation or ASME V&V 20 grid-converged RANS/LES simulations with verified $GCI < 1\%$.
3. **Tier 3: SURROGATE_PREDICTION**
   - Neural network surrogate (`AeroSurrogateV1` / `AeroSurrogateV2`) evaluated with epistemic variance and OOD detection.
4. **Tier 4: ANALYTICAL_RESULT**
   - Potential flow, thin airfoil theory ($C_{L,\alpha} = 2\pi$), or compressible Prandtl-Glauert / Karman-Tsien transformations.
5. **Tier 5: SIMULATION_PLANNER**
   - If no tier satisfies uncertainty requirements, the engine produces a `CFDJobSpec` proposal for high-fidelity execution.

## 2. Mathematical Formulations

### 2.1 Discrepancy Modeling
The discrepancy between high-fidelity truth $y_{\text{high}}(\mathbf{x})$ and a lower-fidelity surrogate $\hat{y}_{\text{low}}(\mathbf{x})$ is modeled as:
$$\Delta(\mathbf{x}) = y_{\text{high}}(\mathbf{x}) - \hat{y}_{\text{low}}(\mathbf{x})$$

The relative discrepancy metric is given by:
$$\delta_{\text{rel}} = \frac{|\Delta(\mathbf{x})|}{|y_{\text{high}}(\mathbf{x})| + \epsilon}$$

### 2.2 Uncertainty Calibration
Uncertainty calibration is evaluated using empirical coverage across test intervals:
$$\text{Coverage}_{1\sigma} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}\left(|y_i - \hat{y}_i| \le \sigma_i\right) \quad (\text{Nominal: } 68.3\%)$$
$$\text{Coverage}_{2\sigma} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}\left(|y_i - \hat{y}_i| \le 2\sigma_i\right) \quad (\text{Nominal: } 95.4\%)$$

Calibration error is computed as:
$$\text{ECE} = \frac{1}{2}\left(|\text{Coverage}_{1\sigma} - 0.683| + |\text{Coverage}_{2\sigma} - 0.954|\right)$$

### 2.3 Linear Co-Kriging Multi-Fidelity Fusion
Data fusion combines predictions using scaling parameter $\rho$ and additive bias field $\delta$:
$$\hat{y}_{\text{fused}}(\mathbf{x}) = \rho \cdot \hat{y}_{\text{low}}(\mathbf{x}) + \delta(\mathbf{x})$$

With fused variance:
$$\sigma_{\text{fused}}^2(\mathbf{x}) = \rho^2 \sigma_{\text{low}}^2(\mathbf{x}) + \sigma_{\delta}^2(\mathbf{x})$$
