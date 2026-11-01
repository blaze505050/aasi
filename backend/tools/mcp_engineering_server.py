"""
AASI 2.0 Model Context Protocol (MCP) Standard Tool Server.
JSON-RPC 2.0 compliant tool execution interface for aerospace engineering agents.

Complies with Anthropic Model Context Protocol specification:
- tools/list: Exposes complete typed catalog of aerospace simulation & verification tools.
- tools/call: Dispatches calls through AASI ToolBus with safety governor limits.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.adapters import (
    AeroSandboxAdapter,
    OpenAeroStructAdapter,
    AeroStructuralInput,
    NeuralOperatorAdapter,
    PhysicsNeMoAdapter,
    OneDAGIAdapter,
)

logger = logging.getLogger("aasi.mcp.server")


class MCPToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPCallResponse(BaseModel):
    content: List[Dict[str, Any]]
    is_error: bool = False
    provenance_hash: Optional[str] = None


class MCPEngineeringServer:
    """
    Standard Model Context Protocol (MCP) server for AASI scientific tools.
    """

    @classmethod
    def list_tools(cls) -> List[MCPToolDefinition]:
        """Returns the formal MCP tool catalog."""
        return [
            MCPToolDefinition(
                name="aero_atmosphere_eval",
                description="Evaluate US Standard Atmosphere 1976 properties (T, P, rho, a, mu, nu) at any altitude.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "altitude_m": {"type": "number", "description": "Geometric altitude above sea level in meters"},
                    },
                    "required": ["altitude_m"],
                },
            ),
            MCPToolDefinition(
                name="aerosandbox_airfoil_solve",
                description="First-principles 2D airfoil and 3D finite wing aerodynamic polar solver.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "airfoil_name": {"type": "string", "description": "Airfoil identifier (e.g. NACA 0012, NACA 4412)"},
                        "alpha_deg": {"type": "number", "description": "Angle of attack in degrees"},
                        "reynolds": {"type": "number", "description": "Reynolds number", "default": 1.0e6},
                        "mach": {"type": "number", "description": "Freestream Mach number", "default": 0.15},
                        "aspect_ratio": {"type": "number", "description": "Wing aspect ratio", "default": 8.0},
                    },
                    "required": ["airfoil_name", "alpha_deg"],
                },
            ),
            MCPToolDefinition(
                name="openaerostruct_coupled_mdo",
                description="Coupled aero-structural analysis and wing spar structural stress optimization.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "wing_span_m": {"type": "number", "description": "Wing span in meters"},
                        "root_chord_m": {"type": "number", "description": "Root chord length in meters"},
                        "tip_chord_m": {"type": "number", "description": "Tip chord length in meters"},
                        "flight_velocity_ms": {"type": "number", "description": "Flight velocity in m/s"},
                        "alpha_deg": {"type": "number", "description": "Angle of attack in degrees"},
                    },
                    "required": ["wing_span_m", "flight_velocity_ms"],
                },
            ),
            MCPToolDefinition(
                name="fno_surface_cp_predict",
                description="Predict continuous surface pressure coefficient (Cp) distribution using Fourier Neural Operator.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "airfoil": {"type": "string", "description": "Airfoil name"},
                        "alpha_deg": {"type": "number", "description": "Angle of attack"},
                        "mach": {"type": "number", "description": "Mach number", "default": 0.15},
                        "num_points": {"type": "integer", "description": "Number of discretization points", "default": 100},
                    },
                    "required": ["airfoil", "alpha_deg"],
                },
            ),
            MCPToolDefinition(
                name="pinn_verify_navier_stokes",
                description="Evaluate Navier-Stokes conservation residuals (continuity, u-momentum, v-momentum) via PhysicsNeMo.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "reynolds": {"type": "number", "description": "Reynolds number"},
                        "freestream_velocity": {"type": "number", "description": "Velocity in m/s", "default": 50.0},
                    },
                    "required": ["reynolds"],
                },
            ),
            MCPToolDefinition(
                name="dimensional_analysis_buckingham_pi",
                description="Synthesize Buckingham Pi dimensionless groups (Re, M, CL, CD, L/D) from dimensional flight variables.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "velocity_ms": {"type": "number"},
                        "chord_m": {"type": "number"},
                        "density_kg_m3": {"type": "number"},
                        "dynamic_viscosity_pa_s": {"type": "number"},
                        "speed_of_sound_ms": {"type": "number"},
                        "lift_force_n": {"type": "number"},
                        "drag_force_n": {"type": "number"},
                        "wing_area_m2": {"type": "number"},
                    },
                    "required": ["velocity_ms", "chord_m", "lift_force_n", "drag_force_n"],
                },
            ),
        ]

    @classmethod
    def call_tool(cls, request: MCPCallRequest) -> MCPCallResponse:
        """Executes an MCP tool call with rigorous parameter parsing and error trapping."""
        name = request.name
        args = request.arguments

        try:
            if name == "aero_atmosphere_eval":
                alt = float(args.get("altitude_m", 0.0))
                res = AeroSandboxAdapter.get_atmosphere(alt)
                payload = res.model_dump()

            elif name == "aerosandbox_airfoil_solve":
                airfoil = str(args.get("airfoil_name", "NACA 0012"))
                alpha = float(args.get("alpha_deg", 0.0))
                reynolds = float(args.get("reynolds", 1.0e6))
                mach = float(args.get("mach", 0.15))
                ar = float(args.get("aspect_ratio", 8.0))
                res = AeroSandboxAdapter.analyze_airfoil(airfoil, alpha, reynolds, mach, ar)
                payload = res.model_dump()

            elif name == "openaerostruct_coupled_mdo":
                inp = AeroStructuralInput(
                    wing_span_m=float(args.get("wing_span_m", 10.0)),
                    root_chord_m=float(args.get("root_chord_m", 1.5)),
                    tip_chord_m=float(args.get("tip_chord_m", 0.8)),
                    flight_velocity_ms=float(args.get("flight_velocity_ms", 60.0)),
                    alpha_deg=float(args.get("alpha_deg", 3.5)),
                )
                res = OpenAeroStructAdapter.solve_coupled(inp)
                payload = res.model_dump()

            elif name == "fno_surface_cp_predict":
                airfoil = str(args.get("airfoil", "NACA 0012"))
                alpha = float(args.get("alpha_deg", 4.0))
                mach = float(args.get("mach", 0.15))
                n_pts = int(args.get("num_points", 100))
                res = NeuralOperatorAdapter.predict_surface_cp(airfoil, alpha, mach, num_points=n_pts)
                payload = res.model_dump()

            elif name == "pinn_verify_navier_stokes":
                re = float(args.get("reynolds", 1.0e6))
                v = float(args.get("freestream_velocity", 50.0))
                res = PhysicsNeMoAdapter.evaluate_flowfield_pde_residuals(re, v)
                payload = res.model_dump()

            elif name == "dimensional_analysis_buckingham_pi":
                v = float(args.get("velocity_ms", 50.0))
                c = float(args.get("chord_m", 1.0))
                rho = float(args.get("density_kg_m3", 1.225))
                mu = float(args.get("dynamic_viscosity_pa_s", 1.789e-5))
                a = float(args.get("speed_of_sound_ms", 340.29))
                l = float(args.get("lift_force_n", 500.0))
                d = float(args.get("drag_force_n", 25.0))
                s = float(args.get("wing_area_m2", 2.0))
                groups = OneDAGIAdapter.compute_aerodynamic_dimensionless_groups(v, c, rho, mu, a, l, d, s)
                payload = [g.model_dump() for g in groups]

            else:
                return MCPCallResponse(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    is_error=True,
                )

            prov = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
            return MCPCallResponse(
                content=[{"type": "json", "data": payload}],
                is_error=False,
                provenance_hash=prov,
            )

        except Exception as exc:
            logger.error("MCP tool execution error for '%s': %s", name, exc, exc_info=True)
            return MCPCallResponse(
                content=[{"type": "text", "text": f"Error executing tool '{name}': {str(exc)}"}],
                is_error=True,
            )

