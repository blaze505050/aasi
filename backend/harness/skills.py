"""
AASI 2.0 Core Scientific Skills Registration.

Wraps deterministic AASI aerospace solvers, geometry engines, uncertainty models,
and exporters into strongly-typed tools registered on the ToolBus:
1. aero_2d_solve — Discrete vortex panel method with viscous corrections
2. aero_3d_vlm — Finite 3D wing aerodynamics with Helmbold-Keune compressibility
3. polar_sweep — Multi-condition angle-of-attack sweep
4. uncertainty_quantify — GUM Guide to Expression of Uncertainty
5. benchmark_verify — Independent NASA TM-4083 / TMR validation gate
6. geometry_parse — Airfoil geometry evaluation and coordinate generator
7. export_datcom — USAF DATCOM stability card generator
8. export_shabp — NASA S/HABP format exporter
9. mesh_generate — OpenFOAM C-grid staging configuration
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional
import numpy as np

from backend.tools.contracts import EpistemicTier, ToolDomain, UncertaintyModel, ComputationalCostModel
from backend.harness.tool_protocol import ToolSpec, ToolParameter
from backend.harness.tool_bus import ToolBus, global_tool_bus
from backend.physics.panel_solver import calculate_airfoil_aerodynamics, generate_naca4_coordinates, AerodynamicPanelSolver


# ─── 1. aero_2d_solve Handler ────────────────────────────────────────────────

def handle_aero_2d_solve(
    airfoil: str = "NACA 0012",
    alpha_deg: float = 4.0,
    reynolds: float = 3e6,
    mach: float = 0.15,
) -> Dict[str, Any]:
    solver = AerodynamicPanelSolver()
    if "NACA" in airfoil.upper():
        solver.set_naca(airfoil)
    res = solver.solve(alpha_deg=alpha_deg, reynolds=reynolds, mach=mach)
    return {
        "airfoil": airfoil,
        "alpha_deg": alpha_deg,
        "reynolds": reynolds,
        "mach": mach,
        "CL": res["CL"],
        "CD": res["CD"],
        "CM": res["CM"],
        "L_over_D": round(res["CL"] / max(res["CD"], 1e-5), 2),
        "solver": res["solver"],
        "thickness_ratio": res.get("thickness_ratio", 0.12),
        "camber_ratio": res.get("camber_ratio", 0.0),
    }


# ─── 2. aero_3d_vlm Handler ──────────────────────────────────────────────────

def handle_aero_3d_vlm(
    wingspan_m: float = 10.0,
    aspect_ratio: float = 7.0,
    sweep_deg: float = 0.0,
    alpha_deg: float = 4.0,
    mach: float = 0.15,
    airfoil: str = "NACA 0012",
) -> Dict[str, Any]:
    # 2D section lift slope
    solver = AerodynamicPanelSolver()
    if "NACA" in airfoil.upper():
        solver.set_naca(airfoil)
    res_2d = solver.solve(alpha_deg=alpha_deg, mach=mach)
    cl_2d = res_2d["CL"]
    cd_2d = res_2d["CD"]

    # Helmbold-Keune 3D finite wing correction:
    # CL_alpha_3D = CL_alpha_2D / (sqrt(1 - M^2 + (CL_alpha_2D / (pi*AR))^2) + CL_alpha_2D / (pi*AR))
    beta = math.sqrt(max(0.01, 1.0 - mach ** 2))
    cla_2d_rad = 2.0 * math.pi
    ar = max(0.5, aspect_ratio)
    sweep_rad = math.radians(sweep_deg)

    denom = math.sqrt((beta ** 2) + ((cla_2d_rad / (math.pi * ar)) ** 2) * (1.0 / max(0.1, math.cos(sweep_rad) ** 2))) + (cla_2d_rad / (math.pi * ar))
    cla_3d_rad = cla_2d_rad / denom
    cla_3d_deg = cla_3d_rad * (math.pi / 180.0)

    # 3D lift
    cl_3d = cla_3d_deg * alpha_deg

    # Induced drag (Oswald efficiency factor e ~ 0.85)
    oswald_e = 0.85
    cd_i = (cl_3d ** 2) / (math.pi * ar * oswald_e)
    cd_total = cd_2d + cd_i

    return {
        "airfoil": airfoil,
        "wingspan_m": wingspan_m,
        "aspect_ratio": aspect_ratio,
        "sweep_deg": sweep_deg,
        "alpha_deg": alpha_deg,
        "mach": mach,
        "CL_3D": round(cl_3d, 4),
        "CD_induced": round(cd_i, 5),
        "CD_total": round(cd_total, 5),
        "L_over_D_3D": round(cl_3d / max(cd_total, 1e-5), 2),
        "lift_curve_slope_per_deg": round(cla_3d_deg, 5),
        "oswald_efficiency": oswald_e,
    }


# ─── 3. polar_sweep Handler ──────────────────────────────────────────────────

def handle_polar_sweep(
    airfoil: str = "NACA 0012",
    alpha_start: float = -4.0,
    alpha_end: float = 14.0,
    step_deg: float = 2.0,
    reynolds: float = 3e6,
    mach: float = 0.15,
) -> Dict[str, Any]:
    solver = AerodynamicPanelSolver()
    if "NACA" in airfoil.upper():
        solver.set_naca(airfoil)

    alphas = np.arange(alpha_start, alpha_end + (step_deg * 0.5), step_deg).tolist()
    polar_points = []
    max_ld = -1e9
    best_alpha = 0.0

    for a in alphas:
        r = solver.solve(alpha_deg=float(a), reynolds=reynolds, mach=mach)
        cl = r["CL"]
        cd = r["CD"]
        cm = r["CM"]
        ld = cl / max(cd, 1e-5)
        if ld > max_ld:
            max_ld = ld
            best_alpha = a

        polar_points.append({
            "alpha_deg": round(float(a), 2),
            "CL": cl,
            "CD": cd,
            "CM": cm,
            "L_over_D": round(ld, 2),
        })

    return {
        "airfoil": airfoil,
        "mach": mach,
        "reynolds": reynolds,
        "num_points": len(polar_points),
        "points": polar_points,
        "max_L_over_D": round(max_ld, 2),
        "alpha_for_max_L_over_D": round(best_alpha, 2),
    }


# ─── 4. uncertainty_quantify Handler ─────────────────────────────────────────

def handle_uncertainty_quantify(
    coefficient: str = "CL",
    nominal_value: float = 0.435,
    reynolds: float = 3e6,
    mach: float = 0.15,
) -> Dict[str, Any]:
    # GUM uncertainty propagation
    # Panel methods have ~1.5% model form uncertainty for CL, ~8% for CD
    rel_unc = 0.015 if coefficient.upper() == "CL" else (0.08 if coefficient.upper() == "CD" else 0.05)
    u_std = abs(nominal_value) * rel_unc
    u_expanded_95 = u_std * 2.0  # coverage factor k = 2

    return {
        "coefficient": coefficient.upper(),
        "nominal_value": nominal_value,
        "standard_uncertainty": round(u_std, 5),
        "expanded_uncertainty_95pct": round(u_expanded_95, 5),
        "confidence_interval_95pct": [
            round(nominal_value - u_expanded_95, 5),
            round(nominal_value + u_expanded_95, 5),
        ],
        "relative_uncertainty_percent": round(rel_unc * 100.0, 2),
        "standard_framework": "GUM (JCGM 100:2008 / ASME V&V 20)",
        "epistemic_classification": "UNCERTAINTY_BOUNDED",
    }


# ─── 5. benchmark_verify Handler ─────────────────────────────────────────────

def handle_benchmark_verify(
    geometry: str = "NACA 0012",
    alpha_deg: float = 4.0,
) -> Dict[str, Any]:
    # Certified reference data for NACA 0012 at Re=3e6, M=0.15
    # Abbott & von Doenhoff experimental: CL ~ 0.4350, CD ~ 0.0084
    ref_cl = 0.4350
    ref_cd = 0.0084

    solver = AerodynamicPanelSolver()
    if "NACA" in geometry.upper():
        solver.set_naca(geometry)
    sol = solver.solve(alpha_deg=alpha_deg)

    cl_calc = sol["CL"]
    cd_calc = sol["CD"]
    cl_err_pct = round(abs(cl_calc - ref_cl) / ref_cl * 100.0, 2)
    cd_err_pct = round(abs(cd_calc - ref_cd) / ref_cd * 100.0, 2)

    passed = (cl_err_pct <= 5.0) and (cd_err_pct <= 25.0)

    return {
        "geometry": geometry,
        "alpha_deg": alpha_deg,
        "calculated": {"CL": cl_calc, "CD": cd_calc},
        "reference_experimental": {"CL": ref_cl, "CD": ref_cd, "source": "NASA TM-4083 / Abbott"},
        "discrepancy_cl_percent": cl_err_pct,
        "discrepancy_cd_percent": cd_err_pct,
        "status": "VERIFIED_ACCURATE" if passed else "REGRESSION_DETECTED",
        "passed": passed,
    }


# ─── 6. geometry_parse Handler ───────────────────────────────────────────────

def handle_geometry_parse(
    geometry: str = "NACA 0012",
    num_points: int = 100,
) -> Dict[str, Any]:
    coords = generate_naca4_coordinates(geometry, num_points=num_points)
    clean_code = geometry.upper().replace("NACA", "").strip()
    if len(clean_code) == 4 and clean_code.isdigit():
        t = int(clean_code[2:]) / 100.0
        m = int(clean_code[0]) / 100.0
        p = int(clean_code[1]) / 10.0
    else:
        t, m, p = 0.12, 0.0, 0.0

    return {
        "geometry": geometry,
        "num_surface_points": len(coords),
        "maximum_thickness_t_c": t,
        "maximum_camber_m_c": m,
        "camber_position_p_c": p,
        "leading_edge_radius_est": round(1.1019 * (t ** 2), 4),
        "coordinates_sample_te": coords[0].tolist(),
        "coordinates_sample_le": coords[len(coords) // 2].tolist(),
    }


# ─── 7. export_datcom Handler ────────────────────────────────────────────────

def handle_export_datcom(
    geometry: str = "NACA 0012",
    mach: float = 0.15,
    reynolds: float = 3e6,
) -> Dict[str, Any]:
    from backend.physics.aerodb_engine import AerodynamicDatabaseEngine
    from backend.export.aerodb_export import AeroDBExporter

    db = AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name=geometry,
        alpha_min=-4.0,
        alpha_max=10.0,
        alpha_step=2.0,
        mach_list=[mach],
        reynolds_list=[reynolds],
    )
    datcom_text = AeroDBExporter.export_datcom(db)

    return {
        "geometry": geometry,
        "format": "USAF_DATCOM_CARD_DECK",
        "card_lines_count": len(datcom_text.splitlines()),
        "content_preview": "\n".join(datcom_text.splitlines()[:15]),
        "raw_datcom": datcom_text,
    }


# ─── 8. export_shabp Handler ─────────────────────────────────────────────────

def handle_export_shabp(
    geometry: str = "NACA 0012",
    mach: float = 2.0,
) -> Dict[str, Any]:
    from backend.physics.aerodb_engine import AerodynamicDatabaseEngine
    from backend.export.aerodb_export import AeroDBExporter

    db = AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name=geometry,
        alpha_min=0.0,
        alpha_max=8.0,
        alpha_step=2.0,
        mach_list=[mach],
        reynolds_list=[5e6],
    )
    shabp_text = AeroDBExporter.export_shabp(db)
    return {
        "geometry": geometry,
        "format": "NASA_SHABP_TABULATED_POLAR",
        "card_lines_count": len(shabp_text.splitlines()),
        "content_preview": "\n".join(shabp_text.splitlines()[:12]),
        "raw_shabp": shabp_text,
    }


# ─── 9. mesh_generate Handler ────────────────────────────────────────────────

def handle_mesh_generate(
    geometry: str = "NACA 0012",
    farfield_radius_chords: float = 20.0,
    first_cell_height_m: float = 1e-5,
) -> Dict[str, Any]:
    # Staging configuration for OpenFOAM C-grid
    return {
        "geometry": geometry,
        "mesh_type": "C-GRID_HYBRID_PRISMATIC",
        "farfield_radius_chords": farfield_radius_chords,
        "first_cell_height_m": first_cell_height_m,
        "target_y_plus": 1.0,
        "openfoam_utility": "blockMesh & snappyHexMesh",
        "status": "STAGED_READY_FOR_COLAB_OR_WSL",
        "epistemic_tier": "STAGED_ONLY",
    }


# ─── 10. rocket_trajectory Handler ──────────────────────────────────────────

def handle_rocket_trajectory(
    dry_mass_kg: float = 20.0,
    propellant_mass_kg: float = 15.0,
    burn_time_s: float = 4.0,
    thrust_n: float = 1200.0,
    drag_coefficient_cd: float = 0.45,
    cross_section_area_m2: float = 0.05,
) -> Dict[str, Any]:
    from backend.adapters.rocketpy_adapter import RocketPyAdapter
    adapter = RocketPyAdapter()
    res = adapter.simulate_vertical_trajectory(
        dry_mass_kg=dry_mass_kg,
        propellant_mass_kg=propellant_mass_kg,
        burn_time_s=burn_time_s,
        thrust_n=thrust_n,
        drag_coefficient_cd=drag_coefficient_cd,
        cross_section_area_m2=cross_section_area_m2,
    )
    return res.model_dump()


# ─── 11. mdao_evaluate Handler ──────────────────────────────────────────────

def handle_mdao_evaluate(
    alpha_deg: float = 3.0,
    mach: float = 0.3,
    camber_pct: float = 2.0,
    thickness_pct: float = 12.0,
) -> Dict[str, Any]:
    from backend.adapters.openmdao_adapter import OpenMDAOAdapter
    adapter = OpenMDAOAdapter()
    res = adapter.evaluate_point(
        alpha_deg=alpha_deg,
        mach=mach,
        camber_pct=camber_pct,
        thickness_pct=thickness_pct,
    )
    return res.model_dump()


# ─── 12. su2_case_setup Handler ─────────────────────────────────────────────

def handle_su2_case_setup(
    solver_type: str = "RANS",
    turbulence_model: str = "SA",
    mach: float = 0.5,
    aoa_deg: float = 2.0,
    reynolds: float = 3e6,
    max_iterations: int = 500,
) -> Dict[str, Any]:
    from backend.adapters.su2_adapter import SU2CaseAdapter, SU2RunConfig
    adapter = SU2CaseAdapter()
    cfg = SU2RunConfig(
        solver_type=solver_type,
        turbulence_model=turbulence_model,
        mach=mach,
        aoa_deg=aoa_deg,
        reynolds=reynolds,
        max_iterations=max_iterations,
    )
    config_text = adapter.generate_config_text(cfg)
    return {
        "status": "CONFIG_GENERATED",
        "solver": "SU2",
        "solver_type": solver_type,
        "mach": mach,
        "aoa_deg": aoa_deg,
        "reynolds": reynolds,
        "max_iterations": max_iterations,
        "config_text_preview": config_text[:400] + "...",
        "epistemic_tier": "STAGED_ONLY",
    }


# ─── 13. browser_research Handler ──────────────────────────────────────────

def handle_browser_research(
    url: str = "https://ntrs.nasa.gov/citations/19930091807",
    topic: str = "NACA 0012 Aerodynamics",
) -> Dict[str, Any]:
    from backend.research.browser_research import BoundedBrowserResearch
    agent = BoundedBrowserResearch()
    res = agent.research_url(url, custom_title=topic)
    return res.model_dump()


# ─── 14. export_jsbsim Handler ──────────────────────────────────────────────

def handle_export_jsbsim(
    aircraft_name: str = "AASI_Research_Airframe",
    empty_weight_lbs: float = 2200.0,
    mtow_lbs: float = 3100.0,
    wingspan_ft: float = 36.0,
    wing_area_sqft: float = 174.0,
    cl_0: float = 0.28,
    cl_alpha: float = 4.85,
    cm_alpha: float = -0.85,
    cd_0: float = 0.024,
) -> Dict[str, Any]:
    from backend.export.jsbsim_export import JSBSimExporter, JSBSimMetrics, JSBSimAeroDerivatives
    metrics = JSBSimMetrics(
        aircraft_name=aircraft_name,
        empty_weight_lbs=empty_weight_lbs,
        mtow_lbs=mtow_lbs,
        wingspan_ft=wingspan_ft,
        wing_area_sqft=wing_area_sqft,
    )
    aero = JSBSimAeroDerivatives(
        cl_0=cl_0,
        cl_alpha_per_rad=cl_alpha,
        cm_alpha_per_rad=cm_alpha,
        cd_0=cd_0,
    )
    res = JSBSimExporter.generate_fdm_xml(metrics, aero)
    return {
        "status": "SUCCESS",
        "aircraft_name": res.aircraft_name,
        "provenance_hash": res.provenance_hash,
        "fdm_xml_length": len(res.fdm_xml),
        "fdm_xml_preview": res.fdm_xml[:500] + "...",
        "summary_metrics": res.summary_metrics,
    }


# ─── 15. export_px4 Handler ────────────────────────────────────────────────

def handle_export_px4(
    airframe_name: str = "AASI_Research_UAV",
    airframe_type: str = "vtol_quadplane",
    vehicle_mass_kg: float = 3.5,
    wing_span_m: float = 1.8,
    cruise_speed_ms: float = 18.0,
    stall_speed_ms: float = 11.0,
    max_thrust_n: float = 48.0,
) -> Dict[str, Any]:
    from backend.export.px4_export import PX4Exporter, PX4AirframeConfig, AirframeType
    cfg = PX4AirframeConfig(
        airframe_name=airframe_name,
        airframe_type=AirframeType(airframe_type),
        vehicle_mass_kg=vehicle_mass_kg,
        wing_span_m=wing_span_m,
        cruise_speed_ms=cruise_speed_ms,
        stall_speed_ms=stall_speed_ms,
        max_thrust_n=max_thrust_n,
    )
    res = PX4Exporter.generate_px4_deck(cfg)
    return {
        "status": "SUCCESS",
        "airframe_name": res.airframe_name,
        "airframe_type": res.airframe_type.value,
        "provenance_hash": res.provenance_hash,
        "params_preview": res.params_content[:400] + "...",
        "mixer_preview": res.mixer_content[:400] + "...",
        "tuning_summary": res.tuning_summary,
    }


# ─── Tool Catalog Registration ───────────────────────────────────────────────

def register_aasi_core_skills(bus: Optional[ToolBus] = None) -> ToolBus:
    """Registers all fundamental AASI skills on the specified tool bus."""
    target_bus = bus or global_tool_bus


    # 1. aero_2d_solve
    target_bus.register(
        ToolSpec(
            name="aero_2d_solve",
            description="Discrete vortex panel solver computing CL, CD, CM and Cp surface pressures for airfoils.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters=[
                ToolParameter(name="airfoil", type="string", description="Airfoil designation (e.g. NACA 0012)", default="NACA 0012"),
                ToolParameter(name="alpha_deg", type="float", description="Angle of attack in degrees", default=4.0, bounds=[-20.0, 25.0]),
                ToolParameter(name="reynolds", type="float", description="Reynolds number", default=3e6, bounds=[1e4, 1e8]),
                ToolParameter(name="mach", type="float", description="Mach number", default=0.15, bounds=[0.0, 0.85]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=15.0, memory_mb=32.0),
        ),
        handle_aero_2d_solve,
    )

    # 2. aero_3d_vlm
    target_bus.register(
        ToolSpec(
            name="aero_3d_vlm",
            description="Computes finite 3D wing aerodynamics using Helmbold-Keune compressible aspect ratio corrections.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters=[
                ToolParameter(name="wingspan_m", type="float", description="Wing span in meters", default=10.0, bounds=[0.5, 100.0]),
                ToolParameter(name="aspect_ratio", type="float", description="Wing aspect ratio AR = b^2/S", default=7.0, bounds=[1.0, 30.0]),
                ToolParameter(name="sweep_deg", type="float", description="Leading edge sweep in degrees", default=0.0, bounds=[-10.0, 60.0]),
                ToolParameter(name="alpha_deg", type="float", description="Angle of attack in degrees", default=4.0, bounds=[-15.0, 20.0]),
                ToolParameter(name="mach", type="float", description="Freestream Mach number", default=0.15, bounds=[0.0, 0.85]),
                ToolParameter(name="airfoil", type="string", description="Section airfoil", default="NACA 0012"),
            ],
            cost=ComputationalCostModel(typical_latency_ms=20.0, memory_mb=32.0),
        ),
        handle_aero_3d_vlm,
    )

    # 3. polar_sweep
    target_bus.register(
        ToolSpec(
            name="polar_sweep",
            description="Generates an aerodynamic polar curve over an angle of attack range and identifies max L/D.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters=[
                ToolParameter(name="airfoil", type="string", description="Airfoil designation", default="NACA 0012"),
                ToolParameter(name="alpha_start", type="float", description="Starting AoA in degrees", default=-4.0, bounds=[-20.0, 20.0]),
                ToolParameter(name="alpha_end", type="float", description="Ending AoA in degrees", default=14.0, bounds=[-20.0, 25.0]),
                ToolParameter(name="step_deg", type="float", description="AoA increment step in degrees", default=2.0, bounds=[0.5, 5.0]),
                ToolParameter(name="reynolds", type="float", description="Reynolds number", default=3e6, bounds=[1e4, 1e8]),
                ToolParameter(name="mach", type="float", description="Mach number", default=0.15, bounds=[0.0, 0.85]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=60.0, memory_mb=64.0),
        ),
        handle_polar_sweep,
    )

    # 4. uncertainty_quantify
    target_bus.register(
        ToolSpec(
            name="uncertainty_quantify",
            description="Evaluates standard and expanded uncertainty (GUM / ASME V&V 20) for aerodynamic coefficients.",
            domain=ToolDomain.VALIDATION,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters=[
                ToolParameter(name="coefficient", type="string", description="Coefficient symbol (CL, CD, CM)", default="CL"),
                ToolParameter(name="nominal_value", type="float", description="Nominal computed value", default=0.435),
                ToolParameter(name="reynolds", type="float", description="Reynolds number", default=3e6),
                ToolParameter(name="mach", type="float", description="Mach number", default=0.15),
            ],
            cost=ComputationalCostModel(typical_latency_ms=5.0, memory_mb=16.0),
        ),
        handle_uncertainty_quantify,
    )

    # 5. benchmark_verify
    target_bus.register(
        ToolSpec(
            name="benchmark_verify",
            description="Performs regression verification against frozen Abbott / NASA TM-4083 reference benchmarks.",
            domain=ToolDomain.VALIDATION,
            epistemic_tier=EpistemicTier.DATABASE_REAL,
            parameters=[
                ToolParameter(name="geometry", type="string", description="Benchmark geometry name", default="NACA 0012"),
                ToolParameter(name="alpha_deg", type="float", description="Validation AoA in degrees", default=4.0),
            ],
            cost=ComputationalCostModel(typical_latency_ms=25.0, memory_mb=32.0),
        ),
        handle_benchmark_verify,
    )

    # 6. geometry_parse
    target_bus.register(
        ToolSpec(
            name="geometry_parse",
            description="Evaluates airfoil geometry, camber line, thickness distribution and surface points.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters=[
                ToolParameter(name="geometry", type="string", description="NACA 4-digit code (e.g. NACA 0012)", default="NACA 0012"),
                ToolParameter(name="num_points", type="int", description="Number of coordinates points", default=100),
            ],
            cost=ComputationalCostModel(typical_latency_ms=10.0, memory_mb=16.0),
        ),
        handle_geometry_parse,
    )

    # 7. export_datcom
    target_bus.register(
        ToolSpec(
            name="export_datcom",
            description="Generates USAF Stability and Control DATCOM standard 80-column fixed-card format.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters=[
                ToolParameter(name="geometry", type="string", description="Airfoil geometry name", default="NACA 0012"),
                ToolParameter(name="mach", type="float", description="Mach number", default=0.15),
                ToolParameter(name="reynolds", type="float", description="Reynolds number", default=3e6),
            ],
            cost=ComputationalCostModel(typical_latency_ms=30.0, memory_mb=32.0),
        ),
        handle_export_datcom,
    )

    # 8. export_shabp
    target_bus.register(
        ToolSpec(
            name="export_shabp",
            description="Generates NASA S/HABP format tabulated polars and pressure records.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters=[
                ToolParameter(name="geometry", type="string", description="Airfoil geometry name", default="NACA 0012"),
                ToolParameter(name="mach", type="float", description="Supersonic Mach number", default=2.0),
            ],
            cost=ComputationalCostModel(typical_latency_ms=30.0, memory_mb=32.0),
        ),
        handle_export_shabp,
    )

    # 9. mesh_generate
    target_bus.register(
        ToolSpec(
            name="mesh_generate",
            description="Prepares OpenFOAM C-grid mesh staging parameters for viscous CFD.",
            domain=ToolDomain.CFD,
            epistemic_tier=EpistemicTier.STAGED_ONLY,
            parameters=[
                ToolParameter(name="geometry", type="string", description="Airfoil profile", default="NACA 0012"),
                ToolParameter(name="farfield_radius_chords", type="float", description="Farfield domain radius in chords", default=20.0),
                ToolParameter(name="first_cell_height_m", type="float", description="First boundary layer cell height in meters", default=1e-5),
            ],
            cost=ComputationalCostModel(typical_latency_ms=5.0, memory_mb=16.0),
        ),
        handle_mesh_generate,
    )

    # 10. rocket_trajectory
    target_bus.register(
        ToolSpec(
            name="rocket_trajectory",
            description="Simulates 3-DOF atmospheric vertical rocket trajectory using 4th-order Runge-Kutta flight dynamics.",
            domain=ToolDomain.PROPULSION,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters=[
                ToolParameter(name="dry_mass_kg", type="float", description="Dry vehicle mass (kg)", default=20.0, bounds=[0.1, 1e6]),
                ToolParameter(name="propellant_mass_kg", type="float", description="Propellant mass (kg)", default=15.0, bounds=[0.0, 1e6]),
                ToolParameter(name="burn_time_s", type="float", description="Motor burn duration (s)", default=4.0, bounds=[0.1, 1000.0]),
                ToolParameter(name="thrust_n", type="float", description="Average thrust (N)", default=1200.0, bounds=[0.0, 1e8]),
                ToolParameter(name="drag_coefficient_cd", type="float", description="Vehicle drag coefficient", default=0.45, bounds=[0.0, 5.0]),
                ToolParameter(name="cross_section_area_m2", type="float", description="Frontal aerodynamic area (m^2)", default=0.05, bounds=[0.001, 100.0]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=25.0, memory_mb=32.0),
        ),
        handle_rocket_trajectory,
    )

    # 11. mdao_evaluate
    target_bus.register(
        ToolSpec(
            name="mdao_evaluate",
            description="Evaluates aerodynamic performance and analytical Jacobian sensitivity partials for OpenMDAO.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters=[
                ToolParameter(name="alpha_deg", type="float", description="Angle of attack in degrees", default=3.0, bounds=[-20.0, 25.0]),
                ToolParameter(name="mach", type="float", description="Freestream Mach number", default=0.3, bounds=[0.0, 0.95]),
                ToolParameter(name="camber_pct", type="float", description="Airfoil maximum camber percentage", default=2.0, bounds=[0.0, 10.0]),
                ToolParameter(name="thickness_pct", type="float", description="Airfoil maximum thickness percentage", default=12.0, bounds=[1.0, 40.0]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=10.0, memory_mb=16.0),
        ),
        handle_mdao_evaluate,
    )

    # 12. su2_case_setup
    target_bus.register(
        ToolSpec(
            name="su2_case_setup",
            description="Synthesizes Stanford University Unstructured (SU2) CFD configuration files and monitoring boundaries.",
            domain=ToolDomain.CFD,
            epistemic_tier=EpistemicTier.STAGED_ONLY,
            parameters=[
                ToolParameter(name="solver_type", type="string", description="Governing equations (EULER, RANS)", default="RANS"),
                ToolParameter(name="turbulence_model", type="string", description="Turbulence closure model (NONE, SA, SST)", default="SA"),
                ToolParameter(name="mach", type="float", description="Freestream Mach number", default=0.5, bounds=[0.0, 5.0]),
                ToolParameter(name="aoa_deg", type="float", description="Angle of attack in degrees", default=2.0, bounds=[-30.0, 30.0]),
                ToolParameter(name="reynolds", type="float", description="Reynolds number", default=3e6, bounds=[1e3, 1e9]),
                ToolParameter(name="max_iterations", type="int", description="Maximum solver iterations", default=500, bounds=[10, 50000]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=10.0, memory_mb=16.0),
        ),
        handle_su2_case_setup,
    )

    # 13. browser_research
    target_bus.register(
        ToolSpec(
            name="browser_research",
            description="Performs read-only scientific literature and documentation research with prompt-injection defense.",
            domain=ToolDomain.VALIDATION,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters=[
                ToolParameter(name="url", type="string", description="Target scientific documentation URL", default="https://ntrs.nasa.gov/citations/19930091807"),
                ToolParameter(name="topic", type="string", description="Research topic or document title", default="NACA 0012 Aerodynamics"),
            ],
            cost=ComputationalCostModel(typical_latency_ms=100.0, memory_mb=32.0),
        ),
        handle_browser_research,
    )

    # 14. export_jsbsim
    target_bus.register(
        ToolSpec(
            name="export_jsbsim",
            description="Exports 6-DoF flight dynamics model (FDM) XML deck for JSBSim, FlightGear, and ArduPilot SITL.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters=[
                ToolParameter(name="aircraft_name", type="string", description="Aircraft designation", default="AASI_Research_Airframe"),
                ToolParameter(name="empty_weight_lbs", type="float", description="Empty weight in lbs", default=2200.0, bounds=[10.0, 1e6]),
                ToolParameter(name="mtow_lbs", type="float", description="Maximum takeoff weight in lbs", default=3100.0, bounds=[10.0, 1e6]),
                ToolParameter(name="wingspan_ft", type="float", description="Wingspan in ft", default=36.0, bounds=[1.0, 500.0]),
                ToolParameter(name="wing_area_sqft", type="float", description="Wing area in sq ft", default=174.0, bounds=[1.0, 10000.0]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=15.0, memory_mb=16.0),
        ),
        handle_export_jsbsim,
    )

    # 15. export_px4
    target_bus.register(
        ToolSpec(
            name="export_px4",
            description="Exports PX4 Autopilot parameter files (.params) and actuator mixers (.mix) for multicopters, planes, and VTOLs.",
            domain=ToolDomain.AERODYNAMICS,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters=[
                ToolParameter(name="airframe_name", type="string", description="UAV airframe designation", default="AASI_Research_UAV"),
                ToolParameter(name="airframe_type", type="string", description="Airframe architecture (quadrotor_x, fixed_wing, vtol_quadplane, vtol_tiltrotor)", default="vtol_quadplane"),
                ToolParameter(name="vehicle_mass_kg", type="float", description="Takeoff mass in kg", default=3.5, bounds=[0.1, 500.0]),
                ToolParameter(name="wing_span_m", type="float", description="Wingspan in meters", default=1.8, bounds=[0.1, 50.0]),
                ToolParameter(name="cruise_speed_ms", type="float", description="Cruise airspeed in m/s", default=18.0, bounds=[2.0, 150.0]),
            ],
            cost=ComputationalCostModel(typical_latency_ms=15.0, memory_mb=16.0),
        ),
        handle_export_px4,
    )

    return target_bus


# Auto-register core skills on global ToolBus
register_aasi_core_skills(global_tool_bus)
