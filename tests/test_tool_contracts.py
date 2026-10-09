"""
Comprehensive test suite for AASI Tool Bus Contracts and Provenance Engine.
Tests input validation, out-of-envelope detection, cryptographic hashing, and contract execution.
"""

import pytest
from backend.tools.registry import tool_registry
from backend.tools.contracts import (
    ToolContract,
    ToolDomain,
    ToolExecutionResult,
    UncertaintyModel,
    ComputationalCostModel,
    EpistemicTier,
)


def test_list_contracts_contains_default_tools():
    contracts = tool_registry.list_contracts()
    assert len(contracts) >= 4
    tool_ids = {c["tool_id"] for c in contracts}
    assert "aerodynamics" in tool_ids
    assert "orbit" in tool_ids
    assert "rocket" in tool_ids
    assert "units" in tool_ids


def test_aerodynamics_contract_execution():
    result = tool_registry.execute_contract(
        tool_id="aerodynamics",
        operation="airfoil_polar",
        airfoil="NACA0012",
        alpha=4.0,
        reynolds=1e6,
        mach=0.15,
    )
    assert isinstance(result, ToolExecutionResult)
    assert result.success
    assert result.domain == ToolDomain.AERODYNAMICS
    assert result.epistemic_tier == EpistemicTier.ANALYTICAL
    assert result.provenance_hash != ""
    assert "cl" in result.output
    assert result.output["cl"] > 0.0


def test_aerodynamics_contract_envelope_warning():
    # Alpha = 25.0 degrees is outside the [-12, 12] validity envelope of the panel solver
    result = tool_registry.execute_contract(
        tool_id="aerodynamics",
        operation="airfoil_polar",
        airfoil="NACA0012",
        alpha=25.0,
        reynolds=1e6,
        mach=0.15,
    )
    assert result.success
    assert result.error_message is not None
    assert "outside certified validity envelope" in result.error_message


def test_contract_missing_required_input_fails_gracefully():
    result = tool_registry.execute_contract(
        tool_id="orbit",
        operation="circular_orbit",
        # altitude_km is missing
    )
    assert not result.success
    assert "Missing required parameter" in result.error_message


def test_custom_tool_contract_registration_and_provenance():
    def custom_stagnation_pressure(mach: float, p_static_pa: float = 101325.0) -> float:
        gamma = 1.4
        return p_static_pa * (1 + 0.5 * (gamma - 1) * mach ** 2) ** (gamma / (gamma - 1))

    contract = ToolContract(
        tool_id="fluid_dynamics",
        operation="stagnation_pressure",
        domain=ToolDomain.AERODYNAMICS,
        epistemic_tier=EpistemicTier.ANALYTICAL,
        description="Isentropic total stagnation pressure calculation",
        handler=custom_stagnation_pressure,
        input_parameters={
            "mach": {"type": "float", "required": True},
            "p_static_pa": {"type": "float", "required": False, "default": 101325.0},
        },
        output_description="Total pressure in Pascals",
        uncertainty=UncertaintyModel(
            typical_relative_error=1e-5,
            validity_envelope={"mach": [0.0, 5.0]},
        ),
    )

    tool_registry.register_contract(contract)
    assert tool_registry.get_contract("fluid_dynamics", "stagnation_pressure") is not None

    res = tool_registry.execute_contract(
        tool_id="fluid_dynamics",
        operation="stagnation_pressure",
        mach=0.8,
        p_static_pa=101325.0,
    )
    assert res.success
    assert res.output > 101325.0
    assert len(res.provenance_hash) == 64
