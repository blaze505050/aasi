"""
AASI Phase 21: Scientific Claim Discipline & Epistemic Support Engine.
Governing Rule: Absolute Anti-Fabrication Rule.
Enforces rigorous categorization of scientific assertions:
OBSERVATION -> CORRELATION -> MODEL_PREDICTION -> SUPPORTED_HYPOTHESIS -> CAUSAL_CLAIM.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceType(str, Enum):
    OBSERVATION = "OBSERVATION"              # Raw, authenticated experimental or numerical data
    CORRELATION = "CORRELATION"              # Empirical statistical association in data
    MODEL_PREDICTION = "MODEL_PREDICTION"    # Output of fitted surrogate function
    SUPPORTED_HYPOTHESIS = "SUPPORTED_HYPOTHESIS"# Hypothesis passing pre-registered falsification test
    CAUSAL_CLAIM = "CAUSAL_CLAIM"            # Physical cause-effect established via controlled interventional experiments


class SupportLevel(str, Enum):
    STRONG_EMPIRICAL = "STRONG_EMPIRICAL"    # Multiple independent authenticated datasets
    MODERATE_EMPIRICAL = "MODERATE_EMPIRICAL"# Single dataset or controlled split
    THEORETICAL_ONLY = "THEORETICAL_ONLY"    # Derived from first principles without validation
    PRELIMINARY = "PRELIMINARY"              # Small sample or exploratory observation
    UNSUPPORTED = "UNSUPPORTED"              # Claim lacks sufficient evidentiary backing


@dataclass
class ScientificClaim:
    claim_id: str
    claim_text: str
    evidence_type: EvidenceType
    support_level: SupportLevel
    datasets: List[str]
    experiments: List[str]
    limitations: List[str]
    falsification_criteria: str
    is_valid: bool = True
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "evidence_type": self.evidence_type.value,
            "support_level": self.support_level.value,
            "datasets": self.datasets,
            "experiments": self.experiments,
            "limitations": self.limitations,
            "falsification_criteria": self.falsification_criteria,
            "is_valid": self.is_valid,
            "rejection_reason": self.rejection_reason,
        }


class ScientificClaimValidator:
    """Validates epistemic discipline and prevents overclaiming."""

    @classmethod
    def validate_claim(cls, claim: ScientificClaim) -> ScientificClaim:
        """
        Audit claim against evidentiary rules:
        1. CAUSAL_CLAIM requires at least 2 distinct interventional experiments or physical ablation tests.
        2. SUPPORTED_HYPOTHESIS requires specified falsification criteria and at least 1 experiment.
        3. Feature importance alone can never justify a CAUSAL_CLAIM.
        4. Claims with no datasets or experiments cannot have STRONG_EMPIRICAL support.
        """
        # Rule 1: Causal claim evidence requirements
        if claim.evidence_type == EvidenceType.CAUSAL_CLAIM:
            if len(claim.experiments) < 2:
                claim.is_valid = False
                claim.rejection_reason = (
                    "Causal claims require at least two independent interventional or ablation experiments."
                )
                claim.support_level = SupportLevel.UNSUPPORTED
                return claim

        # Rule 2: Datasets presence for empirical support
        if claim.support_level in [SupportLevel.STRONG_EMPIRICAL, SupportLevel.MODERATE_EMPIRICAL]:
            if not claim.datasets and not claim.experiments:
                claim.is_valid = False
                claim.rejection_reason = "Empirical support claimed without citing any dataset or experiment."
                claim.support_level = SupportLevel.UNSUPPORTED
                return claim

        # Rule 3: Falsification criteria
        if not claim.falsification_criteria.strip():
            claim.is_valid = False
            claim.rejection_reason = "Scientific claim must have explicit, falsifiable criteria."
            return claim

        claim.is_valid = True
        claim.rejection_reason = None
        return claim
