"""
AASI-Craft Model Context Protocol (MCP) Tool Server.
Provides 1-to-1 tool parity with the AASI-Craft CLI, enabling autonomous AI agents
to perform deterministic aerospace reverse-engineering, ASME V&V 20 verification,
and airworthiness packaging.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List
from .evidence_dossier import EvidenceDossier
from .parsers.polar_parser import AirfoilPolarParser
from .parsers.openfoam_parser import OpenFoamCaseParser
from .parsers.telemetry_parser import CcsdsTelemetryParser
from .synthesis.clean_room_synthesizer import CleanRoomSynthesizer
from .verification.asme_vv20 import AsmeVv20Verifier
from .assurance.rta_packager import RtaAirworthinessPackager
from .flagship_workflow import (
    run_naca4412_surrogate_pipeline,
    run_spadex_eclipse_docking_pipeline,
    NACA_4412_EXPERIMENTAL_POLAR,
)


class AasiCraftMcpServer:
    """
    Exposes AASI-Craft primitives to autonomous agents via standardized tool schemas.
    """

    TOOLS = [
        {
            "name": "aasi_craft_study",
            "description": "Inspects target CFD deck, polar CSV, or telemetry stream to construct an immutable Evidence Dossier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preset": {"type": "string", "enum": ["naca4412", "spadex"], "description": "Built-in target preset"},
                    "file_content": {"type": "string", "description": "Raw text content of polar or dictionary (optional)"},
                    "target_name": {"type": "string", "description": "Identifier name for target system"}
                },
                "required": ["preset"]
            }
        },
        {
            "name": "aasi_craft_check_asme_vv20",
            "description": "Executes ASME V&V 20 3-grid Richardson extrapolation to verify numerical convergence and GCI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "f1_fine": {"type": "number", "description": "Fine grid solution value"},
                    "f2_medium": {"type": "number", "description": "Medium grid solution value"},
                    "f3_coarse": {"type": "number", "description": "Coarse grid solution value"},
                    "refinement_ratio": {"type": "number", "default": 2.0, "description": "Grid refinement ratio (>= 1.3)"},
                    "metric_name": {"type": "string", "default": "CL_max", "description": "Target engineering metric"}
                },
                "required": ["f1_fine", "f2_medium", "f3_coarse"]
            }
        },
        {
            "name": "aasi_craft_run_pipeline",
            "description": "Runs the complete autonomous 4-stage loop (Study -> Build -> Check -> Ready) for a given aerospace mission.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preset": {"type": "string", "enum": ["naca4412", "spadex"], "description": "Mission preset"},
                    "auto_approve": {"type": "boolean", "default": True, "description": "Whether to auto-approve RTA flight safety cards"}
                },
                "required": ["preset"]
            }
        }
    ]

    @classmethod
    def execute_tool(cls, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an MCP tool call and returns structured, tamper-evident results."""
        if tool_name == "aasi_craft_study":
            preset = arguments.get("preset", "naca4412")
            if preset == "naca4412":
                dossier = AirfoilPolarParser.parse_csv_stream(NACA_4412_EXPERIMENTAL_POLAR, airfoil_name="NACA_4412")
                return dossier.to_dict()
            elif preset == "spadex":
                pkt = CcsdsTelemetryParser.create_ccsds_packet(
                    apid=0x042A, seq_count=1, timestamp_s=10.0,
                    pos_xyz=(12.5, 0.0, 0.0), vel_xyz=(-0.1, 0.0, 0.0), quat_wxyz=(1.0, 0.0, 0.0, 0.0)
                )
                dossier = CcsdsTelemetryParser.parse_telemetry_stream(pkt, stream_name="SPADEX_SAMPLE")
                return dossier.to_dict()
            raise ValueError(f"Unknown preset: {preset}")

        elif tool_name == "aasi_craft_check_asme_vv20":
            f1 = float(arguments["f1_fine"])
            f2 = float(arguments["f2_medium"])
            f3 = float(arguments["f3_coarse"])
            r = float(arguments.get("refinement_ratio", 2.0))
            metric = arguments.get("metric_name", "CL_max")
            report = AsmeVv20Verifier.evaluate_3grid_richardson(f1=f1, f2=f2, f3=f3, r21=r, r32=r, metric_name=metric)
            return report.to_dict()

        elif tool_name == "aasi_craft_run_pipeline":
            preset = arguments.get("preset", "naca4412")
            auto_approve = arguments.get("auto_approve", True)
            if preset == "naca4412":
                return run_naca4412_surrogate_pipeline(auto_approve=auto_approve)
            elif preset == "spadex":
                return run_spadex_eclipse_docking_pipeline(auto_approve=auto_approve)
            raise ValueError(f"Unknown preset: {preset}")

        raise ValueError(f"Tool not found: {tool_name}")

