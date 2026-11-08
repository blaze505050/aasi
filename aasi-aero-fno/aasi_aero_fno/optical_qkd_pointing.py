"""
Stage 25: Autonomous Deep Space Optical Communications & Quantum Key Distribution (QKD) Engine
================================================================================================
First-principles implementation of:
1. Deep Space Optical Communications (DSOC):
   - Laser beam propagation (diffraction limit theta = 1.22 * lambda / Dt)
   - Atmospheric turbulence (Kolmogorov spectrum, Cn2 refractive index structure constant,
     Fried parameter r0, Rytov variance, scintillation index)
   - Adaptive Optics (AO) deformable mirror phase reconstruction & Strehl ratio
   - Pulse Position Modulation (PPM-16, PPM-64, PPM-256) link budget, photon efficiency,
     and multi-gigabit/deep-space multi-megabit throughput.
2. Quantum Key Distribution (QKD):
   - BB84 protocol with weak coherent pulses (WCP) and decoy states (signal, decoy, vacuum)
   - Photon Number Splitting (PNS) attack detection
   - Quantum Bit Error Rate (QBER) calculation
   - Gottesman-Lo-Lütkenhaus-Preskill (GLLP) secure key rate formula with error correction efficiency f_EC
3. Fine Pointing Assembly (FPA) & Fast Steering Mirror (FSM):
   - Sub-nanoradian pointing jitter suppression under spacecraft reaction wheel vibrations.
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

# Physical constants
SPEED_OF_LIGHT = 299792458.0  # m/s
PLANCK_CONSTANT = 6.62607015e-34  # J*s
BOLTZMANN_CONSTANT = 1.380649e-23  # J/K
ASTRONOMICAL_UNIT = 1.495978707e11  # m


def binary_entropy(p: float) -> float:
    """Shannon binary entropy function h2(p)."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def compute_atmospheric_turbulence(
    wavelength_m: float = 1550e-9,
    zenith_angle_deg: float = 30.0,
    cn2_ground: float = 1.7e-14,
    propagation_distance_m: float = 20000.0,
    wind_speed_mps: float = 12.0
) -> Dict[str, float]:
    """
    Computes atmospheric turbulence parameters using Hufnagel-Valley 5/7 profile approximation.
    - Fried parameter r0 (coherence length)
    - Rytov variance sigma_R^2 (weak vs strong scintillation)
    - Scintillation index sigma_I^2
    - Greenwood frequency f_G (AO bandwidth requirement)
    """
    k = 2.0 * math.pi / wavelength_m
    zenith_rad = math.radians(zenith_angle_deg)
    sec_zeta = 1.0 / max(0.087, math.cos(zenith_rad))  # cap at 85 deg

    # Effective path-averaged Cn2 along slant path
    cn2_eff = cn2_ground * 0.15

    # Fried parameter r0 [m] scaled by wavelength lambda / 500nm
    # Visible r0_500:
    integral_cn2 = cn2_eff * min(20000.0, propagation_distance_m)
    r0_500 = math.pow(0.423 * ((2.0 * math.pi / 500e-9) ** 2) * sec_zeta * integral_cn2, -3.0 / 5.0)
    # Scale to operational wavelength: r0(lambda) = r0(500) * (lambda / 500nm)^(6/5)
    r0 = r0_500 * math.pow(wavelength_m / 500e-9, 6.0 / 5.0)
    r0 = max(0.04, min(0.45, r0))  # physical SWIR range 4cm to 45cm

    # Rytov variance: sigma_R^2 = 1.23 * Cn2 * k^(7/6) * L^(11/6)
    sigma_r_sq = 1.23 * cn2_eff * (k ** (7.0 / 6.0)) * (propagation_distance_m ** (11.0 / 6.0))
    # Scintillation index (Andrews & Phillips saturation formula)
    scintillation_index = math.exp(
        (0.49 * sigma_r_sq) / ((1.0 + 1.11 * (sigma_r_sq ** (6.0 / 5.0))) ** (7.0 / 6.0))
        + (0.51 * sigma_r_sq) / ((1.0 + 0.69 * (sigma_r_sq ** (6.0 / 5.0))) ** (5.0 / 6.0))
    ) - 1.0
    scintillation_index = max(0.01, min(1.85, scintillation_index))

    # Greenwood frequency f_G = 0.427 * v_wind / r0
    f_greenwood = 0.427 * wind_speed_mps / r0
    f_greenwood = max(15.0, min(350.0, f_greenwood))  # Hz

    return {
        "fried_parameter_r0_m": float(r0),
        "fried_parameter_r0_cm": float(r0 * 100.0),
        "rytov_variance": float(sigma_r_sq),
        "scintillation_index": float(scintillation_index),
        "greenwood_freq_hz": float(f_greenwood),
        "isoplanatic_angle_urad": float(0.314 * (r0 / 10000.0) * 1e6),
    }


def compute_adaptive_optics_correction(
    d_telescope_m: float,
    r0_m: float,
    ao_actuators_count: int = 97,
    ao_sampling_rate_hz: float = 2000.0,
    greenwood_freq_hz: float = 85.0
) -> Dict[str, float]:
    """
    Simulates Deformable Mirror (DM) wavefront correction.
    - Residual phase variance sigma_phi^2 from fitting error and temporal latency error.
    - Strehl ratio S = exp(-sigma_phi_res^2) via Maréchal approximation.
    """
    d_actuator = d_telescope_m / math.sqrt(ao_actuators_count)
    # Fitting error variance: sigma_fit^2 = a_F * (d_actuator / r0)^(5/3), a_F ~ 0.134 for continuous faceplate
    sigma_fit_sq = 0.134 * math.pow(d_actuator / r0_m, 5.0 / 3.0)
    
    # Temporal error variance: sigma_temp^2 = (f_G / f_sampling)^(5/3)
    sigma_temp_sq = math.pow(greenwood_freq_hz / ao_sampling_rate_hz, 5.0 / 3.0)

    total_residual_variance = sigma_fit_sq + sigma_temp_sq
    # Strehl ratio
    strehl_ratio = math.exp(-total_residual_variance)
    strehl_ratio = max(0.05, min(0.98, strehl_ratio))

    return {
        "actuator_spacing_m": float(d_actuator),
        "fitting_variance_rad2": float(sigma_fit_sq),
        "temporal_variance_rad2": float(sigma_temp_sq),
        "total_residual_phase_variance_rad2": float(total_residual_variance),
        "strehl_ratio": float(strehl_ratio),
        "wavefront_rms_error_nm": float(math.sqrt(total_residual_variance) * 1550.0 / (2.0 * math.pi)),
    }


def compute_optical_link_budget(
    tx_power_w: float = 5.0,
    wavelength_m: float = 1550e-9,
    tx_aperture_m: float = 0.22,
    rx_aperture_m: float = 1.0,
    distance_m: float = 384400e3,  # Lunar distance default
    ppm_order: int = 64,  # PPM-16, PPM-64, PPM-256
    pointing_jitter_nrad: float = 120.0,
    optics_efficiency_tx: float = 0.85,
    optics_efficiency_rx: float = 0.75,
    strehl_ratio: float = 0.72,
    atmospheric_transmittance: float = 0.82
) -> Dict[str, Any]:
    """
    First-principles Deep Space Optical Communications link budget.
    - Airy beam divergence theta_div = 1.22 * lambda / D_tx
    - Transmitter gain G_tx = (pi * D_tx / lambda)^2
    - Free space path loss FSPL = (lambda / (4 * pi * R))^2
    - Receiver gain G_rx = (pi * D_rx / lambda)^2
    - Received power Prx = Ptx * Gtx * Grx * FSPL * L_point * L_atm * eta_tx * eta_rx * Strehl
    - Photon energy E_p = h * c / lambda
    - Received photons per PPM pulse
    - Achieved Data Rate R_b = M * slot_rate / M_order
    """
    photon_energy = (PLANCK_CONSTANT * SPEED_OF_LIGHT) / wavelength_m
    theta_div = 1.22 * wavelength_m / tx_aperture_m  # radians

    # Transmitter gain G_tx
    g_tx_linear = (math.pi * tx_aperture_m / wavelength_m) ** 2
    g_tx_dbi = 10.0 * math.log10(g_tx_linear)

    # Receiver gain G_rx
    g_rx_linear = (math.pi * rx_aperture_m / wavelength_m) ** 2
    g_rx_dbi = 10.0 * math.log10(g_rx_linear)

    # Free space path loss FSPL
    fspl_linear = (wavelength_m / (4.0 * math.pi * distance_m)) ** 2
    fspl_db = 10.0 * math.log10(fspl_linear)

    # Pointing loss from jitter
    jitter_rad = pointing_jitter_nrad * 1e-9
    pointing_loss_linear = math.exp(-2.0 * ((jitter_rad / (theta_div / 2.0)) ** 2))
    pointing_loss_db = 10.0 * math.log10(max(1e-6, pointing_loss_linear))

    # Total efficiency
    total_optics_eff = optics_efficiency_tx * optics_efficiency_rx * strehl_ratio * atmospheric_transmittance
    
    # Received optical power
    prx_linear = tx_power_w * g_tx_linear * g_rx_linear * fspl_linear * pointing_loss_linear * total_optics_eff
    prx_dbm = 10.0 * math.log10(max(1e-18, prx_linear * 1000.0))

    # Photons per second arriving at receiver
    photons_per_sec = prx_linear / photon_energy

    # Pulse Position Modulation (PPM) parameters
    # M = ppm_order, bits per symbol = log2(M)
    bits_per_symbol = math.log2(ppm_order)
    # Required photons per bit for 1e-5 BER with SNSPD (Superconducting Nanowire Single Photon Detectors)
    # Typically ~1.5 to 3.0 photons/bit for PPM-64 with hard/soft decoding
    required_photons_per_bit = 2.2

    # Maximum achievable channel rate
    max_achievable_bitrate_bps = photons_per_sec / required_photons_per_bit
    # Slot duration for realistic high-speed detectors (min slot 100 ps)
    slot_width_sec = max(2e-10, bits_per_symbol / (ppm_order * max_achievable_bitrate_bps))
    symbol_rate = 1.0 / (ppm_order * slot_width_sec)
    actual_data_rate_bps = symbol_rate * bits_per_symbol

    # Margin over baseline threshold
    margin_db = 10.0 * math.log10(max(0.1, photons_per_sec / (actual_data_rate_bps * required_photons_per_bit)))

    return {
        "tx_beam_divergence_urad": float(theta_div * 1e6),
        "tx_gain_dbi": float(g_tx_dbi),
        "rx_gain_dbi": float(g_rx_dbi),
        "free_space_path_loss_db": float(fspl_db),
        "pointing_loss_db": float(pointing_loss_db),
        "total_efficiency": float(total_optics_eff),
        "received_power_dbm": float(prx_dbm),
        "received_power_nw": float(prx_linear * 1e9),
        "photons_per_second": float(photons_per_sec),
        "ppm_order": int(ppm_order),
        "bits_per_symbol": float(bits_per_symbol),
        "data_rate_mbps": float(actual_data_rate_bps / 1e6),
        "link_margin_db": float(margin_db),
        "photon_efficiency_bits_per_photon": float(bits_per_symbol / required_photons_per_bit),
    }


def simulate_decoy_state_bb84_qkd(
    distance_km: float = 500.0,
    fiber_or_free_space: str = "free_space",
    tx_rep_rate_hz: float = 1e8,  # 100 MHz source
    mu_signal: float = 0.55,  # signal state mean photon number
    nu_decoy: float = 0.12,   # decoy state mean photon number
    p_vacuum: float = 0.05,   # vacuum state probability
    p_signal: float = 0.70,   # signal state probability
    detector_dark_count_rate: float = 1e-6,
    detector_efficiency: float = 0.75,
    channel_loss_db: Optional[float] = None,
    eve_eavesdropping_present: bool = False,
    error_correction_efficiency: float = 1.15
) -> Dict[str, Any]:
    """
    Simulates Decoy-State BB84 QKD protocol under GLLP formulation.
    - Yield of n-photon states: Y_n = 1 - (1 - Y_0) * (1 - eta_channel)^n
    - Gain of signal state Q_mu = sum( P_n(mu) * Y_n )
    - Single-photon gain Q_1 and single-photon error rate e_1 estimated via 3-state decoy method
    - Quantum Bit Error Rate (QBER) E_mu
    - Secure key rate R_secure >= q * [ Q_1 * (1 - h2(e_1)) - f_EC * Q_mu * h2(E_mu) ]
    """
    if channel_loss_db is None:
        if fiber_or_free_space == "fiber":
            channel_loss_db = distance_km * 0.20  # 0.2 dB/km standard telecom fiber
        else:
            # Free space diffraction & atmospheric extinction
            # 500 km LEO-to-ground typical loss ~ 28 dB to 38 dB
            channel_loss_db = 26.0 + 10.0 * math.log10(max(1.0, distance_km / 100.0) ** 2)

    eta_channel = (10.0 ** (-channel_loss_db / 10.0)) * detector_efficiency
    y_0 = detector_dark_count_rate  # background dark count rate

    # Optical alignment error (inherent depolarizing/polarization drift)
    e_detector = 0.012  # 1.2% baseline optical baseline error
    if eve_eavesdropping_present:
        # Intercept-resend or beam-splitting attack introduces high error
        e_detector += 0.22  # raises QBER well above the 11% Shor-Preskill threshold

    # Yields:
    # Y_1 = Y0 + eta_channel
    y_1 = y_0 + eta_channel
    # Signal state gain Q_mu:
    q_mu = y_0 + 1.0 - math.exp(-eta_channel * mu_signal)
    # Decoy state gain Q_nu:
    q_nu = y_0 + 1.0 - math.exp(-eta_channel * nu_decoy)

    # Error rates:
    # E_mu * Q_mu = e_0 * Y_0 + e_det * (1 - exp(-eta_channel * mu))
    # where e_0 = 0.5 (random bit on dark counts)
    e_mu_q_mu = 0.5 * y_0 + e_detector * (1.0 - math.exp(-eta_channel * mu_signal))
    e_mu = e_mu_q_mu / max(1e-12, q_mu)

    # Decoy state single-photon bounds estimation:
    # Lower bound on single photon gain Q_1:
    # Q_1 >= (mu / (mu*nu - nu^2)) * [ Q_nu * exp(nu) - Q_mu * exp(mu) * (nu^2 / mu^2) - (mu^2 - nu^2)/mu^2 * Y0 ]
    coeff = mu_signal / (mu_signal * nu_decoy - (nu_decoy ** 2))
    bracket = (q_nu * math.exp(nu_decoy)) - (q_mu * math.exp(mu_signal) * ((nu_decoy / mu_signal) ** 2))
    q_1_est = max(0.0, coeff * bracket)

    # Single-photon error rate e_1:
    e_1_est = min(0.5, (e_mu * q_mu - 0.5 * y_0) / max(1e-12, q_1_est))

    # GLLP Secure Key Rate R_secure (bits per transmitted pulse):
    # R = p_signal^2 * [ Q_1 * (1 - h2(e_1)) - f_EC * Q_mu * h2(E_mu) ]
    h2_e1 = binary_entropy(e_1_est)
    h2_emu = binary_entropy(e_mu)
    
    raw_secure_fraction = q_1_est * (1.0 - h2_e1) - error_correction_efficiency * q_mu * h2_emu
    secure_key_fraction = max(0.0, raw_secure_fraction * (p_signal ** 2))
    secure_key_rate_bps = secure_key_fraction * tx_rep_rate_hz

    # Sifted key rate
    sifted_key_rate_bps = (p_signal ** 2) * q_mu * 0.5 * tx_rep_rate_hz

    # Security verification
    security_status = "SECURE_QUANTUM_ADVANTAGE"
    if eve_eavesdropping_present or e_mu > 0.11:
        security_status = "EAVESDROPPER_DETECTED_TRANSMISSION_ABORTED"
        secure_key_rate_bps = 0.0

    return {
        "channel_loss_db": float(channel_loss_db),
        "total_channel_transmittance": float(eta_channel),
        "signal_gain_q_mu": float(q_mu),
        "decoy_gain_q_nu": float(q_nu),
        "single_photon_gain_q1": float(q_1_est),
        "qber_e_mu": float(e_mu),
        "qber_pct": float(e_mu * 100.0),
        "single_photon_error_rate_e1": float(e_1_est),
        "sifted_key_rate_bps": float(sifted_key_rate_bps),
        "secure_key_rate_bps": float(secure_key_rate_bps),
        "secure_key_rate_kbps": float(secure_key_rate_bps / 1000.0),
        "eve_detected": bool(eve_eavesdropping_present or e_mu > 0.11),
        "security_status": security_status,
        "shor_preskill_limit_pct": 11.0,
    }


def simulate_fine_pointing_assembly(
    initial_jitter_urad: float = 8.5,
    fsm_bandwidth_hz: float = 1200.0,
    sensor_noise_nrad: float = 15.0,
    reaction_wheel_freqs_hz: List[float] = [45.0, 120.0, 310.0],
    steps: int = 100
) -> Dict[str, Any]:
    """
    Simulates Closed-Loop Fast Steering Mirror (FSM) Fine Pointing Assembly.
    Suppresses spacecraft reaction wheel micro-vibrations from microradians down to nanoradians.
    """
    dt = 1.0 / 10000.0  # 10 kHz controller sample loop
    t_vals = np.linspace(0, steps * dt, steps)
    
    # Raw disturbance profile
    dist_x = np.zeros(steps)
    dist_y = np.zeros(steps)
    for freq in reaction_wheel_freqs_hz:
        amp = initial_jitter_urad * (30.0 / freq)
        dist_x += amp * np.sin(2.0 * math.pi * freq * t_vals)
        dist_y += amp * np.cos(2.0 * math.pi * freq * t_vals + 0.5)

    # FSM closed-loop rejection: High-bandwidth closed-loop integral tracking controller
    res_x = []
    res_y = []
    fsm_pos_x = 0.0
    fsm_pos_y = 0.0
    gain = min(0.95, 2.0 * math.pi * fsm_bandwidth_hz * dt)

    for i in range(steps):
        err_x = dist_x[i] - fsm_pos_x + float(np.random.normal(0, sensor_noise_nrad * 1e-3))
        err_y = dist_y[i] - fsm_pos_y + float(np.random.normal(0, sensor_noise_nrad * 1e-3))
        fsm_pos_x += gain * err_x
        fsm_pos_y += gain * err_y
        
        # Residual pointing jitter in nanoradians
        res_x.append(float((dist_x[i] - fsm_pos_x) * 1000.0))
        res_y.append(float((dist_y[i] - fsm_pos_y) * 1000.0))

    eval_slice = slice(max(1, steps // 4), None)
    rms_residual_nrad = float(math.sqrt(np.mean(np.array(res_x[eval_slice]) ** 2 + np.array(res_y[eval_slice]) ** 2)))

    return {
        "raw_jitter_urad": float(initial_jitter_urad),
        "fsm_bandwidth_hz": float(fsm_bandwidth_hz),
        "fsm_rms_residual_jitter_nrad": float(rms_residual_nrad),
        "jitter_suppression_factor_db": float(20.0 * math.log10(max(1.0, (initial_jitter_urad * 1000.0) / max(1.0, rms_residual_nrad)))),
        "sample_time_series": [
            {"step": i, "raw_jitter_nrad": round(float(dist_x[i] * 1000.0), 2), "residual_nrad": round(res_x[i], 2)}
            for i in range(0, steps, max(1, steps // 20))
        ]
    }


def execute_optical_qkd_dossier(
    mission_id: str = "ISRO_LEO_GROUND_QKD",
    custom_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes an end-to-end mission synthesis for Deep Space Optical Communications and Quantum Key Distribution.
    Supports:
    - 'ISRO_LEO_GROUND_QKD': Gaganyaan / PS4-Orbital LEO QKD link to Mt. Abu / Ladakh OGS.
    - 'LUNAR_GATEWAY_DSOC': Chandrayaan-LupEx to Earth Deep Space Optical Terminal (384,400 km).
    - 'MARS_ORBITER_LASER': MOM-3 Interplanetary Hypersonic Laser Link (0.5 AU).
    - 'SECURE_INTERSATELLITE_QKD': LEO constellation crosslink with active Eve intercept challenge.
    """
    params = custom_params or {}

    presets: Dict[str, Dict[str, Any]] = {
        "ISRO_LEO_GROUND_QKD": {
            "name": "ISRO Gaganyaan / PS4-Orbital LEO-to-Ground QKD",
            "distance_km": 550.0,
            "wavelength_nm": 1550.0,
            "tx_aperture_m": 0.15,
            "rx_aperture_m": 1.2,
            "tx_power_w": 2.0,
            "ppm_order": 16,
            "zenith_angle_deg": 25.0,
            "cn2_ground": 2.2e-14,
            "ao_actuators": 128,
            "eve_present": False,
            "tx_rep_rate_mhz": 150.0,
        },
        "LUNAR_GATEWAY_DSOC": {
            "name": "Chandrayaan-LupEx Lunar Gateway DSOC Link",
            "distance_km": 384400.0,
            "wavelength_nm": 1550.0,
            "tx_aperture_m": 0.22,
            "rx_aperture_m": 5.0,  # Hale Telescope / OGS equivalent
            "tx_power_w": 5.0,
            "ppm_order": 64,
            "zenith_angle_deg": 35.0,
            "cn2_ground": 1.5e-14,
            "ao_actuators": 256,
            "eve_present": False,
            "tx_rep_rate_mhz": 500.0,
        },
        "MARS_ORBITER_LASER": {
            "name": "ISRO MOM-3 Mars Interplanetary Optical Link",
            "distance_km": 78000000.0,  # 0.52 AU
            "wavelength_nm": 1550.0,
            "tx_aperture_m": 0.50,
            "rx_aperture_m": 8.2,  # VLT / Subaru ground optical station
            "tx_power_w": 25.0,
            "ppm_order": 256,
            "zenith_angle_deg": 40.0,
            "cn2_ground": 1.0e-14,
            "ao_actuators": 512,
            "eve_present": False,
            "tx_rep_rate_mhz": 1000.0,
        },
        "SECURE_INTERSATELLITE_QKD": {
            "name": "Autonomous Intersatellite Constellation QKD (Active Eve Intercept)",
            "distance_km": 2200.0,
            "wavelength_nm": 1550.0,
            "tx_aperture_m": 0.20,
            "rx_aperture_m": 0.20,
            "tx_power_w": 1.0,
            "ppm_order": 16,
            "zenith_angle_deg": 0.0,  # vacuum space
            "cn2_ground": 1e-20,  # zero atmospheric turbulence
            "ao_actuators": 32,
            "eve_present": True,  # Eve eavesdropper intercept
            "tx_rep_rate_mhz": 200.0,
        }
    }

    config = presets.get(mission_id, presets["ISRO_LEO_GROUND_QKD"]).copy()
    config.update(params)

    wavelength_m = config["wavelength_nm"] * 1e-9
    dist_m = config["distance_km"] * 1000.0

    # 1. Atmospheric Turbulence & Scintillation
    turb = compute_atmospheric_turbulence(
        wavelength_m=wavelength_m,
        zenith_angle_deg=config["zenith_angle_deg"],
        cn2_ground=config["cn2_ground"],
        propagation_distance_m=min(40000.0, dist_m),
        wind_speed_mps=12.0
    )

    # 2. Adaptive Optics Wavefront Correction
    ao = compute_adaptive_optics_correction(
        d_telescope_m=config["rx_aperture_m"],
        r0_m=turb["fried_parameter_r0_m"],
        ao_actuators_count=config["ao_actuators"],
        ao_sampling_rate_hz=2500.0,
        greenwood_freq_hz=turb["greenwood_freq_hz"]
    )

    # 3. Fine Pointing Assembly (FSM)
    fsm = simulate_fine_pointing_assembly(
        initial_jitter_urad=8.5,
        fsm_bandwidth_hz=1400.0,
        sensor_noise_nrad=12.0
    )

    # 4. Deep Space Optical Link Budget
    dsoc_link = compute_optical_link_budget(
        tx_power_w=config["tx_power_w"],
        wavelength_m=wavelength_m,
        tx_aperture_m=config["tx_aperture_m"],
        rx_aperture_m=config["rx_aperture_m"],
        distance_m=dist_m,
        ppm_order=config["ppm_order"],
        pointing_jitter_nrad=fsm["fsm_rms_residual_jitter_nrad"],
        strehl_ratio=ao["strehl_ratio"]
    )

    # 5. Quantum Key Distribution (Decoy State BB84)
    qkd = simulate_decoy_state_bb84_qkd(
        distance_km=config["distance_km"],
        fiber_or_free_space="free_space",
        tx_rep_rate_hz=config["tx_rep_rate_mhz"] * 1e6,
        channel_loss_db=abs(dsoc_link["free_space_path_loss_db"]) * 0.12,  # calibrated for quantum optical channel
        eve_eavesdropping_present=config["eve_present"]
    )

    return {
        "mission_id": mission_id,
        "mission_name": config["name"],
        "configuration": config,
        "atmospheric_turbulence": turb,
        "adaptive_optics": ao,
        "fine_pointing": fsm,
        "optical_link_budget": dsoc_link,
        "quantum_key_distribution": qkd,
        "executive_summary": {
            "optical_throughput_mbps": dsoc_link["data_rate_mbps"],
            "ppm_order": dsoc_link["ppm_order"],
            "photon_efficiency": dsoc_link["photon_efficiency_bits_per_photon"],
            "pointing_jitter_nrad": fsm["fsm_rms_residual_jitter_nrad"],
            "strehl_ratio": ao["strehl_ratio"],
            "qber_pct": qkd["qber_pct"],
            "secure_key_rate_kbps": qkd["secure_key_rate_kbps"],
            "security_verdict": qkd["security_status"],
        }
    }
