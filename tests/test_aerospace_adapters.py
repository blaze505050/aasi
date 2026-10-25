"""
Tests for Phase 11: Aerospace Software Adapters.
Verifies RocketPy, OpenMDAO, and SU2 adapters and their integration with ToolBus.
"""

import pytest
from backend.adapters.rocketpy_adapter import RocketPyAdapter, RocketTrajectoryResult
from backend.adapters.openmdao_adapter import OpenMDAOAdapter, OpenMDAOResult
from backend.adapters.su2_adapter import SU2CaseAdapter, SU2RunConfig, SU2ConvergenceReport
from backend.harness.tool_bus import ToolBus
from backend.harness.skills import register_aasi_core_skills


def test_rocketpy_adapter_simulation():
    adapter = RocketPyAdapter()
    result = adapter.simulate_vertical_trajectory(
        dry_mass_kg=25.0,
        propellant_mass_kg=20.0,
        burn_time_s=5.0,
        thrust_n=1500.0,
        drag_coefficient_cd=0.42,
        cross_section_area_m2=0.04,
    )
    assert isinstance(result, RocketTrajectoryResult)
    assert result.apogee_altitude_m > result.burnout_altitude_m > 0
    assert result.burnout_velocity_m_s > 0
    assert result.max_mach_number > 0
    assert result.max_dynamic_pressure_pa > 0
    assert result.flight_time_to_apogee_s > 5.0
    assert result.max_acceleration_g > 0
    assert len(result.provenance_hash) == 64
    assert result.epistemic_tier == "CALCULATED"


def test_rocketpy_adapter_invalid_inputs():
    adapter = RocketPyAdapter()
    with pytest.raises(ValueError, match="Dry mass must be strictly positive"):
        adapter.simulate_vertical_trajectory(
            dry_mass_kg=-5.0,
            propellant_mass_kg=10.0,
            burn_time_s=3.0,
            thrust_n=500.0,
        )


def test_openmdao_adapter_evaluation():
    adapter = OpenMDAOAdapter()
    res = adapter.evaluate_point(
        alpha_deg=4.0,
        mach=0.25,
        camber_pct=2.0,
        thickness_pct=12.0,
    )
    assert isinstance(res, OpenMDAOResult)
    assert res.cl > 0.3  # Positive lift at positive AoA and camber
    assert res.cd > 0.005 # Positive drag
    assert res.lift_to_drag > 10.0
    assert res.dcl_dalpha > 0.05 # Positive lift curve slope
    assert res.dcd_dalpha > 0.0  # Induced drag increases with AoA
    assert len(res.provenance_hash) == 64


def test_su2_adapter_case_generation_and_history_parsing():
    adapter = SU2CaseAdapter()
    cfg = SU2RunConfig(
        solver_type="RANS",
        turbulence_model="SA",
        mach=0.75,
        aoa_deg=1.5,
        reynolds=4e6,
        max_iterations=400,
    )
    text = adapter.generate_config_text(cfg)
    assert "SOLVER= RANS" in text
    assert "MACH_NUMBER= 0.75" in text
    assert "AOA= 1.5" in text
    assert "REYNOLDS_NUMBER= 4000000.0" in text

    # Synthetic SU2 history CSV
    csv_mock = """Iter, "Res[Rho]", "CL", "CD", "CMz"
1, 1.0000e-01, 0.2500, 0.0350, -0.0400
50, 1.2000e-03, 0.4100, 0.0210, -0.0420
100, 8.5000e-07, 0.4520, 0.0185, -0.0450
"""
    report = adapter.parse_history_csv(csv_mock, target_tolerance=1e-5)
    assert isinstance(report, SU2ConvergenceReport)
    assert report.converged is True
    assert report.final_iteration == 100
    assert report.cl == 0.452
    assert report.cd == 0.0185
    assert report.cm == -0.045
    assert report.epistemic_tier == "VERIFIED"


def test_tool_bus_aerospace_adapter_dispatch():
    bus = ToolBus()
    register_aasi_core_skills(bus)

    # Dispatch rocket_trajectory
    rocket_res = bus.dispatch(
        "rocket_trajectory",
        {
            "dry_mass_kg": 15.0,
            "propellant_mass_kg": 10.0,
            "burn_time_s": 3.0,
            "thrust_n": 900.0,
        },
    )
    assert rocket_res.success is True
    assert rocket_res.output["apogee_altitude_m"] > 0

    # Dispatch mdao_evaluate
    mdao_res = bus.dispatch(
        "mdao_evaluate",
        {
            "alpha_deg": 2.5,
            "mach": 0.2,
        },
    )
    assert mdao_res.success is True
    assert mdao_res.output["cl"] > 0
    assert mdao_res.output["dcl_dalpha"] > 0

    # Dispatch su2_case_setup
    su2_res = bus.dispatch(
        "su2_case_setup",
        {
            "solver_type": "EULER",
            "mach": 0.8,
            "aoa_deg": 3.0,
        },
    )
    assert su2_res.success is True
    assert su2_res.output["status"] == "CONFIG_GENERATED"
    assert su2_res.output["solver"] == "SU2"
