"use client";

import React, { useState, useEffect, useCallback } from "react";

/* ─── Types ─── */

interface ModelIOSchema {
  input_type: string;
  input_dimensions: string;
  input_fields: string[];
  output_fields: string[];
  output_type: string;
  mesh_type: string;
  temporal_support: boolean;
  max_resolution?: string | null;
}

interface BenchmarkResult {
  benchmark_name: string;
  dataset: string;
  metric_name: string;
  metric_value: number;
  unit: string;
}

interface PhysicsAIModel {
  model_id: string;
  name: string;
  version: string;
  description: string;
  domain: string;
  architecture: string;
  maturity: string;
  paper_title: string;
  paper_url: string;
  repository_url: string;
  checkpoint_source: string;
  checkpoint_url: string;
  license: string;
  authors: string[];
  io_schema: ModelIOSchema;
  supported_environments: string[];
  parameter_count?: string | null;
  inference_time_ms?: number | null;
  gpu_memory_gb?: number | null;
  applicable_physics: string[];
  conservation_laws_tested: string[];
  validation_datasets: string[];
  known_limitations: string[];
  benchmark_results: BenchmarkResult[];
  is_available: boolean;
  availability_diagnostic: string;
  tags: string[];
  provenance_hash: string;
}

interface ModelZooCatalog {
  total: number;
  models: PhysicsAIModel[];
  domains_summary: Record<string, number>;
  architectures_summary: Record<string, number>;
}

interface ModelZooExplorerProps {
  apiBase?: string;
  onLaunchPipeline?: (modelId: string, geometry: string, alpha: number, mach: number, reynolds: number) => void;
}

/* ─── Constants ─── */

const DOMAIN_LABELS: Record<string, { emoji: string; label: string; color: string }> = {
  CFD_FLUID_DYNAMICS: { emoji: "CFD", label: "CFD / Fluid Dynamics", color: "#38bdf8" },
  POROUS_MEDIA_PDE: { emoji: "PDE", label: "Porous Media / PDEs", color: "#60a5fa" },
  STRUCTURAL_MECHANICS: { emoji: "FEA", label: "Structural Mechanics", color: "#f59e0b" },
  MATERIALS_MOLECULAR: { emoji: "MAT", label: "Materials / Molecular", color: "#10b981" },
  CONSERVATION_MULTIPHYSICS: { emoji: "MULTI", label: "Conservation / Multi-Physics", color: "#fbbf24" },
};

const MATURITY_BADGES: Record<string, { label: string; cls: string }> = {
  RESEARCH_PROTOTYPE: { label: "Research", cls: "mat-research" },
  PUBLISHED_CHECKPOINT: { label: "Published", cls: "mat-published" },
  VALIDATED_BENCHMARK: { label: "Validated", cls: "mat-validated" },
  PRODUCTION_READY: { label: "Production", cls: "mat-production" },
};

const ARCH_SHORT: Record<string, string> = {
  GRAPH_NEURAL_NETWORK: "GNN",
  FOURIER_NEURAL_OPERATOR: "FNO",
  TRANSFORMER: "Transformer",
  EQUIVARIANT_MESSAGE_PASSING: "E(3)-MPNN",
  DEEP_EQUILIBRIUM: "DEQ",
  CONVOLUTIONAL: "CNN",
  HYBRID_PHYSICS_ML: "Hybrid",
  PARTICLE_FINITE_ELEMENT: "PFEM",
  ATTENTION_OPERATOR: "Attn-Op",
  HYENA_OPERATOR: "Hyena",
  MULTI_GRID_OPERATOR: "MGNO",
  LATENT_GRAPH_OPERATOR: "LGNO",
};

/* ─── Component ─── */

export const ModelZooExplorer: React.FC<ModelZooExplorerProps> = ({
  apiBase = "",
  onLaunchPipeline,
}) => {
  const [catalog, setCatalog] = useState<ModelZooCatalog | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDomain, setActiveDomain] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedModelId, setExpandedModelId] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<Record<string, any> | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [stats, setStats] = useState<Record<string, any> | null>(null);

  // Model Runner State
  const [activeRunnerModelId, setActiveRunnerModelId] = useState<string | null>(null);
  const [runnerGeometry, setRunnerGeometry] = useState("NACA 0012");
  const [runnerAlpha, setRunnerAlpha] = useState(4.0);
  const [runnerMach, setRunnerMach] = useState(0.15);
  const [runnerReynolds, setRunnerReynolds] = useState(3.0e6);
  const [runningInference, setRunningInference] = useState(false);
  const [inferenceResult, setInferenceResult] = useState<Record<string, any> | null>(null);

  const handleExecuteInference = async (modelId: string) => {
    setRunningInference(true);
    setInferenceResult(null);
    try {
      const res = await fetch(`${apiBase}/api/model-zoo/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: modelId,
          geometry: runnerGeometry,
          alpha_deg: Number(runnerAlpha),
          mach: Number(runnerMach),
          reynolds: Number(runnerReynolds),
          resolution: 64,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setInferenceResult(data);
      }
    } catch {
      /* ignore */
    } finally {
      setRunningInference(false);
    }
  };

  const fetchCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (activeDomain) params.set("domain", activeDomain);
      if (searchQuery.trim()) params.set("search", searchQuery.trim());

      const res = await fetch(`${apiBase}/api/model-zoo/catalog?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to fetch model catalog.");
      const data: ModelZooCatalog = await res.json();
      setCatalog(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiBase, activeDomain, searchQuery]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/api/model-zoo/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {
      /* ignore */
    }
  }, [apiBase]);

  useEffect(() => {
    fetchCatalog();
    fetchStats();
  }, [fetchCatalog, fetchStats]);

  const handleVerify = async (modelId: string) => {
    setVerifying(true);
    setVerifyResult(null);
    try {
      const res = await fetch(`${apiBase}/api/model-zoo/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: modelId,
          predictions: { CL: 0.485, CD: 0.0092, pressure: 101325.0 },
          conservation_residuals: { mass: 1.2e-5, momentum: 3.4e-4 },
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setVerifyResult(data);
      }
    } catch {
      /* ignore */
    } finally {
      setVerifying(false);
    }
  };

  const filteredModels = catalog?.models || [];

  /* ─── Render ─── */

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

      {/* ─── Header Stats Bar ─── */}
      <div style={{
        background: "rgba(18, 24, 38, 0.65)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "14px",
        padding: "16px 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "12px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "1.4rem" }}>🧬</span>
          <div>
            <div style={{ fontSize: "1rem", fontWeight: 700, color: "#fff", letterSpacing: "0.04em" }}>
              Physics AI Model Zoo
            </div>
            <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginTop: "2px" }}>
              Unified discovery, validation &amp; benchmarking of pre-trained Physics AI models
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "18px", flexWrap: "wrap", fontSize: "0.72rem" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "#64d2ff" }}>
              {stats?.total_models || filteredModels.length}
            </div>
            <div style={{ color: "#94a3b8" }}>Models</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "#30d158" }}>
              {stats ? Object.keys(stats.domains || {}).length : 0}
            </div>
            <div style={{ color: "#94a3b8" }}>Domains</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "#f59e0b" }}>
              {stats ? Object.keys(stats.architectures || {}).length : 0}
            </div>
            <div style={{ color: "#94a3b8" }}>Architectures</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "#ffd60a" }}>
              {stats?.total_benchmarks || 0}
            </div>
            <div style={{ color: "#94a3b8" }}>Benchmarks</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "#ff9f0a" }}>
              {stats?.production_ready_count || 0}
            </div>
            <div style={{ color: "#94a3b8" }}>Production</div>
          </div>
        </div>
      </div>

      {/* ─── Domain Filter Pills ─── */}
      <div style={{
        display: "flex",
        gap: "8px",
        flexWrap: "wrap",
        alignItems: "center",
      }}>
        <button
          onClick={() => setActiveDomain(null)}
          style={{
            padding: "6px 14px",
            borderRadius: "9999px",
            border: `1px solid ${!activeDomain ? "rgba(100, 210, 255, 0.5)" : "rgba(255, 255, 255, 0.1)"}`,
            background: !activeDomain ? "rgba(100, 210, 255, 0.12)" : "rgba(18, 24, 38, 0.5)",
            color: !activeDomain ? "#64d2ff" : "#94a3b8",
            fontSize: "0.72rem",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 200ms ease",
          }}
        >
          All Domains
        </button>
        {Object.entries(DOMAIN_LABELS).map(([key, { emoji, label, color }]) => (
          <button
            key={key}
            onClick={() => setActiveDomain(activeDomain === key ? null : key)}
            style={{
              padding: "6px 14px",
              borderRadius: "9999px",
              border: `1px solid ${activeDomain === key ? color + "80" : "rgba(255, 255, 255, 0.1)"}`,
              background: activeDomain === key ? color + "18" : "rgba(18, 24, 38, 0.5)",
              color: activeDomain === key ? color : "#94a3b8",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 200ms ease",
            }}
          >
            {emoji} {label}
            {catalog?.domains_summary?.[key] ? (
              <span style={{ marginLeft: "6px", opacity: 0.7 }}>({catalog.domains_summary[key]})</span>
            ) : null}
          </button>
        ))}
      </div>

      {/* ─── Search Bar ─── */}
      <div style={{ position: "relative" }}>
        <input
          type="text"
          placeholder="Search models by name, description, or tag..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchCatalog()}
          style={{
            width: "100%",
            padding: "10px 16px 10px 38px",
            borderRadius: "10px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            background: "rgba(18, 24, 38, 0.6)",
            color: "#fff",
            fontSize: "0.82rem",
            outline: "none",
            transition: "border-color 200ms ease",
          }}
        />
        <span style={{
          position: "absolute",
          left: "12px",
          top: "50%",
          transform: "translateY(-50%)",
          fontSize: "0.9rem",
          opacity: 0.5,
        }}>🔍</span>
      </div>

      {/* ─── Error / Loading ─── */}
      {error && (
        <div style={{
          padding: "10px 16px",
          borderRadius: "8px",
          background: "rgba(255, 59, 48, 0.1)",
          border: "1px solid rgba(255, 59, 48, 0.3)",
          color: "#ff6b6b",
          fontSize: "0.78rem",
        }}>
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div style={{
          textAlign: "center",
          padding: "30px",
          color: "#94a3b8",
          fontSize: "0.82rem",
        }}>
          Loading model catalog...
        </div>
      )}

      {/* ─── Model Cards Grid ─── */}
      {!loading && filteredModels.length > 0 && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: "12px",
        }}>
          {filteredModels.map((model) => {
            const domainInfo = DOMAIN_LABELS[model.domain] || { emoji: "📦", label: model.domain, color: "#94a3b8" };
            const maturityInfo = MATURITY_BADGES[model.maturity] || { label: model.maturity, cls: "" };
            const archShort = ARCH_SHORT[model.architecture] || model.architecture;
            const isExpanded = expandedModelId === model.model_id;

            return (
              <div
                key={model.model_id}
                onClick={() => setExpandedModelId(isExpanded ? null : model.model_id)}
                style={{
                  background: isExpanded
                    ? "rgba(18, 24, 38, 0.85)"
                    : "rgba(18, 24, 38, 0.55)",
                  border: `1px solid ${isExpanded ? domainInfo.color + "40" : "rgba(255, 255, 255, 0.06)"}`,
                  borderRadius: "12px",
                  padding: "16px",
                  cursor: "pointer",
                  transition: "all 250ms cubic-bezier(0.16, 1, 0.3, 1)",
                  gridColumn: isExpanded ? "1 / -1" : undefined,
                }}
              >
                {/* ─ Model Header ─ */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span style={{ fontSize: "1.1rem" }}>{domainInfo.emoji}</span>
                      <span style={{
                        fontSize: "0.92rem",
                        fontWeight: 700,
                        color: "#fff",
                        letterSpacing: "0.02em",
                      }}>
                        {model.name}
                      </span>
                    </div>
                    <div style={{
                      fontSize: "0.72rem",
                      color: "#94a3b8",
                      lineHeight: 1.45,
                      display: "-webkit-box",
                      WebkitLineClamp: isExpanded ? 999 : 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}>
                      {model.description}
                    </div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px", flexShrink: 0 }}>
                    <span style={{
                      padding: "2px 8px",
                      borderRadius: "6px",
                      fontSize: "0.65rem",
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      background: model.maturity === "PRODUCTION_READY" ? "rgba(48, 209, 88, 0.15)"
                        : model.maturity === "VALIDATED_BENCHMARK" ? "rgba(100, 210, 255, 0.15)"
                          : model.maturity === "PUBLISHED_CHECKPOINT" ? "rgba(255, 159, 10, 0.15)"
                            : "rgba(148, 163, 184, 0.15)",
                      color: model.maturity === "PRODUCTION_READY" ? "#30d158"
                        : model.maturity === "VALIDATED_BENCHMARK" ? "#64d2ff"
                          : model.maturity === "PUBLISHED_CHECKPOINT" ? "#ff9f0a"
                            : "#94a3b8",
                      border: `1px solid ${model.maturity === "PRODUCTION_READY" ? "rgba(48, 209, 88, 0.3)"
                        : model.maturity === "VALIDATED_BENCHMARK" ? "rgba(100, 210, 255, 0.3)"
                          : model.maturity === "PUBLISHED_CHECKPOINT" ? "rgba(255, 159, 10, 0.3)"
                            : "rgba(148, 163, 184, 0.2)"}`,
                    }}>
                      {maturityInfo.label}
                    </span>
                    <span style={{
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.62rem",
                      fontWeight: 600,
                      background: "rgba(245, 158, 11, 0.1)",
                      color: "#f59e0b",
                      border: "1px solid rgba(245, 158, 11, 0.25)",
                    }}>
                      {archShort}
                    </span>
                  </div>
                </div>

                {/* ─ Quick Stats ─ */}
                <div style={{
                  display: "flex",
                  gap: "12px",
                  marginTop: "10px",
                  flexWrap: "wrap",
                  fontSize: "0.68rem",
                  color: "#94a3b8",
                }}>
                  {model.parameter_count && (
                    <span>📐 {model.parameter_count} params</span>
                  )}
                  {model.inference_time_ms && (
                    <span>⚡ {model.inference_time_ms}ms</span>
                  )}
                  {model.gpu_memory_gb && (
                    <span>🔧 {model.gpu_memory_gb}GB GPU</span>
                  )}
                  <span style={{ color: domainInfo.color }}>
                    {domainInfo.label}
                  </span>
                </div>

                {/* ─ Tags ─ */}
                {model.tags.length > 0 && (
                  <div style={{
                    display: "flex",
                    gap: "4px",
                    marginTop: "8px",
                    flexWrap: "wrap",
                  }}>
                    {model.tags.slice(0, isExpanded ? 20 : 4).map((tag) => (
                      <span key={tag} style={{
                        padding: "2px 6px",
                        borderRadius: "4px",
                        fontSize: "0.6rem",
                        background: "rgba(255, 255, 255, 0.04)",
                        color: "#64748b",
                        border: "1px solid rgba(255, 255, 255, 0.06)",
                      }}>
                        {tag}
                      </span>
                    ))}
                    {!isExpanded && model.tags.length > 4 && (
                      <span style={{ fontSize: "0.6rem", color: "#64748b" }}>
                        +{model.tags.length - 4} more
                      </span>
                    )}
                  </div>
                )}

                {/* ─ Expanded Details ─ */}
                {isExpanded && (
                  <div style={{ marginTop: "16px", borderTop: "1px solid rgba(255, 255, 255, 0.06)", paddingTop: "14px" }}>
                    <div style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                      gap: "14px",
                    }}>
                      {/* I/O Schema */}
                      <div style={{ background: "rgba(0, 0, 0, 0.2)", borderRadius: "8px", padding: "12px" }}>
                        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#64d2ff", marginBottom: "8px", letterSpacing: "0.06em" }}>
                          I/O SPECIFICATION
                        </div>
                        <div style={{ fontSize: "0.68rem", color: "#94a3b8", display: "flex", flexDirection: "column", gap: "4px" }}>
                          <div>Input: <strong style={{ color: "#d1d5db" }}>{model.io_schema.input_type}</strong> ({model.io_schema.input_dimensions})</div>
                          <div>Mesh: <strong style={{ color: "#d1d5db" }}>{model.io_schema.mesh_type}</strong></div>
                          <div>Temporal: <strong style={{ color: model.io_schema.temporal_support ? "#30d158" : "#ff453a" }}>
                            {model.io_schema.temporal_support ? "Yes" : "No"}
                          </strong></div>
                          <div>Inputs: {model.io_schema.input_fields.join(", ")}</div>
                          <div>Outputs: {model.io_schema.output_fields.join(", ")}</div>
                        </div>
                      </div>

                      {/* Physics Coverage */}
                      <div style={{ background: "rgba(0, 0, 0, 0.2)", borderRadius: "8px", padding: "12px" }}>
                        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#30d158", marginBottom: "8px", letterSpacing: "0.06em" }}>
                          PHYSICS COVERAGE
                        </div>
                        <div style={{ fontSize: "0.68rem", color: "#94a3b8", display: "flex", flexDirection: "column", gap: "4px" }}>
                          <div>Applicable: {model.applicable_physics.join(", ")}</div>
                          {model.conservation_laws_tested.length > 0 && (
                            <div>Conservation: <strong style={{ color: "#70ff9c" }}>
                              {model.conservation_laws_tested.join(", ")}
                            </strong></div>
                          )}
                          <div>Validation: {model.validation_datasets.join(", ")}</div>
                        </div>
                      </div>

                      {/* Benchmark Results */}
                      {model.benchmark_results.length > 0 && (
                        <div style={{ background: "rgba(0, 0, 0, 0.2)", borderRadius: "8px", padding: "12px" }}>
                          <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#ffd60a", marginBottom: "8px", letterSpacing: "0.06em" }}>
                            BENCHMARK RESULTS
                          </div>
                          {model.benchmark_results.map((b, i) => (
                            <div key={i} style={{ fontSize: "0.68rem", color: "#94a3b8", marginBottom: "4px" }}>
                              <strong style={{ color: "#d1d5db" }}>{b.benchmark_name}</strong>
                              <span style={{ marginLeft: "6px" }}>
                                {b.metric_name}: <strong style={{ color: "#64d2ff" }}>{b.metric_value}</strong>
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Provenance & Links */}
                      <div style={{ background: "rgba(0, 0, 0, 0.2)", borderRadius: "8px", padding: "12px" }}>
                        <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#ff9f0a", marginBottom: "8px", letterSpacing: "0.06em" }}>
                          PROVENANCE & ACCESS
                        </div>
                        <div style={{ fontSize: "0.68rem", color: "#94a3b8", display: "flex", flexDirection: "column", gap: "4px" }}>
                          {model.paper_title && <div>Paper: {model.paper_title}</div>}
                          <div>License: <strong style={{ color: "#d1d5db" }}>{model.license}</strong></div>
                          <div>Source: {model.checkpoint_source}</div>
                          <div>Environments: {model.supported_environments.join(", ")}</div>
                          <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", color: "#475569", wordBreak: "break-all", marginTop: "4px" }}>
                            SHA-256: {model.provenance_hash.substring(0, 32)}...
                          </div>
                        </div>
                      </div>

                      {/* Limitations */}
                      {model.known_limitations.length > 0 && (
                        <div style={{ background: "rgba(0, 0, 0, 0.2)", borderRadius: "8px", padding: "12px" }}>
                          <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#ff453a", marginBottom: "8px", letterSpacing: "0.06em" }}>
                            KNOWN LIMITATIONS
                          </div>
                          <ul style={{ fontSize: "0.68rem", color: "#94a3b8", paddingLeft: "16px", margin: 0 }}>
                            {model.known_limitations.map((l, i) => (
                              <li key={i} style={{ marginBottom: "3px" }}>{l}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* ─ Action Buttons ─ */}
                    <div style={{
                      display: "flex",
                      gap: "8px",
                      marginTop: "14px",
                      flexWrap: "wrap",
                    }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (activeRunnerModelId === model.model_id) {
                            setActiveRunnerModelId(null);
                          } else {
                            setActiveRunnerModelId(model.model_id);
                            setInferenceResult(null);
                          }
                        }}
                        style={{
                          padding: "7px 16px",
                          borderRadius: "8px",
                          border: "1px solid rgba(100, 210, 255, 0.4)",
                          background: activeRunnerModelId === model.model_id ? "rgba(100, 210, 255, 0.25)" : "rgba(100, 210, 255, 0.12)",
                          color: "#64d2ff",
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          cursor: "pointer",
                          transition: "all 200ms ease",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <span>⚡</span> {activeRunnerModelId === model.model_id ? "Close Model Runner" : "Run Model Inference"}
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleVerify(model.model_id); }}
                        disabled={verifying}
                        style={{
                          padding: "7px 16px",
                          borderRadius: "8px",
                          border: "1px solid rgba(48, 209, 88, 0.3)",
                          background: "rgba(48, 209, 88, 0.1)",
                          color: "#30d158",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                          cursor: "pointer",
                          transition: "all 200ms ease",
                        }}
                      >
                        {verifying ? "Verifying..." : "🔬 Run Verification Gate"}
                      </button>
                      {model.repository_url && (
                        <button
                          onClick={(e) => { e.stopPropagation(); window.open(model.repository_url, "_blank"); }}
                          style={{
                            padding: "7px 16px",
                            borderRadius: "8px",
                            border: "1px solid rgba(148, 163, 184, 0.2)",
                            background: "rgba(148, 163, 184, 0.05)",
                            color: "#94a3b8",
                            fontSize: "0.72rem",
                            fontWeight: 600,
                            cursor: "pointer",
                            transition: "all 200ms ease",
                          }}
                        >
                          📂 Repository
                        </button>
                      )}
                      {model.paper_url && (
                        <button
                          onClick={(e) => { e.stopPropagation(); window.open(model.paper_url, "_blank"); }}
                          style={{
                            padding: "7px 16px",
                            borderRadius: "8px",
                            border: "1px solid rgba(100, 210, 255, 0.2)",
                            background: "rgba(100, 210, 255, 0.05)",
                            color: "#64d2ff",
                            fontSize: "0.72rem",
                            fontWeight: 600,
                            cursor: "pointer",
                            transition: "all 200ms ease",
                          }}
                        >
                          📄 Paper
                        </button>
                      )}
                    </div>

                    {/* ─ Interactive Local Inference Console ─ */}
                    {activeRunnerModelId === model.model_id && (
                      <div
                        onClick={(e) => e.stopPropagation()}
                        style={{
                          marginTop: "14px",
                          background: "rgba(10, 14, 26, 0.75)",
                          border: "1px solid rgba(100, 210, 255, 0.25)",
                          borderRadius: "10px",
                          padding: "16px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "12px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#64d2ff" }}>
                            ⚡ Local Inference Console — {model.name}
                          </div>
                          <span style={{ fontSize: "0.65rem", color: "#94a3b8" }}>
                            Arch: {ARCH_SHORT[model.architecture] || model.architecture}
                          </span>
                        </div>

                        {/* Parameter Controls */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "10px" }}>
                          <div>
                            <label style={{ fontSize: "0.64rem", color: "#94a3b8", display: "block", marginBottom: "3px" }}>Geometry</label>
                            <input
                              type="text"
                              value={runnerGeometry}
                              onChange={(e) => setRunnerGeometry(e.target.value)}
                              style={{ width: "100%", padding: "6px 8px", borderRadius: "6px", background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "0.72rem" }}
                            />
                            <div style={{ display: "flex", gap: "4px", marginTop: "4px" }}>
                              {["NACA 0012", "NACA 2412", "Clark Y"].map((g) => (
                                <button
                                  key={g}
                                  onClick={() => setRunnerGeometry(g)}
                                  style={{ padding: "2px 6px", fontSize: "0.58rem", borderRadius: "4px", background: "rgba(255,255,255,0.05)", border: "none", color: "#94a3b8", cursor: "pointer" }}
                                >
                                  {g.replace("NACA ", "")}
                                </button>
                              ))}
                            </div>
                          </div>

                          <div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <label style={{ fontSize: "0.64rem", color: "#94a3b8" }}>Alpha (α)</label>
                              <span style={{ fontSize: "0.68rem", color: "#64d2ff", fontWeight: 700 }}>{runnerAlpha}°</span>
                            </div>
                            <input
                              type="range"
                              min="-6"
                              max="18"
                              step="0.5"
                              value={runnerAlpha}
                              onChange={(e) => setRunnerAlpha(parseFloat(e.target.value))}
                              style={{ width: "100%", accentColor: "#64d2ff", marginTop: "4px" }}
                            />
                          </div>

                          <div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <label style={{ fontSize: "0.64rem", color: "#94a3b8" }}>Mach (M)</label>
                              <span style={{ fontSize: "0.68rem", color: "#f59e0b", fontWeight: 700 }}>{runnerMach}</span>
                            </div>
                            <input
                              type="range"
                              min="0.05"
                              max="0.80"
                              step="0.05"
                              value={runnerMach}
                              onChange={(e) => setRunnerMach(parseFloat(e.target.value))}
                              style={{ width: "100%", accentColor: "#f59e0b", marginTop: "4px" }}
                            />
                          </div>

                          <div>
                            <label style={{ fontSize: "0.64rem", color: "#94a3b8", display: "block", marginBottom: "3px" }}>Reynolds (Re)</label>
                            <select
                              value={runnerReynolds}
                              onChange={(e) => setRunnerReynolds(parseFloat(e.target.value))}
                              style={{ width: "100%", padding: "6px 8px", borderRadius: "6px", background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "0.72rem" }}
                            >
                              <option value="500000">5.0e5 (UAV)</option>
                              <option value="1800000">1.8e6 (GA)</option>
                              <option value="3000000">3.0e6 (Cruise)</option>
                              <option value="6000000">6.0e6 (Transport)</option>
                            </select>
                          </div>
                        </div>

                        {/* Execute Button */}
                        <div>
                          <button
                            onClick={() => handleExecuteInference(model.model_id)}
                            disabled={runningInference}
                            style={{
                              padding: "8px 18px",
                              borderRadius: "6px",
                              background: runningInference ? "rgba(100, 210, 255, 0.2)" : "linear-gradient(135deg, #0071e3 0%, #00c7be 100%)",
                              border: "none",
                              color: "#fff",
                              fontSize: "0.74rem",
                              fontWeight: 700,
                              cursor: runningInference ? "not-allowed" : "pointer",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "6px",
                            }}
                          >
                            <span>{runningInference ? "⏳ Computing..." : "▶ Compute Physics with " + model.name}</span>
                          </button>
                        </div>

                        {/* Inference Output Cards */}
                        {inferenceResult && (
                          <div style={{ marginTop: "6px", display: "flex", flexDirection: "column", gap: "10px" }}>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(90px, 1fr))", gap: "8px" }}>
                              <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
                                <div style={{ fontSize: "0.6rem", color: "#94a3b8" }}>LIFT (CL)</div>
                                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#64d2ff" }}>
                                  {inferenceResult.predictions?.CL?.toFixed(4) || "—"}
                                </div>
                              </div>
                              <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
                                <div style={{ fontSize: "0.6rem", color: "#94a3b8" }}>DRAG (CD)</div>
                                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#ff9f0a" }}>
                                  {inferenceResult.predictions?.CD?.toFixed(5) || "—"}
                                </div>
                              </div>
                              <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
                                <div style={{ fontSize: "0.6rem", color: "#94a3b8" }}>L/D RATIO</div>
                                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#30d158" }}>
                                  {inferenceResult.predictions?.L_over_D?.toFixed(1) || "—"}
                                </div>
                              </div>
                              <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
                                <div style={{ fontSize: "0.6rem", color: "#94a3b8" }}>SPEED</div>
                                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#70ff9c" }}>
                                  {inferenceResult.execution_time_ms} ms
                                </div>
                              </div>
                              <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
                                <div style={{ fontSize: "0.6rem", color: "#94a3b8" }}>EPISTEMIC</div>
                                <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "#30d158", marginTop: "4px" }}>
                                  {inferenceResult.epistemic_tier}
                                </div>
                              </div>
                            </div>

                            {/* Verification Summary */}
                            {inferenceResult.verification_report && (
                              <div style={{ fontSize: "0.65rem", color: "#94a3b8", display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(48,209,88,0.06)", padding: "6px 10px", borderRadius: "6px", border: "1px solid rgba(48,209,88,0.2)" }}>
                                <span>Verification Gate: <strong style={{ color: "#30d158" }}>{inferenceResult.verification_report.outcome}</strong> ({inferenceResult.verification_report.checks_passed?.length}/{inferenceResult.verification_report.checks_performed?.length} passed)</span>
                                {onLaunchPipeline && (
                                  <button
                                    onClick={() => onLaunchPipeline(model.model_id, runnerGeometry, runnerAlpha, runnerMach, runnerReynolds)}
                                    style={{
                                      padding: "4px 10px",
                                      borderRadius: "4px",
                                      background: "rgba(100, 210, 255, 0.2)",
                                      border: "1px solid rgba(100, 210, 255, 0.4)",
                                      color: "#64d2ff",
                                      fontSize: "0.62rem",
                                      fontWeight: 700,
                                      cursor: "pointer",
                                    }}
                                  >
                                    🔗 Send to Connected Pipeline →
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* ─ Verification Result ─ */}
                    {verifyResult && verifyResult.model_id === model.model_id && (
                      <div style={{
                        marginTop: "12px",
                        padding: "12px",
                        borderRadius: "8px",
                        background: verifyResult.outcome === "PASSED"
                          ? "rgba(48, 209, 88, 0.08)"
                          : verifyResult.outcome === "WARNING_PARTIAL"
                            ? "rgba(255, 214, 10, 0.08)"
                            : "rgba(255, 59, 48, 0.08)",
                        border: `1px solid ${verifyResult.outcome === "PASSED"
                          ? "rgba(48, 209, 88, 0.2)"
                          : verifyResult.outcome === "WARNING_PARTIAL"
                            ? "rgba(255, 214, 10, 0.2)"
                            : "rgba(255, 59, 48, 0.2)"}`,
                      }}>
                        <div style={{
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          color: verifyResult.outcome === "PASSED" ? "#30d158"
                            : verifyResult.outcome === "WARNING_PARTIAL" ? "#ffd60a"
                              : "#ff453a",
                          marginBottom: "6px",
                          letterSpacing: "0.06em",
                        }}>
                          VERIFICATION GATE: {verifyResult.outcome}
                        </div>
                        <div style={{ fontSize: "0.68rem", color: "#94a3b8" }}>
                          <div>Checks: {verifyResult.checks_passed?.length || 0}/{verifyResult.checks_performed?.length || 0} passed</div>
                          <div>Epistemic tier: <strong style={{ color: "#64d2ff" }}>{verifyResult.epistemic_tier_assigned}</strong></div>
                          {verifyResult.conservation_error != null && (
                            <div>Conservation error: <strong>{verifyResult.conservation_error.toExponential(2)}</strong></div>
                          )}
                          {verifyResult.physical_bounds_violated?.length > 0 && (
                            <div style={{ color: "#ff6b6b", marginTop: "4px" }}>
                              Violations: {verifyResult.physical_bounds_violated.join(", ")}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ─── Empty State ─── */}
      {!loading && filteredModels.length === 0 && !error && (
        <div style={{
          textAlign: "center",
          padding: "40px",
          color: "#94a3b8",
          fontSize: "0.82rem",
          background: "rgba(18, 24, 38, 0.4)",
          borderRadius: "12px",
          border: "1px solid rgba(255, 255, 255, 0.06)",
        }}>
          <span style={{ fontSize: "2rem", display: "block", marginBottom: "10px" }}>🧬</span>
          No models found matching your filters.
        </div>
      )}
    </div>
  );
};
