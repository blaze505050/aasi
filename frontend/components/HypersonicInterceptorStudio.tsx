"use client";

import React, { useState, useEffect } from "react";
import {
  Crosshair,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Activity,
  Flame,
  Radio,
  Eye,
  RefreshCw,
  Compass,
  ArrowRight,
  ChevronRight,
  Wind,
  Sliders,
  Target,
  Rocket,
} from "lucide-react";

interface HypersonicInterceptorStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface InterceptorSimulationResult {
  mission_id: string;
  guidance_law: string;
  target_evasion_maneuver: string;
  hit_to_kill_achieved: boolean;
  min_miss_distance_m: number;
  terminal_zem_m: number;
  peak_g_load: number;
  peak_stagnation_heat_flux_mw_m2: number;
  dacs_fuel_consumed_kg: number;
  time_series: Array<{
    time_s: number;
    slant_range_km: number;
    closing_speed_mps: number;
    closing_mach: number;
    t_go_s: number;
    zem_m: number;
    g_load: number;
    stagnation_heat_flux_mw: number;
    interceptor_alt_km: number;
    target_alt_km: number;
  }>;
  executive_summary: {
    engagement_outcome: string;
    miss_distance_cm: number;
    guidance_performance: string;
    peak_load_factor_g: number;
    peak_heat_flux_mw: number;
    dacs_assist_utilized: boolean;
  };
}

export default function HypersonicInterceptorStudio({ isOpen, onClose, apiBase }: HypersonicInterceptorStudioProps) {
  const [activePreset, setActivePreset] = useState<string>("GLIDE_PHASE_INTERCEPTOR");
  const [guidanceLaw, setGuidanceLaw] = useState<string>("DIFFERENTIAL_GAME_ZEM");
  const [targetEvasion, setTargetEvasion] = useState<string>("SINUSOIDAL_WEAVE");
  const [navRatio, setNavRatio] = useState<number>(4.2);
  const [enableDacs, setEnableDacs] = useState<boolean>(true);
  const [result, setResult] = useState<InterceptorSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"visualizer" | "telemetry_table" | "aerothermo">("visualizer");

  useEffect(() => {
    if (!isOpen) return;
    runSimulation();
  }, [isOpen, activePreset, guidanceLaw, targetEvasion, enableDacs]);

  const runSimulation = () => {
    setLoading(true);
    fetch(`${apiBase}/api/interceptor/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mission_id: activePreset,
        guidance_law: guidanceLaw,
        target_evasion: targetEvasion,
        nav_ratio: navRatio,
        enable_dacs_divert: enableDacs,
      }),
    })
      .then((res) => {
        if (!res.ok) throw new Error("Interceptor simulation failed");
        return res.json();
      })
      .then((data: InterceptorSimulationResult) => {
        setResult(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Interceptor Simulation error:", err);
        setLoading(false);
      });
  };

  if (!isOpen) return null;

  const exec = result?.executive_summary;
  const isHTK = result?.hit_to_kill_achieved;

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
                background: "linear-gradient(135deg, #e11d48 0%, #be123c 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(225, 29, 72, 0.3)",
              }}
            >
              <Crosshair size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Hypersonic Boost-Glide Interceptor Guidance Engine
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#e11d48",
                    color: "#ffffff",
                  }}
                >
                  STAGE 27 SOVEREIGN
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                Mach 8+ Hit-to-Kill • Zero Effort Miss (ZEM) Differential Games • Sutton-Graves Aerothermo • DACS Divert
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Engagement Scenario Selector */}
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
              <option value="GLIDE_PHASE_INTERCEPTOR">Glide Phase (GPI vs Mach 9.5 HGV at 38 km)</option>
              <option value="ENDOCRUIRSER_HACM">Endo-atmospheric (Mach 6.2 HACM at 22 km)</option>
              <option value="EXO_ORBITAL_FOBS">Exo-atmospheric (Mach 28 FOBS Re-entry at 85 km)</option>
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
                background: "#e11d48",
                color: "#ffffff",
                fontSize: "0.82rem",
                fontWeight: 600,
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Intercepting..." : "Simulate Interception"}
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

        {/* Engagement Outcome Banner */}
        {exec && (
          <div
            style={{
              padding: "10px 24px",
              background: isHTK ? "#f0fdf4" : "#fef2f2",
              borderBottom: `1px solid ${isHTK ? "#bbf7d0" : "#fecaca"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {isHTK ? <ShieldCheck size={18} color="#16a34a" /> : <ShieldAlert size={18} color="#dc2626" />}
              <span
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: isHTK ? "#166534" : "#991b1b",
                }}
              >
                {isHTK
                  ? `DIRECT KINETIC IMPACT CONFIRMED: Miss Distance = ${exec.miss_distance_cm.toFixed(1)} cm (< 65 cm Hit-To-Kill Criterion)`
                  : `PROXIMITY DETONATION: Miss Distance = ${exec.miss_distance_cm.toFixed(1)} cm (Target maneuvered outside direct body impact envelope)`}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <span style={{ fontSize: "0.76rem", color: "#64748b" }}>
                Guidance: <strong>{guidanceLaw}</strong>
              </span>
              <span
                style={{
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: isHTK ? "#16a34a" : "#e11d48",
                  color: "#ffffff",
                }}
              >
                {exec.engagement_outcome}
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
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Hit-to-Kill Miss Distance</div>
            <div
              style={{
                fontSize: "1.35rem",
                fontWeight: 800,
                color: isHTK ? "#16a34a" : "#e11d48",
                marginTop: "2px",
              }}
            >
              {exec ? exec.miss_distance_cm.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>cm</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              HTK Standard: &lt; 65.0 cm
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Peak Closing Speed</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0284c7", marginTop: "2px" }}>
              {result?.time_series[0]?.closing_speed_mps.toLocaleString() || "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>m/s</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Mach {result?.time_series[0]?.closing_mach || "--"} Combined
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Peak Structural G-Load</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#7c3aed", marginTop: "2px" }}>
              {result ? result.peak_g_load.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>g</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Structural Limit: 35.0 g
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Stagnation Heat Flux</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#f59e0b", marginTop: "2px" }}>
              {result ? result.peak_stagnation_heat_flux_mw_m2.toFixed(2) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>MW/m²</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Sutton-Graves Stagnation
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>DACS Divert Propellant</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#059669", marginTop: "2px" }}>
              {result ? result.dacs_fuel_consumed_kg.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>kg</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Total Capacity: 24.0 kg
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", background: "#f8fafc", padding: "0 24px" }}>
          {[
            { id: "visualizer", label: "Hypersonic Engagement Geometry & Shock Diamonds", icon: <Eye size={14} /> },
            { id: "telemetry_table", label: "Guidance & Kinematics Time-Series", icon: <Activity size={14} /> },
            { id: "aerothermo", label: "Aerothermal Heating & Structural Limits", icon: <Flame size={14} /> },
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
                color: activeTab === tab.id ? "#e11d48" : "#64748b",
                borderBottom: activeTab === tab.id ? "2px solid #e11d48" : "2px solid transparent",
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
              {/* SVG 3D/2D Engagement Canvas */}
              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
                    Hypersonic Engagement Profile (Altitude: {result?.time_series[0]?.interceptor_alt_km} km → {result?.time_series[0]?.target_alt_km} km)
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Slant Range: {result?.time_series[0]?.slant_range_km} km
                  </span>
                </div>

                <div
                  style={{
                    width: "100%",
                    height: "330px",
                    background: "#080b14",
                    borderRadius: "8px",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  <svg width="100%" height="100%" viewBox="0 0 700 330">
                    <defs>
                      <linearGradient id="targetGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.2" />
                        <stop offset="100%" stopColor="#f43f5e" stopOpacity="1" />
                      </linearGradient>
                      <linearGradient id="intGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#0284c7" stopOpacity="0.2" />
                        <stop offset="100%" stopColor="#0284c7" stopOpacity="1" />
                      </linearGradient>
                    </defs>

                    {/* Stratosphere altitude grid lines */}
                    <line x1="40" y1="60" x2="660" y2="60" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
                    <text x="45" y="55" fill="#475569" fontSize="8">40 km Stratopause</text>
                    <line x1="40" y1="160" x2="660" y2="160" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
                    <text x="45" y="155" fill="#475569" fontSize="8">30 km Mid Stratosphere</text>
                    <line x1="40" y1="260" x2="660" y2="260" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
                    <text x="45" y="255" fill="#475569" fontSize="8">20 km Upper Troposphere</text>

                    {/* Target Trajectory (Sinusoidal Weave / Evasion) */}
                    <path
                      d="M 640,70 Q 520,60 420,95 T 260,110 T 150,140 L 120,150"
                      fill="none"
                      stroke="url(#targetGrad)"
                      strokeWidth="2.5"
                    />
                    {/* Target Sprite (HGV) */}
                    <g transform="translate(120, 150)">
                      <polygon points="0,0 16,-6 16,6" fill="#f43f5e" />
                      <circle cx="0" cy="0" r="10" fill="none" stroke="#f43f5e" strokeWidth="1" strokeDasharray="2 2" />
                      <text x="-50" y="-12" fill="#f43f5e" fontSize="9" fontWeight="bold">HGV Target (Mach 9.5)</text>
                    </g>

                    {/* Interceptor Trajectory (Mach 8+ ZEM) */}
                    <path
                      d="M 60,300 Q 80,240 100,190 L 118,152"
                      fill="none"
                      stroke="url(#intGrad)"
                      strokeWidth="2.5"
                    />
                    {/* Interceptor Sprite */}
                    <g transform="translate(118, 152)">
                      <polygon points="0,0 -14,-4 -14,4" fill="#0284c7" />
                      {/* DACS lateral pulse plume */}
                      <line x1="-7" y1="-8" x2="-7" y2="8" stroke="#38bdf8" strokeWidth="2" />
                      <text x="-60" y="24" fill="#0284c7" fontSize="9" fontWeight="bold">GPI Interceptor (DACS Active)</text>
                    </g>

                    {/* Impact Flash Reticle */}
                    {isHTK && (
                      <g transform="translate(119, 151)">
                        <circle cx="0" cy="0" r="14" fill="none" stroke="#22c55e" strokeWidth="2" />
                        <line x1="-18" y1="0" x2="18" y2="0" stroke="#22c55e" strokeWidth="1.5" />
                        <line x1="0" y1="-18" x2="0" y2="18" stroke="#22c55e" strokeWidth="1.5" />
                        <text x="22" y="4" fill="#22c55e" fontSize="10" fontWeight="bold">KINETIC IMPACT ({exec?.miss_distance_cm.toFixed(1)} cm)</text>
                      </g>
                    )}
                  </svg>
                </div>
              </div>

              {/* Guidance & Control Parameters */}
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f172a", marginBottom: "12px" }}>
                    Guidance Law &amp; Navigation Ratio
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.78rem" }}>
                    <div>
                      <label style={{ color: "#64748b", display: "block", marginBottom: "4px" }}>Active Guidance Law:</label>
                      <select
                        value={guidanceLaw}
                        onChange={(e) => setGuidanceLaw(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "6px 8px",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          fontWeight: 600,
                        }}
                      >
                        <option value="DIFFERENTIAL_GAME_ZEM">Differential Game (Zero Effort Miss)</option>
                        <option value="AUGMENTED_PN">Augmented Proportional Navigation (APN)</option>
                        <option value="PROPORTIONAL_NAVIGATION">True Proportional Navigation (TPN)</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ color: "#64748b", display: "block", marginBottom: "4px" }}>Target Evasion Maneuver:</label>
                      <select
                        value={targetEvasion}
                        onChange={(e) => setTargetEvasion(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "6px 8px",
                          borderRadius: "6px",
                          border: "1px solid #cbd5e1",
                          fontWeight: 600,
                        }}
                      >
                        <option value="SINUSOIDAL_WEAVE">Sinusoidal Weave (5g at 0.4 Hz)</option>
                        <option value="BARREL_ROLL">Barrel Roll (6g Spiral)</option>
                        <option value="TERMINAL_PULL_UP">Terminal Pull-Up (8g Dive/Climb)</option>
                        <option value="BALLISTIC">Ballistic Glide</option>
                      </select>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "4px" }}>
                      <span style={{ color: "#64748b" }}>Navigation Ratio N:</span>
                      <strong style={{ color: "#0284c7" }}>{navRatio.toFixed(1)}</strong>
                    </div>

                    <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", marginTop: "4px" }}>
                      <input
                        type="checkbox"
                        checked={enableDacs}
                        onChange={(e) => setEnableDacs(e.target.checked)}
                      />
                      <span>Enable DACS Terminal Pulse Divert</span>
                    </label>
                  </div>
                </div>

                <div style={{ background: "#ffffff", borderRadius: "10px", padding: "16px", border: "1px solid #e2e8f0" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f172a", marginBottom: "8px" }}>
                    DACS Multimode Divert
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
                    Solid/bipropellant lateral thrusters fire in microsecond bursts when time-to-go <em>t_go</em> &lt; 2.5s, nullifying residual Zero Effort Miss (ZEM) even under maximum target pull-up g-loads.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "telemetry_table" && (
            <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
              <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 16px 0", color: "#0f172a" }}>
                Guidance &amp; Kinematics Engagement History
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                <thead>
                  <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px" }}>Time (s)</th>
                    <th style={{ padding: "8px 12px" }}>Slant Range (km)</th>
                    <th style={{ padding: "8px 12px" }}>Closing Speed (m/s)</th>
                    <th style={{ padding: "8px 12px" }}>Closing Mach</th>
                    <th style={{ padding: "8px 12px" }}>Time-to-Go (s)</th>
                    <th style={{ padding: "8px 12px" }}>ZEM (m)</th>
                    <th style={{ padding: "8px 12px" }}>G-Load (g)</th>
                    <th style={{ padding: "8px 12px" }}>Heat Flux (MW/m²)</th>
                  </tr>
                </thead>
                <tbody>
                  {result?.time_series.map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "6px 12px", fontFamily: "monospace" }}>{row.time_s.toFixed(2)}s</td>
                      <td style={{ padding: "6px 12px", fontWeight: 600 }}>{row.slant_range_km.toFixed(2)} km</td>
                      <td style={{ padding: "6px 12px", color: "#0284c7" }}>{row.closing_speed_mps.toLocaleString()}</td>
                      <td style={{ padding: "6px 12px" }}>M {row.closing_mach.toFixed(1)}</td>
                      <td style={{ padding: "6px 12px", fontFamily: "monospace" }}>{row.t_go_s.toFixed(2)}s</td>
                      <td style={{ padding: "6px 12px", fontWeight: 700, color: row.zem_m < 2.0 ? "#16a34a" : "#64748b" }}>
                        {row.zem_m.toFixed(2)} m
                      </td>
                      <td style={{ padding: "6px 12px", color: row.g_load > 25.0 ? "#dc2626" : "#0f172a" }}>
                        {row.g_load.toFixed(1)} g
                      </td>
                      <td style={{ padding: "6px 12px", color: "#f59e0b" }}>{row.stagnation_heat_flux_mw.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "aerothermo" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                  Sutton-Graves Convective Heat Flux Invariants
                </h3>
                <div
                  style={{
                    background: "#090d16",
                    color: "#f59e0b",
                    padding: "12px",
                    borderRadius: "6px",
                    fontFamily: "monospace",
                    fontSize: "0.74rem",
                    marginBottom: "12px",
                  }}
                >
                  q̇_stag = k_SG · √(ρ_∞ / R_nose) · V_∞³<br />
                  where k_SG = 1.74153 × 10⁻⁴ (Earth atmosphere)
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.78rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Nose Radius R_nose:</span>
                    <strong>0.04 m (4.0 cm sharp nose)</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Peak Heat Flux Observed:</span>
                    <strong style={{ color: "#f59e0b" }}>{result?.peak_stagnation_heat_flux_mw_m2.toFixed(2)} MW/m²</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>TPS Material:</span>
                    <strong>Ultra-High-Temperature Ceramics (ZrB₂-SiC)</strong>
                  </div>
                </div>
              </div>

              <div style={{ background: "#ffffff", borderRadius: "10px", padding: "20px", border: "1px solid #e2e8f0" }}>
                <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: "0 0 14px 0", color: "#0f172a" }}>
                  Differential Game Formulation
                </h3>
                <p style={{ fontSize: "0.78rem", color: "#64748b", lineHeight: "1.5" }}>
                  Under the two-player zero-sum differential game with quadratic cost:
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
                  a_M* = (N / t_go²) · ZEM - ½N · a_T
                </div>
                <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
                  The guidance command explicitly cancels out half of the target's evading acceleration while focusing the remaining control effort along the Zero Effort Miss line, guaranteeing bounded terminal miss distance even under evasive weaves.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
