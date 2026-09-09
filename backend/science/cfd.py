"""CFD database cataloging benchmark and locally solved computational fluid dynamics solutions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .models import EpistemicStatus, ScientificResult


class CFDRecord(BaseModel):
    """Detailed metadata and integrated forces for a CFD simulation solution."""
    case_id: str = Field(..., description="Unique CFD case identifier")
    case_name: str = Field(..., description="Descriptive case name")
    geometry: str = Field(..., description="Geometry model e.g. NACA 0012")
    solver: str = Field(..., description="CFD solver e.g. OpenFOAM v2312, SU2 v7.5")
    solver_version: str = Field("v2312", description="Exact version string")
    mesh_type: str = Field("Structured C-grid", description="Mesh topology")
    cell_count: int = Field(..., description="Total cell or element count")
    dimensionality: str = Field("2D", description="2D, Axisymmetric, or 3D")
    turbulence_model: str = Field("k-omega SST", description="Turbulence closure model")
    wall_treatment: str = Field("Wall-resolved (y+ < 1)", description="Near-wall treatment")
    y_plus_max: float = Field(0.85, description="Maximum wall y+ value")
    mach: float = Field(..., description="Freestream Mach number")
    reynolds: float = Field(..., description="Chord-based Reynolds number")
    aoa_deg: float = Field(..., description="Angle of attack in degrees")
    boundary_conditions: Dict[str, Any] = Field(default_factory=dict, description="Inlet, outlet, wall boundary conditions")
    convergence_criteria: str = Field("Residuals < 1e-6", description="Convergence stopping criteria")
    residual_history: Dict[str, float] = Field(default_factory=dict, description="Final residual values for p, U, k, omega")
    discretization_schemes: Dict[str, str] = Field(default_factory=dict, description="Spatial and temporal discretization")
    cl: float = Field(..., description="Integrated lift coefficient")
    cd: float = Field(..., description="Integrated drag coefficient")
    cm: float = Field(..., description="Quarter-chord pitching moment coefficient")
    uncertainty: Dict[str, float] = Field(default_factory=dict, description="Numerical discretization uncertainty")
    mesh_checksum: str = Field("sha256-mesh", description="SHA-256 of mesh files")
    case_checksum: str = Field("sha256-case", description="SHA-256 of case dictionaries")
    result_checksum: str = Field("sha256-result", description="SHA-256 of output solution fields")
    epistemic_status: EpistemicStatus = Field(EpistemicStatus.VALIDATED_CFD, description="OFFICIAL_CFD, VALIDATED_CFD, LOCAL_CFD, UNVALIDATED_CFD")
    validation_status: str = Field("VALIDATED", description="VALIDATED, BENCHMARK, UNVALIDATED")
    source: str = Field("AASI Open Aerodynamics Benchmark Catalog", description="Authoritative creator or source")
    citation: str = Field("", description="Citation or benchmark reference")


class CFDDatabase:
    """Registry managing benchmark and verified CFD simulation cases."""

    def __init__(self):
        self._records: Dict[str, CFDRecord] = {}

    def register(self, record: CFDRecord):
        """Register a CFD record."""
        self._records[record.case_id] = record

    def get(self, case_id: str) -> Optional[CFDRecord]:
        """Retrieve CFD record by ID."""
        return self._records.get(case_id)

    def list_records(self, geometry: Optional[str] = None) -> List[CFDRecord]:
        """List CFD records with optional geometry filter."""
        res = list(self._records.values())
        if geometry:
            clean_geo = geometry.replace(" ", "").replace("-", "").lower()
            res = [r for r in res if clean_geo in r.geometry.replace(" ", "").replace("-", "").lower()]
        return res

    def query_solution(
        self,
        geometry: str,
        mach: Optional[float] = None,
        reynolds: Optional[float] = None,
        aoa_deg: Optional[float] = None,
        target_variable: str = "CD",
        tolerance_mach: float = 0.05,
        tolerance_reynolds_rel: float = 0.25,
        tolerance_aoa: float = 0.5,
    ) -> List[ScientificResult]:
        """Search CFD database for converged simulations matching flight conditions."""
        results: List[ScientificResult] = []
        clean_target_geo = geometry.replace(" ", "").replace("-", "").lower()

        for case_id, rec in self._records.items():
            rec_geo = rec.geometry.replace(" ", "").replace("-", "").lower()
            if clean_target_geo not in rec_geo and rec_geo not in clean_target_geo:
                continue

            if mach is not None and abs(rec.mach - mach) > tolerance_mach:
                continue

            if reynolds is not None:
                rel_diff = abs(rec.reynolds - reynolds) / reynolds
                if rel_diff > tolerance_reynolds_rel:
                    continue

            if aoa_deg is not None and abs(rec.aoa_deg - aoa_deg) > tolerance_aoa:
                continue

            # Case matches conditions
            var_key = target_variable.upper()
            val = rec.cd if var_key == "CD" else (rec.cl if var_key == "CL" else (rec.cm if var_key == "CM" else None))
            if val is not None:
                unc_val = rec.uncertainty.get(var_key.lower(), 0.0008)
                results.append(
                    ScientificResult(
                        result_id=f"CFD-{rec.case_id}",
                        epistemic_status=rec.epistemic_status,
                        quantity=target_variable,
                        value=float(val),
                        units="dimensionless",
                        uncertainty={target_variable.lower(): unc_val},
                        conditions={
                            "geometry": rec.geometry,
                            "mach": rec.mach,
                            "reynolds": rec.reynolds,
                            "aoa_deg": rec.aoa_deg,
                            "turbulence_model": rec.turbulence_model,
                            "cell_count": rec.cell_count,
                            "y_plus": rec.y_plus_max,
                        },
                        source=rec.source,
                        provenance={
                            "solver": rec.solver,
                            "solver_version": rec.solver_version,
                            "mesh_type": rec.mesh_type,
                            "case_checksum": rec.case_checksum,
                            "result_checksum": rec.result_checksum,
                            "citation": rec.citation,
                        },
                        confidence=0.92,
                        method=f"CFD RANS Simulation ({rec.solver}, {rec.turbulence_model})",
                        validation_status=rec.validation_status,
                        notes=[
                            f"Mesh: {rec.mesh_type} ({rec.cell_count:,} cells, y+ < {rec.y_plus_max}).",
                            f"Convergence: {rec.convergence_criteria}.",
                        ],
                    )
                )

        return results
