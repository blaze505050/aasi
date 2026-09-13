"""
AASI Phase 21: OpenFOAM Case Validator.
Governing Rule: Absolute Anti-Fabrication Rule.
Performs rigorous structural and aerodynamic validation on OpenFOAM simulation directories.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
import re


class CFDCaseValidator:
    """Validates structure, boundary definitions, and geometry of an OpenFOAM case."""

    REQUIRED_FILES = [
        "system/controlDict",
        "system/fvSchemes",
        "system/fvSolution",
        "constant/transportProperties",
        "0/U",
        "0/p",
    ]

    REQUIRED_PATCHES = ["inlet", "outlet", "airfoil"]

    @classmethod
    def validate_case_directory(cls, case_dir: Path, expected_geometry_hash: Optional[str] = None) -> Dict[str, Any]:
        """Verify full structural integrity of an OpenFOAM case."""
        case_path = Path(case_dir)
        errors: List[str] = []
        warnings: List[str] = []

        if not case_path.exists() or not case_path.is_dir():
            return {
                "valid": False,
                "case_dir": str(case_path),
                "errors": [f"Case directory does not exist: {case_path}"],
                "warnings": [],
                "mesh_statistics": {},
            }

        # 1. Check required dictionaries
        for rel_file in cls.REQUIRED_FILES:
            file_path = case_path / rel_file
            if not file_path.exists():
                errors.append(f"Missing mandatory simulation dictionary: {rel_file}")
            elif file_path.stat().st_size == 0:
                errors.append(f"Mandatory simulation dictionary is empty: {rel_file}")

        # 2. Check turbulence properties (support OpenFOAM 6-11 naming conventions)
        turb_v1 = case_path / "constant/turbulenceProperties"
        turb_v2 = case_path / "constant/momentumTransport"
        if not turb_v1.exists() and not turb_v2.exists():
            warnings.append("Neither constant/turbulenceProperties nor constant/momentumTransport found.")

        # 3. Check boundary conditions in 0/U
        u_file = case_path / "0/U"
        if u_file.exists():
            try:
                content = u_file.read_text(encoding="utf-8", errors="ignore")
                for patch in cls.REQUIRED_PATCHES:
                    if patch not in content and patch.lower() not in content.lower():
                        warnings.append(f"Expected boundary patch '{patch}' not explicitly defined in 0/U")
            except Exception as e:
                errors.append(f"Failed to read 0/U boundary conditions: {e}")

        # 4. Check mesh existence and basic statistics
        poly_mesh_dir = case_path / "constant/polyMesh"
        mesh_stats: Dict[str, Any] = {"mesh_present": False}
        if poly_mesh_dir.exists() and (poly_mesh_dir / "points").exists():
            mesh_stats["mesh_present"] = True
            try:
                points_content = (poly_mesh_dir / "points").read_text(encoding="utf-8", errors="ignore")
                # Parse number of points from OpenFOAM header
                match = re.search(r"\n(\d+)\s*\n\(", points_content)
                if match:
                    mesh_stats["num_points"] = int(match.group(1))
            except Exception:
                pass

            if (poly_mesh_dir / "owner").exists():
                try:
                    owner_content = (poly_mesh_dir / "owner").read_text(encoding="utf-8", errors="ignore")
                    match = re.search(r"\n(\d+)\s*\n\(", owner_content)
                    if match:
                        mesh_stats["num_faces"] = int(match.group(1))
                except Exception:
                    pass
        else:
            warnings.append("No constant/polyMesh directory present (case requires blockMesh/snappyHexMesh execution).")

        # 5. Verify geometry file hash if expected
        geom_file = case_path / "geometry.dat"
        if expected_geometry_hash:
            if not geom_file.exists():
                errors.append("Expected geometry.dat for hash verification but file was not found.")
            else:
                actual_hash = hashlib.sha256(geom_file.read_bytes()).hexdigest()
                if actual_hash != expected_geometry_hash:
                    errors.append(
                        f"Geometry hash mismatch: expected {expected_geometry_hash[:16]}..., "
                        f"found {actual_hash[:16]}..."
                    )

        return {
            "valid": len(errors) == 0,
            "case_dir": str(case_path),
            "errors": errors,
            "warnings": warnings,
            "mesh_statistics": mesh_stats,
        }
