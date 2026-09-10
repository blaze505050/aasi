# Zero-Leakage Geometry Splitting & OOD Partitions

## The Data Leakage Problem in Aerodynamics

In aerodynamic machine learning, splitting samples purely at random (e.g. standard `train_test_split`) causes severe **geometry data leakage**:
- The model trains on NACA 0012 at $\alpha = 4^\circ$, $M=0.2$ and tests on NACA 0012 at $\alpha = 6^\circ$, $M=0.2$.
- In this regime, the model only memorizes the polar lookup table of that specific airfoil without learning true invariant geometric flow representations.
- Generalization to unseen wings or newly designed airfoils fails completely.

---

## Strict Geometry-Level Isolation

`backend/physics_ai/splits.py` (`GeometryLevelSplitter`) enforces that the set of airfoil geometries in training has zero intersection with the testing or validation sets:

$$\text{Geometries}_{\text{Train}} \cap \text{Geometries}_{\text{Test}} = \emptyset$$
$$\text{Geometries}_{\text{Train}} \cap \text{Geometries}_{\text{Val}} = \emptyset$$
$$\text{Geometries}_{\text{Test}} \cap \text{Geometries}_{\text{Val}} = \emptyset$$

---

## Partition Manifest for TR-AERO-SURROGATE-V1-001

Split Seed: `42`  
Split Cryptographic Checksum: `0b5832a8dd93efd9a9f4c3d4a046894c25be8e27c134015ea195cb9ad9114ce9`

| Partition | Geometries Assigned | Sample Count | Percentage | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | `clark_y`, `naca0009`, `naca4412` | 432 | 51.1% | Parameter learning via AdamW |
| **Validation** | `naca0006` | 144 | 17.0% | Early stopping & hyperparameter tuning on unseen geometry |
| **Test** | `naca0012`, `naca2412` | 180 | 21.3% | Final performance benchmarking on completely held-out airfoils |
| **OOD Geometry** | `rae2822` | 90 | 10.6% | Supercritical high-camber transonic test |
| **Total** | 7 geometries | 846 | 100% | Clean partitioning with zero overlap |

---

## OOD Condition Partitions

In addition to geometry-level holdouts, the splitter identifies:
- **Condition OOD:** Extreme high angles of attack ($\alpha > 12^\circ$ or $\alpha < -5^\circ$), approaching separated flow / stall.
- **Mach OOD:** $M > 0.35$ (onset of compressibility effects).
