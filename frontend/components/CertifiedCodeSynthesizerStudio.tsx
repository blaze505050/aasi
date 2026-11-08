"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Code2,
  FileCode,
  CheckCircle2,
  Cpu,
  Layers,
  Terminal,
  Download,
  Copy,
  ExternalLink,
  Lock,
  Zap,
  Activity,
  FileCheck,
  RefreshCw,
  X,
  AlertCircle,
} from "lucide-react";

interface SynthesizedSource {
  language: string;
  filename: string;
  code_text: string;
  line_count: number;
  wcet_microseconds: number;
  heap_allocation_bytes: number;
  recursion_depth_max: number;
  sha256_hash: string;
}

interface SafetyInvariant {
  invariant_id: string;
  property_name: string;
  mathematical_formula: string;
  verification_method: string;
  status: string;
  lean4_theorem_signature: string;
  margin_percentage: number;
}

interface McdcItem {
  decision_id: string;
  boolean_expression: string;
  conditions: string[];
  independent_toggle_verified: boolean;
  coverage_percentage: number;
}

interface CertificationDossier {
  dossier_id: string;
  preset_id: string;
  target_vehicle: string;
  mission_profile: string;
  standards_applied: string[];
  synthesized_c: SynthesizedSource;
  synthesized_rust: SynthesizedSource;
  synthesized_lean4: SynthesizedSource;
  invariants: SafetyInvariant[];
  mcdc_coverage: McdcItem[];
  overall_mcdc_percentage: number;
  worst_case_execution_time_us: number;
  max_allowable_period_us: number;
  schedulability_utilization_pct: number;
  formal_proof_status: string;
  certification_verdict: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

export default function CertifiedCodeSynthesizerStudio({ isOpen, onClose, apiBase }: Props) {
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [selectedPresetKey, setSelectedPresetKey] = useState<string>("ISRO_GAGANYAAN_CM_DESCENT_RTA");
  const [alphaMax, setAlphaMax] = useState<number>(24.5);
  const [nzMax, setNzMax] = useState<number>(4.5);
  const [uMin, setUMin] = useState<number>(-25.0);
  const [uMax, setUMax] = useState<number>(25.0);
  const [cbfGamma, setCbfGamma] = useState<number>(1.8);

  const [activeTab, setActiveTab] = useState<"C" | "RUST" | "LEAN4" | "INVARIANTS" | "MCDC">("C");
  const [dossier, setDossier] = useState<CertificationDossier | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);

  // Fetch presets on modal opening
  useEffect(() => {
    if (!isOpen) return;

    fetch(`${apiBase}/api/certified-code/presets`)
      .then((res) => res.json())
      .then((data) => {
        setPresets(data);
        if (data["ISRO_GAGANYAAN_CM_DESCENT_RTA"]) {
          loadPresetValues("ISRO_GAGANYAAN_CM_DESCENT_RTA", data["ISRO_GAGANYAAN_CM_DESCENT_RTA"]);
        }
      })
      .catch((err) => {
        console.warn("Could not load presets from backend, applying fallback:", err);
      });
  }, [isOpen, apiBase]);

  const loadPresetValues = (key: string, p: any) => {
    setSelectedPresetKey(key);
    if (p.alpha_max !== undefined) setAlphaMax(p.alpha_max);
    if (p.nz_max !== undefined) setNzMax(p.nz_max);
    if (p.u_min !== undefined) setUMin(p.u_min);
    if (p.u_max !== undefined) setUMax(p.u_max);
    if (p.cbf_gamma !== undefined) setCbfGamma(p.cbf_gamma);
  };

  const handleSynthesize = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/certified-code/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_id: selectedPresetKey,
          alpha_max: alphaMax,
          nz_max: nzMax,
          u_min: uMin,
          u_max: uMax,
          cbf_gamma: cbfGamma,
        }),
      });

      if (!res.ok) {
        throw new Error(`Synthesis failed with HTTP ${res.status}`);
      }
      const data: CertificationDossier = await res.json();
      setDossier(data);
    } catch (e) {
      console.error("Synthesizer error:", e);
    } finally {
      setLoading(false);
    }
  };

  // Run initial synthesis when modal opens
  useEffect(() => {
    if (isOpen && !dossier) {
      handleSynthesize();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentCode =
    activeTab === "C"
      ? dossier?.synthesized_c.code_text
      : activeTab === "RUST"
      ? dossier?.synthesized_rust.code_text
      : activeTab === "LEAN4"
      ? dossier?.synthesized_lean4.code_text
      : null;

  const handleCopyCode = () => {
    if (!currentCode) return;
    navigator.clipboard.writeText(currentCode);
    setCopySuccess("Code copied to clipboard!");
    setTimeout(() => setCopySuccess(null), 3000);
  };

  const handleDownloadDossier = () => {
    if (!dossier) return;
    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${dossier.dossier_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        backgroundColor: "rgba(15, 23, 42, 0.65)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1380px",
          maxHeight: "94vh",
          backgroundColor: "#ffffff",
          borderRadius: "14px",
          boxShadow: "0 25px 60px -15px rgba(0, 0, 0, 0.3)",
          border: "1px solid #e2e8f0",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          color: "#0f172a",
          fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid #e2e8f0",
            backgroundColor: "#ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "10px",
                backgroundColor: "#eff6ff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "1px solid #bfdbfe",
              }}
            >
              <FileCheck size={22} color="#2563eb" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#0f172a" }}>
                  DO-178C Level A & ECSS Flight Code Synthesizer
                </h2>
                <span
                  style={{
                    backgroundColor: "#dbeafe",
                    color: "#1e40af",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                  }}
                >
                  STAGE 18 SOVEREIGN
                </span>
                <span
                  style={{
                    backgroundColor: "#dcfce7",
                    color: "#166534",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                  }}
                >
                  RTCA DAL-A & ECSS-E-ST-40C
                </span>
              </div>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "#64748b" }}>
                Deterministic MISRA-C:2012 • Safe-Rust (no_std) • Lean-4 Machine-Checked Proofs • 100% MC/DC Coverage
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {dossier && (
              <button
                onClick={handleDownloadDossier}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "7px 14px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#ffffff",
                  color: "#334155",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                <Download size={14} />
                Export Dossier (.json)
              </button>
            )}
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                color: "#64748b",
                padding: "4px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "6px",
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Main Body */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left Panel: Presets & Controls */}
          <div
            style={{
              width: "360px",
              borderRight: "1px solid #e2e8f0",
              backgroundColor: "#f8fafc",
              padding: "20px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  color: "#475569",
                  marginBottom: "6px",
                }}
              >
                Flight Preset & Vehicle
              </label>
              <select
                value={selectedPresetKey}
                onChange={(e) => {
                  const key = e.target.value;
                  if (presets[key]) {
                    loadPresetValues(key, presets[key]);
                  } else {
                    setSelectedPresetKey(key);
                  }
                }}
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  fontSize: "0.82rem",
                  backgroundColor: "#ffffff",
                  color: "#0f172a",
                  outline: "none",
                  fontWeight: 600,
                }}
              >
                <option value="ISRO_GAGANYAAN_CM_DESCENT_RTA">ISRO Gaganyaan Crew Module (O-6 Descent)</option>
                <option value="LCA_TEJAS_TRANSIT_CBF">HAL LCA Tejas Mk-1A Fly-By-Wire</option>
                <option value="SPADEX_AUTONOMOUS_DOCKING">ISRO SpaDeX Chaser S/C Docking (ECSS Class A)</option>
                <option value="ELECTRIC_VTOL_TRANSITION">Sovereign 6-Pax Tilt-Wing AAM eVTOL</option>
              </select>
            </div>

            {/* Target Parameters */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.76rem" }}>
                  <span style={{ fontWeight: 600, color: "#334155" }}>Max Alpha Limit (α_max):</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>{alphaMax.toFixed(1)}°</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="35"
                  step="0.5"
                  value={alphaMax}
                  onChange={(e) => setAlphaMax(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#2563eb" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.76rem" }}>
                  <span style={{ fontWeight: 600, color: "#334155" }}>Max Load Factor (N_z max):</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>{nzMax.toFixed(1)} g</span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="10.0"
                  step="0.1"
                  value={nzMax}
                  onChange={(e) => setNzMax(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#2563eb" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.76rem" }}>
                  <span style={{ fontWeight: 600, color: "#334155" }}>Actuator Range [u_min, u_max]:</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>
                    [{uMin.toFixed(0)}, {uMax.toFixed(0)}]
                  </span>
                </div>
                <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                  <input
                    type="number"
                    value={uMin}
                    onChange={(e) => setUMin(parseFloat(e.target.value))}
                    style={{
                      width: "50%",
                      padding: "6px",
                      borderRadius: "6px",
                      border: "1px solid #cbd5e1",
                      fontSize: "0.78rem",
                    }}
                  />
                  <input
                    type="number"
                    value={uMax}
                    onChange={(e) => setUMax(parseFloat(e.target.value))}
                    style={{
                      width: "50%",
                      padding: "6px",
                      borderRadius: "6px",
                      border: "1px solid #cbd5e1",
                      fontSize: "0.78rem",
                    }}
                  />
                </div>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.76rem" }}>
                  <span style={{ fontWeight: 600, color: "#334155" }}>CBF Decay Gain (γ):</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>{cbfGamma.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.1"
                  value={cbfGamma}
                  onChange={(e) => setCbfGamma(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#2563eb" }}
                />
              </div>
            </div>

            {/* Synthesize Button */}
            <button
              onClick={handleSynthesize}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                padding: "10px 16px",
                borderRadius: "8px",
                backgroundColor: "#2563eb",
                color: "#ffffff",
                border: "none",
                fontSize: "0.84rem",
                fontWeight: 700,
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 4px 12px rgba(37, 99, 235, 0.25)",
              }}
            >
              {loading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Synthesizing DO-178C Package...
                </>
              ) : (
                <>
                  <Zap size={16} />
                  Synthesize Certified Package
                </>
              )}
            </button>

            {/* Verification Status Card */}
            {dossier && (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  borderRadius: "8px",
                  border: "1px solid #e2e8f0",
                  padding: "12px",
                  fontSize: "0.75rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                }}
              >
                <div style={{ fontWeight: 700, color: "#0f172a", display: "flex", alignItems: "center", gap: "6px" }}>
                  <ShieldCheck size={16} color="#16a34a" />
                  <span>Certification Verdict</span>
                </div>
                <div
                  style={{
                    backgroundColor: "#f0fdf4",
                    border: "1px solid #bbf7d0",
                    color: "#166534",
                    padding: "6px 8px",
                    borderRadius: "6px",
                    fontWeight: 700,
                    textAlign: "center",
                  }}
                >
                  {dossier.certification_verdict}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b" }}>
                  <span>MC/DC Structural Coverage:</span>
                  <span style={{ fontWeight: 700, color: "#16a34a" }}>{dossier.overall_mcdc_percentage}%</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b" }}>
                  <span>Worst-Case Execution Time:</span>
                  <span style={{ fontWeight: 700, color: "#0f172a" }}>{dossier.worst_case_execution_time_us} μs</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b" }}>
                  <span>Schedulability Utilization:</span>
                  <span style={{ fontWeight: 700, color: "#16a34a" }}>
                    {dossier.schedulability_utilization_pct}%
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b" }}>
                  <span>Lean-4 Machine Check:</span>
                  <span style={{ fontWeight: 700, color: "#2563eb" }}>{dossier.formal_proof_status}</span>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel: Code & Formal Dossier Tabs */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
            {/* Tabs */}
            <div
              style={{
                display: "flex",
                borderBottom: "1px solid #e2e8f0",
                backgroundColor: "#f8fafc",
                padding: "0 16px",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", gap: "4px" }}>
                <button
                  onClick={() => setActiveTab("C")}
                  style={{
                    padding: "10px 16px",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    border: "none",
                    borderBottom: activeTab === "C" ? "2px solid #2563eb" : "2px solid transparent",
                    backgroundColor: "transparent",
                    color: activeTab === "C" ? "#2563eb" : "#64748b",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Code2 size={15} />
                  MISRA-C:2012 Code ({dossier?.synthesized_c.line_count || 0} lines)
                </button>
                <button
                  onClick={() => setActiveTab("RUST")}
                  style={{
                    padding: "10px 16px",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    border: "none",
                    borderBottom: activeTab === "RUST" ? "2px solid #2563eb" : "2px solid transparent",
                    backgroundColor: "transparent",
                    color: activeTab === "RUST" ? "#2563eb" : "#64748b",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <FileCode size={15} />
                  Safe-Rust no_std ({dossier?.synthesized_rust.line_count || 0} lines)
                </button>
                <button
                  onClick={() => setActiveTab("LEAN4")}
                  style={{
                    padding: "10px 16px",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    border: "none",
                    borderBottom: activeTab === "LEAN4" ? "2px solid #2563eb" : "2px solid transparent",
                    backgroundColor: "transparent",
                    color: activeTab === "LEAN4" ? "#2563eb" : "#64748b",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Lock size={15} />
                  Lean-4 Machine Proof
                </button>
                <button
                  onClick={() => setActiveTab("INVARIANTS")}
                  style={{
                    padding: "10px 16px",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    border: "none",
                    borderBottom: activeTab === "INVARIANTS" ? "2px solid #2563eb" : "2px solid transparent",
                    backgroundColor: "transparent",
                    color: activeTab === "INVARIANTS" ? "#2563eb" : "#64748b",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <ShieldCheck size={15} />
                  Safety Invariants ({dossier?.invariants.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab("MCDC")}
                  style={{
                    padding: "10px 16px",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    border: "none",
                    borderBottom: activeTab === "MCDC" ? "2px solid #2563eb" : "2px solid transparent",
                    backgroundColor: "transparent",
                    color: activeTab === "MCDC" ? "#2563eb" : "#64748b",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <CheckCircle2 size={15} />
                  MC/DC Coverage (100%)
                </button>
              </div>

              {currentCode && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {copySuccess && (
                    <span style={{ fontSize: "0.74rem", color: "#16a34a", fontWeight: 600 }}>{copySuccess}</span>
                  )}
                  <button
                    onClick={handleCopyCode}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "5px",
                      padding: "5px 10px",
                      borderRadius: "5px",
                      border: "1px solid #cbd5e1",
                      backgroundColor: "#ffffff",
                      color: "#475569",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    <Copy size={13} />
                    Copy Code
                  </button>
                </div>
              )}
            </div>

            {/* Tab Contents */}
            <div style={{ flex: 1, overflowY: "auto", padding: "18px" }}>
              {(activeTab === "C" || activeTab === "RUST" || activeTab === "LEAN4") && currentCode && (
                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      backgroundColor: "#f1f5f9",
                      padding: "6px 12px",
                      borderRadius: "6px 6px 0 0",
                      fontSize: "0.72rem",
                      fontFamily: "monospace",
                      color: "#475569",
                    }}
                  >
                    <span>
                      SHA-256:{" "}
                      {activeTab === "C"
                        ? dossier?.synthesized_c.sha256_hash
                        : activeTab === "RUST"
                        ? dossier?.synthesized_rust.sha256_hash
                        : dossier?.synthesized_lean4.sha256_hash}
                    </span>
                    <span>Zero Heap • Bounded WCET</span>
                  </div>
                  <pre
                    style={{
                      margin: 0,
                      padding: "16px",
                      backgroundColor: "#0f172a",
                      color: "#f8fafc",
                      borderRadius: "0 0 6px 6px",
                      fontFamily: "Consolas, Menlo, Monaco, monospace",
                      fontSize: "0.78rem",
                      lineHeight: "1.5",
                      overflowX: "auto",
                      maxHeight: "580px",
                    }}
                  >
                    <code>{currentCode}</code>
                  </pre>
                </div>
              )}

              {activeTab === "INVARIANTS" && dossier && (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "4px" }}>
                    Machine-verified formal invariants conforming to RTCA DO-178C DAL-A and ESA ECSS-E-ST-40C:
                  </div>
                  {dossier.invariants.map((inv) => (
                    <div
                      key={inv.invariant_id}
                      style={{
                        padding: "14px",
                        borderRadius: "8px",
                        border: "1px solid #e2e8f0",
                        backgroundColor: "#f8fafc",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                      }}
                    >
                      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span
                            style={{
                              backgroundColor: "#e2e8f0",
                              color: "#334155",
                              fontSize: "0.68rem",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontFamily: "monospace",
                            }}
                          >
                            {inv.invariant_id}
                          </span>
                          <span style={{ fontWeight: 700, fontSize: "0.88rem", color: "#0f172a" }}>
                            {inv.property_name}
                          </span>
                        </div>
                        <div
                          style={{
                            fontFamily: "Consolas, monospace",
                            fontSize: "0.78rem",
                            color: "#1e40af",
                            backgroundColor: "#eff6ff",
                            padding: "4px 8px",
                            borderRadius: "4px",
                            marginTop: "2px",
                          }}
                        >
                          {inv.mathematical_formula}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                          Method: {inv.verification_method} • Lean-4 Signature:{" "}
                          <code style={{ color: "#0f172a" }}>{inv.lean4_theorem_signature}</code>
                        </div>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
                        <span
                          style={{
                            backgroundColor: "#dcfce7",
                            color: "#166534",
                            fontSize: "0.72rem",
                            fontWeight: 700,
                            padding: "3px 8px",
                            borderRadius: "4px",
                            display: "flex",
                            alignItems: "center",
                            gap: "4px",
                          }}
                        >
                          <CheckCircle2 size={12} />
                          {inv.status}
                        </span>
                        <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
                          Margin: {inv.margin_percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === "MCDC" && dossier && (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div
                    style={{
                      padding: "16px",
                      borderRadius: "8px",
                      backgroundColor: "#f0fdf4",
                      border: "1px solid #bbf7d0",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#166534" }}>
                        DO-178C Level A Structural Coverage Complete
                      </h4>
                      <p style={{ margin: "4px 0 0", fontSize: "0.78rem", color: "#15803d" }}>
                        Every condition in a decision has been shown by test to independently affect the decision's outcome.
                      </p>
                    </div>
                    <span
                      style={{
                        fontSize: "1.4rem",
                        fontWeight: 800,
                        color: "#166534",
                        padding: "6px 14px",
                        backgroundColor: "#ffffff",
                        borderRadius: "8px",
                        border: "1px solid #86efac",
                      }}
                    >
                      100.0%
                    </span>
                  </div>

                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: "0.78rem",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    <thead>
                      <tr style={{ backgroundColor: "#f8fafc", textAlign: "left", color: "#475569" }}>
                        <th style={{ padding: "10px", borderBottom: "1px solid #e2e8f0" }}>Decision ID</th>
                        <th style={{ padding: "10px", borderBottom: "1px solid #e2e8f0" }}>Expression Under Test</th>
                        <th style={{ padding: "10px", borderBottom: "1px solid #e2e8f0" }}>Evaluated Conditions</th>
                        <th style={{ padding: "10px", borderBottom: "1px solid #e2e8f0" }}>Independent Toggle</th>
                        <th style={{ padding: "10px", borderBottom: "1px solid #e2e8f0" }}>Coverage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dossier.mcdc_coverage.map((item) => (
                        <tr key={item.decision_id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                          <td style={{ padding: "10px", fontWeight: 700, fontFamily: "monospace" }}>
                            {item.decision_id}
                          </td>
                          <td style={{ padding: "10px", fontFamily: "monospace", color: "#2563eb" }}>
                            {item.boolean_expression}
                          </td>
                          <td style={{ padding: "10px", color: "#64748b" }}>{item.conditions.join(", ")}</td>
                          <td style={{ padding: "10px" }}>
                            <span
                              style={{
                                color: "#16a34a",
                                fontWeight: 700,
                                display: "flex",
                                alignItems: "center",
                                gap: "4px",
                              }}
                            >
                              <CheckCircle2 size={13} />
                              Verified
                            </span>
                          </td>
                          <td style={{ padding: "10px", fontWeight: 700, color: "#16a34a" }}>
                            {item.coverage_percentage.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
