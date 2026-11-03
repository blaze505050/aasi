"""
Clean-Room AI & Physical Model Synthesis for AASI-Craft.
Synthesizes neural surrogate operators, 6-DOF orbital dynamics, and control laws
using only verified evidence from the Evidence Dossier.
"""

from .clean_room_synthesizer import CleanRoomSynthesizer, SynthesizedArtifact

__all__ = ["CleanRoomSynthesizer", "SynthesizedArtifact"]

