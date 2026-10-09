"use client";

import React, { useState, useEffect } from "react";

interface CognitiveBrainWorkspaceProps {
  apiBase: string;
}

interface WorldModelData {
  world_model_id: string;
  version: number;
  objective: {
    question: string;
    target_quantities: string[];
    is_resolved: boolean;
    resolution_summary?: string;
  };
  geometry: {
    name: string;
    thickness_ratio: number;
    camber_ratio: number;
    chord_m: number;
    is_normalized: boolean;
  };
  operating_state: {
    alpha_deg: number;
    reynolds: number;
    mach: number;
  };
  active_domains: string[];
  assertions: Record<string, {
    assertion_id: string;
    subject: string;
    property_name: string;
    value: any;
    status: string;
    source: string;
    epistemic_tier: string;
  }>;
  unknowns: string[];
  provenance_hash: string;
}

interface HypothesisData {
  hypothesis_id: string;
  title: string;
  statement: string;
  mechanism: string;
  predictions: Record<string, any>;
  status: string;
  testability: string;
  falsification_criteria: Array<{
    quantity: string;
    condition: string;
    physical_rationale: string;
  }>;
}

interface CritiqueData {
  hypothesis_id: string;
  hypothesis_title: string;
  extrapolation_risk: string;
  overall_critique_verdict: string;
  potential_law_conflicts: string[];
  falsifying_observation: string;
  vulnerabilities: Array<{
    dimension: string;
    question_challenged: string;
    finding: string;
    risk_level: string;
    suggested_audit: string;
  }>;
}

interface ExperimentData {
  experiment_id: string;
  title: string;
  tool_required: string;
  fidelity_level: string;
  utility: {
    composite_utility: number;
    scientific_value: number;
    hypothesis_discrimination: number;
    expected_information_gain_bits: number;
    computational_cost_index: number;
    utility_breakdown: string;
  };
}

interface SessionData {
  session_id: string;
  question: string;
  autonomy_level: string;
  current_state: string;
  current_cycle: number;
  max_cycles: number;
  stopping_reason?: string;
  world_model: WorldModelData;
  active_hypotheses: HypothesisData[];
  active_critiques: CritiqueData[];
  candidate_experiments: ExperimentData[];
  contradiction_reports: any[];
  timeline: Array<{
    stage: string;
    message: string;
    timestamp: string;
  }>;
}

interface GraphNode {
  id: string;
  type: string;
  label: string;
  status: string;
  details?: string;
}

interface GraphLink {
  source: string;
  target: string;
  relation: string;
}

export const CognitiveBrainWorkspace: React.FC<CognitiveBrainWorkspaceProps> = ({ apiBase }) => {
  const [question, setQuestion] = useState("Investigate aerodynamic lift and drag behavior of NACA 0012 across flight regime");
  const [geometry, setGeometry] = useState("NACA 0012");
  const [alphaDeg, setAlphaDeg] = useState(6.0);
  const [reynolds, setReynolds] = useState(3.0e6);
  const [mach, setMach] = useState(0.15);
  const [autonomyLevel, setAutonomyLevel] = useState("LEVEL_4");

  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<SessionData | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] } | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [activeTab, setActiveTab] = useState<"LIVE_REASONING" | "WORLD_MODEL" | "GRAPH" | "CRITIQUE" | "CONTRADICTION">("LIVE_REASONING");

  const runCognitiveInvestigation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/cognitive/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          geometry_name: geometry,
          alpha_deg: Number(alphaDeg),
          reynolds: Number(reynolds),
          mach: Number(mach),
          autonomy_level: autonomyLevel,
          max_cycles: 3,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSession(data.session);
        fetchGraph(data.session.session_id);
      }
    } catch (err) {
      console.error("Cognitive investigation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchGraph = async (sessionId: string) => {
    try {
      const res = await fetch(`${apiBase}/api/cognitive/session/${sessionId}/graph`);
      if (res.ok) {
        const g = await res.json();
        setGraphData({ nodes: g.nodes, links: g.links });
      }
    } catch (err) {
      console.error("Graph fetch failed:", err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED":
      case "QUESTION_RESOLVED":
      case "SUPPORTED":
      case "VERIFIED":
        return "#10b981";
      case "STALLED":
      case "AWAITING_HUMAN_APPROVAL":
      case "PARTIALLY_SUPPORTED":
        return "#f59e0b";
      case "FAILED":
      case "CONTRADICTED":
      case "HIGH_EXTRAPOLATION_RISK":
        return "#ef4444";
      default:
        return "#3b82f6";
    }
  };

  return (
    <div style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "24px" }} className="animate-fade-in">
      {/* Header & Title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "28px" }}>⚡</span>
            <h1 style={{ fontSize: "24px", fontWeight: 700, margin: 0, letterSpacing: "-0.02em" }}>AASI COGNITIVE ENGINE</h1>
            <span style={{ fontSize: "11px", fontWeight: 600, padding: "3px 8px", borderRadius: "12px", background: "rgba(59, 130, 246, 0.15)", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.3)" }}>
              AEROSPACE COGNITIVE BRAIN
            </span>
          </div>
          <p style={{ margin: "6px 0 0 0", fontSize: "13px", color: "rgba(255,255,255,0.6)" }}>
            Autonomous Aerospace Scientific Reasoning • Active World Model • Adversarial Critique • Multi-Fidelity Reconciler
          </p>
        </div>

        {/* Autonomy Level Indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", background: "rgba(255,255,255,0.03)", padding: "8px 16px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>AUTONOMY:</div>
          <select
            value={autonomyLevel}
            onChange={(e) => setAutonomyLevel(e.target.value)}
            style={{ background: "#111827", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.4)", borderRadius: "4px", padding: "4px 8px", fontSize: "12px", fontWeight: 600 }}
          >
            <option value="LEVEL_0">Level 0 (Passive / Answer Only)</option>
            <option value="LEVEL_1">Level 1 (Analyze &amp; Recommend)</option>
            <option value="LEVEL_2">Level 2 (Plan Experiments)</option>
            <option value="LEVEL_3">Level 3 (Stage Cases &amp; Notebooks)</option>
            <option value="LEVEL_4">Level 4 (Safe Computational Execution)</option>
            <option value="LEVEL_5">Level 5 (Full Closed-Loop Autonomous)</option>
          </select>
        </div>
      </div>

      {/* Investigation Problem Framing Card */}
      <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "flex", gap: "16px", alignItems: "flex-end" }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.5)", marginBottom: "6px", textTransform: "uppercase" }}>
              Scientific Aerospace Question / Investigation Objective
            </label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              style={{ width: "100%", background: "#0b0f19", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "6px", padding: "10px 14px", color: "#fff", fontSize: "14px" }}
              placeholder="E.g. What physical mechanism causes drag rise for NACA 0012 at alpha=6 deg?"
            />
          </div>

          <button
            onClick={runCognitiveInvestigation}
            disabled={loading}
            style={{
              padding: "10px 24px",
              background: loading ? "#4b5563" : "linear-gradient(135deg, #2563eb, #1d4ed8)",
              color: "#fff",
              fontWeight: 600,
              fontSize: "14px",
              borderRadius: "6px",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 2px 10px rgba(37, 99, 235, 0.3)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {loading ? "Reasoning & Executing..." : "⚡ Run Cognitive Investigation"}
          </button>
        </div>

        {/* Flight Condition Controls */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", background: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "6px" }}>
          <div>
            <label style={{ display: "block", fontSize: "10px", color: "rgba(255,255,255,0.5)", marginBottom: "4px" }}>GEOMETRY PROFILE</label>
            <input
              type="text"
              value={geometry}
              onChange={(e) => setGeometry(e.target.value)}
              style={{ width: "100%", background: "#111827", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px", padding: "6px 8px", color: "#e5e7eb", fontSize: "12px" }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "10px", color: "rgba(255,255,255,0.5)", marginBottom: "4px" }}>ANGLE OF ATTACK (α)</label>
            <input
              type="number"
              value={alphaDeg}
              onChange={(e) => setAlphaDeg(Number(e.target.value))}
              style={{ width: "100%", background: "#111827", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px", padding: "6px 8px", color: "#e5e7eb", fontSize: "12px" }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "10px", color: "rgba(255,255,255,0.5)", marginBottom: "4px" }}>REYNOLDS NUMBER (Re)</label>
            <input
              type="number"
              value={reynolds}
              onChange={(e) => setReynolds(Number(e.target.value))}
              style={{ width: "100%", background: "#111827", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px", padding: "6px 8px", color: "#e5e7eb", fontSize: "12px" }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "10px", color: "rgba(255,255,255,0.5)", marginBottom: "4px" }}>MACH NUMBER (M)</label>
            <input
              type="number"
              step="0.05"
              value={mach}
              onChange={(e) => setMach(Number(e.target.value))}
              style={{ width: "100%", background: "#111827", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px", padding: "6px 8px", color: "#e5e7eb", fontSize: "12px" }}
            />
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "8px" }}>
        {[
          { key: "LIVE_REASONING", label: "⚡ Live Investigation & Timeline" },
          { key: "WORLD_MODEL", label: "🌐 Aerospace World Model" },
          { key: "GRAPH", label: "🕸️ Investigation Graph" },
          { key: "CRITIQUE", label: "🛡️ Adversarial Scientific Critique" },
          { key: "CONTRADICTION", label: "⚖️ Contradiction Engine" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              padding: "8px 16px",
              background: activeTab === tab.key ? "rgba(59, 130, 246, 0.15)" : "transparent",
              color: activeTab === tab.key ? "#60a5fa" : "rgba(255,255,255,0.6)",
              border: activeTab === tab.key ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid transparent",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── Tab Content 1: Live Reasoning & Timeline ─── */}
      {activeTab === "LIVE_REASONING" && (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "20px" }}>
          {/* Left Column: Cognitive Loop State & Hypotheses */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Status Card */}
            <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "rgba(255,255,255,0.5)", textTransform: "uppercase" }}>CURRENT COGNITIVE STATE</span>
                <span style={{ fontSize: "12px", fontWeight: 700, padding: "2px 10px", borderRadius: "10px", background: getStatusColor(session?.current_state || "IDLE") + "20", color: getStatusColor(session?.current_state || "IDLE"), border: `1px solid ${getStatusColor(session?.current_state || "IDLE")}50` }}>
                  {session?.current_state || "IDLE"}
                </span>
              </div>
              <div style={{ fontSize: "13px", color: "rgba(255,255,255,0.8)" }}>
                {session?.stopping_reason ? (
                  <div>
                    <span style={{ color: "#10b981", fontWeight: 600 }}>Resolved: </span>
                    {session.world_model.objective.resolution_summary || session.stopping_reason}
                  </div>
                ) : (
                  "Ready to formulate hypotheses, critique assumptions, and design discriminating experiments."
                )}
              </div>
            </div>

            {/* Active Hypotheses Cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <h3 style={{ fontSize: "13px", fontWeight: 700, color: "rgba(255,255,255,0.6)", textTransform: "uppercase", margin: 0 }}>
                Competing Physical Hypotheses ({session?.active_hypotheses?.length || 0})
              </h3>
              {session?.active_hypotheses && session.active_hypotheses.length > 0 ? (
                session.active_hypotheses.map((h, i) => (
                  <div
                    key={h.hypothesis_id}
                    style={{
                      background: "rgba(255,255,255,0.02)",
                      border: `1px solid ${h.status === "SUPPORTED" ? "rgba(16, 185, 129, 0.4)" : "rgba(255,255,255,0.08)"}`,
                      borderRadius: "8px",
                      padding: "14px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                      <span style={{ fontSize: "11px", fontWeight: 700, color: "#60a5fa" }}>H{i + 1}: {h.title}</span>
                      <span style={{ fontSize: "10px", fontWeight: 600, padding: "2px 8px", borderRadius: "4px", background: getStatusColor(h.status) + "20", color: getStatusColor(h.status) }}>
                        {h.status}
                      </span>
                    </div>
                    <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.8)", margin: "0 0 8px 0" }}>{h.statement}</p>
                    <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", background: "rgba(0,0,0,0.2)", padding: "6px 8px", borderRadius: "4px" }}>
                      <strong>Mechanism:</strong> {h.mechanism}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", fontStyle: "italic", padding: "16px", textAlign: "center", border: "1px dashed rgba(255,255,255,0.1)", borderRadius: "8px" }}>
                  No active hypotheses generated yet. Click &quot;Run Cognitive Investigation&quot; to begin.
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Live Reasoning Timeline */}
          <div style={{ background: "rgba(0,0,0,0.25)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "16px", display: "flex", flexDirection: "column", gap: "12px", maxHeight: "550px", overflowY: "auto" }}>
            <h3 style={{ fontSize: "12px", fontWeight: 700, color: "rgba(255,255,255,0.5)", textTransform: "uppercase", margin: 0 }}>
              Live Cognitive Timeline &amp; Decision Audit
            </h3>
            {session?.timeline && session.timeline.length > 0 ? (
              session.timeline.map((entry, idx) => (
                <div key={idx} style={{ display: "flex", gap: "10px", alignItems: "flex-start", fontSize: "12px", paddingBottom: "10px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                  <span style={{ fontSize: "10px", fontWeight: 700, color: "#38bdf8", minWidth: "110px", textTransform: "uppercase" }}>{entry.stage}</span>
                  <span style={{ color: "rgba(255,255,255,0.8)", flex: 1 }}>{entry.message}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", fontStyle: "italic" }}>
                Awaiting cognitive loop execution...
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Tab Content 2: Aerospace World Model ─── */}
      {activeTab === "WORLD_MODEL" && session && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          {/* Left: World Model State & Invariants */}
          <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "16px", display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#60a5fa" }}>AerospaceWorldModel (v{session.world_model.version})</span>
              <span style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.4)" }}>SHA256: {session.world_model.provenance_hash.slice(0, 16)}...</span>
            </div>

            <div>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.5)" }}>ACTIVE CONTINUUM DOMAINS</span>
              <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                {session.world_model.active_domains.map((dom) => (
                  <span key={dom} style={{ fontSize: "11px", padding: "2px 8px", background: "rgba(59, 130, 246, 0.2)", color: "#93c5fd", borderRadius: "4px" }}>{dom}</span>
                ))}
              </div>
            </div>

            <div>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.5)" }}>GEOMETRY DEFINITION</span>
              <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.8)", marginTop: "4px" }}>
                Profile: <strong>{session.world_model.geometry.name}</strong> • Chord: {session.world_model.geometry.chord_m}m • Thickness: {(session.world_model.geometry.thickness_ratio * 100).toFixed(1)}% • Camber: {(session.world_model.geometry.camber_ratio * 100).toFixed(1)}%
              </div>
            </div>

            <div>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.5)" }}>EXPLICIT UNKNOWNS (WHAT AASI DOES NOT ASSUME AS FACT)</span>
              <div style={{ marginTop: "4px" }}>
                {session.world_model.unknowns.length > 0 ? (
                  session.world_model.unknowns.map((u, i) => (
                    <div key={i} style={{ fontSize: "11px", color: "#f87171", padding: "4px 8px", background: "rgba(239, 68, 68, 0.1)", borderRadius: "4px", marginBottom: "4px" }}>
                      ⚠️ {u}
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", fontStyle: "italic" }}>No critical physical unknowns flagged.</div>
                )}
              </div>
            </div>
          </div>

          {/* Right: Assertions Table */}
          <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "16px" }}>
            <h3 style={{ fontSize: "12px", fontWeight: 700, color: "rgba(255,255,255,0.5)", textTransform: "uppercase", margin: "0 0 12px 0" }}>
              Persistent Assertions ({Object.keys(session.world_model.assertions).length})
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {Object.values(session.world_model.assertions).map((ast) => (
                <div key={ast.assertion_id} style={{ background: "rgba(0,0,0,0.2)", padding: "10px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#fff" }}>{ast.property_name}</span>
                    <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "#10b98120", color: "#10b981" }}>{ast.epistemic_tier}</span>
                  </div>
                  <div style={{ fontSize: "13px", fontWeight: 700, color: "#38bdf8", margin: "4px 0" }}>
                    {typeof ast.value === "number" ? ast.value.toFixed(4) : ast.value}
                  </div>
                  <div style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)" }}>
                    Source: {ast.source} • Status: {ast.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ─── Tab Content 3: Clickable Investigation Graph ─── */}
      {activeTab === "GRAPH" && (
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#fff", margin: 0 }}>
              Autonomous Investigation Graph (Clickable Nodes)
            </h3>
            <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)" }}>
              Question → Hypotheses → Experiments → Verification → Decision
            </span>
          </div>

          {graphData ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
                {graphData.nodes.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    style={{
                      padding: "10px 16px",
                      background: selectedNode?.id === node.id ? "rgba(59, 130, 246, 0.3)" : "rgba(0,0,0,0.4)",
                      border: `1px solid ${selectedNode?.id === node.id ? "#60a5fa" : "rgba(255,255,255,0.15)"}`,
                      borderRadius: "6px",
                      color: "#fff",
                      cursor: "pointer",
                      textAlign: "left",
                      minWidth: "180px",
                    }}
                  >
                    <div style={{ fontSize: "10px", color: "#60a5fa", fontWeight: 700, textTransform: "uppercase" }}>{node.type}</div>
                    <div style={{ fontSize: "12px", fontWeight: 600, marginTop: "2px" }}>{node.label}</div>
                    <div style={{ fontSize: "10px", color: getStatusColor(node.status), marginTop: "4px" }}>Status: {node.status}</div>
                  </button>
                ))}
              </div>

              {selectedNode && (
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "6px", border: "1px solid rgba(59, 130, 246, 0.3)" }}>
                  <div style={{ fontSize: "11px", color: "#60a5fa", fontWeight: 700 }}>NODE INSPECTOR: {selectedNode.type}</div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#fff", marginTop: "4px" }}>{selectedNode.label}</div>
                  {selectedNode.details && (
                    <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.7)", marginTop: "6px" }}>
                      <strong>Details:</strong> {selectedNode.details}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", fontStyle: "italic", textAlign: "center", padding: "20px" }}>
              Run an investigation to render the real graph topology.
            </div>
          )}
        </div>
      )}

      {/* ─── Tab Content 4: Adversarial Scientific Critique ─── */}
      {activeTab === "CRITIQUE" && session && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {session.active_critiques.map((crit, idx) => (
            <div key={idx} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                <span style={{ fontSize: "13px", fontWeight: 700, color: "#fff" }}>Critic Audit: {crit.hypothesis_title}</span>
                <span style={{ fontSize: "11px", fontWeight: 600, padding: "2px 8px", borderRadius: "4px", background: crit.extrapolation_risk === "SEVERE" ? "#ef444420" : "#10b98120", color: crit.extrapolation_risk === "SEVERE" ? "#ef4444" : "#10b981" }}>
                  Extrapolation Risk: {crit.extrapolation_risk}
                </span>
              </div>

              <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.8)", marginBottom: "8px" }}>
                <strong>Verdict:</strong> {crit.overall_critique_verdict}
              </div>

              <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.6)", marginBottom: "12px" }}>
                <strong>Falsifying Observation:</strong> {crit.falsifying_observation}
              </div>

              {crit.vulnerabilities.map((v, vIdx) => (
                <div key={vIdx} style={{ background: "rgba(0,0,0,0.25)", padding: "10px", borderRadius: "6px", borderLeft: `3px solid ${v.risk_level === "CRITICAL" ? "#ef4444" : "#f59e0b"}`, marginBottom: "6px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 700, color: v.risk_level === "CRITICAL" ? "#f87171" : "#fbbf24" }}>{v.dimension} ({v.risk_level})</div>
                  <div style={{ fontSize: "12px", color: "#e5e7eb", margin: "2px 0" }}>{v.finding}</div>
                  <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)" }}>Audit: {v.suggested_audit}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* ─── Tab Content 5: Contradiction Engine ─── */}
      {activeTab === "CONTRADICTION" && session && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {session.contradiction_reports.length > 0 ? (
            session.contradiction_reports.map((con, idx) => (
              <div key={idx} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "13px", fontWeight: 700, color: "#f59e0b" }}>{con.contradiction_type}</span>
                  <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)" }}>Divergence: {con.relative_divergence_percent?.toFixed(1)}%</span>
                </div>
                <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.8)", marginBottom: "8px" }}>
                  {con.physical_explanation}
                </div>
                <div style={{ fontSize: "11px", color: "#60a5fa", background: "rgba(59, 130, 246, 0.1)", padding: "8px", borderRadius: "4px" }}>
                  <strong>Governing Mechanism:</strong> {con.governing_mechanism}
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", fontStyle: "italic", textAlign: "center", padding: "20px" }}>
              No physical contradictions detected.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
