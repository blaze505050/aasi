"""Tests for EngineeringQueryNormalizer covering real-world aerospace syntax variations."""

import pytest
from backend.science.normalizer import EngineeringQueryNormalizer
from backend.science.models import FlowRegime


class TestEngineeringQueryNormalizer:
    """Test comprehensive parameter normalization from natural language."""

    @pytest.fixture
    def normalizer(self):
        return EngineeringQueryNormalizer()

    def test_mach_variations(self, normalizer):
        queries = [
            ("What is the drag at Mach 0.3?", 0.3),
            ("NACA 0012 with M = 0.3", 0.3),
            ("Flow at M0.3 and 8 deg", 0.3),
            ("Mach=0.85 transonic flow", 0.85),
            ("M 2.5 supersonic cone", 2.5),
        ]
        for q, expected in queries:
            cond = normalizer.normalize(q)
            assert cond.mach == pytest.approx(expected, rel=1e-3), f"Failed on query: {q}"

    def test_reynolds_variations(self, normalizer):
        queries = [
            ("NACA 0012 at Re = 500k", 500000.0),
            ("Reynolds number 5e5 on airfoil", 500000.0),
            ("At 500,000 Reynolds", 500000.0),
            ("Re=6000000 boundary layer", 6000000.0),
            ("Reynolds 3.0e6 laminar flow", 3000000.0),
        ]
        for q, expected in queries:
            cond = normalizer.normalize(q)
            assert cond.reynolds == pytest.approx(expected, rel=1e-3), f"Failed on query: {q}"

    def test_aoa_variations(self, normalizer):
        queries = [
            ("Airfoil at 8 degrees", 8.0),
            ("At 8 deg angle of attack", 8.0),
            ("alpha = 8° flow", 8.0),
            ("AoA 8 degrees", 8.0),
            ("Negative angle at -4 deg", -4.0),
            ("alpha=-4.5° polar point", -4.5),
        ]
        for q, expected in queries:
            cond = normalizer.normalize(q)
            assert cond.aoa_deg == pytest.approx(expected, rel=1e-3), f"Failed on query: {q}"

    def test_geometry_variations(self, normalizer):
        queries = [
            ("NACA 0012 drag", "NACA 0012"),
            ("NACA0012 lift curve", "NACA 0012"),
            ("NACA-0012 polar", "NACA 0012"),
            ("NACA 4412 cambered airfoil", "NACA 4412"),
            ("RAE 2822 transonic shock", "RAE 2822"),
            ("ONERA M6 swept wing", "ONERA M6"),
            ("Clark-Y flat bottom", "Clark-Y"),
        ]
        for q, expected in queries:
            cond = normalizer.normalize(q)
            assert cond.geometry == expected, f"Failed on query: {q}"

    def test_flow_regime_classification(self, normalizer):
        assert normalizer.normalize("Flow at Mach 0.1").flow_regime == FlowRegime.INCOMPRESSIBLE
        assert normalizer.normalize("Flow at Mach 0.5").flow_regime == FlowRegime.SUBSONIC
        assert normalizer.normalize("Flow at Mach 0.95").flow_regime == FlowRegime.TRANSONIC
        assert normalizer.normalize("Flow at Mach 2.2").flow_regime == FlowRegime.SUPERSONIC
        assert normalizer.normalize("Flow at Mach 6.0").flow_regime == FlowRegime.HYPERSONIC

    def test_missing_conditions_audit(self, normalizer):
        # Querying Cd without conditions must detect missing Mach, Re, AoA
        cond = normalizer.normalize("What is the Cd of NACA 0012?")
        assert cond.geometry == "NACA 0012"
        assert len(cond.missing_critical_conditions) >= 3
        assert any("Mach" in m for m in cond.missing_critical_conditions)
        assert any("Reynolds" in m for m in cond.missing_critical_conditions)
        assert any("Angle of attack" in m for m in cond.missing_critical_conditions)

    def test_complete_query_has_no_missing_conditions(self, normalizer):
        cond = normalizer.normalize("Drag coefficient of NACA 0012 at Mach 0.3, Re 500k and AoA 8 deg")
        assert cond.geometry == "NACA 0012"
        assert cond.mach == 0.3
        assert cond.reynolds == 500000.0
        assert cond.aoa_deg == 8.0
        assert len(cond.missing_critical_conditions) == 0
