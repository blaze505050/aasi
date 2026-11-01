"""
Unit tests for AASI Python Client SDK v0.3.0 autonomous multi-agent integration.
Verifies client invocation signatures, MCP tool calling schemas, and CLI subcommands.
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add sdk/python to sys.path
sdk_path = Path(__file__).resolve().parent.parent / "sdk" / "python"
if str(sdk_path) not in sys.path:
    sys.path.insert(0, str(sdk_path))

from aasi_client.client import AASIClient, AASIClientError
from aasi_client.cli import main as cli_main


class TestAASIClientAutonomousSDK(unittest.TestCase):
    def setUp(self):
        self.client = AASIClient(base_url="http://127.0.0.1:8000", api_key="test_key_123")

    @patch.object(AASIClient, "_request")
    def test_run_autonomous_investigation(self, mock_request):
        mock_request.return_value = {
            "investigation_id": "INV-AASI-40-NACA4412",
            "stage": "VERIFICATION_COMPLETE",
            "cl_3d": 0.658,
            "cd_3d": 0.0163,
            "l_over_d": 40.37,
            "cas_score": 29,
            "cas_grade": "Grade 4 (Highest Rigor)",
            "provenance_root_hash": "06879af5aa057282f087bfb2746dc214f212f9e8274a19211e6dbb7732bd1575",
            "specialists_dispatched": 8,
            "events_count": 8,
        }

        result = self.client.run_autonomous_investigation(
            objective_prompt="Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency.",
            airfoil="NACA 4412",
            alpha_deg=4.0,
            reynolds=1.5e6,
            mach=0.18,
            aspect_ratio=8.0,
        )

        self.assertEqual(result["investigation_id"], "INV-AASI-40-NACA4412")
        self.assertEqual(result["specialists_dispatched"], 8)
        self.assertAlmostEqual(result["cl_3d"], 0.658, places=3)
        self.assertEqual(result["cas_score"], 29)
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "/api/v1/investigation/flagship/run")
        self.assertEqual(kwargs["body"]["airfoil"], "NACA 4412")

    @patch.object(AASIClient, "_request")
    def test_list_mcp_tools(self, mock_request):
        mock_request.return_value = [
            {"name": "aerosandbox_vlm_solve", "description": "Solves finite wing VLM"},
            {"name": "openaerostruct_mdo_solve", "description": "Solves aerostructural MDO"},
        ]

        tools = self.client.list_mcp_tools()
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["name"], "aerosandbox_vlm_solve")
        mock_request.assert_called_once_with("GET", "/api/v1/investigation/mcp/tools")

    @patch.object(AASIClient, "_request")
    def test_call_mcp_tool(self, mock_request):
        mock_request.return_value = {
            "status": "SUCCESS",
            "tool_name": "aerosandbox_vlm_solve",
            "content": {"cl_3d": 0.658},
        }

        res = self.client.call_mcp_tool("aerosandbox_vlm_solve", {"alpha_deg": 4.0, "aspect_ratio": 8.0})
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["tool_name"], "aerosandbox_vlm_solve")
        mock_request.assert_called_once_with(
            "POST",
            "/api/v1/investigation/mcp/call",
            body={"name": "aerosandbox_vlm_solve", "arguments": {"alpha_deg": 4.0, "aspect_ratio": 8.0}},
        )


if __name__ == "__main__":
    unittest.main()

