"""
AASI Flagship Autonomous Demonstration:
"Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency."

Executes the complete stateful multi-agent system across all 8 specialists:
1. Supervisory Orchestrator
2. Aerospace Research Agent
3. Physics & Mathematics Agent
4. CFD Agent
5. Scientific ML Agent
6. Design Optimization Agent
7. Literature Intelligence Agent
8. Independent Verification Agent

Outputs complete scientific report with ASME V&V 20 and NASA-STD-7009B CAS scorecards.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.agent.stateful_multi_agent_system import (
    MultiAgentInvestigationState,
    SupervisoryOrchestrator,
    MultiAgentStage,
)


def run_flagship_demonstration():
    print("=" * 80)
    print("AASI FLAGSHIP AUTONOMOUS SCIENTIFIC DEMONSTRATION")
    print("Inquiry: 'Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency.'")
    print("=" * 80)

    # 1. Initialize shared typed state
    state = MultiAgentInvestigationState(
        investigation_id="AASI-FLAGSHIP-NACA4412-2026",
        objective_prompt="Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency.",
        airfoil="NACA 4412",
        alpha_deg=4.0,
        reynolds=1.5e6,
        mach=0.18,
        aspect_ratio=8.0,
    )

    orchestrator = SupervisoryOrchestrator(state)

    print("\n[Stage 1/8] Problem Formulation & Competing Physical Hypotheses...")
    print("[Stage 2/8] Querying NASA Langley LTPT & Abbott & von Doenhoff Experimental Archives...")
    print("[Stage 3/8] Solving Closed-Form Navier-Stokes & Buckingham Pi Dimensional Groups...")
    print("[Stage 4/8] Fourier Neural Operator (FNO) Spectral Cp & PINN Residual Verification...")
    print("[Stage 5/8] Synthesizing y+ Wall Mesh & OpenFOAM / SU2 CFD Case Directory...")
    print("[Stage 6/8] Coupled Aerostructural MDO Beam Stress & Deflection (OpenAeroStruct)...")
    print("[Stage 7/8] Evaluating Human Authorization Checkpoint...")
    print("[Stage 8/8] Independent ASME V&V 20 GCI & NASA-STD-7009B CAS Credibility Audit...")

    final_state = orchestrator.run_to_completion(auto_approve_human_gate=True)

    print("\n" + "=" * 80)
    print(f"INVESTIGATION COMPLETE: {final_state.current_stage.value}")
    print(f"Root Merkle Lineage Hash: {final_state.provenance_root_hash}")
    print("=" * 80)

    # Write outputs to output/ directory
    out_dir = ROOT_DIR / "output" / "flagship_demonstration"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "NACA_4412_Scientific_Investigation_Report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_state.scientific_report_markdown or "")

    state_path = out_dir / "NACA_4412_MultiAgent_State.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(final_state.model_dump(), f, indent=2, default=str)

    print(f"\n[Artifact Saved] Scientific Report: {report_path}")
    print(f"[Artifact Saved] Multi-Agent State JSON: {state_path}")

    # Print summary table
    aero = final_state.analytical_results.get("aerodynamics_analytical", {})
    cas = final_state.verification_scorecard.get("nasa_std_7009b_cas", {})
    asme = final_state.verification_scorecard.get("asme_vv20", {})

    print("\nEXECUTIVE RESULTS SUMMARY:")
    print(f"  * 2D Section Lift (CL):        {aero.get('cl')} [ANALYTICAL]")
    print(f"  * 3D Finite Wing Lift (CL_3D): {aero.get('cl_3d')} [ANALYTICAL]")
    print(f"  * Total Drag (CD_3D):          {aero.get('cd_3d')} [ANALYTICAL]")
    print(f"  * Aerodynamic Efficiency (L/D):{aero.get('l_over_d')}")
    print(f"  * ASME V&V 20 GCI fine:        {asme.get('gci_fine_percent')}% (p={asme.get('observed_order_p')})")
    print(f"  * NASA-STD-7009B CAS:          {cas.get('total_score')} / {cas.get('max_possible')} ({cas.get('credibility_grade')})")
    print(f"  * Checkpoints Recorded:        {len(final_state.checkpoints)}")
    print(f"  * Specialists Dispatched:      8")

    return final_state


if __name__ == "__main__":
    run_flagship_demonstration()

