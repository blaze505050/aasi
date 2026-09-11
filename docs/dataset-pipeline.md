# AASI Reproducible Dataset Pipeline

## 1. Architectural Overview & Workflow

The AASI Dataset Pipeline transforms raw, external aerospace measurements and simulation polars into structured, immutable, and leak-free machine learning datasets.

```text
RAW SOURCE (UIUC / NASA TMR / User OpenFOAM)
    │
    ▼
PRE-FLIGHT DISK CHECK & USER QUOTA AUDIT
    │
    ▼
DOWNLOAD & CRYPTOGRAPHIC SHA-256 VALIDATION
    │
    ▼
AUTHENTIC PARSING (Selig / Lednicer / TMR Formats)
    │
    ▼
PHYSICAL & GEOMETRIC NORMALIZATION (Chord = 1.0, Alpha Deg)
    │
    ▼
AUTOMATED QUALITY CONTROL (Positivity, Monotonicity, Outlier Filters)
    │
    ▼
GEOMETRY-LEVEL LEAKAGE-FREE GROUPING & SPLITTING
    │
    ▼
IMMUTABLE SIDECAR MANIFEST GENERATION (SHA-256, Conditions, License)
    │
    ▼
REGISTRATION IN MULTI-FIDELITY DATASET REGISTRY
```

---

## 2. Authentic Raw Parsers (`backend/datasets/authentic_parsers.py`)

AASI rejects synthetic or fabricated geometry files, implementing dedicated parsers for verified academic standards:

### A. UIUC Airfoil Parser (`UIUCAirfoilParser`)
- **Supported Formats:** Selig (continuous wrap from upper TE to lower TE) and Lednicer (explicit upper and lower surface tables).
- **Geometric Normalization:**
  - Automatic detection of leading edge ($x_{min}$) and trailing edge ($x_{max}$).
  - Chord normalization: $x \leftarrow \frac{x - x_{min}}{x_{max} - x_{min}}$.
  - Calculation of genuine aerodynamic geometric properties: maximum thickness ($t/c$) and maximum camber ($z_{cam}/c$) with chordwise station location.
- **Fail-Closed Guarantees:** Rejects coordinate sets with $< 10$ points, degenerate bounds ($x_{max} \le x_{min}$), or invalid numerical tokens.

### B. NASA Turbulence Modeling Resource Parser (`NASATMRParser`)
- **Coverage:** Official 2D RANS verification cases (NACA 0012, 2D Zero Pressure Gradient Flat Plate).
- **Reference Benchmarks:** Standardizes grid-converged $C_L$, $C_D$, $C_M$ benchmark values produced by verified codes (CFL3D, FUN3D) for model calibration.

---

## 3. Storage Status State Machine & Download Safety

To prevent developer workstation disk exhaustion, AASI introduces the `StorageStatus` state machine in `backend/datasets/models.py`:

| Storage Status | Definition | Operational Handling |
|:---|:---|:---|
| `AVAILABLE_LOCAL` | File resides on disk and matches registered SHA-256 checksum. | Can be parsed and used immediately for training or validation. |
| `AVAILABLE_REMOTE_DIRECT` | Public file available via direct HTTPS URL. | Pre-flight disk check executed (`shutil.disk_usage`); downloads only if within safety quota ($\le 500$ MB). |
| `AVAILABLE_REMOTE_MANUAL` | Proprietary or account-gated file (e.g. AIAA portal). | Requires manual user download and placement in `data/datasets/`. |
| `DEGRADED_SAMPLE_ONLY` | High-volume raw archive (e.g. 50 GB DNS run) truncated to representative polars. | Clearly flagged to prevent users assuming full-domain volumetric availability. |
| `MISSING_AUTHENTIC_SOURCE` | Reference metadata exists but authentic file is unavailable. | Inference and training fail closed; returns HTTP 503. |

### Pre-Flight Disk Safety Rules
- Minimum free disk headroom: **2.0 GB**.
- Maximum single download size on developer workstation: **500 MB**.
- If disk space is insufficient, the download manager halts with `HTTP 413 Payload Too Large` and diagnostic guidance.

---

## 4. Geometry-Level Leakage Prevention

In traditional machine learning, random train/test splits inadvertently assign different angles of attack ($\alpha = 4^\circ$ and $\alpha = 5^\circ$) of the *same airfoil geometry* across training and test sets, allowing neural networks to memorize geometry rather than learning physics.

AASI enforces **strict geometry-level partitioning**:
- All polars for a given airfoil geometry (e.g., NACA 0012) are assigned exclusively to either `TRAIN`, `VAL`, or `TEST`.
- Zero parameter leakage across geometric boundaries ensures genuine generalization to unseen airfoils.
