"use client";

import React from "react";

export interface TimelineTransition {
  from_state: string;
  to_state: string;
  timestamp: string;
  trigger: string;
  detail?: string;
  transition_hash: string;
}

export interface ExecutionTimelineProps {
  currentState: string;
  history: TimelineTransition[];
  coarseState?: string;
  progressPct?: number;
}

const ALL_STATES = [
  { key: "RECEIVED", label: "Received", color: "#94a3b8" },
  { key: "PLANNED", label: "Planned", color: "#38bdf8" },
  { key: "KNOWLEDGE_SEARCH", label: "Knowledge Search", color: "#60a5fa" },
  { key: "FIDELITY_DECISION", label: "Fidelity Decision", color: "#fbbf24" },
  { key: "CASE_GENERATED", label: "Case Staged", color: "#34d399" },
  { key: "PREFLIGHT", label: "Preflight Audit", color: "#2dd4bf" },
  { key: "BACKEND_SELECTED", label: "Backend Selected", color: "#60a5fa" },
  { key: "JOB_STAGED", label: "Job Staged", color: "#f59e0b" },
  { key: "USER_AUTHORIZATION_REQUIRED", label: "User Authorization", color: "#f97316" },
  { key: "REMOTE_EXECUTING", label: "Remote Executing", color: "#f59e0b" },
  { key: "RESULTS_AVAILABLE", label: "Results Available", color: "#38bdf8" },
  { key: "INGESTING", label: "Ingesting", color: "#06b6d4" },
  { key: "VERIFYING", label: "Verifying", color: "#0ea5e9" },
  { key: "SCIENTIFIC_VALIDATION", label: "Scientific Validation", color: "#10b981" },
  { key: "KNOWLEDGE_COMMIT", label: "Knowledge Commit", color: "#059669" },
  { key: "REPORT_GENERATED", label: "Report Generated", color: "#14b8a6" },
  { key: "COMPLETE", label: "Complete", color: "#22c55e" },
];

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({
  currentState,
  history,
  coarseState,
  progressPct = 0,
}) => {
  const currentIndex = ALL_STATES.findIndex((s) => s.key === currentState);

  const getEpistemicBadgeColor = (state: string) => {
    if (state.includes("VERIFIED") || state === "COMPLETE") return "#22c55e";
    if (state.includes("USER_AUTHORIZATION")) return "#f97316";
    if (state.includes("FAILED") || state.includes("ERROR")) return "#ef4444";
    if (state.includes("EXECUTING")) return "#f59e0b";
    return "#38bdf8";
  };

  return (
    <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "8px", padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
        <div>
          <span style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "1px", color: "#38bdf8", fontWeight: "bold" }}>
            AASI DETERMINISTIC STATE TRACE
          </span>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 800, color: "#fff", margin: "2px 0 0 0" }}>
            Autonomous Execution Timeline (17 Formal Milestones)
          </h3>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {coarseState && (
            <span style={{
              fontSize: "0.7rem",
              padding: "4px 8px",
              borderRadius: "4px",
              fontWeight: "bold",
              background: coarseState === "RUNNING" ? "rgba(245, 158, 11, 0.2)" : "rgba(16, 185, 129, 0.2)",
              color: coarseState === "RUNNING" ? "#fcd34d" : "#a7f3d0",
              border: `1px solid ${coarseState === "RUNNING" ? "#f59e0b" : "#10b981"}`,
            }}>
              STATUS: {coarseState}
            </span>
          )}
          <span style={{
            fontSize: "0.75rem",
            padding: "4px 10px",
            borderRadius: "6px",
            fontWeight: "bold",
            background: "rgba(56, 189, 248, 0.15)",
            border: `1px solid ${getEpistemicBadgeColor(currentState)}`,
            color: "#bae6fd",
          }}>
            STATE: {currentState} ({progressPct}%)
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ width: "100%", background: "#1e293b", height: "6px", borderRadius: "3px", overflow: "hidden", marginBottom: "16px" }}>
        <div style={{
          width: `${Math.max(5, progressPct)}%`,
          height: "100%",
          background: "linear-gradient(90deg, #0284c7, #10b981)",
          transition: "width 0.4s ease",
        }} />
      </div>

      {/* Milestone Badges */}
      <div style={{ display: "flex", gap: "6px", overflowX: "auto", paddingBottom: "8px" }}>
        {ALL_STATES.map((state, idx) => {
          const isPassed = idx < currentIndex;
          const isCurrent = idx === currentIndex;

          return (
            <div
              key={state.key}
              style={{
                flex: "0 0 auto",
                padding: "6px 10px",
                borderRadius: "4px",
                fontSize: "0.65rem",
                fontWeight: "bold",
                background: isCurrent
                  ? "rgba(56, 189, 248, 0.25)"
                  : isPassed
                  ? "rgba(16, 185, 129, 0.15)"
                  : "#1e293b",
                border: isCurrent
                  ? "1px solid #38bdf8"
                  : isPassed
                  ? "1px solid rgba(16, 185, 129, 0.4)"
                  : "1px solid #334155",
                color: isCurrent ? "#38bdf8" : isPassed ? "#a7f3d0" : "#64748b",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span>{isPassed ? "✓" : isCurrent ? "⟳" : "○"}</span>
              <span>{state.label}</span>
            </div>
          );
        })}
      </div>

      {/* Cryptographic Transition History Stream */}
      {history && history.length > 0 && (
        <div style={{ marginTop: "14px", borderTop: "1px solid #334155", paddingTop: "10px" }}>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8", fontWeight: "bold", marginBottom: "6px" }}>
            AUDITABLE TRANSITION LEDGER ({history.length} TRANSITIONS):
          </div>
          <div style={{ maxHeight: "120px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "4px" }}>
            {history.slice(-5).reverse().map((t, idx) => (
              <div key={idx} style={{ fontSize: "0.65rem", color: "#cbd5e1", background: "#1e293b", padding: "4px 8px", borderRadius: "3px", fontFamily: "var(--font-mono, monospace)" }}>
                <span style={{ color: "#38bdf8", fontWeight: "bold" }}>{t.from_state} → {t.to_state}</span> |
                <span style={{ color: "#a7f3d0" }}> {t.trigger}</span> |
                <span style={{ color: "#94a3b8" }}> {t.detail || "Executed"}</span> |
                <span style={{ color: "#64748b" }}> Hash: {t.transition_hash.slice(0, 8)}...</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
