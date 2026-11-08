"""
API Routes for Stage 20: The Autonomous Discovery Machine & Landmark Publication Synthesizer.
=============================================================================================
Provides endpoints for generating camera-ready academic manuscripts for Nature, Science,
JFM, and AIAA Journal, complete with ASME V&V 20 multi-fidelity verification evidence,
vector data figures, BibTeX bibliography, and zero-drift Docker reproducibility containers.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/publication", tags=["Stage 20: Landmark Academic Publication Synthesizer"])


class PublicationSynthesisRequest(BaseModel):
    preset_key: str = Field("NATURE_AEROSPACE_LANDMARK", description="Target academic publication preset")
    target_journal: Optional[str] = Field(None, description="Optional journal target override")
    target_mach: Optional[float] = Field(None, description="Target cruise Mach number")


@router.post("/synthesize")
def synthesize_publication(request: PublicationSynthesisRequest) -> Dict[str, Any]:
    """
    Synthesizes a complete camera-ready academic manuscript, vector figures, and Docker bundle.
    """
    try:
        return NeuralOperatorAdapter.synthesize_landmark_publication(
            preset_key=request.preset_key,
            target_journal=request.target_journal,
            target_mach=request.target_mach,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publication synthesis failed: {str(e)}")


@router.get("/presets")
def get_publication_presets() -> Dict[str, Any]:
    """Returns available publication presets and target journals."""
    try:
        return NeuralOperatorAdapter.get_publication_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch publication presets: {str(e)}")
