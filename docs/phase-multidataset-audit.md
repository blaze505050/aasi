# AASI Multi-Dataset Architecture & Migration Audit

## 1. Executive Summary & Audit Mandate
Governing Directive: **AASI Next Phase Master Engineering Directive: AirfRANS / Complete CFD Dataset Integration, Multi-Dataset Validation & Scientific Generalization.**

This audit provides a comprehensive pre-implementation inspection of the existing single-dataset, NACA 0012-centered architecture across:
- `backend/datasets/`
- `backend/physics/`
- `backend/research/`
- `backend/simulation/`

The audit identifies hard-coded assumptions, defines the general multi-dataset abstraction layer, establishes strict hardware and storage boundaries, and ensures zero regressions across the verified 352-test baseline.

---

## 2. Current Architecture vs. Multi-Dataset Target

| Architectural Subsystem | Current State (NACA 0012 Focus) | Scientific Limitation | Multi-Dataset Target State |
|---|---|---|---|
| **Dataset Manifest & Lifecycle** | Single `DatasetManifest` class, primarily tracking UIUC Selig `.dat` file and polar tables. | Storage status does not distinguish streaming, partial chunking, or hardware-limited states. | Unified `DatasetAdapter` protocol with `DatasetStorageState` (`METADATA_ONLY`, `PARTIAL`, `FULLY_INGESTED`, `RESOURCE_LIMITED`). |
| **Airfoil / Geometry Handling** | `UIUCAirfoilParser` and `NASATMRParser` in `authentic_parsers.py` handle discrete `.dat` coordinate files. | Cannot parse unstructured 2D/3D volume meshes, boundary-layer normals, wall distance fields, or procedural NACA generators. | Extensible geometry and mesh abstractions supporting procedural generators (NACA 4/5-digit), surface meshes, and field point clouds. |
| **Validation Framework** | `AerodynamicBenchmarkEngine` checks linear slope ($2\pi/\text{rad}$) and symmetry specifically for NACA 0012 at $Re = 3 \times 10^6$. | Inapplicable to asymmetric, high-camber, or variable Reynolds/Mach datasets like AirfRANS. | Dataset-aware `DatasetValidator` checking mesh sanity, field bounds, duplicate cases, NaN/Inf, and train/test geometry leakage. |
| **Split & Generalization** | Static splits (`GEOMETRY_LEVEL`, `CONDITION_LEVEL`) without OOD parameter tracking. | Models can receive essentially identical geometries under different IDs; cannot evaluate Reynolds or AoA extrapolation. | Formal `DataSplitManager` supporting official benchmark splits (`full_train`, `full_test`, `scarce_train`, `reynolds_test`, `aoa_test`) with strict 0% geometry leakage verification. |
| **Aerodynamic Benchmarking** | Hard-coded comparison against NACA 0012 experimental data (NASA TM-4083). | Cannot evaluate field predictions (velocity vector, pressure field, eddy viscosity) or arbitrary airfoils. | Multi-dataset `MultiDatasetBenchmarkEngine` comparing Reference Truth $\rightarrow$ Analytical Baseline $\rightarrow$ CFD Reference $\rightarrow$ ML Surrogate across dataset-appropriate metrics. |
| **Evidence Ledger DAG** | Rigid evidence types (`SURFACE_COORDINATES`, `POLAR_DATASET`). | Missing atomic types for multi-case datasets, OOD evaluation splits, and validation reports. | Expanded `EvidenceType` (`DATASET_CASE`, `DATASET_VALIDATION`, `OOD_EVALUATION`) with distinct package, file, and manifest hashes. |
| **Hardware & Storage Safety** | Assumes small file sizes (<10 MB). | Attempting to download or extract the 14 GB AirfRANS archive on a 20 GB free disk would crash the workstation. | Storage requirement estimator and disk quota guards preventing unconstrained multi-gigabyte downloads. |

---

## 3. Storage & Workstation Feasibility Analysis

```
Workstation Disk Inspection:
----------------------------------------------
Available Free Disk Space: 20.26 GB
AirfRANS Archive (Dataset.zip): ~14.0 GB (compressed)
AirfRANS Extracted Footprint:  >20.0 GB (uncompressed)
Required Download Buffer:     >34.0 GB (archive + extracted)
----------------------------------------------
FEASIBILITY VERDICT: BULK DOWNLOAD WILL EXHAUST DISK.
SAFE OPERATIONAL MODES ENFORCED:
  1. DATASET_METADATA_ONLY (1,000 cases, official NeurIPS splits, metadata index)
  2. DATASET_PARTIAL (sample cases for regression and unit validation)
  3. RESOURCE_LIMITED (marks bulk download/training as pending external compute)
```

---

## 4. Migration Plan & Preservation of Baseline
1. **Preserve NACA 0012 Benchmark**: The existing flagship research pipeline, ASME V&V 20 grid study, and 5-tier GUM uncertainty model remain 100% functional and tested.
2. **Backward-Compatible Models**: All additions to `DatasetManifest` and `ResearchRun` retain default values.
3. **No Fabricated Arrays**: Missing or unexecuted fields are never populated with zeros or synthetic approximations.
