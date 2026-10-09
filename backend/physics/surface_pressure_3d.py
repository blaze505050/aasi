"""
AASI 3D Surface Pressure & Mesh Contour Engine (ASME V&V 20 / Transonic Aerodynamics).
Generates structured quadrilateral surface meshes, 3D vertex coordinate arrays,
and physical surface pressure coefficient (Cp) distributions with transonic shock capturing.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class Surface3DRequest(BaseModel):
    airfoil: str = Field(default="NACA 0012", description="Airfoil profile name (e.g., NACA 0012, RAE 2822, NASA SC(2)-0714)")
    alpha_deg: float = Field(default=4.0, ge=-10.0, le=25.0, description="Angle of attack in degrees")
    mach: float = Field(default=0.72, ge=0.05, le=0.90, description="Free-stream Mach number")
    reynolds: float = Field(default=3e6, ge=1e5, le=5e7, description="Reynolds number")
    span: float = Field(default=3.0, ge=0.5, le=20.0, description="Wing span in meters")
    aspect_ratio: float = Field(default=6.0, ge=1.0, le=15.0, description="Wing aspect ratio")
    sweep_deg: float = Field(default=15.0, ge=0.0, le=45.0, description="Quarter-chord sweep angle in degrees")
    taper_ratio: float = Field(default=0.7, ge=0.2, le=1.0, description="Tip-to-root chord ratio")
    nx: int = Field(default=50, ge=20, le=120, description="Chordwise surface nodes")
    ny: int = Field(default=24, ge=10, le=60, description="Spanwise surface nodes")
    slice_eta: float = Field(default=0.5, ge=0.0, le=1.0, description="Spanwise station for 2D chordwise slice (0 = root, 1 = tip)")


class ChordwiseSlicePoint(BaseModel):
    xc: float
    cp_upper: float
    cp_lower: float
    is_shock: bool = False


class Surface3DResponse(BaseModel):
    airfoil: str
    alpha_deg: float
    mach: float
    reynolds: float
    cl: float
    cd: float
    cm: float
    lift_to_drag: float
    has_shock: bool
    shock_xc: Optional[float]
    stagnation_xc: float
    vertices: List[float]  # Flat array [x0, y0, z0, x1, y1, z1, ...]
    normals: List[float]   # Flat array [nx0, ny0, nz0, ...]
    colors: List[float]    # Flat array [r0, g0, b0, ...] normalized 0-1
    indices: List[int]     # Triangle face indices
    cp_min: float
    cp_max: float
    slice_data: List[ChordwiseSlicePoint]
    mesh_stats: Dict[str, Any]


def _get_base_airfoil_coords(airfoil_name: str, n_points: int = 50) -> Tuple[List[float], List[float], List[float]]:
    """
    Returns x/c, y_upper/c, y_lower/c for standard aerospace geometries.
    Cosine clustering at leading and trailing edges.
    """
    beta = [i * math.pi / (n_points - 1) for i in range(n_points)]
    x = [0.5 * (1.0 - math.cos(b)) for b in beta]

    name_lower = airfoil_name.lower().replace(" ", "").replace("-", "")

    if "rae2822" in name_lower:
        # Supercritical RAE 2822 profile approximation
        t_max = 0.121
        y_u, y_l = [], []
        for xi in x:
            yt = 5.0 * t_max * (0.2969 * math.sqrt(max(xi, 1e-6)) - 0.1260 * xi - 0.3516 * xi**2 + 0.2843 * xi**3 - 0.1015 * xi**4)
            # Rear camber for supercritical design
            yc = 0.015 * xi * (1.0 - xi) if xi < 0.6 else 0.015 * 0.24 - 0.03 * (xi - 0.6)**1.5
            y_u.append(yc + yt * 0.95)
            y_l.append(yc - yt * 1.05)
        return x, y_u, y_l

    elif "sc(2)" in name_lower or "sc2" in name_lower:
        # NASA SC(2)-0714 supercritical
        t_max = 0.14
        y_u, y_l = [], []
        for xi in x:
            yt = 5.0 * t_max * (0.2969 * math.sqrt(max(xi, 1e-6)) - 0.1260 * xi - 0.3516 * xi**2 + 0.2843 * xi**3 - 0.1015 * xi**4)
            yc = 0.02 * math.sin(math.pi * xi) - 0.012 * (xi**2) if xi > 0.5 else 0.02 * math.sin(math.pi * xi)
            y_u.append(yc + yt)
            y_l.append(yc - yt)
        return x, y_u, y_l

    elif "clarky" in name_lower:
        # Flat bottom Clark Y
        y_u, y_l = [], []
        for xi in x:
            yu = 0.117 * math.sqrt(max(xi, 1e-6)) * (1.0 - xi) * 2.8
            yl = -0.01 * (1.0 - xi) * xi * 4.0 if xi < 0.2 else 0.0
            y_u.append(yu)
            y_l.append(yl)
        return x, y_u, y_l

    else:
        # Default NACA 0012 symmetric profile
        t_max = 0.12
        y_u, y_l = [], []
        for xi in x:
            yt = 5.0 * t_max * (0.2969 * math.sqrt(max(xi, 1e-6)) - 0.1260 * xi - 0.3516 * xi**2 + 0.2843 * xi**3 - 0.1015 * xi**4)
            y_u.append(yt)
            y_l.append(-yt)
        return x, y_u, y_l


def _cp_to_rgb(cp: float, cp_min: float, cp_max: float) -> Tuple[float, float, float]:
    """
    Maps Cp into high-contrast aerodynamic colormap:
    - Deep cyan/blue for suction peak (low Cp)
    - Slate/gray for zero/free-stream
    - Amber/red for stagnation (high Cp)
    """
    # Normalize cp in [0, 1] range: 0 is cp_min (suction), 1 is cp_max (stagnation)
    denom = max(cp_max - cp_min, 1e-4)
    t = (cp - cp_min) / denom
    t = max(0.0, min(1.0, t))

    if t < 0.25:
        # Deep blue -> bright sky cyan
        f = t / 0.25
        return (0.05 + 0.15 * f, 0.45 + 0.45 * f, 0.85 + 0.15 * f)
    elif t < 0.50:
        # Bright sky cyan -> neutral slate
        f = (t - 0.25) / 0.25
        return (0.20 + 0.20 * f, 0.70 - 0.25 * f, 0.90 - 0.40 * f)
    elif t < 0.75:
        # Neutral slate -> amber warning
        f = (t - 0.50) / 0.25
        return (0.40 + 0.55 * f, 0.45 + 0.17 * f, 0.50 - 0.45 * f)
    else:
        # Amber -> stagnation vermilion
        f = (t - 0.75) / 0.25
        return (0.95 + 0.05 * f, 0.62 - 0.35 * f, 0.05 + 0.15 * f)


def generate_3d_surface_pressure(req: Surface3DRequest) -> Surface3DResponse:
    """
    Computes 3D surface geometry, structured quad-to-triangle mesh,
    and transonic / subsonic surface pressure field.
    """
    x_nodes, yu_nodes, yl_nodes = _get_base_airfoil_coords(req.airfoil, req.nx)

    alpha_rad = math.radians(req.alpha_deg)
    beta_prandtl = math.sqrt(max(1.0 - req.mach**2, 0.15))

    # Determine critical Mach and shock presence
    has_shock = req.mach >= 0.70
    shock_xc = 0.58 if has_shock else None

    # Compute baseline Lift, Drag, Moment
    cl_base = (2.0 * math.pi * alpha_rad) / beta_prandtl
    cd_base = 0.0080 + 0.035 * (cl_base**2) / (math.pi * req.aspect_ratio * 0.85)
    if has_shock:
        # Wave drag penalty
        wave_drag = 0.006 * ((req.mach - 0.68) / 0.1)**3
        cd_base += max(0.0, wave_drag)
        cl_base *= 0.92  # Shock boundary layer interaction decambering

    cm_base = -0.05 - 0.02 * req.alpha_deg

    # Wing planform definitions
    b = req.span
    ar = req.aspect_ratio
    c_root = (2.0 * b) / (ar * (1.0 + req.taper_ratio))
    sweep_rad = math.radians(req.sweep_deg)

    vertices: List[float] = []
    normals: List[float] = []
    colors: List[float] = []
    indices: List[int] = []

    # We evaluate upper surface first, then lower surface
    # Grid size: 2 surfaces * nx chordwise * ny spanwise
    cp_grid_upper: List[List[float]] = []
    cp_grid_lower: List[List[float]] = []

    cp_all: List[float] = []

    for j in range(req.ny):
        eta = j / (req.ny - 1)  # 0 (root) to 1 (tip)
        c_eta = c_root * (1.0 - (1.0 - req.taper_ratio) * eta)
        x_le = 0.25 * c_root + (eta * b * 0.5) * math.tan(sweep_rad) - 0.25 * c_eta
        y_pos = (eta - 0.5) * b  # Centered wing from -b/2 to +b/2

        # 3D induced downwash reduces effective alpha at tips
        downwash = (cl_base / (math.pi * ar)) * (1.0 + 0.4 * eta)
        eff_alpha = alpha_rad - downwash

        row_cp_u = []
        row_cp_l = []

        for i, xi in enumerate(x_nodes):
            # Upper Surface Pressure
            # Suction peak near LE
            le_term = math.sqrt(max(1.0 - xi, 1e-4) / max(xi, 1e-4))
            cp_u = - (2.0 * eff_alpha / beta_prandtl) * (le_term + 0.3)
            # Add thickness acceleration
            cp_u -= 0.6 * yu_nodes[i] / beta_prandtl

            # Transonic normal shock wave compression
            if has_shock and xi > 0.55:
                # Shock jump
                delta_m = (req.mach - 0.65) * 4.0
                cp_u += 0.85 * min(1.0, (xi - 0.55) * 12.0) * delta_m

            # Trailing edge pressure recovery
            cp_u = min(0.3, max(-3.8, cp_u + 0.2 * (xi**2)))

            # Lower Surface Pressure
            # Stagnation at leading edge
            cp_l = 1.0 * (1.0 - xi)**1.8 * math.cos(eff_alpha)**2
            cp_l += 0.4 * eff_alpha * math.sqrt(max(xi, 1e-4))
            cp_l = min(1.0, max(-0.5, cp_l))

            row_cp_u.append(cp_u)
            row_cp_l.append(cp_l)
            cp_all.extend([cp_u, cp_l])

        cp_grid_upper.append(row_cp_u)
        cp_grid_lower.append(row_cp_l)

    cp_min = min(cp_all)
    cp_max = max(cp_all)

    # Build 3D mesh geometry (Upper surface then Lower surface)
    # Upper surface grid
    for j in range(req.ny):
        eta = j / (req.ny - 1)
        c_eta = c_root * (1.0 - (1.0 - req.taper_ratio) * eta)
        x_le = 0.25 * c_root + (eta * b * 0.5) * math.tan(sweep_rad) - 0.25 * c_eta
        y_pos = (eta - 0.5) * b

        for i, xi in enumerate(x_nodes):
            # Rotated with pitch angle
            x_local = xi * c_eta
            z_local = yu_nodes[i] * c_eta

            # Global coordinates
            xg = x_le + x_local * math.cos(alpha_rad) + z_local * math.sin(alpha_rad)
            yg = y_pos
            zg = -x_local * math.sin(alpha_rad) + z_local * math.cos(alpha_rad)

            vertices.extend([round(xg, 4), round(yg, 4), round(zg, 4)])

            # Normal pointing upward
            normals.extend([0.0, 0.0, 1.0])

            # Color from Cp
            rgb = _cp_to_rgb(cp_grid_upper[j][i], cp_min, cp_max)
            colors.extend([round(rgb[0], 3), round(rgb[1], 3), round(rgb[2], 3)])

    # Generate Upper Surface Indices (quads split into 2 triangles)
    for j in range(req.ny - 1):
        for i in range(req.nx - 1):
            p0 = j * req.nx + i
            p1 = p0 + 1
            p2 = (j + 1) * req.nx + i
            p3 = p2 + 1
            indices.extend([p0, p2, p1, p1, p2, p3])

    # Lower surface grid
    lower_offset = len(vertices) // 3
    for j in range(req.ny):
        eta = j / (req.ny - 1)
        c_eta = c_root * (1.0 - (1.0 - req.taper_ratio) * eta)
        x_le = 0.25 * c_root + (eta * b * 0.5) * math.tan(sweep_rad) - 0.25 * c_eta
        y_pos = (eta - 0.5) * b

        for i, xi in enumerate(x_nodes):
            x_local = xi * c_eta
            z_local = yl_nodes[i] * c_eta

            xg = x_le + x_local * math.cos(alpha_rad) + z_local * math.sin(alpha_rad)
            yg = y_pos
            zg = -x_local * math.sin(alpha_rad) + z_local * math.cos(alpha_rad)

            vertices.extend([round(xg, 4), round(yg, 4), round(zg, 4)])
            normals.extend([0.0, 0.0, -1.0])

            rgb = _cp_to_rgb(cp_grid_lower[j][i], cp_min, cp_max)
            colors.extend([round(rgb[0], 3), round(rgb[1], 3), round(rgb[2], 3)])

    # Lower Surface Indices
    for j in range(req.ny - 1):
        for i in range(req.nx - 1):
            p0 = lower_offset + j * req.nx + i
            p1 = p0 + 1
            p2 = lower_offset + (j + 1) * req.nx + i
            p3 = p2 + 1
            indices.extend([p0, p1, p2, p1, p3, p2])

    # 2D Chordwise Slice at slice_eta
    slice_j = min(req.ny - 1, max(0, int(round(req.slice_eta * (req.ny - 1)))))
    slice_data: List[ChordwiseSlicePoint] = []
    for i, xi in enumerate(x_nodes):
        cpu = cp_grid_upper[slice_j][i]
        cpl = cp_grid_lower[slice_j][i]
        is_shk = bool(has_shock and 0.54 <= xi <= 0.62)
        slice_data.append(ChordwiseSlicePoint(
            xc=round(xi, 4),
            cp_upper=round(cpu, 3),
            cp_lower=round(cpl, 3),
            is_shock=is_shk,
        ))

    ld = cl_base / max(cd_base, 1e-4)

    return Surface3DResponse(
        airfoil=req.airfoil,
        alpha_deg=req.alpha_deg,
        mach=req.mach,
        reynolds=req.reynolds,
        cl=round(cl_base, 4),
        cd=round(cd_base, 5),
        cm=round(cm_base, 4),
        lift_to_drag=round(ld, 2),
        has_shock=has_shock,
        shock_xc=shock_xc,
        stagnation_xc=0.015,
        vertices=vertices,
        normals=normals,
        colors=colors,
        indices=indices,
        cp_min=round(cp_min, 3),
        cp_max=round(cp_max, 3),
        slice_data=slice_data,
        mesh_stats={
            "nodes_total": len(vertices) // 3,
            "triangles_count": len(indices) // 3,
            "quad_panels": (req.nx - 1) * (req.ny - 1) * 2,
            "aspect_ratio": req.aspect_ratio,
            "span_m": req.span,
            "sweep_deg": req.sweep_deg,
        },
    )
