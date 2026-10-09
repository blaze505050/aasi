"""
AASI Cognitive Engine: Autonomous Aerospace Scientific Reasoning & Discovery System.
Governing Doctrine: Absolute Anti-Fabrication Rule & Epistemic Verification Hierarchy.
"""

from .states import CognitiveState, CognitiveTransitionRecord
from .world_model import AerospaceWorldModel, WorldModelAssertion

__all__ = [
    "CognitiveState",
    "CognitiveTransitionRecord",
    "AerospaceWorldModel",
    "WorldModelAssertion",
]
