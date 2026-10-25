# AASI 2.0 — 09. Runtime Budget Policy

**Policy Version**: 2.0.0  
**Enforcement Authority**: `backend.governor.SafetyGovernor` & `backend.governor.ResourceBudget`

---

## 1. Workstation Resource Allocation Quotas

To prevent operating system instability, browser tab termination, or OOM exceptions on development workstations, the following conservative limits are enforced:

```
                    TOTAL WORKSTATION RAM: 7.8 GB
┌─────────────────────────────────────────────────────────────┬───────────┐
│ Windows OS + Antigravity IDE + Browser + Background Tasks   │ AASI Task │
│ (Reserved Baseline: ~7.5 GB)                                │ (<=250MB) │
└─────────────────────────────────────────────────────────────┴───────────┘
                                ▲
                   CRITICAL RESERVE FLOOR: 200 MB
```

| Resource Category | Default Task Budget | Hard Max Ceiling | Critical Reserve Floor |
| :--- | :--- | :--- | :--- |
| **Task Wall-Clock Duration** | 300 seconds (5 min) | 3,600 seconds (1 hour) | Immediate timeout termination |
| **Task CPU Utilization** | 85.0% maximum | 95.0% | 98.0% sustained halts new tasks |
| **Task RAM Allocation** | 0.25 GB (250 MB) | 2.0 GB (configured) | 0.20 GB (200 MB) refuses new tasks |
| **Task Disk Space** | 1.0 GB | 5.0 GB | 1.0 GB free refuses write operations |
| **Task GPU VRAM** | 0.0 GB (CPU only) | Host GPU VRAM | 10% VRAM free floor |
| **Max Concurrent Tasks** | 2 parallel jobs | 4 parallel jobs | Queue or reject |

---

## 2. Dynamic Execution States

Every requested agent action is evaluated into one of 6 formal governance states:

1. `ALLOWED_LOCAL`: Resource request is within bounds and verified headroom exists.
2. `ALLOWED_RESTRICTED`: Action is permitted with scoped filesystem sandbox and CPU throttling.
3. `REQUIRES_APPROVAL`: Action involves high compute ($> 2$ GB RAM), external network access, or modified files.
4. `ROUTE_REMOTE`: Task exceeds local capacity (e.g. 3D viscous mesh generation) and is packaged for Colab / remote HPC.
5. `BLOCKED_BY_POLICY`: Action violates security allowlists, executes dangerous patterns, or kill switch is active.
6. `UNKNOWN_CAPABILITY`: Resource requirement cannot be evaluated; fails closed by default.
