"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Unlock,
  Key,
  Cpu,
  RefreshCw,
  X,
  Radio,
  FileCheck2,
  AlertTriangle,
  Play,
  Zap,
  Activity,
  Layers,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface PostQuantumBusStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface FrameTelemetry {
  step: number;
  sequence_count: number;
  action: string;
  threat_injected: string;
  is_authenticated: boolean;
  rejection_reason: string | null;
  verification_latency_ms: number;
  bus_state: string;
}

interface AuditData {
  simulation_id: string;
  session: {
    status: string;
    cipher_suite: string;
    post_quantum_security_margin: string;
    shared_secret_sha256: string;
    measured_host_latency_ms: number;
    modeled_space_cpu_latency_ms: number;
    processor_architecture: string;
    memory_footprint_kb: number;
  };
  spacecraft_metadata: {
    spacecraft_id: string;
    spacecraft_name: string;
    processor: string;
    bus_standard: string;
  };
  audit_summary: {
    total_frames_evaluated: number;
    authenticated_count: number;
    rejected_count: number;
    threats_prevented: number;
    firewall_effectiveness_percent: number;
    avg_latency_ms: number;
    zero_day_vulnerabilities: number;
  };
  frame_telemetry: FrameTelemetry[];
}

export default function PostQuantumBusStudio({
  isOpen,
  onClose,
  apiBase,
}: PostQuantumBusStudioProps) {
  const [processorType, setProcessorType] = useState<string>("BAE_RAD750_133MHZ");
  const [spacecraftId, setSpacecraftId] = useState<number>(676);
  const [totalFrames, setTotalFrames] = useState<number>(8);
  const [injectThreats, setInjectThreats] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [auditData, setAuditData] = useState<AuditData | null>(null);
  const [selectedFrame, setSelectedFrame] = useState<FrameTelemetry | null>(null);

  const runAudit = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/pqc-bus/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spacecraft_id: spacecraftId,
          processor_type: processorType,
          total_frames: totalFrames,
          inject_threats: injectThreats,
        }),
      });
      const data: Record<string, any> = await resp.json();
      if (data.status === "success" && data.data) {
        setAuditData(data.data);
        if (data.data.frame_telemetry && data.data.frame_telemetry.length > 0) {
          setSelectedFrame(data.data.frame_telemetry[0]);
        }
      }
    } catch (err) {
      console.error("Failed to run PQC bus audit:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !auditData) {
      runAudit();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        backgroundColor: "rgba(15, 23, 42, 0.75)",
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
          backgroundColor: "#ffffff",
          borderRadius: "14px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          border: "1px solid #e2e8f0",
          color: "#0f172a",
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "linear-gradient(to right, #f8fafc, #ffffff)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                backgroundColor: "rgba(16, 185, 129, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "1px solid rgba(16, 185, 129, 0.25)",
              }}
            >
              <ShieldCheck size={22} color="#059669" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                  Zero-Trust Post-Quantum Spacecraft Bus Security
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    backgroundColor: "#059669",
                    color: "#ffffff",
                    padding: "2px 8px",
                    borderRadius: "9999px",
                    letterSpacing: "0.05em",
                  }}
                >
                  STAGE 29 • NIST FIPS 203/204
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "#64748b", margin: 0, marginTop: "2px" }}>
                CRYSTALS-Kyber-1024 Key Encapsulation • CRYSTALS-Dilithium-5 Digital Signatures • CCSDS Anti-Replay Bus Firewall
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              onClick={runAudit}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                backgroundColor: "#059669",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                padding: "8px 16px",
                fontSize: "0.82rem",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 2px 4px rgba(5, 150, 105, 0.2)",
              }}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              {loading ? "Verifying..." : "Run Zero-Trust Audit"}
            </button>

            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "8px",
                cursor: "pointer",
                color: "#64748b",
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Main Body */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left Controls & Overview */}
          <div
            style={{
              width: "360px",
              borderRight: "1px solid #e2e8f0",
              backgroundColor: "#f8fafc",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
              overflowY: "auto",
            }}
          >
            {/* Processor & Spacecraft Settings */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "10px",
                padding: "16px",
                border: "1px solid #e2e8f0",
              }}
            >
              <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b" }}>
                Spacecraft Flight Computer
              </h3>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Flight Processor Model
                </label>
                <select
                  value={processorType}
                  onChange={(e) => setProcessorType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.8rem",
                    backgroundColor: "#ffffff",
                    color: "#0f172a",
                  }}
                >
                  <option value="BAE_RAD750_133MHZ">BAE Systems RAD750 PowerPC (133 MHz)</option>
                  <option value="COBHAM_LEON4_150MHZ">Cobham Gaisler LEON4 SPARC V8 (150 MHz)</option>
                </select>
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Spacecraft ID (CCSDS 10-Bit)
                </label>
                <input
                  type="number"
                  value={spacecraftId}
                  onChange={(e) => setSpacecraftId(parseInt(e.target.value) || 676)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontSize: "0.8rem",
                  }}
                />
              </div>

              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "4px" }}>
                  Audit Batch Size: {totalFrames} Frames
                </label>
                <input
                  type="range"
                  min="4"
                  max="20"
                  value={totalFrames}
                  onChange={(e) => setTotalFrames(parseInt(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input
                  type="checkbox"
                  id="threatToggle"
                  checked={injectThreats}
                  onChange={(e) => setInjectThreats(e.target.checked)}
                />
                <label htmlFor="threatToggle" style={{ fontSize: "0.78rem", fontWeight: 600, color: "#334155" }}>
                  Inject Adversarial Attacks (Replay, Spoof, MITM)
                </label>
              </div>
            </div>

            {/* Cryptographic Assurance Metrics */}
            {auditData && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Lock size={14} color="#059669" />
                  Quantum Resilience Spec
                </h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>KEM Algorithm:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>ML-KEM-1024 (Kyber)</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>Signature Standard:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>ML-DSA-87 (Dilithium-5)</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>Security Margin:</span>
                    <span style={{ fontWeight: 700, color: "#059669" }}>256-bit Post-Quantum</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: "4px" }}>
                    <span style={{ color: "#64748b" }}>Memory Footprint:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{auditData.session.memory_footprint_kb} KB (&lt; 64 KB Budget)</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "4px" }}>
                    <span style={{ color: "#64748b" }}>Modeled Space CPU Latency:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{auditData.session.modeled_space_cpu_latency_ms} ms</span>
                  </div>
                </div>
              </div>
            )}

            {/* Firewall Summary */}
            {auditData && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "10px",
                  padding: "16px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <h3 style={{ fontSize: "0.85rem", fontWeight: 700, margin: "0 0 12px 0", color: "#1e293b" }}>
                  Zero-Trust Telecommand Firewall
                </h3>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  <div style={{ backgroundColor: "#ecfdf5", padding: "10px", borderRadius: "8px", border: "1px solid #a7f3d0" }}>
                    <div style={{ fontSize: "0.68rem", color: "#047857", fontWeight: 600 }}>AUTHENTICATED</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#065f46" }}>
                      {auditData.audit_summary.authenticated_count}
                    </div>
                  </div>

                  <div style={{ backgroundColor: "#fff1f2", padding: "10px", borderRadius: "8px", border: "1px solid #fecdd3" }}>
                    <div style={{ fontSize: "0.68rem", color: "#be123c", fontWeight: 600 }}>THREATS DROPPED</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#9f1239" }}>
                      {auditData.audit_summary.threats_prevented}
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: "12px", display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                  <span style={{ color: "#64748b" }}>Firewall Effectiveness:</span>
                  <span style={{ fontWeight: 800, color: "#059669" }}>
                    {auditData.audit_summary.firewall_effectiveness_percent}%
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Right Main Content */}
          <div style={{ flex: 1, padding: "24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Real-Time Session Status Banner */}
            {auditData && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "12px",
                  padding: "18px 24px",
                  border: "1px solid #e2e8f0",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <div
                    style={{
                      width: "48px",
                      height: "48px",
                      borderRadius: "12px",
                      backgroundColor: "rgba(16, 185, 129, 0.1)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Lock size={24} color="#059669" />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
                      Active PQC Channel • {auditData.spacecraft_metadata.spacecraft_name} ({auditData.spacecraft_metadata.spacecraft_id})
                    </div>
                    <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#0f172a", marginTop: "2px" }}>
                      Shared Secret SHA-256:{" "}
                      <code style={{ fontSize: "0.8rem", backgroundColor: "#f1f5f9", padding: "2px 6px", borderRadius: "4px", color: "#334155" }}>
                        {auditData.session.shared_secret_sha256.substring(0, 24)}...
                      </code>
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      backgroundColor: "#dcfce7",
                      color: "#15803d",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                    }}
                  >
                    IMMUNE TO QUANTUM SPOOFING
                  </span>
                  <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "4px" }}>
                    Avg TC Verification: <b>{auditData.audit_summary.avg_latency_ms} ms</b>
                  </div>
                </div>
              </div>
            )}

            {/* Telecommand Frames Table */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                overflow: "hidden",
                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
              }}
            >
              <div
                style={{
                  padding: "14px 20px",
                  borderBottom: "1px solid #e2e8f0",
                  backgroundColor: "#f8fafc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#1e293b" }}>
                  CCSDS Telecommand (TC) Transfer Frame Audit Log
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                  Click row to inspect cryptographic proof & firewall verdict
                </div>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
                  <thead>
                    <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>
                      <th style={{ padding: "10px 16px" }}>Seq #</th>
                      <th style={{ padding: "10px 16px" }}>Telecommand Action</th>
                      <th style={{ padding: "10px 16px" }}>Adversarial Vector</th>
                      <th style={{ padding: "10px 16px" }}>Latency (ms)</th>
                      <th style={{ padding: "10px 16px" }}>Firewall State</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditData?.frame_telemetry.map((frame) => {
                      const isSelected = selectedFrame?.sequence_count === frame.sequence_count && selectedFrame?.step === frame.step;
                      return (
                        <tr
                          key={`${frame.step}-${frame.sequence_count}`}
                          onClick={() => setSelectedFrame(frame)}
                          style={{
                            borderBottom: "1px solid #f1f5f9",
                            cursor: "pointer",
                            backgroundColor: isSelected
                              ? "rgba(16, 185, 129, 0.08)"
                              : frame.is_authenticated
                              ? "#ffffff"
                              : "#fffbfa",
                            transition: "background-color 0.15s ease",
                          }}
                        >
                          <td style={{ padding: "12px 16px", fontWeight: 700, fontFamily: "monospace" }}>
                            #{frame.sequence_count}
                          </td>
                          <td style={{ padding: "12px 16px", fontWeight: 600, color: "#1e293b" }}>
                            {frame.action}
                          </td>
                          <td style={{ padding: "12px 16px" }}>
                            {frame.threat_injected === "NO_THREAT_BENIGN" ? (
                              <span style={{ color: "#64748b", fontSize: "0.75rem" }}>None (Benign)</span>
                            ) : (
                              <span
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "4px",
                                  padding: "2px 8px",
                                  borderRadius: "4px",
                                  backgroundColor: "#fee2e2",
                                  color: "#b91c1c",
                                  fontSize: "0.72rem",
                                  fontWeight: 700,
                                }}
                              >
                                <AlertTriangle size={12} />
                                {frame.threat_injected}
                              </span>
                            )}
                          </td>
                          <td style={{ padding: "12px 16px", fontFamily: "monospace", color: "#475569" }}>
                            {frame.verification_latency_ms.toFixed(2)} ms
                          </td>
                          <td style={{ padding: "12px 16px" }}>
                            {frame.is_authenticated ? (
                              <span
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "4px",
                                  padding: "3px 8px",
                                  borderRadius: "6px",
                                  backgroundColor: "#dcfce7",
                                  color: "#15803d",
                                  fontSize: "0.72rem",
                                  fontWeight: 700,
                                }}
                              >
                                <ShieldCheck size={12} />
                                DISPATCHED
                              </span>
                            ) : (
                              <span
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "4px",
                                  padding: "3px 8px",
                                  borderRadius: "6px",
                                  backgroundColor: "#fee2e2",
                                  color: "#dc2626",
                                  fontSize: "0.72rem",
                                  fontWeight: 700,
                                }}
                              >
                                <ShieldAlert size={12} />
                                REJECTED
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Selected Frame Deep-Dive Inspector */}
            {selectedFrame && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "12px",
                  padding: "20px",
                  border: "1px solid #e2e8f0",
                  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        padding: "6px",
                        borderRadius: "8px",
                        backgroundColor: selectedFrame.is_authenticated ? "#ecfdf5" : "#fef2f2",
                      }}
                    >
                      {selectedFrame.is_authenticated ? (
                        <ShieldCheck size={20} color="#059669" />
                      ) : (
                        <ShieldAlert size={20} color="#dc2626" />
                      )}
                    </div>
                    <div>
                      <h4 style={{ fontSize: "0.95rem", fontWeight: 700, margin: 0, color: "#0f172a" }}>
                        Frame #{selectedFrame.sequence_count} Forensic Inspection
                      </h4>
                      <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
                        Action: <b>{selectedFrame.action}</b> • Latency: <b>{selectedFrame.verification_latency_ms} ms</b>
                      </span>
                    </div>
                  </div>

                  <span
                    style={{
                      padding: "4px 12px",
                      borderRadius: "6px",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      backgroundColor: selectedFrame.is_authenticated ? "#dcfce7" : "#fee2e2",
                      color: selectedFrame.is_authenticated ? "#166534" : "#991b1b",
                    }}
                  >
                    {selectedFrame.bus_state}
                  </span>
                </div>

                <div
                  style={{
                    backgroundColor: "#f8fafc",
                    borderRadius: "8px",
                    padding: "14px",
                    border: "1px solid #e2e8f0",
                    fontSize: "0.8rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b" }}>Threat Category:</span>
                    <span style={{ fontWeight: 600, color: selectedFrame.threat_injected === "NO_THREAT_BENIGN" ? "#0f172a" : "#dc2626" }}>
                      {selectedFrame.threat_injected}
                    </span>
                  </div>

                  {selectedFrame.rejection_reason && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginTop: "4px" }}>
                      <span style={{ color: "#991b1b", fontWeight: 700 }}>Firewall Rejection Verdict:</span>
                      <div
                        style={{
                          backgroundColor: "#fef2f2",
                          padding: "8px 12px",
                          borderRadius: "6px",
                          border: "1px solid #fecaca",
                          color: "#991b1b",
                          fontSize: "0.75rem",
                          fontFamily: "monospace",
                        }}
                      >
                        {selectedFrame.rejection_reason}
                      </div>
                    </div>
                  )}

                  {!selectedFrame.rejection_reason && (
                    <div style={{ color: "#059669", fontWeight: 600, fontSize: "0.75rem" }}>
                      ✓ Verified against CRYSTALS-Dilithium-5 digital signature, monotonic sequence counter within sliding window, and valid session HMAC.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
