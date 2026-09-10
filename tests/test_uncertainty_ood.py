"""
Tests for Epistemic Uncertainty & Out-of-Distribution (OOD) Routing.

Verifies:
- High confidence and low uncertainty for in-domain training manifold points
- Medium confidence and scaled uncertainty for boundary conditions
- Strict rejection (SURROGATE_OUT_OF_DOMAIN) for transonic/hypersonic or extreme AoA points
- Proper integration with ScientificResolutionEngine Level 4 fallback.
"""

import pytest
from backend.physics_ai.service import PhysicsAIService
from backend.physics_ai.schemas import DomainStatusEnum
from backend.science.engine import ScientificResolutionEngine


def test_in_domain_uncertainty_evaluation():
    service = PhysicsAIService.get_instance()
    # Clean in-domain subsonic point
    pred = service.predict("naca0012", mach=0.2, reynolds=2.0e6, aoa_deg=2.0)
    assert pred.domain_status == DomainStatusEnum.IN_DOMAIN
    assert pred.uncertainty.confidence_level == "HIGH"
    assert pred.uncertainty.confidence_score >= 0.70
    assert pred.uncertainty.ood_score < 2.0


def test_near_boundary_uncertainty_evaluation():
    service = PhysicsAIService.get_instance()
    # Near boundary: AoA = 13 deg or Mach = 0.38
    pred = service.predict("naca0012", mach=0.38, reynolds=2.0e6, aoa_deg=13.0)
    assert pred.domain_status in [DomainStatusEnum.EXTRAPOLATION_NEAR_BOUNDARY, DomainStatusEnum.SURROGATE_OUT_OF_DOMAIN]
    assert pred.uncertainty.cl_uncertainty > 0.015


def test_out_of_domain_rejection():
    service = PhysicsAIService.get_instance()
    # Out of domain: Mach 0.85
    pred = service.predict("naca0012", mach=0.85, reynolds=2.0e6, aoa_deg=4.0)
    assert pred.domain_status == DomainStatusEnum.SURROGATE_OUT_OF_DOMAIN
    assert pred.uncertainty.confidence_level == "OOD"


def test_scientific_engine_ood_escalation():
    engine = ScientificResolutionEngine()
    # Query outside valid envelope should not give a fake surrogate prediction
    res = engine.resolve("What is the drag coefficient of a NACA 0012 airfoil at Mach 0.85, Re 2.0e6, AoA 4 deg?")
    # Escalates past Level 4
    assert res["resolution_level"] != "LEVEL 4 - VALIDATED SURROGATE MODEL"
    assert res["epistemic_status"] == "NO_RESULT"
