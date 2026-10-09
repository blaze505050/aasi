"use client";

import React, { useState, useEffect } from "react";

export interface SurrogatePredictionResult {
  geometry: string;
  alpha_deg: number;
  reynolds: number;
  mach: number;
  predictions: {
    CL: number;
    CD: number;
    CM: number;
  };
  in_domain: boolean;
  extrapolation_warnings: string[];
  envelope: {
    alpha_min: number;
    alpha_max: number;
    reynolds_min: number;
    reynolds_max: number;
    mach_min: number;
    mach_max: number;
  };
  disclaimer: string;
}

export interface ActiveLearningSuggestion {
  geometry: string;
  alpha_deg: number;
  reynolds: number;
  mach: number;
  priority_score: number;
  rationale: string;
}

interface SurrogateInferencePanelProps {
  apiBase: string;
  onSelectCondition?: (alpha: number, re: number) => void;
}

export const SurrogateInferencePanel: React.FC<SurrogateInferencePanelProps> = ({
  apiBase,
  onSelectCondition,
}) => {
  const [alpha, setAlpha] = useState(4.0);
  const [reynolds, setReynolds] = useState(3000000);
  const [mach, setMach] = useState(0.15);
  const [geometry, setGeometry] = useState("NACA 0012");
  const [prediction, setPrediction] = useState<SurrogatePredictionResult | null>(null);
  const [suggestions, setSuggestions] = useState<ActiveLearningSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchActiveLearning();
  }, [apiBase]);

  const fetchActiveLearning = async () => {
    try {
      const res = await fetch(`${apiBase}/api/surrogate/active-learning?n_suggestions=3`);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
      }
    } catch {
      /* ignore */
    }
  };

  const handlePredict = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${apiBase}/api/surrogate/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry,
          alpha_deg: alpha,
          reynolds,
          mach,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Inference failed" }));
        throw new Error(err.detail || "Prediction failed");
      }
      const data = await res.json();
      setPrediction(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute surrogate inference");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card animate-fade-in" style={{ padding: "16px", marginTop: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent-teal)" }}>
            SCIKIT-LEARN AERO SURROGATE ENGINE
          </div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Multi-Fidelity Approximation · In-Domain Verification & Active Learning Suggestions
          </div>
        </div>

        <button
          className="btn-secondary"
          style={{ fontSize: "0.7rem", padding: "6px 12px" }}
          onClick={() => handlePredict()}
          disabled={loading}
        >
          {loading ? "Computing…" : "⚡ Run Inference"}
        </button>
      </div>

      <div className="disclaimer-banner">
        <strong>Strict Anti-CFD Label Rule:</strong> Surrogate outputs are fast statistical approximations trained on verified datasets. They are strictly prohibited from ever being labeled as CFD. Extrapolations outside the training envelope trigger explicit warnings.
      </div>

      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--status-red)", padding: "8px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.72rem", color: "#fca5a5", margin: "8px 0" }}>
          {errorMsg}
        </div>
      )}

      {/* Input Controls */}
      <form onSubmit={handlePredict} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "10px", margin: "14px 0" }}>
        <div>
          <label style={{ fontSize: "0.62rem", color: "var(--text-muted)", display: "block", marginBottom: "2px" }}>GEOMETRY</label>
          <input
            type="text"
            className="problem-input"
            style={{ fontSize: "0.74rem", padding: "6px 8px" }}
            value={geometry}
            onChange={(e) => setGeometry(e.target.value)}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.62rem", color: "var(--text-muted)", display: "block", marginBottom: "2px" }}>ANGLE OF ATTACK (°)</label>
          <input
            type="number"
            step="0.5"
            className="problem-input"
            style={{ fontSize: "0.74rem", padding: "6px 8px" }}
            value={alpha}
            onChange={(e) => setAlpha(parseFloat(e.target.value) || 0)}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.62rem", color: "var(--text-muted)", display: "block", marginBottom: "2px" }}>REYNOLDS NUMBER</label>
          <input
            type="number"
            className="problem-input"
            style={{ fontSize: "0.74rem", padding: "6px 8px" }}
            value={reynolds}
            onChange={(e) => setReynolds(parseFloat(e.target.value) || 1e6)}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.62rem", color: "var(--text-muted)", display: "block", marginBottom: "2px" }}>MACH NUMBER</label>
          <input
            type="number"
            step="0.01"
            className="problem-input"
            style={{ fontSize: "0.74rem", padding: "6px 8px" }}
            value={mach}
            onChange={(e) => setMach(parseFloat(e.target.value) || 0.15)}
          />
        </div>
      </form>

      {/* Prediction Results */}
      {prediction && (
        <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "14px", marginTop: "10px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Surrogate Multi-Fidelity Estimate
            </span>
            <span className={`badge ${prediction.in_domain ? "badge-success" : "badge-neutral"}`} style={{ fontSize: "0.62rem" }}>
              {prediction.in_domain ? "✓ IN TRAINING ENVELOPE" : "⚠ EXTRAPOLATION"}
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", margin: "12px 0", textAlign: "center" }}>
            <div style={{ background: "var(--bg-primary)", padding: "10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)" }}>
              <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", display: "block" }}>LIFT (CL)</span>
              <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                {prediction.predictions.CL.toFixed(4)}
              </span>
            </div>

            <div style={{ background: "var(--bg-primary)", padding: "10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)" }}>
              <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", display: "block" }}>DRAG (CD)</span>
              <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--status-amber)" }}>
                {prediction.predictions.CD.toFixed(4)}
              </span>
            </div>

            <div style={{ background: "var(--bg-primary)", padding: "10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)" }}>
              <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", display: "block" }}>PITCHING MOMENT (CM)</span>
              <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-indigo)" }}>
                {prediction.predictions.CM.toFixed(4)}
              </span>
            </div>
          </div>

          {prediction.extrapolation_warnings && prediction.extrapolation_warnings.length > 0 && (
            <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid var(--status-amber)", padding: "8px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.68rem", color: "#fcd34d" }}>
              <strong>Extrapolation Alert: </strong>
              {prediction.extrapolation_warnings.join("; ")}
            </div>
          )}
        </div>
      )}

      {/* Active Learning Suggestions */}
      {suggestions.length > 0 && (
        <div style={{ marginTop: "16px" }}>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent-cyan)", marginBottom: "8px" }}>
            Active Learning Optimal Sampling Points
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "8px" }}>
            {suggestions.map((s, i) => (
              <div
                key={i}
                style={{ background: "var(--bg-primary)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", padding: "10px", cursor: "pointer" }}
                onClick={() => {
                  setAlpha(s.alpha_deg);
                  setReynolds(s.reynolds);
                  if (onSelectCondition) onSelectCondition(s.alpha_deg, s.reynolds);
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", fontWeight: 600 }}>
                  <span style={{ color: "var(--text-primary)" }}>α = {s.alpha_deg}°, Re = {s.reynolds.toExponential(1)}</span>
                  <span style={{ color: "var(--accent-cyan)" }}>Score: {s.priority_score.toFixed(1)}</span>
                </div>
                <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  {s.rationale}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
