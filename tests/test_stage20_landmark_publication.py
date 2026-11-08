"""
Unit and Integration Tests for Stage 20: The Autonomous Discovery Machine & Landmark Publication Synthesizer.
=============================================================================================================
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from aasi_aero_fno.landmark_publication_synthesizer import (
    LandmarkPublicationSynthesizer,
    PUBLICATION_PRESETS,
    generate_nature_latex_manuscript,
    generate_bibtex_citations,
    generate_reproducibility_dockerfile,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_landmark_publication_synthesis_nature():
    """Validates camera-ready academic manuscript synthesis for Nature."""
    dossier = LandmarkPublicationSynthesizer.synthesize_publication(
        preset_key="NATURE_AEROSPACE_LANDMARK",
        target_mach=0.85,
    )

    assert "Nature" in dossier.target_journal
    assert dossier.publication_readiness_score >= 99.0
    assert len(dossier.merkle_provenance_root) == 64

    # Discovered airframe metrics
    af = dossier.discovered_airframe
    assert af.airframe_designation == "AASI-Apex-S1 Supercritical Morphing Airframe"
    assert af.buffet_onset_mach >= 0.88
    assert af.buffet_mach_improvement_pct >= 12.0
    assert af.wave_drag_reduction_pct >= 25.0
    assert af.asme_richardson_gci_pct < 0.5, "ASME Richardson GCI must be under 0.5% for landmark publication"
    assert af.epistemic_confidence_pct >= 99.0

    # Figures & checklist
    assert len(dossier.figures) >= 3
    for fig in dossier.figures:
        assert fig.title
        assert fig.caption
        assert "data_series" in fig.__dict__

    for rule, passed in dossier.peer_review_checklist.items():
        assert passed is True, f"Peer review check failed: {rule}"


def test_latex_manuscript_structure():
    """Verifies that generated LaTeX manuscript is syntactically sound and contains all required scientific proofs."""
    dossier = LandmarkPublicationSynthesizer.synthesize_publication("NATURE_AEROSPACE_LANDMARK")
    tex = dossier.latex_manuscript_text

    assert "\\documentclass[fleqn,10pt]{wlscirep}" in tex
    assert "\\begin{abstract}" in tex
    assert "\\end{abstract}" in tex
    assert "\\section*{Introduction}" in tex
    assert "\\section*{Results}" in tex
    assert "\\section*{Methods}" in tex
    assert "AASI-Apex-S1" in tex
    assert "GCI_{21}" in tex
    assert "\\bibliography{" in tex


def test_reproducibility_dockerfile():
    """Verifies that Docker reproducibility container contains strict environment pins and tests."""
    dockerfile = generate_reproducibility_dockerfile()

    assert "FROM python:3.12-slim-bookworm" in dockerfile
    assert "AASI_REPRODUCIBILITY_SEED=42" in dockerfile
    assert "ASME_VV20_STRICT_MODE=1" in dockerfile
    assert "pytest" in dockerfile


def test_bibtex_bibliography():
    """Verifies standard BibTeX aerospace citations."""
    bib = generate_bibtex_citations()

    assert "@article{li2020fourier" in bib
    assert "@article{ling2016reynolds" in bib
    assert "@standard{asme2009standard" in bib
    assert "@standard{rtca2011do178c" in bib


def test_api_landmark_publication_endpoints(client):
    """Verifies FastAPI endpoints for Stage 20 Landmark Publication Synthesizer."""
    # 1. Presets endpoint
    res_presets = client.get("/api/publication/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert "NATURE_AEROSPACE_LANDMARK" in presets
    assert "SCIENCE_ROBOTICS_AUTONOMY" in presets
    assert "JFM_TURBULENCE_SCIML" in presets

    # 2. Synthesize endpoint
    payload = {
        "preset_key": "NATURE_AEROSPACE_LANDMARK",
        "target_mach": 0.85,
    }
    res_synth = client.post("/api/publication/synthesize", json=payload)
    assert res_synth.status_code == 200
    data = res_synth.json()

    assert "dossier_id" in data
    assert "discovered_airframe" in data
    assert data["discovered_airframe"]["airframe_designation"] == "AASI-Apex-S1 Supercritical Morphing Airframe"
    assert data["publication_readiness_score"] >= 99.0
    assert len(data["figures"]) >= 3
    assert "latex_manuscript_text" in data
    assert "bibtex_citations" in data
    assert "dockerfile_reproducibility" in data
