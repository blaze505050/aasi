"""Tests for ScientificResolutionEngine orchestrating the 8-level scientific resolution hierarchy."""

import pytest
from backend.science.engine import ScientificResolutionEngine
from backend.science.models import EpistemicStatus
from backend.science.service import get_science_service


class TestScientificResolutionEngine:
    """Test the deterministic 8-level resolution hierarchy."""

    @pytest.fixture
    def engine(self):
        return get_science_service().engine

    def test_level_2_official_experimental_match(self, engine):
        # Query known NASA TN-D-628 point: NACA 0012, M=0.3, Re=500k, AoA=8 deg
        query = "What is the drag coefficient of NACA 0012 at Mach 0.3, Re 500k and AoA 8 deg?"
        res = engine.resolve(query)

        assert res["status"] == "SUCCESS"
        assert "LEVEL 2" in res["resolution_level"]
        assert res["epistemic_status"] == EpistemicStatus.OFFICIAL_EXPERIMENT.value

        primary = res["primary_result"]
        assert primary["value"] == pytest.approx(0.0142, abs=1e-4)
        assert primary["quantity"] == "CD"
        assert "NASA" in primary["source"]
        assert "TN-D-628" in str(primary["provenance"])

    def test_level_3_cfd_match_fallback(self, engine):
        # Query condition where only CFD benchmark exists (or CFD dataset query)
        cfd_rec = get_science_service().cfd_db.get("AASI-CFD-RANS-NACA0012-M03-RE5E5-AOA8")
        assert cfd_rec is not None
        assert cfd_rec.cd == 0.0145
        assert cfd_rec.cl == 0.815

    def test_level_4_surrogate_envelope_check(self, engine):
        # Surrogate inside domain: M=0.4, Re=1e6, AoA=4 deg
        surr_reg = get_science_service().surrogate_registry
        is_valid, surr, reason = surr_reg.check_validity_envelope(
            engine.normalizer.normalize("NACA 0012 at Mach 0.4, Re 1000000, AoA 4 deg")
        )
        assert is_valid is True
        assert surr.model_id in ["aerographnet-airfoil-subsonic-v1", "MODEL-AERO-SURROGATE-V1"]

        # Surrogate out of domain: Mach 1.5 supersonic

        is_valid_out, surr_out, reason_out = surr_reg.check_validity_envelope(
            engine.normalizer.normalize("NACA 0012 at Mach 1.5, Re 1000000, AoA 4 deg")
        )
        assert is_valid_out is False
        assert "SURROGATE_OUT_OF_DOMAIN" in reason_out

    def test_level_5_analytical_orbital_solver(self, engine):
        # Query orbital mechanics problem -> Level 5 Analytical Solver
        query = "Calculate circular orbital velocity at altitude 500 km around Earth"
        res = engine.resolve(query)

        assert res["status"] == "SUCCESS"
        assert "LEVEL 5" in res["resolution_level"]
        assert res["epistemic_status"] == EpistemicStatus.ANALYTICAL_RESULT.value
        assert res["primary_result"]["value"] == pytest.approx(7.6126, rel=1e-3)
        assert res["primary_result"]["units"] == "km/s"

    def test_level_7_parameter_clarification(self, engine):
        # Query without conditions -> Level 7 Clarification
        query = "What is the drag coefficient of NACA 0012?"
        res = engine.resolve(query)

        assert res["status"] == "CLARIFICATION_NEEDED"
        assert "LEVEL 7" in res["resolution_level"]
        assert len(res["missing_conditions"]) >= 3
        assert "Parameter Clarification Needed" in res["message"]

    def test_level_7_no_validated_result(self, engine):
        # Query exotic out-of-domain condition where no data exists
        query = "Drag coefficient of NACA 0012 at Mach 0.95, Re 80000000 and AoA 45 deg"
        res = engine.resolve(query)

        assert res["status"] == "NO_VALIDATED_RESULT"
        assert "LEVEL 7" in res["resolution_level"]
        assert "No verified experimental polar or benchmark CFD" in res["message"]

    def test_conflict_resolution_multi_source_comparison(self, engine):
        # When both experiment (Cd=0.0142) and CFD (Cd=0.0145) match
        query = "What is the drag coefficient of NACA 0012 at Mach 0.3, Re 500k and AoA 8 deg?"
        res = engine.resolve(query)

        assert len(res["all_results"]) >= 2
        discrepancy = res.get("discrepancy")
        assert discrepancy is not None
        assert discrepancy["max_relative_difference"] > 0.0
        assert len(discrepancy["physical_reasons"]) >= 2
        assert any("Boundary Layer Transition" in r for r in discrepancy["physical_reasons"])
