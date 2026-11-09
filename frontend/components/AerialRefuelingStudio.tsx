"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Compass,
  Wind,
  ShieldCheck,
  ShieldAlert,
  Fuel,
  Play,
  RefreshCw,
  X,
  Crosshair,
  AlertTriangle,
  Layers,
  ArrowRight,
  Plane,
  Gauge,
  Sliders,
  CheckCircle2,
} from "lucide-react";

interface AerialRefuelingStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface TelemetryPoint {
  time_sec: number;
  distance_to_drogue_m: number;
  radial_error_m: number;
  closing_velocity_mps: number;
  tanker_downwash_mps: number;
  tanker_sidewash_mps: number;
  drogue_bow_wave_lift_m: number;
  cbf_barrier_val: number;
  phase: string;
  fuel_transferred_kg: number;
}

interface SimResult {
  mission_id: string;
  tanker_metadata: {
    type: string;
    name: string;
    mass_kg: number;
    wingspan_m: number;
    vortex_circulation_m2_per_s: number;
    refueling_speed_mps: number;
  };
  receiver_metadata: {
    name: string;
    cbf_protection_active: boolean;
    docking_cone_half_angle_deg: number;
    bow_wave_compensation: boolean;
  };
  mission_outcome: {
    status: string;
    successful_docking: boolean;
    latch_contact_time_sec: number | null;
    final_radial_error_cm: number | null;
    final_contact_speed_mps: number | null;
    total_fuel_transferred_kg: number;
    cbf_safety_interventions: number;
    breakaway_executed: boolean;
  };
  telemetry_points: TelemetryPoint[];
}

export default function AerialRefuelingStudio({
  isOpen,
  onClose,
  apiBase,
}: AerialRefuelingStudioProps) {
  const [tankerType, setTankerType] = useState<string>("KC_767");
  const [standoffDist, setStandoffDist] = useState<number>(15.0);
  const [turbulenceGust, setTurbulenceGust] = useState<number>(3.0);
  const [enableCbf, setEnableCbf] = useState<boolean>(true);
  const [forceBreakaway, setForceBreakaway] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<SimResult | null>(null);
  const [selectedPointIndex, setSelectedPointIndex] = useState<number>(0);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/aerial-refueling/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tanker_type: tankerType,
          receiver_name: "Ghatak Autonomous Strike UCAV",
          initial_standoff_distance_m: standoffDist,
          enable_cbf_protection: enableCbf,
          enable_emergency_breakaway_test: forceBreakaway,
          turbulence_gust_mps: turbulenceGust,
          sim_time_sec: 25.0,
        }),
      });
      const data: Record<string, any> = await resp.json();
      if (data.status === "success" && data.data) {
        setSimResult(data.data);
        const pts = data.data.telemetry_points || [];
        setSelectedPointIndex(pts.length > 0 ? pts.length - 1 : 0);
      }
    } catch (err) {
      console.error("Failed to run aerial refueling simulation:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !simResult) {
      runSimulation();
    }
  }, [isOpen]);

  // Render Visual Servoing Crosshair & Funnel Canvas
  useEffect(() => {
    if (!canvasRef.current || !simResult) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Background grid
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    const step = 25;
    for (let x = 0; x < width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const centerX = width / 2;
    const centerY = height / 2;

    const curPoint = simResult.telemetry_points[selectedPointIndex] || simResult.telemetry_points[0];
    if (!curPoint) return;

    // Draw Drogue Outer Ring & Target Receptacle Center
    // Radius of outer basket: ~ 45 cm (~ 90px on screen)
    // Throat receptacle: ~ 12 cm (~ 25px)
    const basketRadius = 100;
    const throatRadius = 28;

    // Drogue Basket Mesh Lines (Conical Petals)
    ctx.strokeStyle = "rgba(100, 116, 139, 0.4)";
    ctx.lineWidth = 1.5;
    for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 8) {
      ctx.beginPath();
      ctx.moveTo(centerX + throatRadius * Math.cos(angle), centerY + throatRadius * Math.sin(angle));
      ctx.lineTo(centerX + basketRadius * Math.cos(angle), centerY + basketRadius * Math.sin(angle));
      ctx.stroke();
    }

    // Outer Basket Ring
    ctx.beginPath();
    ctx.arc(centerX, centerY, basketRadius, 0, Math.PI * 2);
    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Inner Latch Throat (Target)
    ctx.beginPath();
    ctx.arc(centerX, centerY, throatRadius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(16, 185, 129, 0.15)";
    ctx.fill();
    ctx.strokeStyle = "#059669";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Crosshairs
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = "#94a3b8";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(centerX - 120, centerY);
    ctx.lineTo(centerX + 120, centerY);
    ctx.moveTo(centerX, centerY - 120);
    ctx.lineTo(centerX, centerY + 120);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Bow Wave Induced Drogue Center Shift
    const drogueShiftY = -curPoint.drogue_bow_wave_lift_m * 120; // Upward in screen coords is negative Y
    if (Math.abs(drogueShiftY) > 2) {
      ctx.beginPath();
      ctx.arc(centerX, centerY + drogueShiftY, throatRadius, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(234, 88, 12, 0.7)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.fillStyle = "rgba(234, 88, 12, 0.8)";
      ctx.font = "10px sans-serif";
      ctx.fillText("Bow Wave Lifted Target", centerX + throatRadius + 6, centerY + drogueShiftY + 4);
    }

    // Receiver Probe Tip Coordinates
    // Radial error determines probe offset from throat center
    // We project radial error along current azimuth
    const scalePxPerM = 200.0;
    const probeX = centerX + (curPoint.radial_error_m * 0.707) * scalePxPerM;
    const probeY = (centerY + drogueShiftY) + (curPoint.radial_error_m * 0.707) * scalePxPerM;

    // Draw Safe CBF Cone Circle for current distance
    const coneAngleRad = (22.0 * Math.PI) / 180.0;
    const maxAllowedRadiusM = curPoint.distance_to_drogue_m * Math.tan(coneAngleRad) + 0.15;
    const maxAllowedRadiusPx = Math.min(width * 0.48, maxAllowedRadiusM * scalePxPerM);

    ctx.beginPath();
    ctx.arc(centerX, centerY + drogueShiftY, maxAllowedRadiusPx, 0, Math.PI * 2);
    ctx.strokeStyle = curPoint.cbf_barrier_val >= 0 ? "rgba(16, 185, 129, 0.5)" : "rgba(225, 29, 72, 0.7)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Probe Tip Reticle
    ctx.beginPath();
    ctx.arc(probeX, probeY, 8, 0, Math.PI * 2);
    const isInsideThroat = curPoint.radial_error_m <= 0.12 && curPoint.distance_to_drogue_m <= 0.10;
    ctx.fillStyle = isInsideThroat ? "#059669" : curPoint.phase === "EMERGENCY_BREAKAWAY" ? "#dc2626" : "#2563eb";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Probe Lead Line to Receptacle
    ctx.beginPath();
    ctx.moveTo(probeX, probeY);
    ctx.lineTo(centerX, centerY + drogueShiftY);
    ctx.strokeStyle = isInsideThroat ? "rgba(5, 150, 105, 0.6)" : "rgba(37, 99, 235, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // HUD Text Overlay
    ctx.fillStyle = "#0f172a";
    ctx.font = "bold 11px monospace";
    ctx.fillText(`DIST: ${curPoint.distance_to_drogue_m.toFixed(2)}m`, 14, 22);
    ctx.fillText(`RAD ERROR: ${(curPoint.radial_error_m * 100).toFixed(1)}cm`, 14, 38);
    ctx.fillText(`V_CLOSE: ${curPoint.closing_velocity_mps.toFixed(2)}m/s`, 14, 54);
    ctx.fillText(`DOWNWASH: ${curPoint.tanker_downwash_mps.toFixed(2)}m/s`, 14, 70);

    const phaseColor =
      curPoint.phase === "LATCHED_FUEL"
        ? "#059669"
        : curPoint.phase === "EMERGENCY_BREAKAWAY"
        ? "#dc2626"
        : "#2563eb";

    ctx.fillStyle = phaseColor;
    ctx.fillText(`PHASE: ${curPoint.phase}`, width - 200, 22);
  }, [simResult, selectedPointIndex]);

  if (!isOpen) return null;

  const currentPoint =
    simResult?.telemetry_points[selectedPointIndex] || simResult?.telemetry_points[0];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        backgroundColor: "rgba(15, 23, 42, 0.75)",
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
          maxWidth: "1320px",
          height: "92vh",
          backgroundColor: "#ffffff",
          borderRadius: "14px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          border: "1px solid #e2e8f0",
          color: "#0f172a",
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "linear-gradient(to right, #f8fafc, #ffffff)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                backgroundColor: "rgba(37, 99, 235, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "1px solid rgba(37, 99, 235, 0.25)",
              }}
            >
              <Fuel size={22} color="#2563eb" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Autonomous Aerial Refueling & Visually-Coupled Docking CBF
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    backgroundColor: "#2563eb",
                    color: "#ffffff",
                    padding: "2px 8px",
                    borderRadius: "9999px",
                    letterSpacing: "0.05em",
                  }}
                >
                  STAGE 30 • EPOCH VI CAPSTONE
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "#64748b", margin: 0, marginTop: "2px" }}>
                Hallock-Burnham Heavy Tanker Wake Vortex • Receiver Stagnation Bow Wave • Control Barrier Function Safe Cone & Escape
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              onClick={runSimulation}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                backgroundColor: "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                padding: "8px 16px",
                fontSize: "0.82rem",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 2px 4px rgba(37, 99, 235, 0.2)",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Simulating Approach..." : "Execute Docking Run"}
            </button>

            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "8px",
                cursor: "pointer",
                color: "#64748b",
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Main Workspace Body */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left Controls & Parameters */}
          <div
            style={{
              width: "360px",
              borderRight: "1px solid #e2e8f0",
              backgroundColor: "#f8fafc",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
              overflowY: "auto",
            }}
          >
            {/* Tanker & Mission Config */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "10px",
                padding: "16px",
                border: "1px solid #e2e8f0",
              }}
            >
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b", display: "flex", alignItems: "center", gap: "6px" }}>
                <Plane size={15} color="#2563eb" />
                Tanker & Wake Vortex Model
              </h3>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Tanker Aircraft Platform
                </label>
                <select
                  value={tankerType}
                  onChange={(e) => setTankerType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.8rem",
                    backgroundColor: "#ffffff",
                    color: "#0f172a",
                  }}
                >
                  <option value="KC_767">Boeing KC-767 Tanker (155,000 kg)</option>
                  <option value="IL_78">Ilyushin Il-78 MKI Heavy Tanker (190,000 kg)</option>
                  <option value="KC_46">Boeing KC-46A Pegasus (165,000 kg)</option>
                </select>
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Initial Standoff Distance: {standoffDist.toFixed(1)} m
                </label>
                <input
                  type="range"
                  min="5"
                  max="25"
                  step="0.5"
                  value={standoffDist}
                  onChange={(e) => setStandoffDist(parseFloat(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Turbulence Gust RMS: {turbulenceGust.toFixed(1)} m/s
                </label>
                <input
                  type="range"
                  min="0"
                  max="8"
                  step="0.5"
                  value={turbulenceGust}
                  onChange={(e) => setTurbulenceGust(parseFloat(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <input
                    type="checkbox"
                    id="cbfToggle"
                    checked={enableCbf}
                    onChange={(e) => setEnableCbf(e.target.checked)}
                  />
                  <label htmlFor="cbfToggle" style={{ fontSize: "0.78rem", fontWeight: 600, color: "#334155" }}>
                    Enable CBF Safe Cone Protection (22° Funnel)
                  </label>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <input
                    type="checkbox"
                    id="breakawayToggle"
                    checked={forceBreakaway}
                    onChange={(e) => setForceBreakaway(e.target.checked)}
                  />
                  <label htmlFor="breakawayToggle" style={{ fontSize: "0.78rem", fontWeight: 600, color: "#dc2626" }}>
                    Force Mid-Approach Emergency Breakaway
                  </label>
                </div>
              </div>
            </div>

            {/* Aerodynamic Circulation Card */}
            {simResult && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Wind size={15} color="#2563eb" />
                  Wake Aerodynamics
                </h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>Circulation Γ₀:</span>
                    <span style={{ fontWeight: 700, color: "#0f172a" }}>
                      {simResult.tanker_metadata.vortex_circulation_m2_per_s} m²/s
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>Airspeed:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>
                      {simResult.tanker_metadata.refueling_speed_mps} m/s (~350 KIAS)
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>Wingspan:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>
                      {simResult.tanker_metadata.wingspan_m} m
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "4px" }}>
                    <span style={{ color: "#64748b" }}>Bow Wave Rejection:</span>
                    <span style={{ fontWeight: 700, color: "#059669" }}>Adaptive Lead Compensator</span>
                  </div>
                </div>
              </div>
            )}

            {/* Mission Outcome Card */}
            {simResult && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b" }}>
                  Refueling Outcome
                </h3>

                <div
                  style={{
                    padding: "10px 12px",
                    borderRadius: "8px",
                    backgroundColor: simResult.mission_outcome.successful_docking ? "#ecfdf5" : "#fef2f2",
                    border: `1px solid ${simResult.mission_outcome.successful_docking ? "#a7f3d0" : "#fecaca"}`,
                    marginBottom: "12px",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.8rem",
                      fontWeight: 800,
                      color: simResult.mission_outcome.successful_docking ? "#065f46" : "#991b1b",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    {simResult.mission_outcome.successful_docking ? (
                      <CheckCircle2 size={16} />
                    ) : (
                      <AlertTriangle size={16} />
                    )}
                    {simResult.mission_outcome.status}
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.75rem" }}>
                  {simResult.mission_outcome.latch_contact_time_sec && (
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>Latch Contact Time:</span>
                      <span style={{ fontWeight: 600 }}>{simResult.mission_outcome.latch_contact_time_sec} s</span>
                    </div>
                  )}
                  {simResult.mission_outcome.final_radial_error_cm !== null && (
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#64748b" }}>Contact Centering Error:</span>
                      <span style={{ fontWeight: 700, color: "#059669" }}>
                        {simResult.mission_outcome.final_radial_error_cm} cm (NATO MA-2 Spec)
                      </span>
                    </div>
                  )}
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Fuel Delivered:</span>
                    <span style={{ fontWeight: 700, color: "#2563eb" }}>
                      {simResult.mission_outcome.total_fuel_transferred_kg} kg
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>CBF Safety Overrides:</span>
                    <span style={{ fontWeight: 600 }}>{simResult.mission_outcome.cbf_safety_interventions}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Main Canvas & Flight Telemetry */}
          <div style={{ flex: 1, padding: "24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Top Status & HUD Bar */}
            {currentPoint && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "12px",
                  padding: "16px 20px",
                  border: "1px solid #e2e8f0",
                  display: "grid",
                  gridTemplateColumns: "repeat(5, 1fr)",
                  gap: "12px",
                  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600 }}>STANDOFF DISTANCE</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "#0f172a" }}>
                    {currentPoint.distance_to_drogue_m.toFixed(2)} m
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600 }}>RADIAL OFFSET</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: currentPoint.radial_error_m <= 0.15 ? "#059669" : "#ea580c" }}>
                    {(currentPoint.radial_error_m * 100).toFixed(1)} cm
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600 }}>CLOSING SPEED</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "#0f172a" }}>
                    {currentPoint.closing_velocity_mps.toFixed(2)} m/s
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600 }}>WAKE DOWNWASH</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "#2563eb" }}>
                    {currentPoint.tanker_downwash_mps.toFixed(2)} m/s
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 600 }}>FUEL DELIVERED</div>
                  <div style={{ fontSize: "1.15rem", fontWeight: 800, color: "#059669" }}>
                    {currentPoint.fuel_transferred_kg.toFixed(0)} kg
                  </div>
                </div>
              </div>
            )}

            {/* Visual Servoing Crosshairs Canvas */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                padding: "16px",
                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <div style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#1e293b", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Crosshair size={16} color="#2563eb" />
                  Optical-LiDAR Relative Servoing & Conical Barrier Funnel
                </div>
                <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                  Green Circle = CBF Safe Cone Boundary • Orange Circle = Bow-Wave Shifted Drogue Basket
                </div>
              </div>

              <canvas
                ref={canvasRef}
                width={700}
                height={340}
                style={{
                  borderRadius: "8px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#f8fafc",
                }}
              />

              {/* Timeline Scrubber */}
              {simResult && simResult.telemetry_points.length > 0 && (
                <div style={{ width: "100%", marginTop: "14px", display: "flex", alignItems: "center", gap: "12px" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b" }}>Timeline:</span>
                  <input
                    type="range"
                    min="0"
                    max={simResult.telemetry_points.length - 1}
                    value={selectedPointIndex}
                    onChange={(e) => setSelectedPointIndex(parseInt(e.target.value))}
                    style={{ flex: 1 }}
                  />
                  <span style={{ fontSize: "0.75rem", fontFamily: "monospace", fontWeight: 700 }}>
                    {currentPoint?.time_sec.toFixed(2)}s / 25.0s
                  </span>
                </div>
              )}
            </div>

            {/* Telemetry Log Table */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                overflow: "hidden",
                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
              }}
            >
              <div
                style={{
                  padding: "12px 18px",
                  borderBottom: "1px solid #e2e8f0",
                  backgroundColor: "#f8fafc",
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: "#1e293b",
                }}
              >
                Flight Telemetry Record
              </div>

              <div style={{ maxHeight: "180px", overflowY: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem", textAlign: "left" }}>
                  <thead>
                    <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>
                      <th style={{ padding: "8px 14px" }}>Time (s)</th>
                      <th style={{ padding: "8px 14px" }}>Distance</th>
                      <th style={{ padding: "8px 14px" }}>Radial Err</th>
                      <th style={{ padding: "8px 14px" }}>Closing Vel</th>
                      <th style={{ padding: "8px 14px" }}>Downwash</th>
                      <th style={{ padding: "8px 14px" }}>CBF Barrier</th>
                      <th style={{ padding: "8px 14px" }}>Flight Phase</th>
                    </tr>
                  </thead>
                  <tbody>
                    {simResult?.telemetry_points.map((pt, idx) => (
                      <tr
                        key={idx}
                        onClick={() => setSelectedPointIndex(idx)}
                        style={{
                          borderBottom: "1px solid #f1f5f9",
                          cursor: "pointer",
                          backgroundColor: idx === selectedPointIndex ? "rgba(37, 99, 235, 0.08)" : "#ffffff",
                        }}
                      >
                        <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{pt.time_sec.toFixed(1)}s</td>
                        <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{pt.distance_to_drogue_m.toFixed(2)}m</td>
                        <td style={{ padding: "6px 14px", fontFamily: "monospace", color: pt.radial_error_m <= 0.15 ? "#059669" : "#ea580c" }}>
                          {(pt.radial_error_m * 100).toFixed(1)}cm
                        </td>
                        <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{pt.closing_velocity_mps.toFixed(2)}m/s</td>
                        <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{pt.tanker_downwash_mps.toFixed(2)}m/s</td>
                        <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{pt.cbf_barrier_val.toFixed(3)}</td>
                        <td style={{ padding: "6px 14px", fontWeight: 600 }}>{pt.phase}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
