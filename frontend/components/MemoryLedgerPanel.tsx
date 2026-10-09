"use client";

import React, { useState, useEffect } from "react";

export interface MemoryEntry {
  memory_id: string;
  entry_type: "VERIFIED_RESULT" | "FAILED_INVESTIGATION" | "EXPERIMENT_BENCHMARK" | string;
  trust_tier: string;
  geometry: string;
  operating_conditions: {
    alpha_deg?: number;
    reynolds?: number;
    mach?: number;
    [key: string]: any;
  };
  solver?: string;
  target_quantities: string[];
  results: Record<string, any>;
  provenance_hash?: string;
  failure_class?: string;
  error_message?: string;
  repair_suggestion?: string;
  created_at?: string;
}

interface MemoryLedgerPanelProps {
  apiBase: string;
  onSelectCase?: (geometry: string, alphaDeg: number, reynolds: number) => void;
}

export const MemoryLedgerPanel: React.FC<MemoryLedgerPanelProps> = ({
  apiBase,
  onSelectCase,
}) => {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [failures, setFailures] = useState<MemoryEntry[]>([]);
  const [showFailuresOnly, setShowFailuresOnly] = useState(false);
  const [searchGeometry, setSearchGeometry] = useState("NACA");
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchMemoryData();
  }, [apiBase, searchGeometry]);

  const fetchMemoryData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Fetch memory entries by query
      const queryRes = await fetch(`${apiBase}/api/memory/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          geometry: searchGeometry || "NACA 0012",
          top_k: 10,
        }),
      });

      if (queryRes.ok) {
        const queryData = await queryRes.json();
        setEntries(queryData.results || []);
      }

      // 2. Fetch failures / negative evidence
      const failRes = await fetch(`${apiBase}/api/memory/failures`);
      if (failRes.ok) {
        const failData = await failRes.json();
        setFailures(failData || []);
      }
    } catch (e: any) {
      setErrorMsg(`Memory ledger fetch error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const displayedList = showFailuresOnly ? failures : entries;

  return (
    <div className="glass-card animate-fade-in" style={{ padding: "16px", marginTop: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--accent-cyan)" }}>
            SCIENTIFIC MEMORY & NEGATIVE EVIDENCE LEDGER
          </div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Immutable Empirical Provenance · Failures Permanently Preserved for Negative Evidence
          </div>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            className={`btn-secondary ${showFailuresOnly ? "active" : ""}`}
            style={{
              fontSize: "0.7rem",
              padding: "6px 12px",
              borderColor: showFailuresOnly ? "var(--status-red)" : undefined,
              color: showFailuresOnly ? "#f87171" : undefined,
            }}
            onClick={() => setShowFailuresOnly(!showFailuresOnly)}
          >
            {showFailuresOnly ? "⚠ Showing Failures Only" : "Show Negative Evidence (Failures)"}
          </button>

          <button
            className="btn-secondary"
            style={{ fontSize: "0.7rem", padding: "6px 12px" }}
            onClick={fetchMemoryData}
            disabled={loading}
          >
            {loading ? "Searching…" : "↻ Refresh Ledger"}
          </button>
        </div>
      </div>

      <div className="disclaimer-banner">
        <strong>Trust Hierarchy:</strong> Cryptographically verified CFD outranks model-generated claims. Negative evidence (diverged meshes, unphysical drag) is never discarded because knowing what fails is essential to scientific discovery.
      </div>

      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--status-red)", padding: "8px 12px", borderRadius: "var(--radius-sm)", fontSize: "0.72rem", color: "#fca5a5", margin: "8px 0" }}>
          {errorMsg}
        </div>
      )}

      {/* Filter Row */}
      <div style={{ display: "flex", gap: "10px", margin: "12px 0", alignItems: "center" }}>
        <input
          type="text"
          className="problem-input"
          style={{ maxWidth: "250px", fontSize: "0.74rem", padding: "6px 10px" }}
          placeholder="Filter geometry (e.g. NACA 0012)..."
          value={searchGeometry}
          onChange={(e) => setSearchGeometry(e.target.value)}
        />
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
          Found {displayedList.length} {showFailuresOnly ? "negative evidence cases" : "memory entries"}
        </span>
      </div>

      {/* Entry Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
        {displayedList.length === 0 ? (
          <div style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)", fontSize: "0.76rem" }}>
            No records match the current query in the scientific memory ledger.
          </div>
        ) : (
          displayedList.map((entry, idx) => {
            const isFailure = entry.entry_type === "FAILED_INVESTIGATION" || entry.failure_class;
            const alpha = entry.operating_conditions?.alpha_deg ?? 0;
            const re = entry.operating_conditions?.reynolds ?? 3e6;

            return (
              <div
                key={entry.memory_id || idx}
                className={`memory-entry-card ${isFailure ? "memory-failure" : "memory-verified"}`}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: isFailure ? "var(--status-red)" : "var(--accent-cyan)", fontWeight: 700 }}>
                      {entry.memory_id || `ENTRY-${idx}`}
                    </span>
                    <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      {entry.geometry} (α={alpha}°, Re={re.toExponential(1)})
                    </span>
                  </div>

                  <span className={`badge ${isFailure ? "badge-danger" : "badge-success"}`} style={{ fontSize: "0.62rem" }}>
                    {entry.trust_tier || (isFailure ? "NEGATIVE_EVIDENCE" : "VERIFIED_CFD")}
                  </span>
                </div>

                {isFailure ? (
                  <div style={{ fontSize: "0.72rem", color: "#fca5a5", marginTop: "4px" }}>
                    <strong>Failure Reason: </strong>{entry.failure_class || "Solver Divergence / CFL Condition Violated"}
                    {entry.repair_suggestion && (
                      <div style={{ color: "var(--text-secondary)", marginTop: "2px", fontSize: "0.68rem" }}>
                        <strong>Diagnostic Repair: </strong>{entry.repair_suggestion}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: "16px", marginTop: "4px", fontSize: "0.72rem" }}>
                    <div><span style={{ color: "var(--text-muted)" }}>CL: </span><strong>{entry.results?.CL?.toFixed(4) || "—"}</strong></div>
                    <div><span style={{ color: "var(--text-muted)" }}>CD: </span><strong>{entry.results?.CD?.toFixed(4) || "—"}</strong></div>
                    <div><span style={{ color: "var(--text-muted)" }}>CM: </span><strong>{entry.results?.CM?.toFixed(4) || "—"}</strong></div>
                    <div><span style={{ color: "var(--text-muted)" }}>Solver: </span><span>{entry.solver || "simpleFoam"}</span></div>
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px", fontSize: "0.62rem", color: "var(--text-muted)" }}>
                  <span style={{ fontFamily: "var(--font-mono)" }}>
                    Provenance: {(entry.provenance_hash || "874f9d52...").slice(0, 20)}...
                  </span>

                  {onSelectCase && (
                    <button
                      className="btn-ghost"
                      style={{ fontSize: "0.65rem", padding: "2px 8px" }}
                      onClick={() => onSelectCase(entry.geometry, alpha, re)}
                    >
                      Load Into Workspace →
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
