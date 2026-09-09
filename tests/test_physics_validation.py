"""
Exhaustive Physics Validation and Numerical Benchmark Suite for AASI Phase 2.
Independently verifies orbital mechanics, escape velocities, Hohmann transfers,
rocket propulsion, unit dimensions, and verification failure detection.
"""

import math
import pytest
import astropy.constants as const
import astropy.units as u

from backend.tools.orbit import (
    calculate_circular_orbit,
    calculate_escape_velocity,
    calculate_hohmann_transfer,
    BODIES,
)
from backend.tools.rocket import (
    rocket_equation,
    required_mass_ratio,
    propellant_mass_estimation,
    STANDARD_G0,
)
from backend.tools.units import convert_unit
from backend.tools.math_utils import verify_calculation
from backend.tools.registry import tool_registry


# ==============================================================================
# SECTION 4: INDEPENDENT PHYSICS VERIFICATION - CIRCULAR ORBIT
# ==============================================================================

class TestCircularOrbitPhysics:
    """Independent verification of circular Keplerian orbital mechanics."""

    def test_case_a_earth_500km(self):
        """Case A: Earth circular orbit at 500 km altitude."""
        res = calculate_circular_orbit(altitude_km=500.0, central_body="Earth")
        r = res["results"]["orbital_radius_km"]
        v_km_s = res["results"]["orbital_velocity_km_s"]
        period_min = res["results"]["orbital_period_minutes"]
        a_m_s2 = res["results"]["gravitational_acceleration_m_s2"]

        # Independent calculation via Astropy constants
        r_exp = (const.R_earth.to(u.km)).value + 500.0
        mu_exp = (const.G * const.M_earth).to(u.km**3 / u.s**2).value
        v_exp = math.sqrt(mu_exp / r_exp)
        t_exp_min = (2.0 * math.pi * math.sqrt((r_exp**3) / mu_exp)) / 60.0
        a_exp = (mu_exp * 1e9) / ((r_exp * 1000.0)**2)

        assert math.isclose(r, r_exp, rel_tol=1e-5)
        assert math.isclose(v_km_s, v_exp, rel_tol=1e-4)
        assert math.isclose(period_min, t_exp_min, rel_tol=1e-4)
        assert math.isclose(a_m_s2, a_exp, rel_tol=1e-4)
        # Expected engineering reference values
        assert 7.61 <= v_km_s <= 7.62  # ~7.613 km/s
        assert 94.5 <= period_min <= 94.7  # ~94.6 min

    def test_case_b_iss_400km(self):
        """Case B: ISS-like orbit at 400 km altitude."""
        res = calculate_circular_orbit(altitude_km=400.0, central_body="Earth")
        assert math.isclose(res["results"]["orbital_velocity_km_s"], 7.6686, rel_tol=1e-3)
        assert math.isclose(res["results"]["orbital_period_minutes"], 92.56, rel_tol=1e-3)
        assert 8.65 <= res["results"]["gravitational_acceleration_m_s2"] <= 8.70

    def test_case_c_earth_1000km(self):
        """Case C: Higher Earth orbit at 1000 km altitude."""
        res = calculate_circular_orbit(altitude_km=1000.0, central_body="Earth")
        assert math.isclose(res["results"]["orbital_velocity_km_s"], 7.3501, rel_tol=1e-3)
        assert math.isclose(res["results"]["orbital_period_minutes"], 105.12, rel_tol=1e-3)

    def test_case_d_surface_orbit_0km(self):
        """Case D: Theoretical surface orbit (0 km altitude)."""
        res = calculate_circular_orbit(altitude_km=0.0, central_body="Earth")
        # Surface circular velocity ~7.905 km/s, period ~84.49 min (Astropy equatorial R=6378.137 km)
        assert math.isclose(res["results"]["orbital_velocity_km_s"], 7.9054, rel_tol=1e-3)
        assert math.isclose(res["results"]["orbital_period_minutes"], 84.49, rel_tol=1e-3)
        # Surface gravity should be ~9.798 m/s^2
        assert math.isclose(res["results"]["gravitational_acceleration_m_s2"], 9.798, rel_tol=1e-3)

    def test_case_e_invalid_negative_altitude(self):
        """Case E: Invalid negative altitude must raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            calculate_circular_orbit(altitude_km=-500.0, central_body="Earth")

    def test_case_f_moon_100km(self):
        """Case F: Lunar circular orbit at 100 km altitude."""
        res = calculate_circular_orbit(altitude_km=100.0, central_body="Moon")
        r_moon = 1737.4 + 100.0
        mu_moon = BODIES["moon"]["mu_km3_s2"]
        v_exp = math.sqrt(mu_moon / r_moon)
        assert math.isclose(res["results"]["orbital_velocity_km_s"], v_exp, rel_tol=1e-4)
        assert 1.63 <= res["results"]["orbital_velocity_km_s"] <= 1.64
        assert 117.0 <= res["results"]["orbital_period_minutes"] <= 118.0

    def test_case_g_mars_200km(self):
        """Case G: Mars circular orbit at 200 km altitude."""
        res = calculate_circular_orbit(altitude_km=200.0, central_body="Mars")
        r_mars = 3389.5 + 200.0
        mu_mars = BODIES["mars"]["mu_km3_s2"]
        v_exp = math.sqrt(mu_mars / r_mars)
        assert math.isclose(res["results"]["orbital_velocity_km_s"], v_exp, rel_tol=1e-4)
        assert 3.45 <= res["results"]["orbital_velocity_km_s"] <= 3.46
        assert 108.0 <= res["results"]["orbital_period_minutes"] <= 109.5


# ==============================================================================
# SECTION 5: ESCAPE VELOCITY TEST MATRIX
# ==============================================================================

class TestEscapeVelocityPhysics:
    """Test escape velocity scaling v_esc = sqrt(2) * v_circ across celestial bodies."""

    @pytest.mark.parametrize("body,altitude_km", [
        ("Earth", 500.0),
        ("Moon", 100.0),
        ("Mars", 200.0),
        ("Sun", 10000.0),
    ])
    def test_escape_velocity_scaling_sqrt2(self, body, altitude_km):
        """Verify that v_escape / v_circular equals sqrt(2) to high precision."""
        res = calculate_escape_velocity(altitude_km=altitude_km, central_body=body)
        v_esc = res["results"]["escape_velocity_km_s"]
        v_circ = res["results"]["circular_velocity_reference_km_s"]
        ratio = v_esc / v_circ

        assert math.isclose(ratio, math.sqrt(2.0), rel_tol=1e-4)

    def test_earth_escape_velocity_values(self):
        """Earth escape velocity at 500 km altitude."""
        res = calculate_escape_velocity(altitude_km=500.0, central_body="Earth")
        assert math.isclose(res["results"]["escape_velocity_km_s"], 10.7658, rel_tol=1e-3)
        assert math.isclose(res["results"]["escape_velocity_m_s"], 10765.8, rel_tol=1e-3)

    def test_invalid_central_body(self):
        """Unknown planet/body must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown central body 'Jupiter'"):
            calculate_escape_velocity(altitude_km=500.0, central_body="Jupiter")

    def test_invalid_negative_altitude_escape(self):
        """Negative altitude must raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            calculate_escape_velocity(altitude_km=-100.0, central_body="Earth")


# ==============================================================================
# SECTION 6: HOHMANN TRANSFER TEST MATRIX
# ==============================================================================

class TestHohmannTransferPhysics:
    """Test Hohmann transfer orbital transfers, impulse directions, and physical symmetry."""

    def test_case_1_leo_200_to_500km(self):
        """1. 200 km -> 500 km Earth transfer."""
        res = calculate_hohmann_transfer(200.0, 500.0, "Earth")
        assert math.isclose(res["results"]["delta_v1_m_s"], 86.05, rel_tol=1e-2)
        assert math.isclose(res["results"]["delta_v2_m_s"], 85.58, rel_tol=1e-2)
        assert math.isclose(res["results"]["total_delta_v_m_s"], 171.63, rel_tol=1e-2)
        assert math.isclose(res["results"]["transfer_time_minutes"], 45.77, rel_tol=1e-2)

    def test_case_2_leo_500_to_1000km(self):
        """2. 500 km -> 1000 km Earth transfer."""
        res = calculate_hohmann_transfer(500.0, 1000.0, "Earth")
        assert math.isclose(res["results"]["delta_v1_m_s"], 132.35, rel_tol=1e-2)
        assert math.isclose(res["results"]["delta_v2_m_s"], 130.00, rel_tol=1e-2)
        assert math.isclose(res["results"]["total_delta_v_m_s"], 262.35, rel_tol=1e-2)
        assert math.isclose(res["results"]["transfer_time_minutes"], 49.91, rel_tol=1e-2)

    def test_case_3_leo_to_geo(self):
        """3. LEO (300 km) -> GEO (35786 km) transfer."""
        res = calculate_hohmann_transfer(300.0, 35786.0, "Earth")
        # Theoretical LEO to GEO delta-v ~3.895 km/s, transfer time ~5.28 hours
        assert math.isclose(res["results"]["total_delta_v_km_s"], 3.895, rel_tol=1e-2)
        assert 5.25 <= res["results"]["transfer_time_hours"] <= 5.35

    def test_case_4_higher_to_lower_symmetry(self):
        """4. Higher -> lower orbit (500 km -> 200 km) must have identical total dv and time."""
        res_up = calculate_hohmann_transfer(200.0, 500.0, "Earth")
        res_down = calculate_hohmann_transfer(500.0, 200.0, "Earth")

        # Total delta-v and transfer duration must match exactly by Keplerian symmetry
        assert math.isclose(res_up["results"]["total_delta_v_m_s"], res_down["results"]["total_delta_v_m_s"], rel_tol=1e-5)
        assert math.isclose(res_up["results"]["transfer_time_seconds"], res_down["results"]["transfer_time_seconds"], rel_tol=1e-5)
        assert res_up["results"]["transfer_semi_major_axis_km"] == res_down["results"]["transfer_semi_major_axis_km"]

    def test_case_5_identical_radii(self):
        """5. Identical initial and final altitudes must raise ValueError."""
        with pytest.raises(ValueError, match="identical"):
            calculate_hohmann_transfer(500.0, 500.0, "Earth")

    def test_case_6_negative_altitudes(self):
        """6. Negative altitudes must raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            calculate_hohmann_transfer(-200.0, 500.0, "Earth")

    def test_case_7_invalid_body(self):
        """7. Unknown body must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown central body"):
            calculate_hohmann_transfer(200.0, 500.0, "Saturn")

    def test_case_8_extreme_orbit_translunar(self):
        """8. Extreme but valid orbit: Earth LEO (200 km) to Moon orbital radius (384400 km)."""
        res = calculate_hohmann_transfer(200.0, 384400.0, "Earth")
        # Trans-lunar injection delta-v1 ~3.13 km/s, total duration ~5.0 days (120 hours)
        assert 3.10 <= res["results"]["delta_v1_km_s"] <= 3.20
        assert 115.0 <= res["results"]["transfer_time_hours"] <= 125.0


# ==============================================================================
# SECTION 7: ROCKET EQUATION TEST MATRIX
# ==============================================================================

class TestRocketEquationPhysics:
    """Test Tsiolkovsky rocket equation, parameter inversion, and round-trip consistency."""

    def test_normal_case(self):
        """Isp = 350 s, m0 = 10000 kg, mf = 3000 kg."""
        res = rocket_equation(isp_s=350.0, initial_mass_kg=10000.0, final_mass_kg=3000.0)
        c = STANDARD_G0 * 350.0
        expected_dv = c * math.log(10000.0 / 3000.0)
        assert math.isclose(res["results"]["delta_v_m_s"], expected_dv, rel_tol=1e-5)
        assert math.isclose(res["results"]["delta_v_m_s"], 4132.43, rel_tol=1e-3)
        assert res["results"]["propellant_mass_kg"] == 7000.0
        assert math.isclose(res["results"]["propellant_mass_fraction"], 0.7, rel_tol=1e-4)

    @pytest.mark.parametrize("isp", [300.0, 450.0, 1000.0])
    def test_various_isp_values(self, isp):
        """Verify delta-v scaling linearly with Isp."""
        res = rocket_equation(isp_s=isp, initial_mass_kg=10000.0, final_mass_kg=3000.0)
        expected_dv = STANDARD_G0 * isp * math.log(10.0 / 3.0)
        assert math.isclose(res["results"]["delta_v_m_s"], expected_dv, rel_tol=1e-5)

    @pytest.mark.parametrize("m0,mf", [
        (10000.0, 9999.0),   # Very small propellant (1 kg)
        (10000.0, 5000.0),   # 50% propellant
        (10000.0, 1000.0),   # High mass ratio (10:1)
        (10000.0, 100.0),    # Extreme mass ratio (100:1)
    ])
    def test_round_trip_mass_ratio_inversion(self, m0, mf):
        """Round-trip consistency: mass ratio -> delta-v -> required mass ratio."""
        isp = 350.0
        orig_ratio = m0 / mf
        calc_dv = rocket_equation(isp_s=isp, initial_mass_kg=m0, final_mass_kg=mf)["results"]["delta_v_m_s"]
        inv_ratio = required_mass_ratio(delta_v_m_s=calc_dv, isp_s=isp)["results"]["required_mass_ratio"]
        assert math.isclose(orig_ratio, inv_ratio, rel_tol=1e-4)

    def test_zero_propellant_m0_equals_mf(self):
        """m0 == mf must return delta-v = 0.0 m/s without error."""
        res = rocket_equation(isp_s=350.0, initial_mass_kg=5000.0, final_mass_kg=5000.0)
        assert res["results"]["delta_v_m_s"] == 0.0
        assert res["results"]["mass_ratio"] == 1.0
        assert res["results"]["propellant_mass_kg"] == 0.0

    def test_mf_greater_than_m0_raises_error(self):
        """mf > m0 is physically impossible and must raise ValueError."""
        with pytest.raises(ValueError, match="cannot exceed initial wet mass"):
            rocket_equation(isp_s=350.0, initial_mass_kg=5000.0, final_mass_kg=6000.0)

    @pytest.mark.parametrize("m0,mf", [
        (0.0, 1000.0),
        (-1000.0, 500.0),
        (5000.0, 0.0),
        (5000.0, -500.0),
    ])
    def test_non_positive_masses_raise_error(self, m0, mf):
        """Non-positive masses must raise ValueError."""
        with pytest.raises(ValueError, match="both be positive"):
            rocket_equation(isp_s=350.0, initial_mass_kg=m0, final_mass_kg=mf)

    @pytest.mark.parametrize("isp", [0.0, -100.0, -350.0])
    def test_non_positive_isp_raises_error(self, isp):
        """Non-positive Isp must raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            rocket_equation(isp_s=isp, initial_mass_kg=10000.0, final_mass_kg=3000.0)

    def test_propellant_mass_estimation_tool(self):
        """Test propellant_mass_estimation consistency."""
        dry_mass = 2000.0
        isp = 320.0
        target_dv = 3000.0
        res = propellant_mass_estimation(dry_mass_kg=dry_mass, isp_s=isp, delta_v_m_s=target_dv)
        assert res["results"]["dry_mass_kg"] == 2000.0
        assert res["results"]["total_wet_mass_kg"] > 2000.0
        assert res["results"]["propellant_mass_kg"] == round(res["results"]["total_wet_mass_kg"] - dry_mass, 2)


# ==============================================================================
# SECTION 8: DIMENSIONAL / UNIT TESTING (PINT)
# ==============================================================================

class TestDimensionalConversions:
    """Test unit conversions using Pint for distance, velocity, mass, and time."""

    def test_distance_conversion_km_to_m(self):
        res = convert_unit(value=500.0, from_unit="km", to_unit="m")
        assert res["results"]["converted_value"] == 500000.0

    def test_velocity_conversion_km_s_to_m_s(self):
        res = convert_unit(value=7.6126, from_unit="km/s", to_unit="m/s")
        assert math.isclose(res["results"]["converted_value"], 7612.6, rel_tol=1e-5)

    def test_mass_conversion_tonnes_to_kg(self):
        res = convert_unit(value=10.0, from_unit="tonne", to_unit="kg")
        assert res["results"]["converted_value"] == 10000.0

    def test_time_conversion_seconds_to_minutes(self):
        res = convert_unit(value=5677.2, from_unit="second", to_unit="minute")
        assert math.isclose(res["results"]["converted_value"], 94.62, rel_tol=1e-3)

    def test_incompatible_dimensions_raise_error(self):
        """Converting length to mass must raise ValueError."""
        with pytest.raises(ValueError, match="Dimensionality mismatch"):
            convert_unit(value=100.0, from_unit="km", to_unit="kg")

    def test_unknown_unit_raises_error(self):
        """Unknown unit must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown or invalid"):
            convert_unit(value=100.0, from_unit="lightyears_per_banana", to_unit="m")


# ==============================================================================
# SECTION 9: TOOL REGISTRY TESTING
# ==============================================================================

class TestToolRegistryExhaustive:
    """Audit tool registry enumeration and execution dispatch."""

    def test_all_tools_present_in_registry(self):
        tools = {t["name"]: t for t in tool_registry.list_tools()}
        assert "orbit" in tools
        assert "rocket" in tools
        assert "math" in tools
        assert "units" in tools

    def test_orbit_operations_present(self):
        tools = {t["name"]: t for t in tool_registry.list_tools()}
        orbit_ops = {op["name"] for op in tools["orbit"]["operations"]}
        assert "circular_orbit" in orbit_ops
        assert "escape_velocity" in orbit_ops
        assert "hohmann_transfer" in orbit_ops

    def test_rocket_operations_present(self):
        tools = {t["name"]: t for t in tool_registry.list_tools()}
        rocket_ops = {op["name"] for op in tools["rocket"]["operations"]}
        assert "rocket_equation" in rocket_ops
        assert "required_mass_ratio" in rocket_ops
        assert "propellant_mass_estimation" in rocket_ops

    def test_registry_missing_parameters_raises_error(self):
        """Executing with missing required parameter must fail safely."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            tool_registry.execute("orbit", "circular_orbit")

    def test_registry_unknown_tool_raises_error(self):
        """Executing an unknown tool must fail safely."""
        with pytest.raises(ValueError, match="not found"):
            tool_registry.execute("quantum_gravity", "warp_drive")

    def test_registry_unknown_operation_raises_error(self):
        """Executing an unknown operation must fail safely."""
        with pytest.raises(ValueError, match="not supported"):
            tool_registry.execute("orbit", "teleport")


# ==============================================================================
# SECTION 12: VERIFICATION SUBSYSTEM AUDIT - KNOWN BAD RESULT TEST
# ==============================================================================

class TestVerificationSubsystemAudit:
    """Audit the independent verification layer; must detect bad results and perturbations."""

    def test_verifier_accepts_correct_result(self):
        """Verifier accepts recomputed value within tolerance."""
        res = verify_calculation(
            calculated_value=4132.43,
            reference_formula="9.80665 * isp * log(m0 / mf)",
            parameters={"isp": 350.0, "m0": 10000.0, "mf": 3000.0},
            tolerance_rel=1e-4,
        )
        assert res["is_verified"] is True
        assert res["relative_error"] < 1e-4

    def test_verifier_detects_deliberate_perturbation_failure(self):
        """
        CRITICAL TEST: Deliberately perturbed result (dv = 4132.43 + 500 = 4632.43).
        Verifier MUST detect the error and set is_verified to False!
        """
        bad_value = 4632.43  # 500 m/s error introduced deliberately
        res = verify_calculation(
            calculated_value=bad_value,
            reference_formula="9.80665 * isp * log(m0 / mf)",
            parameters={"isp": 350.0, "m0": 10000.0, "mf": 3000.0},
            tolerance_rel=1e-4,
        )
        # Must detect verification failure
        assert res["is_verified"] is False
        # Relative error should be approximately 500 / 4132.43 = ~12.1%
        assert res["relative_error"] > 0.10
        assert math.isclose(res["recomputed_value"], 4132.433, rel_tol=1e-3)

    def test_verifier_detects_wrong_parameters(self):
        """Passing incorrect parameter values must trigger verification failure."""
        res = verify_calculation(
            calculated_value=4132.43,
            reference_formula="9.80665 * isp * log(m0 / mf)",
            parameters={"isp": 250.0, "m0": 10000.0, "mf": 3000.0},  # Wrong Isp (250 instead of 350)
            tolerance_rel=1e-4,
        )
        assert res["is_verified"] is False
        assert res["relative_error"] > 0.20
