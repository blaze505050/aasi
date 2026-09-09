"""
33-Query Agent Routing, Parameter Extraction, and Execution Accuracy Matrix for Phase 2.
Evaluates local agent performance across conceptual, numerical, ambiguous, and adversarial queries.
"""

import asyncio
import json
import math
import sys
from typing import Any, Dict, List

from backend.agent import default_agent

# Reconfigure stdout for utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BENCHMARK_QUERIES: List[Dict[str, Any]] = [
    # 1. Conceptual queries
    {
        "id": 1,
        "query": "What is a Hohmann transfer and when is it used?",
        "expected_intent": "conceptual",
        "expected_tool": None,
    },
    {
        "id": 2,
        "query": "What is specific impulse and why is it measured in seconds?",
        "expected_intent": "conceptual",
        "expected_tool": None,
    },
    {
        "id": 3,
        "query": "Explain escape velocity from a gravitational potential perspective.",
        "expected_intent": "conceptual",
        "expected_tool": None,
    },
    {
        "id": 4,
        "query": "What is orbital period and how does Kepler's third law define it?",
        "expected_intent": "conceptual",
        "expected_tool": None,
    },
    {
        "id": 5,
        "query": "Explain the Tsiolkovsky rocket equation and its physical derivation.",
        "expected_intent": "conceptual",
        "expected_tool": None,
    },

    # 2. Orbital mechanics calculations
    {
        "id": 6,
        "query": "Calculate the orbital velocity and period for a satellite in circular Earth orbit at 500 km altitude.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.circular_orbit",
        "expected_params": {"altitude_km": 500.0, "central_body": "Earth"},
    },
    {
        "id": 7,
        "query": "What is the orbital speed and period at 400 km altitude in low Earth orbit?",
        "expected_intent": "calculation",
        "expected_tool": "orbit.circular_orbit",
        "expected_params": {"altitude_km": 400.0, "central_body": "Earth"},
    },
    {
        "id": 8,
        "query": "Calculate circular orbit velocity at 1000 km altitude.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.circular_orbit",
        "expected_params": {"altitude_km": 1000.0, "central_body": "Earth"},
    },
    {
        "id": 9,
        "query": "Calculate circular orbit at 100 km altitude around the Moon.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.circular_orbit",
        "expected_params": {"altitude_km": 100.0, "central_body": "Moon"},
    },
    {
        "id": 10,
        "query": "Calculate circular orbital velocity at 200 km altitude around Mars.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.circular_orbit",
        "expected_params": {"altitude_km": 200.0, "central_body": "Mars"},
    },
    {
        "id": 11,
        "query": "Calculate circular orbit velocity at 0 km altitude on Earth.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.circular_orbit",
        "expected_params": {"altitude_km": 0.0, "central_body": "Earth"},
    },

    # 3. Escape velocity calculations
    {
        "id": 12,
        "query": "Calculate the escape velocity from Earth at 500 km altitude.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.escape_velocity",
        "expected_params": {"altitude_km": 500.0, "central_body": "Earth"},
    },
    {
        "id": 13,
        "query": "Calculate escape velocity for Earth at 400 km altitude.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.escape_velocity",
        "expected_params": {"altitude_km": 400.0, "central_body": "Earth"},
    },
    {
        "id": 14,
        "query": "What is the escape velocity from the Moon at 100 km altitude?",
        "expected_intent": "calculation",
        "expected_tool": "orbit.escape_velocity",
        "expected_params": {"altitude_km": 100.0, "central_body": "Moon"},
    },
    {
        "id": 15,
        "query": "Calculate the escape velocity from Mars at 200 km altitude.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.escape_velocity",
        "expected_params": {"altitude_km": 200.0, "central_body": "Mars"},
    },
    {
        "id": 16,
        "query": "Calculate the escape velocity from the Sun at 10000 km altitude.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.escape_velocity",
        "expected_params": {"altitude_km": 10000.0, "central_body": "Sun"},
    },

    # 4. Hohmann transfer calculations
    {
        "id": 17,
        "query": "Compute the delta-v needed for a Hohmann transfer from 200 km to 500 km circular Earth orbit.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.hohmann_transfer",
        "expected_params": {"initial_altitude_km": 200.0, "final_altitude_km": 500.0, "central_body": "Earth"},
    },
    {
        "id": 18,
        "query": "Calculate Hohmann transfer delta-v between 500 km and 1000 km around Earth.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.hohmann_transfer",
        "expected_params": {"initial_altitude_km": 500.0, "final_altitude_km": 1000.0, "central_body": "Earth"},
    },
    {
        "id": 19,
        "query": "Calculate Hohmann transfer delta-v from 300 km to 35786 km for GEO insertion.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.hohmann_transfer",
        "expected_params": {"initial_altitude_km": 300.0, "final_altitude_km": 35786.0, "central_body": "Earth"},
    },
    {
        "id": 20,
        "query": "Calculate Hohmann transfer from 500 km to 200 km orbit around Earth.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.hohmann_transfer",
        "expected_params": {"initial_altitude_km": 500.0, "final_altitude_km": 200.0, "central_body": "Earth"},
    },
    {
        "id": 21,
        "query": "Calculate Hohmann transfer between 100 km and 500 km around Mars.",
        "expected_intent": "calculation",
        "expected_tool": "orbit.hohmann_transfer",
        "expected_params": {"initial_altitude_km": 100.0, "final_altitude_km": 500.0, "central_body": "Mars"},
    },

    # 5. Rocket propulsion calculations
    {
        "id": 22,
        "query": "A rocket has an Isp of 350 s, initial mass of 10000 kg, and dry mass of 3000 kg. What is its delta-v?",
        "expected_intent": "calculation",
        "expected_tool": "rocket.rocket_equation",
        "expected_params": {"isp_s": 350.0, "initial_mass_kg": 10000.0, "final_mass_kg": 3000.0},
    },
    {
        "id": 23,
        "query": "Calculate rocket delta-v with Isp = 300 s, initial mass = 5000 kg, and final mass = 2000 kg.",
        "expected_intent": "calculation",
        "expected_tool": "rocket.rocket_equation",
        "expected_params": {"isp_s": 300.0, "initial_mass_kg": 5000.0, "final_mass_kg": 2000.0},
    },
    {
        "id": 24,
        "query": "Calculate rocket delta-v for Isp = 450 s, initial mass of 20000 kg, final mass of 4000 kg.",
        "expected_intent": "calculation",
        "expected_tool": "rocket.rocket_equation",
        "expected_params": {"isp_s": 450.0, "initial_mass_kg": 20000.0, "final_mass_kg": 4000.0},
    },
    {
        "id": 25,
        "query": "Calculate the required mass ratio to achieve a target delta-v of 4000 m/s with an Isp of 350 s.",
        "expected_intent": "calculation",
        "expected_tool": "rocket.required_mass_ratio",
        "expected_params": {"delta_v_m_s": 4000.0, "isp_s": 350.0},
    },
    {
        "id": 26,
        "query": "Calculate required mass ratio for delta-v = 3000 m/s with Isp = 300 s.",
        "expected_intent": "calculation",
        "expected_tool": "rocket.required_mass_ratio",
        "expected_params": {"delta_v_m_s": 3000.0, "isp_s": 300.0},
    },

    # 6. Ambiguous / clarification queries
    {
        "id": 27,
        "query": "How fast does a satellite move?",
        "expected_intent": "clarification",
        "expected_tool": "agent_reasoning.request_clarification_orbital_velocity",
    },
    {
        "id": 28,
        "query": "How much delta-v do I need?",
        "expected_intent": "clarification",
        "expected_tool": "agent_reasoning.request_clarification_delta_v",
    },
    {
        "id": 29,
        "query": "How much fuel does a rocket need?",
        "expected_intent": "clarification",
        "expected_tool": "agent_reasoning.request_clarification_propellant_mass",
    },

    # 7. Adversarial / edge cases
    {
        "id": 30,
        "query": "Calculate circular orbit at -500 km altitude.",
        "expected_intent": "validation_error",
        "expected_tool": "orbit.circular_orbit",
    },
    {
        "id": 31,
        "query": "A rocket has an Isp of 350 s, initial mass of 5000 kg, and dry mass of 6000 kg. What is its delta-v?",
        "expected_intent": "validation_error",
        "expected_tool": "rocket.rocket_equation",
    },
    {
        "id": 32,
        "query": "Calculate escape velocity for Jupiter at 500 km altitude.",
        "expected_intent": "validation_error",
        "expected_tool": "orbit.escape_velocity",
    },
    {
        "id": 33,
        "query": "Convert 500 km to m.",
        "expected_intent": "calculation",
        "expected_tool": "units.convert",
        "expected_params": {"value": 500.0, "from_unit": "km", "to_unit": "m"},
    },
]


async def run_benchmark():
    print("=" * 80)
    print("AASI PHASE 2 — 33-QUERY AGENT ROUTING & ACCURACY BENCHMARK")
    print("=" * 80)

    routing_correct = 0
    param_correct = 0
    tool_exec_success = 0
    verification_success = 0
    total_queries = len(BENCHMARK_QUERIES)

    results_table = []

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        q = item["query"]
        exp_intent = item["expected_intent"]
        exp_tool = item["expected_tool"]
        exp_params = item.get("expected_params")

        raw_intent = default_agent.detect_calculation_intent(q)
        
        # Determine actual intent and tool
        if raw_intent is None:
            act_intent = "conceptual"
            act_tool = None
            act_params = None
        elif raw_intent[0] == "clarification":
            act_intent = "clarification"
            act_tool = f"agent_reasoning.request_clarification_{raw_intent[1]}"
            act_params = None
        else:
            act_tool = f"{raw_intent[0]}.{raw_intent[1]}"
            act_params = raw_intent[2]
            act_intent = "calculation"

        # Check routing
        is_route_ok = False
        if exp_intent in ("conceptual", "clarification"):
            is_route_ok = (act_intent == exp_intent)
        elif exp_intent in ("calculation", "validation_error"):
            is_route_ok = (act_tool == exp_tool)
        if is_route_ok:
            routing_correct += 1

        # Check parameter extraction
        is_param_ok = True
        if exp_params:
            if not act_params:
                is_param_ok = False
            else:
                for k, v in exp_params.items():
                    if k not in act_params or act_params[k] != v:
                        is_param_ok = False
                        break
        if is_param_ok and exp_intent != "conceptual":
            param_correct += 1
        elif exp_intent == "conceptual":
            param_correct += 1

        # Run process_chat
        try:
            chat_res = await default_agent.process_chat(q)
            status = chat_res.get("status")
            tool_calls = chat_res.get("tool_calls", [])
            verif = chat_res.get("verification")

            if exp_intent == "validation_error":
                is_exec_ok = (status == "validation_error")
            elif exp_intent == "clarification":
                is_exec_ok = (status == "clarification_needed")
            else:
                is_exec_ok = (status == "success")
            
            if is_exec_ok:
                tool_exec_success += 1

            # Verification check
            is_verif_ok = "N/A"
            if verif is not None:
                if verif.get("is_verified") is True:
                    is_verif_ok = "PASS"
                    verification_success += 1
                else:
                    is_verif_ok = "FAIL"

            results_table.append({
                "id": qid,
                "query": q,
                "exp_tool": exp_tool or "None (Conceptual)",
                "act_tool": act_tool or "None (Conceptual)",
                "route_status": "PASS" if is_route_ok else "FAIL",
                "param_status": "PASS" if is_param_ok else "FAIL",
                "exec_status": "PASS" if is_exec_ok else "FAIL",
                "verif_status": is_verif_ok,
            })
            print(f"[{qid:02d}/33] Route: {'✓' if is_route_ok else '✗'} | Params: {'✓' if is_param_ok else '✗'} | Exec: {'✓' if is_exec_ok else '✗'} | {q[:55]}...")
        except Exception as e:
            results_table.append({
                "id": qid,
                "query": q,
                "exp_tool": exp_tool or "None",
                "act_tool": act_tool or "None",
                "route_status": "PASS" if is_route_ok else "FAIL",
                "param_status": "PASS" if is_param_ok else "FAIL",
                "exec_status": f"ERROR: {str(e)}",
                "verif_status": "N/A",
            })
            print(f"[{qid:02d}/33] ERROR: {e}")

    route_pct = (routing_correct / total_queries) * 100.0
    param_pct = (param_correct / total_queries) * 100.0
    exec_pct = (tool_exec_success / total_queries) * 100.0

    print("\n" + "=" * 80)
    print(f"BENCHMARK SUMMARY ({total_queries} QUERIES):")
    print(f"- Routing Accuracy:          {routing_correct}/{total_queries} ({route_pct:.1f}%)")
    print(f"- Parameter Extraction:      {param_correct}/{total_queries} ({param_pct:.1f}%)")
    print(f"- Execution Success Rate:    {tool_exec_success}/{total_queries} ({exec_pct:.1f}%)")
    print(f"- Independent Verifications: {verification_success} recomputations verified with SymPy")
    print("=" * 80)

    with open("tests/benchmarks/agent_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_queries": total_queries,
                "routing_accuracy_pct": route_pct,
                "param_accuracy_pct": param_pct,
                "exec_success_pct": exec_pct,
                "results": results_table,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    asyncio.run(run_benchmark())
