"""
Test Suite for Stage 16: Autonomous Popperian Hypothesis Falsification & Multi-Agent Discovery Loop.
===================================================================================================
Validates:
1. 4-Agent collaborative scientific dialogue (Lead Scientist -> Discretization -> Adversarial -> Metrology Auditor).
2. Popperian logic of falsification: survival under nominal stress vs. falsification under extreme adversarial perturbations.
3. ASME V&V 20 three-grid Richardson extrapolation with Grid Convergence Index (GCI_fine).
4. Bayesian model comparison with Jeffreys Bayes Factor K and publication readiness grading.
5. FastAPI integration endpoints (/api/discovery/presets, /api/discovery/execute).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from aasi_aero_fno.popperian_discovery import (
    PopperianDiscoveryEngine,
    DISCOVERY_PRESETS,
)

client = TestClient(app)


def test_four_agent_scientific_dialogue_structure():
    """Validates that all four scientific agents participate with quantitative evidence."""
    dossier = PopperianDiscoveryEngine.execute_discovery_campaign(
        preset_key="SUPERCRITICAL_BUFFET_DELAY",
        adversarial_rigor=1.0,
        enable_adaptive_meshing=True,
    )

    assert len(dossier.agent_dialogue) == 4
    roles = [m.agent_role for m in dossier.agent_dialogue]
    assert roles == [
        "LEAD_SCIENTIST",
        "DISCRETIZATION_AGENT",
        "ADVERSARIAL_POPPERIAN",
        "METROLOGY_AUDITOR",
    ]

    # Check that each message has quantitative data and high epistemic confidence
    for msg in dossier.agent_dialogue:
        assert msg.epistemic_confidence >= 0.70
        assert len(msg.quantitative_data) > 0
        assert msg.timestamp_s > 0


def test_nominal_corroboration_under_asme_gci():
    """Validates that under nominal rigor, the hypothesis is corroborated with Bayes Factor K > 10 and GCI < 1.5%."""
    dossier = PopperianDiscoveryEngine.execute_discovery_campaign(
        preset_key="SUPERCRITICAL_BUFFET_DELAY",
        adversarial_rigor=1.0,
        enable_adaptive_meshing=True,
    )

    assert dossier.verdict == "CORROBORATED_WITH_HIGH_CONFIDENCE"
    assert dossier.bayes_factor >= 10.0, f"Expected Bayes Factor K >= 10, got {dossier.bayes_factor}"
    assert dossier.asme_gci_fine_pct <= 1.5, f"Expected GCI <= 1.5%, got {dossier.asme_gci_fine_pct}%"
    assert dossier.novelty_score_pct >= 90.0
    assert dossier.publication_readiness == "READY_FOR_NATURE_SCIENCE_PEER_REVIEW"
    assert len(dossier.merkle_provenance_hash) == 64


def test_adversarial_falsification_trigger():
    """Validates that extreme adversarial parameter search identifies unmodeled shock flutter and triggers falsification."""
    dossier = PopperianDiscoveryEngine.execute_discovery_campaign(
        preset_key="SUPERCRITICAL_BUFFET_DELAY",
        adversarial_rigor=2.5,  # High adversarial rigor triggers falsification
        enable_adaptive_meshing=True,
    )

    assert dossier.verdict == "FALSIFIED_BY_NUMERICAL_EVIDENCE"
    assert dossier.bayes_factor < 1.0, f"Expected Bayes Factor K < 1 for falsification, got {dossier.bayes_factor}"
    assert dossier.publication_readiness == "REJECTED_REFALSIFIED_FOR_NEXT_CYCLE"


def test_hypersonic_waverider_preset():
    """Validates hypersonic waverider forebody ablation discovery campaign."""
    dossier = PopperianDiscoveryEngine.execute_discovery_campaign(
        preset_key="HYPERSONIC_WAVERIDER_ABLATION",
        adversarial_rigor=1.0,
        enable_adaptive_meshing=True,
    )
    assert dossier.domain == "Hypersonic Aerothermodynamics (Mach 8 to 14)"
    assert dossier.verdict == "CORROBORATED_WITH_HIGH_CONFIDENCE"
    assert len(dossier.falsification_criteria) >= 1


def test_api_popperian_discovery_routes():
    """Validates FastAPI /api/discovery/presets and /api/discovery/execute endpoints."""
    # Presets
    res_presets = client.get("/api/discovery/presets")
    assert res_presets.status_code == 200
    presets_data = res_presets.json()
    assert "SUPERCRITICAL_BUFFET_DELAY" in presets_data
    assert "HYPERSONIC_WAVERIDER_ABLATION" in presets_data

    # Execute POST
    payload = {
        "preset_key": "STRUT_BRACED_WING_LAMINAR",
        "adversarial_rigor": 1.0,
        "enable_adaptive_meshing": True,
    }
    res_exec = client.post("/api/discovery/execute", json=payload)
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["campaign_id"].startswith("DISCOV-")
    assert exec_data["verdict"] == "CORROBORATED_WITH_HIGH_CONFIDENCE"
    assert len(exec_data["agent_dialogue"]) == 4
    assert exec_data["asme_gci_fine_pct"] <= 1.5
