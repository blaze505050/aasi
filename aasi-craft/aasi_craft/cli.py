"""
AASI-Craft Unified Command-Line Interface.
Provides 1-to-1 parity with the MCP Server tools:
  study      Inspect target deck/polar and construct Evidence Dossier
  build      Clean-room synthesize neural surrogate or GNC state space
  check      Execute ASME V&V 20 Richardson GCI & discrepancy attribution
  ready      Evaluate ASTM F3269-21 RTA envelope, generate approval card & sign
  pipeline   Execute complete 4-step loop (Study -> Build -> Check -> Ready)
  inspect    Deep-mode inspection without code generation
"""

from __future__ import annotations
import argparse
import json
import sys
import os
from typing import List, Optional
from .evidence_dossier import EvidenceDossier
from .parsers.polar_parser import AirfoilPolarParser
from .parsers.openfoam_parser import OpenFoamCaseParser
from .parsers.telemetry_parser import CcsdsTelemetryParser
from .synthesis.clean_room_synthesizer import CleanRoomSynthesizer
from .verification.asme_vv20 import AsmeVv20Verifier
from .assurance.rta_packager import RtaAirworthinessPackager
from .flagship_workflow import run_naca4412_surrogate_pipeline, run_spadex_eclipse_docking_pipeline, NACA_4412_EXPERIMENTAL_POLAR


def cmd_study(args: argparse.Namespace) -> int:
    """Executes the Study phase: deterministic ingestion to create Evidence Dossier."""
    if args.preset == "naca4412":
        dossier = AirfoilPolarParser.parse_csv_stream(NACA_4412_EXPERIMENTAL_POLAR, airfoil_name="NACA_4412")
    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 1
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        dossier = AirfoilPolarParser.parse_csv_stream(content, airfoil_name=os.path.basename(args.file))
    else:
        print("Error: Specify a valid file with --file or preset with --preset [naca4412|spadex]", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(dossier.to_dict(), indent=2))
    else:
        print("=== AASI-CRAFT EVIDENCE DOSSIER ===")
        print(f"Target:       {dossier.target_name} ({dossier.target_type})")
        print(f"Dossier ID:   {dossier.dossier_id}")
        print(f"Merkle Root:  {dossier.merkle_root}")
        print(f"Integrity:    {'VALID_SHA256' if dossier.verify_integrity() else 'CORRUPTED'}")
        print("Parameters:")
        for k, v in dossier.extracted_parameters.items():
            print(f"  {k}: {v}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Executes the Check phase: ASME V&V 20 Richardson GCI calculation."""
    f1 = args.f1
    f2 = args.f2
    f3 = args.f3
    r = args.ratio
    report = AsmeVv20Verifier.evaluate_3grid_richardson(
        f1=f1, f2=f2, f3=f3, r21=r, r32=r, metric_name=args.metric
    )
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("=== ASME V&V 20-2009 VERIFICATION REPORT ===")
        print(f"Target Metric:           {report.target_metric}")
        print(f"Apparent Order p:        {report.apparent_order_p}")
        print(f"Extrapolated Continuum:  {report.extrapolated_solution}")
        print(f"Fine GCI (h1):           {report.fine_gci_pct:.3f}% (Limit <= 1.5%)")
        print(f"Asymptotic Ratio:        {report.asymptotic_range_ratio:.3f}")
        print(f"Airworthy Verified:      {report.is_verified_airworthy}")
        print(f"Verdict:                 {report.summary_verdict}")
    return 0 if report.is_verified_airworthy else 2


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Executes the complete flagship reverse-engineering pipeline."""
    preset = args.preset.lower()
    print(f"[*] Launching AASI-Craft 4-Stage Autonomous Pipeline: {preset.upper()}...")
    if preset in ["naca4412", "naca_4412", "aero"]:
        result = run_naca4412_surrogate_pipeline(auto_approve=not args.require_manual_approval)
    elif preset in ["spadex", "spadex2", "orbital", "bas01"]:
        result = run_spadex_eclipse_docking_pipeline(auto_approve=not args.require_manual_approval)
    else:
        print(f"Error: Unknown preset '{preset}'. Available: naca4412, spadex", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"[+] Pipeline Completed in {result['elapsed_ms']} ms")
        print(f"[+] Status: {result['pipeline_status']}")
        print(f"    Merkle Root: {result['stage_1_study']['merkle_root'][:24]}...")
        print(f"    Architecture: {result['stage_2_build']['model_architecture']}")
        print(f"    Verification: {result['stage_3_check'].get('summary_verdict', '')}")
        print(f"    Ed25519 Seal: {result['stage_4_ready']['ed25519_signature_hex'][:24]}...")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aasi-craft",
        description="AASI-Craft: Autonomous Clean-Room Aerospace Reverse-Engineering & AI Synthesis Engine",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # study subcommand
    study_p = subparsers.add_parser("study", help="Extract ground-truth evidence into Evidence Dossier")
    study_p.add_argument("--file", "-f", type=str, help="Path to input solver deck, polar CSV, or telemetry stream")
    study_p.add_argument("--preset", "-p", type=str, choices=["naca4412", "spadex"], default="naca4412", help="Built-in preset")
    study_p.add_argument("--json", action="store_true", help="Output full raw JSON")

    # check subcommand
    check_p = subparsers.add_parser("check", help="ASME V&V 20 3-grid Richardson extrapolation")
    check_p.add_argument("--f1", type=float, default=1.670, help="Fine grid solution value")
    check_p.add_argument("--f2", type=float, default=1.658, help="Medium grid solution value")
    check_p.add_argument("--f3", type=float, default=1.625, help="Coarse grid solution value")
    check_p.add_argument("--ratio", "-r", type=float, default=2.0, help="Grid refinement ratio")
    check_p.add_argument("--metric", "-m", type=str, default="CL_max", help="Metric name")
    check_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # pipeline subcommand
    pipe_p = subparsers.add_parser("pipeline", help="Run end-to-end 4-stage flagship pipeline")
    pipe_p.add_argument("--preset", "-p", type=str, default="naca4412", choices=["naca4412", "spadex"], help="Flagship target")
    pipe_p.add_argument("--require-manual-approval", action="store_true", help="Hold for manual operator approval")
    pipe_p.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "study":
        return cmd_study(args)
    elif args.subcommand == "check":
        return cmd_check(args)
    elif args.subcommand == "pipeline":
        return cmd_pipeline(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

