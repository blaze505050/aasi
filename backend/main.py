"""
FastAPI application for AASI — Autonomous Aerospace Scientific Intelligence.
"""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import settings
from backend.agent import AASIAgent, OllamaUnavailableError, OllamaRuntimeError, default_agent

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aasi.backend")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for AASI: Experimental AI Research Assistant for Aerospace Engineering & Space Science.",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Schemas ---

class HealthResponse(BaseModel):
    """Schema for GET /api/health."""
    status: str = Field(..., description="Backend operational status (e.g. 'ok')")
    version: str = Field(..., description="Application version")
    ollama_connected: bool = Field(..., description="Whether Ollama runtime is reachable")
    configured_model: str = Field(..., description="Configured open-weight LLM")
    error: Optional[str] = Field(None, description="Diagnostic error if Ollama is unreachable")


class ChatRequest(BaseModel):
    """Schema for POST /api/chat request body."""
    message: str = Field(..., min_length=1, max_length=16384, description="User query or technical prompt")


class ChatResponse(BaseModel):
    """Schema for POST /api/chat response."""
    response: str = Field(..., description="AASI AI response")
    model: str = Field(..., description="Model identifier that produced the response")
    status: str = Field(default="success", description="Status of the generation")


# --- API Routes ---

@app.get("/api/health", response_model=HealthResponse, summary="System Health Check")
async def get_health():
    """
    Returns backend health, application version, Ollama runtime connectivity,
    and configured model without exposing secrets.
    """
    is_healthy, error_msg = await default_agent.check_health()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        ollama_connected=is_healthy,
        configured_model=settings.ollama_model,
        error=error_msg,
    )


@app.post("/api/chat", response_model=ChatResponse, summary="AASI Chat Completion")
async def chat_completion(request: ChatRequest):
    """
    Receives user query, orchestrates AASI agent prompt and context,
    invokes configured Ollama model, and returns structured response.
    """
    logger.info("Received chat query: '%s...'", request.message[:80])

    try:
        result = await default_agent.generate_response(request.message)
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            status="success",
        )
    except OllamaUnavailableError as exc:
        logger.error("Ollama unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except OllamaRuntimeError as exc:
        logger.error("Ollama runtime error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except ValueError as exc:
        logger.warning("Invalid request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected internal error during chat processing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the request.",
        )


@app.get("/", summary="Root index")
async def root():
    """Root endpoint providing service metadata."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
