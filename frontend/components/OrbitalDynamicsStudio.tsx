"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Globe,
  Orbit,
  Compass,
  Zap,
  Activity,
  Layers,
  ShieldCheck,
  Download,
  Play,
  RotateCcw,
  Sun,
  Moon,
  Info,
  Clock,
  Sparkles,
} from "lucide-react";

interface TrajectoryPoint {
  time_s: number;
  position_km: [number, number, number];
  velocity_km_s: [number, number, number];
  altitude_km: number;
  speed_km_s: number;
  semi_major_axis_km: number;
  eccentricity: number;
  inclination_deg: number;
  raan_deg: number;
  true_anomaly_deg: number;
  hamiltonian_energy_mj_kg: number;
  energy_error: number;
  in_sunlight: boolean;
  acceleration_breakdown: Record<string, number>;
}

interface OrbitalPropagationResponse {
  vehicle_name: string;
  vehicle_mass_kg: number;
  duration_hours: number;
  time_step_s: number;
  total_computed_steps: number;
  transmitted_points: number;
  max_hamiltonian_energy_error: number;
  symplectic_invariant_verified: boolean;
  initial_state: {
    altitude_km: number;
    speed_km_s: number;
    semi_major_axis_km: number;
    eccentricity: number;
    inclination_deg: number;
    period_minutes: number;
  };
  final_state: {
    altitude_km: number;
    speed_km_s: number;
    semi_major_axis_km: number;
    eccentricity: number;
    inclination_deg: number;
  };
  trajectory: TrajectoryPoint[];
  provenance_hash: string;
  asme_vv20_status: string;
}

interface OrbitalDynamicsStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase?: string;
}

const PRESET_OPTIONS = [
  {
    key: "GAGANYAAN_LEO",
    label: "ISRO Gaganyaan Crew Module (400 km LEO)",
    badge: "Crewed Flight",
    desc: "400 km circular orbit, 51.6 deg inclination, dynamic thermospheric drag.",
  },
  {
    key: "SPADEX_CHASER",
    label: "ISRO SpaDeX Autonomous Chaser (700 km SSO)",
    badge: "Autonomous Docking",
    desc: "700 km Sun-Synchronous, 98.2 deg inclination, relative rendezvous trajectory.",
  },
  {
    key: "CHANDRAYAAN4_TLI",
    label: "ISRO Chandrayaan-4 Trans-Lunar Injection (TLI)",
    badge: "Lunar Transfer",
    desc: "Highly elliptical orbit (e=0.966), Moon third-body gravity, solar radiation pressure.",
  },
  {
    key: "NAVIC_GEO",
    label: "NavIC / IRNSS Sovereign Constellation (GSO)",
    badge: "Sovereign PNT",
    desc: "35,786 km geostationary orbit, 29.0 deg inclination, solar radiation pressure.",
  },
];

export default function OrbitalDynamicsStudio({
  isOpen,
  onClose,
  apiBase = "http://127.0.0.1:8000",
}: OrbitalDynamicsStudioProps) {
  const [selectedPreset, setSelectedPreset] = useState("GAGANYAAN_LEO");
  const [durationHours, setDurationHours] = useState(3.0);
  const [timeStepSeconds, setTimeStepSeconds] = useState(30.0);
  const [enableDrag, setEnableDrag] = useState(true);
  const [enableSRP, setEnableSRP] = useState(true);
  const [enableThirdBody, setEnableThirdBody] = useState(true);
  const [enableRelativity, setEnableRelativity] = useState(true);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OrbitalPropagationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activePlaybackIndex, setActivePlaybackIndex] = useState(0);

  const runPropagation = async (presetKey: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await fetch(`${apiBase}/api/orbital/propagate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: presetKey,
          duration_hours: durationHours,
          time_step_s: timeStepSeconds,
          enable_drag: enableDrag,
          enable_srp: enableSRP,
          enable_third_body: enableThirdBody,
          enable_relativity: enableRelativity,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP Error ${resp.status}`);
      }
      const data: OrbitalPropagationResponse = await resp.json();
      setResult(data);
      setActivePlaybackIndex(0);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute orbital propagation.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !result && !loading) {
      runPropagation(selectedPreset);
    }
  }, [isOpen]);

  const currentPt = useMemo<TrajectoryPoint | null>(() => {
    if (!result || !result.trajectory.length) return null;
    const idx = Math.min(activePlaybackIndex, result.trajectory.length - 1);
    return result.trajectory[idx];
  }, [result, activePlaybackIndex]);

  // Project 3D trajectory into 2D SVG canvas
  const svgTrajectoryPath = useMemo(() => {
    if (!result || !result.trajectory.length) return "";
    // Scale based on semi-major axis
    const maxR = Math.max(...result.trajectory.map((p) => Math.hypot(p.position_km[0], p.position_km[1])));
    const scale = 140 / (maxR || 7000);
    const pts = result.trajectory.map((p) => {
      const sx = 200 + p.position_km[0] * scale;
      const sy = 200 - p.position_km[1] * scale;
      return `${sx.toFixed(1)},${sy.toFixed(1)}`;
    });
    return `M ${pts.join(" L ")}`;
  }, [result]);

  const currentPosSvg = useMemo(() => {
    if (!currentPt || !result) return { x: 200, y: 200 };
    const maxR = Math.max(...result.trajectory.map((p) => Math.hypot(p.position_km[0], p.position_km[1])));
    const scale = 140 / (maxR || 7000);
    return {
      x: 200 + currentPt.position_km[0] * scale,
      y: 200 - currentPt.position_km[1] * scale,
    };
  }, [currentPt, result]);

  const earthRadiusSvg = useMemo(() => {
    if (!result) return 40;
    const maxR = Math.max(...result.trajectory.map((p) => Math.hypot(p.position_km[0], p.position_km[1])));
    const scale = 140 / (maxR || 7000);
    return Math.max(6, Math.min(80, 6378.137 * scale));
  }, [result]);

  const exportEphemerisCSV = () => {
    if (!result) return;
    const headers = [
      "Time_s",
      "X_km",
      "Y_km",
      "Z_km",
      "Vx_km_s",
      "Vy_km_s",
      "Vz_km_s",
      "Altitude_km",
      "Speed_km_s",
      "Energy_MJ_kg",
      "InSunlight",
    ].join(",");
    const rows = result.trajectory.map((p) =>
      [
        p.time_s.toFixed(1),
        p.position_km[0].toFixed(3),
        p.position_km[1].toFixed(3),
        p.position_km[2].toFixed(3),
        p.velocity_km_s[0].toFixed(5),
        p.velocity_km_s[1].toFixed(5),
        p.velocity_km_s[2].toFixed(5),
        p.altitude_km.toFixed(3),
        p.speed_km_s.toFixed(5),
        p.hamiltonian_energy_mj_kg.toFixed(6),
        p.in_sunlight ? "1" : "0",
      ].join(",")
    );
    const blob = new Blob([[headers, ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `AASI_Ephemeris_${result.vehicle_name}_Stage11.csv`);
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
                background: "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(2, 132, 199, 0.3)",
              }}
            >
              <Orbit size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.2rem", fontWeight: 800, color: "#0f172a", margin: 0 }}>
                  High-Precision Orbital Dynamics &amp; Non-Spherical Gravity Studio
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#0284c7",
                    color: "#ffffff",
                    letterSpacing: "0.05em",
                  }}
                >
                  STAGE 11 SOVEREIGN
                </span>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#ecfdf5",
                    color: "#059669",
                    border: "1px solid #a7f3d0",
                  }}
                >
                  4TH-ORDER SYMPLECTIC YOSHIDA
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "#64748b", margin: "2px 0 0 0" }}>
                Special perturbations with J2-J4 geopotential, dynamic thermospheric drag, solar radiation pressure, and third-body gravity.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={exportEphemerisCSV}
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
              Export Ephemeris (CSV)
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
          {/* Left Column: Preset Selector & Force Controls */}
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
                ISRO / Sovereign Mission Preset
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                {PRESET_OPTIONS.map((p) => {
                  const active = selectedPreset === p.key;
                  return (
                    <div
                      key={p.key}
                      onClick={() => {
                        setSelectedPreset(p.key);
                        runPropagation(p.key);
                      }}
                      style={{
                        padding: "10px 12px",
                        borderRadius: "10px",
                        border: active ? "2px solid #0284c7" : "1px solid #e2e8f0",
                        background: active ? "#f0f9ff" : "#ffffff",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span style={{ fontSize: "0.82rem", fontWeight: 700, color: active ? "#0369a1" : "#1e293b" }}>
                          {p.label.split("(")[0]}
                        </span>
                        <span
                          style={{
                            fontSize: "0.62rem",
                            fontWeight: 700,
                            padding: "1px 6px",
                            borderRadius: "4px",
                            background: active ? "#0284c7" : "#e2e8f0",
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

            {/* Simulation Parameters */}
            <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                Trajectory Parameters
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#475569" }}>
                    <span>Duration:</span>
                    <strong style={{ color: "#0f172a" }}>{durationHours.toFixed(1)} Hours</strong>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="12.0"
                    step="0.5"
                    value={durationHours}
                    onChange={(e) => setDurationHours(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: "#0284c7" }}
                  />
                </div>

                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#475569" }}>
                    <span>Integrator Step:</span>
                    <strong style={{ color: "#0f172a" }}>{timeStepSeconds} s</strong>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="120"
                    step="10"
                    value={timeStepSeconds}
                    onChange={(e) => setTimeStepSeconds(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: "#0284c7" }}
                  />
                </div>
              </div>
            </div>

            {/* Physics Toggles */}
            <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                Perturbation Force Inclusions
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "10px" }}>
                {[
                  { label: "Dynamic Upper Atmospheric Drag", state: enableDrag, setter: setEnableDrag },
                  { label: "Solar Radiation Pressure (SRP)", state: enableSRP, setter: setEnableSRP },
                  { label: "Moon & Sun 3-Body Gravity", state: enableThirdBody, setter: setEnableThirdBody },
                  { label: "Schwarzschild General Relativity", state: enableRelativity, setter: setEnableRelativity },
                ].map((item, idx) => (
                  <label
                    key={idx}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      fontSize: "0.78rem",
                      color: "#334155",
                      cursor: "pointer",
                    }}
                  >
                    <span>{item.label}</span>
                    <input
                      type="checkbox"
                      checked={item.state}
                      onChange={(e) => item.setter(e.target.checked)}
                      style={{ accentColor: "#0284c7", width: "16px", height: "16px" }}
                    />
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={() => runPropagation(selectedPreset)}
              disabled={loading}
              style={{
                marginTop: "auto",
                padding: "12px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
                color: "#ffffff",
                border: "none",
                fontWeight: 700,
                fontSize: "0.85rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 4px 14px rgba(2, 132, 199, 0.35)",
              }}
            >
              {loading ? <RotateCcw size={16} className="animate-spin" /> : <Play size={16} />}
              {loading ? "Propagating Ephemeris..." : "Run Symplectic Propagation"}
            </button>
          </div>

          {/* Right Column: Visualization & Diagnostics */}
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
                <strong>Propagation Error:</strong> {errorMsg}
              </div>
            )}

            {/* Top Cards: Initial vs Current vs Final State */}
            {result && currentPt && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px" }}>
                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>ALTITUDE / SPEED</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {currentPt.altitude_km.toFixed(1)} <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>km</span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#0284c7", fontWeight: 600, marginTop: "2px" }}>
                    {currentPt.speed_km_s.toFixed(3)} km/s
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
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>SEMI-MAJOR AXIS &amp; ECC</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {currentPt.semi_major_axis_km.toFixed(1)} <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>km</span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600, marginTop: "2px" }}>
                    e = {currentPt.eccentricity.toFixed(5)}
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
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>INCLINATION &amp; RAAN</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {currentPt.inclination_deg.toFixed(2)}°
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#8b5cf6", fontWeight: 600, marginTop: "2px" }}>
                    Ω = {currentPt.raan_deg.toFixed(2)}°
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
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>SOLAR ILLUMINATION</div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "1.1rem",
                      fontWeight: 800,
                      color: currentPt.in_sunlight ? "#d97706" : "#2563eb",
                      marginTop: "6px",
                    }}
                  >
                    {currentPt.in_sunlight ? <Sun size={18} /> : <Moon size={18} />}
                    <span>{currentPt.in_sunlight ? "DIRECT SUNLIGHT" : "UMBRA ECLIPSE"}</span>
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
                    {currentPt.in_sunlight ? "SRP Acceleration Active" : "Thermal Decay Phase"}
                  </div>
                </div>
              </div>
            )}

            {/* Middle Section: SVG Orbit Map & Acceleration Breakdown */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "16px" }}>
              {/* SVG 2D Orbit Viewport */}
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
                    Orbital Plane Projection (ECI X-Y)
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Epoch T + {(currentPt ? currentPt.time_s : 0).toFixed(0)} s
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
                    {/* Background Grid */}
                    <circle cx="200" cy="200" r="180" fill="none" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                    <circle cx="200" cy="200" r="120" fill="none" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                    <line x1="20" y1="200" x2="380" y2="200" stroke="rgba(255,255,255,0.08)" />
                    <line x1="200" y1="20" x2="200" y2="380" stroke="rgba(255,255,255,0.08)" />

                    {/* Earth Sphere */}
                    <circle cx="200" cy="200" r={earthRadiusSvg} fill="#1d4ed8" opacity="0.8" />
                    <circle cx="200" cy="200" r={earthRadiusSvg} fill="none" stroke="#38bdf8" strokeWidth="1.5" />
                    <text x="200" y="204" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="700">
                      EARTH
                    </text>

                    {/* Orbit Path */}
                    {svgTrajectoryPath && (
                      <path d={svgTrajectoryPath} fill="none" stroke="#38bdf8" strokeWidth="2" opacity="0.85" />
                    )}

                    {/* Current Vehicle Position */}
                    <circle
                      cx={currentPosSvg.x}
                      cy={currentPosSvg.y}
                      r="6"
                      fill={currentPt && currentPt.in_sunlight ? "#f59e0b" : "#3b82f6"}
                      stroke="#ffffff"
                      strokeWidth="2"
                    />
                    <circle
                      cx={currentPosSvg.x}
                      cy={currentPosSvg.y}
                      r="12"
                      fill="none"
                      stroke={currentPt && currentPt.in_sunlight ? "#f59e0b" : "#3b82f6"}
                      strokeWidth="1"
                      opacity="0.5"
                    />
                  </svg>
                </div>

                {/* Trajectory Playback Slider */}
                {result && result.trajectory.length > 0 && (
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "4px" }}>
                    <span style={{ fontSize: "0.72rem", color: "#64748b" }}>Playback:</span>
                    <input
                      type="range"
                      min="0"
                      max={result.trajectory.length - 1}
                      value={activePlaybackIndex}
                      onChange={(e) => setActivePlaybackIndex(parseInt(e.target.value))}
                      style={{ flex: 1, accentColor: "#0284c7" }}
                    />
                    <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "#0f172a" }}>
                      Pt {activePlaybackIndex + 1}/{result.trajectory.length}
                    </span>
                  </div>
                )}
              </div>

              {/* Real-Time Perturbation Force Breakdown */}
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
                  Instantaneous Force Perturbation Breakdown
                </div>
                {currentPt ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {[
                      {
                        name: "Central Gravity (Two-Body)",
                        val: currentPt.acceleration_breakdown["central_g"] || 0,
                        color: "#0284c7",
                      },
                      {
                        name: "J2 Oblateness Perturbation",
                        val: currentPt.acceleration_breakdown["j2_oblateness"] || 0,
                        color: "#059669",
                      },
                      {
                        name: "J3 Pear-Shape Harmonic",
                        val: currentPt.acceleration_breakdown["j3_pear"] || 0,
                        color: "#10b981",
                      },
                      {
                        name: "J4 Zonal Harmonic",
                        val: currentPt.acceleration_breakdown["j4_harmonic"] || 0,
                        color: "#14b8a6",
                      },
                      {
                        name: "Upper Atmospheric Drag",
                        val: currentPt.acceleration_breakdown["atmospheric_drag"] || 0,
                        color: "#ef4444",
                      },
                      {
                        name: "Solar Radiation Pressure (SRP)",
                        val: currentPt.acceleration_breakdown["solar_radiation_pressure"] || 0,
                        color: "#f59e0b",
                      },
                      {
                        name: "Moon & Sun 3-Body Gravity",
                        val: currentPt.acceleration_breakdown["third_body_gravity"] || 0,
                        color: "#8b5cf6",
                      },
                      {
                        name: "General Relativity (Schwarzschild)",
                        val: currentPt.acceleration_breakdown["general_relativity"] || 0,
                        color: "#6366f1",
                      },
                    ].map((force, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: "8px 10px",
                          borderRadius: "8px",
                          background: "#f8fafc",
                          border: "1px solid #f1f5f9",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem" }}>
                          <span style={{ fontWeight: 600, color: "#334155" }}>{force.name}</span>
                          <span style={{ fontWeight: 700, color: force.color }}>
                            {force.val > 0.001
                              ? `${force.val.toFixed(4)} m/s²`
                              : `${force.val.toExponential(3)} m/s²`}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: "0.78rem", color: "#64748b" }}>Run simulation to observe force breakdown.</div>
                )}
              </div>
            </div>

            {/* Bottom Card: Symplectic Invariant Proof & Merkle Provenance */}
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
                      ASME V&amp;V 20 Symplectic Invariant Proof:{" "}
                      {result.symplectic_invariant_verified ? "PASSED (NO ENERGY DRIFT)" : "DEGRADED"}
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                      Max Hamiltonian Energy Error ΔH/H₀ = {result.max_hamiltonian_energy_error.toExponential(4)} (Tolerance: &lt; 1e-4)
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
                    {result.provenance_hash.slice(0, 16)}...{result.provenance_hash.slice(-8)}
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
