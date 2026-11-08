"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Activity,
  Layers,
  Sparkles,
  Lock,
  Eye,
  RefreshCw,
  Compass,
  ArrowRight,
  ChevronRight,
  Wifi,
  Sliders,
} from "lucide-react";

interface OpticalQkdStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface QkdSimulationResult {
  mission_id: string;
  mission_name: string;
  configuration: {
    name: string;
    distance_km: number;
    wavelength_nm: number;
    tx_aperture_m: number;
    rx_aperture_m: number;
    tx_power_w: number;
    ppm_order: number;
    zenith_angle_deg: number;
    cn2_ground: number;
    ao_actuators: number;
    eve_present: boolean;
    tx_rep_rate_mhz: number;
  };
  atmospheric_turbulence: {
    fried_parameter_r0_m: number;
    fried_parameter_r0_cm: number;
    rytov_variance: number;
    scintillation_index: number;
    greenwood_freq_hz: number;
    isoplanatic_angle_urad: number;
  };
  adaptive_optics: {
    actuator_spacing_m: number;
    fitting_variance_rad2: number;
    temporal_variance_rad2: number;
    total_residual_phase_variance_rad2: number;
    strehl_ratio: number;
    wavefront_rms_error_nm: number;
  };
  fine_pointing: {
    raw_jitter_urad: number;
    fsm_bandwidth_hz: number;
    fsm_rms_residual_jitter_nrad: number;
    jitter_suppression_factor_db: number;
    sample_time_series: Array<{
      step: number;
      raw_jitter_nrad: number;
      residual_nrad: number;
    }>;
  };
  optical_link_budget: {
    tx_beam_divergence_urad: number;
    tx_gain_dbi: number;
    rx_gain_dbi: number;
    free_space_path_loss_db: number;
    pointing_loss_db: number;
    total_efficiency: number;
    received_power_dbm: number;
    received_power_nw: number;
    photons_per_second: number;
    ppm_order: number;
    bits_per_symbol: number;
    data_rate_mbps: number;
    link_margin_db: number;
    photon_efficiency_bits_per_photon: number;
  };
  quantum_key_distribution: {
    channel_loss_db: number;
    total_channel_transmittance: number;
    signal_gain_q_mu: number;
    decoy_gain_q_nu: number;
    single_photon_gain_q1: number;
    qber_e_mu: number;
    qber_pct: number;
    single_photon_error_rate_e1: number;
    sifted_key_rate_bps: number;
    secure_key_rate_bps: number;
    secure_key_rate_kbps: number;
    eve_detected: boolean;
    security_status: string;
    shor_preskill_limit_pct: number;
  };
  executive_summary: {
    optical_throughput_mbps: number;
    ppm_order: number;
    photon_efficiency: number;
    pointing_jitter_nrad: number;
    strehl_ratio: number;
    qber_pct: number;
    secure_key_rate_kbps: number;
    security_verdict: string;
  };
}

export default function OpticalQkdStudio({ isOpen, onClose, apiBase }: OpticalQkdStudioProps) {
  const [activePreset, setActivePreset] = useState<string>("ISRO_LEO_GROUND_QKD");
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [result, setResult] = useState<QkdSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"visualizer" | "link_budget" | "qkd_security" | "fpa_pointing">("visualizer");
  const [eveSimulated, setEveSimulated] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;

    fetch(`${apiBase}/api/optical-qkd/presets`)
      .then((res) => (res.ok ? res.json() : {}))
      .then((data: Record<string, any>) => {
        setPresets(data);
        if (data && Object.keys(data).length > 0 && !data[activePreset]) {
          setActivePreset(Object.keys(data)[0]);
        }
      })
      .catch(() => {});

    runSimulation(activePreset, eveSimulated);
  }, [isOpen, activePreset]);

  const runSimulation = (presetId: string, eveOverride?: boolean) => {
    setLoading(true);
    const body: any = { mission_id: presetId };
    if (eveOverride !== undefined) {
      body.custom_params = { eve_present: eveOverride };
    }

    fetch(`${apiBase}/api/optical-qkd/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((res) => {
        if (!res.ok) throw new Error("Simulation failed");
        return res.json();
      })
      .then((data: QkdSimulationResult) => {
        setResult(data);
        setEveSimulated(data.quantum_key_distribution.eve_detected);
        setLoading(false);
      })
      .catch((err) => {
        console.error("QKD Simulation error:", err);
        setLoading(false);
      });
  };

  if (!isOpen) return null;

  const qkd = result?.quantum_key_distribution;
  const link = result?.optical_link_budget;
  const fsm = result?.fine_pointing;
  const ao = result?.adaptive_optics;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(15, 23, 42, 0.65)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1280px",
          height: "92vh",
          background: "#ffffff",
          borderRadius: "14px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          border: "1px solid #e2e8f0",
          fontFamily: "var(--font-sans, system-ui, sans-serif)",
          color: "#0f172a",
        }}
      >
        {/* Header Bar */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#f8fafc",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(2, 132, 199, 0.3)",
              }}
            >
              <Radio size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Autonomous Deep Space Optical Comms &amp; Quantum Key Distribution
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#0284c7",
                    color: "#ffffff",
                  }}
                >
                  STAGE 25 SOVEREIGN
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                Sub-nanoradian FSM pointing • PPM-256 gigabit link • Decoy-State BB84 QKD • Kolmogorov Strehl AO
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Mission Selector */}
            <select
              value={activePreset}
              onChange={(e) => {
                setActivePreset(e.target.value);
                runSimulation(e.target.value);
              }}
              style={{
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid #cbd5e1",
                background: "#ffffff",
                fontSize: "0.82rem",
                fontWeight: 600,
                color: "#0f172a",
                cursor: "pointer",
                outline: "none",
              }}
            >
              <option value="ISRO_LEO_GROUND_QKD">ISRO LEO-to-Ground QKD (550 km)</option>
              <option value="LUNAR_GATEWAY_DSOC">Chandrayaan-LupEx Lunar Gateway DSOC (384,400 km)</option>
              <option value="MARS_ORBITER_LASER">MOM-3 Mars Deep Space Laser (0.52 AU)</option>
              <option value="SECURE_INTERSATELLITE_QKD">Intersatellite Constellation (Active Eve Intercept)</option>
            </select>

            {/* Run Button */}
            <button
              onClick={() => runSimulation(activePreset, eveSimulated)}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#0284c7",
                color: "#ffffff",
                fontSize: "0.82rem",
                fontWeight: 600,
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Simulating..." : "Recalibrate Link"}
            </button>

            <button
              onClick={onClose}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                background: "#ffffff",
                fontSize: "0.85rem",
                cursor: "pointer",
                color: "#64748b",
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Security Alert Banner */}
        {qkd && (
          <div
            style={{
              padding: "10px 24px",
              background: qkd.eve_detected ? "#fef2f2" : "#f0fdf4",
              borderBottom: `1px solid ${qkd.eve_detected ? "#fecaca" : "#bbf7d0"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {qkd.eve_detected ? (
                <ShieldAlert size={18} color="#dc2626" />
              ) : (
                <ShieldCheck size={18} color="#16a34a" />
              )}
              <span
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: qkd.eve_detected ? "#991b1b" : "#166534",
                }}
              >
                {qkd.eve_detected
                  ? `SECURITY ALERT: Photon Number Splitting (PNS) Eavesdropper Detected! QBER = ${qkd.qber_pct.toFixed(2)}% > 11% Shor-Preskill Bound`
                  : `QUANTUM SECURITY CONFIRMED: Decoy-State BB84 Sifted Key Channel Secure (QBER = ${qkd.qber_pct.toFixed(2)}% < 11.0%)`}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: "#475569", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={eveSimulated}
                  onChange={(e) => {
                    setEveSimulated(e.target.checked);
                    runSimulation(activePreset, e.target.checked);
                  }}
                />
                Simulate Eve Intercept-Resend Attack
              </label>

              <span
                style={{
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: qkd.eve_detected ? "#dc2626" : "#16a34a",
                  color: "#ffffff",
                }}
              >
                {qkd.security_status}
              </span>
            </div>
          </div>
        )}

        {/* Telemetry KPI Strip */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: "12px",
            padding: "16px 24px",
            background: "#ffffff",
            borderBottom: "1px solid #e2e8f0",
          }}
        >
          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Throughput (DSOC)</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0284c7", marginTop: "2px" }}>
              {link ? link.data_rate_mbps.toFixed(2) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>Mbps</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              PPM-{link?.ppm_order || "--"} ({link?.bits_per_symbol || "--"} bits/symbol)
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Quantum Bit Error (QBER)</div>
            <div
              style={{
                fontSize: "1.35rem",
                fontWeight: 800,
                color: (qkd?.qber_pct || 0) > 11.0 ? "#dc2626" : "#16a34a",
                marginTop: "2px",
              }}
            >
              {qkd ? qkd.qber_pct.toFixed(2) : "--"} <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>%</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Threshold &lt; 11.0% (Shor-Preskill)
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Secure Key Rate (GLLP)</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0f172a", marginTop: "2px" }}>
              {qkd ? qkd.secure_key_rate_kbps.toFixed(2) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>kbps</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Sifted: {qkd ? (qkd.sifted_key_rate_bps / 1000).toFixed(1) : "--"} kbps
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Pointing Jitter (FSM)</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#7c3aed", marginTop: "2px" }}>
              {fsm ? fsm.fsm_rms_residual_jitter_nrad.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>nrad</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Rejection: -{fsm ? fsm.jitter_suppression_factor_db.toFixed(1) : "--"} dB
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Strehl Ratio (AO)</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#059669", marginTop: "2px" }}>
              {ao ? (ao.strehl_ratio * 100).toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>%</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Fried r₀: {result?.atmospheric_turbulence.fried_parameter_r0_cm.toFixed(1) || "--"} cm
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", background: "#f8fafc", padding: "0 24px" }}>
          {[
            { id: "visualizer", label: "Optical Link & Quantum Beam View", icon: <Eye size={14} /> },
            { id: "link_budget", label: "DSOC Link Budget & PPM Modulation", icon: <Wifi size={14} /> },
            { id: "qkd_security", label: "BB84 Decoy-State Cryptanalysis", icon: <Lock size={14} /> },
            { id: "fpa_pointing", label: "FSM Sub-Nanoradian Stabilizer", icon: <Sliders size={14} /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "12px 18px",
                fontSize: "0.82rem",
                fontWeight: activeTab === tab.id ? 700 : 500,
                color: activeTab === tab.id ? "#0284c7" : "#64748b",
                borderBottom: activeTab === tab.id ? "2px solid #0284c7" : "2px solid transparent",
                background: "transparent",
                borderTop: "none",
                borderLeft: "none",
                borderRight: "none",
                cursor: "pointer",
              }}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px", background: "#f8fafc" }}>
          {activeTab === "visualizer" && (
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px" }}>
              {/* SVG Link Schematic */}
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
                    Optical Beam Propagation &amp; Adaptive Optics Wavefront
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Range: {result?.configuration.distance_km.toLocaleString()} km • λ: 1550 nm
                  </span>
                </div>

                <div
                  style={{
                    width: "100%",
                    height: "320px",
                    background: "#090d16",
                    borderRadius: "8px",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  <svg width="100%" height="100%" viewBox="0 0 700 320">
                    <defs>
                      <linearGradient id="laserBeamGrad" x1="0%" y1="50%" x2="100%" y2="50%">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.95" />
                        <stop offset="60%" stopColor="#0284c7" stopOpacity="0.7" />
                        <stop offset="100%" stopColor="#0369a1" stopOpacity="0.85" />
                      </linearGradient>
                      <radialGradient id="txGlow" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity="1" />
                        <stop offset="100%" stopColor="#0284c7" stopOpacity="0" />
                      </radialGradient>
                    </defs>

                    {/* Background star dots */}
                    {[...Array(25)].map((_, i) => (
                      <circle
                        key={i}
                        cx={(i * 37) % 680 + 10}
                        cy={(i * 59) % 300 + 10}
                        r="1.2"
                        fill="#ffffff"
                        opacity="0.35"
                      />
                    ))}

                    {/* Spacecraft / Optical Terminal TX */}
                    <g transform="translate(60, 160)">
                      <rect x="-35" y="-18" width="50" height="36" rx="4" fill="#334155" stroke="#94a3b8" strokeWidth="1.5" />
                      <line x1="-35" y1="-28" x2="-35" y2="28" stroke="#64748b" strokeWidth="2" />
                      <rect x="-48" y="-28" width="12" height="56" rx="2" fill="#0284c7" />
                      {/* Laser aperture */}
                      <polygon points="15,-14 25,-22 25,22 15,14" fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
                      <circle cx="22" cy="0" r="14" fill="url(#txGlow)" />
                      <text x="-40" y="-36" fill="#94a3b8" fontSize="10" fontWeight="bold">TX Terminal (Space)</text>
                    </g>

                    {/* Laser Beam Expansion Cone */}
                    <polygon
                      points="85,160 580,90 580,230"
                      fill="url(#laserBeamGrad)"
                      opacity="0.3"
                    />
                    <line x1="85" y1="160" x2="580" y2="160" stroke="#38bdf8" strokeWidth="2" strokeDasharray="6 3" />

                    {/* Atmospheric Turbulence Slant Layer */}
                    <rect x="420" y="40" width="80" height="240" fill="rgba(14, 165, 233, 0.08)" stroke="#38bdf8" strokeWidth="1" strokeDasharray="3 3" />
                    <text x="424" y="58" fill="#38bdf8" fontSize="9" fontWeight="bold">Turbulence (Cn²)</text>
                    <text x="424" y="72" fill="#94a3b8" fontSize="8">r₀: {result?.atmospheric_turbulence.fried_parameter_r0_cm.toFixed(1)} cm</text>

                    {/* Ground Optical Station RX */}
                    <g transform="translate(600, 160)">
                      {/* Telescope dome */}
                      <path d="M-15,-60 A45,45 0 0,1 45,-60 L50,60 L-15,60 Z" fill="#1e293b" stroke="#64748b" strokeWidth="1.5" />
                      <rect x="-10" y="-35" width="20" height="70" rx="3" fill="#38bdf8" opacity="0.6" />
                      {/* Deformable mirror */}
                      <line x1="15" y1="-28" x2="15" y2="28" stroke="#f59e0b" strokeWidth="3" />
                      <text x="-25" y="80" fill="#94a3b8" fontSize="10" fontWeight="bold">Ground OGS (AO &amp; SNSPD)</text>
                      <text x="-15" y="94" fill="#10b981" fontSize="9">Strehl: {(result?.adaptive_optics.strehl_ratio ? result.adaptive_optics.strehl_ratio * 100 : 0).toFixed(1)}%</text>
                    </g>

                    {/* Eve eavesdropper if active */}
                    {eveSimulated && (
                      <g transform="translate(320, 100)">
                        <circle cx="0" cy="0" r="16" fill="#dc2626" opacity="0.25" />
                        <circle cx="0" cy="0" r="8" fill="#dc2626" />
                        <line x1="0" y1="8" x2="0" y2="50" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3 2" />
                        <text x="-35" y="-12" fill="#ef4444" fontSize="10" fontWeight="bold">Eve (PNS Beam Splitter)</text>
                      </g>
                    )}
                  </svg>
                </div>
              </div>

              {/* Status & Control Deck */}
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f172a", marginBottom: "10px" }}>
                    Mission Configuration
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.78rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>Target Regime:</span>
                      <span style={{ fontWeight: 600 }}>{result?.mission_name}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>Link Distance:</span>
                      <span style={{ fontWeight: 600 }}>{result?.configuration.distance_km.toLocaleString()} km</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>Laser Wavelength:</span>
                      <span style={{ fontWeight: 600 }}>{result?.configuration.wavelength_nm} nm (SWIR)</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>TX Optical Power:</span>
                      <span style={{ fontWeight: 600 }}>{result?.configuration.tx_power_w} W</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>TX / RX Apertures:</span>
                      <span style={{ fontWeight: 600 }}>
                        {result?.configuration.tx_aperture_m} m / {result?.configuration.rx_aperture_m} m
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>AO Deformable Mirror:</span>
                      <span style={{ fontWeight: 600 }}>{result?.configuration.ao_actuators} Actuators</span>
                    </div>
                  </div>
                </div>

                <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f172a", marginBottom: "10px" }}>
                    Pulse Position Modulation (PPM)
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                    {[16, 64, 256].map((m) => (
                      <span
                        key={m}
                        style={{
                          padding: "4px 8px",
                          borderRadius: "4px",
                          fontSize: "0.74rem",
                          fontWeight: link?.ppm_order === m ? 700 : 500,
                          background: link?.ppm_order === m ? "#0284c7" : "#f1f5f9",
                          color: link?.ppm_order === m ? "#ffffff" : "#64748b",
                        }}
                      >
                        PPM-{m}
                      </span>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
                    Photon Efficiency: <strong>{link?.photon_efficiency_bits_per_photon.toFixed(2)}</strong> bits/photon.
                    Free-space path loss: <strong>{link?.free_space_path_loss_db.toFixed(1)} dB</strong>.
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "link_budget" && (
            <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 16px 0", color: "#0f172a" }}>
                Deep Space Optical Link Budget &amp; PPM Photon Accounting
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                <thead>
                  <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                    <th style={{ padding: "10px 12px" }}>Parameter</th>
                    <th style={{ padding: "10px 12px" }}>Symbol</th>
                    <th style={{ padding: "10px 12px" }}>Calculated Value</th>
                    <th style={{ padding: "10px 12px" }}>Physical Units</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: "Laser Center Wavelength", symbol: "λ", value: result?.configuration.wavelength_nm, units: "nm" },
                    { label: "Transmitter Beam Divergence (Airy)", symbol: "θ_div", value: link?.tx_beam_divergence_urad.toFixed(2), units: "µrad" },
                    { label: "Transmitter Optical Gain", symbol: "G_tx", value: link?.tx_gain_dbi.toFixed(1), units: "dBi" },
                    { label: "Receiver Telescope Gain", symbol: "G_rx", value: link?.rx_gain_dbi.toFixed(1), units: "dBi" },
                    { label: "Free Space Path Loss", symbol: "FSPL", value: link?.free_space_path_loss_db.toFixed(1), units: "dB" },
                    { label: "Pointing Jitter Loss", symbol: "L_point", value: link?.pointing_loss_db.toFixed(3), units: "dB" },
                    { label: "Atmospheric Scintillation Index", symbol: "σ_I²", value: result?.atmospheric_turbulence.scintillation_index.toFixed(3), units: "dimensionless" },
                    { label: "Deformable Mirror Strehl Ratio", symbol: "S", value: (ao?.strehl_ratio ? ao.strehl_ratio * 100 : 0).toFixed(2), units: "%" },
                    { label: "Received Optical Power", symbol: "P_rx", value: link?.received_power_dbm.toFixed(2), units: "dBm" },
                    { label: "Received Optical Power (Linear)", symbol: "P_rx", value: link?.received_power_nw.toFixed(4), units: "nW" },
                    { label: "Arriving Photon Flux", symbol: "Φ_p", value: link?.photons_per_second.toExponential(3), units: "photons / sec" },
                    { label: "PPM Modulation Order", symbol: "M", value: link?.ppm_order, units: "slots/symbol" },
                    { label: "Effective Channel Bitrate", symbol: "R_b", value: link?.data_rate_mbps.toFixed(2), units: "Mbps" },
                    { label: "Photon Efficiency", symbol: "η_ph", value: link?.photon_efficiency_bits_per_photon.toFixed(2), units: "bits / photon" },
                  ].map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "8px 12px", fontWeight: 600 }}>{row.label}</td>
                      <td style={{ padding: "8px 12px", color: "#64748b", fontFamily: "monospace" }}>{row.symbol}</td>
                      <td style={{ padding: "8px 12px", fontWeight: 700, color: "#0284c7" }}>{row.value}</td>
                      <td style={{ padding: "8px 12px", color: "#64748b" }}>{row.units}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "qkd_security" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                  BB84 Decoy-State Protocol Parameters
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.8rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Quantum Channel Loss:</span>
                    <span style={{ fontWeight: 700 }}>{qkd?.channel_loss_db.toFixed(1)} dB</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Single-Photon Gain Q₁:</span>
                    <span style={{ fontWeight: 700 }}>{qkd?.single_photon_gain_q1.toExponential(3)}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Signal State Gain Q_μ:</span>
                    <span style={{ fontWeight: 700 }}>{qkd?.signal_gain_q_mu.toExponential(3)}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Decoy State Gain Q_ν:</span>
                    <span style={{ fontWeight: 700 }}>{qkd?.decoy_gain_q_nu.toExponential(3)}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Single-Photon Error e₁:</span>
                    <span style={{ fontWeight: 700 }}>{(qkd ? qkd.single_photon_error_rate_e1 * 100 : 0).toFixed(2)}%</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Total Quantum Bit Error (QBER):</span>
                    <span style={{ fontWeight: 700, color: (qkd?.qber_pct || 0) > 11 ? "#dc2626" : "#16a34a" }}>
                      {qkd?.qber_pct.toFixed(2)}%
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Shor-Preskill Security Bound:</span>
                    <span style={{ fontWeight: 700, color: "#64748b" }}>11.00%</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>GLLP Secure Key Rate:</span>
                    <span style={{ fontWeight: 800, color: "#0284c7" }}>{qkd?.secure_key_rate_kbps.toFixed(2)} kbps</span>
                  </div>
                </div>
              </div>

              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                  Eavesdropper Intercept Proof
                </h3>
                <p style={{ fontSize: "0.78rem", color: "#64748b", lineHeight: "1.5" }}>
                  The 3-state decoy method allows precise extraction of the single-photon gain <em>Q₁</em> and error rate <em>e₁</em>, defeating Photon Number Splitting (PNS) attacks:
                </p>
                <div
                  style={{
                    background: "#090d16",
                    color: "#38bdf8",
                    padding: "12px",
                    borderRadius: "6px",
                    fontFamily: "monospace",
                    fontSize: "0.74rem",
                    marginBottom: "12px",
                  }}
                >
                  R_secure ≥ q · [ Q₁ · (1 - h₂(e₁)) - f_EC · Q_μ · h₂(E_μ) ]
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div
                    style={{
                      width: "12px",
                      height: "12px",
                      borderRadius: "50%",
                      background: qkd?.eve_detected ? "#dc2626" : "#16a34a",
                    }}
                  />
                  <span style={{ fontSize: "0.8rem", fontWeight: 700, color: qkd?.eve_detected ? "#dc2626" : "#16a34a" }}>
                    {qkd?.eve_detected
                      ? "ATTACK ACTIVE: QBER exceeds threshold. Key discarded."
                      : "LINK SECURE: No eavesdropping present. Quantum pad verified."}
                  </span>
                </div>
              </div>
            </div>
          )}

          {activeTab === "fpa_pointing" && (
            <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                Fast Steering Mirror (FSM) Closed-Loop Vibration Suppression
              </h3>
              <p style={{ fontSize: "0.78rem", color: "#64748b", marginBottom: "16px" }}>
                Spacecraft reaction wheel harmonics (45 Hz, 120 Hz, 310 Hz) cause raw pointing jitter of {fsm?.raw_jitter_urad} µrad. The 1.4 kHz high-bandwidth FSM controller suppresses jitter down to {fsm?.fsm_rms_residual_jitter_nrad.toFixed(1)} nanoradians (-{fsm?.jitter_suppression_factor_db.toFixed(1)} dB).
              </p>

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                <thead>
                  <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px" }}>Sample Step</th>
                    <th style={{ padding: "8px 12px" }}>Raw Disturbance Jitter (nrad)</th>
                    <th style={{ padding: "8px 12px" }}>Residual Pointing Jitter (nrad)</th>
                    <th style={{ padding: "8px 12px" }}>Instantaneous Suppression</th>
                  </tr>
                </thead>
                <tbody>
                  {fsm?.sample_time_series.map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "6px 12px", fontFamily: "monospace" }}>#{row.step}</td>
                      <td style={{ padding: "6px 12px", color: "#dc2626" }}>{row.raw_jitter_nrad.toFixed(1)} nrad</td>
                      <td style={{ padding: "6px 12px", fontWeight: 700, color: "#16a34a" }}>{row.residual_nrad.toFixed(1)} nrad</td>
                      <td style={{ padding: "6px 12px", color: "#64748b" }}>
                        {(20 * Math.log10(Math.max(1, Math.abs(row.raw_jitter_nrad) / Math.max(0.1, Math.abs(row.residual_nrad))))).toFixed(1)} dB
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
