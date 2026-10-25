---
name: hardware-capability-audit
version: 2.0.0
description: Discovers workstation CPU, RAM, disk, GPU VRAM, and runtime solvers safely.
triggers:
  - "audit hardware"
  - "discover system capabilities"
preconditions:
  - Host operating system detectable
permitted_tools:
  - resource_sampler
  - discovery_probe
required_inputs:
  workspace_path: string
output_schema:
  cpu_cores: integer
  ram_total_gb: float
  ram_available_gb: float
  gpu_available: boolean
resource_estimate:
  ram_mb: 32
  wall_time_seconds: 5
---

# Hardware Capability Audit Skill

## Purpose
Collects verifiable physical and runtime telemetry using safe, read-only system queries. Never elevates privileges or changes system settings.

## Execution Procedure
1. Query logical and physical CPU cores.
2. Probe total and available physical RAM via ctypes `GlobalMemoryStatusEx` or Linux `/proc/meminfo`.
3. Audit workspace disk free space.
4. Check for presence of CUDA devices and OpenFOAM binaries.
