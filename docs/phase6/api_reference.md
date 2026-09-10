# Phase 6 API Reference Manual

## Endpoints Summary

| Method | Route | Description | Request Payload | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/physics/aerodynamics/predict` | Single-point surrogate prediction with epistemic uncertainty | `AerodynamicPredictRequest` | `AerodynamicPrediction` |
| `POST` | `/api/physics/aerodynamics/polar` | Full polar sweep ($\alpha \in [\alpha_{start}, \alpha_{end}]$) | `AerodynamicPolarRequest` | Polar sweep curve & physical checks |
| `GET` | `/api/physics/aerodynamics/model-status` | Model architecture, checksum, parameters, validity envelope | None | Status dictionary |
| `GET` | `/api/physics/audit/datasets` | Audits local disk datasets (VERIFIED vs METADATA_ONLY) | None | `DatasetAuditSummary` |
| `POST` | `/api/validation/grid-convergence` | Calculates ASME V&V 20 observed order $p$, $f_{ext}$, GCI | `GCIRequest` | `GCIResult` |
| `GET` | `/api/validation/grid-convergence/benchmarks` | Returns verified reference multi-grid CFD benchmark | None | Benchmark dictionaries |

---

## Endpoint Details

### 1. `POST /api/physics/aerodynamics/predict`

**Request:**
```json
{
  "geometry": "naca0012",
  "mach": 0.2,
  "reynolds": 2000000.0,
  "aoa_deg": 4.0
}
```

**Response (200 OK):**
```json
{
  "model_id": "AERO_SURROGATE_V1",
  "model_version": "1.0.0",
  "geometry": "naca0012",
  "mach": 0.2,
  "reynolds": 2000000.0,
  "aoa_deg": 4.0,
  "cl": 0.4196,
  "cd": 0.00825,
  "cm": -0.0083,
  "domain_status": "IN_DOMAIN",
  "validation_status": "VALIDATED_ON_TEST_SET",
  "uncertainty": {
    "confidence_level": "HIGH",
    "confidence_score": 0.94,
    "ood_score": 0.58,
    "feature_distance": 0.72,
    "nearest_neighbor_density": 0.61,
    "cl_uncertainty": 0.015,
    "cd_uncertainty": 0.0012,
    "cm_uncertainty": 0.008
  },
  "physics_checks": {
    "drag_positive": true,
    "symmetry_satisfied": true,
    "cl_bounds_satisfied": true,
    "cd_bounds_satisfied": true
  },
  "provenance": {
    "sha256_checksum": "bc549596f676c5d336fe33333845c53c6d2c170bce2eb964516c51dc8f4ee433",
    "physics_valid": true
  }
}
```

---

### 2. `POST /api/physics/aerodynamics/polar`

**Request:**
```json
{
  "geometry": "naca0012",
  "mach": 0.2,
  "reynolds": 2000000.0,
  "aoa_start": -4.0,
  "aoa_end": 14.0,
  "aoa_step": 1.0
}
```

**Response (200 OK):**
Contains array of `points` with $C_L$, $C_D$, $C_M$, and `sweep_validation`:
```json
{
  "geometry": "naca0012",
  "sweep_validation": {
    "is_sweep_valid": true,
    "checks": {
      "lift_monotonicity": true,
      "drag_all_positive": true,
      "continuity_smoothness": true,
      "zero_lift_at_zero_aoa": true
    },
    "violations": []
  }
}
```

---

### 3. `POST /api/validation/grid-convergence`

**Request:**
```json
{
  "f1": 0.4285,
  "f2": 0.4210,
  "f3": 0.4070,
  "r21": 1.4142,
  "r32": 1.4142,
  "safety_factor": 1.25,
  "metric_name": "Lift Coefficient (CL)"
}
```

**Response (200 OK):**
```json
{
  "metric_name": "Lift Coefficient (CL)",
  "apparent_order_p": 1.801,
  "extrapolated_value": 0.4371,
  "approx_relative_error_pct": 1.7503,
  "gci_fine_pct": 2.5245,
  "gci_medium_pct": 4.6732,
  "asymptotic_ratio": 0.998,
  "is_in_asymptotic_range": true,
  "convergence_type": "MONOTONIC_CONVERGENCE"
}
```
