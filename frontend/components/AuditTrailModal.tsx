"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Hash,
  Clock,
  UserCheck,
  RefreshCw,
  X,
  FileCheck,
  CheckCircle2,
  Lock,
} from "lucide-react";

interface AuditEntry {
  sequence_num: number;
  entry_id: string;
  timestamp: string;
  org_id: string;
  user_id: string;
  action: string;
  resource_id: string;
  details: Record<string, any>;
  current_hash: string;
  prev_hash: string;
}

interface VerificationResult {
  valid: boolean;
  entries_checked: number;
  head_sequence?: number;
  head_hash?: string;
  status: string;
  reason?: string;
}

interface AuditTrailModalProps {
  isOpen: boolean;
  onClose: () => void;
  orgId?: string;
  apiBase?: string;
}

export const AuditTrailModal: React.FC<AuditTrailModalProps> = ({
  isOpen,
  onClose,
  orgId = "default",
  apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
}) => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verification, setVerification] = useState<VerificationResult | null>(null);

  const fetchAuditLog = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/observability/audit-log?org_id=${orgId}&limit=50`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
      }
    } catch (e) {
      console.error("Failed to fetch audit log:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await fetch(`${apiBase}/api/observability/audit-log/verify`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setVerification(data);
      }
    } catch (e) {
      setVerification({
        valid: false,
        entries_checked: 0,
        status: "VERIFICATION_ERROR",
        reason: "Could not connect to audit verification service.",
      });
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAuditLog();
      handleVerifyChain();
    }
  }, [isOpen, orgId]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(3, 7, 18, 0.85)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "20px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "960px",
          maxHeight: "90vh",
          backgroundColor: "#0b101b",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "16px",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.8)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "rgba(15, 23, 42, 0.6)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                backgroundColor: "rgba(56, 189, 248, 0.12)",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#38bdf8",
              }}
            >
              <Lock size={20} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                  Cryptographic Audit Trail
                </h2>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.68rem",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    backgroundColor: "rgba(56, 189, 248, 0.12)",
                    color: "#38bdf8",
                    fontWeight: 600,
                  }}
                >
                  SHA-256 APPEND-ONLY CHAIN
                </span>
              </div>
              <p style={{ fontSize: "0.8rem", color: "#94a3b8", margin: 0, marginTop: "2px" }}>
                Immutable transaction ledger verifying zero data tampering for FAA, EASA, and ASME V&amp;V 20 compliance.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              onClick={handleVerifyChain}
              disabled={verifying}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "8px",
                backgroundColor: "rgba(56, 189, 248, 0.15)",
                border: "1px solid rgba(56, 189, 248, 0.35)",
                color: "#38bdf8",
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: verifying ? "not-allowed" : "pointer",
              }}
            >
              <RefreshCw size={14} className={verifying ? "animate-spin" : ""} />
              <span>{verifying ? "Verifying..." : "Verify Hash Chain"}</span>
            </button>
            <button
              onClick={onClose}
              style={{
                backgroundColor: "transparent",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
                padding: "6px",
                borderRadius: "6px",
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Verification Status Banner */}
        {verification && (
          <div
            style={{
              padding: "12px 24px",
              backgroundColor: verification.valid ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.1)",
              borderBottom: `1px solid ${verification.valid ? "rgba(16, 185, 129, 0.25)" : "rgba(239, 68, 68, 0.3)"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              {verification.valid ? (
                <ShieldCheck size={18} color="#10b981" />
              ) : (
                <ShieldAlert size={18} color="#ef4444" />
              )}
              <span
                style={{
                  fontSize: "0.84rem",
                  fontWeight: 600,
                  color: verification.valid ? "#34d399" : "#f87171",
                }}
              >
                {verification.valid
                  ? `CHAIN INTEGRITY VERIFIED: All ${verification.entries_checked} transactions sealed with 100% mathematical validity`
                  : `CHAIN INTEGRITY BREACH: ${verification.reason || "Hash mismatch detected"}`}
              </span>
            </div>

            {verification.head_hash && (
              <span style={{ fontSize: "0.72rem", color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                Head Hash: <span style={{ color: "#38bdf8" }}>{verification.head_hash.slice(0, 16)}...</span>
              </span>
            )}
          </div>
        )}

        {/* Content Table */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
              <p style={{ margin: 0, fontSize: "0.85rem" }}>Loading cryptographic audit ledger...</p>
            </div>
          ) : entries.length === 0 ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
              <CheckCircle2 size={32} color="#10b981" style={{ margin: "0 auto 12px" }} />
              <p style={{ margin: 0, fontSize: "0.9rem", color: "#f8fafc", fontWeight: 600 }}>
                Ledger Initialized &amp; Ready
              </p>
              <p style={{ margin: 0, marginTop: "4px", fontSize: "0.8rem" }}>
                Every investigation run, simulation, and ASME V&amp;V 20 PDF export is cryptographically chained.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {entries.map((entry) => (
                <div
                  key={entry.entry_id}
                  style={{
                    backgroundColor: "rgba(15, 23, 42, 0.5)",
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                    borderRadius: "10px",
                    padding: "14px 16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.72rem",
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        #{entry.sequence_num}
                      </span>
                      <span
                        style={{
                          fontSize: "0.82rem",
                          fontWeight: 700,
                          color: "#f8fafc",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {entry.action}
                      </span>
                      <span
                        style={{
                          fontSize: "0.74rem",
                          color: "#38bdf8",
                          backgroundColor: "rgba(56, 189, 248, 0.1)",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        {entry.resource_id}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.74rem", color: "#64748b" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Clock size={12} />
                        {new Date(entry.timestamp).toLocaleString()}
                      </span>
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <UserCheck size={12} />
                        {entry.user_id}
                      </span>
                    </div>
                  </div>

                  {/* Hash Chain Details */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "12px",
                      marginTop: "4px",
                      padding: "8px 12px",
                      backgroundColor: "rgba(2, 6, 23, 0.6)",
                      borderRadius: "6px",
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.7rem",
                    }}
                  >
                    <div>
                      <span style={{ color: "#64748b" }}>Current Block Hash (SHA-256): </span>
                      <span style={{ color: "#38bdf8" }}>{entry.current_hash.slice(0, 24)}...</span>
                    </div>
                    <div>
                      <span style={{ color: "#64748b" }}>Previous Block Hash: </span>
                      <span style={{ color: "#94a3b8" }}>{entry.prev_hash.slice(0, 24)}...</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "14px 24px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            fontSize: "0.76rem",
            color: "#94a3b8",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <FileCheck size={14} color="#10b981" />
            <span>Compliant with ASME V&amp;V 20-2009 Standard for Verification &amp; Validation</span>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: "6px 16px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "#f8fafc",
              fontSize: "0.78rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
