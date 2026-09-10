"""
AASI Multi-Fidelity Service Layer.

Provides high-level singleton access for multi-fidelity resolution, discrepancy
estimation, uncertainty calibration, and cross-tier analysis.
"""

from typing import Dict, Any, List, Optional, Tuple
from backend.multifidelity.models import (
    MultiFidelityResult,
    FidelityLevel,
    DiscrepancyResult,
    UncertaintyCalibrationMetrics,
    FlowConditions,
)
from backend.multifidelity.registry import MultiFidelityRegistry
from backend.multifidelity.resolver import MultiFidelityResolver
from backend.multifidelity.discrepancy import MultiFidelityDiscrepancyEngine
from backend.multifidelity.calibration import UncertaintyCalibrationEngine
from backend.multifidelity.consistency import CrossFidelityConsistencyValidator
from backend.multifidelity.fusion import MultiFidelityFusionEngine


class MultiFidelityService:
    """Singleton service manager for Multi-Fidelity Physics."""

    _instance: Optional["MultiFidelityService"] = None

    def __init__(self):
        self.registry = MultiFidelityRegistry()
        self.resolver = MultiFidelityResolver()

    @classmethod
    def get_instance(cls) -> "MultiFidelityService":
        if cls._instance is None:
            cls._instance = MultiFidelityService()
        return cls._instance

    def resolve(
        self,
        geometry: str,
        mach: float,
        reynolds: float,
        aoa_deg: float,
        quantity: str = "CL"
    ) -> Dict[str, Any]:
        """Resolves the best available fidelity result for the given conditions."""
        # Query registered experiments and validated CFD
        exps = self.registry.query_results(geometry=geometry, fidelity=FidelityLevel.EXPERIMENT, quantity=quantity)
        cfds = self.registry.query_results(geometry=geometry, fidelity=FidelityLevel.HIGH_FIDELITY_CFD, quantity=quantity)

        return self.resolver.resolve_best_source(
            geometry=geometry,
            mach=mach,
            reynolds=reynolds,
            aoa_deg=aoa_deg,
            quantity=quantity,
            available_experiments=exps,
            available_cfd=cfds,
        )

    def compute_discrepancy(
        self,
        high_result: MultiFidelityResult,
        low_result: MultiFidelityResult
    ) -> DiscrepancyResult:
        """Computes discrepancy between two results."""
        return MultiFidelityDiscrepancyEngine.calculate_discrepancy(high_result, low_result)

    def evaluate_surrogate_calibration(
        self,
        model_id: str = "AERO_SURROGATE_V1",
        quantity: str = "CL"
    ) -> UncertaintyCalibrationMetrics:
        """Evaluates uncertainty calibration of AeroSurrogateV1 against authentic test airfoils."""
        test_samples = self.registry.query_results(geometry="NACA 0012", fidelity=FidelityLevel.EXPERIMENT, quantity=quantity)
        
        preds = []
        trues = []
        uncs = []

        for s in test_samples[:60]:  # Evaluate on authentic samples
            try:
                p = self.resolver.surrogate_service.predict(
                    geometry=s.geometry,
                    mach=s.conditions.mach,
                    reynolds=s.conditions.reynolds,
                    aoa_deg=s.conditions.aoa_deg
                )
                val = getattr(p, quantity.lower(), None)
                if val is not None and p.uncertainty:
                    preds.append(val)
                    trues.append(s.value)
                    u = getattr(p.uncertainty, f"{quantity.lower()}_uncertainty", 0.03)
                    uncs.append(max(u, 0.005))
            except Exception:
                continue

        return UncertaintyCalibrationEngine.evaluate_calibration(
            predicted_values=preds,
            true_values=trues,
            predicted_uncertainties=uncs,
            model_id=model_id
        )

    def query(
        self,
        geometry: Optional[str] = None,
        fidelity: Optional[FidelityLevel] = None,
        quantity: Optional[str] = None,
        mach_range: Optional[tuple] = None,
        aoa_range: Optional[tuple] = None
    ) -> List[MultiFidelityResult]:
        """Queries stored multi-fidelity results with optional filters."""
        return self.registry.query_results(
            geometry=geometry,
            fidelity=fidelity,
            quantity=quantity,
            mach_range=mach_range,
            aoa_range=aoa_range
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Returns statistics of multi-fidelity registry."""
        return {
            "total_records": self.registry.count(),
            "by_fidelity": self.registry.count_by_fidelity(),
        }



multi_fidelity_service = MultiFidelityService.get_instance()

