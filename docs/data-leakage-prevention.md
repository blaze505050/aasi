# AASI Data Leakage Prevention & Dataset Partitioning

## The Geometry-Level Leakage Vulnerability
In aerodynamic machine learning, splitting data by individual operating points $(AoA, Re)$ rather than by physical geometry (airfoil contour) produces catastrophic data leakage. Because an airfoil at $\alpha = 2^\circ$ has nearly identical surface pressure distribution to the same airfoil at $\alpha = 2.5^\circ$, naive point-wise random splits result in artificially inflated test accuracy ($R^2 > 0.999$) that collapses completely when applied to unseen airfoils in real flight.

AASI enforces **strict geometry-level partitioning** and normalizer isolation across all datasets.

---

## Capability Status Classification Matrix
| Mechanism | Classification | Implementation | Verification Test |
| :--- | :--- | :--- | :--- |
| **Geometry-Level Train/Val/Test Split** | `REAL IMPLEMENTED` | Partitions by airfoil ID / geometry hash; zero geometry overlap. | `test_geometry_leakage_detection_raises_error` |
| **Normalizer Statistics Isolation** | `REAL IMPLEMENTED` | Fits mean/scale strictly on training split; transforms val/test. | `test_normalizer_isolated_to_training_set` |
| **Reynolds Number Stratification** | `REAL IMPLEMENTED` | Holds out discrete Reynolds regimes ($Re = 5 \times 10^5, 2 \times 10^6$) for OOD validation. | `backend/physics_ai/splits.py` |
| **Angle of Attack (AoA) Extrapolation Gate** | `REAL IMPLEMENTED` | Isolates high-angle post-stall points ($\alpha > 12^\circ$) into separate test bucket. | `backend/physics_ai/splits.py` |

---

## Partitioning Rules & Integrity Invariants

### 1. Geometry Invariant
Let $\mathcal{G}_{train}, \mathcal{G}_{val}, \mathcal{G}_{test}$ denote the sets of geometric profiles in the respective splits:
$$\mathcal{G}_{train} \cap \mathcal{G}_{val} = \emptyset, \quad \mathcal{G}_{train} \cap \mathcal{G}_{test} = \emptyset, \quad \mathcal{G}_{val} \cap \mathcal{G}_{test} = \emptyset$$
Any intersection triggers `DataLeakageError: Airfoil geometry <id> appears in both training and evaluation splits!`

### 2. Normalization Invariant
Normalizer parameters $\mu, \sigma$ are computed strictly over the training partition:
$$\mu_{train} = \frac{1}{N_{train}} \sum_{i \in \text{train}} x_i, \quad \sigma_{train} = \sqrt{\frac{1}{N_{train}} \sum_{i \in \text{train}} (x_i - \mu_{train})^2}$$
Evaluation data points $x_{test}$ are scaled using $\mu_{train}, \sigma_{train}$ without updating parameters. Computing $\mu, \sigma$ over the pooled dataset is caught by automated unit tests and rejected.

### 3. Five-Tier Evaluation Bucketing
Evaluation splits are partitioned into five orthogonal testing tiers:
```
┌────────────────────────────────────────────────────────────────────────┐
│                        Evaluation Partitions                           │
├──────────────────┬─────────────────────────────────────────────────────┤
│ IN-DISTRIBUTION  │ Seen geometries, seen Re and AoA ranges.            │
├──────────────────┼─────────────────────────────────────────────────────┤
│ GEOMETRY-OOD     │ Unseen airfoil shapes (e.g. supercritical, cambered)│
├──────────────────┼─────────────────────────────────────────────────────┤
│ REYNOLDS-OOD     │ Unseen boundary-layer regimes (e.g. transitional)   │
├──────────────────┼─────────────────────────────────────────────────────┤
│ AOA-OOD          │ Near-stall and separated flow regimes               │
├──────────────────┼─────────────────────────────────────────────────────┤
│ JOINT-OOD        │ Unseen shape + unseen flow condition                │
└──────────────────┴─────────────────────────────────────────────────────┘
```
This multi-tier breakdown prevents false claims of generalizability.
