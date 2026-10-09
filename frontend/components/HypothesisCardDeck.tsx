"use client";

import React, { useState } from "react";

export interface HypothesisItem {
  hypothesis_id: string;
  statement: string;
  evidence_basis: string;
  assumptions: string[];
  prediction: string;
  candidate_test: string;
  refutation_criteria?: string;
  status: "FORMULATED" | "TESTING" | "SUPPORTED" | "REFUTED" | "ABANDONED" | string;
  is_established_fact: boolean;
  provenance_hash?: string;
}

interface HypothesisCardDeckProps {
  hypotheses: HypothesisItem[];
  apiBase: string;
  onRefresh?: () => void;
  onStageTest?: (hypothesis: HypothesisItem) => void;
}

export const HypothesisCardDeck: React.FC<HypothesisCardDeckProps> = ({
  hypotheses,
  apiBase,
  onRefresh,
  onStageTest,
}) => {
  const [statement, setStatement] = useState("");
  const [evidenceBasis, setEvidenceBasis] = useState("");
  const [prediction, setPrediction] = useState("");
  const [candidateTest, setCandidateTest] = useState("");
  const [refutationCriteria, setRefutationCriteria] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleStatusTransition = async (hypothesisId: string, newStatus: string) => {
    setActionError(null);
    try {
      const res = await fetch(`${apiBase}/api/hypotheses/${hypothesisId}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_status: newStatus,
          reason: `Operator updated hypothesis status to ${newStatus} in Scientific Workspace`,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Transition failed" }));
        throw new Error(err.detail || "Status transition rejected");
      }
      if (onRefresh) onRefresh();
    } catch (e: any) {
      setActionError(e.message || "Failed to update hypothesis status");
    }
  };

  const handleFormulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statement.trim() || !prediction.trim()) return;

    setIsSubmitting(true);
    setActionError(null);
    try {
      const res = await fetch(`${apiBase}/api/hypotheses/formulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          statement,
          evidence_basis: evidenceBasis || "Empirical aerodynamic observations and potential flow theory.",
          assumptions: ["Subsonic incompressible flow", "Turbulent boundary layer attached"],
          prediction,
          candidate_test: candidateTest || "RANS simpleFoam k-omega SST simulation sweep",
          refutation_criteria: refutationCriteria || "Relative discrepancy exceeding 10% or monotonic stall divergence.",
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Formulation failed" }));
        throw new Error(err.detail || "Failed to formulate hypothesis");
      }
      setStatement("");
      setEvidenceBasis("");
      setPrediction("");
      setCandidateTest("");
      setRefutationCriteria("");
      setShowForm(false);
      if (onRefresh) onRefresh();
    } catch (e: any) {
      setActionError(e.message || "Failed to formulate hypothesis");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusClass = (status: string) => {
    switch (status.toUpperCase()) {
      case "SUPPORTED":
        return "status-supported";
      case "REFUTED":
        return "status-refuted";
      case "TESTING":
        return "status-testing";
      default:
        return "status-formulated";
    }
  };

  return (
    <div className="glass-card animate-fade-in" style={{ padding: "16px", marginTop: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent-cyan)" }}>
            SCIENTIFIC HYPOTHESIS ENGINE
          </div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            {hypotheses.length} Active Hypotheses · Explicit Refutation Criteria
          </div>
        </div>

        <button
          className="btn-secondary"
          style={{ fontSize: "0.7rem", padding: "6px 12px" }}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "+ Formulate Hypothesis"}
        </button>
      </div>

      <div className="disclaimer-banner">
        <strong>Absolute Epistemic Rule:</strong> Hypotheses are falsifiable scientific conjectures. They are never represented as established facts (<code style={{ color: "var(--accent-cyan)" }}>is_established_fact: false</code>).
      </div>

      {actionError && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--status-red)", padding: "8px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.72rem", color: "#fca5a5", margin: "8px 0" }}>
          {actionError}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleFormulate} style={{ background: "var(--bg-primary)", padding: "14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", margin: "12px 0" }}>
          <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
            Formulate New Testable Hypothesis
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <input
              type="text"
              className="problem-input"
              style={{ fontSize: "0.74rem", padding: "8px" }}
              placeholder="Hypothesis statement (e.g. Boundary layer remains attached up to alpha = 10 deg)..."
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              required
            />
            <input
              type="text"
              className="problem-input"
              style={{ fontSize: "0.74rem", padding: "8px" }}
              placeholder="Falsifiable numerical prediction (e.g. CL > 0.95, CD < 0.015)..."
              value={prediction}
              onChange={(e) => setPrediction(e.target.value)}
              required
            />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
              <input
                type="text"
                className="problem-input"
                style={{ fontSize: "0.74rem", padding: "8px" }}
                placeholder="Candidate test (e.g. simpleFoam k-omega SST)..."
                value={candidateTest}
                onChange={(e) => setCandidateTest(e.target.value)}
              />
              <input
                type="text"
                className="problem-input"
                style={{ fontSize: "0.74rem", padding: "8px" }}
                placeholder="Refutation criteria (e.g. Stall occurs at alpha < 8 deg)..."
                value={refutationCriteria}
                onChange={(e) => setRefutationCriteria(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
              style={{ alignSelf: "flex-start", marginTop: "4px", fontSize: "0.72rem", padding: "6px 14px" }}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Formulating…" : "Commit Hypothesis →"}
            </button>
          </div>
        </form>
      )}

      {hypotheses.length === 0 ? (
        <div style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)", fontSize: "0.76rem" }}>
          No active hypotheses yet. Formulate one above or launch an aerodynamic inquiry.
        </div>
      ) : (
        <div className="hypothesis-grid">
          {hypotheses.map((h) => (
            <div key={h.hypothesis_id} className="hypothesis-card">
              <div>
                <div className="hypothesis-card-header">
                  <span className="hypothesis-id">{h.hypothesis_id}</span>
                  <span className={`hypothesis-status-badge ${getStatusClass(h.status)}`}>
                    {h.status}
                  </span>
                </div>

                <div className="hypothesis-statement" style={{ marginTop: "6px" }}>
                  {h.statement}
                </div>

                <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div className="hypothesis-detail-row">
                    <span className="hypothesis-detail-label">PREDICTION</span>
                    <span style={{ color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                      {h.prediction}
                    </span>
                  </div>

                  <div className="hypothesis-detail-row">
                    <span className="hypothesis-detail-label">CANDIDATE TEST</span>
                    <span>{h.candidate_test}</span>
                  </div>

                  {h.refutation_criteria && (
                    <div className="hypothesis-detail-row">
                      <span className="hypothesis-detail-label">REFUTATION CRITERIA</span>
                      <span style={{ color: "#fca5a5" }}>{h.refutation_criteria}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="hypothesis-actions">
                {onStageTest && h.status !== "SUPPORTED" && h.status !== "REFUTED" && (
                  <button
                    className="btn-hyp-action"
                    onClick={() => onStageTest(h)}
                    title="Stage experimental test for this hypothesis"
                  >
                    Stage Test
                  </button>
                )}
                {h.status !== "SUPPORTED" && (
                  <button
                    className="btn-hyp-action btn-hyp-support"
                    onClick={() => handleStatusTransition(h.hypothesis_id, "SUPPORTED")}
                  >
                    Support ✓
                  </button>
                )}
                {h.status !== "REFUTED" && (
                  <button
                    className="btn-hyp-action btn-hyp-refute"
                    onClick={() => handleStatusTransition(h.hypothesis_id, "REFUTED")}
                  >
                    Refute ✗
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
