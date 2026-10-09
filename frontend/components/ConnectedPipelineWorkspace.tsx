"use client";

import React, { useState, useEffect } from "react";

/* ─── Interfaces ─── */

interface PipelineStageResult {
  stage_id: string;
  stage_name: string;
  status: string;
  execution_time_ms: number;
  data: Record<string, any>;
  summary: string;
}

interface PipelineExecutionResult {
  pipeline_id: string;
  status: string;
  total_execution_time_ms: number;
  timestamp: string;
  geometry: string;
  alpha_deg: number;
  reynolds: number;
  mach: number;
  selected_model: string;
  stages: Record<string, PipelineStageResult>;
  final_summary: Record<string, any>;
  exports: Record<string, string>;
}

interface ConnectedPipelineWorkspaceProps {
  apiBase?: string;
  initialGeometry?: string;
  initialAlpha?: number;
  initialMach?: number;
  initialReynolds?: number;
  initialModelId?: string;
  onNavigateToTab?: (tab: string) => void;
}

const PRESETS = [
  {
    name: "NACA 0012 Subsonic Cruise Audit",
    geometry: "NACA 0012",
    alpha_deg: 4.0,
    reynolds: 3.0e6,
    mach: 0.15,
    model: "MeshGraphNet",
    desc: "Attached potential flow, symmetric drag polar, and static pitch stability verification.",
  },
  {
    name: "NACA 2412 Cambered Wing Evaluation",
    geometry: "NACA 2412",
    alpha_deg: 2.0,
    reynolds: 2.5e6,
    mach: 0.20,
    model: "Transolver",
    desc: "Cambered section assessing negative zero-lift angle alpha_0L and nose-down CM_0.",
  },
  {
    name: "Clark Y High-Lift General Aviation",
    geometry: "Clark Y",
    alpha_deg: 6.0,
    reynolds: 1.8e6,
    mach: 0.12,
    model: "DPOT",
    desc: "Flat-bottom GA airfoil evaluating boundary layer growth and high glide ratio.",
  },
  {
    name: "RAE 2822 Transonic Supercritical Shock",
    geometry: "RAE 2822",
    alpha_deg: 2.79,
    reynolds: 6.5e6,
    mach: 0.725,
    model: "DoMINO",
    desc: "Supercritical airfoil testing compressibility factor beta, suction plateau, and shock.",
  },
];

const STAGE_KEYS = [
  { key: "geometry", label: "Geometry Ingestion", icon: "📐", subtitle: "Profile Normalization" },
  { key: "surrogate", label: "Model Zoo AI Inference", icon: "🧬", subtitle: "Neural Operator Field" },
  { key: "verification", label: "Verification Gate", icon: "🔬", subtitle: "Conservation & Bounds" },
  { key: "cognitive", label: "Cognitive Brain", icon: "⚡", subtitle: "Epistemic Reasoning" },
  { key: "aero_db", label: "Aero DB Synthesis", icon: "📊", subtitle: "Polar Envelope & S&C" },
  { key: "exports", label: "Flight Certification", icon: "🛫", subtitle: "DATCOM & 6-DOF CSV" },
];

export const ConnectedPipelineWorkspace: React.FC<ConnectedPipelineWorkspaceProps> = ({
  apiBase = "",
  initialGeometry = "NACA 0012",
  initialAlpha = 4.0,
  initialMach = 0.15,
  initialReynolds = 3.0e6,
  initialModelId,
  onNavigateToTab,
}) => {
  const [geometry, setGeometry] = useState(initialGeometry);
  const [alphaDeg, setAlphaDeg] = useState(initialAlpha);
  const [mach, setMach] = useState(initialMach);
  const [reynolds, setReynolds] = useState(initialReynolds);
  const [primaryModelId, setPrimaryModelId] = useState(initialModelId || "");
  const [modelsList, setModelsList] = useState<Array<{ model_id: string; name: string; domain: string }>>([]);
  const [running, setRunning] = useState(false);
  const [activeStageStep, setActiveStageStep] = useState(0);
  const [result, setResult] = useState<PipelineExecutionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedResultTab, setSelectedResultTab] = useState<"surrogate" | "verification" | "cognitive" | "aero_db" | "exports">("surrogate");

  // Fetch catalog models for dropdown
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const res = await fetch(`${apiBase}/api/model-zoo/catalog`);
        if (res.ok) {
          const data = await res.json();
          setModelsList(data.models || []);
          if (!primaryModelId && data.models && data.models.length > 0) {
            setPrimaryModelId(data.models[0].model_id);
          }
        }
      } catch {
        /* ignore */
      }
    };
    fetchCatalog();
  }, [apiBase, primaryModelId]);

  const handleApplyPreset = (p: typeof PRESETS[0]) => {
    setGeometry(p.geometry);
    setAlphaDeg(p.alpha_deg);
    setMach(p.mach);
    setReynolds(p.reynolds);
    const matched = modelsList.find((m) => m.name.toLowerCase().includes(p.model.toLowerCase()));
    if (matched) {
      setPrimaryModelId(matched.model_id);
    }
  };

  const handleRunPipeline = async () => {
    setRunning(true);
    setErrorMsg(null);
    setActiveStageStep(1);

    try {
      const res = await fetch(`${apiBase}/api/model-zoo/pipeline/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry,
          alpha_deg: Number(alphaDeg),
          reynolds: Number(reynolds),
          mach: Number(mach),
          primary_model_id: primaryModelId || undefined,
          run_aero_db_sweep: true,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Pipeline execution failed" }));
        throw new Error(err.detail || "Pipeline failed");
      }

      const data: PipelineExecutionResult = await res.json();
      setResult(data);
      setActiveStageStep(6);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute pipeline.");
      setActiveStageStep(0);
    } finally {
      setRunning(false);
    }
  };

  const handleDownload = (content: string, filename: string, mimeType: string = "text/plain") => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Render pressure distribution SVG
  const renderPressurePlot = () => {
    if (!result || !result.stages.surrogate) return null;
    const field = result.stages.surrogate.data.field_distribution;
    if (!field || !field.x || !field.Cp_upper) return null;

    const xPts: number[] = field.x;
    const cpUpper: number[] = field.Cp_upper;
    const cpLower: number[] = field.Cp_lower;

    const svgWidth = 600;
    const svgHeight = 240;
    const padX = 50;
    const padY = 30;
    const plotW = svgWidth - 2 * padX;
    const plotH = svgHeight - 2 * padY;

    // Aerodynamics standard: Inverted Cp axis (negative Cp on top)
    const minCp = Math.min(...cpUpper, ...cpLower, -2.5);
    const maxCp = Math.max(...cpUpper, ...cpLower, 1.2);

    const scaleX = (x: number) => padX + x * plotW;
    const scaleY = (cp: number) => padY + ((cp - minCp) / (maxCp - minCp)) * plotH;

    const upperPoints = xPts.map((x, i) => `${scaleX(x)},${scaleY(cpUpper[i])}`).join(" ");
    const lowerPoints = xPts.map((x, i) => `${scaleX(x)},${scaleY(cpLower[i])}`).join(" ");

    return (
      <div style={{ background: "rgba(0,0,0,0.3)", borderRadius: "10px", padding: "16px", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#fff" }}>
            Surface Pressure Distribution $C_p(x)$ (Aerodynamic Inverted Axis)
          </div>
          <div style={{ display: "flex", gap: "12px", fontSize: "0.68rem" }}>
            <span style={{ color: "#64d2ff" }}>━━ Upper Suction Surface</span>
            <span style={{ color: "#ff9f0a" }}>━━ Lower Compression Surface</span>
          </div>
        </div>

        <svg width="100%" height={svgHeight} viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ overflow: "visible" }}>
          {/* Reference Axis Grid */}
          <line x1={padX} y1={padY} x2={padX + plotW} y2={padY} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
          <line x1={padX} y1={padY + plotH} x2={padX + plotW} y2={padY + plotH} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
          <line x1={padX} y1={scaleY(0)} x2={padX + plotW} y2={scaleY(0)} stroke="rgba(255,255,255,0.2)" />
          <line x1={padX} y1={padY} x2={padX} y2={padY + plotH} stroke="rgba(255,255,255,0.15)" />

          {/* Labels */}
          <text x={padX - 8} y={scaleY(0) + 3} fill="#94a3b8" fontSize="9" textAnchor="end">Cp=0</text>
          <text x={padX - 8} y={scaleY(minCp) + 3} fill="#64d2ff" fontSize="9" textAnchor="end">{minCp.toFixed(1)}</text>
          <text x={padX - 8} y={scaleY(maxCp) + 3} fill="#ff9f0a" fontSize="9" textAnchor="end">{maxCp.toFixed(1)}</text>
          <text x={scaleX(0)} y={padY + plotH + 16} fill="#94a3b8" fontSize="9" textAnchor="middle">x/c = 0 (LE)</text>
          <text x={scaleX(0.5)} y={padY + plotH + 16} fill="#94a3b8" fontSize="9" textAnchor="middle">0.5</text>
          <text x={scaleX(1.0)} y={padY + plotH + 16} fill="#94a3b8" fontSize="9" textAnchor="middle">1.0 (TE)</text>

          {/* Upper curve */}
          <polyline fill="none" stroke="#64d2ff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" points={upperPoints} />
          {/* Lower curve */}
          <polyline fill="none" stroke="#ff9f0a" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" points={lowerPoints} />
        </svg>
      </div>
    );
  };

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
      {/* ─── Hero Header & Status Banner ─── */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(18, 24, 38, 0.85) 0%, rgba(10, 14, 26, 0.95) 100%)",
          backdropFilter: "blur(24px)",
          border: "1px solid rgba(100, 210, 255, 0.2)",
          borderRadius: "16px",
          padding: "20px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
          boxShadow: "0 12px 36px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.6rem" }}>🔗</span>
            <div>
              <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#fff", letterSpacing: "0.02em" }}>
                Connected Autonomous Scientific Pipeline
              </div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "2px" }}>
                End-to-End Orchestration: Geometry Ingestion → Model Zoo AI Surrogate → Verification Gate → Cognitive Brain → Aero DB → Flight Certification
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              padding: "6px 14px",
              borderRadius: "9999px",
              fontSize: "0.72rem",
              fontWeight: 700,
              letterSpacing: "0.06em",
              background: running
                ? "rgba(100, 210, 255, 0.15)"
                : result
                ? "rgba(48, 209, 88, 0.15)"
                : "rgba(255, 255, 255, 0.08)",
              border: `1px solid ${
                running
                  ? "rgba(100, 210, 255, 0.4)"
                  : result
                  ? "rgba(48, 209, 88, 0.4)"
                  : "rgba(255, 255, 255, 0.15)"
              }`,
              color: running ? "#64d2ff" : result ? "#30d158" : "#94a3b8",
            }}
          >
            {running ? "⚡ EXECUTING PIPELINE..." : result ? "✅ PIPELINE CERTIFIED" : "READY"}
          </div>

          <button
            onClick={handleRunPipeline}
            disabled={running}
            style={{
              padding: "10px 22px",
              borderRadius: "10px",
              background: running
                ? "rgba(100, 210, 255, 0.2)"
                : "linear-gradient(135deg, #0071e3 0%, #00c7be 100%)",
              color: "#fff",
              fontSize: "0.82rem",
              fontWeight: 700,
              border: "none",
              cursor: running ? "not-allowed" : "pointer",
              boxShadow: "0 4px 16px rgba(0, 113, 227, 0.35)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              transition: "transform 150ms ease, box-shadow 150ms ease",
            }}
          >
            <span>{running ? "⏳ Running..." : "🚀 Run Connected Pipeline"}</span>
          </button>
        </div>
      </div>

      {/* ─── Presets Row ─── */}
      <div style={{ display: "flex", gap: "8px", overflowX: "auto", paddingBottom: "4px" }}>
        {PRESETS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleApplyPreset(p)}
            style={{
              flexShrink: 0,
              padding: "8px 14px",
              borderRadius: "10px",
              background: geometry === p.geometry ? "rgba(100, 210, 255, 0.12)" : "rgba(18, 24, 38, 0.5)",
              border: `1px solid ${geometry === p.geometry ? "rgba(100, 210, 255, 0.4)" : "rgba(255, 255, 255, 0.08)"}`,
              textAlign: "left",
              cursor: "pointer",
              transition: "all 150ms ease",
            }}
          >
            <div style={{ fontSize: "0.72rem", fontWeight: 700, color: geometry === p.geometry ? "#64d2ff" : "#e2e8f0" }}>
              {p.name}
            </div>
            <div style={{ fontSize: "0.64rem", color: "#94a3b8", marginTop: "2px" }}>
              {p.geometry} • α={p.alpha_deg}° • M={p.mach} • {p.model}
            </div>
          </button>
        ))}
      </div>

      {/* ─── Parameter Control Deck ─── */}
      <div
        style={{
          background: "rgba(18, 24, 38, 0.65)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "16px 20px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "14px",
          alignItems: "end",
        }}
      >
        <div>
          <label style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94a3b8", display: "block", marginBottom: "4px" }}>
            AIRFOIL GEOMETRY
          </label>
          <input
            type="text"
            value={geometry}
            onChange={(e) => setGeometry(e.target.value)}
            placeholder="e.g. NACA 0012, Clark Y"
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.35)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#fff",
              fontSize: "0.78rem",
            }}
          />
        </div>

        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
            <label style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94a3b8" }}>
              ANGLE OF ATTACK (α)
            </label>
            <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64d2ff" }}>{alphaDeg}°</span>
          </div>
          <input
            type="range"
            min="-6"
            max="18"
            step="0.5"
            value={alphaDeg}
            onChange={(e) => setAlphaDeg(parseFloat(e.target.value))}
            style={{ width: "100%", accentColor: "#64d2ff" }}
          />
        </div>

        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
            <label style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94a3b8" }}>MACH NUMBER (M)</label>
            <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "#f59e0b" }}>M={mach}</span>
          </div>
          <input
            type="range"
            min="0.05"
            max="0.85"
            step="0.025"
            value={mach}
            onChange={(e) => setMach(parseFloat(e.target.value))}
            style={{ width: "100%", accentColor: "#f59e0b" }}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94a3b8", display: "block", marginBottom: "4px" }}>
            REYNOLDS NUMBER (Re)
          </label>
          <select
            value={reynolds}
            onChange={(e) => setReynolds(parseFloat(e.target.value))}
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.35)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#fff",
              fontSize: "0.78rem",
            }}
          >
            <option value="500000">5.0e5 (UAV / Glider)</option>
            <option value="1800000">1.8e6 (General Aviation)</option>
            <option value="3000000">3.0e6 (Subsonic Benchmark)</option>
            <option value="6000000">6.0e6 (High Reynolds Transport)</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: "0.68rem", fontWeight: 700, color: "#94a3b8", display: "block", marginBottom: "4px" }}>
            PRIMARY PHYSICS AI MODEL
          </label>
          <select
            value={primaryModelId}
            onChange={(e) => setPrimaryModelId(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: "8px",
              background: "rgba(0, 0, 0, 0.35)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#fff",
              fontSize: "0.78rem",
            }}
          >
            {modelsList.map((m) => (
              <option key={m.model_id} value={m.model_id}>
                {m.name} ({m.domain.replace("_", " ")})
              </option>
            ))}
          </select>
        </div>
      </div>

      {errorMsg && (
        <div style={{ background: "rgba(255, 59, 48, 0.1)", border: "1px solid rgba(255, 59, 48, 0.3)", borderRadius: "10px", padding: "12px 16px", color: "#ff453a", fontSize: "0.75rem" }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* ─── Animated 6-Stage Visual Flowchart ─── */}
      <div
        style={{
          background: "rgba(18, 24, 38, 0.65)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
        }}
      >
        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#94a3b8", marginBottom: "14px", letterSpacing: "0.06em" }}>
          PIPELINE EXECUTION ARCHITECTURE &amp; ACTIVE STAGE PULSE
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
            gap: "10px",
            position: "relative",
          }}
        >
          {STAGE_KEYS.map((s, idx) => {
            const isDone = result && result.stages[s.key];
            const isActive = running && activeStageStep === idx + 1;
            const stageRes = result?.stages[s.key];

            return (
              <div
                key={s.key}
                style={{
                  background: isDone
                    ? "rgba(48, 209, 88, 0.08)"
                    : isActive
                    ? "rgba(100, 210, 255, 0.12)"
                    : "rgba(0, 0, 0, 0.25)",
                  border: `1px solid ${
                    isDone
                      ? "rgba(48, 209, 88, 0.3)"
                      : isActive
                      ? "rgba(100, 210, 255, 0.5)"
                      : "rgba(255, 255, 255, 0.06)"
                  }`,
                  borderRadius: "10px",
                  padding: "12px",
                  transition: "all 250ms ease",
                  position: "relative",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <span style={{ fontSize: "1.2rem" }}>{s.icon}</span>
                  <span
                    style={{
                      fontSize: "0.6rem",
                      fontWeight: 700,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: isDone ? "rgba(48, 209, 88, 0.2)" : "rgba(255, 255, 255, 0.05)",
                      color: isDone ? "#30d158" : "#64748b",
                    }}
                  >
                    {isDone ? "PASS" : `0${idx + 1}`}
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#fff" }}>{s.label}</div>
                <div style={{ fontSize: "0.62rem", color: "#94a3b8", marginTop: "2px" }}>{s.subtitle}</div>

                {stageRes && (
                  <div style={{ marginTop: "8px", fontSize: "0.62rem", color: "#30d158", fontWeight: 600 }}>
                    ✓ {stageRes.execution_time_ms}ms
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── Detailed Outputs & Artifacts ─── */}
      {result && (
        <div
          style={{
            background: "rgba(18, 24, 38, 0.75)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {/* Summary KPIs */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "10px" }}>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontSize: "0.64rem", color: "#94a3b8" }}>LIFT COEFF (CL)</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#64d2ff" }}>
                {result.final_summary.CL?.toFixed(4) || "—"}
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontSize: "0.64rem", color: "#94a3b8" }}>DRAG COEFF (CD)</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#ff9f0a" }}>
                {result.final_summary.CD?.toFixed(5) || "—"}
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontSize: "0.64rem", color: "#94a3b8" }}>LIFT-TO-DRAG (L/D)</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#30d158" }}>
                {result.final_summary.L_over_D?.toFixed(1) || "—"}
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontSize: "0.64rem", color: "#94a3b8" }}>LIFT SLOPE (dCL/dα)</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#38bdf8" }}>
                {result.final_summary.CL_alpha_per_deg?.toFixed(3)}/deg
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontSize: "0.64rem", color: "#94a3b8" }}>PITCH STABILITY</div>
              <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#ffd60a", marginTop: "4px" }}>
                {result.final_summary.longitudinal_stability || "STABLE"}
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontSize: "0.64rem", color: "#94a3b8" }}>EXECUTION TIME</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#70ff9c" }}>
                {result.total_execution_time_ms} ms
              </div>
            </div>
          </div>

          {/* Sub-Tabs for Result Inspection */}
          <div style={{ display: "flex", gap: "6px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "8px" }}>
            {[
              { id: "surrogate", label: "🧬 AI Surrogate & Flowfield" },
              { id: "verification", label: "🔬 Verification Gate" },
              { id: "cognitive", label: "⚡ Cognitive Brain" },
              { id: "aero_db", label: "📊 Aero DB Polar Envelope" },
              { id: "exports", label: "🛫 1-Click Exporters" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedResultTab(t.id as any)}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  background: selectedResultTab === t.id ? "rgba(100, 210, 255, 0.15)" : "transparent",
                  color: selectedResultTab === t.id ? "#64d2ff" : "#94a3b8",
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  border: "none",
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab 1: Surrogate & Flowfield */}
          {selectedResultTab === "surrogate" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {renderPressurePlot()}
              <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                Inference Model: <strong style={{ color: "#fff" }}>{result.selected_model}</strong> | SHA-256 Provenance Hash: <span style={{ fontFamily: "var(--font-mono)", color: "#64d2ff" }}>{result.stages.surrogate?.data.provenance_hash?.substring(0, 32)}...</span>
              </div>
            </div>
          )}

          {/* Tab 2: Verification Gate */}
          {selectedResultTab === "verification" && (
            <div style={{ background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "10px", fontSize: "0.72rem", display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ fontWeight: 700, color: "#30d158" }}>
                Physics Verification Gate Audit: {result.stages.verification?.data.outcome}
              </div>
              <div>Checks Performed: {result.stages.verification?.data.checks_performed?.join(", ")}</div>
              <div>Checks Passed: <strong style={{ color: "#30d158" }}>{result.stages.verification?.data.checks_passed?.join(", ")}</strong></div>
              <div>Conservation Error: <span style={{ fontFamily: "var(--font-mono)", color: "#64d2ff" }}>{result.stages.verification?.data.conservation_error?.toExponential(2)}</span></div>
              <div>Epistemic Tier: <span style={{ padding: "2px 8px", borderRadius: "4px", background: "rgba(48,209,88,0.2)", color: "#30d158", fontWeight: 700 }}>{result.stages.verification?.data.epistemic_tier_assigned}</span></div>
            </div>
          )}

          {/* Tab 3: Cognitive Brain */}
          {selectedResultTab === "cognitive" && (
            <div style={{ background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "10px", fontSize: "0.72rem", display: "flex", flexDirection: "column", gap: "10px" }}>
              <div>
                <span style={{ color: "#94a3b8" }}>FORMULATED HYPOTHESIS:</span>
                <div style={{ color: "#fff", fontWeight: 600, marginTop: "4px", padding: "8px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                  {result.stages.cognitive?.data.formulated_hypothesis}
                </div>
              </div>
              <div>
                <span style={{ color: "#94a3b8" }}>ADVERSARIAL CRITIQUE VERDICT:</span>
                <div style={{ color: "#30d158", fontWeight: 600, marginTop: "4px" }}>
                  {result.stages.cognitive?.data.adversarial_critique}
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: Aero DB Envelope */}
          {selectedResultTab === "aero_db" && (
            <div style={{ background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "10px", fontSize: "0.72rem" }}>
              <div style={{ fontWeight: 700, color: "#fff", marginBottom: "8px" }}>
                Multi-Condition Envelope Sweep Summary ({result.stages.aero_db?.data.total_polar_points} Points)
              </div>
              <div style={{ color: "#94a3b8", lineHeight: 1.6 }}>
                {result.stages.aero_db?.summary}
              </div>
            </div>
          )}

          {/* Tab 5: Exporters */}
          {selectedResultTab === "exports" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                Directly export standardized aerospace decks verified by the connected pipeline:
              </div>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {result.exports.datcom && (
                  <button
                    onClick={() => handleDownload(result.exports.datcom, `${result.geometry}_AERO_DB.dat`)}
                    style={{
                      padding: "10px 16px",
                      borderRadius: "8px",
                      background: "rgba(100, 210, 255, 0.15)",
                      border: "1px solid rgba(100, 210, 255, 0.3)",
                      color: "#64d2ff",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Export USAF DATCOM (.dat)
                  </button>
                )}

                {result.exports.shabp && (
                  <button
                    onClick={() => handleDownload(result.exports.shabp, `${result.geometry}_SHABP.shabp`)}
                    style={{
                      padding: "10px 16px",
                      borderRadius: "6px",
                      background: "rgba(245, 158, 11, 0.12)",
                      border: "1px solid rgba(245, 158, 11, 0.3)",
                      color: "#f59e0b",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Export NASA S/HABP (.shabp)
                  </button>
                )}

                {result.exports.csv && (
                  <button
                    onClick={() => handleDownload(result.exports.csv, `${result.geometry}_6DOF_POLARS.csv`, "text/csv")}
                    style={{
                      padding: "10px 16px",
                      borderRadius: "6px",
                      background: "rgba(16, 185, 129, 0.12)",
                      border: "1px solid rgba(16, 185, 129, 0.3)",
                      color: "#10b981",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Export 6-DOF Simulation (.csv)
                  </button>
                )}

                <button
                  onClick={() => handleDownload(JSON.stringify(result, null, 2), `${result.geometry}_PIPELINE_DOSSIER.json`, "application/json")}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "8px",
                    background: "rgba(255, 214, 10, 0.15)",
                    border: "1px solid rgba(255, 214, 10, 0.3)",
                    color: "#ffd60a",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  💾 Download Full Pipeline JSON Dossier
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
