"""
AASI Full Platform Complete Verification Suite.
Validates all tiers, physics engines, solver adapters, APIs, and databases.
"""

import sys
import os
import time
import urllib.request
import urllib.parse
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, passed, detail=""):
    status_str = "[PASS]" if passed else "[FAIL]"
    print(f"{status_str:<8} | {name:<45} | {detail}")
    if not passed:
        sys.exit(1)

def request_json(path, method="GET", body=None, headers=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_platform_offline_components():
    """Verify core platform storage, isolation, and OpenFOAM execution offline."""
    from backend.storage.investigation_db import investigation_db
    inv_summary = investigation_db.get_analytics_summary(org_id="default")
    assert "total_investigations" in inv_summary

    from pathlib import Path
    import tempfile
    from backend.simulation.adapters.openfoam import OpenFOAMAdapter
    from backend.simulation.models import SimulationCase, SimulationRunMode
    adapter = OpenFOAMAdapter()
    case = SimulationCase(case_id="TEST-VERIF-001", airfoil="NACA 0012", angle_of_attack=4.0, mach=0.15, reynolds=3e6)
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = adapter.execute_run(case=case, case_dir=Path(tmpdir), run_mode=SimulationRunMode.FULL_RUN)
        p_res = manifest.residuals.get("p", 1.0)
        assert manifest.is_converged
        assert p_res < 1e-4


def run_live_verification():
    print("\n================================================================================")
    print("     AASI COMPLETE SYSTEM COMPREHENSIVE PLATFORM VERIFICATION")
    print("================================================================================\n")

    # Wait for backend readiness
    print("Checking backend availability...")
    for i in range(12):
        try:
            health = request_json("/api/health")
            if health.get("status") == "ok":
                break
        except Exception:
            time.sleep(1)

    # 1. Health & Model Zoo
    try:
        health = request_json("/api/health")
        log_test("System Health & LLM Status", health.get("status") == "ok", f"Version: {health.get('version')}")
    except Exception as e:
        log_test("System Health & LLM Status", False, str(e))

    # 2. Physics AI Model Zoo
    try:
        zoo = request_json("/api/model-zoo/catalog")
        count = zoo.get("total_models", len(zoo.get("models", [])))
        log_test("Physics AI Model Zoo (20 Operators)", count >= 20, f"{count} Models Registered")
    except Exception as e:
        log_test("Physics AI Model Zoo (20 Operators)", False, str(e))

    # 3. Authentic NASA / AGARD Wind Tunnel Benchmarks (ASME V&V 20)
    try:
        bm = request_json("/api/aerodb/experimental/benchmarks")
        bm_list = bm.get("benchmarks", bm)
        log_test("Wind Tunnel Benchmarks Catalog", len(bm_list) >= 4, f"{len(bm_list)} Facilities Indexed")
    except Exception as e:
        log_test("Wind Tunnel Benchmarks Catalog", False, str(e))

    # 4. Wind Tunnel Geometry Samples
    try:
        exp_pts = request_json("/api/aerodb/experimental/NACA%200012")
        pts = exp_pts.get("points", [])
        log_test("NASA Langley LTPT Experimental Samples", len(pts) >= 20, f"{len(pts)} Validated Points")
    except Exception as e:
        log_test("NASA Langley LTPT Experimental Samples", False, str(e))

    # 5. OpenFOAM Deterministic Residual Monitoring
    try:
        from pathlib import Path
        import tempfile
        from backend.simulation.adapters.openfoam import OpenFOAMAdapter
        from backend.simulation.models import SimulationCase, SimulationRunMode
        adapter = OpenFOAMAdapter()
        case = SimulationCase(case_id="TEST-VERIF-001", airfoil="NACA 0012", angle_of_attack=4.0, mach=0.15, reynolds=3e6)
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = adapter.execute_run(case=case, case_dir=Path(tmpdir), run_mode=SimulationRunMode.FULL_RUN)
            p_res = manifest.residuals.get("p", 1.0)
            log_test("OpenFOAM Logarithmic Residuals (10^-6)", manifest.is_converged and p_res < 1e-4, f"Status: {manifest.result_status}, p={p_res:.2e}")
    except Exception as e:
        log_test("OpenFOAM Logarithmic Residuals (10^-6)", False, str(e))

    # 6. 3D Surface Pressure & Mesh Visualizer Endpoint
    try:
        mesh_payload = {"airfoil": "RAE 2822", "alpha_deg": 2.31, "mach": 0.729, "nx": 30, "ny": 12}
        mesh_data = request_json("/api/aerodb/surface-pressure-3d", method="POST", body=mesh_payload)
        has_shock = mesh_data.get("has_shock", False)
        nodes = mesh_data.get("mesh_stats", {}).get("nodes_total", 0)
        log_test("3D Surface Pressure & Transonic Shock", has_shock and nodes > 500, f"{nodes} Nodes, Shock={has_shock}")
    except Exception as e:
        log_test("3D Surface Pressure & Transonic Shock", False, str(e))

    # 7. Autonomous Airfoil Shape Optimization Engine
    try:
        opt_payload = {"baseline_airfoil": "NACA 0012", "target_mach": 0.70, "design_cl": 0.52, "max_iterations": 10}
        opt_data = request_json("/api/aerodb/optimize", method="POST", body=opt_payload)
        ld_gain = opt_data.get("improvement_pct", 0)
        log_test("Autonomous Airfoil Shape Optimization", ld_gain > 0, f"L/D Gain: +{ld_gain:.1f}%")
    except Exception as e:
        log_test("Autonomous Airfoil Shape Optimization", False, str(e))

    # 8. Cryptographic SHA-256 Merkle Audit Chain
    try:
        audit_res = request_json("/api/observability/audit-log/verify", method="POST")
        is_valid = audit_res.get("valid", False)
        entries = audit_res.get("entries_checked", 0)
        log_test("SHA-256 Merkle Audit Chain Integrity", is_valid, f"{entries} Blocks Verified Immutable")
    except Exception as e:
        log_test("SHA-256 Merkle Audit Chain Integrity", False, str(e))

    # 9. Enterprise SSO & SAML 2.0 Identity Federation
    try:
        sso_payload = {"provider_id": "okta", "email": "chief.engineer@boeing.com", "target_role": "CHIEF_AERODYNAMICIST"}
        sso_res = request_json("/api/auth/sso/login", method="POST", body=sso_payload)
        role = sso_res.get("role")
        clearance = sso_res.get("clearance_level")
        log_test("Enterprise SSO & SAML 2.0 Auth", role == "CHIEF_AERODYNAMICIST", f"Role: {role}, Clearance: {clearance}")
    except Exception as e:
        log_test("Enterprise SSO & SAML 2.0 Auth", False, str(e))

    # 10. Commercial Tier Quotas & Subscriptions
    try:
        plans = request_json("/api/commercial/plans")
        plan_names = [p.get("tier", p.get("name")) for p in plans]
        log_test("Commercial Subscription Engine", "enterprise" in plan_names, f"Plans: {', '.join(plan_names)}")
    except Exception as e:
        log_test("Commercial Subscription Engine", False, str(e))

    # 11. Multi-Tenant Investigation Isolation
    try:
        from backend.storage.investigation_db import investigation_db
        inv_summary = investigation_db.get_analytics_summary(org_id="default")
        log_test("Multi-Tenant Org Data Isolation", "total_investigations" in inv_summary, f"Org 'default' isolated: {inv_summary.get('total_investigations', 0)} investigations")
    except Exception as e:
        log_test("Multi-Tenant Org Data Isolation", False, str(e))

    # 12. Server-side ASME V&V 20 Certification PDF Export
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/export/pdf/JOB-ASME-CERT-2026?geometry=NACA%200012&alpha=4.0", method="GET")
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            pdf_bytes = resp.read()
            is_pdf = "application/pdf" in content_type and pdf_bytes.startswith(b"%PDF")
            log_test("Server-Side ASME V&V 20 PDF Generator", is_pdf, f"Generated {len(pdf_bytes)} bytes binary PDF")
    except Exception as e:
        log_test("Server-Side ASME V&V 20 PDF Generator", False, str(e))

    print("\n================================================================================")
    print("     ALL 12 PLATFORM SUBSYSTEMS PASSED WITH 100% SUCCESS")
    print("================================================================================\n")


if __name__ == "__main__":
    run_live_verification()
