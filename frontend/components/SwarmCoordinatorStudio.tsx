"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Sparkles,
  Users,
  Radio,
  Eye,
  RefreshCw,
  Compass,
  ArrowRight,
  ChevronRight,
  Wind,
  Sliders,
  Crosshair,
} from "lucide-react";

interface SwarmCoordinatorStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface SwarmAgent {
  uav_id: number;
  role: string;
  x: number;
  y: number;
  z: number;
  speed_mps: number;
  compromised: boolean;
}

interface SwarmSimulationResult {
  mission_id: string;
  formation_type: string;
  total_uavs: number;
  roles_breakdown: Record<string, number>;
  safety_guarantees: {
    d_safe_prescribed_m: number;
    min_distance_observed_m: number;
    cbf_zero_collision_verified: boolean;
    cbf_filter_activations: number;
  };
  aerodynamics: {
    induced_drag_reduction_pct: number;
    fuel_range_extension_pct: number;
    wake_upwash_velocity_mps: number;
  };
  byzantine_consensus: {
    swarm_nodes_count: number;
    tolerable_byzantine_faults: number;
    compromised_nodes_count: number;
    compromised_node_indices: number[];
    consensus_resilience_intact: boolean;
    agreed_consensus_value: number;
    consensus_status: string;
  };
  trajectory_snapshots: Array<{
    step: number;
    time_s: number;
    agents: SwarmAgent[];
  }>;
  executive_summary: {
    formation: string;
    total_nodes: number;
    min_inter_agent_distance_m: number;
    collision_status: string;
    drag_reduction_pct: number;
    consensus_status: string;
    byzantine_resilient: boolean;
  };
}

export default function SwarmCoordinatorStudio({ isOpen, onClose, apiBase }: SwarmCoordinatorStudioProps) {
  const [activePreset, setActivePreset] = useState<string>("INDIAN_AF_ALFAS_SWARM");
  const [formation, setFormation] = useState<string>("V_FORMATION");
  const [uavCount, setUavCount] = useState<number>(18);
  const [dSafe, setDSafe] = useState<number>(12.0);
  const [byzantineAdversary, setByzantineAdversary] = useState<boolean>(false);
  const [result, setResult] = useState<SwarmSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeSnapshotIdx, setActiveSnapshotIdx] = useState<number>(0);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    runSimulation();
  }, [isOpen, activePreset, formation, byzantineAdversary]);

  const runSimulation = () => {
    setLoading(true);
    fetch(`${apiBase}/api/swarm/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mission_id: activePreset,
        formation_type: formation,
        num_uavs: uavCount,
        d_safe: dSafe,
        byzantine_adversary_present: byzantineAdversary,
        steps: 40,
      }),
    })
      .then((res) => {
        if (!res.ok) throw new Error("Swarm simulation failed");
        return res.json();
      })
      .then((data: SwarmSimulationResult) => {
        setResult(data);
        setActiveSnapshotIdx(data.trajectory_snapshots.length - 1);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Swarm Simulation error:", err);
        setLoading(false);
      });
  };

  if (!isOpen) return null;

  const currentSnapshot = result?.trajectory_snapshots[activeSnapshotIdx];
  const agents = currentSnapshot?.agents || [];
  const bft = result?.byzantine_consensus;
  const aero = result?.aerodynamics;
  const safety = result?.safety_guarantees;

  const getRoleColor = (role: string, compromised: boolean) => {
    if (compromised) return "#dc2626";
    switch (role) {
      case "LEADER":
        return "#eab308";
      case "SCOUT":
        return "#06b6d4";
      case "ELECTRONIC_ATTACK":
        return "#8b5cf6";
      case "KINETIC_STRIKE":
        return "#f43f5e";
      case "COMMS_RELAY":
        return "#10b981";
      default:
        return "#64748b";
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(15, 23, 42, 0.65)",
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
          maxWidth: "1280px",
          height: "92vh",
          background: "#ffffff",
          borderRadius: "14px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          border: "1px solid #e2e8f0",
          fontFamily: "var(--font-sans, system-ui, sans-serif)",
          color: "#0f172a",
        }}
      >
        {/* Header Bar */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#f8fafc",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, #10b981 0%, #047857 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)",
              }}
            >
              <Users size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Autonomous Heterogeneous UAV Swarm Tactical Coordinator
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#10b981",
                    color: "#ffffff",
                  }}
                >
                  STAGE 26 SOVEREIGN
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "#64748b" }}>
                Control Barrier Functions (CBF) • Byzantine Fault Consensus • Aerodynamic Upwash Formation
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Formation Selector */}
            <select
              value={formation}
              onChange={(e) => setFormation(e.target.value)}
              style={{
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid #cbd5e1",
                background: "#ffffff",
                fontSize: "0.82rem",
                fontWeight: 600,
                color: "#0f172a",
                cursor: "pointer",
                outline: "none",
              }}
            >
              <option value="V_FORMATION">V-Formation (Aerodynamic Upwash)</option>
              <option value="DEFENSIVE_RING">Defensive Ring (360° Perimeter)</option>
              <option value="PINCER_ENVELOPMENT">Double Pincer Envelopment</option>
              <option value="DISTRIBUTED_MESH">Distributed Aperture Mesh</option>
            </select>

            {/* Run Button */}
            <button
              onClick={runSimulation}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#10b981",
                color: "#ffffff",
                fontSize: "0.82rem",
                fontWeight: 600,
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Computing..." : "Dispatch Swarm"}
            </button>

            <button
              onClick={onClose}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                background: "#ffffff",
                fontSize: "0.85rem",
                cursor: "pointer",
                color: "#64748b",
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Byzantine Fault Banner */}
        {bft && (
          <div
            style={{
              padding: "10px 24px",
              background: byzantineAdversary ? "#fef2f2" : "#f0fdf4",
              borderBottom: `1px solid ${byzantineAdversary ? "#fecaca" : "#bbf7d0"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {bft.consensus_resilience_intact ? (
                <ShieldCheck size={18} color="#16a34a" />
              ) : (
                <ShieldAlert size={18} color="#dc2626" />
              )}
              <span
                style={{
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: bft.consensus_resilience_intact ? "#166534" : "#991b1b",
                }}
              >
                {byzantineAdversary
                  ? `BYZANTINE ATTACK ACTIVE: Nodes [${bft.compromised_node_indices.join(", ")}] spoofed. Resilient consensus maintained (${bft.compromised_nodes_count} ≤ ${bft.tolerable_byzantine_faults} tolerable).`
                  : `SWARM CONSENSUS INTACT: All ${bft.swarm_nodes_count} nodes participating in decentralized target quorum.`}
              </span>
            </div>

            <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: "#475569", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={byzantineAdversary}
                onChange={(e) => setByzantineAdversary(e.target.checked)}
              />
              Inject Compromised Rogue Drone
            </label>
          </div>
        )}

        {/* Telemetry Metric Tiles */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: "12px",
            padding: "16px 24px",
            background: "#ffffff",
            borderBottom: "1px solid #e2e8f0",
          }}
        >
          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Safety Certificate</div>
            <div
              style={{
                fontSize: "1.05rem",
                fontWeight: 800,
                color: safety?.cbf_zero_collision_verified ? "#16a34a" : "#dc2626",
                marginTop: "4px",
              }}
            >
              {safety?.cbf_zero_collision_verified ? "PROVABLE ZERO COLLISION" : "PROXIMITY WARNING"}
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Active CBF Filter QP
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Min Separation Observed</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0f172a", marginTop: "2px" }}>
              {safety ? safety.min_distance_observed_m.toFixed(2) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>m</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Prescribed d_safe: {safety?.d_safe_prescribed_m || "--"} m
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Induced Drag Reduction</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#10b981", marginTop: "2px" }}>
              -{aero ? aero.induced_drag_reduction_pct.toFixed(1) : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>%</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Range Extension: +{aero?.fuel_range_extension_pct || "--"}%
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Byzantine Quorum Limit</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#8b5cf6", marginTop: "2px" }}>
              {bft ? bft.tolerable_byzantine_faults : "--"}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>nodes max</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Tolerance f &lt; n / 3
            </div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Heterogeneous Force</div>
            <div style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0284c7", marginTop: "2px" }}>
              {agents.length}{" "}
              <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>UAVs</span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
              Leader • Scouts • EW • Strike • Relay
            </div>
          </div>
        </div>

        {/* Main Canvas & Inspection Pane */}
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "2.2fr 1fr", overflow: "hidden" }}>
          {/* SVG Tactical Radar Screen */}
          <div style={{ position: "relative", background: "#0a0f1d", display: "flex", flexDirection: "column" }}>
            {/* Timeline Stepper at top */}
            <div
              style={{
                padding: "8px 16px",
                background: "rgba(15, 23, 42, 0.8)",
                borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                color: "#e2e8f0",
                fontSize: "0.75rem",
              }}
            >
              <span>Time: <strong>{currentSnapshot?.time_s.toFixed(1)}s</strong></span>
              <input
                type="range"
                min={0}
                max={(result?.trajectory_snapshots.length || 1) - 1}
                value={activeSnapshotIdx}
                onChange={(e) => setActiveSnapshotIdx(parseInt(e.target.value))}
                style={{ flex: 1, accentColor: "#10b981", cursor: "pointer" }}
              />
              <span>Snapshot {activeSnapshotIdx + 1} / {result?.trajectory_snapshots.length || 1}</span>
            </div>

            <div style={{ flex: 1, position: "relative" }}>
              <svg width="100%" height="100%" viewBox="-150 -120 400 240" style={{ cursor: "crosshair" }}>
                {/* Radar Grid Circles */}
                <circle cx="0" cy="0" r="40" fill="none" stroke="rgba(16, 185, 129, 0.15)" strokeWidth="1" strokeDasharray="3 3" />
                <circle cx="0" cy="0" r="80" fill="none" stroke="rgba(16, 185, 129, 0.15)" strokeWidth="1" strokeDasharray="3 3" />
                <circle cx="0" cy="0" r="120" fill="none" stroke="rgba(16, 185, 129, 0.15)" strokeWidth="1" strokeDasharray="3 3" />

                {/* Axes */}
                <line x1="-150" y1="0" x2="250" y2="0" stroke="rgba(16, 185, 129, 0.15)" strokeWidth="1" />
                <line x1="0" y1="-120" x2="0" y2="120" stroke="rgba(16, 185, 129, 0.15)" strokeWidth="1" />

                {/* Interswarm communication mesh links */}
                {agents.map((ag_i, i) =>
                  agents.slice(i + 1).map((ag_j, j) => {
                    const dist = Math.hypot(ag_i.x - ag_j.x, ag_i.y - ag_j.y);
                    if (dist > 45.0) return null;
                    return (
                      <line
                        key={`mesh-${ag_i.uav_id}-${ag_j.uav_id}`}
                        x1={ag_i.x}
                        y1={ag_i.y}
                        x2={ag_j.x}
                        y2={ag_j.y}
                        stroke="rgba(16, 185, 129, 0.25)"
                        strokeWidth="0.8"
                      />
                    );
                  })
                )}

                {/* Drone Sprites */}
                {agents.map((ag) => {
                  const isSelected = selectedAgentId === ag.uav_id;
                  const color = getRoleColor(ag.role, ag.compromised);

                  return (
                    <g
                      key={`drone-${ag.uav_id}`}
                      transform={`translate(${ag.x}, ${ag.y})`}
                      onClick={() => setSelectedAgentId(ag.uav_id)}
                      style={{ cursor: "pointer" }}
                    >
                      {/* CBF Safety Bubble when selected */}
                      {isSelected && (
                        <circle
                          cx="0"
                          cy="0"
                          r={dSafe}
                          fill="rgba(16, 185, 129, 0.15)"
                          stroke="#10b981"
                          strokeWidth="1"
                          strokeDasharray="2 2"
                        />
                      )}

                      {/* UAV Sprite Shape */}
                      <circle cx="0" cy="0" r="4" fill={color} />
                      <line x1="-6" y1="-3" x2="6" y2="3" stroke={color} strokeWidth="1.5" />
                      <line x1="-6" y1="3" x2="6" y2="-3" stroke={color} strokeWidth="1.5" />

                      {/* Label */}
                      <text
                        x="6"
                        y="-4"
                        fill="#cbd5e1"
                        fontSize="7"
                        fontFamily="monospace"
                        fontWeight={isSelected ? "bold" : "normal"}
                      >
                        UAV-{ag.uav_id}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Side Inspection Panel */}
          <div
            style={{
              padding: "16px",
              background: "#ffffff",
              borderLeft: "1px solid #e2e8f0",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            {/* Roles Legend */}
            <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f172a", marginBottom: "8px" }}>
                Heterogeneous Force Breakdown
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.74rem" }}>
                {[
                  { role: "LEADER", color: "#eab308", desc: "Tactical Coordinator (1)" },
                  { role: "SCOUT", color: "#06b6d4", desc: "EO/IR Reconnaissance" },
                  { role: "ELECTRONIC_ATTACK", color: "#8b5cf6", desc: "Radar Jammer & EW" },
                  { role: "KINETIC_STRIKE", color: "#f43f5e", desc: "Precision Loitering Munition" },
                  { role: "COMMS_RELAY", color: "#10b981", desc: "NavIC Mesh Transceiver" },
                ].map((item) => (
                  <div key={item.role} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <div style={{ width: "8px", height: "8px", borderRadius: "2px", background: item.color }} />
                      <span style={{ fontWeight: 600 }}>{item.role}</span>
                    </div>
                    <span style={{ color: "#64748b" }}>{item.desc}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Agent Details */}
            {selectedAgentId !== null && (
              <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f172a", marginBottom: "8px" }}>
                  Telemetry: UAV #{selectedAgentId}
                </div>
                {(() => {
                  const ag = agents.find((a) => a.uav_id === selectedAgentId);
                  if (!ag) return <div>No telemetry</div>;
                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.75rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Role:</span>
                        <strong style={{ color: getRoleColor(ag.role, ag.compromised) }}>{ag.role}</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Coordinates (X, Y, Z):</span>
                        <span>({ag.x.toFixed(1)}, {ag.y.toFixed(1)}, {ag.z.toFixed(1)}) m</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Airspeed:</span>
                        <span>{ag.speed_mps.toFixed(1)} m/s ({Math.round(ag.speed_mps * 3.6)} km/h)</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Integrity Status:</span>
                        <span style={{ color: ag.compromised ? "#dc2626" : "#16a34a", fontWeight: 700 }}>
                          {ag.compromised ? "COMPROMISED (ADVERSARIAL)" : "NOMINAL ENCRYPTED"}
                        </span>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Mathematical CBF & BFT Invariants */}
            <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f172a", marginBottom: "6px" }}>
                Control Barrier Function (CBF) Invariant
              </div>
              <div
                style={{
                  background: "#090d16",
                  color: "#34d399",
                  padding: "8px",
                  borderRadius: "4px",
                  fontFamily: "monospace",
                  fontSize: "0.7rem",
                  marginBottom: "8px",
                }}
              >
                h(x) = ‖pᵢ - pⱼ‖² - d_safe² ≥ 0<br />
                ∇h · u + ½α·h ≥ 0
              </div>
              <p style={{ margin: 0, fontSize: "0.73rem", color: "#64748b", lineHeight: "1.4" }}>
                Ensures provable safety: even if a hostile drone attempts a collision course, the decentralized QP actively projects the velocity vector away from the invariant barrier.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
