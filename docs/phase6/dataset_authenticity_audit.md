# Dataset Authenticity Audit Report

## Audit Scope & Principles

AASI enforces an explicit rule: **Never claim a dataset is verified unless its raw data payload is physically present on local disk, fully validated against schema specifications, and compliant with fluid dynamics sanity bounds.**

The audit inspects:
1. Physical existence of directory and files (`.json`, `.csv`, `.dat`)
2. Total file sizes in bytes
3. Schema conformance and absence of NaN / Inf tokens
4. Physical aerodynamic plausibility bounds ($-3.0 \le C_L \le 3.5$, $0.001 \le C_D \le 1.0$)
5. Licensing declarations vs actual access rights.

---

## Repository Audit Findings

Audit Timestamp: `2026-09-10T12:49:31Z`  
Audit Engine: `backend.datasets.audit.DatasetAuditService`

| Dataset ID | Classification | Local Files | Actual Samples | Declared Samples | Physical Status | Audit Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`DATASET-AUTHENTIC-AIRFOILS-V1`** | `VERIFIED` | 2 JSON files (176.8 KB) | 1,008 | 1,008 | `VALID` | 7 distinct geometries (NACA 0012, 0009, 0006, 2412, 4412, Clark Y, RAE 2822). Authentic experimental & CFD polars across Mach 0.1–0.3, Re $10^6 - 3\times 10^6$, $\alpha \in [-6^\circ, 16^\circ]$. Zero NaNs. |
| **`DATASET-AIRFRANS-1K`** | `METADATA_ONLY` | Absent locally | 0 | 1,000 | `NOT_DOWNLOADED` | Declared in catalog manifest with download URL and license, but raw 1,000-mesh CFD dataset is not downloaded to local development disk to conserve workstation quota. |
| **`NASA-CRM`** | `METADATA_ONLY` | Absent locally | 0 | 450 | `NOT_DOWNLOADED` | Transonic Common Research Model wing-body benchmark manifest registered; raw volumetric meshes not downloaded. |
| **`NACA-TR-824`** | `METADATA_ONLY` | Absent locally | 0 | 800 | `NOT_DOWNLOADED` | Summary of Airfoil Data (Abbott & von Doenhoff) digitized wind tunnel polars cataloged; full digitized tables pending local mirror. |

---

## Summary Statistics

- **Total Registered Manifests Audited:** 4
- **Physically Verified Datasets on Disk:** 1 (`DATASET-AUTHENTIC-AIRFOILS-V1`)
- **Metadata-Only Registrations:** 3
- **Demo / Synthetic Payloads:** 0
- **Invalid / Corrupted Payloads:** 0
- **Unavailable / Broken Sources:** 0

---

## Audit Verification Commands

```powershell
# Run programmatic dataset audit:
.\.venv\Scripts\python.exe -c "from backend.datasets.audit import DatasetAuditService; s = DatasetAuditService().audit_all(); print('Verified:', s.verified_count, 'Metadata Only:', s.metadata_only_count)"

# Run automated audit test:
.\.venv\Scripts\python.exe -m pytest tests/test_dataset_audit.py -v
```
