"""
AASI Milestone 2: Deterministic Compute Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Routes computational cases to LOCAL, COLAB, REMOTE_FUTURE, or UNAVAILABLE
based on deterministic resource estimates and detected workstation capabilities.
Explicitly avoids claiming exact runtime predictions.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from runner.protocol.models import RunnerCapabilities
from runner.detector.capabilities import HostCapabilityDetector

logger = logging.getLogger("aasi.compute.router")


class ComputeDestination(str, Enum):
    LOCAL = "LOCAL"
    COLAB = "COLAB"
    REMOTE_FUTURE = "REMOTE_FUTURE"
    UNAVAILABLE = "UNAVAILABLE"


class ComputeRequirements(BaseModel):
    """Case specifications for compute routing."""
    case_id: str
    solver: str = "simpleFoam"
    estimated_cells: int = 100_000
    timestep_count: int = 1000
    memory_gb: Optional[float] = None
    parallelism: int = 1
    dimension: str = "2D"  # "2D" or "3D"
    requires_cuda: bool = False


class RoutingAudit(BaseModel):
    """Detailed deterministic audit checkpoints."""
    estimated_memory_gb: float
    local_solver_available: bool
    local_ram_sufficient: bool
    local_cores_sufficient: bool
    local_mpi_sufficient: bool
    colab_cells_sufficient: bool
    colab_ram_sufficient: bool
    safe_local_cell_ceiling: int


class ComputeRouterDecision(BaseModel):
    """Deterministic routing verdict with scientific justification."""
    destination: ComputeDestination
    recommended_backend: str
    reason: str
    explanation: str
    estimated_regime: str
    runtime_prediction_disclaimer: str = (
        "Exact wall-clock runtime cannot be predicted deterministically without iterative convergence history. "
        "Order-of-magnitude regime provided based on cell count and solver complexity."
    )
    audit: RoutingAudit
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DeterministicComputeRouter:
    """
    Evaluates simulation requirements against host workstation resources
    and routes fail-closed without fabricating capabilities.
    """

    KNOWN_SOLVERS = {
        "simplefoam", "pimplefoam", "rhosimplefoam", "icofoam",
        "scalarptransportfoam", "potentialfoam", "blockmesh",
        "snappyhexmesh", "checkmesh", "foamtovtk"
    }

    # Bounds for Google Colab Free Tier
    COLAB_MAX_CELLS = 1_500_000
    COLAB_MAX_RAM_GB = 10.0
    COLAB_MAX_CORES = 2

    @classmethod
    def estimate_memory_gb(cls, cells: int, dimension: str = "2D") -> float:
        """
        Estimates OpenFOAM memory footprint deterministically:
        Base solver overhead = 0.4 GB
        2D RANS: ~0.35 GB per 100,000 cells
        3D RANS: ~0.75 GB per 100,000 cells
        """
        base_overhead = 0.4
        rate = 0.75 if dimension.upper() == "3D" else 0.35
        needed = base_overhead + (cells / 100_000.0) * rate
        return round(needed, 2)

    @classmethod
    def classify_regime(cls, cells: int, timesteps: int, dimension: str) -> str:
        """Classifies workload into an order-of-magnitude execution regime."""
        total_operations = cells * timesteps
        if dimension.upper() == "3D" or total_operations > 500_000_000:
            return "HEAVY_CLUSTER_REGIME (> 1 hour, multi-core/HPC required)"
        elif total_operations > 100_000_000:
            return "EXTENDED_REGIME (approx 15-45 minutes)"
        elif total_operations > 20_000_000:
            return "MODERATE_REGIME (approx 5-15 minutes)"
        else:
            return "RAPID_REGIME (< 5 minutes)"

    @classmethod
    def route(
        cls,
        requirements: ComputeRequirements,
        capabilities: Optional[RunnerCapabilities] = None,
    ) -> ComputeRouterDecision:
        """
        Deterministically evaluates requirements against capabilities.
        """
        caps = capabilities or HostCapabilityDetector.detect()

        # 1. Parameter sanity check
        solver_norm = requirements.solver.strip().lower()
        if (
            requirements.estimated_cells <= 0
            or requirements.timestep_count <= 0
            or requirements.parallelism <= 0
            or solver_norm not in cls.KNOWN_SOLVERS
        ):
            audit = RoutingAudit(
                estimated_memory_gb=0.0,
                local_solver_available=False,
                local_ram_sufficient=False,
                local_cores_sufficient=False,
                local_mpi_sufficient=False,
                colab_cells_sufficient=False,
                colab_ram_sufficient=False,
                safe_local_cell_ceiling=0,
            )
            reason = f"Invalid or unrecognized simulation parameters: solver='{requirements.solver}', cells={requirements.estimated_cells}."
            return ComputeRouterDecision(
                destination=ComputeDestination.UNAVAILABLE,
                recommended_backend="NONE",
                reason=reason,
                explanation="Parameters violate physical or numerical bounds. Execution cannot be scheduled.",
                estimated_regime="UNAVAILABLE",
                audit=audit,
            )

        # 2. Memory requirement estimation
        est_ram = requirements.memory_gb or cls.estimate_memory_gb(
            requirements.estimated_cells, requirements.dimension
        )

        # 3. Determine safe local ceiling based on physical hardware
        if caps.ram_total_gb <= 10.0 or caps.cpu_cores_logical <= 4:
            safe_cells = 60_000
        elif caps.ram_total_gb <= 16.0:
            safe_cells = 250_000
        elif caps.ram_total_gb <= 32.0:
            safe_cells = 1_000_000
        else:
            safe_cells = 3_000_000

        # Check local constraints
        solver_local = caps.openfoam_available or any(
            s.lower() == solver_norm for s in caps.supported_solvers
        )
        # Use available RAM with 15% safety buffer
        ram_ok_local = est_ram <= (caps.ram_available_gb * 0.85)
        cores_ok_local = requirements.parallelism <= caps.cpu_cores_logical
        mpi_ok_local = (requirements.parallelism == 1) or caps.has_mpi
        cuda_ok_local = (not requirements.requires_cuda) or caps.has_cuda
        is_3d = requirements.dimension.upper() == "3D"

        # Colab constraints
        colab_cells_ok = requirements.estimated_cells <= cls.COLAB_MAX_CELLS
        colab_ram_ok = est_ram <= cls.COLAB_MAX_RAM_GB

        regime = cls.classify_regime(
            requirements.estimated_cells,
            requirements.timestep_count,
            requirements.dimension,
        )

        audit = RoutingAudit(
            estimated_memory_gb=est_ram,
            local_solver_available=solver_local,
            local_ram_sufficient=ram_ok_local,
            local_cores_sufficient=cores_ok_local,
            local_mpi_sufficient=mpi_ok_local,
            colab_cells_sufficient=colab_cells_ok,
            colab_ram_sufficient=colab_ram_ok,
            safe_local_cell_ceiling=safe_cells,
        )

        # 4. Routing Decision Hierarchy

        # Branch A: Massive 3D or massive mesh exceeding Colab free tier -> REMOTE_FUTURE
        if requirements.estimated_cells > cls.COLAB_MAX_CELLS or est_ram > cls.COLAB_MAX_RAM_GB or (is_3d and requirements.estimated_cells > 500_000):
            return ComputeRouterDecision(
                destination=ComputeDestination.REMOTE_FUTURE,
                recommended_backend="REMOTE_HPC_SLURM",
                reason=(
                    f"Workload ({requirements.estimated_cells:,} cells, {est_ram:.1f} GB RAM) "
                    f"exceeds both local workstation and Colab free-tier capacity."
                ),
                explanation=(
                    f"High-fidelity {requirements.dimension} simulation requires dedicated multi-node cluster resources. "
                    f"Free-tier limits ({cls.COLAB_MAX_CELLS:,} cells, {cls.COLAB_MAX_RAM_GB} GB RAM) are exceeded. "
                    f"Scheduled for remote Slurm HPC cluster backend."
                ),
                estimated_regime=regime,
                audit=audit,
            )

        # Branch B: Workstation is equipped, has solver, and sufficient headroom -> LOCAL
        if (
            solver_local
            and ram_ok_local
            and cores_ok_local
            and mpi_ok_local
            and cuda_ok_local
            and requirements.estimated_cells <= safe_cells
            and not (is_3d and caps.ram_total_gb < 16.0)
        ):
            return ComputeRouterDecision(
                destination=ComputeDestination.LOCAL,
                recommended_backend="LOCAL_OPENFOAM_RUNNER",
                reason=(
                    f"Workstation has native solver '{requirements.solver}', sufficient memory "
                    f"({est_ram:.1f} GB required vs {caps.ram_available_gb:.1f} GB available), "
                    f"and mesh ({requirements.estimated_cells:,} cells) is within the safe local ceiling ({safe_cells:,})."
                ),
                explanation=(
                    f"Local execution selected via explicitly installed Local Runner. "
                    f"Host provides {caps.cpu_cores_logical} CPU cores and {caps.ram_total_gb:.1f} GB total RAM. "
                    f"Estimated memory footprint ({est_ram:.1f} GB) leaves safe OS buffer."
                ),
                estimated_regime=regime,
                audit=audit,
            )

        # Branch C: Local is missing solver or lacks memory, but fits Colab -> COLAB
        if colab_cells_ok and colab_ram_ok:
            reasons = []
            if not solver_local:
                reasons.append(f"local workstation lacks native OpenFOAM binary '{requirements.solver}'")
            if not ram_ok_local:
                reasons.append(f"required RAM ({est_ram:.1f} GB) exceeds safe local available memory ({caps.ram_available_gb:.1f} GB)")
            if requirements.estimated_cells > safe_cells:
                reasons.append(f"cell count ({requirements.estimated_cells:,}) exceeds workstation safe limit ({safe_cells:,})")
            if is_3d and caps.ram_total_gb < 16.0:
                reasons.append("3D simulation requires minimum 16 GB workstation RAM")

            reason_str = "; ".join(reasons) if reasons else "Colab selected as optimal free compute destination"

            return ComputeRouterDecision(
                destination=ComputeDestination.COLAB,
                recommended_backend="GOOGLE_COLAB_NOTEBOOK",
                reason=f"Routed to Colab fallback because {reason_str}.",
                explanation=(
                    f"Workload ({requirements.estimated_cells:,} cells, {est_ram:.1f} GB RAM) fits within "
                    f"Google Colab free-tier environment (~12.7 GB RAM, 2 vCPUs). "
                    f"A reproducible, signed Colab notebook will be staged for external execution."
                ),
                estimated_regime=regime,
                audit=audit,
            )

        # Fallback Branch: REMOTE_FUTURE
        return ComputeRouterDecision(
            destination=ComputeDestination.REMOTE_FUTURE,
            recommended_backend="REMOTE_HPC_SLURM",
            reason="Workload requirements exceed local workstation and standard cloud container constraints.",
            explanation="Requires distributed memory MPI or dedicated GPU cluster.",
            estimated_regime=regime,
            audit=audit,
        )


# Convenient alias
compute_router = DeterministicComputeRouter
