"use client";

import React, { useState } from "react";

export interface CostEstimate {
  estimated_cpu_core_hours: number;
  estimated_wall_clock_seconds: number;
  requires_gpu: boolean;
  notes?: string;
}

export interface CandidateExperiment {
  experiment_id: string;
  question: string;
  parameters: {
    geometry?: string;
    alpha_deg?: number;
    reynolds?: number;
    mach?: number;
    [key: string]: any;
  };
  method: string;
  expected_information: string;
  cost_estimate: CostEstimate;
  dependencies: string[];
  rationale: string;
  heuristic_score: number;
  optimality_disclaimer?: string;
  status: "PROPOSED" | "STAGED" | "RUNNING" | "COMPLETED" | string;
  provenance_hash?: string;
}

interface ExperimentPlannerPanelProps {
  experiments: CandidateExperiment[];
  apiBase: string;
  geometry?: string;
  alphaDeg?: number;
  reynolds?: number;
  mach?: number;
  onRefresh?: () => void;
  onStageExperiment?: (exp: CandidateExperiment) => void;
}

export const ExperimentPlannerPanel: React.FC<ExperimentPlannerPanelProps> = ({
  experiments,
  apiBase,
  geometry = "NACA 0012",
  alphaDeg = 4.0,
  reynolds = 3e6,
  mach = 0.15,
  onRefresh,
  onStageExperiment,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [stagingId, setStagingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleGenerateExperiments = async () => {
    setIsGenerating(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase}/api/planner/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry,
          current_alpha_deg: alphaDeg,
          reynolds,
          mach,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Generation failed" }));
        throw new Error(err.detail || "Failed to generate candidates");
      }
      setMessage("Generated new heuristic-ranked candidate experiments.");
      if (onRefresh) onRefresh();
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleStage = async (exp: CandidateExperiment) => {
    setStagingId(exp.experiment_id);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase}/api/planner/stage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experiment_id: exp.experiment_id }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Staging failed" }));
        throw new Error(err.detail || "Staging rejected");
      }
      setMessage(`Experiment ${exp.experiment_id} successfully staged into execution queue.`);
      if (onStageExperiment) onStageExperiment(exp);
      if (onRefresh) onRefresh();
    } catch (e: any) {
      setMessage(`Staging error: ${e.message}`);
    } finally {
      setStagingId(null);
    }
  };

  return (
    <div className="glass-card animate-fade-in" style={{ padding: "16px", marginTop: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent-indigo)" }}>
            TRANSPARENT EXPERIMENT PLANNER
          </div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            {experiments.length} Candidate Experiments · Heuristic Priority Ranking
          </div>
        </div>

        <button
          className="btn-secondary"
          style={{ fontSize: "0.7rem", padding: "6px 12px" }}
          onClick={handleGenerateExperiments}
          disabled={isGenerating}
        >
          {isGenerating ? "Synthesizing Plan…" : "⚡ Propose Candidate Sweep"}
        </button>
      </div>

      <div className="disclaimer-banner">
        <strong>Anti-Optimality Doctrine:</strong> Experiment candidates are prioritized using transparent aerodynamic heuristics (information gain, parameter coverage). AASI explicitly disclaims mathematical optimality.
      </div>

      {message && (
        <div style={{ background: "rgba(59, 130, 246, 0.1)", border: "1px solid var(--accent-blue)", padding: "8px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.72rem", color: "#93c5fd", margin: "8px 0" }}>
          {message}
        </div>
      )}

      {experiments.length === 0 ? (
        <div style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)", fontSize: "0.76rem" }}>
          No candidate experiments planned yet. Click "Propose Candidate Sweep" or initiate an inquiry.
        </div>
      ) : (
        <div className="planner-grid">
          {experiments.map((exp) => (
            <div key={exp.experiment_id} className="experiment-card">
              <div>
                <div className="experiment-header">
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "var(--accent-cyan)", fontWeight: 600 }}>
                    {exp.experiment_id}
                  </span>
                  <span className="score-badge">
                    Score: {exp.heuristic_score.toFixed(1)} / 10.0
                  </span>
                </div>

                <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "6px" }}>
                  {exp.question}
                </div>

                <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                  <strong>Method: </strong>{exp.method}
                </div>

                <div style={{ fontSize: "0.7rem", color: "var(--accent-teal)", marginTop: "4px" }}>
                  <strong>Gain: </strong>{exp.expected_information}
                </div>

                <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: "4px", fontStyle: "italic" }}>
                  {exp.rationale}
                </div>

                {/* Cost Estimate Grid */}
                <div className="cost-grid" style={{ marginTop: "10px" }}>
                  <div>
                    <span className="cost-label">CPU CORE-HRS</span>
                    <span className="cost-val">{exp.cost_estimate.estimated_cpu_core_hours.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="cost-label">WALL CLOCK</span>
                    <span className="cost-val">~{Math.round(exp.cost_estimate.estimated_wall_clock_seconds / 60)} min</span>
                  </div>
                  <div>
                    <span className="cost-label">GPU REQ</span>
                    <span className="cost-val">{exp.cost_estimate.requires_gpu ? "YES" : "NO"}</span>
                  </div>
                </div>
              </div>

              <div style={{ marginTop: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="badge badge-neutral" style={{ fontSize: "0.6rem" }}>
                  Status: {exp.status}
                </span>

                <button
                  className="btn-primary"
                  style={{ fontSize: "0.68rem", padding: "5px 12px" }}
                  onClick={() => handleStage(exp)}
                  disabled={stagingId === exp.experiment_id || exp.status === "STAGED"}
                >
                  {stagingId === exp.experiment_id ? "Staging…" : exp.status === "STAGED" ? "✓ Staged" : "Stage Experiment →"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
