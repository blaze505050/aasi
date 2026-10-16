"use client";

import React, { useState, useEffect } from "react";

interface AeroPolarPoint {
  alpha_deg: number;
  mach: number;
  reynolds: number;
  cl: number;
  cd: number;
  cm: number;
  l_over_d: number;
  epistemic_status: string;
}

interface StabilityDerivatives {
  cl_alpha_per_rad: number;
  cl_alpha_per_deg: number;
  alpha_zero_lift_deg: number;
  cl_zero_alpha: number;
  cl_max: number;
  alpha_stall_deg: number;
  cd_0: number;
  cl_at_cd_min: number;
  k_induced_factor: number;
  l_over_d_max: number;
  alpha_cruise_deg: number;
  cm_alpha_per_rad: number;
  cm_alpha_per_deg: number;
  cm_zero_alpha: number;
  aerodynamic_center_x_over_c: number;
  static_margin_ref_quarter_chord: number;
  longitudinal_stability: string;
  subsonic_drag_divergence_mach_est: number;
}

interface FlightConditionPolar {
  mach: number;
  reynolds: number;
  points: AeroPolarPoint[];
  derivatives: StabilityDerivatives;
}

interface AeroDatabase {
  db_id: string;
  geometry_name: string;
  created_at_utc: string;
  chord_m: number;
  conditions: Array<{ mach: number; reynolds: number }>;
  polars: FlightConditionPolar[];
  envelope_summary: {
    total_points_evaluated: number;
    num_conditions: number;
    max_glide_efficiency: number;
    max_lift_capability: number;
    alpha_envelope_range_deg: [number, number];
  };
  provenance_hash: string;
}

interface AeroDbSummary {
  db_id: string;
  geometry_name: string;
  created_at_utc: string;
  num_conditions: number;
  total_points: number;
  max_glide_efficiency: number;
  max_lift_capability: number;
}

interface AeroDbPanelProps {
  apiBase?: string;
  initialGeometry?: string;
}

export const AeroDbPanel: React.FC<AeroDbPanelProps> = ({
  apiBase = process.env.NEXT_PUBLIC_API_URL || "",
  initialGeometry = "NACA 0012",
}) => {
  const [geometry, setGeometry] = useState(initialGeometry);
  const [alphaMin, setAlphaMin] = useState(-6.0);
  const [alphaMax, setAlphaMax] = useState(16.0);
  const [alphaStep, setAlphaStep] = useState(1.0);
  const [reynolds, setReynolds] = useState(3000000);
  const [mach, setMach] = useState(0.15);
  const [generating, setGenerating] = useState(false);
  const [aeroDb, setAeroDb] = useState<AeroDatabase | null>(null);
  const [savedDbs, setSavedDbs] = useState<AeroDbSummary[]>([]);
  const [selectedDbId, setSelectedDbId] = useState<string>("");
  const [selectedCondIdx, setSelectedCondIdx] = useState(0);
  const [hoveredPoint, setHoveredPoint] = useState<AeroPolarPoint | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchSavedDatabases = async () => {
    try {
      const res = await fetch(`${apiBase}/api/aerodb`);
      if (res.ok) {
        const list: AeroDbSummary[] = await res.json();
        setSavedDbs(list);
        return list;
      }
    } catch {
      // offline fallback
    }
    return [];
  };

  const handleLoadDb = async (dbId: string) => {
    if (!dbId) return;
    setGenerating(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${apiBase}/api/aerodb/${dbId}`);
      if (!res.ok) {
        throw new Error(`Failed to load database ${dbId}`);
      }
      const data: AeroDatabase = await res.json();
      setAeroDb(data);
      setSelectedCondIdx(0);
      setGeometry(data.geometry_name);
      setSelectedDbId(data.db_id);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load aerodynamic database.");
    } finally {
      setGenerating(false);
    }
  };

  // On mount, load latest saved database from SQLite or generate initial
  useEffect(() => {
    let isMounted = true;
    const initialize = async () => {
      const list = await fetchSavedDatabases();
      if (!isMounted) return;
      if (list && list.length > 0) {
        await handleLoadDb(list[0].db_id);
      } else {
        await handleGenerateDb();
      }
    };
    initialize();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleGenerateDb = async () => {
    setGenerating(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${apiBase}/api/aerodb/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry,
          alpha_min: alphaMin,
          alpha_max: alphaMax,
          alpha_step: alphaStep,
          reynolds_list: [reynolds],
          mach_list: [mach],
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Failed to generate database" }));
        throw new Error(err.detail || "Polar sweep execution failed");
      }

      const data: AeroDatabase = await res.json();
      setAeroDb(data);
      setSelectedCondIdx(0);
      setSelectedDbId(data.db_id);
      await fetchSavedDatabases();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate aerodynamic database.");
    } finally {
      setGenerating(false);
    }
  };

  const currentCondition = aeroDb?.polars?.[selectedCondIdx] || null;
  const currentPoints = currentCondition?.points || [];
  const derivs = currentCondition?.derivatives || null;

  // Chart rendering helper
  const renderSvgChart = (
    title: string,
    xKey: "alpha_deg" | "cd",
    yKey: "cl" | "cd" | "cm" | "l_over_d",
    xLabel: string,
    yLabel: string,
    color: string,
    width = 460,
    height = 240
  ) => {
    if (!currentPoints || currentPoints.length < 2) return null;

    const padL = 50;
    const padR = 25;
    const padT = 30;
    const padB = 40;
    const plotW = width - padL - padR;
    const plotH = height - padT - padB;

    const xVals = currentPoints.map((p) => p[xKey]);
    const yVals = currentPoints.map((p) => p[yKey]);

    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const minY = Math.min(...yVals);
    const maxY = Math.max(...yVals);

    const spanX = maxX - minX || 1;
    const spanY = maxY - minY || 1;

    const scaleX = (val: number) => padL + ((val - minX) / spanX) * plotW;
    const scaleY = (val: number) => padT + plotH - ((val - minY) / spanY) * plotH;

    // Build polyline points
    const ptsStr = currentPoints
      .map((p) => `${scaleX(p[xKey]).toFixed(1)},${scaleY(p[yKey]).toFixed(1)}`)
      .join(" ");

    // Zero axes if within range
    const zeroX = minX <= 0 && maxX >= 0 ? scaleX(0) : null;
    const zeroY = minY <= 0 && maxY >= 0 ? scaleY(0) : null;

    return (
      <div style={{ background: "#0c1222", border: "1px solid #1e293b", borderRadius: "10px", padding: "14px", position: "relative" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "0.74rem", fontWeight: 700, color: "#fff", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            {title}
          </span>
          <span style={{ fontSize: "0.65rem", fontFamily: "var(--font-mono)", color: color }}>
            {yKey.toUpperCase()} vs {xKey.toUpperCase()}
          </span>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", display: "block" }}>
          {/* Background grid */}
          <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#1e293b" strokeWidth="1" />
          <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#1e293b" strokeWidth="1" />

          {/* Zero X Axis (horizontal reference line) */}
          {zeroY !== null && (
            <line x1={padL} y1={zeroY} x2={padL + plotW} y2={zeroY} stroke="#334155" strokeDasharray="3 3" strokeWidth="1" />
          )}

          {/* Zero Y Axis (vertical reference line) */}
          {zeroX !== null && (
            <line x1={zeroX} y1={padT} x2={zeroX} y2={padT + plotH} stroke="#334155" strokeDasharray="3 3" strokeWidth="1" />
          )}

          {/* Data Line */}
          <polyline fill="none" stroke={color} strokeWidth="2.4" points={ptsStr} strokeLinejoin="round" strokeLinecap="round" />

          {/* Data Points */}
          {currentPoints.map((p, i) => {
            const cx = scaleX(p[xKey]);
            const cy = scaleY(p[yKey]);
            const isHovered = hoveredPoint?.alpha_deg === p.alpha_deg;
            return (
              <circle
                key={i}
                cx={cx}
                cy={cy}
                r={isHovered ? 5.5 : 2.5}
                fill={isHovered ? "#fff" : color}
                stroke={color}
                strokeWidth="1.5"
                style={{ cursor: "pointer", transition: "all 0.15s ease" }}
                onMouseEnter={() => setHoveredPoint(p)}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            );
          })}

          {/* Axis Labels */}
          <text x={padL} y={padT - 8} fill="#94a3b8" fontSize="10" fontFamily="sans-serif">
            {maxY.toFixed(2)}
          </text>
          <text x={padL} y={padT + plotH + 16} fill="#94a3b8" fontSize="10" fontFamily="sans-serif">
            {minY.toFixed(2)}
          </text>
          <text x={padL} y={padT + plotH + 30} fill="#94a3b8" fontSize="10" fontFamily="sans-serif">
            {minX.toFixed(1)}°
          </text>
          <text x={padL + plotW - 25} y={padT + plotH + 30} fill="#94a3b8" fontSize="10" fontFamily="sans-serif">
            {maxX.toFixed(1)}°
          </text>
          <text x={padL + plotW / 2 - 20} y={padT + plotH + 32} fill="#64748b" fontSize="11" fontWeight="600" fontFamily="sans-serif">
            {xLabel}
          </text>
        </svg>

        {hoveredPoint && (
          <div style={{
            position: "absolute",
            bottom: "12px",
            right: "14px",
            background: "rgba(15, 23, 42, 0.9)",
            border: "1px solid #38bdf8",
            borderRadius: "6px",
            padding: "4px 8px",
            fontSize: "0.68rem",
            fontFamily: "var(--font-mono)",
            color: "#fff",
            pointerEvents: "none"
          }}>
            α={hoveredPoint.alpha_deg.toFixed(1)}° | CL={hoveredPoint.cl.toFixed(4)} | CD={hoveredPoint.cd.toFixed(5)} | L/D={hoveredPoint.l_over_d.toFixed(1)}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="aerodb-workspace animate-fade-in" style={{ marginTop: "12px" }}>
      {/* ─── Control Header ─── */}
      <div style={{
        background: "rgba(17, 24, 39, 0.75)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "12px",
        padding: "18px 24px",
        marginBottom: "16px",
        backdropFilter: "blur(20px)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "1.2rem" }}>📊</span>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 800, color: "#fff", letterSpacing: "-0.01em" }}>
                Autonomous Aerodynamic Database (Aero DB) &amp; Polars
              </h2>
            </div>
            <p style={{ fontSize: "0.74rem", color: "var(--text-muted)", marginTop: "2px" }}>
              Full flight envelope synthesis, stability derivatives, and industry-standard exports for 6-DOF flight simulators.
            </p>
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            {savedDbs.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginRight: "6px" }}>
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>
                  AeroDB Store:
                </span>
                <select
                  value={selectedDbId}
                  onChange={(e) => handleLoadDb(e.target.value)}
                  style={{
                    background: "#0f172a",
                    border: "1px solid #334155",
                    color: "#38bdf8",
                    fontSize: "0.72rem",
                    borderRadius: "6px",
                    padding: "6px 10px",
                    cursor: "pointer",
                    outline: "none",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 600,
                  }}
                  title="Select previously computed and persisted aerodynamic flight envelope database"
                >
                  {savedDbs.map((db) => (
                    <option key={db.db_id} value={db.db_id}>
                      {db.geometry_name} ({db.db_id.slice(-8)}) — {db.total_points} pts
                    </option>
                  ))}
                </select>
              </div>
            )}
            {aeroDb && (
              <>
                <a
                  href={`${apiBase}/api/aerodb/${aeroDb.db_id}/export?format=datcom`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-export"
                  style={{
                    background: "rgba(2, 132, 199, 0.2)",
                    border: "1px solid #0284c7",
                    color: "#38bdf8",
                    fontWeight: 700,
                  }}
                  title="Download USAF Stability and Control DATCOM standard card deck (.dat)"
                >
                  <span>✈️</span>
                  <span>DATCOM (.dat)</span>
                </a>

                <a
                  href={`${apiBase}/api/aerodb/${aeroDb.db_id}/export?format=shabp`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-export"
                  style={{
                    background: "rgba(16, 185, 129, 0.2)",
                    border: "1px solid #10b981",
                    color: "#10b981",
                    fontWeight: 700,
                  }}
                  title="Download NASA S/HABP tabulated polar format (.shabp)"
                >
                  <span>🚀</span>
                  <span>NASA S/HABP</span>
                </a>

                <a
                  href={`${apiBase}/api/aerodb/${aeroDb.db_id}/export?format=csv`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-export"
                  title="Download 6-DOF Simulation CSV lookup table"
                >
                  <span>📈</span>
                  <span>6-DOF CSV</span>
                </a>

                <a
                  href={`${apiBase}/api/aerodb/${aeroDb.db_id}/export?format=json`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-export"
                  title="Download raw JSON schema"
                >
                  <span>{`{ }`}</span>
                  <span>JSON</span>
                </a>
              </>
            )}
          </div>
        </div>

        {/* Sweep Parameter Controls */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
          gap: "12px",
          alignItems: "end"
        }}>
          <div>
            <label style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Airfoil Profile
            </label>
            <input
              type="text"
              className="problem-input"
              style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              value={geometry}
              onChange={(e) => setGeometry(e.target.value)}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Alpha Min (deg)
            </label>
            <input
              type="number"
              className="problem-input"
              style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              value={alphaMin}
              onChange={(e) => setAlphaMin(Number(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Alpha Max (deg)
            </label>
            <input
              type="number"
              className="problem-input"
              style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              value={alphaMax}
              onChange={(e) => setAlphaMax(Number(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Step (deg)
            </label>
            <input
              type="number"
              className="problem-input"
              style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              value={alphaStep}
              onChange={(e) => setAlphaStep(Number(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Reynolds (Re)
            </label>
            <input
              type="number"
              className="problem-input"
              style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              value={reynolds}
              onChange={(e) => setReynolds(Number(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.68rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Mach Number
            </label>
            <input
              type="number"
              step="0.05"
              className="problem-input"
              style={{ fontSize: "0.75rem", padding: "6px 10px" }}
              value={mach}
              onChange={(e) => setMach(Number(e.target.value))}
            />
          </div>

          <div>
            <button
              className="btn-primary"
              style={{ width: "100%", padding: "8px 14px", fontSize: "0.75rem" }}
              disabled={generating}
              onClick={handleGenerateDb}
            >
              {generating ? "Sweeping…" : "GENERATE AERO DB →"}
            </button>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="error-alert animate-fade-in" style={{ marginBottom: "14px" }}>
          <span>⚠ {errorMsg}</span>
        </div>
      )}

      {/* ─── Multi-Condition Flight Envelope Switcher Tabs ─── */}
      {aeroDb && aeroDb.polars && aeroDb.polars.length > 1 && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "14px",
          flexWrap: "wrap",
          padding: "8px 14px",
          background: "rgba(15, 23, 42, 0.75)",
          borderRadius: "8px",
          border: "1px solid rgba(255, 255, 255, 0.08)"
        }}>
          <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            FLIGHT CONDITIONS ({aeroDb.polars.length}):
          </span>
          {aeroDb.polars.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setSelectedCondIdx(idx)}
              style={{
                fontSize: "0.72rem",
                padding: "4px 10px",
                borderRadius: "6px",
                fontFamily: "var(--font-mono)",
                fontWeight: selectedCondIdx === idx ? 700 : 500,
                background: selectedCondIdx === idx ? "#0284c7" : "rgba(30, 41, 59, 0.7)",
                color: selectedCondIdx === idx ? "#ffffff" : "#94a3b8",
                border: selectedCondIdx === idx ? "1px solid #38bdf8" : "1px solid #334155",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              M = {p.mach.toFixed(2)} · Re = {p.reynolds.toExponential(1)} ({p.points.length} pts)
            </button>
          ))}
        </div>
      )}

      {/* ─── Stability & Control Derivatives KPI Cards ─── */}
      {derivs && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: "10px",
          marginBottom: "16px"
        }}>
          <div className="aero-kpi-card">
            <div className="aero-kpi-header">
              <span className="aero-kpi-label">LIFT SLOPE (C_L_α)</span>
              <span className="aero-kpi-chip aero-kpi-chip-blue">LINEAR</span>
            </div>
            <div className="aero-kpi-value-row">
              <span className="aero-kpi-value">{derivs.cl_alpha_per_rad.toFixed(3)}</span>
              <span className="aero-kpi-delta aero-kpi-delta-good">/rad</span>
            </div>
            <div className="aero-kpi-footer">
              <span className="aero-kpi-sub">
                {derivs.cl_alpha_per_deg.toFixed(4)} / deg
              </span>
            </div>
          </div>

          <div className="aero-kpi-card">
            <div className="aero-kpi-header">
              <span className="aero-kpi-label">ZERO-LIFT ANGLE</span>
              <span className="aero-kpi-chip aero-kpi-chip-teal">α_0L</span>
            </div>
            <div className="aero-kpi-value-row">
              <span className="aero-kpi-value">{derivs.alpha_zero_lift_deg.toFixed(2)}°</span>
            </div>
            <div className="aero-kpi-footer">
              <span className="aero-kpi-sub">
                CL(α=0) = {derivs.cl_zero_alpha.toFixed(4)}
              </span>
            </div>
          </div>

          <div className="aero-kpi-card">
            <div className="aero-kpi-header">
              <span className="aero-kpi-label">MAX GLIDE EFFICIENCY</span>
              <span className="aero-kpi-chip aero-kpi-chip-indigo">(L/D)_max</span>
            </div>
            <div className="aero-kpi-value-row">
              <span className="aero-kpi-value" style={{ color: "#38bdf8" }}>{derivs.l_over_d_max.toFixed(1)}</span>
            </div>
            <div className="aero-kpi-footer">
              <span className="aero-kpi-sub">
                Cruise AoA: <strong>{derivs.alpha_cruise_deg.toFixed(1)}°</strong>
              </span>
            </div>
          </div>

          <div className="aero-kpi-card">
            <div className="aero-kpi-header">
              <span className="aero-kpi-label">MIN PROFILE DRAG</span>
              <span className="aero-kpi-chip aero-kpi-chip-purple">C_D0</span>
            </div>
            <div className="aero-kpi-value-row">
              <span className="aero-kpi-value">{derivs.cd_0.toFixed(5)}</span>
            </div>
            <div className="aero-kpi-footer">
              <span className="aero-kpi-sub">
                K factor: {derivs.k_induced_factor.toFixed(4)}
              </span>
            </div>
          </div>

          <div className="aero-kpi-card">
            <div className="aero-kpi-header">
              <span className="aero-kpi-label">AERODYNAMIC CENTER</span>
              <span className="aero-kpi-chip aero-kpi-chip-blue">x_ac / c</span>
            </div>
            <div className="aero-kpi-value-row">
              <span className="aero-kpi-value">{(derivs.aerodynamic_center_x_over_c * 100).toFixed(1)}%</span>
            </div>
            <div className="aero-kpi-footer">
              <span className="aero-kpi-sub">
                Δ from c/4: {((derivs.aerodynamic_center_x_over_c - 0.25) * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="aero-kpi-card">
            <div className="aero-kpi-header">
              <span className="aero-kpi-label">PITCH STABILITY</span>
              <span className="aero-kpi-chip aero-kpi-chip-teal">C_M_α</span>
            </div>
            <div className="aero-kpi-value-row">
              <span className="aero-kpi-value" style={{
                color: derivs.longitudinal_stability === "STATICALLY_STABLE" ? "#10b981" : "#f59e0b",
                fontSize: "1rem"
              }}>
                {derivs.longitudinal_stability.replace("_", " ")}
              </span>
            </div>
            <div className="aero-kpi-footer">
              <span className="aero-kpi-sub">
                CM_α = {derivs.cm_alpha_per_deg.toFixed(4)} / deg
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ─── 4 Interactive Polar Visualizers ─── */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
        gap: "14px",
        marginBottom: "20px"
      }}>
        {renderSvgChart("1. Lift Curve", "alpha_deg", "cl", "Angle of Attack (α deg)", "Lift Coefficient (CL)", "#38bdf8")}
        {renderSvgChart("2. Drag Polar (Parabolic)", "cd", "cl", "Drag Coefficient (CD)", "Lift Coefficient (CL)", "#34d399")}
        {renderSvgChart("3. Pitching Moment (Quarter-Chord)", "alpha_deg", "cm", "Angle of Attack (α deg)", "Pitch Moment (CM)", "#a78bfa")}
        {renderSvgChart("4. Aerodynamic Efficiency (Glide Ratio)", "alpha_deg", "l_over_d", "Angle of Attack (α deg)", "L / D Ratio", "#f59e0b")}
      </div>

      {/* ─── Tabular Inspection Data Table ─── */}
      {currentPoints.length > 0 && (
        <div className="glass-card" style={{ padding: "18px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#fff", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Aerodynamic Database Polar Tabular Records ({geometry})
            </span>
            <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              Mach={currentCondition?.mach.toFixed(2)} · Re={currentCondition?.reynolds.toExponential(1)} · {currentPoints.length} points
            </span>
          </div>

          <div style={{ overflowX: "auto", maxHeight: "280px" }}>
            <table className="matrix-table" style={{ fontSize: "0.72rem" }}>
              <thead>
                <tr>
                  <th>AoA (α°)</th>
                  <th>CL (Total)</th>
                  <th>CD (Profile)</th>
                  <th>CM (c/4)</th>
                  <th>L / D</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {currentPoints.map((pt, idx) => (
                  <tr key={idx} style={{ background: hoveredPoint?.alpha_deg === pt.alpha_deg ? "rgba(56, 189, 248, 0.12)" : "transparent" }}>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#fff" }}>{pt.alpha_deg.toFixed(1)}°</td>
                    <td style={{ fontFamily: "var(--font-mono)", color: "#38bdf8" }}>{pt.cl.toFixed(4)}</td>
                    <td style={{ fontFamily: "var(--font-mono)", color: "#34d399" }}>{pt.cd.toFixed(5)}</td>
                    <td style={{ fontFamily: "var(--font-mono)", color: "#a78bfa" }}>{pt.cm.toFixed(4)}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: pt.l_over_d > 0 ? "#10b981" : "#ef4444" }}>
                      {pt.l_over_d.toFixed(2)}
                    </td>
                    <td>
                      <span className="badge badge-success" style={{ fontSize: "0.6rem" }}>
                        {pt.epistemic_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
