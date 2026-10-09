"""
AASI Phase 1: Aerospace Mission Language (AML) & Tool Bus API Router.
Exposes endpoints for parsing, validating, serializing AML programs,
introspecting tool contracts, and executing tools with cryptographic provenance.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.scientific_language import (
    parse_aml,
    validate_aml,
    serialize_aml,
    AMLParseError,
    AMLLexerError,
    AMLProgram,
)
from backend.tools.registry import tool_registry
from backend.agent.investigation_lifecycle import AutonomyLevel, AutonomyEnvelope

router = APIRouter(prefix="/aml", tags=["Aerospace Mission Language"])


class AMLParseRequest(BaseModel):
    source: str = Field(..., description="AML source code string")


class AMLParseResponse(BaseModel):
    success: bool
    ast: Optional[Dict[str, Any]] = None
    statement_count: int = 0
    error: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


class AMLValidateRequest(BaseModel):
    source: str = Field(..., description="AML source code string")


class AMLValidateResponse(BaseModel):
    is_valid: bool
    error_count: int
    warning_count: int
    diagnostics: List[Dict[str, Any]] = Field(default_factory=list)


class ToolContractExecuteRequest(BaseModel):
    tool_id: str
    operation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


@router.post("/parse", response_model=AMLParseResponse)
def parse_aml_endpoint(req: AMLParseRequest):
    """
    Parses an AML code script into a strongly typed AST.
    """
    try:
        prog = parse_aml(req.source)
        return AMLParseResponse(
            success=True,
            ast=prog.model_dump(),
            statement_count=len(prog.statements),
        )
    except (AMLLexerError, AMLParseError) as e:
        return AMLParseResponse(
            success=False,
            error=str(e),
            line=getattr(e, "line", None),
            column=getattr(e, "column", None),
        )
    except Exception as e:
        return AMLParseResponse(
            success=False,
            error=f"Unexpected error: {str(e)}",
        )


@router.post("/validate", response_model=AMLValidateResponse)
def validate_aml_endpoint(req: AMLValidateRequest):
    """
    Performs full lexical, grammatical, and semantic physical validation on AML code.
    """
    try:
        prog = parse_aml(req.source)
        val = validate_aml(prog)
        return AMLValidateResponse(
            is_valid=val.is_valid,
            error_count=len(val.errors),
            warning_count=len(val.warnings),
            diagnostics=[d.model_dump() for d in val.diagnostics],
        )
    except (AMLLexerError, AMLParseError) as e:
        return AMLValidateResponse(
            is_valid=False,
            error_count=1,
            warning_count=0,
            diagnostics=[{
                "severity": "ERROR",
                "message": str(e),
                "line": getattr(e, "line", None),
                "column": getattr(e, "column", None),
            }],
        )


@router.get("/contracts")
def list_tool_contracts_endpoint():
    """
    Returns the catalog of formal Tool Bus contracts with uncertainty and cost models.
    """
    return {
        "count": len(tool_registry.list_contracts()),
        "contracts": tool_registry.list_contracts(),
    }


@router.post("/contracts/execute")
def execute_tool_contract_endpoint(req: ToolContractExecuteRequest):
    """
    Executes a registered tool through its formal contract and attaches cryptographic provenance.
    """
    try:
        res = tool_registry.execute_contract(req.tool_id, req.operation, **req.parameters)
        return res.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/autonomy-levels")
def get_autonomy_levels_endpoint():
    """
    Returns definitions of standard aerospace autonomy tiers (L0-L5) and default governance envelopes.
    """
    return {
        "levels": [
            {
                "level": level.value,
                "name": level.name,
                "description": level.__doc__.strip() if level.__doc__ else "",
            }
            for level in AutonomyLevel
        ],
        "default_envelope": AutonomyEnvelope().model_dump(),
    }
