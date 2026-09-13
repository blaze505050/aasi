# AASI Phase 20 Architecture: Physics-AI Generalization & Active Scientific Experimentation

**Document ID:** AASI-ARCH-PHASE20-001  
**Status:** Architectural Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule (Zero synthetic placeholders, fail-closed execution)

---

## 1. System Pipeline Overview

Phase 20 introduces an end-to-end, mathematically rigorous, and active scientific discovery feedback loop:

```
[AUTHENTIC DATA] (Experimental Polars / Signed CFD Manifest)
       ↓
[DATASET CATALOG & STORAGE GUARD] (15 GB safety reserve)
       ↓
[PROVENANCE & CRYPTOGRAPHIC HASHING] (SHA-256 DAG)
       ↓
[GEOMETRY REPRESENTATION LAYER] (Representations A, B, C, D)
       ↓
[LEAKAGE-SAFE GEOMETRY SPLITTING] (Disjoint airfoil shapes)
       ↓
[MODEL BENCHMARK SUITE] (Unified fit/predict/evaluate interface)
       ↓
[PHYSICS VALIDATION GATES] (Drag positivity, stagnation ceiling, lift monotonicity)
       ↓
[QUANTITATIVE OOD EVALUATION] (7-tier matrix with distance metrics)
       ↓
[UNCERTAINTY CALIBRATION ENGINE] (Conformal prediction & empirical coverage)
       ↓
[SCIENTIFIC PROMOTION HIERARCHY] (6-stage unearned promotion gate)
       ↓
[PERSISTENT EXPERIMENT REGISTRY] (Immutable AASI-P20-EXP-XXX records)
       ↓
[ACTIVE LEARNING CANDIDATE SELECTOR] (Uncertainty + OOD Distance + Diversity)
       ↓
[CANONICAL CFD CASE DECK STAGING] (USER_EXECUTED_REQUIRED when solver is offline)
       ↓
[AUTHENTIC RESULT INGESTION] (Schema, physics, and provenance verification)
       ↓
[RETRAIN & BENCHMARK COMPARISON]
```

---

## 2. Geometry Representation Subsystem

The geometry representation layer converts raw airfoil point clouds into standardized, coordinate-normalized, and mathematically invariant geometric structures:
1. **Raw Ingestion:** Ingests upper/lower curves or closed boundary contours.
2. **Normalization:** Scales coordinates to unit chord ($x \in [0, 1]$), aligns the leading edge to the origin $(0, 0)$, and cleans redundant or duplicate points.
3. **Equidistant Contour Resampling:** Resamples contours via arc-length parametrization to a fixed target point count $N$ (e.g. $N = 64$ points: 32 upper surface, 32 lower surface).
4. **Curvature & Geometric Feature Extraction:** Computes maximum thickness ratio $t/c$, maximum camber $m$, position of maximum camber $p$, leading-edge radius proxy $r_{\text{LE}}$, and trailing-edge gap $\delta_{\text{TE}}$.
5. **Geometry Identity Hashing:**
   $$\mathcal{H}_{\text{geom}} = \text{SHA-256}\left(\text{Normalized Coordinates Rounded to } 6 \text{ Decimals}\right)$$
   Any two airfoils possessing identical normalized contours resolve to the exact same cryptographic hash.
6. **Experimental Representations:**
   - **Representation A (Engineering Descriptors):** $[\alpha, Re, t/c, m, p, \alpha^2]$
   - **Representation B (Coordinate Vector):** Flattened standardized contour vector $[x_1, y_1, \dots, x_N, y_N]$ concatenated with flow conditions $[\alpha, Re, M]$.
   - **Representation C (Surface Separation):** Separate upper surface $y_u(x)$ and lower surface $y_l(x)$ evaluated on standard abscissae.
   - **Representation D (Hybrid):** Concatenation of engineering descriptors and geometric contour moments.

---

## 3. Modular Model Benchmark Engine

All surrogate models adhere to the `AeroSurrogateBase` contract:
- `fit(X, y)`: Trains deterministically with fixed random seed.
- `predict(X)`: Computes point estimates $[\hat{C}_L, \hat{C}_D, \hat{C}_m]$.
- `predict_with_uncertainty(X)`: Returns point estimate and epistemic standard deviation $\hat{\sigma}(X)$.
- `save(path)` / `load(path)`: Persists weights with SHA-256 checksum verification.
- `hash()`: Computes cryptographic digest of active weight arrays.
- `evaluate(X, y)`: Computes $R^2$, RMSE, MAE, Max Error, and physical violation counts.

Supported Model Family:
1. `Phase19RidgeBaseline`: Analytical $L_2$ regression baseline.
2. `PolynomialRidgeSurrogate`: Polynomial feature expansion (degree 2 & 3) + Ridge.
3. `RandomForestSurrogate`: Ensemble of 50 regression trees with leaf variance estimation.
4. `GradientBoostingSurrogate`: Gradient boosted regression trees for non-linear boundary capture.
5. `MultilayerPerceptronSurrogate`: 3-layer neural network with GELU activations.
6. `GeometryAwareMLPSurrogate`: Dual-encoder neural network fusing geometry coordinate latent embeddings with condition latent embeddings.
7. `PhysicsConstrainedSurrogate`: Penalized loss enforcing non-negative drag, attached-flow lift monotonicity, and stagnation bounds.
8. `ModelEnsembleSurrogate`: Variance-weighted ensemble combining predictions and pooling epistemic uncertainty.

---

## 4. Quantitative OOD Evaluation & Epistemic Uncertainty Calibration

### 7-Tier Out-of-Distribution Taxonomy
1. **In-Distribution (ID):** Interpolation within training geometries and flow envelopes.
2. **Geometry-OOD:** Testing on unseen airfoil shapes (e.g. NACA 6409, NACA 4415, Clark Y, RAE 2822).
3. **Reynolds-OOD:** Testing on Reynolds regimes outside training range ($Re > 10^7$ or $Re < 5\times 10^5$).
4. **AoA-OOD:** Testing at extreme angles of attack ($\alpha > 15^\circ$).
5. **Joint-OOD:** Simultaneous geometry, Reynolds, and AoA extrapolation.
6. **Thickness-OOD:** Airfoils with thickness ratios far from training distribution ($t/c < 0.06$ or $t/c > 0.18$).
7. **Camber-OOD:** Airfoils with camber values far from training distribution ($m > 0.05$).

### Quantitative Distribution Distance Metrics
- **Contour Hausdorff Distance:** $d_H(G_1, G_2) = \max\left(\sup_{x \in G_1} \inf_{y \in G_2} \|x - y\|, \sup_{y \in G_2} \inf_{x \in G_1} \|x - y\|\right)$
- **Mean Euclidean Contour Distance:** Average point-to-point distance on arc-length resampled coordinates.
- **Feature-Space Mahalanobis Distance:** $d_M(x, \mu_{\text{train}}) = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$

### Conformal Prediction & Calibration Gate
Conformal prediction computes non-conformity scores on a held-out calibration split:
$$s_i = \frac{|y_i - \hat{y}(x_i)|}{\hat{\sigma}(x_i)}$$
Given significance level $\alpha = 0.05$, the conformal quantile $\hat{q}$ guarantees marginal coverage:
$$\mathbb{P}\left(y_{n+1} \in \left[\hat{y}(x_{n+1}) \pm \hat{q} \cdot \hat{\sigma}(x_{n+1})\right]\right) \ge 1 - \alpha$$
- **Hard Calibration Gate:** A model is classified as `UNCERTAINTY_CALIBRATED` if and only if empirical coverage on the validation set satisfies $|\text{Coverage} - 0.95| \le 0.08$. Otherwise, it is strictly tagged `UNCERTAINTY_NOT_CALIBRATED`.

---

## 5. Active Learning Loop & Experiment Registry

1. **Candidate Pool Generation:** High-density parameter sweep over Reynolds number, angle of attack, and candidate airfoil geometries.
2. **Composite Acquisition Score:**
   $$\text{Score}(x) = w_u \cdot \tilde{\sigma}(x) + w_d \cdot \tilde{d}_{\text{OOD}}(x) + w_v \cdot \tilde{\text{Div}}(x)$$
3. **Case Staging:** Top-ranked candidates generate complete OpenFOAM case decks in `data/cases/staged/` with complete boundary dictionaries and `Allrun` scripts.
4. **Fail-Closed Execution Gate:** Probing solver status returns `USER_EXECUTED_REQUIRED` with solver status `SOLVER_UNAVAILABLE`. The active learning loop halts at the acquisition gate with zero fabricated results.
5. **Persistent Experiment Registry:** Every run is assigned an immutable ID (`AASI-P20-EXP-XXX`) stored in `data/experiments/registry.json`.

---

## 6. Scientific Model Promotion Hierarchy

A model cannot skip stages or achieve verified status without satisfying every prerequisite:
$$\text{TRAINED} \longrightarrow \text{PHYSICS\_VALIDATED} \longrightarrow \text{REPRODUCIBLE} \longrightarrow \text{OOD\_EVALUATED} \longrightarrow \text{UNCERTAINTY\_AUDITED} \longrightarrow \text{SCIENTIFICALLY\_VERIFIED}$$
Models with uncalibrated uncertainty or failing OOD performance remain locked as `TRAINED_UNVERIFIED` or `PARTIALLY_VALIDATED`.
