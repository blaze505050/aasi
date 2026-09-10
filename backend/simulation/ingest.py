"""
AASI Multi-Format Simulation Artifact Ingestion Service.

Parses simulation results from OpenFOAM, SU2, XFOIL, and generic tabular formats,
applies automated quality control, and produces immutable MultiFidelityResult records.
"""

import os
import re
import csv
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from backend.multifidelity.models import (
    MultiFidelityResult,
    FidelityLevel,
    CFDQualityClassification,
    FlowConditions,
)
from backend.simulation.quality_control import CFDQualityControlEngine


class SimulationIngestionService:
    """Ingests and validates raw simulation output files."""

    @classmethod
    def ingest_openfoam_force_coeffs(
        cls,
        file_content: str,
        geometry: str,
        conditions: FlowConditions,
        solver_version: str = "v2312",
        mesh_cells: Optional[int] = None,
        job_id: Optional[str] = None
    ) -> Tuple[List[MultiFidelityResult], CFDQualityClassification, Dict[str, Any]]:
        """
        Parses OpenFOAM postProcessing/forceCoeffs/0/forceCoeffs.dat
        Expected format:
        # Time       Cm          Cd          Cl          Cl(f)       Cl(r)
        0            0.000       0.050       0.000       ...
        """
        forces_history: List[Dict[str, float]] = []
        for line in file_content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    it = float(parts[0])
                    cm = float(parts[1])
                    cd = float(parts[2])
                    cl = float(parts[3])
                    forces_history.append({"iteration": int(it), "cm": cm, "cd": cd, "cl": cl})
                except ValueError:
                    continue

        quality_class, audit_report = CFDQualityControlEngine.audit_simulation_run(
            forces_history=forces_history,
            flow_conditions=conditions
        )

        final_cl = audit_report.get("final_cl", 0.0)
        final_cd = audit_report.get("final_cd", 0.0)
        final_cm = audit_report.get("final_cm", 0.0)

        prov_hash = hashlib.sha256(file_content.encode("utf-8")).hexdigest()
        job_tag = job_id or f"OF-{geometry.replace(' ', '_')}-{conditions.mach:.2f}-{conditions.aoa_deg:.1f}"

        results = []
        for qty, val in [("CL", final_cl), ("CD", final_cd), ("CM", final_cm)]:
            res = MultiFidelityResult(
                result_id=f"{job_tag}-{qty}",
                geometry=geometry,
                geometry_hash=f"GEOM-{geometry.replace(' ', '_').upper()}",
                fidelity=FidelityLevel.HIGH_FIDELITY_CFD if quality_class in (CFDQualityClassification.CONVERGED, CFDQualityClassification.GRID_CONVERGED) else FidelityLevel.LOW_FIDELITY_CFD,
                quantity=qty,
                value=round(val, 6),
                uncertainty=0.02 if qty == "CL" else 0.001,
                conditions=conditions,
                source="OpenFOAM simpleFoam Simulation",
                solver="OpenFOAM",
                solver_version=solver_version,
                mesh_cells=mesh_cells,
                quality_classification=quality_class,
                provenance_hash=prov_hash,
                metadata={"iterations": len(forces_history), "job_id": job_id, "audit": audit_report}
            )
            results.append(res)

        return results, quality_class, audit_report

    @classmethod
    def ingest_generic_tabular(
        cls,
        data: List[Dict[str, Any]],
        geometry: str,
        conditions: FlowConditions,
        solver_name: str = "UserCFD",
        source_name: str = "User Ingestion"
    ) -> Tuple[List[MultiFidelityResult], CFDQualityClassification, Dict[str, Any]]:
        """
        Ingests structured force history: [{"iteration": int, "cl": float, "cd": float, "cm": float}]
        """
        quality_class, audit_report = CFDQualityControlEngine.audit_simulation_run(
            forces_history=data,
            flow_conditions=conditions
        )

        final_cl = audit_report.get("final_cl", 0.0)
        final_cd = audit_report.get("final_cd", 0.0)
        final_cm = audit_report.get("final_cm", 0.0)

        prov_str = json.dumps(data, sort_keys=True)
        prov_hash = hashlib.sha256(prov_str.encode("utf-8")).hexdigest()

        results = []
        for qty, val in [("CL", final_cl), ("CD", final_cd), ("CM", final_cm)]:
            res = MultiFidelityResult(
                result_id=f"GEN-{geometry}-{conditions.mach:.2f}-{conditions.aoa_deg:.1f}-{qty}",
                geometry=geometry,
                geometry_hash=f"GEOM-{geometry.replace(' ', '_').upper()}",
                fidelity=FidelityLevel.HIGH_FIDELITY_CFD if quality_class == CFDQualityClassification.CONVERGED else FidelityLevel.USER_PROVIDED,
                quantity=qty,
                value=round(val, 6),
                uncertainty=0.025 if qty == "CL" else 0.0015,
                conditions=conditions,
                source=source_name,
                solver=solver_name,
                quality_classification=quality_class,
                provenance_hash=prov_hash,
                metadata={"audit": audit_report}
            )
            results.append(res)

        return results, quality_class, audit_report
