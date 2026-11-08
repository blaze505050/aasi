"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCcw,
  Zap,
  Activity,
  Layers,
  CheckCircle2,
  Lock,
  Compass,
  Sparkles,
  BookOpen,
  Microscope,
  Scale,
  Flame,
  FileText,
  X,
} from "lucide-react";

interface FalsificationCriterion {
  metric_name: string;
  target_value: number;
  tolerance_threshold: number;
  operator: string;
  mathematical_formula: string;
}

interface AgentMessage {
  step_number: number;
  agent_role: string;
  message_title: string;
  content: string;
  quantitative_data: Record<string, any>;
  epistemic_confidence: number;
  timestamp_s: number;
}

interface DiscoveryDossier {
  campaign_id: string;
  hypothesis_title: string;
  domain: string;
  proposed_mechanism: string;
  simulation_fidelity: string;
  bayes_factor: number;
  asme_gci_fine_pct: number;
  verdict: string;
  novelty_score_pct: number;
  scientific_impact_index: number;
  publication_readiness: string;
  merkle_provenance_hash: string;
  falsification_criteria: FalsificationCriterion[];
  agent_dialogue: AgentMessage[];
}

interface PresetItem {
  title: string;
  domain: string;
  mechanism: string;
  airframe: string;
}

export interface PopperianDiscoveryStudioProps {
  isOpen?: boolean;
  onClose?: () => void;
  apiBase?: string;
}

export default function PopperianDiscoveryStudio({
  isOpen,
  onClose,
  apiBase = "",
}: PopperianDiscoveryStudioProps = {}) {
  const [presets, setPresets] = useState<Record<string, PresetItem>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>("SUPERCRITICAL_BUFFET_DELAY");
  const [adversarialRigor, setAdversarialRigor] = useState<number>(1.0);
  const [enableAdaptiveMeshing, setEnableAdaptiveMeshing] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DiscoveryDossier | null>(null);
  const [statusNotice, setStatusNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    fetchPresets();
  }, [apiBase]);

  const fetchPresets = async () => {
    try {
      const res = await fetch(`${apiBase}/api/discovery/presets`);
      if (res.ok) {
        const data = await res.json();
        setPresets(data);
      }
    } catch {
      setPresets({
        SUPERCRITICAL_BUFFET_DELAY: {
          title: "Shock-Induced Separation Delay via Supercritical Biomimetic Curvature",
          domain: "Transonic Aerodynamics & Buffet Onset",
          mechanism: "Biomimetic continuous-curvature aft-camber relieves upper-surface supersonic recompression shock gradient, delaying buffet onset by > 1.8 deg AoA.",
          airframe: "SC(2)-0714 Modified Bio-Contoured Wing",
        },
        HYPERSONIC_WAVERIDER_ABLATION: {
          title: "Low-Boom Hypersonic Waverider Forebody Boundary Layer Preservation",
          domain: "Hypersonic Aerothermodynamics (Mach 8 to 14)",
          mechanism: "Anisotropic micro-grooved catalytic wall coating suppresses 2nd-mode acoustic instability waves, mitigating laminar-to-turbulent transition peak heat flux.",
          airframe: "ISRO RLV-TD / HSTDV Sharp Forebody",
        },
        ACTIVE_JET_BUFFET_SUPPRESSION: {
          title: "Synthetic Jet Array Dynamic Transonic Buffet Suppression",
          domain: "Active Flow Control & Fluid-Structure Interaction",
          mechanism: "Zero-net-mass-flux piezoceramic micro-jets operating at Helmholtz resonance break coherent vortex shedding behind lambda shock.",
          airframe: "NLR 7301 Benchmark Transonic Airfoil",
        },
        STRUT_BRACED_WING_LAMINAR: {
          title: "High-Aspect-Ratio Transonic Truss-Braced Wing Natural Laminar Flow",
          domain: "Sustainable Aviation & High-Aspect Wing Aeroelastics",
          mechanism: "Custom favorable pressure gradient profile maintains laminar boundary layer over 62% chord on an AR=19.5 strut-braced wing.",
          airframe: "Transonic Truss-Braced Wing (TTBW) Class",
        },
      });
    }
  };

  const runCampaign = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/discovery/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: selectedPreset,
          adversarial_rigor: adversarialRigor,
          enable_adaptive_meshing: enableAdaptiveMeshing,
        }),
      });

      if (!res.ok) throw new Error(`Discovery campaign failed with status ${res.status}`);

      const data: DiscoveryDossier = await res.json();
      setResult(data);
      setStatusNotice({
        type: data.verdict.startsWith("CORROBORATED") ? "success" : "error",
        text: data.verdict.startsWith("CORROBORATED")
          ? `Hypothesis Corroborated: Bayes Factor K = ${data.bayes_factor.toFixed(1)} • ASME GCI = ${data.asme_gci_fine_pct.toFixed(2)}% • ${data.publication_readiness}`
          : `Hypothesis Falsified: Adversarial stress test discovered boundary layer shock flutter (Bayes Factor K = ${data.bayes_factor.toFixed(2)})`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setStatusNotice({ type: "error", text: `Campaign execution failed: ${msg}` });
    } finally {
      setLoading(false);
    }
  };

  if (isOpen !== undefined && !isOpen) return null;

  const content = (
    <div className="w-full max-w-7xl mx-auto space-y-6 p-4 md:p-6 bg-slate-50 min-h-screen text-slate-900">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition"
            aria-label="Close studio"
          >
            <X className="w-5 h-5" />
          </button>
        )}
        <div className="pr-8">
          <div className="flex items-center gap-3">
            <span className="bg-purple-100 text-purple-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-purple-200">
              Stage 16 • Autonomous Discovery
            </span>
            <span className="bg-indigo-100 text-indigo-800 text-xs font-mono px-2 py-0.5 rounded border border-indigo-200">
              Popperian Falsification &amp; Multi-Agent AI
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Autonomous Popperian Hypothesis Falsification Engine
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-3xl">
            Closed-loop scientific discovery engine orchestrating Lead Scientist, Discretization Agent, Adversarial Popperian Agent, and Epistemic Metrology Auditor. Enforces strict Popperian falsifiability under ASME V&amp;V 20 CAS Level 4 and Bayesian evidence criteria.
          </p>
        </div>

        <button
          onClick={runCampaign}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium px-5 py-2.5 rounded-lg shadow-sm transition disabled:opacity-50 shrink-0"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Microscope className="w-4 h-4 text-purple-400" />
          )}
          {loading ? "Executing Multi-Agent Loop..." : "Initiate Discovery Campaign"}
        </button>
      </div>

      {statusNotice && (
        <div
          className={`px-4 py-2.5 rounded-lg border text-xs font-medium flex items-center justify-between ${
            statusNotice.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-red-50 text-red-800 border-red-200"
          }`}
        >
          <span>{statusNotice.text}</span>
          <button onClick={() => setStatusNotice(null)} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Control Configuration Deck */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Preset Selection */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs md:col-span-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 block">
            Scientific Hypothesis Campaign
          </label>
          <select
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            {Object.entries(presets).map(([k, v]) => (
              <option key={k} value={k}>
                {v.title}
              </option>
            ))}
          </select>
          {presets[selectedPreset] && (
            <p className="text-xs text-slate-500 mt-2">
              Domain: {presets[selectedPreset].domain} • Airframe: {presets[selectedPreset].airframe}
            </p>
          )}
        </div>

        {/* Adversarial Rigor Slider */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex justify-between text-xs text-slate-500">
            <span className="font-semibold uppercase tracking-wider">Adversarial Rigor</span>
            <span className="font-mono font-medium text-slate-900">{adversarialRigor.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.5"
            step="0.1"
            value={adversarialRigor}
            onChange={(e) => setAdversarialRigor(parseFloat(e.target.value))}
            className="w-full mt-1 accent-slate-900"
          />
          <p className="text-[11px] text-slate-400">
            {adversarialRigor > 1.8 ? "Extreme corner-case stress: likely to trigger falsification" : "Nominal peer-review stress testing"}
          </p>
        </div>

        {/* Adaptive Mesh Verification */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
              ASME V&amp;V 20 Adaptive Mesh
            </label>
            <Layers className="w-4 h-4 text-sky-600" />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => setEnableAdaptiveMeshing(!enableAdaptiveMeshing)}
              className={`w-full py-2 px-3 text-xs font-semibold rounded-lg border transition ${
                enableAdaptiveMeshing
                  ? "bg-sky-50 text-sky-800 border-sky-300"
                  : "bg-slate-100 text-slate-700 border-slate-300"
              }`}
            >
              {enableAdaptiveMeshing ? "3-GRID RICHARDSON (GCI < 1.5%)" : "SINGLE-GRID NOMINAL"}
            </button>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {enableAdaptiveMeshing ? "CAS Level 4 certified grid convergence" : "Uncertified numerical error"}
          </p>
        </div>
      </div>

      {/* Main Results View */}
      {result && (
        <div className="space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Popperian Verdict</span>
              <span className={`text-sm font-bold flex items-center gap-1 mt-1 ${result.verdict.startsWith("CORROBORATED") ? "text-emerald-700" : "text-red-700"}`}>
                {result.verdict.startsWith("CORROBORATED") ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Corroborated
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5" /> Falsified
                  </>
                )}
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Bayes Factor (K)</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.bayes_factor.toFixed(1)}
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">ASME GCI_fine</span>
              <span className="text-lg font-mono font-bold text-sky-700 mt-0.5 block">
                {result.asme_gci_fine_pct.toFixed(2)}%
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Novelty Score</span>
              <span className="text-lg font-mono font-bold text-purple-700 mt-0.5 block">
                {result.novelty_score_pct.toFixed(1)}%
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Impact Index</span>
              <span className="text-lg font-mono font-bold text-indigo-700 mt-0.5 block">
                {result.scientific_impact_index.toFixed(1)} / 10
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Publication Target</span>
              <span className="text-xs font-semibold text-slate-800 mt-1 block truncate">
                {result.publication_readiness.includes("NATURE") ? "Nature / Science" : "Archive Archive"}
              </span>
            </div>
          </div>

          {/* Falsification Criteria Compliance Board */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Scale className="w-4 h-4 text-purple-600" />
              Popperian Falsification Criteria &amp; Empirical Validation Gate
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.falsification_criteria.map((crit, idx) => (
                <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-xs text-slate-900">{crit.metric_name}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${result.verdict.startsWith("CORROBORATED") ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}`}>
                      {result.verdict.startsWith("CORROBORATED") ? "PASS: SATISFIED" : "FAIL: BREACHED"}
                    </span>
                  </div>
                  <div className="font-mono text-xs text-slate-600 bg-white p-2 rounded border border-slate-200">
                    {crit.mathematical_formula}
                  </div>
                  <div className="text-[11px] text-slate-500 flex justify-between">
                    <span>Target: {crit.target_value}</span>
                    <span>Tolerance: ±{crit.tolerance_threshold}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 4-Agent Collaborative Scientific Feed */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Brain className="w-4 h-4 text-indigo-600" />
                4-Agent Discovery Loop Dialogue &amp; Evidence Ledger
              </h3>
              <span className="text-[11px] font-mono text-slate-500">Autonomous Multi-Agent Consensus</span>
            </div>

            <div className="space-y-4">
              {result.agent_dialogue.map((msg) => {
                let badgeCol = "bg-indigo-100 text-indigo-800 border-indigo-200";
                let icon = <Brain className="w-4 h-4 text-indigo-700" />;
                if (msg.agent_role === "DISCRETIZATION_AGENT") {
                  badgeCol = "bg-sky-100 text-sky-800 border-sky-200";
                  icon = <Layers className="w-4 h-4 text-sky-700" />;
                } else if (msg.agent_role === "ADVERSARIAL_POPPERIAN") {
                  badgeCol = "bg-amber-100 text-amber-800 border-amber-200";
                  icon = <Zap className="w-4 h-4 text-amber-700" />;
                } else if (msg.agent_role === "METROLOGY_AUDITOR") {
                  badgeCol = "bg-emerald-100 text-emerald-800 border-emerald-200";
                  icon = <Scale className="w-4 h-4 text-emerald-700" />;
                }

                return (
                  <div key={msg.step_number} className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {icon}
                        <span className="font-bold text-xs text-slate-900">{msg.message_title}</span>
                        <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${badgeCol}`}>
                          {msg.agent_role}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-500">
                        Confidence: {(msg.epistemic_confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 leading-relaxed">{msg.content}</p>

                    {/* Quantitative parameters */}
                    <div className="bg-white p-2.5 rounded-lg border border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] font-mono text-slate-600">
                      {Object.entries(msg.quantitative_data).map(([k, v]) => (
                        <div key={k}>
                          <span className="text-slate-400 block text-[10px] uppercase">{k.replace(/_/g, " ")}:</span>
                          <span className="font-semibold text-slate-800">{Array.isArray(v) ? v.join(", ") : String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Cryptographic Provenance & Peer-Review Certificate */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-3">
              <Lock className="w-5 h-5 text-purple-600 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-slate-900 block">
                  SHA-256 Merkle Provenance &amp; Scientific Discovery DAG
                </span>
                <span className="text-[11px] font-mono text-slate-500 break-all">
                  {result.merkle_provenance_hash}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="bg-purple-50 text-purple-800 font-mono text-xs px-2.5 py-1 rounded border border-purple-200">
                {result.publication_readiness}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  if (isOpen !== undefined) {
    return (
      <div className="fixed inset-0 z-[9999] bg-slate-950/70 backdrop-blur-md flex items-center justify-center p-2 md:p-6 overflow-y-auto">
        <div className="w-full max-w-7xl max-h-[92vh] overflow-y-auto rounded-2xl bg-slate-50 shadow-2xl border border-slate-200">
          {content}
        </div>
      </div>
    );
  }

  return content;
}
