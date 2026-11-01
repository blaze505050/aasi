"""
Tests for AASI 2.0 Aerospace & Scientific AI Adapters:
- AeroSandboxAdapter
- OpenAeroStructAdapter
- NeuralOperatorAdapter
- PhysicsNeMoAdapter
- ASBenchAdapter
- OneDAGIAdapter
"""

import math
import pytest
from backend.adapters import (
    AeroSandboxAdapter,
    OpenAeroStructAdapter,
    AeroStructuralInput,
    NeuralOperatorAdapter,
    PhysicsNeMoAdapter,
    ASBenchAdapter,
    OneDAGIAdapter,
)


def test_aerosandbox_atmosphere():
    # Sea level
    sl = AeroSandboxAdapter.get_atmosphere(0.0)
    assert sl.temperature_k == 288.15
    assert sl.pressure_pa == 101325.0
    assert abs(sl.density_kg_m3 - 1.225) < 0.001
    assert abs(sl.speed_of_sound_m_s - 340.29) < 0.5

    # Tropopause (11,000m)
    tp = AeroSandboxAdapter.get_atmosphere(11000.0)
    assert abs(tp.temperature_k - 216.65) < 0.5
    assert tp.density_kg_m3 < 0.40


def test_aerosandbox_airfoil_analysis():
    # NACA 0012 symmetric at alpha=0 deg
    res_0 = AeroSandboxAdapter.analyze_airfoil("NACA 0012", alpha_deg=0.0)
    assert abs(res_0.cl) < 1e-3
    assert abs(res_0.cm) < 1e-3
    assert res_0.cd > 0.005
    assert len(res_0.provenance_hash) == 64
    assert res_0.epistemic_tier == "ANALYTICAL"

    # NACA 0012 at alpha=4 deg
    res_4 = AeroSandboxAdapter.analyze_airfoil("NACA 0012", alpha_deg=4.0)
    assert 0.40 <= res_4.cl <= 0.50
    assert res_4.l_over_d > 18.0
    assert res_4.cl_3d < res_4.cl # 3D finite wing lift slope is lower than 2D infinite section

    # Cambered NACA 4412
    res_4412 = AeroSandboxAdapter.analyze_airfoil("NACA 4412", alpha_deg=0.0)
    assert res_4412.cl > 0.35 # Positive lift at zero alpha due to camber
    assert res_4412.cm < -0.03 # Negative pitching moment due to positive camber


def test_openaerostruct_coupled_solver():
    inp = AeroStructuralInput(
        wing_span_m=8.0,
        root_chord_m=1.2,
        tip_chord_m=0.6,
        flight_velocity_ms=50.0,
        alpha_deg=4.0,
    )
    res = OpenAeroStructAdapter.solve_coupled(inp)
    assert res.lift_total_n > 0.0
    assert res.cl > 0.2
    assert res.tip_deflection_m > 0.0 # Bends upwards under positive lift
    assert res.wing_structural_mass_kg > 5.0
    assert res.is_structurally_sound is True
    assert len(res.provenance_hash) == 64
    assert res.epistemic_tier == "COUPLED_MDO"


def test_neuraloperator_fno_continuous_cp():
    fno_res = NeuralOperatorAdapter.predict_surface_cp(
        airfoil="NACA 0012",
        alpha_deg=4.0,
        num_points=80,
    )
    assert fno_res.num_eval_points == 80
    assert len(fno_res.x_coords) == 80
    assert len(fno_res.cp_upper) == 80
    assert len(fno_res.cp_lower) == 80
    assert fno_res.cl_integrated > 0.30
    assert fno_res.cp_min < 0.0 # Peak suction on upper surface
    assert fno_res.epistemic_tier == "SURROGATE"
    assert len(fno_res.provenance_hash) == 64


def test_physics_nemo_pde_residuals():
    pde_res = PhysicsNeMoAdapter.evaluate_flowfield_pde_residuals(
        reynolds=1.0e6,
        freestream_velocity=45.0,
        grid_dim_x=20,
        grid_dim_y=20,
    )
    assert pde_res.num_collocation_points == 400
    assert pde_res.l2_residual_continuity < 0.08
    assert pde_res.l2_residual_u_momentum < 0.08
    assert pde_res.is_physically_adherent is True
    assert pde_res.epistemic_tier == "PINN_VERIFIED"
    assert len(pde_res.provenance_hash) == 64


def test_as_bench_adapter():
    scenarios = ASBenchAdapter.get_standard_scenarios()
    assert len(scenarios) >= 3

    # Test evaluation of discovery
    scorecard = ASBenchAdapter.evaluate_transonic_drag_discovery(
        discovered_m_dd=0.742,
        proposed_hypothesis="Shock wave formation at supersonic suction peak triggers boundary layer separation and drag divergence (dCD/dM threshold).",
        experimental_plan=[{"mach": 0.40}, {"mach": 0.70}, {"mach": 0.74}, {"mach": 0.78}],
        reported_uncertainty=0.015,
        fabricated_cfd_flag=False,
    )
    assert scorecard.discovery_accuracy_score >= 90.0
    assert scorecard.hypothesis_quality_score >= 90.0
    assert scorecard.epistemic_honesty_score == 100.0
    assert scorecard.composite_as_bench_score >= 90.0


def test_one_d_agi_symbolic_and_dimensionless():
    # 1. Buckingham Pi groups
    groups = OneDAGIAdapter.compute_aerodynamic_dimensionless_groups(
        velocity_ms=50.0,
        chord_m=1.0,
        density_kg_m3=1.225,
        dynamic_viscosity_pa_s=1.789e-5,
        speed_of_sound_ms=340.0,
        lift_force_n=600.0,
        drag_force_n=30.0,
        wing_area_m2=2.0,
    )
    re_grp = next(g for g in groups if g.symbol == "Re")
    cl_grp = next(g for g in groups if g.symbol == "CL")
    assert 3.4e6 <= re_grp.calculated_value <= 3.5e6
    assert 0.15 <= cl_grp.calculated_value <= 0.25

    # 2. Power-law scaling discovery (e.g. skin friction scaling Cf = 0.074 * Re^-0.20)
    re_samples = [1e5, 5e5, 1e6, 5e6, 1e7]
    cf_samples = [0.074 / (re ** 0.2) for re in re_samples]
    law = OneDAGIAdapter.discover_power_law_scaling(re_samples, cf_samples, "Reynolds", "Cf")
    assert abs(law.power_exponents["Reynolds"] - (-0.20)) < 0.001
    assert abs(law.leading_coefficient - 0.074) < 0.001
    assert law.r_squared > 0.999
    assert law.is_physically_consistent is True
