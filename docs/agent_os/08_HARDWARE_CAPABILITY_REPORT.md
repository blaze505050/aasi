# AASI 2.0 — 08. Hardware Capability Report

**Host Detection Timestamp**: 2026-10-25 02:00 UTC  
**Detection Engine**: `backend/governor/resource_monitor.py` & `runner/detector/capabilities.py`  
**Host Platform**: Microsoft Windows 11 AMD64 (build 10.0.26100)  
**Hostname**: `DESKTOP-F7IJ4EI`

---

## 1. Measured Physical Resources

| Hardware Dimension | Measured Value | Measurement Technique | Detection Confidence |
| :--- | :--- | :--- | :--- |
| **Logical CPU Cores** | 8 logical cores | `os.cpu_count()` | 100% Verified |
| **Physical CPU Cores** | 4 physical cores | Win32 Processor Discovery | 100% Verified |
| **Total Physical RAM** | 7.79 GB | `GlobalMemoryStatusEx` (`ctypes`) | 100% Verified |
| **Available RAM** | 0.40 – 0.85 GB (fluctuating) | `GlobalMemoryStatusEx` (`ctypes`) | 100% Verified |
| **Memory Pressure** | High (~89% used by OS/IDE/Browser)| `ullAvailPhys / ullTotalPhys` | 100% Verified |
| **Primary Workspace Disk** | 118.2 GB Total, 14.2 GB Free | `shutil.disk_usage` | 100% Verified |
| **GPU / CUDA Acceleration** | None (Integrated Display) | `torch.cuda` / `nvidia-smi` | 100% Verified (GPU Absent) |
| **Python Runtime** | Python 3.12.10 AMD64 | `sys.version` | 100% Verified |
| **WSL2 Availability** | Present (`wsl.exe` in PATH) | `shutil.which('wsl')` | 100% Verified |
| **Native OpenFOAM** | Not in Windows PATH | Binary executable search | 100% Verified |
| **OpenFOAM via WSL2** | Supported via WSL container | `wsl which simpleFoam` | Staged Capability |

---

## 2. Operational Constraints on this Workstation

1. **Memory Budget**: With ~400 MB to 800 MB free RAM, heavy 3D RANS mesh generation and in-memory deep neural operators must NOT run locally without pagination. All tasks default to a safe per-task RAM budget of **250 MB**.
2. **Compute Routing**:
   - Analytical panel methods, VLM 3D aerodynamics, and surrogate inference execute **locally** ($< 50$ ms latency).
   - High-cell OpenFOAM RANS CFD ($> 500,000$ cells) is routed to **Colab** or remote HPC packaging.
