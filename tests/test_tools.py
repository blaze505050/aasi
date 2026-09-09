"""
Unit and integration tests for AASI Engineering Tools Subsystem.
Validates orbital mechanics, rocketry, symbolic mathematics, registry, and agent routing.
"""

import pytest
import math
from unittest.mock import AsyncMock, patch
from backend.tools.orbit import calculate_circular_orbit, calculate_escape_velocity, calculate_hohmann_transfer
from backend.tools.rocket import rocket_equation, required_mass_ratio, propellant_mass_estimation
from backend.tools.math_utils import evaluate_symbolic_expression, solve_symbolic_equation, verify_calculation
from backend.tools.registry import tool_registry
from backend.agent import AASIAgent


# --- 1. Orbital Mechanics Tests ---

def test_circular_orbit_earth_500km():
    res = calculate_circular_orbit(altitude_km=500.0, central_body="Earth")
    assert res["tool"] == "orbit"
    assert res["calculation"] == "circular_orbit"
    assert res["inputs"]["altitude_km"] == 500.0
    
    # Earth radius ~6378.137 km -> r ~ 6878.137 km
    # v = sqrt(398600.44 / 6878.137) ~ 7.613 km/s
    assert math.isclose(res["results"]["orbital_velocity_km_s"], 7.613, rel_tol=1e-3)
    assert math.isclose(res["results"]["orbital_period_minutes"], 94.6, rel_tol=1e-2)
    assert len(res["assumptions"]) > 0


def test_circular_orbit_invalid_altitude():
    with pytest.raises(ValueError, match="non-negative"):
        calculate_circular_orbit(altitude_km=-100.0)


def test_escape_velocity_earth_500km():
    res = calculate_escape_velocity(altitude_km=500.0, central_body="Earth")
    assert res["tool"] == "orbit"
    assert res["calculation"] == "escape_velocity"
    
    # v_esc = sqrt(2) * v_circ ~ 1.4142 * 7.613 ~ 10.766 km/s
    assert math.isclose(res["results"]["escape_velocity_km_s"], 10.766, rel_tol=1e-3)
    assert math.isclose(res["results"]["ratio_to_circular"], math.sqrt(2.0), rel_tol=1e-4)


def test_hohmann_transfer_200_to_500km():
    res = calculate_hohmann_transfer(initial_altitude_km=200.0, final_altitude_km=500.0, central_body="Earth")
    assert res["tool"] == "orbit"
    assert res["calculation"] == "hohmann_transfer"
    assert res["results"]["total_delta_v_m_s"] > 0.0
    # Expected delta-v for 200 to 500 km with Astropy Earth radius is 171.63 m/s
    assert math.isclose(res["results"]["total_delta_v_m_s"], 171.63, rel_tol=1e-2)
    assert res["results"]["transfer_time_minutes"] > 0.0


def test_hohmann_transfer_identical_altitudes():
    with pytest.raises(ValueError, match="cannot be identical"):
        calculate_hohmann_transfer(initial_altitude_km=300.0, final_altitude_km=300.0)


# --- 2. Rocket / Propulsion Tests ---

def test_rocket_equation_basic():
    # Isp = 350 s, m0 = 10000 kg, mf = 3000 kg
    res = rocket_equation(isp_s=350.0, initial_mass_kg=10000.0, final_mass_kg=3000.0)
    assert res["tool"] == "rocket"
    assert res["calculation"] == "tsiolkovsky_rocket_equation"
    
    # Delta-v = 9.80665 * 350 * ln(10000 / 3000) ~ 3432.3275 * 1.20397 ~ 4132.4 m/s
    assert math.isclose(res["results"]["delta_v_m_s"], 4132.4, rel_tol=1e-3)
    assert res["results"]["propellant_mass_kg"] == 7000.0
    assert math.isclose(res["results"]["mass_ratio"], 3.3333, rel_tol=1e-3)


def test_rocket_equation_invalid_mass():
    with pytest.raises(ValueError, match="cannot exceed initial wet mass"):
        rocket_equation(isp_s=300.0, initial_mass_kg=5000.0, final_mass_kg=6000.0)


def test_rocket_equation_zero_propellant():
    res = rocket_equation(isp_s=300.0, initial_mass_kg=5000.0, final_mass_kg=5000.0)
    assert res["results"]["delta_v_m_s"] == 0.0
    assert res["results"]["propellant_mass_kg"] == 0.0
    assert res["results"]["mass_ratio"] == 1.0


def test_required_mass_ratio():
    # Target Delta-v = 4132.4 m/s with Isp = 350 s -> mass ratio should be ~3.333
    res = required_mass_ratio(delta_v_m_s=4132.4, isp_s=350.0)
    assert math.isclose(res["results"]["required_mass_ratio"], 3.333, rel_tol=1e-3)


def test_propellant_mass_estimation():
    # Dry mass = 3000 kg, Isp = 350, Delta-v = 4132.4 -> propellant ~ 7000 kg
    res = propellant_mass_estimation(dry_mass_kg=3000.0, isp_s=350.0, delta_v_m_s=4132.4)
    assert math.isclose(res["results"]["propellant_mass_kg"], 7000.0, rel_tol=1e-2)


# --- 3. Symbolic Mathematics & Verification Tests ---

def test_symbolic_expression_evaluation():
    res = evaluate_symbolic_expression("x**2 + 2*x + 1", substitutions={"x": 3.0})
    assert res["tool"] == "math"
    assert res["results"]["numeric_result"] == 16.0
    assert "x" in res["results"]["free_symbols"]


def test_symbolic_equation_solver():
    res = solve_symbolic_equation("v**2 - 25 = 0", "v")
    assert res["tool"] == "math"
    assert "-5" in res["results"]["solutions"]
    assert "5" in res["results"]["solutions"]


def test_independent_verification():
    # Check verification passes when calculated matches reference
    res = verify_calculation(
        calculated_value=4132.4,
        reference_formula="9.80665 * 350 * log(10000 / 3000)",
        parameters={},
        tolerance_rel=1e-3,
    )
    assert res["is_verified"] is True
    assert res["relative_error"] < 1e-3


# --- 4. Tool Registry Tests ---

def test_tool_registry_discovery():
    tools = tool_registry.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "orbit" in tool_names
    assert "rocket" in tool_names
    assert "math" in tool_names


def test_tool_registry_execution():
    res = tool_registry.execute("orbit", "circular_orbit", altitude_km=400.0)
    assert res["tool"] == "orbit"
    assert res["results"]["orbital_velocity_km_s"] > 7.0


def test_tool_registry_invalid_tool():
    with pytest.raises(ValueError, match="not found"):
        tool_registry.execute("unknown_tool", "op")


# --- 5. Agent Tool Routing & Fallback Tests ---

@pytest.mark.asyncio
async def test_agent_conceptual_question_no_tool():
    agent = AASIAgent()
    
    mock_llm_response = {
        "response": "A Hohmann transfer is an elliptical orbital transfer maneuver...",
        "model": "qwen2.5:0.5b",
        "status": "success",
    }
    
    with patch.object(agent, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_response
        result = await agent.process_chat("What is a Hohmann transfer?")
        
    assert len(result["tool_calls"]) == 0
    assert len(result["calculations"]) == 0
    assert "Hohmann transfer" in result["response"]


@pytest.mark.asyncio
async def test_agent_numerical_orbital_question_triggers_tool():
    agent = AASIAgent()
    
    mock_llm_response = {
        "response": "The circular orbital velocity at 500 km altitude is approximately 7.61 km/s with a period of 94.6 minutes.",
        "model": "qwen2.5:0.5b",
        "status": "success",
    }
    
    with patch.object(agent, "generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_response
        result = await agent.process_chat("What is the circular orbital velocity at 500 km altitude around Earth?")
        
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool"] == "orbit"
    assert result["tool_calls"][0]["operation"] == "circular_orbit"
    assert result["tool_calls"][0]["status"] == "success"
    assert len(result["calculations"]) == 1
    assert result["calculations"][0]["results"]["orbital_velocity_km_s"] > 7.0
    assert len(result["tool_calls"][0]["trace"]) >= 4


@pytest.mark.asyncio
async def test_agent_malformed_question_returns_validation_notice():
    agent = AASIAgent()
    
    # Query with negative altitude
    result = await agent.process_chat("What is the circular orbital velocity at -500 km altitude around Earth?")
    
    assert result["status"] == "validation_error"
    assert result["tool_calls"][0]["status"] == "validation_error"
    assert "Parameter Validation Notice" in result["response"]
    assert len(result["calculations"]) == 0
