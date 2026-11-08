"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Compass,
  Crosshair,
  Target,
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Download,
  Play,
  RotateCcw,
  Sparkles,
  Radio,
  Lock,
  Anchor,
  CheckCircle2,
} from "lucide-react";

interface DockingWaypoint {
  time_s: number;
  rel_pos_m: [number, number, number];
  rel_vel_mps: [number, number, number];
  rel_distance_m: number;
  rel_speed_mps: number;
  attitude_quaternion: [number, number, number, number];
  attitude_error_deg: number;
  rcs_thrust_applied_n: [number, number, number];
  approach_cone_angle_deg: number;
  in_approach_cone: boolean;
  navic_carrier_locked: boolean;
  carrier_phase_cm_error: number;
  docking_latched: boolean;
  fuel_remaining_kg: number;
}

interface SpaDeXSimulationResponse {
  mission_preset: string;
  target_vehicle: string;
  chaser_vehicle: string;
  orbit_type: string;
  initial_distance_m: number;
  final_distance_m: number;
  final_speed_mps: number;
  terminal_latch_status: string;
  astm_f3269_cone_compliant: boolean;
  attitude_alignment_deg: number;
  navic_lambda_ratio_metric: number;
  total_delta_v_mps: number;
  fuel_consumed_kg: number;
  simulation_duration_s: number;
  total_waypoints: number;
  waypoints: DockingWaypoint[];
  merkle_provenance_hash: string;
  safety_standard: string;
}

interface SpadexDockingStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase?: string;
}

const PRESET_OPTIONS = [
  {
    key: "SPADEX_NOMINAL_VBAR",
    label: "ISRO SpaDeX Nominal V-Bar Capture",
    badge: "Primary Mission",
    desc: "225m hold point along +V-bar to 40mm BDS latch entry at 700 km SSO.",
  },
  {
    key: "SPADEX_POST_ECLIPSE_DRIFT_FIX",
    label: "SpaDeX Post-Eclipse Rapid Carrier-Phase Relock",
    badge: "Drift Fix",
    desc: "NavIC L5/S-band carrier phase lock eliminates 225m post-eclipse drift in < 3s.",
  },
  {
    key: "CHANDRAYAAN4_LUNAR_DOCKING",
    label: "Chandrayaan-4 Lunar Orbit ARPO Rendezvous",
    badge: "Lunar Orbit",
    desc: "100 km circular lunar orbit docking between Ascent Lander and Earth Return Module.",
  },
  {
    key: "BAS01_STATION_MODULE",
    label: "Bharatiya Antariksh Station (BAS-01) Heavy Module",
    badge: "Space Station",
    desc: "12,000 kg core module docking with 800 mm APDS peripheral ring at 400 km LEO.",
  },
];

export default function SpadexDockingStudio({
  isOpen,
  onClose,
  apiBase = "http://127.0.0.1:8000",
}: SpadexDockingStudioProps) {
  const [selectedPreset, setSelectedPreset] = useState("SPADEX_NOMINAL_VBAR");
  const [initialDistanceM, setInitialDistanceM] = useState(225.0);
  const [corridorAngleDeg, setCorridorAngleDeg] = useState(15.0);
  const [enableNavicLambda, setEnableNavicLambda] = useState(true);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SpaDeXSimulationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activePlaybackIndex, setActivePlaybackIndex] = useState(0);

  const runSimulation = async (presetKey: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await fetch(`${apiBase}/api/spadex/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: presetKey,
          initial_distance_m: initialDistanceM,
          approach_corridor_deg: corridorAngleDeg,
          enable_navic_lambda: enableNavicLambda,
          max_duration_s: 300.0,
          time_step_s: 1.0,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP Error ${resp.status}`);
      }
      const data: SpaDeXSimulationResponse = await resp.json();
      setResult(data);
      setActivePlaybackIndex(0);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute SpaDeX docking simulation.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !result && !loading) {
      runSimulation(selectedPreset);
    }
  }, [isOpen]);

  const currentWp = useMemo<DockingWaypoint | null>(() => {
    if (!result || !result.waypoints.length) return null;
    const idx = Math.min(activePlaybackIndex, result.waypoints.length - 1);
    return result.waypoints[idx];
  }, [result, activePlaybackIndex]);

  // Project 2D relative approach (X = lateral deviation, Y = along V-bar distance)
  const svgTrajectoryPath = useMemo(() => {
    if (!result || !result.waypoints.length) return "";
    const initDist = result.initial_distance_m || 225.0;
    const pts = result.waypoints.map((w) => {
      // Map V-bar distance (from initDist down to 0) to X-axis [360 to 50]
      const sx = 50 + (w.rel_pos_m[1] / initDist) * 310;
      // Map lateral deviation (X and Z) to Y-axis centered at 200
      const latDev = w.rel_pos_m[0];
      const sy = 200 - latDev * 20.0;
      return `${sx.toFixed(1)},${sy.toFixed(1)}`;
    });
    return `M ${pts.join(" L ")}`;
  }, [result]);

  const currentChaserSvg = useMemo(() => {
    if (!currentWp || !result) return { x: 50, y: 200 };
    const initDist = result.initial_distance_m || 225.0;
    const sx = 50 + (currentWp.rel_pos_m[1] / initDist) * 310;
    const sy = 200 - currentWp.rel_pos_m[0] * 20.0;
    return { x: sx, y: sy };
  }, [currentWp, result]);

  const exportDockingCSV = () => {
    if (!result) return;
    const headers = [
      "Time_s",
      "X_Radial_m",
      "Y_Vbar_m",
      "Z_Crosstrack_m",
      "Distance_m",
      "Speed_mps",
      "AttitudeError_deg",
      "ApproachConeAngle_deg",
      "InCone",
      "NavIC_CarrierLocked",
      "DockingLatched",
      "FuelRemaining_kg",
    ].join(",");
    const rows = result.waypoints.map((w) =>
      [
        w.time_s.toFixed(1),
        w.rel_pos_m[0].toFixed(4),
        w.rel_pos_m[1].toFixed(4),
        w.rel_pos_m[2].toFixed(4),
        w.rel_distance_m.toFixed(4),
        w.rel_speed_mps.toFixed(4),
        w.attitude_error_deg.toFixed(4),
        w.approach_cone_angle_deg.toFixed(2),
        w.in_approach_cone ? "1" : "0",
        w.navic_carrier_locked ? "1" : "0",
        w.docking_latched ? "1" : "0",
        w.fuel_remaining_kg.toFixed(3),
      ].join(",")
    );
    const blob = new Blob([[headers, ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `AASI_SpaDeX_Docking_${result.mission_preset}_Stage12.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1380px",
          maxHeight: "94vh",
          background: "#ffffff",
          borderRadius: "16px",
          border: "1px solid #e2e8f0",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          color: "#0f172a",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "18px 24px",
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
                background: "linear-gradient(135deg, #059669 0%, #047857 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(5, 150, 105, 0.3)",
              }}
            >
              <Target size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.2rem", fontWeight: 800, color: "#0f172a", margin: 0 }}>
                  NavIC Relative Orbit Determination &amp; SpaDeX Autonomous Docking Studio
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#059669",
                    color: "#ffffff",
                    letterSpacing: "0.05em",
                  }}
                >
                  STAGE 12 SOVEREIGN
                </span>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#eff6ff",
                    color: "#2563eb",
                    border: "1px solid #bfdbfe",
                  }}
                >
                  LAMBDA CARRIER-PHASE 1.8 CM FIX
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "#64748b", margin: "2px 0 0 0" }}>
                6-DOF Clohessy-Wiltshire proximity operations, ASTM F3269-21 approach corridor enforcement, and 10 mm/s capture.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={exportDockingCSV}
              disabled={!result}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#f1f5f9",
                border: "1px solid #cbd5e1",
                color: "#334155",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: result ? "pointer" : "not-allowed",
              }}
            >
              <Download size={14} />
              Export Docking Telemetry (CSV)
            </button>
            <button
              onClick={onClose}
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "#f1f5f9",
                border: "1px solid #e2e8f0",
                color: "#475569",
                fontSize: "1.1rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Studio Content */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left Column: Preset Selector & Corridor Parameters */}
          <div
            style={{
              width: "360px",
              borderRight: "1px solid #e2e8f0",
              background: "#ffffff",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              overflowY: "auto",
            }}
          >
            <div>
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                Rendezvous &amp; Docking Scenario Preset
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                {PRESET_OPTIONS.map((p) => {
                  const active = selectedPreset === p.key;
                  return (
                    <div
                      key={p.key}
                      onClick={() => {
                        setSelectedPreset(p.key);
                        runSimulation(p.key);
                      }}
                      style={{
                        padding: "10px 12px",
                        borderRadius: "10px",
                        border: active ? "2px solid #059669" : "1px solid #e2e8f0",
                        background: active ? "#ecfdf5" : "#ffffff",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span style={{ fontSize: "0.82rem", fontWeight: 700, color: active ? "#065f46" : "#1e293b" }}>
                          {p.label.split("(")[0]}
                        </span>
                        <span
                          style={{
                            fontSize: "0.62rem",
                            fontWeight: 700,
                            padding: "1px 6px",
                            borderRadius: "4px",
                            background: active ? "#059669" : "#e2e8f0",
                            color: active ? "#ffffff" : "#475569",
                          }}
                        >
                          {p.badge}
                        </span>
                      </div>
                      <p style={{ fontSize: "0.7rem", color: "#64748b", margin: "4px 0 0 0" }}>{p.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Approach Corridor Parameters */}
            <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                Approach Corridor Bounds
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#475569" }}>
                    <span>Initial Standoff Distance:</span>
                    <strong style={{ color: "#0f172a" }}>{initialDistanceM.toFixed(0)} m</strong>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="500"
                    step="25"
                    value={initialDistanceM}
                    onChange={(e) => setInitialDistanceM(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: "#059669" }}
                  />
                </div>

                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#475569" }}>
                    <span>LOS Approach Cone Half-Angle:</span>
                    <strong style={{ color: "#0f172a" }}>±{corridorAngleDeg.toFixed(0)}°</strong>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="25"
                    step="1"
                    value={corridorAngleDeg}
                    onChange={(e) => setCorridorAngleDeg(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: "#059669" }}
                  />
                </div>

                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: "0.78rem",
                    color: "#334155",
                    cursor: "pointer",
                    marginTop: "4px",
                  }}
                >
                  <span>NavIC LAMBDA Carrier Fix</span>
                  <input
                    type="checkbox"
                    checked={enableNavicLambda}
                    onChange={(e) => setEnableNavicLambda(e.target.checked)}
                    style={{ accentColor: "#059669", width: "16px", height: "16px" }}
                  />
                </label>
              </div>
            </div>

            <button
              onClick={() => runSimulation(selectedPreset)}
              disabled={loading}
              style={{
                marginTop: "auto",
                padding: "12px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, #059669 0%, #047857 100%)",
                color: "#ffffff",
                border: "none",
                fontWeight: 700,
                fontSize: "0.85rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 4px 14px rgba(5, 150, 105, 0.35)",
              }}
            >
              {loading ? <RotateCcw size={16} className="animate-spin" /> : <Play size={16} />}
              {loading ? "Simulating Proximity Ops..." : "Execute ARPO Simulation"}
            </button>
          </div>

          {/* Right Column: Visualizer & Real-Time Telemetry */}
          <div
            style={{
              flex: 1,
              background: "#f8fafc",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
              overflowY: "auto",
            }}
          >
            {errorMsg && (
              <div
                style={{
                  padding: "12px 16px",
                  borderRadius: "10px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  fontSize: "0.82rem",
                }}
              >
                <strong>Simulation Error:</strong> {errorMsg}
              </div>
            )}

            {/* Top Cards: Proximity & Alignment Telemetry */}
            {result && currentWp && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px" }}>
                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>RELATIVE DISTANCE</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {currentWp.rel_distance_m >= 1.0
                      ? `${currentWp.rel_distance_m.toFixed(2)} m`
                      : `${(currentWp.rel_distance_m * 100.0).toFixed(1)} cm`}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600, marginTop: "2px" }}>
                    Closure: {(currentWp.rel_speed_mps * 1000.0).toFixed(1)} mm/s
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>ATTITUDE ALIGNMENT</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {currentWp.attitude_error_deg.toFixed(3)}°
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#2563eb", fontWeight: 600, marginTop: "2px" }}>
                    {currentWp.attitude_error_deg < 0.05 ? "ALIGNED (< 0.05°)" : "CORRECTING SLEW"}
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>NAVIC LAMBDA CARRIER</div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "1.05rem",
                      fontWeight: 800,
                      color: currentWp.navic_carrier_locked ? "#059669" : "#d97706",
                      marginTop: "4px",
                    }}
                  >
                    <Radio size={16} />
                    <span>{currentWp.navic_carrier_locked ? "FIXED (1.8 CM)" : "FLOAT CONVERGING"}</span>
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                    Ratio Metric: {result.navic_lambda_ratio_metric.toFixed(2)} (≥ 2.5)
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>CAPTURE LATCH STATUS</div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "1.05rem",
                      fontWeight: 800,
                      color: currentWp.docking_latched ? "#059669" : "#0284c7",
                      marginTop: "4px",
                    }}
                  >
                    {currentWp.docking_latched ? <Lock size={16} /> : <Crosshair size={16} />}
                    <span>{currentWp.docking_latched ? "LATCH SECURED" : "APPROACH PHASE"}</span>
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                    Fuel: {currentWp.fuel_remaining_kg.toFixed(2)} kg rem.
                  </div>
                </div>
              </div>
            )}

            {/* Middle Section: SVG V-Bar Corridor Viewport & Real-Time Vectors */}
            <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: "16px" }}>
              {/* Approach Corridor SVG Viewport */}
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "14px",
                  border: "1px solid #e2e8f0",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>
                    V-Bar Proximity Corridor Viewport (LVLH Frame)
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Cone Angle: {currentWp ? currentWp.approach_cone_angle_deg.toFixed(2) : 0}° (Corridor: ±{corridorAngleDeg}°)
                  </div>
                </div>

                <div
                  style={{
                    width: "100%",
                    height: "360px",
                    background: "#090d16",
                    borderRadius: "10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  <svg viewBox="0 0 400 400" style={{ width: "100%", height: "100%" }}>
                    {/* Approach Cone Boundaries: ±15 deg cone radiating from docking port at (50, 200) */}
                    <polygon
                      points="50,200 380,110 380,290"
                      fill="rgba(5, 150, 105, 0.08)"
                      stroke="rgba(5, 150, 105, 0.3)"
                      strokeDasharray="4 4"
                    />

                    {/* V-Bar Centerline */}
                    <line x1="30" y1="200" x2="380" y2="200" stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />
                    <text x="370" y="215" fill="#64748b" fontSize="8" textAnchor="end">
                      +V-BAR (FLIGHT DIRECTION)
                    </text>

                    {/* Target Docking Mechanism Port at (50, 200) */}
                    <circle cx="50" cy="200" r="24" fill="#047857" opacity="0.3" />
                    <circle cx="50" cy="200" r="16" fill="none" stroke="#10b981" strokeWidth="2" />
                    <circle cx="50" cy="200" r="6" fill="#10b981" />
                    <line x1="50" y1="170" x2="50" y2="230" stroke="#10b981" strokeWidth="1" strokeDasharray="2 2" />
                    <line x1="20" y1="200" x2="80" y2="200" stroke="#10b981" strokeWidth="1" strokeDasharray="2 2" />
                    <text x="50" y="240" fill="#a7f3d0" fontSize="8" fontWeight="700" textAnchor="middle">
                      TARGET DOCKING PORT
                    </text>

                    {/* Approach Trajectory Curve */}
                    {svgTrajectoryPath && (
                      <path d={svgTrajectoryPath} fill="none" stroke="#38bdf8" strokeWidth="2" opacity="0.8" />
                    )}

                    {/* Chaser Spacecraft */}
                    <g transform={`translate(${currentChaserSvg.x}, ${currentChaserSvg.y})`}>
                      {/* Spacecraft Body */}
                      <rect x="-10" y="-10" width="20" height="20" rx="3" fill="#0284c7" stroke="#ffffff" strokeWidth="1.5" />
                      {/* Solar Panels */}
                      <rect x="-18" y="-4" width="7" height="8" fill="#38bdf8" stroke="#ffffff" strokeWidth="0.5" />
                      <rect x="11" y="-4" width="7" height="8" fill="#38bdf8" stroke="#ffffff" strokeWidth="0.5" />
                      {/* Docking Probe Nose */}
                      <polygon points="-10,0 -16,-3 -16,3" fill="#f59e0b" />
                    </g>
                  </svg>
                </div>

                {/* Trajectory Playback Slider */}
                {result && result.waypoints.length > 0 && (
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px" }}>
                    <span style={{ fontSize: "0.72rem", color: "#64748b" }}>Playback:</span>
                    <input
                      type="range"
                      min="0"
                      max={result.waypoints.length - 1}
                      value={activePlaybackIndex}
                      onChange={(e) => setActivePlaybackIndex(parseInt(e.target.value))}
                      style={{ flex: 1, accentColor: "#059669" }}
                    />
                    <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0f172a" }}>
                      Wp {activePlaybackIndex + 1}/{result.waypoints.length}
                    </span>
                  </div>
                )}
              </div>

              {/* 6-DOF RCS Control Forces & NavIC Ambiguities */}
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "14px",
                  border: "1px solid #e2e8f0",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>
                  Active 6-DOF RCS Commanded Thrust
                </div>
                {currentWp ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem" }}>
                        <span style={{ fontWeight: 600, color: "#334155" }}>Radial Thrust (Fx):</span>
                        <strong style={{ color: "#0284c7" }}>{currentWp.rcs_thrust_applied_n[0].toFixed(2)} N</strong>
                      </div>
                    </div>

                    <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem" }}>
                        <span style={{ fontWeight: 600, color: "#334155" }}>V-Bar Braking (Fy):</span>
                        <strong style={{ color: "#059669" }}>{currentWp.rcs_thrust_applied_n[1].toFixed(2)} N</strong>
                      </div>
                    </div>

                    <div style={{ padding: "10px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem" }}>
                        <span style={{ fontWeight: 600, color: "#334155" }}>Cross-Track Thrust (Fz):</span>
                        <strong style={{ color: "#8b5cf6" }}>{currentWp.rcs_thrust_applied_n[2].toFixed(2)} N</strong>
                      </div>
                    </div>

                    <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "8px", marginTop: "4px" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#334155" }}>
                        Attitude Quaternion State (q):
                      </div>
                      <div
                        style={{
                          fontSize: "0.68rem",
                          fontFamily: "var(--font-mono)",
                          color: "#64748b",
                          marginTop: "4px",
                          wordBreak: "break-all",
                        }}
                      >
                        [{currentWp.attitude_quaternion.map((v) => v.toFixed(5)).join(", ")}]
                      </div>
                    </div>

                    <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "8px" }}>
                      <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#334155" }}>
                        Cumulative Mission Delta-V:
                      </div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#0f172a", marginTop: "2px" }}>
                        {result ? result.total_delta_v_mps.toFixed(3) : "0.000"} m/s
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: "0.78rem", color: "#64748b" }}>Run simulation to observe 6-DOF telemetry.</div>
                )}
              </div>
            </div>

            {/* Bottom Card: ASTM F3269-21 Compliance & Merkle Provenance */}
            {result && (
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "14px",
                  border: "1px solid #e2e8f0",
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "16px",
                  flexWrap: "wrap",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "8px",
                      background: "#ecfdf5",
                      border: "1px solid #a7f3d0",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#059669",
                    }}
                  >
                    <ShieldCheck size={20} />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#065f46" }}>
                      ASTM F3269-21 Run-Time Assurance:{" "}
                      {result.astm_f3269_cone_compliant ? "100% CORRIDOR COMPLIANT" : "CONE EXCURSION DETECTED"}
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                      Capture Speed = {(result.final_speed_mps * 1000.0).toFixed(1)} mm/s (Limit: ≤ 50 mm/s) • Alignment = {result.attitude_alignment_deg.toFixed(3)}°
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "#64748b" }}>
                  <span>MERKLE ROOT:</span>
                  <span
                    style={{
                      padding: "2px 8px",
                      background: "#f1f5f9",
                      borderRadius: "4px",
                      border: "1px solid #e2e8f0",
                      color: "#0f172a",
                    }}
                  >
                    {result.merkle_provenance_hash.slice(0, 16)}...{result.merkle_provenance_hash.slice(-8)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
