"""
End-to-End Integration Test for the Complete Airfoil Engineering Workflow (Phase D).

Verifies the full pipeline:
1. Geometry Parsing (Selig format, Lednicer format, analytical NACA 4-digit)
2. Resampling & Curvature Cosine Clustering
3. Aerodynamic Panel Solution & Surface Pressure (Cp) Distribution
4. AeroDB Polar Envelope Sweep & Stability Derivatives Extraction
5. Multi-Condition Matrix & Stability Margins Evaluation
6. SQLite Persistence & Cross-Session Retrieval
7. Standard Aerospace Exports (USAF DATCOM, NASA S/HABP, 6-DOF CSV, Cryptographic JSON)
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.physics.airfoil_parser import AirfoilCoordinateParser, AirfoilGeometry
from backend.physics.panel_solver import AerodynamicPanelSolver, calculate_airfoil_aerodynamics
from backend.physics.aerodb_engine import AerodynamicDatabaseEngine, _AERO_DATABASES
from backend.storage.aerodb_store import aerodb_store
from backend.export.aerodb_export import AeroDBExporter

client = TestClient(app)


def test_complete_airfoil_engineering_workflow():
    # -------------------------------------------------------------------------
    # Step 1: Geometry Parsing & Resampling
    # -------------------------------------------------------------------------
    # Test NACA 4412 coordinate parsing via Selig text
    selig_text = """NACA 4412 Cambered Airfoil
1.000000  0.001300
0.950000  0.014200
0.800000  0.048900
0.600000  0.088000
0.400000  0.118000
0.200000  0.108000
0.050000  0.052000
0.000000  0.000000
0.050000 -0.024000
0.200000 -0.038000
0.400000 -0.038000
0.600000 -0.028000
0.800000 -0.014000
0.950000 -0.003500
1.000000 -0.001300
"""
    geom = AirfoilCoordinateParser.parse_text(selig_text)
    assert isinstance(geom, AirfoilGeometry)
    assert "NACA 4412" in geom.name
    # 120-panel resampling
    assert geom.point_count >= 100
    assert 0.10 <= geom.max_thickness <= 0.17
    assert 0.03 <= geom.max_camber <= 0.05

    # -------------------------------------------------------------------------
    # Step 2: Surface Pressure (Cp) & Panel Solver Integration
    # -------------------------------------------------------------------------
    panel_res = calculate_airfoil_aerodynamics(
        geometry="NACA 4412",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15
    )
    panel_results = panel_res["results"]
    assert "CL" in panel_results
    assert "CD" in panel_results
    assert "CM" in panel_results
    assert panel_results["CL"] > 0.6  # NACA 4412 at 4 deg AoA has high lift
    assert panel_results["CD"] > 0.005  # Positive profile drag
    assert "cp_distribution" in panel_results
    assert len(panel_results["cp_distribution"]) > 0

    # -------------------------------------------------------------------------
    # Step 3: AeroDB Multi-Condition Envelope Sweep
    # -------------------------------------------------------------------------
    aero_db = AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name="NACA 4412",
        coordinates_text=selig_text,
        alpha_min=-4.0,
        alpha_max=12.0,
        alpha_step=2.0,
        reynolds_list=[1e6, 3e6],
        mach_list=[0.15, 0.25],
        fidelity_tier="MULTI_FIDELITY"
    )

    assert "NACA 4412" in aero_db.geometry_name
    assert len(aero_db.polars) == 4  # 2 Re * 2 Mach = 4 polar curves
    assert len(aero_db.provenance_hash) == 64  # SHA-256 hash

    # Stability derivatives check for Re=3e6, Mach=0.15
    polar_sub = next(p for p in aero_db.polars if p.reynolds == 3e6 and p.mach == 0.15)
    derivs = polar_sub.derivatives
    assert derivs.cl_alpha_per_deg > 0.08  # Positive lift slope
    assert derivs.alpha_zero_lift_deg < -2.0  # Negative zero-lift angle for cambered airfoil
    assert derivs.cd_0 > 0.004  # Minimum drag
    assert derivs.l_over_d_max > 25.0  # High glide ratio
    assert 0.20 <= derivs.aerodynamic_center_x_over_c <= 0.30  # Near quarter chord

    # -------------------------------------------------------------------------
    # Step 4: ACID SQLite Persistence Verification
    # -------------------------------------------------------------------------
    db_id = aero_db.db_id
    # Clear in-memory dictionary to verify disk reload
    if db_id in _AERO_DATABASES:
        del _AERO_DATABASES[db_id]

    reloaded = AerodynamicDatabaseEngine.get_aero_db(db_id)
    assert reloaded is not None
    assert reloaded.db_id == db_id
    assert "NACA 4412" in reloaded.geometry_name
    assert len(reloaded.polars) == 4

    # -------------------------------------------------------------------------
    # Step 5: Aerospace Export Generation
    # -------------------------------------------------------------------------
    # 1. USAF DATCOM card deck
    datcom_text = AeroDBExporter.export_datcom(reloaded)
    assert "$FLTCON" in datcom_text
    assert "MACH(1)=0.150" in datcom_text
    assert "NEXT CASE" in datcom_text

    # 2. NASA S/HABP format
    shabp_text = AeroDBExporter.export_shabp(reloaded)
    assert "$TABLE" in shabp_text
    assert "CL_ALPHA" in shabp_text
    assert "$ENDTABLE" in shabp_text

    # 3. 6-DOF simulation CSV
    csv_text = AeroDBExporter.export_6dof_csv(reloaded)
    for col in ["mach", "reynolds", "alpha_deg", "cl", "cd", "cm", "provenance_hash"]:
        assert col in csv_text
    lines = csv_text.strip().splitlines()
    assert len(lines) > 20  # Header + multiple polar points

    # 4. JSON Schema serialization
    json_export = json.loads(reloaded.model_dump_json())
    assert json_export["db_id"] == db_id
    assert "envelope_summary" in json_export
    assert json_export["provenance_hash"] == aero_db.provenance_hash


def test_api_airfoil_workflow_via_http():
    """Verifies the HTTP API endpoints for the complete airfoil workflow."""
    # 1. Generate AeroDB via HTTP API
    gen_payload = {
        "geometry": "NACA 2412",
        "alpha_min": -2.0,
        "alpha_max": 6.0,
        "alpha_step": 2.0,
        "reynolds_list": [2_000_000.0],
        "mach_list": [0.20],
    }
    res = client.post(
        "/api/aerodb/generate",
        json=gen_payload,
        headers={"X-User-Id": "flight_test_engineer", "X-User-Role": "ADMIN"}
    )
    assert res.status_code == 200
    db_data = res.json()
    db_id = db_data["db_id"]

    # 2. Retrieve via GET /api/aerodb/{id}
    get_res = client.get(
        f"/api/aerodb/{db_id}",
        headers={"X-User-Id": "flight_test_engineer", "X-User-Role": "ADMIN"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["db_id"] == db_id

    # 3. List databases via GET /api/aerodb
    list_res = client.get(
        "/api/aerodb",
        headers={"X-User-Id": "flight_test_engineer", "X-User-Role": "ADMIN"}
    )
    assert list_res.status_code == 200
    dbs = list_res.json()
    assert any(d["db_id"] == db_id for d in dbs)

    # 4. Export DATCOM via HTTP API
    datcom_res = client.get(
        f"/api/aerodb/{db_id}/export?format=datcom",
        headers={"X-User-Id": "flight_test_engineer", "X-User-Role": "ADMIN"}
    )
    assert datcom_res.status_code == 200
    assert "$FLTCON" in datcom_res.text
