"use client";

import React, { useState } from "react";
import {
  X,
  ShieldCheck,
  Cpu,
  Layers,
  Terminal,
  Zap,
  CheckCircle2,
  Lock,
  ArrowRight,
  Code2,
  Copy,
  Check,
} from "lucide-react";

interface EnterpriseOverviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenUpgrade?: () => void;
}

type TabKey = "ARCHITECTURE" | "VV20" | "SDK" | "TIERS";

const SDK_SNIPPET = `from aasi_client import AASIClient

# 1. Initialize certified enterprise client
client = AASIClient(base_url="http://127.0.0.1:8000", api_key="aasi_live_sec_key")

# 2. Sub-15ms Neural Surrogate Inference
polar = client.predict(geometry="NACA 0012", mach=0.15, reynolds=3e6, aoa_deg=4.0)
print(f"CL: {polar['cl']:.4f}, CD: {polar['cd']:.5f}")

# 3. Ground Truth Verification against NASA Langley LTPT Wind Tunnel
exp = client.get_experimental_benchmark(geometry="NACA 0012")
comparison = client.compare_against_wind_tunnel("NACA 0012", [polar])
assert comparison["is_asme_vv20_validated"], "ASME V&V 20 discrepancy exceeds tolerance"

# 4. Generate & Download Cryptographically Sealed ASME V&V 20 PDF Dossier
client.download_asme_certificate(job_id="JOB-CERT-001", output_path="NACA0012_Cert.pdf")`;

export function EnterpriseOverviewModal({
  isOpen,
  onClose,
  onOpenUpgrade,
}: EnterpriseOverviewModalProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("ARCHITECTURE");
  const [copiedCode, setCopiedCode] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(SDK_SNIPPET);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(3, 7, 18, 0.88)",
        backdropFilter: "blur(14px)",
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
          maxWidth: "1020px",
          maxHeight: "92vh",
          backgroundColor: "#0b101b",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "18px",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 30px 80px -20px rgba(0, 0, 0, 0.9)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "22px 28px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "linear-gradient(90deg, rgba(15, 23, 42, 0.8), rgba(2, 6, 23, 0.9))",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.7rem",
                  padding: "3px 8px",
                  borderRadius: "5px",
                  backgroundColor: "rgba(245, 158, 11, 0.15)",
                  color: "#f59e0b",
                  fontWeight: 700,
                  border: "1px solid rgba(245, 158, 11, 0.3)",
                }}
              >
                ENTERPRISE AEROSPACE PLATFORM
              </span>
              <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>ASME V&amp;V 20-2009 Standards Compliant</span>
            </div>
            <h1 style={{ fontSize: "1.3rem", fontWeight: 800, color: "#f8fafc", margin: "4px 0 0" }}>
              AASI Aerospace Engineering &amp; Verification Suite
            </h1>
          </div>

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

        {/* Tab Navigation */}
        <div
          style={{
            padding: "0 28px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            gap: "24px",
            backgroundColor: "rgba(15, 23, 42, 0.4)",
          }}
        >
          {[
            { id: "ARCHITECTURE", label: "Dual-Engine Architecture" },
            { id: "VV20", label: "ASME V&V 20 & Wind Tunnel" },
            { id: "SDK", label: "Python SDK (CI/CD)" },
            { id: "TIERS", label: "Commercial Licenses" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabKey)}
              style={{
                padding: "14px 4px",
                border: "none",
                borderBottom: activeTab === tab.id ? "2px solid #38bdf8" : "2px solid transparent",
                backgroundColor: "transparent",
                color: activeTab === tab.id ? "#38bdf8" : "#94a3b8",
                fontSize: "0.82rem",
                fontWeight: activeTab === tab.id ? 700 : 500,
                cursor: "pointer",
                transition: "all 150ms ease",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "28px" }}>
          {activeTab === "ARCHITECTURE" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "20px",
                }}
              >
                {/* Engine 1 */}
                <div
                  style={{
                    backgroundColor: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(56, 189, 248, 0.25)",
                    borderRadius: "12px",
                    padding: "20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        padding: "8px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(56, 189, 248, 0.15)",
                        color: "#38bdf8",
                      }}
                    >
                      <Zap size={20} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                        Physics AI Neural Operators
                      </h3>
                      <span style={{ fontSize: "0.74rem", color: "#38bdf8", fontFamily: "var(--font-mono)" }}>
                        Sub-15ms Instantaneous Inference
                      </span>
                    </div>
                  </div>
                  <p style={{ fontSize: "0.82rem", color: "#94a3b8", margin: 0, lineHeight: 1.5 }}>
                    Trained across 17,595 authentic Navier-Stokes simulations. Achieves high fidelity with epistemic ensemble variance bounds and zero hallucination.
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "auto" }}>
                    <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: "4px", color: "#cbd5e1" }}>
                      Deep Ensembles
                    </span>
                    <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: "4px", color: "#cbd5e1" }}>
                      Epistemic Bounds
                    </span>
                    <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: "4px", color: "#cbd5e1" }}>
                      Zero Hallucination
                    </span>
                  </div>
                </div>

                {/* Engine 2 */}
                <div
                  style={{
                    backgroundColor: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(245, 158, 11, 0.25)",
                    borderRadius: "12px",
                    padding: "20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        padding: "8px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(245, 158, 11, 0.15)",
                        color: "#f59e0b",
                      }}
                    >
                      <Cpu size={20} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                        Navier-Stokes CFD Orchestrator
                      </h3>
                      <span style={{ fontSize: "0.74rem", color: "#f59e0b", fontFamily: "var(--font-mono)" }}>
                        OpenFOAM · SU2 · High-Fidelity RANS
                      </span>
                    </div>
                  </div>
                  <p style={{ fontSize: "0.82rem", color: "#94a3b8", margin: 0, lineHeight: 1.5 }}>
                    Executes wall-resolved simpleFoam cases with k-omega SST closure, logarithmic residual decay monitoring down to 1e-6, and automated mesh refinement.
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "auto" }}>
                    <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: "4px", color: "#cbd5e1" }}>
                      Residual Tracking
                    </span>
                    <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: "4px", color: "#cbd5e1" }}>
                      Colab / Cloud Compute
                    </span>
                    <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: "4px", color: "#cbd5e1" }}>
                      ASME V&amp;V 20 GCI
                    </span>
                  </div>
                </div>
              </div>

              {/* Data Security Banner */}
              <div
                style={{
                  backgroundColor: "rgba(2, 6, 23, 0.6)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "12px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <Lock size={18} color="#10b981" />
                  <div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f8fafc" }}>
                      ITAR &amp; Defense Multi-Tenant Data Isolation
                    </div>
                    <div style={{ fontSize: "0.76rem", color: "#94a3b8" }}>
                      Every organization&apos;s geometry CAD, mesh decks, and polars are segregated with SQLite multi-tenant indexing.
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: "0.74rem", color: "#10b981", fontWeight: 600 }}>
                  ACTIVE ORG ISOLATION: ENABLED
                </div>
              </div>
            </div>
          )}

          {activeTab === "VV20" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <ShieldCheck size={28} color="#10b981" />
                <div>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                    ASME V&amp;V 20-2009 Standards Compliance
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8", margin: "2px 0 0" }}>
                    Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer
                  </p>
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: "16px",
                }}
              >
                <div style={{ backgroundColor: "rgba(15, 23, 42, 0.5)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "16px" }}>
                  <div style={{ fontSize: "0.78rem", color: "#38bdf8", fontWeight: 700, marginBottom: "6px" }}>
                    1. GRID CONVERGENCE INDEX (GCI)
                  </div>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", margin: 0, lineHeight: 1.4 }}>
                    Calculates apparent order of convergence p and Richardson extrapolation across 3 structured grid refinements with Fs = 1.25.
                  </p>
                </div>

                <div style={{ backgroundColor: "rgba(15, 23, 42, 0.5)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "16px" }}>
                  <div style={{ fontSize: "0.78rem", color: "#f59e0b", fontWeight: 700, marginBottom: "6px" }}>
                    2. WIND TUNNEL BENCHMARKS
                  </div>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", margin: 0, lineHeight: 1.4 }}>
                    Overlays 9,775 verified physical test points from NASA Langley LTPT (Ladson 1988), AGARD-AR-138, and UIUC with instrumentation bounds ±σ.
                  </p>
                </div>

                <div style={{ backgroundColor: "rgba(15, 23, 42, 0.5)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "16px" }}>
                  <div style={{ fontSize: "0.78rem", color: "#10b981", fontWeight: 700, marginBottom: "6px" }}>
                    3. VALIDATION UNCERTAINTY (u_val)
                  </div>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", margin: 0, lineHeight: 1.4 }}>
                    Evaluates comparison error |E| ≤ u_val. Blocks certification if simulation error exceeds empirical bounds.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "SDK" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                    Standalone Python Client (<code style={{ color: "#38bdf8" }}>aasi-client</code>)
                  </h3>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8", margin: "2px 0 0" }}>
                    Zero-dependency HTTP SDK for continuous aerospace certification in GitHub Actions or Jenkins.
                  </p>
                </div>
                <button
                  onClick={copyToClipboard}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 12px",
                    borderRadius: "6px",
                    backgroundColor: "rgba(255, 255, 255, 0.08)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    color: "#f8fafc",
                    fontSize: "0.76rem",
                    cursor: "pointer",
                  }}
                >
                  {copiedCode ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                  <span>{copiedCode ? "Copied!" : "Copy Snippet"}</span>
                </button>
              </div>

              <pre
                style={{
                  backgroundColor: "#020617",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "10px",
                  padding: "16px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.76rem",
                  color: "#cbd5e1",
                  lineHeight: 1.5,
                  overflowX: "auto",
                  margin: 0,
                }}
              >
                {SDK_SNIPPET}
              </pre>
            </div>
          )}

          {activeTab === "TIERS" && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "16px",
              }}
            >
              {/* Community */}
              <div
                style={{
                  backgroundColor: "rgba(15, 23, 42, 0.5)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div>
                  <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>Community</h4>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#38bdf8", marginTop: "4px" }}>
                    $0<span style={{ fontSize: "0.78rem", color: "#64748b" }}> / month</span>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.76rem", color: "#94a3b8" }}>
                  <div>✓ 5 Investigations / month</div>
                  <div>✓ Neural Surrogate Point Inference</div>
                  <div>✓ Standard PDF Export</div>
                </div>
              </div>

              {/* Team (Recommended) */}
              <div
                style={{
                  backgroundColor: "rgba(15, 23, 42, 0.7)",
                  border: "2px solid #f59e0b",
                  borderRadius: "12px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: "-10px",
                    right: "16px",
                    backgroundColor: "#f59e0b",
                    color: "#0f172a",
                    fontSize: "0.66rem",
                    fontWeight: 800,
                    padding: "2px 8px",
                    borderRadius: "4px",
                  }}
                >
                  MOST POPULAR
                </div>
                <div>
                  <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>Aerodynamics Team</h4>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#f59e0b", marginTop: "4px" }}>
                    $499<span style={{ fontSize: "0.78rem", color: "#64748b" }}> / month</span>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.76rem", color: "#e2e8f0" }}>
                  <div>✓ 500 Investigations / month</div>
                  <div>✓ Full ASME V&amp;V 20 Certification Engine</div>
                  <div>✓ Wind Tunnel Overlay (NASA / AGARD)</div>
                  <div>✓ Standalone Python SDK Access</div>
                  <div>✓ Cryptographic SHA-256 Audit Trail</div>
                </div>
                <button
                  onClick={() => {
                    onClose();
                    onOpenUpgrade?.();
                  }}
                  style={{
                    marginTop: "auto",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    backgroundColor: "#f59e0b",
                    border: "none",
                    color: "#0f172a",
                    fontWeight: 700,
                    fontSize: "0.8rem",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                  }}
                >
                  <span>Select Plan</span>
                  <ArrowRight size={14} />
                </button>
              </div>

              {/* Enterprise */}
              <div
                style={{
                  backgroundColor: "rgba(15, 23, 42, 0.5)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div>
                  <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>Enterprise Dedicated</h4>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#f8fafc", marginTop: "4px" }}>
                    $2,499<span style={{ fontSize: "0.78rem", color: "#64748b" }}> / month</span>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.76rem", color: "#94a3b8" }}>
                  <div>✓ Unlimited Investigations</div>
                  <div>✓ Private On-Premises Docker Deployment</div>
                  <div>✓ ITAR / Defense Air-Gapped Operation</div>
                  <div>✓ SLA 99.99% &amp; Dedicated CFD Engineer</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "16px 28px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: "rgba(15, 23, 42, 0.6)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.76rem", color: "#94a3b8" }}>
            <CheckCircle2 size={15} color="#10b981" />
            <span>FAA &amp; EASA Flight Clearance Ready · Dual Engine Architecture</span>
          </div>

          <button
            onClick={onClose}
            style={{
              padding: "7px 18px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "#f8fafc",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Close Overview
          </button>
        </div>
      </div>
    </div>
  );
}
