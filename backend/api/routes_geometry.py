"""
AASI Geometry API Router: Custom Airfoil & CAD File Upload and Normalization.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from backend.physics.airfoil_parser import AirfoilCoordinateParser, AirfoilParseError

router = APIRouter(prefix="/geometry", tags=["Geometry & Airfoil Ingestion"])


class GeometryUploadResponse(BaseModel):
    name: str
    format_detected: str
    max_thickness: float
    thickness_x_location: float
    max_camber: float
    camber_x_location: float
    leading_edge_radius: float
    trailing_edge_gap: float
    point_count: int
    coordinates: List[List[float]]
    svg_preview: str


class DirectCoordinatePayload(BaseModel):
    name: Optional[str] = "Custom_Airfoil"
    content: str


def generate_svg_preview(coords: List[List[float]], width: int = 500, height: int = 150) -> str:
    """Generates a clean, modern SVG path representation of the airfoil."""
    if not coords:
        return ""

    pad_x = 30
    pad_y = 25
    w_draw = width - 2 * pad_x
    h_draw = height - 2 * pad_y
    y_center = height / 2.0

    # Scale x from [0, 1] to [pad_x, pad_x + w_draw]
    # Invert and scale y
    path_cmds = []
    for i, pt in enumerate(coords):
        px = pad_x + pt[0] * w_draw
        py = y_center - pt[1] * w_draw * 1.5  # preserve 1:1 aspect ratio with slight vertical zoom
        cmd = "M" if i == 0 else "L"
        path_cmds.append(f"{cmd} {px:.2f} {py:.2f}")

    path_d = " ".join(path_cmds) + " Z"

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: auto; display: block;">
  <defs>
    <linearGradient id="foilGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0077ed" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#00c7be" stop-opacity="0.15"/>
    </linearGradient>
  </defs>
  <!-- Chord reference line -->
  <line x1="{pad_x}" y1="{y_center}" x2="{pad_x + w_draw}" y2="{y_center}" stroke="rgba(255,255,255,0.15)" stroke-dasharray="4 4" stroke-width="1"/>
  <!-- Quarter-chord marker -->
  <circle cx="{pad_x + 0.25 * w_draw}" cy="{y_center}" r="3" fill="#ff9f0a"/>
  <!-- Airfoil surface -->
  <path d="{path_d}" fill="url(#foilGrad)" stroke="#64d2ff" stroke-width="1.8" stroke-linejoin="round"/>
</svg>"""
    return svg


@router.post("/upload", response_model=GeometryUploadResponse, summary="Upload proprietary .dat, .csv, or .txt airfoil file")
async def upload_airfoil_file(file: UploadFile = File(...)):
    """
    Ingests and normalizes proprietary Selig, Lednicer, or CSV airfoil coordinate files.
    """
    filename = file.filename or "Custom_Airfoil.dat"
    try:
        content_bytes = await file.read()
        text = content_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(exc)}"
        )

    clean_name = filename.rsplit(".", 1)[0]
    try:
        geom = AirfoilCoordinateParser.parse_text(text, default_name=clean_name)
    except AirfoilParseError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Airfoil parsing error: {str(err)}"
        )

    coords_list = geom.coordinates.tolist()
    svg = generate_svg_preview(coords_list)

    return GeometryUploadResponse(
        name=geom.name,
        format_detected=geom.format_detected,
        max_thickness=round(geom.max_thickness, 4),
        thickness_x_location=round(geom.thickness_x_location, 4),
        max_camber=round(geom.max_camber, 4),
        camber_x_location=round(geom.camber_x_location, 4),
        leading_edge_radius=round(geom.leading_edge_radius, 5),
        trailing_edge_gap=round(geom.trailing_edge_gap, 5),
        point_count=len(geom.coordinates),
        coordinates=coords_list,
        svg_preview=svg,
    )


@router.post("/direct", response_model=GeometryUploadResponse, summary="Direct text coordinate string ingestion")
async def ingest_direct_text(payload: DirectCoordinatePayload):
    try:
        geom = AirfoilCoordinateParser.parse_text(payload.content, default_name=payload.name or "Custom_Airfoil")
    except AirfoilParseError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Airfoil parsing error: {str(err)}"
        )

    coords_list = geom.coordinates.tolist()
    svg = generate_svg_preview(coords_list)

    return GeometryUploadResponse(
        name=geom.name,
        format_detected=geom.format_detected,
        max_thickness=round(geom.max_thickness, 4),
        thickness_x_location=round(geom.thickness_x_location, 4),
        max_camber=round(geom.max_camber, 4),
        camber_x_location=round(geom.camber_x_location, 4),
        leading_edge_radius=round(geom.leading_edge_radius, 5),
        trailing_edge_gap=round(geom.trailing_edge_gap, 5),
        point_count=len(geom.coordinates),
        coordinates=coords_list,
        svg_preview=svg,
    )
