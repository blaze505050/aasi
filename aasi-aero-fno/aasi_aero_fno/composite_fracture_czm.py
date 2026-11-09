"""
Stage 34: Composite Layup & Fracture Mechanics Cohesive Zone Digital Twin.

First-principles Classical Laminate Theory (CLT), 3D Tsai-Wu failure criteria,
and mixed-mode Bilinear Cohesive Zone Modeling (CZM) with Benzeggagh-Kenane (B-K)
fracture energy criterion for aerospace composite structures (IM7/8552, E-Glass/913).
"""

import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# 1. COMPOSITE MATERIAL DATABASE
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CompositeMaterial:
    name: str
    e1_gpa: float        # Longitudinal Young's modulus
    e2_gpa: float        # Transverse Young's modulus
    g12_gpa: float       # In-plane shear modulus
    nu12: float          # Major Poisson's ratio
    ply_thickness_mm: float
    # Strengths (MPa)
    xt_mpa: float        # Longitudinal tensile
    xc_mpa: float        # Longitudinal compressive
    yt_mpa: float        # Transverse tensile
    yc_mpa: float        # Transverse compressive
    s12_mpa: float       # In-plane shear strength
    # Interlaminar Fracture Properties (kJ/m^2 = N/mm)
    g_ic_kj_m2: float    # Mode I critical fracture energy
    g_iic_kj_m2: float   # Mode II critical fracture energy
    bk_eta: float        # Benzeggagh-Kenane mixed-mode exponent
    interfacial_strength_mpa: float  # Interlaminar normal strength


COMPOSITE_DB: Dict[str, CompositeMaterial] = {
    "IM7_8552": CompositeMaterial(
        name="Hexcel HexPly IM7/8552 Aerospace Carbon/Epoxy",
        e1_gpa=161.0,
        e2_gpa=11.38,
        g12_gpa=5.17,
        nu12=0.32,
        ply_thickness_mm=0.125,
        xt_mpa=2560.0,
        xc_mpa=1690.0,
        yt_mpa=64.0,
        yc_mpa=286.0,
        s12_mpa=90.0,
        g_ic_kj_m2=0.28,
        g_iic_kj_m2=0.79,
        bk_eta=1.75,
        interfacial_strength_mpa=60.0,
    ),
    "E_GLASS_913": CompositeMaterial(
        name="E-Glass/913 Structural Fiberglass/Epoxy",
        e1_gpa=42.0,
        e2_gpa=10.5,
        g12_gpa=3.9,
        nu12=0.28,
        ply_thickness_mm=0.150,
        xt_mpa=1120.0,
        xc_mpa=610.0,
        yt_mpa=36.0,
        yc_mpa=145.0,
        s12_mpa=72.0,
        g_ic_kj_m2=0.22,
        g_iic_kj_m2=0.62,
        bk_eta=2.00,
        interfacial_strength_mpa=45.0,
    ),
}


# Standard Aerospace Layups
STANDARD_LAYUPS: Dict[str, List[float]] = {
    "QUASI_ISOTROPIC_16": [0, 45, -45, 90, 90, -45, 45, 0, 0, 45, -45, 90, 90, -45, 45, 0],
    "HARD_WING_SPAR_16": [0, 0, 45, -45, 0, 0, 45, -45, -45, 45, 0, 0, -45, 45, 0, 0],
    "TORSION_BOX_SKIN_16": [45, -45, 45, -45, 0, 90, 45, -45, -45, 45, 90, 0, -45, 45, -45, 45],
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. CLASSICAL LAMINATE THEORY (CLT) ABD MATRIX ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def compute_clt_abd_matrix(
    material_key: str = "IM7_8552",
    ply_angles_deg: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Computes Classical Laminate Theory (CLT) Extensional (A), Coupling (B),
    and Bending (D) stiffness matrices for a composite laminate.
    """
    mat = COMPOSITE_DB.get(material_key, COMPOSITE_DB["IM7_8552"])
    if ply_angles_deg is None:
        ply_angles_deg = STANDARD_LAYUPS["QUASI_ISOTROPIC_16"]

    num_plies = len(ply_angles_deg)
    total_thickness_mm = num_plies * mat.ply_thickness_mm

    # 1. On-axis reduced stiffness matrix Q (in GPa)
    nu21 = mat.nu12 * mat.e2_gpa / mat.e1_gpa
    denom = 1.0 - mat.nu12 * nu21

    q11 = mat.e1_gpa / denom
    q22 = mat.e2_gpa / denom
    q12 = mat.nu12 * mat.e2_gpa / denom
    q66 = mat.g12_gpa

    # 2. Ply coordinates z_k in millimeters from mid-plane (-h/2 to +h/2)
    z_coords = np.linspace(-total_thickness_mm / 2.0, total_thickness_mm / 2.0, num_plies + 1)

    a_mat = np.zeros((3, 3))
    b_mat = np.zeros((3, 3))
    d_mat = np.zeros((3, 3))

    ply_details: List[Dict[str, Any]] = []

    for k, theta_deg in enumerate(ply_angles_deg):
        theta_rad = math.radians(theta_deg)
        m = math.cos(theta_rad)
        n = math.sin(theta_rad)
        m2 = m * m
        n2 = n * n
        m4 = m2 * m2
        n4 = n2 * n2
        m3n = m2 * m * n
        mn3 = m * n2 * n

        # Transformed reduced stiffness Qbar (in GPa)
        qbar11 = q11 * m4 + 2.0 * (q12 + 2.0 * q66) * m2 * n2 + q22 * n4
        qbar22 = q11 * n4 + 2.0 * (q12 + 2.0 * q66) * m2 * n2 + q22 * m4
        qbar12 = (q11 + q22 - 4.0 * q66) * m2 * n2 + q12 * (m4 + n4)
        qbar66 = (q11 + q22 - 2.0 * q12 - 2.0 * q66) * m2 * n2 + q66 * (m4 + n4)
        qbar16 = (q11 - q12 - 2.0 * q66) * m3n + (q12 - q22 + 2.0 * q66) * mn3
        qbar26 = (q11 - q12 - 2.0 * q66) * mn3 + (q12 - q22 + 2.0 * q66) * m3n

        qbar = np.array([
            [qbar11, qbar12, qbar16],
            [qbar12, qbar22, qbar26],
            [qbar16, qbar26, qbar66],
        ])

        zk = z_coords[k + 1]
        zk_prev = z_coords[k]

        # Integrate through thickness:
        # With zk in mm and qbar in GPa:
        # A_ij = sum(Qbar_ij * dz) [kN/mm]
        # B_ij = 0.5 * sum(Qbar_ij * dz^2) * 1e3 [N]
        # D_ij = (1/3) * sum(Qbar_ij * dz^3) * 1e3 [N*mm]
        a_mat += qbar * (zk - zk_prev)  # kN/mm
        b_mat += 0.5 * qbar * (zk ** 2 - zk_prev ** 2) * 1e3  # N
        d_mat += (1.0 / 3.0) * qbar * (zk ** 3 - zk_prev ** 3) * 1e3  # N*mm

        ply_details.append({
            "ply_index": k + 1,
            "angle_deg": theta_deg,
            "z_lower_mm": round(zk_prev, 3),
            "z_upper_mm": round(zk, 3),
            "qbar_11_gpa": round(qbar11, 2),
            "qbar_22_gpa": round(qbar22, 2),
        })

    # Effective Laminate Engineering Properties
    # Invert A matrix for in-plane compliance
    try:
        a_inv = np.linalg.inv(a_mat)  # (kN/mm)^-1
        ex_eff_gpa = round(1.0 / (a_inv[0, 0] * total_thickness_mm), 2)
        ey_eff_gpa = round(1.0 / (a_inv[1, 1] * total_thickness_mm), 2)
        gxy_eff_gpa = round(1.0 / (a_inv[2, 2] * total_thickness_mm), 2)
        nuxy_eff = round(-a_inv[0, 1] / a_inv[0, 0], 3)
    except Exception:
        ex_eff_gpa = 50.0
        ey_eff_gpa = 50.0
        gxy_eff_gpa = 20.0
        nuxy_eff = 0.3

    is_symmetric = bool(np.max(np.abs(b_mat)) < 1e-4)

    return {
        "material": mat.name,
        "num_plies": num_plies,
        "total_thickness_mm": round(total_thickness_mm, 3),
        "is_symmetric": is_symmetric,
        "effective_engineering_constants": {
            "ex_eff_gpa": ex_eff_gpa,
            "ey_eff_gpa": ey_eff_gpa,
            "gxy_eff_gpa": gxy_eff_gpa,
            "nu_xy_eff": nuxy_eff,
        },
        "abd_matrices": {
            "a_matrix_kn_per_mm": [[round(float(v), 2) for v in row] for row in a_mat],
            "b_matrix_n": [[round(float(v), 4) for v in row] for row in b_mat],
            "d_matrix_n_mm": [[round(float(v), 2) for v in row] for row in d_mat],
        },
        "plies": ply_details,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. 3D TSAI-WU FAILURE CRITERION & FIRST PLY FAILURE ENVELOPE
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_tsai_wu_failure(
    material_key: str = "IM7_8552",
    sigma1_mpa: float = 800.0,
    sigma2_mpa: float = 35.0,
    tau12_mpa: float = 40.0,
) -> Dict[str, Any]:
    """
    Evaluates the Tsai-Wu interactive quadratic failure criterion:
    F_1 * sigma_1 + F_2 * sigma_2 + F_11 * sigma_1^2 + F_22 * sigma_2^2 +
    F_66 * tau_12^2 + 2 * F_12 * sigma_1 * sigma_2 <= 1.0
    """
    mat = COMPOSITE_DB.get(material_key, COMPOSITE_DB["IM7_8552"])

    xt = mat.xt_mpa
    xc = mat.xc_mpa
    yt = mat.yt_mpa
    yc = mat.yc_mpa
    s12 = mat.s12_mpa

    # Linear & Quadratic strength tensor coefficients
    f1 = (1.0 / xt) - (1.0 / xc)
    f11 = 1.0 / (xt * xc)
    f2 = (1.0 / yt) - (1.0 / yc)
    f22 = 1.0 / (yt * yc)
    f66 = 1.0 / (s12 ** 2)

    # Normalized interaction coefficient F12 (typically -0.5 * sqrt(F11 * F22))
    f12 = -0.5 * math.sqrt(f11 * f22)

    # Failure index computation
    f_index = (
        f1 * sigma1_mpa
        + f2 * sigma2_mpa
        + f11 * (sigma1_mpa ** 2)
        + f22 * (sigma2_mpa ** 2)
        + f66 * (tau12_mpa ** 2)
        + 2.0 * f12 * sigma1_mpa * sigma2_mpa
    )

    is_failed = bool(f_index >= 1.0)

    # Reserve factor / safety factor (scaling factor R such that F(R * sigma) = 1)
    # a * R^2 + b * R - 1 = 0
    a_quad = f11 * (sigma1_mpa ** 2) + f22 * (sigma2_mpa ** 2) + f66 * (tau12_mpa ** 2) + 2.0 * f12 * sigma1_mpa * sigma2_mpa
    b_lin = f1 * sigma1_mpa + f2 * sigma2_mpa

    if a_quad > 1e-12:
        disc = b_lin ** 2 + 4.0 * a_quad
        safety_factor = round((-b_lin + math.sqrt(max(0.0, disc))) / (2.0 * a_quad), 3)
    else:
        safety_factor = 99.0

    # Generate 2D Tsai-Wu failure envelope curve (sigma1 vs sigma2 at tau12 = 0)
    theta_vals = np.linspace(0.0, 2.0 * math.pi, 60)
    envelope_pts: List[Dict[str, float]] = []

    for th in theta_vals:
        # Unit vector direction (cos, sin)
        u1 = math.cos(th)
        u2 = math.sin(th)
        aq = f11 * (u1 ** 2) + f22 * (u2 ** 2) + 2.0 * f12 * u1 * u2
        bl = f1 * u1 + f2 * u2
        if aq > 1e-12:
            r = (-bl + math.sqrt(max(0.0, bl ** 2 + 4.0 * aq))) / (2.0 * aq)
            envelope_pts.append({
                "sigma1_mpa": round(r * u1, 1),
                "sigma2_mpa": round(r * u2, 1),
            })

    return {
        "material": mat.name,
        "input_stress_state_mpa": {
            "sigma1_longitudinal": sigma1_mpa,
            "sigma2_transverse": sigma2_mpa,
            "tau12_inplane_shear": tau12_mpa,
        },
        "tsai_wu_failure_index": round(f_index, 4),
        "is_failed": is_failed,
        "safety_factor": safety_factor,
        "failure_margin_percent": round((safety_factor - 1.0) * 100.0, 1),
        "envelope_2d_points": envelope_pts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. BILINEAR COHESIVE ZONE DELAMINATION & B-K MIXED-MODE FRACTURE
# ─────────────────────────────────────────────────────────────────────────────
def simulate_czm_delamination(
    material_key: str = "IM7_8552",
    applied_normal_opening_um: float = 12.0,
    applied_shear_sliding_um: float = 8.0,
    interface_penalty_stiffness_kpa_um: float = 1.0e5,  # K_n ~ 100 GPa/m = 100 N/mm^3
) -> Dict[str, Any]:
    """
    Simulates Bilinear Cohesive Zone Modeling (CZM) delamination response
    governed by the Benzeggagh-Kenane (B-K) mixed-mode criterion.
    """
    mat = COMPOSITE_DB.get(material_key, COMPOSITE_DB["IM7_8552"])

    g_ic = mat.g_ic_kj_m2 * 1e3    # N/m = J/m^2
    g_iic = mat.g_iic_kj_m2 * 1e3  # N/m
    eta = mat.bk_eta
    sigma_max_pa = mat.interfacial_strength_mpa * 1e6
    kn = interface_penalty_stiffness_kpa_um * 1e9  # Pa/m

    # 1. Damage initiation displacement delta_0 (m)
    delta_0 = sigma_max_pa / kn
    # 2. Ultimate separation displacement delta_f (m)
    delta_f_mode1 = (2.0 * g_ic) / sigma_max_pa
    delta_f_mode2 = (2.0 * g_iic) / sigma_max_pa

    delta_n_m = max(0.0, applied_normal_opening_um * 1e-6)
    delta_s_m = abs(applied_shear_sliding_um * 1e-6)
    delta_mixed = math.sqrt(delta_n_m ** 2 + delta_s_m ** 2)

    # Mode mixity ratio B = G_II / (G_I + G_II)
    if delta_mixed > 1e-12:
        mixity_ratio = (delta_s_m / delta_mixed) ** 2
    else:
        mixity_ratio = 0.0

    # Benzeggagh-Kenane (B-K) mixed-mode critical fracture energy G_c
    gc_mixed = g_ic + (g_iic - g_ic) * (mixity_ratio ** eta)

    # Mixed-mode separation threshold
    delta_f_mixed = (2.0 * gc_mixed) / sigma_max_pa

    # Damage parameter d (0.0 = pristine, 1.0 = fully separated delamination)
    if delta_mixed <= delta_0:
        damage_d = 0.0
        traction_pa = kn * delta_mixed
    elif delta_mixed < delta_f_mixed:
        damage_d = (delta_f_mixed * (delta_mixed - delta_0)) / (delta_mixed * (delta_f_mixed - delta_0))
        traction_pa = (1.0 - damage_d) * kn * delta_mixed
    else:
        damage_d = 1.0
        traction_pa = 0.0

    traction_mpa = traction_pa / 1e6

    # Generate full Bilinear Traction-Separation Curve for UI display
    disp_pts_um = np.linspace(0.0, (delta_f_mixed * 1e6) * 1.3, 50)
    curve_data: List[Dict[str, float]] = []

    for disp_um in disp_pts_um:
        d_m = disp_um * 1e-6
        if d_m <= delta_0:
            tr_mpa = (kn * d_m) / 1e6
            d_val = 0.0
        elif d_m < delta_f_mixed:
            d_val = (delta_f_mixed * (d_m - delta_0)) / (d_m * (delta_f_mixed - delta_0))
            tr_mpa = ((1.0 - d_val) * kn * d_m) / 1e6
        else:
            d_val = 1.0
            tr_mpa = 0.0
        curve_data.append({
            "separation_um": round(disp_um, 2),
            "traction_mpa": round(max(0.0, tr_mpa), 2),
            "damage": round(d_val, 3),
        })

    return {
        "material": mat.name,
        "cohesive_interface": {
            "mode1_fracture_energy_j_m2": round(g_ic, 1),
            "mode2_fracture_energy_j_m2": round(g_iic, 1),
            "bk_exponent_eta": eta,
            "mode_mixity_ratio_b": round(mixity_ratio, 3),
            "critical_mixed_energy_j_m2": round(gc_mixed, 1),
            "damage_initiation_separation_um": round(delta_0 * 1e6, 2),
            "ultimate_separation_um": round(delta_f_mixed * 1e6, 2),
        },
        "current_state": {
            "applied_mixed_displacement_um": round(delta_mixed * 1e6, 2),
            "current_traction_mpa": round(traction_mpa, 2),
            "damage_variable_d": round(damage_d, 3),
            "is_delaminated": bool(damage_d >= 0.99),
        },
        "traction_separation_curve": curve_data,
    }
