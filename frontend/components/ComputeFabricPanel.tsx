"use client";

import React, { useState, useEffect } from "react";

export interface RunnerCapabilities {
  openfoam_installed: boolean;
  openfoam_version?: string | null;
  openfoam_path?: string | null;
  cpu_count: number;
  ram_gb: number;
  cuda_available: boolean;
  mpi_available: boolean;
  python_version: string;
  allowlisted_executables: string[];
}

export interface RouteDecision {
  destination: "LOCAL" | "COLAB" | "REMOTE_FUTURE" | "UNAVAILABLE";
  decision_explanation: string;
  detected_capabilities: RunnerCapabilities;
  case_requirements: Record<string, any>;
}

interface ComputeFabricPanelProps {
  apiBase: string;
  geometry?: string;
  alphaDeg?: number;
  reynolds?: number;
  mach?: number;
  jobId?: string;
  onLaunchLocal?: () => void;
  onColabLaunch?: () => void;
}

export const ComputeFabricPanel: React.FC<ComputeFabricPanelProps> = ({
  apiBase,
  geometry = "NACA 0012",
  alphaDeg = 4.0,
  reynolds = 3e6,
  mach = 0.15,
  jobId,
  onLaunchLocal,
  onColabLaunch,
}) => {
  const [capabilities, setCapabilities] = useState<RunnerCapabilities | null>(null);
  const [routeDecision, setRouteDecision] = useState<RouteDecision | null>(null);
  const [loading, setLoading] = useState(true);
  const [colabSession, setColabSession] = useState<any | null>(null);
  const [preparingColab, setPreparingColab] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchCapabilitiesAndRoute();
  }, [apiBase, geometry, alphaDeg, reynolds, mach]);

  const fetchCapabilitiesAndRoute = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Fetch Local Runner Capabilities
      const capRes = await fetch(`${apiBase}/api/runner/capabilities`);
      if (capRes.ok) {
        const capData: RunnerCapabilities = await capRes.json();
        setCapabilities(capData);
      }

      // 2. Fetch Compute Router Decision
      const routeRes = await fetch(`${apiBase}/api/compute/route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_requirements: {
            estimated_cells: 50000,
            required_solver: "simpleFoam",
            requires_gpu: false,
          },
        }),
      });

      if (routeRes.ok) {
        const routeData: RouteDecision = await routeRes.json();
        setRouteDecision(routeData);
      }
    } catch (e: any) {
      setErrorMsg(`Compute fabric detection error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePrepareColab = async () => {
    setPreparingColab(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${apiBase}/api/colab/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: jobId || "NACA0012_alpha4_re3m",
          geometry_name: geometry,
          alpha_deg: alphaDeg,
          reynolds,
          mach,
        }),
      });
      if (!res.ok) throw new Error("Failed to prepare Colab session bundle");
      const data = await res.json();
      setColabSession(data);
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setPreparingColab(false);
    }
  };

  return (
    <div className="glass-card animate-fade-in" style={{ padding: "16px", marginTop: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent-cyan)" }}>
            ZERO-COST COMPUTE ROUTER & LOCAL RUNNER
          </div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Deterministic Compute Dispatch · Air-Gapped Local Sandbox or Colab Fallback
          </div>
        </div>

        <button
          className="btn-secondary"
          style={{ fontSize: "0.7rem", padding: "6px 12px" }}
          onClick={fetchCapabilitiesAndRoute}
          disabled={loading}
        >
          {loading ? "Detecting…" : "↻ Refresh Environment"}
        </button>
      </div>

      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--status-red)", padding: "8px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.72rem", color: "#fca5a5", margin: "8px 0" }}>
          {errorMsg}
        </div>
      )}

      {/* Capabilities Overview */}
      <div className="capability-grid" style={{ marginTop: "12px" }}>
        <div className="capability-box">
          <span className="capability-title">LOCAL OPENFOAM</span>
          <span className="capability-status" style={{ color: capabilities?.openfoam_installed ? "var(--status-green)" : "var(--status-amber)" }}>
            {capabilities?.openfoam_installed ? `Installed (${capabilities.openfoam_version || "OK"})` : "Not Detected"}
          </span>
        </div>

        <div className="capability-box">
          <span className="capability-title">CPU CORES</span>
          <span className="capability-status">{capabilities?.cpu_count || 4} Cores</span>
        </div>

        <div className="capability-box">
          <span className="capability-title">SYSTEM MEMORY</span>
          <span className="capability-status">{(capabilities?.ram_gb || 8).toFixed(1)} GB RAM</span>
        </div>

        <div className="capability-box">
          <span className="capability-title">CUDA ACCELERATION</span>
          <span className="capability-status">{capabilities?.cuda_available ? "Available" : "None (CPU RANS)"}</span>
        </div>

        <div className="capability-box">
          <span className="capability-title">COMPUTE ROUTE</span>
          <span className="capability-status" style={{ color: "var(--accent-cyan)" }}>
            {routeDecision?.destination || "COLAB"}
          </span>
        </div>
      </div>

      {/* Router Decision Explanation */}
      {routeDecision && (
        <div className="compute-card" style={{ marginTop: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Deterministic Routing Rationale
            </span>
            <span className="badge badge-info">{routeDecision.destination}</span>
          </div>

          <p style={{ fontSize: "0.74rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
            {routeDecision.decision_explanation}
          </p>

          {/* Action based on destination */}
          {routeDecision.destination === "LOCAL" ? (
            <div style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.2)", padding: "12px", borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontSize: "0.72rem", color: "#34d399", fontWeight: 600 }}>
                ✓ Local OpenFOAM environment verified. Sandboxed runner ready.
              </div>
              <button
                className="btn-primary"
                style={{ marginTop: "8px", fontSize: "0.72rem" }}
                onClick={onLaunchLocal}
              >
                ⚡ RUN LOCALLY IN SANDBOX →
              </button>
            </div>
          ) : (
            <div style={{ background: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.2)", padding: "12px", borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontSize: "0.72rem", color: "#fbbf24", fontWeight: 600 }}>
                Google Colab Fallback Ready (OpenFOAM 10 in Docker)
              </div>
              <p style={{ fontSize: "0.68rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                Zero-cost remote CFD via Google Colab. Packages reproducible notebooks, complete OpenFOAM case decks, and dual manifests.
              </p>

              <div style={{ display: "flex", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
                <button
                  className="btn-primary"
                  style={{ fontSize: "0.72rem", padding: "6px 14px" }}
                  onClick={handlePrepareColab}
                  disabled={preparingColab}
                >
                  {preparingColab ? "Packaging Bundle…" : "📦 Prepare Colab Session Bundle"}
                </button>

                {colabSession?.launch_url && (
                  <a
                    href={colabSession.launch_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-launch"
                    style={{ fontSize: "0.72rem", padding: "6px 14px" }}
                  >
                    OPEN IN GOOGLE COLAB →
                  </a>
                )}

                {colabSession?.notebook_path && (
                  <a
                    href={`${apiBase}/api/colab/download/${colabSession.session_id || "session"}`}
                    download
                    className="btn-secondary"
                    style={{ fontSize: "0.72rem", padding: "6px 14px" }}
                  >
                    Download Notebook (.ipynb)
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Local Runner Executable Allowlist Guarantee */}
          <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "10px", marginTop: "4px" }}>
            <span style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
              Sandboxed Allowlist Model (No Arbitrary Shell Execution):
            </span>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
              {(capabilities?.allowlisted_executables || ["simpleFoam", "blockMesh", "checkMesh", "snappyHexMesh"]).map((exe) => (
                <code key={exe} style={{ fontSize: "0.62rem", background: "var(--bg-primary)", padding: "2px 6px", borderRadius: "3px", border: "1px solid var(--border-color)", color: "var(--accent-cyan)" }}>
                  {exe}
                </code>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
