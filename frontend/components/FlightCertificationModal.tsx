"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  FileText,
  Download,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  GitBranch,
  Copy,
  Check,
  X,
  Cpu,
  Layers,
  Award,
} from "lucide-react";

export interface FlightCertificationModalProps {
  apiBase?: string;
  isOpen: boolean;
  onClose: () => void;
  investigation: {
    investigation_id: string;
    job_id: string;
    geometry: string;
    alpha_deg: number;
    reynolds: number;
    mach: number;
    cl?: number | null;
    cd?: number | null;
    cm?: number | null;
  } | null;
}

interface DossierData {
  dossier_id: string;
  job_id: string;
  generated_at_utc: string;
  geometry: {
    name: string;
    max_thickness_pct: number;
    max_camber_pct: number;
    sha256_hash: string;
  };
  conditions: {
    alpha_deg: number;
    reynolds: number;
    mach: number;
  };
  executive_verdict: string;
  is_flight_envelope_cleared: boolean;
  asme_vv20: {
    gci_fine_pct: number;
    observed_order_p: number;
    in_asymptotic_range: boolean;
    numerical_uncertainty_plus_minus: number;
    relative_approx_error_21_pct: number;
    summary_verdict: string;
  };
  nasa_cas: {
    composite_score_pct: number;
    credibility_tier: string;
    compliance_statement: string;
    categories: Array<{
      dimension_id: number;
      dimension_name: string;
      standard_clause: string;
      score: number;
      max_score: number;
      evidence_summary: string;
    }>;
  };
  provenance: {
    coordinate_sha256: string;
    results_sha256: string;
    verifier_signature: string;
    merkle_root_hash: string;
    lineage_node_id: string;
    node_count: number;
    epistemic_trust_tier: string;
  };
}

export const FlightCertificationModal: React.FC<FlightCertificationModalProps> = ({
  apiBase = "http://127.0.0.1:8000",
  isOpen,
  onClose,
  investigation,
}) => {
  const [loading, setLoading] = useState(false);
  const [dossier, setDossier] = useState<DossierData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);
  const [activeTab, setActiveTab] = useState<"asme" | "nasa" | "merkle">("asme");

  useEffect(() => {
    if (!isOpen || !investigation) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    const fetchOrCreateDossier = async () => {
      try {
        const genRes = await fetch(`${apiBase}/api/v1/certification/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            job_id: investigation.job_id || investigation.investigation_id,
            geometry_name: investigation.geometry,
            alpha_deg: investigation.alpha_deg,
            reynolds: investigation.reynolds,
            mach: investigation.mach,
            live_cfd_results: investigation.cl != null ? { CL: investigation.cl, CD: investigation.cd || 0.01 } : null,
          }),
        });

        if (!genRes.ok) {
          throw new Error(`Failed to generate flight certification (${genRes.status})`);
        }

        const data = await genRes.json();
        if (isMounted) setDossier(data);
      } catch (err: any) {
        if (isMounted) setError(err.message || "Failed to load certification");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchOrCreateDossier();

    return () => {
      isMounted = false;
    };
  }, [isOpen, investigation, apiBase]);

  if (!isOpen) return null;

  const copyMerkleRoot = () => {
    const hash = dossier?.provenance?.merkle_root_hash || dossier?.provenance?.verifier_signature;
    if (hash && typeof navigator !== "undefined") {
      navigator.clipboard.writeText(hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleDownloadPdf = () => {
    if (!dossier) return;
    const url = `${apiBase}/api/v1/certification/${dossier.dossier_id}/pdf`;
    window.open(url, "_blank");
  };

  const handleViewHtml = () => {
    if (!dossier) return;
    const url = `${apiBase}/api/v1/certification/${dossier.dossier_id}/html`;
    window.open(url, "_blank");
  };

  const isCleared = dossier?.is_flight_envelope_cleared ?? false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl bg-[#0f172a] border border-[#1e293b] shadow-2xl overflow-hidden text-slate-100">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e293b] bg-[#131d35]/60">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-xl ${isCleared ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                Flight Certification Dossier
                <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-medium bg-[#1e293b] text-cyan-400 border border-cyan-500/20">
                  ASME V&amp;V 20 / NASA-STD-7009B
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                {investigation?.geometry} • &alpha; = {investigation?.alpha_deg}&deg; • Re = {investigation?.reynolds?.toExponential(1)} • Mach {investigation?.mach}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center space-y-3">
              <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
              <p className="text-sm text-slate-400 font-mono">Executing ASME V&amp;V 20 Richardson Extrapolation &amp; Merkle Lineage Sealing...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Certification Synthesis Error</p>
                <p className="text-xs opacity-80 mt-1">{error}</p>
              </div>
            </div>
          )}

          {dossier && !loading && (
            <>
              {/* Airworthiness Verdict Banner */}
              <div
                className={`p-4 rounded-xl border flex items-start justify-between gap-4 ${
                  isCleared
                    ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-200"
                    : "bg-amber-950/30 border-amber-500/30 text-amber-200"
                }`}
              >
                <div className="flex items-start gap-3">
                  {isCleared ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider">
                      {isCleared ? "AIRWORTHINESS CLEARED" : "CONDITIONALLY ACCEPTED"}
                    </h3>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                      {dossier.executive_verdict}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[10px] uppercase font-mono tracking-widest text-slate-400 block">Dossier ID</span>
                  <span className="font-mono text-sm font-bold text-white">{dossier.dossier_id}</span>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <button
                  onClick={() => setActiveTab("asme")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                    activeTab === "asme"
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Cpu className="w-3.5 h-3.5" />
                  ASME V&amp;V 20 GCI Study
                </button>
                <button
                  onClick={() => setActiveTab("nasa")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                    activeTab === "nasa"
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Award className="w-3.5 h-3.5" />
                  NASA-STD-7009B CAS Scorecard
                </button>
                <button
                  onClick={() => setActiveTab("merkle")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                    activeTab === "merkle"
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <GitBranch className="w-3.5 h-3.5" />
                  Cryptographic Merkle Proof
                </button>
              </div>

              {/* Tab 1: ASME V&V 20 Grid Convergence */}
              {activeTab === "asme" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-[#141d33] border border-slate-800">
                      <span className="text-[11px] text-slate-400 uppercase font-mono">Fine Grid GCI</span>
                      <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
                        &plusmn;{dossier.asme_vv20.gci_fine_pct.toFixed(2)}%
                      </p>
                      <span className="text-[10px] text-slate-500">Safety factor Fs = 1.25</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#141d33] border border-slate-800">
                      <span className="text-[11px] text-slate-400 uppercase font-mono">Observed Order (p)</span>
                      <p className="text-xl font-bold font-mono text-white mt-1">
                        {dossier.asme_vv20.observed_order_p.toFixed(2)}
                      </p>
                      <span className="text-[10px] text-slate-500">Formal order = 2.00</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#141d33] border border-slate-800">
                      <span className="text-[11px] text-slate-400 uppercase font-mono">Relative Error (e21)</span>
                      <p className="text-xl font-bold font-mono text-white mt-1">
                        {dossier.asme_vv20.relative_approx_error_21_pct.toFixed(2)}%
                      </p>
                      <span className="text-[10px] text-slate-500">Fine vs. medium mesh</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-[#141d33] border border-slate-800">
                      <span className="text-[11px] text-slate-400 uppercase font-mono">Asymptotic Regime</span>
                      <p className={`text-base font-bold font-mono mt-1 ${dossier.asme_vv20.in_asymptotic_range ? "text-emerald-400" : "text-amber-400"}`}>
                        {dossier.asme_vv20.in_asymptotic_range ? "VERIFIED (1.00)" : "BOUNDED"}
                      </p>
                      <span className="text-[10px] text-slate-500">Richardson condition</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-[#141d33]/50 border border-slate-800 text-xs text-slate-300">
                    <p className="font-semibold text-white mb-1">ASME V&amp;V 20 Convergence Assessment</p>
                    <p>{dossier.asme_vv20.summary_verdict}</p>
                  </div>
                </div>
              )}

              {/* Tab 2: NASA-STD-7009B Credibility Assessment Scale */}
              {activeTab === "nasa" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#141d33] border border-slate-800">
                    <div>
                      <span className="text-xs text-slate-400 uppercase font-mono">NASA Credibility Rating</span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-2xl font-bold text-white">{dossier.nasa_cas.composite_score_pct}%</span>
                        <span className="px-2 py-0.5 rounded font-mono text-xs font-semibold bg-cyan-500/20 text-cyan-400">
                          {dossier.nasa_cas.credibility_tier} CREDIBILITY
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 max-w-sm text-right">
                      {dossier.nasa_cas.compliance_statement}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    {dossier.nasa_cas.categories.map((cat) => (
                      <div key={cat.dimension_id} className="p-3 rounded-lg bg-[#141d33]/40 border border-slate-800/80">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-white">
                            {cat.dimension_id}. {cat.dimension_name}
                          </span>
                          <span className="text-xs font-mono font-bold text-cyan-400">
                            {cat.score} / {cat.max_score}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                          {cat.evidence_summary}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: Cryptographic Merkle Lineage Proof */}
              {activeTab === "merkle" && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="p-4 rounded-xl bg-black/40 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Merkle Root Hash (Causal DAG Digest):</span>
                      <button
                        onClick={copyMerkleRoot}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 transition text-[11px]"
                      >
                        {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        {copiedHash ? "Copied" : "Copy Root"}
                      </button>
                    </div>
                    <p className="p-2.5 rounded bg-slate-950 text-cyan-400 break-all select-all border border-slate-800">
                      {dossier.provenance.merkle_root_hash || dossier.provenance.verifier_signature}
                    </p>
                    <div className="grid grid-cols-2 gap-3 text-[11px] text-slate-400 pt-2 border-t border-slate-850">
                      <div>
                        <span>Audit Node ID: </span>
                        <span className="text-slate-200">{dossier.provenance.lineage_node_id || "NODE-AUDIT"}</span>
                      </div>
                      <div>
                        <span>Lineage Blocks: </span>
                        <span className="text-slate-200">{dossier.provenance.node_count} sealed</span>
                      </div>
                      <div>
                        <span>Trust Tier: </span>
                        <span className="text-emerald-400 font-semibold">{dossier.provenance.epistemic_trust_tier}</span>
                      </div>
                      <div>
                        <span>Results SHA-256: </span>
                        <span className="text-slate-300">{dossier.provenance.results_sha256?.substring(0, 12)}...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#1e293b] bg-[#131d35]/60">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span>
            <span>Cryptographically sealed under Absolute Anti-Fabrication Rule</span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleViewHtml}
              disabled={!dossier || loading}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-semibold text-white flex items-center gap-1.5 transition border border-slate-700"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              View Airworthiness HTML
            </button>
            <button
              onClick={handleDownloadPdf}
              disabled={!dossier || loading}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-xs font-semibold text-white flex items-center gap-1.5 transition shadow-lg shadow-cyan-500/20"
            >
              <Download className="w-3.5 h-3.5" />
              Download Signed PDF Dossier
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
