# AASI Phase 19: Hardware & Execution Environment Specification

## 1. System Hardware & Host Platform
- **Operating System:** Microsoft Windows 11 Home / Pro (Build 10.0.26200-SP0, 64-bit AMD64)
- **Host Architecture:** x86_64 / AMD64
- **Physical Memory (RAM):**
  - Total Visible RAM: 8,165,168 KB (~7.78 GiB / 8.16 GB)
  - Free Physical Memory: ~520 MB – 1.0 GB (dynamically managed by Windows OS)
  - Memory Management Rule: Tensor allocations exceeding available memory are rejected to prevent OS kernel paging.
- **Storage Subsystem:**
  - Total Storage Capacity: 118.28 GB
  - Used Storage: 94.73 GB
  - Available Free Storage: **23.55 GB**
  - **Hardware Safety Reserve Gate:** Minimum 15.00 GB mandatory reserve enforced at all times.
  - Usable Working Buffer: **8.55 GB** maximum allowable working dataset footprint. Datasets exceeding this threshold (e.g. raw 24.5 GB AirfRANS or 18.2 GB CRM) are classified as `RESOURCE_LIMITED` and rejected from uncompressed download.
- **Graphics & Accelerated Compute:**
  - Video Controller: Intel(R) UHD Graphics (Driver 27.20.100.8935)
  - Dedicated VRAM: 1,073,741,824 bytes (1.0 GB shared/system aperture)
  - Discrete NVIDIA CUDA GPU: **None detected on local host**.
  - Compute Execution Mode: **Pure CPU Vectorized Execution**.

---

## 2. Software Runtime & Scientific Toolchain
- **Python Runtime:** Python 3.12.10 (AMD64, MSC v.1943 64-bit)
- **Virtual Environment:** Dedicated local venv at `c:\Users\ADITYA\Desktop\AASI\.venv`
- **Numerical Core Libraries:**
  - `numpy`: Version 2.5.3 (Vectorized linear algebra, BLAS/LAPACK)
  - `scipy`: Version 1.18.1 (Optimization, spatial Kd-trees, interpolation)
  - `scikit-learn`: Version 1.9.0 (Regularized Ridge regression, standard scalers, conformal metrics)
- **Deep Learning Framework (PyTorch):**
  - Status: Library present on disk, but native `c10.dll` fails to load due to missing Visual C++ Redistributable runtime.
  - Fail-Closed Policy: Deep neural operator training defaults to `RESOURCE_LIMITED` / `SCAFFOLD`, while the CPU Physics-AI surrogate engine operates via exact analytical Ridge / Polynomial ML models with guaranteed numerical determinism.
- **CFD Solvers (OpenFOAM / simpleFoam):**
  - Windows PATH: `simpleFoam.exe` **Not Found**.
  - WSL2 Environment: WSL executable detected (`wsl.exe`), but distribution disk (`ext4.vhdx`) is unmounted/detached.
  - CFD Execution Policy: AASI generates complete, bit-for-bit reproducible OpenFOAM case decks (`0/`, `constant/`, `system/`, `Allrun`), returning `USER_EXECUTED_REQUIRED` with complete instructions rather than fabricating CFD coefficients.

---

## 3. Version Control & Cryptographic Provenance
- **Git Repository:** `https://github.com/blaze505050/aasi.git`
- **Active Branch:** `main`
- **Baseline Commit:** `c14017aea16b685a2a4e83c8e92afb3b29acf418`
- **Digest Algorithm:** Standard SHA-256 (256-bit cryptographic digest) across all manifests, weights, cases, and logs.
