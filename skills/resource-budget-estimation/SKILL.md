---
name: resource-budget-estimation
version: 2.0.0
description: A priori physics-informed estimation of CPU, RAM, disk, and wall-time requirements for engineering jobs before execution.
triggers:
  - "estimate resource budget"
  - "compute cost estimation"
  - "check solver feasibility"
preconditions:
  - Task specifications including mesh cell count, domain dimensions, Reynolds number, and solver type
permitted_tools:
  - inspect_hardware
required_inputs:
  solver_type: string
  mesh_cell_count: integer
  iterations: integer
  hardware_profile: object
output_schema:
  estimated_ram_mb: float
  estimated_cpu_time_sec: float
  estimated_disk_mb: float
  execution_target: string
  within_budget: boolean
resource_estimate:
  ram_mb: 24
  wall_time_seconds: 2
---

# Resource Budget Estimation Skill

## Purpose
Prevents host system crashes and out-of-memory (OOM) lockups by calculating empirical and analytical upper bounds for computational requirements before launching tasks. Enforces fail-closed routing between local execution, WSL, Colab, or remote HPC.

## Execution Procedure
1. Extract numerical parameters from task request:
   - 2D Panel / discrete vortex: $\sim 50$ MB RAM, $< 1$ s CPU.
   - 3D VLM / Helmbold: $\sim 120$ MB RAM, $< 5$ s CPU.
   - 2D OpenFOAM / RANS: $\sim 1.5$ KB RAM per cell; 200k cells $\rightarrow \sim 300$ MB RAM, $\sim 300$ s CPU.
   - 3D CFD / Large mesh: $> 1$ GB RAM per 1M cells; exceeds workstation safety envelope.
2. Probe current host headroom via `ResourceMonitor`.
3. Apply safety factor ($1.5\times$ memory, $2.0\times$ wall time).
4. Evaluate routing decision:
   - If estimated RAM + safety reserve $\le$ host available RAM: Assign `ALLOWED_LOCAL`.
   - If estimated RAM exceeds host envelope but matches Colab GPU/CPU profile: Route to `COLAB_USER_EXECUTED` and generate self-contained bundle.
   - If memory is unpredictable: Flag as `REQUIRES_APPROVAL`.

## Safety Constraints
- If host available RAM $< 200$ MB, unconditionally reject local execution.
- CPU time limits are enforced by external watchdog timers, not cooperative subroutines alone.
