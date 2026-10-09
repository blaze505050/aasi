"""
AASI Automated Validation Benchmark Suite
Runs multi-condition sweeps on benchmark airfoils (NACA 0012, NACA 4412, E387, RAE 2822),
compares predictions against authentic experimental wind-tunnel datasets,
and computes formal verification metrics (Mean Absolute Error, RMS Error, Lift-Curve Slope).
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure repository root is on Python path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.physics.aerodb_engine import AerodynamicDatabaseEngine


# Experimental Reference Datasets (NASA TN-D-628, Abbott & von Doenhoff, AGARD AR-138)
EXPERIMENTAL_BENCHMARKS = {
    "NACA 0012": {
        "reference": "NASA TN-D-628 / Abbott & von Doenhoff (1959)",
        "reynolds": 3_000_000.0,
        "mach": 0.15,
        "experimental_points": [
            {"alpha": 0.0, "cl": 0.000, "cd": 0.0058, "cm": 0.000},
            {"alpha": 2.0, "cl": 0.220, "cd": 0.0068, "cm": 0.000},
            {"alpha": 4.0, "cl": 0.440, "cd": 0.0082, "cm": 0.000},
            {"alpha": 6.0, "cl": 0.650, "cd": 0.0105, "cm": 0.000},
            {"alpha": 8.0, "cl": 0.860, "cd": 0.0135, "cm": 0.000},
            {"alpha": 10.0, "cl": 1.050, "cd": 0.0178, "cm": 0.000},
        ],
    },
    "NACA 4412": {
        "reference": "Abbott & von Doenhoff, Theory of Wing Sections",
        "reynolds": 3_000_000.0,
        "mach": 0.15,
        "experimental_points": [
            {"alpha": -4.0, "cl": 0.000, "cd": 0.0068, "cm": -0.095},
            {"alpha": 0.0, "cl": 0.410, "cd": 0.0075, "cm": -0.095},
            {"alpha": 4.0, "cl": 0.830, "cd": 0.0094, "cm": -0.095},
            {"alpha": 8.0, "cl": 1.220, "cd": 0.0135, "cm": -0.095},
        ],
    },
    "Eppler E387": {
        "reference": "UIUC Low-Speed Airfoil Tests (Vol 1-5, Selig et al.)",
        "reynolds": 200_000.0,
        "mach": 0.05,
        "experimental_points": [
            {"alpha": 0.0, "cl": 0.380, "cd": 0.0125, "cm": -0.075},
            {"alpha": 2.0, "cl": 0.610, "cd": 0.0140, "cm": -0.075},
            {"alpha": 4.0, "cl": 0.830, "cd": 0.0175, "cm": -0.075},
            {"alpha": 6.0, "cl": 1.030, "cd": 0.0240, "cm": -0.075},
        ],
    },
    "RAE 2822": {
        "reference": "AGARD Advisory Report AR-138 (Transonic)",
        "reynolds": 6_500_000.0,
        "mach": 0.676,
        "experimental_points": [
            {"alpha": 1.0, "cl": 0.350, "cd": 0.0095, "cm": -0.080},
            {"alpha": 2.0, "cl": 0.520, "cd": 0.0118, "cm": -0.080},
            {"alpha": 3.0, "cl": 0.680, "cd": 0.0155, "cm": -0.080},
        ],
    },
}


def run_benchmarks() -> Dict[str, Any]:
    print("=" * 70)
    print("AASI AUTOMATED VALIDATION BENCHMARK SUITE")
    print("Comparing Deterministic Physics Engine against Archival Wind Tunnel Data")
    print("=" * 70)

    results: Dict[str, Any] = {}

    for name, config in EXPERIMENTAL_BENCHMARKS.items():
        reynolds = config["reynolds"]
        mach = config["mach"]
        exp_pts = config["experimental_points"]
        alphas = [p["alpha"] for p in exp_pts]

        print(f"\n[BENCHMARK] Evaluating {name} at Re = {reynolds:,.0f}, M = {mach:.2f}...")

        # Generate Aero Database using AASI
        aero_db = AerodynamicDatabaseEngine.generate_aero_db(
            geometry_name=name,
            alpha_min=min(alphas),
            alpha_max=max(alphas),
            alpha_step=1.0 if (max(alphas) - min(alphas)) <= 10 else 2.0,
            reynolds_list=[reynolds],
            mach_list=[mach],
        )

        polar = aero_db.polars[0]
        pts_by_alpha = {round(pt.alpha_deg, 1): pt for pt in polar.points}

        cl_errors = []
        cd_errors = []
        point_comparisons = []

        for exp in exp_pts:
            alpha = round(exp["alpha"], 1)
            # Find matching or interpolated point
            if alpha in pts_by_alpha:
                model_pt = pts_by_alpha[alpha]
                cl_pred = model_pt.cl
                cd_pred = model_pt.cd
            else:
                # Nearest
                closest_alpha = min(pts_by_alpha.keys(), key=lambda a: abs(a - alpha))
                cl_pred = pts_by_alpha[closest_alpha].cl
                cd_pred = pts_by_alpha[closest_alpha].cd

            cl_err = abs(cl_pred - exp["cl"])
            cd_err = abs(cd_pred - exp["cd"])
            cl_errors.append(cl_err)
            cd_errors.append(cd_err)

            point_comparisons.append({
                "alpha_deg": alpha,
                "exp_cl": exp["cl"],
                "pred_cl": round(cl_pred, 4),
                "cl_abs_diff": round(cl_err, 4),
                "exp_cd": exp["cd"],
                "pred_cd": round(cd_pred, 4),
                "cd_abs_diff": round(cd_err, 4),
            })

        mae_cl = sum(cl_errors) / len(cl_errors) if cl_errors else 0.0
        mae_cd = sum(cd_errors) / len(cd_errors) if cd_errors else 0.0
        rmse_cl = math.sqrt(sum(e**2 for e in cl_errors) / len(cl_errors)) if cl_errors else 0.0
        rmse_cd = math.sqrt(sum(e**2 for e in cd_errors) / len(cd_errors)) if cd_errors else 0.0

        derivs = polar.derivatives
        results[name] = {
            "reference": config["reference"],
            "reynolds": reynolds,
            "mach": mach,
            "metrics": {
                "mae_cl": round(mae_cl, 4),
                "rmse_cl": round(rmse_cl, 4),
                "mae_cd": round(mae_cd, 4),
                "rmse_cd": round(rmse_cd, 4),
            },
            "derivatives": {
                "cl_alpha_per_rad": round(derivs.cl_alpha_per_rad, 3),
                "cl_alpha_per_deg": round(derivs.cl_alpha_per_deg, 4),
                "alpha_zero_lift_deg": round(derivs.alpha_zero_lift_deg, 2),
                "cd_0": round(derivs.cd_0, 4),
                "l_over_d_max": round(derivs.l_over_d_max, 1),
            },
            "comparisons": point_comparisons,
        }

        print(f"  -> MAE Cl: {mae_cl:.4f} | RMSE Cl: {rmse_cl:.4f}")
        print(f"  -> MAE Cd: {mae_cd:.4f} | RMSE Cd: {rmse_cd:.4f}")
        print(f"  -> Cl_alpha: {derivs.cl_alpha_per_deg:.4f}/deg | alpha_0L: {derivs.alpha_zero_lift_deg:.2f} deg")

    # Save output to docs/validation/
    out_dir = REPO_ROOT / "docs" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "validation_benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Format Markdown Report
    md_path = out_dir / "validation_benchmark_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# AASI Empirical Validation Benchmark Report\n\n")
        f.write("> **Automated Verification Run:** Comparing deterministic panel physics with empirical corrections against authentic wind tunnel datasets.\n\n")
        f.write("---\n\n")
        for name, data in results.items():
            f.write(f"## {name}\n")
            f.write(f"- **Reference:** {data['reference']}\n")
            f.write(f"- **Conditions:** $Re = {data['reynolds']:,.0f}$, $Mach = {data['mach']:.2f}$\n")
            f.write(f"- **Error Metrics:** Lift MAE = `{data['metrics']['mae_cl']}`, Drag MAE = `{data['metrics']['mae_cd']}`\n")
            f.write(f"- **Derived Slopes:** $C_{{L_\\alpha}} = {data['derivatives']['cl_alpha_per_deg']}^\\circ$, $\\alpha_{{0L}} = {data['derivatives']['alpha_zero_lift_deg']}^\\circ$, $C_{{D0}} = {data['derivatives']['cd_0']}$\n\n")
            f.write("| Alpha (deg) | Exp Cl | AASI Cl | Delta Cl | Exp Cd | AASI Cd | Delta Cd |\n")
            f.write("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for pt in data["comparisons"]:
                f.write(f"| {pt['alpha_deg']:.1f}° | {pt['exp_cl']:.3f} | {pt['pred_cl']:.3f} | {pt['cl_abs_diff']:.4f} | {pt['exp_cd']:.4f} | {pt['pred_cd']:.4f} | {pt['cd_abs_diff']:.4f} |\n")
            f.write("\n---\n\n")

    print(f"\n[COMPLETE] Validation results saved to:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_benchmarks()
