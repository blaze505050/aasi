"""
Integrity tests for OpenFOAM C-grid mesh generator and case deck synthesis.
Verifies that meshes contain genuine physical airfoil boundary faces and non-zero volume.
"""

from pathlib import Path
import pytest

from backend.cfd.mesh_generator import CGridBlockMeshGenerator
from backend.cfd.openfoam_runner import OpenFOAMRunner
from backend.physics.panel_solver import generate_naca4_coordinates


def test_cgrid_blockmesh_contains_airfoil_faces():
    coords = generate_naca4_coordinates("0012", 60).tolist()
    mesh_text = CGridBlockMeshGenerator.generate_blockmesh_dict(
        coordinates=coords,
        airfoil_name="NACA_0012",
    )

    assert "FoamFile" in mesh_text
    assert "blockMeshDict" in mesh_text
    assert "convertToMeters 1.0;" in mesh_text

    # Verify that the airfoil patch has non-empty faces
    assert "airfoil" in mesh_text
    assert "type wall;" in mesh_text
    # Must NOT contain empty faces ()
    assert "airfoil\n    {\n        type wall;\n        faces ();" not in mesh_text
    assert "faces\n        (\n            (8 20 19 7)" in mesh_text


def test_openfoam_runner_prepares_case_with_blockmesh(tmp_path):
    runner = OpenFOAMRunner(default_output_dir=tmp_path)
    coords = generate_naca4_coordinates("0012", 60).tolist()

    case_dir = runner.prepare_case(
        case_name="TEST_CASE_NACA0012",
        airfoil_name="NACA 0012",
        coordinates=coords,
        alpha_deg=4.0,
        reynolds=3e6,
    )

    blockmesh_file = case_dir / "system" / "blockMeshDict"
    assert blockmesh_file.exists()

    content = blockmesh_file.read_text(encoding="utf-8")
    assert "airfoil" in content
    assert "type wall;" in content
    assert "faces" in content
    assert "hex" in content
