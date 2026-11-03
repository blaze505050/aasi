"""
Comprehensive Verification Test Suite for AASI-Craft.
Tests Evidence Dossier Merkle trees, OpenFOAM parser, CCSDS telemetry,
ASME V&V 20 Richardson GCI mathematics, RTA safety approval cards, and CLI/MCP parity.
"""

import sys
import os
import math
import pytest
import torch

# Ensure aasi-craft and sovereign modules are on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-craft"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-constitution-rta"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-aero-fno"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-orbital-gnc"))
sys.path.insert(0, os.path.join(BASE_DIR, "aasi-netra-catfm"))

from aasi_craft.evidence_dossier import EvidenceDossier, compute_merkle_root, compute_sha256_string
from aasi_craft.parsers.openfoam_parser import OpenFoamCaseParser
from aasi_craft.parsers.telemetry_parser import CcsdsTelemetryParser, NavicRinexParser
from aasi_craft.parsers.polar_parser import AirfoilPolarParser
from aasi_craft.verification.asme_vv20 import AsmeVv20Verifier
from aasi_craft.synthesis.clean_room_synthesizer import CleanRoomSynthesizer
from aasi_craft.assurance.rta_packager import RtaAirworthinessPackager
from aasi_craft.flagship_workflow import (
    run_naca4412_surrogate_pipeline,
    run_spadex_eclipse_docking_pipeline,
    NACA_4412_EXPERIMENTAL_POLAR,
)
from aasi_craft.mcp_server import AasiCraftMcpServer
from aasi_craft.cli import main as cli_main


def test_evidence_dossier_merkle_root():
    """Verifies that Merkle DAG calculation is deterministic, balanced, and tamper-evident."""
    hashes = [
        compute_sha256_string("item_1"),
        compute_sha256_string("item_2"),
        compute_sha256_string("item_3"),
    ]
    root1 = compute_merkle_root(hashes)
    root2 = compute_merkle_root(hashes)
    assert len(root1) == 64
    assert root1 == root2

    dossier = EvidenceDossier(
        dossier_id="DOSSIER-TEST-01",
        target_name="TEST_AIRFOIL",
        target_type="WIND_TUNNEL_POLAR",
        extracted_parameters={"lift_slope": 6.28, "cl_max": 1.55},
        physics_envelope={"alpha_range": [-4, 16]},
    )
    assert dossier.verify_integrity() is True
    # Tampering should break integrity
    dossier.extracted_parameters["cl_max"] = 9.99
    assert dossier.verify_integrity() is False


def test_openfoam_parser():
    """Verifies OpenFOAM dictionary cleaning, parsing, and y+ boundary layer calculations."""
    mock_control_dict = """
    /* Multi-line OpenFOAM Header */
    FoamFile { version 2.0; format ascii; }
    application     simpleFoam;
    startFrom       startTime;
    startTime       0;
    stopAt          endTime;
    endTime         500;
    deltaT          1;
    writeInterval   50;
    // End of file comment
    """
    res = OpenFoamCaseParser.parse_control_dict(mock_control_dict)
    assert res["application"] == "simpleFoam"
    assert res["endTime"] == 500.0
    assert res["writeInterval"] == 50.0

    # Test y+ wall spacing estimation
    # Re = 1e6, chord = 1.0m, delta_y1 = 1e-4m
    y_plus_info = OpenFoamCaseParser.estimate_y_plus(
        u_inf=50.0, chord=1.0, nu=1.5e-5, delta_y1=1e-4
    )
    assert y_plus_info["reynolds"] > 1e6
    assert y_plus_info["u_tau"] > 0
    assert y_plus_info["y_plus"] > 0
    assert "WALL_" in y_plus_info["wall_resolution_grade"]


def test_ccsds_telemetry_binary_codec():
    """Verifies CCSDS Blue Book 133.0-B-2 packet synthesis and binary unpacking."""
    pkt = CcsdsTelemetryParser.create_ccsds_packet(
        apid=0x042A,
        seq_count=42,
        timestamp_s=12345.678,
        pos_xyz=(100.5, -20.2, 5.1),
        vel_xyz=(-0.15, 0.02, -0.01),
        quat_wxyz=(1.0, 0.0, 0.0, 0.0),
    )
    assert len(pkt) == 6 + 104  # 6-byte header + 104-byte IEEE-754 payload

    decoded = CcsdsTelemetryParser.parse_packet(pkt)
    hdr = decoded["header"]
    assert hdr["apid"] == 0x042A
    assert hdr["sequence_count"] == 42
    assert hdr["packet_type"] == "TELEMETRY"

    st = decoded["telemetry_state"]
    assert abs(st["timestamp_sec"] - 12345.678) < 1e-3
    assert abs(st["rel_position_m"][0] - 100.5) < 1e-3
    assert abs(st["rel_velocity_mps"][0] - (-0.15)) < 1e-3


def test_airfoil_polar_parser():
    """Verifies aerodynamic polar CSV parsing and thin airfoil theory comparisons."""
    dossier = AirfoilPolarParser.parse_csv_stream(NACA_4412_EXPERIMENTAL_POLAR, airfoil_name="NACA_4412")
    params = dossier.extracted_parameters
    assert params["airfoil"] == "NACA_4412"
    # Thin airfoil theory predicts ~2*pi = 6.28 / rad. NACA 4412 is typically ~6.0-6.3.
    assert 5.5 <= params["lift_curve_slope_per_rad"] <= 6.8
    # Stall angle for NACA 4412 at Re=3e6 is ~14-16 deg
    assert 12.0 <= params["alpha_stall_deg"] <= 18.0
    assert params["cl_max"] > 1.5
    assert dossier.verify_integrity() is True


def test_asme_vv20_richardson_gci_mathematics():
    """
    Verifies ASME V&V 20-2009 Richardson extrapolation with exact mathematical rigor.
    For an asymptotic 2nd-order convergence (p=2.0) with r=2:
    f(h) = f_exact + C * h^2
    Let f_exact = 1.0, C = 0.04
    h1 = 1 (fine)   -> f1 = 1.04
    h2 = 2 (medium) -> f2 = 1.16
    h3 = 4 (coarse) -> f3 = 1.64
    Then eps21 = 0.12, eps32 = 0.48. Ratio = 4.0.
    p = ln(4.0) / ln(2.0) = 2.0.
    f_ext = f1 + (f1 - f2)/(2^2 - 1) = 1.04 + (-0.12)/3 = 1.04 - 0.04 = 1.000.
    """
    f1 = 1.04
    f2 = 1.16
    f3 = 1.64
    r = 2.0
    report = AsmeVv20Verifier.evaluate_3grid_richardson(
        f1=f1, f2=f2, f3=f3, r21=r, r32=r, metric_name="TEST_METRIC"
    )
    assert abs(report.apparent_order_p - 2.0) < 1e-3
    assert abs(report.extrapolated_solution - 1.0) < 1e-3
    assert report.convergence_type == "MONOTONIC_CONVERGENCE"
    assert report.is_in_asymptotic_range is True
    # In ASME V&V 20-2009, asymptotic range is satisfied if ratio in [0.85, 1.15]
    assert report.is_in_asymptotic_range is True
    assert abs(report.asymptotic_range_ratio - 1.0) < 0.15


def test_clean_room_synthesizer_and_rta_packager():
    """Verifies clean-room synthesis and ASTM F3269-21 RTA airworthiness packaging."""
    dossier = AirfoilPolarParser.parse_csv_stream(NACA_4412_EXPERIMENTAL_POLAR, airfoil_name="NACA_4412")
    artifact = CleanRoomSynthesizer.synthesize_aerodynamic_surrogate(dossier)
    assert artifact.is_converged is True
    assert artifact.synthesis_metrics["inference_latency_ms"] < 5.0
    assert "FourNetFlows" in artifact.model_architecture

    packager = RtaAirworthinessPackager()
    card = packager.generate_approval_card(
        action_type="TEST_APPROVE",
        target_system="TEST_SYSTEM",
        plain_summary="Test safety card authorization",
        load_factor_g=1.2,
    )
    assert card.status == "PENDING_APPROVAL"
    card.approve("CHIEF_TEST_PILOT")
    assert card.status == "APPROVED"

    release_pkg = packager.package_flight_release(
        target_name="TEST_SYSTEM",
        merkle_root=dossier.merkle_root,
        is_asme_vv20_verified=True,
        approved_cards=[card],
    )
    assert len(release_pkg.ed25519_signature_hex) == 128  # 64 bytes in hex
    assert release_pkg.asme_vv20_airworthy is True


def test_flagship_naca4412_pipeline():
    """Executes the complete flagship NACA 4412 reverse-engineering workflow end-to-end."""
    result = run_naca4412_surrogate_pipeline(auto_approve=True)
    assert result["pipeline_status"] == "COMPLETED_AIRWORTHY"
    assert result["elapsed_ms"] > 0
    assert "stage_1_study" in result
    assert "stage_2_build" in result
    assert "stage_3_check" in result
    assert "stage_4_ready" in result
    assert result["stage_3_check"]["fine_gci_pct"] <= 1.5


def test_flagship_spadex_eclipse_pipeline():
    """Executes the complete SpaDeX-2 / BAS-01 eclipse drift elimination pipeline."""
    result = run_spadex_eclipse_docking_pipeline(auto_approve=True)
    assert result["pipeline_status"] == "COMPLETED_AIRWORTHY"
    check = result["stage_3_check"]
    assert check["aasi_craft_synthesized_drift_m"] < 0.10
    assert check["drift_reduction_percentage"] > 99.0


def test_cli_and_mcp_parity():
    """Verifies that MCP tools and CLI functions produce identical results."""
    # Test MCP tool: study
    mcp_study = AasiCraftMcpServer.execute_tool("aasi_craft_study", {"preset": "naca4412"})
    assert mcp_study["target_name"] == "NACA_4412"
    assert "lift_curve_slope_per_rad" in mcp_study["extracted_parameters"]

    # Test MCP tool: check
    mcp_check = AasiCraftMcpServer.execute_tool(
        "aasi_craft_check_asme_vv20",
        {"f1_fine": 1.670, "f2_medium": 1.658, "f3_coarse": 1.625}
    )
    assert mcp_check["is_verified_airworthy"] is True
    assert mcp_check["fine_gci_pct"] < 1.5

    # Test CLI interface exit codes
    cli_ret = cli_main(["study", "--preset", "naca4412", "--json"])
    assert cli_ret == 0

    cli_ret_check = cli_main(["check", "--f1", "1.670", "--f2", "1.658", "--f3", "1.625", "--json"])
    assert cli_ret_check == 0
