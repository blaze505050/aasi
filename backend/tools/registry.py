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


class ToolRegistry:
    """Central registry and execution dispatcher for AASI scientific tools."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
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


# Global singleton instance
tool_registry = ToolRegistry()
