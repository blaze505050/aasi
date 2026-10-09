"""
Tests for AASI Enterprise SQLite Investigation Database and Analytics.
"""

import pytest
from pathlib import Path
from backend.storage.investigation_db import InvestigationDatabase
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_investigation_db_lifecycle(tmp_path: Path):
    db_file = tmp_path / "test_aasi.db"
    db = InvestigationDatabase(db_path=db_file)

    # 1. Upsert investigation
    db.upsert_investigation(
        job_id="JOB-TEST-001",
        investigation_id="INV-TEST-001",
        objective="Analyze NACA 0012 cruise drag polar",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15,
        verification_status="VERIFIED",
        epistemic_class="USER_EXECUTED_VERIFIED",
        cl=0.44,
        cd=0.0084,
        cm=-0.005,
        tags=["naca-0012", "cruise", "subsonic"],
        full_payload={"test_key": "test_val"},
    )

    # 2. Retrieve
    item = db.get_investigation("JOB-TEST-001")
    assert item is not None
    assert item["geometry"] == "NACA 0012"
    assert item["cl"] == 0.44
    assert item["verification_status"] == "VERIFIED"
    assert "naca-0012" in item["tags"]
    assert item["full_payload"].get("test_key") == "test_val"

    # 3. List
    results = db.list_investigations(query="cruise")
    assert len(results) == 1
    assert results[0]["job_id"] == "JOB-TEST-001"

    # 4. Analytics Summary
    analytics = db.get_analytics_summary()
    assert analytics["total_investigations"] == 1
    assert analytics["verified_investigations"] == 1
    assert analytics["unique_geometries"] == 1
    assert analytics["avg_cl"] == 0.44


def test_api_investigate_analytics_endpoint():
    res = client.get("/api/investigate/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_investigations" in data
    assert "verification_rate_pct" in data
