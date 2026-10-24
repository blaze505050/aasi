"""
AASI 30-Problem Aerospace Platform: Plug-in Module Contract & Fidelity Ladder.

Every problem module in AASI implements this standardized interface:
1. solve(inputs, fidelity) -> ModuleResult
2. uncertainty(inputs, results) -> Dict[str, Any]
3. benchmarks() -> List[BenchmarkCase]
4. evidence(results) -> EvidenceRecord

Fidelity Ladder:
- L0: Analytic or empirical closed-form (milliseconds)
- L1: Reduced-order or panel/vortex-lattice method (seconds)
- L2: High-fidelity CFD/FEA with mesh generation (minutes to hours)
"""

from __future__ import annotations

import abc
import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FidelityLevel(str, Enum):
    L0_ANALYTIC = "L0_ANALYTIC"
    L1_REDUCED_ORDER = "L1_REDUCED_ORDER"
    L2_HIGH_FIDELITY = "L2_HIGH_FIDELITY"


class EpistemicClassification(str, Enum):
    CALCULATED = "CALCULATED"
    PREDICTED = "PREDICTED"
    ESTIMATED = "ESTIMATED"
    ASSUMED = "ASSUMED"
    UNVERIFIED = "UNVERIFIED"


class BenchmarkCase(BaseModel):
    case_id: str
    name: str
    reference_source: str
    citation: str
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, float]
    tolerances: Dict[str, float]  # relative tolerance (0.10 = 10%) or absolute if specified in notes
    regime_description: str
    notes: Optional[str] = None


class BenchmarkEvaluation(BaseModel):
    case_id: str
    case_name: str
    passed: bool
    metrics: Dict[str, Dict[str, float]]  # metric_name -> {actual, expected, relative_error, tolerance, passed}
    summary: str


class EvidenceRecord(BaseModel):
    evidence_id: str
    module_id: str
    problem_id: int
    fidelity_level: FidelityLevel
    solver_name: str
    code_version: str = "AASI-v1.1.0"
    timestamp_utc: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    uncertainty_intervals: Dict[str, Any]
    epistemic_classification: EpistemicClassification
    inputs_hash: str
    provenance_hash: str


class ModuleResult(BaseModel):
    module_id: str
    problem_id: int
    fidelity_level: FidelityLevel
    solver_name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    uncertainty: Dict[str, Any]
    epistemic_classification: EpistemicClassification
    evidence: EvidenceRecord
    metadata: Dict[str, Any] = Field(default_factory=dict)


def compute_sha256_provenance(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash for arbitrary dictionary."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ProblemModule(abc.ABC):
    """
    Abstract Base Class for all AASI 30 Aerospace Problem Modules.
    Enforces the four-part module contract: solve, uncertainty, benchmarks, evidence.
    """

    @property
    @abc.abstractmethod
    def problem_id(self) -> int:
        """Problem index (1 to 30) from the AASI technical roadmap."""
        pass

    @property
    @abc.abstractmethod
    def module_id(self) -> str:
        """Unique slug identifier for the module (e.g. 'aero_3d_vlm')."""
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable module name."""
        pass

    @property
    @abc.abstractmethod
    def tier(self) -> int:
        """Tier: 1 (Aerodynamics Core), 2 (Vehicle Systems & Propulsion), 3 (Space & Operations)."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Summary of physics capabilities, assumptions, and validation regime."""
        pass

    @property
    def supported_fidelities(self) -> List[FidelityLevel]:
        """Available fidelity levels in this module."""
        return [FidelityLevel.L0_ANALYTIC, FidelityLevel.L1_REDUCED_ORDER]

    @abc.abstractmethod
    def solve(
        self,
        inputs: Dict[str, Any],
        fidelity: FidelityLevel = FidelityLevel.L1_REDUCED_ORDER,
    ) -> ModuleResult:
        """
        Solves the forward physical problem at the requested fidelity level.
        Returns deterministic outputs wrapped in a ModuleResult.
        """
        pass

    @abc.abstractmethod
    def uncertainty(
        self,
        inputs: Dict[str, Any],
        results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Computes formal uncertainty intervals (input, numerical, model, combined U95).
        """
        pass

    @abc.abstractmethod
    def benchmarks(self) -> List[BenchmarkCase]:
        """
        Returns list of published reference benchmark cases for automated CI verification.
        """
        pass

    def evidence(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        fidelity: FidelityLevel,
        solver_name: str,
        uncertainty_intervals: Dict[str, Any],
        epistemic_classification: EpistemicClassification = EpistemicClassification.CALCULATED,
    ) -> EvidenceRecord:
        """
        Generates cryptographic evidence record with SHA-256 provenance hash.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        evidence_id = f"EV-{uuid.uuid4().hex[:12].upper()}"

        inputs_hash = compute_sha256_provenance(inputs)
        provenance_payload = {
            "evidence_id": evidence_id,
            "module_id": self.module_id,
            "problem_id": self.problem_id,
            "fidelity_level": fidelity.value,
            "solver_name": solver_name,
            "inputs_hash": inputs_hash,
            "outputs": outputs,
            "uncertainty": uncertainty_intervals,
            "timestamp_utc": now_utc,
        }
        prov_hash = compute_sha256_provenance(provenance_payload)

        return EvidenceRecord(
            evidence_id=evidence_id,
            module_id=self.module_id,
            problem_id=self.problem_id,
            fidelity_level=fidelity,
            solver_name=solver_name,
            code_version="AASI-v1.1.0",
            timestamp_utc=now_utc,
            inputs=inputs,
            outputs=outputs,
            uncertainty_intervals=uncertainty_intervals,
            epistemic_classification=epistemic_classification,
            inputs_hash=inputs_hash,
            provenance_hash=prov_hash,
        )

    def verify_benchmarks(self) -> List[BenchmarkEvaluation]:
        """
        Runs all registered benchmark cases for this module and checks outputs against tolerances.
        """
        cases = self.benchmarks()
        evaluations: List[BenchmarkEvaluation] = []

        for case in cases:
            # Execute solver at appropriate fidelity (default L1)
            result = self.solve(case.inputs, fidelity=FidelityLevel.L1_REDUCED_ORDER)
            metrics: Dict[str, Dict[str, float]] = {}
            case_passed = True

            for metric_key, expected_val in case.expected_outputs.items():
                actual_val = float(result.outputs.get(metric_key, 0.0))
                tol = float(case.tolerances.get(metric_key, 0.15))

                # Relative error if expected != 0, else absolute
                if abs(expected_val) > 1e-6:
                    rel_err = abs(actual_val - expected_val) / abs(expected_val)
                    passed = rel_err <= tol
                else:
                    abs_err = abs(actual_val - expected_val)
                    rel_err = abs_err
                    passed = abs_err <= tol

                if not passed:
                    case_passed = False

                metrics[metric_key] = {
                    "actual": round(actual_val, 5),
                    "expected": round(expected_val, 5),
                    "relative_error": round(rel_err, 4),
                    "tolerance": round(tol, 4),
                    "passed": passed,
                }

            evaluations.append(
                BenchmarkEvaluation(
                    case_id=case.case_id,
                    case_name=case.name,
                    passed=case_passed,
                    metrics=metrics,
                    summary="PASSED" if case_passed else "FAILED_TOLERANCE",
                )
            )

        return evaluations
