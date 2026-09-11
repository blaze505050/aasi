# AASI Scientific Integrity Framework

## 1. Executive Summary & Core Principle

The fundamental governing principle of AASI (Autonomous Aerospace Scientific Intelligence) is:

> **"AASI must never claim a capability that it does not actually possess. Build AASI as a scientific instrument, not a chatbot with aerospace branding."**

In computational aerospace engineering and space science, false confidence or silent fallbacks lead to catastrophic design failures. AASI replaces generative speculation with an **epistemically explicit, truth-preserving architecture** that fails closed when data, models, or solvers are missing, uncalibrated, or out-of-domain.

---

## 2. Epistemic Hierarchy of Truth

AASI categorizes all scientific claims, outputs, and retrieved data into an unambiguous hierarchy of truth. The system will never present a lower-tier prediction as if it were higher-tier evidence:

| Epistemic Status | Scientific Authority Level | Generation Source | Handling & Verification |
|:---|:---:|:---|:---|
| `EXPERIMENTAL` | Highest (Tier 1) | Calibrated wind tunnel / flight test data (e.g., NASA Langley, UIUC, DLR) | Backed by cryptographic checksums, Reynolds/Mach condition bounds, and peer-reviewed report IDs. |
| `CALCULATED` | Tier 2 | Exact analytical / closed-form formulas (SymPy, Pint, Astropy) | Independently recomputed with symbolic verification; relative numerical error reported. |
| `VALIDATED CFD` | Tier 3 | Grid-converged numerical solutions (ASME V&V 20 compliant) | Richardson extrapolation applied across 3 grids; $GCI_{fine} < 5\%$; asymptotic range confirmed. |
| `SURROGATE` | Tier 4 | Trained neural operators or polynomial response surfaces | Validated strictly within hypercube bounds; fails closed if invoked outside valid domain or without verified checkpoint. |
| `USER CFD` | Tier 5 | External user-executed simulation runs (`aasi_case/`) | Ingested via automated QC; residuals ($< 10^{-4}$), drag positivity ($C_D > 0$), and force stability audited. |
| `CURRENT INFORMATION` | Tier 6 | Fresh public announcements or regulatory filings | Declared with retrieval timestamp, age, source URI, and `is_live` boolean. |
| `STALE` | Tier 7 | Seed datasets or unrefreshed historical feeds | Explicitly flagged when last refresh exceeds TTL; never disguised as real-time. |
| `MODEL UNAVAILABLE` | Exception | Model architecture registered without trained weights | Returns HTTP 503; refuses inference rather than returning random noise or uncalibrated guesses. |
| `OUT OF DOMAIN` | Exception | Query parameters outside calibrated envelope | Rejects extrapolation; explains physical regime departure (e.g., transonic shock or post-stall separation). |

---

## 3. The 4 Dimensions of Scientific Correctness

When evaluating or generating results, AASI audits four distinct dimensions rather than collapsing confidence into a single subjective number:

### A. Mathematical Correctness
- **Definition:** SymPy-verified symbolic consistency and dimensional homogeneity.
- **Enforcement:** Units tracked using `pint` with dimensional invariants ($[L]/[T]$ for velocity, dimensionless $C_L$, $C_D$, $C_M$).
- **Status:** **[IMPLEMENTED & VERIFIED]** (`backend/physics/dimensional.py`, `backend/tools/units.py`).

### B. Numerical Correctness
- **Definition:** Discretization convergence, residual stability, and algorithmic reproducibility.
- **Enforcement:** ASME V&V 20 Roache Grid Convergence Index ($GCI$) across 3 grid refinements ($r_{21}, r_{32} \ge 1.3$).
- **Status:** **[IMPLEMENTED & VERIFIED]** (`backend/validation/grid_convergence.py`, `backend/compute/artifacts.py`).

### C. Physical Correctness
- **Definition:** Invariant physical constraints and boundary conditions.
- **Enforcement:** Drag non-negativity ($C_D > 0$), linear pre-stall lift slope monotonicity ($dC_L/d\alpha > 0$ for subsonic attached flow), sensible stall boundaries ($|C_L| \le 3.0$).
- **Status:** **[IMPLEMENTED & VERIFIED]** (`backend/physics/constraints.py`).

### D. Experimental & Model Agreement
- **Definition:** Quantified epistemic discrepancy between surrogate predictions and reference wind tunnel polars.
- **Enforcement:** Discrepancy analysis engine compares surrogate outputs against authentic UIUC/NASA datasets and explains aerodynamic physical root causes (boundary layer separation, shock formation).
- **Status:** **[IMPLEMENTED & VERIFIED]** (`backend/multifidelity/discrepancy.py`).

---

## 4. Operational Truth-Preserving Rules

1. **No Silent Fallbacks:** If a target variable (e.g., $C_D$) is requested from a model that only predicts $C_L$, the system returns an explicit error (`HTTP 422 Unprocessable Entity`) rather than substituting $C_L$ silently.
2. **Deterministic Checkpoint Integrity:** All model checkpoints must verify against their registered SHA-256 hash before loading into memory. If the hash does not match, inference fails closed.
3. **Transparent Provenance:** Every response identifies:
   - Primary data source (NASA, UIUC, AIAA)
   - Publication year and report identifier
   - Raw content hash
   - Exact physical conditions (Mach, Reynolds, AoA)
