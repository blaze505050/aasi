"""
Central tool registry for AASI engineering tools.
Enables dynamic tool discovery, validation, and execution.
"""

from typing import Any, Callable, Dict, List, Optional
import inspect

from backend.tools.orbit import (
    calculate_circular_orbit,
    calculate_escape_velocity,
    calculate_hohmann_transfer,
)
from backend.tools.rocket import (
    rocket_equation,
    required_mass_ratio,
    propellant_mass_estimation,
)
from backend.tools.math_utils import (
    evaluate_symbolic_expression,
    solve_symbolic_equation,
    verify_calculation,
)
from backend.tools.units import convert_unit
from backend.physics.panel_solver import calculate_airfoil_aerodynamics
from backend.tools.contracts import (
    ToolContract,
    ToolDomain,
    ToolExecutionResult,
    UncertaintyModel,
    ComputationalCostModel,
    EpistemicTier,
)


class ToolRegistry:
    """Central registry and execution dispatcher for AASI scientific tools."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._contracts: Dict[str, ToolContract] = {}
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        operations: Dict[str, Callable],
        operation_descriptions: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a new tool and its supported operations."""
        op_meta = {}
        op_descs = operation_descriptions or {}

        for op_name, fn in operations.items():
            sig = inspect.signature(fn)
            params = [
                {
                    "name": param.name,
                    "default": None if param.default == inspect.Parameter.empty else param.default,
                    "required": param.default == inspect.Parameter.empty,
                }
                for param in sig.parameters.values()
            ]
            op_meta[op_name] = {
                "function": fn,
                "description": op_descs.get(op_name, fn.__doc__.strip() if fn.__doc__ else ""),
                "parameters": params,
            }

        self._tools[name] = {
            "name": name,
            "description": description,
            "operations": op_meta,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return public metadata for all registered tools."""
        catalog = []
        for name, tool in self._tools.items():
            catalog.append({
                "name": name,
                "description": tool["description"],
                "operations": [
                    {
                        "name": op_name,
                        "description": op_data["description"],
                        "parameters": op_data["parameters"],
                    }
                    for op_name, op_data in tool["operations"].items()
                ],
            })
        return catalog

    def execute(self, tool_name: str, operation: str, **params) -> Dict[str, Any]:
        """
        Execute a registered tool operation with provided arguments.
        """
        if tool_name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available}")

        tool = self._tools[tool_name]
        if operation not in tool["operations"]:
            available_ops = ", ".join(tool["operations"].keys())
            raise ValueError(
                f"Operation '{operation}' not supported by tool '{tool_name}'. Available operations: {available_ops}"
            )

        op_data = tool["operations"][operation]
        fn = op_data["function"]

        # Filter and cast params to match function signature
        sig = inspect.signature(fn)
        bound_args = {}
        for param_name, param in sig.parameters.items():
            if param_name in params:
                val = params[param_name]
                # Cast float if appropriate
                if param.annotation in (float, "float") and isinstance(val, (int, str)):
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                bound_args[param_name] = val
            elif param.default == inspect.Parameter.empty:
                raise ValueError(f"Missing required parameter '{param_name}' for {tool_name}.{operation}")

        return fn(**bound_args)

    def register_contract(self, contract: ToolContract) -> None:
        """Register a strongly typed tool contract."""
        key = f"{contract.tool_id}.{contract.operation}"
        self._contracts[key] = contract

    def get_contract(self, tool_id: str, operation: str) -> Optional[ToolContract]:
        """Retrieve a registered tool contract."""
        return self._contracts.get(f"{tool_id}.{operation}")

    def list_contracts(self) -> List[Dict[str, Any]]:
        """List metadata for all formal tool contracts."""
        res = []
        for key, c in self._contracts.items():
            res.append({
                "contract_id": key,
                "tool_id": c.tool_id,
                "operation": c.operation,
                "domain": c.domain.value,
                "epistemic_tier": c.epistemic_tier.value,
                "description": c.description,
                "uncertainty": c.uncertainty.model_dump(),
                "cost": c.cost.model_dump(),
            })
        return res

    def execute_contract(self, tool_id: str, operation: str, **params) -> ToolExecutionResult:
        """Execute a tool through its formal contract with provenance verification."""
        contract = self.get_contract(tool_id, operation)
        if not contract:
            raise ValueError(f"No formal contract registered for '{tool_id}.{operation}'")
        return contract.execute(**params)

    def _register_default_tools(self) -> None:
        """Register the built-in Phase 2 tools."""
        # 1. Orbital Mechanics
        self.register_tool(
            name="orbit",
            description="Orbital mechanics, circular velocities, orbital periods, escape velocities, and Hohmann transfers using Astropy constants.",
            operations={
                "circular_orbit": calculate_circular_orbit,
                "escape_velocity": calculate_escape_velocity,
                "hohmann_transfer": calculate_hohmann_transfer,
            },
            operation_descriptions={
                "circular_orbit": "Calculate velocity and orbital period for a circular orbit at a given altitude.",
                "escape_velocity": "Calculate parabolic escape velocity from a given altitude.",
                "hohmann_transfer": "Calculate Hohmann transfer delta-v requirements and transfer duration between two circular orbits.",
            },
        )

        # 2. Rocket Propulsion
        self.register_tool(
            name="rocket",
            description="Preliminary rocket propulsion sizing, Tsiolkovsky rocket equation, mass ratios, and propellant estimation.",
            operations={
                "rocket_equation": rocket_equation,
                "required_mass_ratio": required_mass_ratio,
                "propellant_mass_estimation": propellant_mass_estimation,
            },
            operation_descriptions={
                "rocket_equation": "Compute ideal Delta-v, mass ratio, and propellant mass from Isp and initial/final masses.",
                "required_mass_ratio": "Compute the required mass ratio (m0/mf) to achieve a desired Delta-v with a given Isp.",
                "propellant_mass_estimation": "Estimate propellant mass needed to achieve a target Delta-v for a dry mass.",
            },
        )

        # 3. Symbolic Mathematics & Verification
        self.register_tool(
            name="math",
            description="Symbolic expression evaluation, analytical equation solving, and independent numerical verification with SymPy.",
            operations={
                "symbolic_evaluation": evaluate_symbolic_expression,
                "solve_equation": solve_symbolic_equation,
                "verify_calculation": verify_calculation,
            },
            operation_descriptions={
                "symbolic_evaluation": "Safely evaluate and simplify symbolic mathematical expressions.",
                "solve_equation": "Analytically solve an equation for a specified target variable.",
                "verify_calculation": "Independently verify a numerical result against a reference formula.",
            },
        )

        # 4. Dimensional Analysis & Units
        self.register_tool(
            name="units",
            description="Dimensional analysis and verified unit conversions using Pint.",
            operations={
                "convert": convert_unit,
            },
            operation_descriptions={
                "convert": "Convert a numerical quantity from one unit to another across consistent physical dimensions.",
            },
        )

        # 5. Fast Aerodynamics
        self.register_tool(
            name="aerodynamics",
            description="Subsonic 2D airfoil aerodynamic coefficient calculations (CL, CD, CM) using the discrete vortex panel method.",
            operations={
                "airfoil_polar": calculate_airfoil_aerodynamics,
            },
            operation_descriptions={
                "airfoil_polar": "Compute lift, drag, and moment coefficients for an airfoil at given AoA, Reynolds, and Mach.",
            },
        )

        # Register Formal Tool Contracts
        def _adapt_airfoil_polar(
            geometry: str = "NACA 0012",
            airfoil: Optional[str] = None,
            alpha: Optional[float] = None,
            alpha_deg: float = 4.0,
            reynolds: float = 3e6,
            mach: float = 0.15,
        ) -> Dict[str, Any]:
            geom = airfoil or geometry
            aoa = alpha if alpha is not None else alpha_deg
            res = calculate_airfoil_aerodynamics(geometry=geom, alpha_deg=aoa, reynolds=reynolds, mach=mach)
            return {
                "cl": res["results"]["CL"],
                "cd": res["results"]["CD"],
                "cm": res["results"]["CM"],
                "raw": res,
            }

        self.register_contract(
            ToolContract(
                tool_id="aerodynamics",
                operation="airfoil_polar",
                domain=ToolDomain.AERODYNAMICS,
                epistemic_tier=EpistemicTier.ANALYTICAL,
                description="Subsonic discrete vortex panel solver with Karman-Tsien compressibility correction.",
                handler=_adapt_airfoil_polar,
                input_parameters={
                    "geometry": {"type": "str", "required": False, "default": "NACA 0012"},
                    "airfoil": {"type": "str", "required": False},
                    "alpha": {"type": "float", "required": False, "default": 0.0},
                    "alpha_deg": {"type": "float", "required": False, "default": 0.0},
                    "reynolds": {"type": "float", "required": False, "default": 1e6},
                    "mach": {"type": "float", "required": False, "default": 0.0},
                },
                output_description="Aerodynamic force coefficients (cl, cd, cm) and raw calculations",
                uncertainty=UncertaintyModel(
                    typical_relative_error=0.03,
                    confidence_level=0.95,
                    validity_envelope={"alpha": [-12.0, 12.0], "alpha_deg": [-12.0, 12.0], "mach": [0.0, 0.7]},
                    known_limitations=["Inviscid potential flow with boundary-layer approximations; cannot predict deep stall or shock waves"],
                ),
                cost=ComputationalCostModel(typical_latency_ms=8.0, memory_mb=32.0, device_requirement="CPU"),
            )
        )

        self.register_contract(
            ToolContract(
                tool_id="orbit",
                operation="circular_orbit",
                domain=ToolDomain.ORBITAL,
                epistemic_tier=EpistemicTier.ANALYTICAL,
                description="Closed-form Keplerian circular velocity and orbital period.",
                handler=calculate_circular_orbit,
                input_parameters={"altitude_km": {"type": "float", "required": True}},
                output_description="Orbital velocity in km/s and period in minutes",
                uncertainty=UncertaintyModel(
                    typical_relative_error=0.001,
                    confidence_level=0.99,
                    validity_envelope={"altitude_km": [100.0, 100000.0]},
                ),
                cost=ComputationalCostModel(typical_latency_ms=2.0, memory_mb=16.0),
            )
        )

        self.register_contract(
            ToolContract(
                tool_id="rocket",
                operation="rocket_equation",
                domain=ToolDomain.PROPULSION,
                epistemic_tier=EpistemicTier.ANALYTICAL,
                description="Tsiolkovsky rocket equation calculation.",
                handler=rocket_equation,
                input_parameters={
                    "isp": {"type": "float", "required": True},
                    "m0": {"type": "float", "required": True},
                    "mf": {"type": "float", "required": True},
                },
                output_description="Delta-v, mass ratio, and propellant mass",
                uncertainty=UncertaintyModel(typical_relative_error=0.0001),
                cost=ComputationalCostModel(typical_latency_ms=1.0, memory_mb=16.0),
            )
        )

        self.register_contract(
            ToolContract(
                tool_id="units",
                operation="convert",
                domain=ToolDomain.UNITS,
                epistemic_tier=EpistemicTier.ANALYTICAL,
                description="Pint-verified physical unit conversion.",
                handler=convert_unit,
                input_parameters={
                    "value": {"type": "float", "required": True},
                    "from_unit": {"type": "str", "required": True},
                    "to_unit": {"type": "str", "required": True},
                },
                output_description="Converted numerical value and dimensionality",
                uncertainty=UncertaintyModel(typical_relative_error=1e-6),
                cost=ComputationalCostModel(typical_latency_ms=2.0, memory_mb=16.0),
            )
        )


# Global singleton instance
tool_registry = ToolRegistry()
