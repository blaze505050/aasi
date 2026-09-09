"""Artifact and reproducible manifest manager for simulation cases."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from .models import SimulationCase, SimulationManifest, SimulationRunMode


class SimulationArtifactManager:
    """Manages input/output hashing, directory structure, and manifest persistence for scientific simulations."""

    def __init__(self, base_sim_dir: Optional[Path] = None):
        self.base_sim_dir = base_sim_dir or Path("data/simulations")

    def prepare_case_directory(self, case: SimulationCase) -> Path:
        """Create clean isolated workspace directory for simulation execution."""
        case_dir = self.base_sim_dir / case.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def compute_directory_hash(self, directory: Path) -> str:
        """Compute recursive SHA-256 hash over all case files in directory."""
        hasher = hashlib.sha256()
        for root, _, files in os.walk(str(directory)):
            for f in sorted(files):
                file_path = Path(root) / f
                if file_path.is_file() and not f.endswith(".log") and not f.endswith(".manifest.json"):
                    hasher.update(f.encode("utf-8"))
                    try:
                        hasher.update(file_path.read_bytes())
                    except Exception:
                        pass
        return hasher.hexdigest()

    def create_manifest(
        self,
        case: SimulationCase,
        run_mode: SimulationRunMode,
        input_checksum: str,
        output_checksum: Optional[str] = None,
        is_converged: bool = False,
        cl: Optional[float] = None,
        cd: Optional[float] = None,
        cm: Optional[float] = None,
        residuals: Optional[Dict[str, float]] = None,
        logs: Optional[List[str]] = None,
        result_files: Optional[List[str]] = None,
        result_status: str = "SUCCESS",
        git_revision: str = "33325ff",
    ) -> SimulationManifest:
        """Construct reproducible experiment manifest."""
        manifest = SimulationManifest(
            experiment_id=f"EXP-{case.case_id}",
            solver=case.solver,
            solver_version="v2312",
            geometry=case.geometry,
            input_parameters={
                "mach": case.mach,
                "reynolds": case.reynolds,
                "aoa_deg": case.aoa_deg,
                "parameters": case.parameters,
            },
            units={
                "mach": "dimensionless",
                "reynolds": "dimensionless",
                "aoa_deg": "degrees",
                "cl": "dimensionless",
                "cd": "dimensionless",
                "cm": "dimensionless",
            },
            mesh_specification={"mesh_cells": case.mesh_cells, "geometry": case.geometry},
            boundary_conditions={"wall": "noSlip", "inlet": "freestreamVelocity", "outlet": "fixedPressure"},
            turbulence_model=case.turbulence_model,
            numerical_settings={"max_iterations": case.max_iterations, "tolerance": case.convergence_tolerance},
            git_revision=git_revision,
            input_checksum=input_checksum,
            output_checksum=output_checksum,
            run_mode=run_mode,
            is_converged=is_converged,
            cl=cl,
            cd=cd,
            cm=cm,
            residuals=residuals or {},
            logs=logs or [],
            result_files=result_files or [],
            result_status=result_status,
            epistemic_status="LOCAL_CFD" if is_converged else "DRY_RUN_VERIFIED",
        )
        return manifest

    def save_manifest(self, manifest: SimulationManifest, target_directory: Path) -> Path:
        """Write manifest JSON to case directory."""
        target_directory.mkdir(parents=True, exist_ok=True)
        manifest_path = target_directory / f"{manifest.experiment_id}.manifest.json"
        manifest_path.write_text(json.dumps(manifest.model_dump(), indent=2), encoding="utf-8")
        return manifest_path
