# AASI Model Uncertainty Quantification & Epistemic Labeling

## Epistemic vs Aleatoric Uncertainty
In aerodynamic modeling, uncertainty arises from two distinct physical sources:
1. **Aleatoric Uncertainty (Data Noise / Environmental)**: Unavoidable variability arising from wind-tunnel turbulence intensity, surface roughness deviations, measurement sensor precision, or thermal fluctuations.
2. **Epistemic Uncertainty (Model Ignorance / Domain Shift)**: Lack of knowledge due to sparse training data, unrepresented geometries (e.g. sharp blunt edges), or unmodeled flow physics (e.g. transition, laminar separation bubbles, shock buffet).

AASI explicitly separates and quantifies epistemic and aleatoric uncertainty, displaying distinct confidence intervals and epistemological labels on every prediction.

---

## Capability Status Classification Matrix
| Mechanism | Classification | Implementation | Audit Test |
| :--- | :--- | :--- | :--- |
| **Epistemic Classification Tagger** | `REAL IMPLEMENTED` | Assigns verified tags (`SURROGATE — VERIFIED DOMAIN`, `SURROGATE — OOD WARNING`, `OUT OF DOMAIN`). | `test_ood_detection_tags_prediction_correctly` |
| **Distance-to-Training-Data (Mahalanobis)** | `REAL IMPLEMENTED` | Quantifies distance in normalized parameter space ($Re, AoA, t/c$). | Active (`backend/physics_ai/uncertainty.py`) |
| **Ensemble Disagreement Estimator** | `REAL IMPLEMENTED` | Computes inter-model variance $\sigma_{ens}^2$ across multi-seed surrogate ensemble. | Active (`backend/physics_ai/uncertainty.py`) |
| **Conformal Prediction Intervals** | `REAL IMPLEMENTED` | Provides finite-sample coverage guarantees ($1 - \alpha$) calibrated on validation split. | Active (`backend/physics_ai/uncertainty.py`) |
| **Uncalibrated Status Protection** | `REAL IMPLEMENTED` | Flags models without conformal calibration as `UNCERTAINTY_NOT_CALIBRATED`. | Active (`backend/physics_ai/uncertainty.py`) |

---

## Epistemic Tagging Hierarchy
When an inference request is processed by the AASI backend, the prediction is evaluated against three criteria:
1. Is the operating condition inside the convex hull of training conditions?
2. Is the airfoil shape within the geometric training distribution?
3. Does the ensemble disagreement $\sigma$ remain within calibrated bounds?

```
                     ┌───────────────────────────────────┐
                     │         Inference Request         │
                     │  (Airfoil Geometry, Mach, Re, AoA)│
                     └─────────────────┬─────────────────┘
                                       │
                      [Inside Convex Hull & Envelope?]
                                       ├──► NO  ──► Epistemic Tag: [OUT OF DOMAIN]
                                       │            Confidence: REDUCE TO ZERO
                                       │            Action: Recommend User-Executed CFD
                                       └──► YES
                                             │
                                  [Ensemble Sigma > Threshold?]
                                             ├──► YES ──► Epistemic Tag: [SURROGATE — OOD WARNING]
                                             │            Warning: High Model Disagreement
                                             └──► NO
                                                   │
                                     [Conformal Calibrated?]
                                                   ├──► NO  ──► Epistemic Tag: [SURROGATE — HIGH UNCERTAINTY]
                                                   │            Status: UNCERTAINTY_NOT_CALIBRATED
                                                   └──► YES ──► Epistemic Tag: [SURROGATE — VERIFIED DOMAIN]
                                                                Status: CALIBRATED (95% Coverage Interval)
```

---

## Calibration Integrity & Fail-Closed Behavior
- Surrogates evaluated without empirical calibration sets MUST NOT present tight confidence intervals.
- The UI displays explicit interval bounds: $C_L \pm 1.96 \sigma$.
- If operating in an uncalibrated regime, the tag `UNCERTAINTY_NOT_CALIBRATED` is permanently affixed to the response payload and visualized in amber/orange in the UI.
