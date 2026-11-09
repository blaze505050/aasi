"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Layers,
  Cpu,
  RefreshCw,
  X,
  Play,
  Sliders,
  CheckCircle2,
  Sparkles,
  Zap,
  Activity,
  Box,
  Flame,
  ArrowRight,
} from "lucide-react";

interface GenerativeMdoStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface MdoResult {
  component_id: string;
  optimization: {
    grid: { nx: number; ny: number; total_elements: number };
    alloy: string;
    convergence: Array<{
      iteration: number;
      compliance: number;
      volume_fraction: number;
      max_change: number;
    }>;
    final_metrics: {
      initial_compliance: number;
      final_compliance: number;
      final_volume_fraction: number;
      nominal_mass_kg: number;
      optimized_mass_kg: number;
      mass_reduction_percent: number;
      max_stress_mpa: number;
      yield_strength_mpa: number;
      safety_factor: number;
      self_supporting_manufacturability_percent: number;
      total_solve_time_sec: number;
    };
    density_field: number[];
  };
  lpbf_toolpath: {
    toolpath_compiler: string;
    alloy: string;
    laser_power_w: number;
    scan_speed_mps: number;
    layer_thickness_um: number;
    hatch_spacing_um: number;
    representative_layer_hatches: number;
    total_laser_track_length_m: number;
    total_3d_layers: number;
    estimated_build_time_hours: number;
    hatch_samples: Array<{
      start: [number, number];
      end: [number, number];
      power_w: number;
      speed_mps: number;
    }>;
  };
}

export default function GenerativeMdoStudio({
  isOpen,
  onClose,
  apiBase,
}: GenerativeMdoStudioProps) {
  const [componentName, setComponentName] = useState<string>("TITANIUM_TRANSONIC_WING_RIB");
  const [alloyChoice, setAlloyChoice] = useState<string>("TI_6AL_4V");
  const [targetVolfrac, setTargetVolfrac] = useState<number>(0.40);
  const [maxIterations, setMaxIterations] = useState<number>(20);
  const [showToolpaths, setShowToolpaths] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [mdoData, setMdoData] = useState<MdoResult | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const runOptimization = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/generative-mdo/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          component_name: componentName,
          target_volume_fraction: targetVolfrac,
          alloy_choice: alloyChoice,
          max_iterations: maxIterations,
        }),
      });
      const data: Record<string, any> = await resp.json();
      if (data.status === "success" && data.data) {
        setMdoData(data.data);
      }
    } catch (err) {
      console.error("Failed to run generative MDO optimization:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !mdoData) {
      runOptimization();
    }
  }, [isOpen]);

  // Render Topology Density Field & LPBF Laser Toolpaths
  useEffect(() => {
    if (!canvasRef.current || !mdoData) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const nx = mdoData.optimization.grid.nx;
    const ny = mdoData.optimization.grid.ny;
    const cellW = width / nx;
    const cellH = height / ny;
    const densities = mdoData.optimization.density_field;

    // 1. Draw Density Heatmap
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const e = j * nx + i;
        const rho = densities[e] || 0.0;
        // Invert Y so j=0 is bottom
        const y = (ny - 1 - j) * cellH;
        const x = i * cellW;

        if (rho < 0.15) {
          ctx.fillStyle = "#f8fafc"; // Void background
        } else {
          // Solid Titanium / Alloy gradient: dark slate to cyan
          const intensity = Math.min(1.0, (rho - 0.15) / 0.85);
          const r = Math.round(15 + (1.0 - intensity) * 80);
          const g = Math.round(23 + (1.0 - intensity) * 120);
          const b = Math.round(42 + (1.0 - intensity) * 160);
          ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        }
        ctx.fillRect(x, y, cellW + 0.5, cellH + 0.5);
      }
    }

    // 2. Overlay LPBF Laser Vector Toolpaths if enabled
    if (showToolpaths && mdoData.lpbf_toolpath.hatch_samples) {
      ctx.strokeStyle = "#06b6d4"; // Cyan laser scan tracks
      ctx.lineWidth = 1.5;

      const scaleX = width / (nx * 5.0); // 5mm per cell = 250mm width
      const scaleY = height / (ny * 5.0);

      mdoData.lpbf_toolpath.hatch_samples.forEach((hatch) => {
        const startX = hatch.start[0] * scaleX;
        const startY = height - hatch.start[1] * scaleY;
        const endX = hatch.end[0] * scaleX;
        const endY = height - hatch.end[1] * scaleY;

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.stroke();

        // Little laser bead indicator
        ctx.fillStyle = "#e11d48";
        ctx.beginPath();
        ctx.arc(endX, endY, 2.0, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // 3. Coordinate Axes & Scale Indicator
    ctx.fillStyle = "#0f172a";
    ctx.font = "bold 11px monospace";
    ctx.fillText("5-AXIS CNC / LPBF SCANPATH COMPILATION (Ti-6Al-4V)", 14, 20);
    ctx.fillText(`GRID: ${nx} x ${ny} (${nx * 5}mm x ${ny * 5}mm)`, 14, 36);
  }, [mdoData, showToolpaths]);

  if (!isOpen) return null;

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
                backgroundColor: "rgba(14, 165, 233, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "1px solid rgba(14, 165, 233, 0.25)",
              }}
            >
              <Box size={22} color="#0284c7" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Multidisciplinary Topology Optimization to 5-Axis CNC / LPBF Toolpaths
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    padding: "2px 8px",
                    borderRadius: "9999px",
                    letterSpacing: "0.05em",
                  }}
                >
                  STAGE 31 • EPOCH VII INITIATION
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "#64748b", margin: 0, marginTop: "2px" }}>
                SIMP Finite Element Compliance Minimization • Self-Supporting Overhang Constraints • Direct Neural-Implicit Scanpath Compiler
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              onClick={runOptimization}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                backgroundColor: "#0284c7",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                padding: "8px 16px",
                fontSize: "0.82rem",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 2px 4px rgba(2, 132, 199, 0.2)",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Optimizing Topology..." : "Synthesize Topology"}
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
            {/* Component & Alloy Settings */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "10px",
                padding: "16px",
                border: "1px solid #e2e8f0",
              }}
            >
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b", display: "flex", alignItems: "center", gap: "6px" }}>
                <Sliders size={15} color="#0284c7" />
                Structural Design Domain
              </h3>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Aerospace Component
                </label>
                <select
                  value={componentName}
                  onChange={(e) => setComponentName(e.target.value)}
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
                  <option value="TITANIUM_TRANSONIC_WING_RIB">Titanium Ti-6Al-4V Transonic Wing Rib</option>
                  <option value="ROCKET_ENGINE_GIMBAL_BRACKET">Inconel 718 Cryogenic Gimbal Pivot Bracket</option>
                  <option value="SATELLITE_OPTICAL_BENCH">AlSi10Mg Satellite Optical Bench Mount</option>
                </select>
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Aerospace Alloy Material
                </label>
                <select
                  value={alloyChoice}
                  onChange={(e) => setAlloyChoice(e.target.value)}
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
                  <option value="TI_6AL_4V">Titanium Ti-6Al-4V (E=114 GPa, σ_y=880 MPa)</option>
                  <option value="INCONEL_718">Inconel 718 Superalloy (E=205 GPa, σ_y=1100 MPa)</option>
                  <option value="AL_SI10_MG">AlSi10Mg Additive Aluminum (E=70 GPa, σ_y=240 MPa)</option>
                </select>
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Target Volume Fraction: {(targetVolfrac * 100).toFixed(0)}% (Mass Cut: {((1 - targetVolfrac) * 100).toFixed(0)}%)
                </label>
                <input
                  type="range"
                  min="0.25"
                  max="0.65"
                  step="0.05"
                  value={targetVolfrac}
                  onChange={(e) => setTargetVolfrac(parseFloat(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input
                  type="checkbox"
                  id="toolpathToggle"
                  checked={showToolpaths}
                  onChange={(e) => setShowToolpaths(e.target.checked)}
                />
                <label htmlFor="toolpathToggle" style={{ fontSize: "0.78rem", fontWeight: 600, color: "#334155" }}>
                  Overlay LPBF Laser Scanpath Vectors
                </label>
              </div>
            </div>

            {/* Mass Reduction & Mechanical KPIs */}
            {mdoData && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b" }}>
                  Lightweighting & Stress Metrics
                </h3>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "12px" }}>
                  <div style={{ backgroundColor: "#ecfdf5", padding: "10px", borderRadius: "8px", border: "1px solid #a7f3d0" }}>
                    <div style={{ fontSize: "0.68rem", color: "#047857", fontWeight: 600 }}>MASS REDUCTION</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#065f46" }}>
                      -{mdoData.optimization.final_metrics.mass_reduction_percent}%
                    </div>
                  </div>

                  <div style={{ backgroundColor: "#eff6ff", padding: "10px", borderRadius: "8px", border: "1px solid #bfdbfe" }}>
                    <div style={{ fontSize: "0.68rem", color: "#1e40af", fontWeight: 600 }}>SAFETY FACTOR</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#1e3a8a" }}>
                      {mdoData.optimization.final_metrics.safety_factor}x
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Nominal Solid Mass:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.optimization.final_metrics.nominal_mass_kg} kg</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Optimized Bionic Mass:</span>
                    <span style={{ fontWeight: 700, color: "#059669" }}>
                      {mdoData.optimization.final_metrics.optimized_mass_kg} kg
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Max von Mises Stress:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.optimization.final_metrics.max_stress_mpa} MPa</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Yield Strength:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.optimization.final_metrics.yield_strength_mpa} MPa</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Self-Supporting Ratio:</span>
                    <span style={{ fontWeight: 700, color: "#0284c7" }}>
                      {mdoData.optimization.final_metrics.self_supporting_manufacturability_percent}%
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* LPBF Additive Manufacturing Spec */}
            {mdoData && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Flame size={15} color="#ea580c" />
                  LPBF 3D Print Recipe
                </h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Laser Power:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.lpbf_toolpath.laser_power_w} W</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Scan Velocity:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.lpbf_toolpath.scan_speed_mps} m/s</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Layer Thickness:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.lpbf_toolpath.layer_thickness_um} μm</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Total 3D Layers:</span>
                    <span style={{ fontWeight: 600 }}>{mdoData.lpbf_toolpath.total_3d_layers} layers</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Total Laser Track:</span>
                    <span style={{ fontWeight: 700, color: "#0284c7" }}>
                      {mdoData.lpbf_toolpath.total_laser_track_length_m} m/layer
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "4px", borderTop: "1px solid #f1f5f9" }}>
                    <span style={{ color: "#64748b" }}>Est. Build Time:</span>
                    <span style={{ fontWeight: 800, color: "#ea580c" }}>
                      {mdoData.lpbf_toolpath.estimated_build_time_hours} hours
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Main Content */}
          <div style={{ flex: 1, padding: "24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Canvas Viewer */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                padding: "20px",
                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <div style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                <div>
                  <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                    Optimized Density Isosurface & LPBF Scanpath
                  </h4>
                  <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
                    Dark Slate = Solid Load-Bearing Structure • Cyan Lines = Laser Vector Scanpaths • Red Dots = Hatch Turnarounds
                  </span>
                </div>

                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    backgroundColor: "#ecfdf5",
                    color: "#047857",
                  }}
                >
                  DIRECT G-CODE COMPLIANT
                </span>
              </div>

              <canvas
                ref={canvasRef}
                width={720}
                height={360}
                style={{
                  borderRadius: "8px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#f8fafc",
                }}
              />
            </div>

            {/* Optimization Convergence Table */}
            {mdoData && (
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
                    display: "flex",
                    justifyContent: "space-between",
                  }}
                >
                  <span>SIMP Convergence History (Compliance Minimization)</span>
                  <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Solved in {mdoData.optimization.final_metrics.total_solve_time_sec}s
                  </span>
                </div>

                <div style={{ maxHeight: "180px", overflowY: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem", textAlign: "left" }}>
                    <thead>
                      <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>
                        <th style={{ padding: "8px 14px" }}>Iteration</th>
                        <th style={{ padding: "8px 14px" }}>Compliance (Strain Energy)</th>
                        <th style={{ padding: "8px 14px" }}>Volume Fraction</th>
                        <th style={{ padding: "8px 14px" }}>Max Density Change</th>
                        <th style={{ padding: "8px 14px" }}>Convergence Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mdoData.optimization.convergence.map((row) => (
                        <tr key={row.iteration} style={{ borderBottom: "1px solid #f1f5f9" }}>
                          <td style={{ padding: "6px 14px", fontFamily: "monospace", fontWeight: 700 }}>
                            Iter #{row.iteration}
                          </td>
                          <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{row.compliance.toFixed(4)}</td>
                          <td style={{ padding: "6px 14px", fontFamily: "monospace", color: "#0284c7" }}>
                            {(row.volume_fraction * 100).toFixed(1)}%
                          </td>
                          <td style={{ padding: "6px 14px", fontFamily: "monospace" }}>{row.max_change.toFixed(4)}</td>
                          <td style={{ padding: "6px 14px" }}>
                            {row.max_change < 0.02 ? (
                              <span style={{ color: "#059669", fontWeight: 700 }}>CONVERGED</span>
                            ) : (
                              <span style={{ color: "#64748b" }}>OPTIMIZING</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
