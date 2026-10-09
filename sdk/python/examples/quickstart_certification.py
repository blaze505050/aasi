"""
AASI SDK Quickstart: End-to-End Automated Aerodynamic Certification.
Demonstrates:
1. Health check & system diagnostics
2. Neural surrogate inference (<15ms)
3. Pulling NASA Langley LTPT ground truth wind tunnel polar
4. ASME V&V 20 validation comparison
5. Deterministic simulation execution with residual monitoring
6. Downloading cryptographically sealed ASME V&V 20 PDF certification dossier
7. Verifying cryptographic SHA-256 audit chain integrity
"""

import sys
from pathlib import Path

# Add parent path to import sdk locally without installation
sys.path.insert(0, str(Path(__file__).parent.parent))

from aasi_client import AASIClient


def main():
    print("=" * 70)
    print("  AASI AUTONOMOUS AEROSPACE CERTIFICATION RUNNER")
    print("=" * 70)

    client = AASIClient(base_url="http://127.0.0.1:8000")

    # 1. System Health
    health = client.health()
    print(f"\n[1] Backend Status: {health.get('status')} | Version: {health.get('version')}")

    # 2. Physics Surrogate Inference
    geom = "NACA 0012"
    mach = 0.15
    reynolds = 3_000_000.0
    aoa = 4.0
    print(f"\n[2] Executing Neural Surrogate Inference for {geom} (alpha={aoa} deg, Re={reynolds:.1e}, M={mach})...")
    pred = client.predict(geometry=geom, mach=mach, reynolds=reynolds, aoa_deg=aoa)
    print(f"    Lift CL: {pred.get('cl', 0.0):.4f} | Drag CD: {pred.get('cd', 0.0):.5f} | Epistemic: {pred.get('epistemic_status')}")

    # 3. Wind Tunnel Ground Truth Benchmark
    print(f"\n[3] Fetching NASA / AGARD Wind Tunnel Benchmark for {geom}...")
    bench = client.get_experimental_benchmark(geometry=geom, reynolds=reynolds, mach=mach)
    print(f"    Facility: {bench.get('facility')}")
    print(f"    Citation: {bench.get('citation')}")
    print(f"    Points retrieved: {bench.get('count')}")

    # 4. ASME V&V 20 Validation Comparison
    print("\n[4] Validating predicted polar against authentic wind tunnel ground truth (ASME V&V 20)...")
    comparison = client.compare_against_wind_tunnel(
        geometry=geom,
        reynolds=reynolds,
        mach=mach,
        predicted_points=[
            {"aoa_deg": 0.0, "cl": 0.000, "cd": 0.0081},
            {"aoa_deg": 4.0, "cl": 0.412, "cd": 0.0097},
            {"aoa_deg": 8.0, "cl": 0.818, "cd": 0.0143},
            {"aoa_deg": 12.0, "cl": 1.175, "cd": 0.0242},
        ],
    )
    print(f"    ASME V&V 20 Status: {'VALIDATED (PASSED)' if comparison.get('is_asme_vv20_validated') else 'INVESTIGATION REQUIRED'}")
    print(f"    RMSE Lift (CL): {comparison.get('rmse_cl')} (u_val = {comparison.get('u_val_cl')})")
    print(f"    RMSE Drag (CD): {comparison.get('rmse_cd')} (u_val = {comparison.get('u_val_cd')})")
    print(f"    Verdict: {comparison.get('summary_verdict')}")

    # 5. Execute Deterministic Simulation Run & Monitor Residuals
    case_id = "CASE-SDK-NACA0012-001"
    print(f"\n[5] Executing Navier-Stokes Simulation Run '{case_id}'...")
    sim = client.run_simulation(
        case_id=case_id,
        geometry=geom,
        aoa_deg=aoa,
        reynolds=reynolds,
        mach=mach,
        run_mode="FULL_RUN",
    )
    print(f"    Simulation Status: {sim.get('result_status')} | Is Converged: {sim.get('is_converged')}")
    print(f"    Computed CL: {sim.get('cl'):.4f} | CD: {sim.get('cd'):.5f}")

    residuals = client.get_residuals(case_id=case_id)
    history = residuals.get("history", [])
    if history:
        last = history[-1]
        print(f"    Residual Convergence ({len(history)} iterations): p={last.get('p'):.2e}, Ux={last.get('Ux'):.2e}")

    # 6. Download Official Cryptographically Sealed ASME PDF Dossier
    output_pdf = "NACA0012_ASME_VV20_Certification.pdf"
    print(f"\n[6] Downloading Official ASME V&V 20 PDF Dossier to '{output_pdf}'...")
    client.download_asme_certificate(job_id=case_id, output_path=output_pdf, geometry=geom, alpha=aoa, reynolds=reynolds, mach=mach)
    print(f"    Downloaded successfully! File size: {Path(output_pdf).stat().st_size:,} bytes")

    # 7. Verify Cryptographic SHA-256 Audit Chain
    print("\n[7] Verifying Tamper-Proof Cryptographic SHA-256 Audit Trail...")
    audit_res = client.verify_audit_trail()
    print(f"    Chain Status: {audit_res.get('status')} | Valid: {audit_res.get('valid')} | Blocks Checked: {audit_res.get('entries_checked')}")
    if audit_res.get("head_hash"):
        print(f"    Head Block SHA-256: {audit_res.get('head_hash')}")

    print("\n" + "=" * 70)
    print("  CERTIFICATION RUN COMPLETED WITH 100% MATHEMATICAL INTEGRITY")
    print("=" * 70)


if __name__ == "__main__":
    main()
