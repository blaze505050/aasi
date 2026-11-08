"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Radio,
  Eye,
  RefreshCw,
  Compass,
  ArrowRight,
  ChevronRight,
  Sliders,
  Waves,
  Sparkles,
} from "lucide-react";

interface MetamaterialRcsStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface RcsSimulationResult {
  model_name: string;
  radar_band: string;
  frequency_ghz: number;
  wavelength_cm: number;
  metamaterial_ram_enabled: boolean;
  ram_thickness_mm: number;
  frontal_rcs_m2: number;
  frontal_rcs_dbsm: number;
  mean_rcs_m2: number;
  mean_rcs_dbsm: number;
  peak_rcs_dbsm: number;
  stealth_classification: string;
  polar_rcs_signature: Array<{
    azimuth_deg: number;
    rcs_m2: number;
    rcs_dbsm: number;
  }>;
  frequency_sweep: Array<{
    frequency_ghz: number;
    absorption_pct: number;
    rcs_m2: number;
    rcs_dbsm: number;
    ram_attenuation_db: number;
  }>;
  executive_summary: {
    airframe: string;
    frontal_rcs_dbsm: number;
    frontal_rcs_cm2: number;
    stealth_category: string;
    metamaterial_reduction_db: number;
    x_band_peak_absorption_pct: number;
  };
}

export default function MetamaterialRcsStudio({ isOpen, onClose, apiBase }: MetamaterialRcsStudioProps) {
  const [activePreset, setActivePreset] = useState<string>("AMCA_5TH_GEN_STEALTH");
  const [radarBand, setRadarBand] = useState<string>("X_BAND");
  const [freqGhz, setFreqGhz] = useState<number>(10.0);
  const [enableRam, setEnableRam] = useState<boolean>(true);
  const [ramThickness, setRamThickness] = useState<number>(2.8);
  const [result, setResult] = useState<RcsSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"polar_plot" | "frequency_sweep" | "metamaterial_physics">("polar_plot");

  useEffect(() => {
    if (!isOpen) return;
    runSimulation();
  }, [isOpen, activePreset, radarBand, freqGhz, enableRam, ramThickness]);

  const handleBandChange = (band: string) => {
    setRadarBand(band);
    if (band === "S_BAND") setFreqGhz(3.0);
    else if (band === "C_BAND") setFreqGhz(6.0);
    else if (band === "X_BAND") setFreqGhz(10.0);
    else if (band === "KU_BAND") setFreqGhz(15.0);
  };

  const runSimulation = () => {
    setLoading(true);
    fetch(`${apiBase}/api/rcs/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_name: activePreset,
        radar_band: radarBand,
        frequency_ghz: freqGhz,
        enable_metamaterial_ram: enableRam,
        ram_thickness_mm: ramThickness,
      }),
    })
      .then((res) => {
        if (!res.ok) throw new Error("RCS simulation failed");
        return res.json();
      })
      .then((data: RcsSimulationResult) => {
        setResult(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("RCS Simulation error:", err);
        setLoading(false);
      });
  };

  if (!isOpen) return null;

  const exec = result?.executive_summary;
  const isVLO = (result?.frontal_rcs_dbsm || 0) < -30.0;

  // Polar plot points generator
  // Maps dBsm [-50, +20] to radius [20, 140]
  const polarPoints = (result?.polar_rcs_signature || []).map((pt) => {
    const angleRad = (pt.azimuth_deg - 90) * (Math.PI / 180);
    const clampedDb = Math.max(-50, Math.min(20, pt.rcs_dbsm));
    const normalizedRadius = ((clampedDb - (-50)) / 70) * 120 + 20;
    const x = normalizedRadius * Math.cos(angleRad);
    const y = normalizedRadius * Math.sin(angleRad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

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
                background: "linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(79, 70, 229, 0.3)",
              }}
            >
              <Waves size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Electromagnetic Metamaterial RCS &amp; Inverse Stealth Synthesizer
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#4f46e5",
                    color: "#ffffff",
                  }}
                >
                  STAGE 28 SOVEREIGN
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                Physical Optics (PO) • Salisbury Metasurface Absorption • 360° Polar Radar Cross Section • AMCA VLO
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Airframe Preset Selector */}
            <select
              value={activePreset}
              onChange={(e) => setActivePreset(e.target.value)}
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
              <option value="AMCA_5TH_GEN_STEALTH">Indian AMCA 5th/6th Gen Stealth</option>
              <option value="HYPERSONIC_STRIKE_HGV">Hypersonic HGV Diamond Facet</option>
              <option value="CONVENTIONAL_FIGHTER_BASELINE">Conventional 4th Gen Baseline (Non-Stealth)</option>
            </select>

            {/* Run Button */}
            <button
              onClick={runSimulation}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#4f46e5",
                color: "#ffffff",
                fontSize: "0.82rem",
                fontWeight: 600,
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Synthesizing..." : "Compute RCS"}
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

        {/* Stealth Verdict Banner */}
        {exec && (
          <div
            style={{
              padding: "10px 24px",
              background: isVLO ? "#f0fdf4" : "#fef2f2",
              borderBottom: `1px solid ${isVLO ? "#bbf7d0" : "#fecaca"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {isVLO ? <ShieldCheck size={18} color="#16a34a" /> : <ShieldAlert size={18} color="#dc2626" />}
              <span
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: isVLO ? "#166534" : "#991b1b",
                }}
              >
                {isVLO
                  ? `VERY LOW OBSERVABLE (VLO) CONFIRMED: Frontal RCS = ${exec.frontal_rcs_dbsm.toFixed(1)} dBsm (${exec.frontal_rcs_cm2.toFixed(2)} cm²) - Metamaterial Attenuation: -${exec.metamaterial_reduction_db} dB`
                  : `CONVENTIONAL RADAR SIGNATURE: Frontal RCS = ${exec.frontal_rcs_dbsm.toFixed(1)} dBsm (${(result?.frontal_rcs_m2 || 0).toFixed(2)} m²) - High specular backscatter detected.`}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: "#475569", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={enableRam}
                  onChange={(e) => setEnableRam(e.target.checked)}
                />
                Metamaterial RAM Cloak
              </label>

              <span
                style={{
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: isVLO ? "#16a34a" : "#4f46e5",
                  color: "#ffffff",
                }}
              >
                {result?.stealth_classification}
              </span>
            </div>
          </div>
        )}

        {/* Telemetry Metric Tiles */}
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
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Frontal Nose RCS (0°)</div>
            <div
              style={{
                fontSize: "1.35rem",
                fontWeight: 800,
                color: isVLO ? "#16a34a" : "#dc2626",
                marginTop: "2px",
              }}
            >
              {result ? result.frontal_rcs_dbsm.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>dBsm</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Area: {result ? (result.frontal_rcs_m2 * 10000).toFixed(2) : "--"} cm²
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Mean 360° RCS</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0f172a", marginTop: "2px" }}>
              {result ? result.mean_rcs_dbsm.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>dBsm</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Azimuth integrated average
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>RAM Resonant Absorption</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#4f46e5", marginTop: "2px" }}>
              {exec ? exec.x_band_peak_absorption_pct.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>%</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Salisbury Screen {ramThickness}mm
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Radar Frequency Band</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0284c7", marginTop: "2px" }}>
              {freqGhz.toFixed(1)}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>GHz</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              {radarBand} (λ = {result?.wavelength_cm} cm)
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Peak Specular Lobe</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#7c3aed", marginTop: "2px" }}>
              {result ? result.peak_rcs_dbsm.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>dBsm</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Deflected to 48° / 132° Azimuth
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", background: "#f8fafc", padding: "0 24px" }}>
          {[
            { id: "polar_plot", label: "360° Polar RCS Radiation Pattern", icon: <Compass size={14} /> },
            { id: "frequency_sweep", label: "S/C/X/Ku Multi-Band Frequency Sweep", icon: <Activity size={14} /> },
            { id: "metamaterial_physics", label: "Salisbury Metasurface Impedance Match", icon: <Layers size={14} /> },
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
                color: activeTab === tab.id ? "#4f46e5" : "#64748b",
                borderBottom: activeTab === tab.id ? "2px solid #4f46e5" : "2px solid transparent",
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
          {activeTab === "polar_plot" && (
            <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "20px" }}>
              {/* Polar Plot Canvas */}
              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
                    360° Monostatic Radar Cross Section Pattern (dBsm)
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Scale: -50 dBsm (Center) to +20 dBsm (Outer Ring)
                  </span>
                </div>

                <div
                  style={{
                    width: "100%",
                    height: "340px",
                    background: "#090d16",
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                  }}
                >
                  <svg width="340" height="340" viewBox="-170 -170 340 340">
                    {/* Concentric dBsm rings */}
                    {[
                      { r: 20, label: "-50" },
                      { r: 54, label: "-30" },
                      { r: 88, label: "-10" },
                      { r: 122, label: "+10" },
                      { r: 140, label: "+20" },
                    ].map((ring) => (
                      <g key={ring.label}>
                        <circle cx="0" cy="0" r={ring.r} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1" strokeDasharray="3 3" />
                        <text x="4" y={-ring.r + 10} fill="#64748b" fontSize="7" fontFamily="monospace">{ring.label} dBsm</text>
                      </g>
                    ))}

                    {/* Radial Angular Grid Lines */}
                    {[0, 30, 48, 60, 90, 120, 132, 150, 180, 210, 228, 240, 270, 300, 312, 330].map((deg) => {
                      const rad = (deg - 90) * (Math.PI / 180);
                      const x2 = 145 * Math.cos(rad);
                      const y2 = 145 * Math.sin(rad);
                      const isSpecularAngle = [48, 132, 228, 312].includes(deg);
                      return (
                        <g key={deg}>
                          <line
                            x1="0"
                            y1="0"
                            x2={x2}
                            y2={y2}
                            stroke={isSpecularAngle ? "rgba(239, 68, 68, 0.35)" : "rgba(255, 255, 255, 0.08)"}
                            strokeWidth={isSpecularAngle ? "1.5" : "0.8"}
                          />
                          <text
                            x={155 * Math.cos(rad)}
                            y={155 * Math.sin(rad) + 3}
                            fill={isSpecularAngle ? "#ef4444" : "#94a3b8"}
                            fontSize="7"
                            textAnchor="middle"
                            fontFamily="monospace"
                          >
                            {deg}°
                          </text>
                        </g>
                      );
                    })}

                    {/* Airframe Central Silhouette (AMCA Shape) */}
                    <g transform="scale(0.35)">
                      <polygon
                        points="0,-45 28,-10 40,25 15,20 0,35 -15,20 -40,25 -28,-10"
                        fill="rgba(79, 70, 229, 0.25)"
                        stroke="#818cf8"
                        strokeWidth="1.5"
                      />
                    </g>

                    {/* Polar RCS Radiation Curve */}
                    <polygon
                      points={polarPoints}
                      fill="rgba(79, 70, 229, 0.3)"
                      stroke="#4f46e5"
                      strokeWidth="2"
                    />
                  </svg>
                </div>
              </div>

              {/* Band & Coating Control Panel */}
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f172a", marginBottom: "12px" }}>
                    Radar Illumination Parameters
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.78rem" }}>
                    <div>
                      <label style={{ color: "#64748b", display: "block", marginBottom: "4px" }}>Frequency Band:</label>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "6px" }}>
                        {["S_BAND", "C_BAND", "X_BAND", "KU_BAND"].map((b) => (
                          <button
                            key={b}
                            onClick={() => handleBandChange(b)}
                            style={{
                              padding: "6px",
                              borderRadius: "4px",
                              fontSize: "0.72rem",
                              fontWeight: radarBand === b ? 700 : 500,
                              background: radarBand === b ? "#4f46e5" : "#f1f5f9",
                              color: radarBand === b ? "#ffffff" : "#475569",
                              border: "none",
                              cursor: "pointer",
                            }}
                          >
                            {b.replace("_BAND", "")}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ color: "#64748b" }}>Exact Frequency:</span>
                      <strong>{freqGhz.toFixed(1)} GHz</strong>
                    </div>

                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                        <span style={{ color: "#64748b" }}>RAM Spacer Thickness:</span>
                        <strong>{ramThickness.toFixed(1)} mm</strong>
                      </div>
                      <input
                        type="range"
                        min="1.0"
                        max="8.0"
                        step="0.2"
                        value={ramThickness}
                        onChange={(e) => setRamThickness(parseFloat(e.target.value))}
                        style={{ width: "100%", accentColor: "#4f46e5" }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f172a", marginBottom: "8px" }}>
                    Stealth Faceting Law
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
                    Edge alignment restricts specular flash lobes to narrow spike angles (48° and 132° azimuth), leaving the critical ±30° frontal nose cone in a deep electromagnetic shadow with &lt; -38 dBsm cross section.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "frequency_sweep" && (
            <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 16px 0", color: "#0f172a" }}>
                Multi-Band RCS &amp; Metamaterial Attenuation Profile (S, C, X, Ku Bands)
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                <thead>
                  <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px" }}>Frequency (GHz)</th>
                    <th style={{ padding: "8px 12px" }}>Radar Band</th>
                    <th style={{ padding: "8px 12px" }}>Absorption Efficiency (%)</th>
                    <th style={{ padding: "8px 12px" }}>RAM Attenuation (dB)</th>
                    <th style={{ padding: "8px 12px" }}>Frontal RCS (dBsm)</th>
                    <th style={{ padding: "8px 12px" }}>Equivalent Area (cm²)</th>
                  </tr>
                </thead>
                <tbody>
                  {result?.frequency_sweep.map((row, idx) => {
                    const bandLabel = row.frequency_ghz < 4.0 ? "S-Band" : (row.frequency_ghz < 8.0 ? "C-Band" : (row.frequency_ghz < 12.0 ? "X-Band" : "Ku-Band"));
                    return (
                      <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                        <td style={{ padding: "6px 12px", fontFamily: "monospace", fontWeight: 700 }}>{row.frequency_ghz.toFixed(1)} GHz</td>
                        <td style={{ padding: "6px 12px", color: "#64748b" }}>{bandLabel}</td>
                        <td style={{ padding: "6px 12px", color: row.absorption_pct > 80 ? "#16a34a" : "#0f172a", fontWeight: 600 }}>
                          {row.absorption_pct.toFixed(1)}%
                        </td>
                        <td style={{ padding: "6px 12px", color: "#4f46e5", fontWeight: 700 }}>
                          {row.ram_attenuation_db.toFixed(1)} dB
                        </td>
                        <td style={{ padding: "6px 12px", fontWeight: 700, color: row.rcs_dbsm < -30 ? "#16a34a" : "#dc2626" }}>
                          {row.rcs_dbsm.toFixed(2)} dBsm
                        </td>
                        <td style={{ padding: "6px 12px", color: "#64748b" }}>{(row.rcs_m2 * 10000).toFixed(2)} cm²</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "metamaterial_physics" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                  Salisbury Screen &amp; Dallenbach Layer Equations
                </h3>
                <div
                  style={{
                    background: "#090d16",
                    color: "#818cf8",
                    padding: "12px",
                    borderRadius: "6px",
                    fontFamily: "monospace",
                    fontSize: "0.74rem",
                    marginBottom: "12px",
                  }}
                >
                  Z_in = j · η_d · tan(k_spacer · d · cos θ_t)<br />
                  Z_total = (R_sheet || Z_in)<br />
                  Γ = (Z_total - η₀) / (Z_total + η₀)
                </div>
                <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
                  When the spacer thickness equals a quarter wavelength (<em>d ≈ λ / (4√ε_r)</em>), the short-circuit impedance of the backing metal transforms into an open circuit at the resistive sheet, producing zero net reflection (|Γ| → 0) and 99%+ absorption.
                </p>
              </div>

              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                  Generalized Snell's Law Metasurface Steering
                </h3>
                <div
                  style={{
                    background: "#090d16",
                    color: "#34d399",
                    padding: "12px",
                    borderRadius: "6px",
                    fontFamily: "monospace",
                    fontSize: "0.74rem",
                    marginBottom: "12px",
                  }}
                >
                  sin θ_r - sin θ_i = (λ / 2π) · (dΦ / dx)
                </div>
                <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
                  A phase-gradient metasurface imparts a spatial phase gradient <em>dΦ/dx</em>, deflecting anomalous reflected waves completely away from the monostatic illumination vector, neutralizing high-angle secondary edge diffraction.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
