# Open Physics Dataset Factory & Leakage-Free Partitioning

## Overview
AASI Phase 5 provides an automated, hardware-aware dataset factory designed to manage high-value open physics datasets for scientific machine learning and surrogate modeling.

To respect resource-constrained developer hardware, the dataset factory employs a **download-on-demand and manifest-first** strategy. Instead of downloading hundreds of gigabytes of raw simulation meshes, AASI indexes verified manifests with cryptographic SHA-256 hashes and enforces a 2 GB local storage quota.

---

## High-Value Open Physics Datasets

| Dataset | Domain | Samples | Raw Size | Geometry Leakage Guard | License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AirfRANS** | 2D Airfoil RANS CFD | 1,000 simulations | ~14 GB (full) / 120 MB (sampled) | Strict geometry-level grouping (0% leakage) | CC-BY 4.0 |
| **NASA Common Research Model (CRM)** | 3D Transonic Wing/Fuselage | 32 RANS polar points | ~8 GB (full) / 45 MB (coefficients) | Config isolation (High-Lift vs Cruise) | Public Domain (US Govt) |
| **Abbott & von Doenhoff Polars** | 2D Wind Tunnel Experiments | 180 airfoil sections | 12 MB | Individual section isolation | Public Domain |

---

## The Critical Danger: Geometry Data Leakage in Aerodynamics

In traditional machine learning, random train/test splits (e.g. `train_test_split(test_size=0.2)`) are standard practice. However, in computational aerodynamics and surrogate modeling, **random splitting creates severe data leakage**:

$$P(\text{airfoil } G \in \text{Test} \mid G \in \text{Train}) > 0$$

If the training set contains NACA 0012 at $\alpha \in \{0^\circ, 2^\circ, 6^\circ, 8^\circ\}$ and the test set contains NACA 0012 at $\alpha = 4^\circ$, the neural operator does not evaluate true geometric generalization. It merely interpolates across angles of attack on a geometry whose surface curvature and boundary layer profile it has already memorized. This creates an illusion of high accuracy (e.g., 99.5%) that catastrophically degrades when presented with an unseen supercritical or laminar airfoil profile.

### The AASI Solution: `GeometryLevelSplitter`
The `GeometryLevelSplitter` algorithm enforces strict group isolation:
1. All simulation samples are mapped to their canonical geometry identifier (e.g. `NACA 0012`, `RAE 2822`, `NACA 4412`, `Clark Y`).
2. Splitting occurs strictly at the **geometry level**, not the sample level:
   $$\text{Geometries}_{\text{Train}} \cap \text{Geometries}_{\text{Test}} = \emptyset$$
3. Guaranteed **0.0% geometry leakage**. The test partition contains exclusively airfoils that the model has never encountered during training.

---

## Out-of-Domain (OOD) Extrapolation Partitions
To evaluate physics-AI robustness beyond standard flight envelopes, `OODSplitter` generates specialized out-of-domain partitions:
- **High Angle-of-Attack (Stall Regime):** $\alpha > 12^\circ$
- **Transonic Shock Regime:** $M > 0.70$
- **Low Reynolds Regime:** $Re < 5 \times 10^5$

Surrogates evaluated on these partitions are tested specifically for physical failure modes (unphysical negative drag, violation of lift monotonicity).

---

## Physical Quality & Sanity Validation
Every ingested dataset point is audited by `DatasetValidator`:
- $C_D > 0$ (strictly positive drag in unpowered external flow)
- $|C_L| \le 3.5$ (aerodynamic sanity ceiling for subsonic airfoils)
- Identical duplicate flow conditions within tolerance are flagged and deduplicated.
