"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Zap,
  TrendingUp,
  Sliders,
  Download,
  CheckCircle,
  X,
  Layers,
  ArrowRight,
  Shield,
  Activity,
} from "lucide-react";

interface IterationStep {
  iteration: number;
  cl: number;
  cd: number;
  cm: number;
  lift_to_drag: number;
  thickness_ratio: number;
  camber_ratio: number;
  objective_score: number;
  constraint_violation: number;
}

interface OptimizationResult {
  baseline_airfoil: string;
  target_mach: number;
  target_reynolds: number;
  design_cl: number;
  initial_ld: number;
  optimized_ld: number;
  improvement_pct: number;
  initial_cd: number;
  optimized_cd: number;
  final_thickness_ratio: number;
  final_camber_ratio: number;
  iterations_history: IterationStep[];
  baseline_coordinates: number[][];
  optimized_coordinates: number[][];
  summary: string;
}

interface AirfoilOptimizationStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

export const AirfoilOptimizationStudio: React.FC<AirfoilOptimizationStudioProps> = ({
  isOpen,
  onClose,
  apiBase,
}) => {
  const [baselineAirfoil, setBaselineAirfoil] = useState("NACA 0012");
  const [targetMach, setTargetMach] = useState(0.72);
  const [designCl, setDesignCl] = useState(0.50);
  const [minThickness, setMinThickness] = useState(0.11);
  const [maxCm, setMaxCm] = useState(0.08);
  const [iterations, setIterations] = useState(20);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRunOptimization = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/aerodb/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_airfoil: baselineAirfoil,
          target_mach: targetMach,
          target_reynolds: 6.5e6,
          design_cl: designCl,
          min_thickness_ratio: minThickness,
          max_cm_pitch: maxCm,
          max_iterations: iterations,
        }),
      });

      if (!res.ok) {
        throw new Error(`Optimization failed with status HTTP ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Autonomous optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportDAT = () => {
    if (!result) return;
    let dat = `${result.baseline_airfoil}_OPTIMIZED_LtoD_${result.optimized_ld}\n`;
    for (const pt of result.optimized_coordinates) {
      dat += `  ${pt[0].toFixed(6)}   ${pt[1].toFixed(6)}\n`;
    }
    const blob = new Blob([dat], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.baseline_airfoil.replace(/[^a-zA-Z0-9]/g, "_")}_AASI_Optimized.dat`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="aerospace-modal-overlay" onClick={onClose}>
      <div
        className="aerospace-modal-container"
        style={{
          maxWidth: "1300px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 20px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            background: "rgba(10, 15, 28, 0.95)",
            backdropFilter: "blur(20px)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "rgba(245, 158, 11, 0.15)",
                border: "1px solid rgba(245, 158, 11, 0.35)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#f59e0b",
              }}
            >
              <Sparkles size={18} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700 }}>
                  Autonomous Airfoil Shape Optimization Studio
                </h3>
                <span
                  style={{
                    fontSize: "0.68rem",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(56, 189, 248, 0.15)",
                    border: "1px solid rgba(56, 189, 248, 0.35)",
                    color: "#38bdf8",
                    fontWeight: 700,
                  }}
                >
                  Gradient &amp; Nelder-Mead L/D Maximizer
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.72rem", color: "#64748b" }}>
                Nonlinear parameter optimization for transonic cruise efficiency subject to structural thickness and moment limits.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {result && (
              <button
                onClick={handleExportDAT}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  color: "#f8fafc",
                  fontSize: "0.76rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                <Download size={13} />
                <span>Export Optimized DAT</span>
              </button>
            )}

            <button
              onClick={onClose}
              style={{
                background: "none",
                border: "none",
                color: "#64748b",
                cursor: "pointer",
                padding: "4px",
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Studio Content */}
        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          {/* Left: Design Conditions & Constraints Panel */}
          <div
            style={{
              width: "min(360px, 32vw)",
              minWidth: "270px",
              borderRight: "1px solid rgba(255, 255, 255, 0.08)",
              background: "rgba(10, 15, 28, 0.95)",
              padding: "14px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              overflowY: "auto",
            }}
          >
            <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#cbd5e1" }}>
              Design Objectives &amp; Hard Constraints
            </div>

            {/* Baseline Airfoil */}
            <div>
              <label style={{ fontSize: "0.7rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                Baseline Airfoil Geometry
              </label>
              <select
                value={baselineAirfoil}
                onChange={(e) => setBaselineAirfoil(e.target.value)}
                style={{
                  width: "100%",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  background: "#111827",
                  border: "1px solid #1f2937",
                  color: "#f8fafc",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                }}
              >
                <option value="NACA 0012">NACA 0012 (Symmetric Baseline)</option>
                <option value="RAE 2822">RAE 2822 (Transonic Supercritical)</option>
                <option value="NACA 4412">NACA 4412 (Cambered Baseline)</option>
              </select>
            </div>

            {/* Cruise Mach */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                <span>Cruise Mach Number (M∞)</span>
                <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono)" }}>{targetMach.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.30"
                max="0.82"
                step="0.01"
                value={targetMach}
                onChange={(e) => setTargetMach(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "#38bdf8", cursor: "pointer" }}
              />
            </div>

            {/* Design CL */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                <span>Target Cruise Lift (CL)</span>
                <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono)" }}>{designCl.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.20"
                max="0.90"
                step="0.02"
                value={designCl}
                onChange={(e) => setDesignCl(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "#38bdf8", cursor: "pointer" }}
              />
            </div>

            {/* Structural Min Thickness Constraint */}
            <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                <span>Min Structural Thickness (t/c)</span>
                <span style={{ color: "#f59e0b", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                  {(minThickness * 100).toFixed(1)}%
                </span>
              </div>
              <input
                type="range"
                min="0.08"
                max="0.16"
                step="0.005"
                value={minThickness}
                onChange={(e) => setMinThickness(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "#f59e0b", cursor: "pointer", marginTop: "4px" }}
              />
              <span style={{ fontSize: "0.64rem", color: "#64748b", display: "block", marginTop: "4px" }}>
                Hard constraint: Prevents wing spar buckling &amp; preserves fuel tank volume.
              </span>
            </div>

            {/* Max Moment Limit */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                <span>Max Pitching Moment (|Cm|)</span>
                <span style={{ color: "#94a3b8", fontFamily: "var(--font-mono)" }}>{maxCm.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.03"
                max="0.15"
                step="0.01"
                value={maxCm}
                onChange={(e) => setMaxCm(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "#94a3b8", cursor: "pointer" }}
              />
            </div>

            {/* Iterations */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                <span>Optimizer Steps</span>
                <span style={{ color: "#cbd5e1", fontFamily: "var(--font-mono)" }}>{iterations}</span>
              </div>
              <input
                type="range"
                min="10"
                max="40"
                step="5"
                value={iterations}
                onChange={(e) => setIterations(parseInt(e.target.value))}
                style={{ width: "100%", accentColor: "#cbd5e1", cursor: "pointer" }}
              />
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunOptimization}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                padding: "10px 16px",
                borderRadius: "6px",
                background: "#f59e0b",
                border: "none",
                color: "#0a0d14",
                fontSize: "0.82rem",
                fontWeight: 700,
                cursor: "pointer",
                marginTop: "auto",
              }}
            >
              <Zap size={15} />
              <span>{loading ? "Running Shape Descent..." : "Run Autonomous Optimization"}</span>
            </button>

            {error && (
              <div style={{ color: "#f87171", fontSize: "0.72rem", background: "rgba(239, 68, 68, 0.12)", padding: "8px", borderRadius: "6px" }}>
                {error}
              </div>
            )}
          </div>

          {/* Right: Shape Comparison Canvas & Convergence Telemetry */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              padding: "16px",
              gap: "14px",
              background: "#060911",
              overflowY: "auto",
            }}
          >
            {/* KPI Banner */}
            {result ? (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr 1fr",
                  gap: "10px",
                }}
              >
                <div style={{ background: "#0c111d", border: "1px solid #1e293b", borderRadius: "8px", padding: "12px", textAlign: "center" }}>
                  <div style={{ fontSize: "0.66rem", color: "#64748b" }}>BASELINE L/D</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                    {result.initial_ld.toFixed(1)}
                  </div>
                </div>
                <div style={{ background: "#0c111d", border: "1px solid rgba(16, 185, 129, 0.35)", borderRadius: "8px", padding: "12px", textAlign: "center" }}>
                  <div style={{ fontSize: "0.66rem", color: "#10b981" }}>OPTIMIZED L/D</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#10b981", fontFamily: "var(--font-mono)" }}>
                    {result.optimized_ld.toFixed(1)}
                  </div>
                </div>
                <div style={{ background: "#0c111d", border: "1px solid rgba(56, 189, 248, 0.35)", borderRadius: "8px", padding: "12px", textAlign: "center" }}>
                  <div style={{ fontSize: "0.66rem", color: "#38bdf8" }}>L/D EFFICIENCY GAIN</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#38bdf8", fontFamily: "var(--font-mono)" }}>
                    +{result.improvement_pct.toFixed(1)}%
                  </div>
                </div>
                <div style={{ background: "#0c111d", border: "1px solid #1e293b", borderRadius: "8px", padding: "12px", textAlign: "center" }}>
                  <div style={{ fontSize: "0.66rem", color: "#64748b" }}>THICKNESS (t/c)</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#f59e0b", fontFamily: "var(--font-mono)" }}>
                    {(result.final_thickness_ratio * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ) : (
              <div
                style={{
                  background: "#0c111d",
                  border: "1px dashed #1e293b",
                  borderRadius: "8px",
                  padding: "16px",
                  textAlign: "center",
                  color: "#64748b",
                  fontSize: "0.78rem",
                }}
              >
                Configure flight parameters on the left and click <strong>&quot;Run Autonomous Optimization&quot;</strong> to begin shape synthesis.
              </div>
            )}

            {/* Superimposed 2D Airfoil Shape Comparison Canvas */}
            <div
              style={{
                flex: 1,
                minHeight: "220px",
                background: "#0c111d",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                padding: "14px",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "#cbd5e1" }}>
                  Superimposed Geometry Comparison: Baseline vs Optimized Shape
                </span>
                <div style={{ display: "flex", gap: "14px", fontSize: "0.68rem" }}>
                  <span style={{ color: "#64748b", display: "flex", alignItems: "center", gap: "5px" }}>
                    <span style={{ width: "12px", height: "2px", background: "#64748b", borderTop: "1px dashed #64748b" }} />
                    Baseline ({baselineAirfoil})
                  </span>
                  <span style={{ color: "#38bdf8", display: "flex", alignItems: "center", gap: "5px" }}>
                    <span style={{ width: "12px", height: "2px", background: "#38bdf8" }} />
                    Optimized Airfoil (ASME V&amp;V 20)
                  </span>
                </div>
              </div>

              {/* Airfoil SVG Profile */}
              <div style={{ flex: 1, position: "relative" }}>
                <svg viewBox="0 0 600 200" style={{ width: "100%", height: "100%", display: "block" }}>
                  {/* Grid Lines */}
                  <line x1="50" y1="100" x2="550" y2="100" stroke="#1f2937" strokeDasharray="3 3" />
                  <line x1="300" y1="20" x2="300" y2="180" stroke="#1f2937" strokeDasharray="3 3" />

                  {/* Chord line */}
                  <line x1="50" y1="100" x2="550" y2="100" stroke="#334155" strokeWidth="1" />

                  {/* Baseline path */}
                  {result?.baseline_coordinates && (
                    <path
                      d={result.baseline_coordinates
                        .map((pt, i) => `${i === 0 ? "M" : "L"} ${(50 + pt[0] * 500).toFixed(1)} ${(100 - pt[1] * 380).toFixed(1)}`)
                        .join(" ") + " Z"}
                      fill="none"
                      stroke="#475569"
                      strokeWidth="1.5"
                      strokeDasharray="4 3"
                    />
                  )}

                  {/* Optimized path */}
                  {result?.optimized_coordinates && (
                    <path
                      d={result.optimized_coordinates
                        .map((pt, i) => `${i === 0 ? "M" : "L"} ${(50 + pt[0] * 500).toFixed(1)} ${(100 - pt[1] * 380).toFixed(1)}`)
                        .join(" ") + " Z"}
                      fill="rgba(56, 189, 248, 0.08)"
                      stroke="#38bdf8"
                      strokeWidth="2"
                    />
                  )}

                  {/* Labels */}
                  <text x="50" y="190" fill="#64748b" fontSize="9">0.0 (Leading Edge)</text>
                  <text x="500" y="190" fill="#64748b" fontSize="9">1.0 (Trailing Edge)</text>
                </svg>
              </div>
            </div>

            {/* Convergence History Table / Chart */}
            {result?.iterations_history && (
              <div
                style={{
                  height: "170px",
                  background: "#0c111d",
                  border: "1px solid #1e293b",
                  borderRadius: "8px",
                  padding: "12px",
                  display: "flex",
                  flexDirection: "column",
                  overflowY: "auto",
                }}
              >
                <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#cbd5e1", marginBottom: "8px" }}>
                  Optimization Convergence Progression (Step 1 to {result.iterations_history.length})
                </div>

                <table style={{ width: "100%", fontSize: "0.68rem", borderCollapse: "collapse", fontFamily: "var(--font-mono)" }}>
                  <thead>
                    <tr style={{ color: "#64748b", borderBottom: "1px solid #1f2937", textAlign: "left" }}>
                      <th style={{ padding: "4px" }}>ITER</th>
                      <th style={{ padding: "4px" }}>L/D</th>
                      <th style={{ padding: "4px" }}>CD</th>
                      <th style={{ padding: "4px" }}>t/c</th>
                      <th style={{ padding: "4px" }}>CAMBER</th>
                      <th style={{ padding: "4px" }}>OBJECTIVE</th>
                      <th style={{ padding: "4px" }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.iterations_history.map((s) => (
                      <tr key={s.iteration} style={{ borderBottom: "1px solid #111827" }}>
                        <td style={{ padding: "3px 4px", color: "#cbd5e1" }}>#{s.iteration}</td>
                        <td style={{ padding: "3px 4px", color: "#38bdf8", fontWeight: 700 }}>{s.lift_to_drag.toFixed(1)}</td>
                        <td style={{ padding: "3px 4px", color: "#f59e0b" }}>{s.cd.toFixed(5)}</td>
                        <td style={{ padding: "3px 4px", color: "#cbd5e1" }}>{(s.thickness_ratio * 100).toFixed(1)}%</td>
                        <td style={{ padding: "3px 4px", color: "#94a3b8" }}>{(s.camber_ratio * 100).toFixed(1)}%</td>
                        <td style={{ padding: "3px 4px", color: "#cbd5e1" }}>{s.objective_score.toFixed(1)}</td>
                        <td style={{ padding: "3px 4px", color: s.constraint_violation === 0 ? "#10b981" : "#ef4444" }}>
                          {s.constraint_violation === 0 ? "FEASIBLE" : "PENALTY"}
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
    </div>
  );
};
