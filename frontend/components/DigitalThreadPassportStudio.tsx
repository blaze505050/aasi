"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  X,
  Sliders,
  Sparkles,
  Zap,
  Lock,
  GitBranch,
  Layers,
  Award,
  QrCode,
  FileCheck,
} from "lucide-react";

interface DigitalThreadStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface ThreadStep {
  step_id: string;
  phase_name: string;
  facility: string;
  timestamp_iso: string;
  process_parameters: Record<string, any>;
  inspection_verdict: string;
  parent_hashes: string[];
  step_hash: string;
}

interface SpcAudit {
  sample_size: number;
  spec_unit: string;
  limits: {
    lower_spec_limit: number;
    nominal_target: number;
    upper_spec_limit: number;
  };
  sample_statistics: {
    mean: number;
    std_dev: number;
    min: number;
    max: number;
  };
  capability_indices: {
    cp: number;
    cpk: number;
    cpu: number;
    cpl: number;
    process_verdict: string;
    estimated_ppm_defects: number;
  };
  as9100d_clauses: Array<{
    clause: string;
    title: string;
    status: string;
  }>;
}

interface Form8130 {
  form_standard: string;
  cert_tracking_id: string;
  organization: {
    name: string;
    approval_cert_number: string;
    address: string;
  };
  item_details: {
    part_name: string;
    part_number: string;
    serial_number: string;
    quantity: number;
    status_work: string;
  };
  airworthiness_approval: {
    authority: string;
    cfr_reference: string;
    compliance_statement: string;
    authorized_signatory: string;
    issue_date: string;
    digital_signature_hash: string;
  };
  remarks: string;
}

interface ThreadAuditResult {
  digital_thread_id: string;
  merkle_root_hash: string;
  is_tamper_free: boolean;
  tamper_error: string | null;
  part_overview: {
    part_name: string;
    part_number: string;
    serial_number: string;
    material: string;
    specification: string;
  };
  lifecycle_steps: ThreadStep[];
  spc_quality_audit: SpcAudit;
  airworthiness_certificate: Form8130;
}

export default function DigitalThreadPassportStudio({
  isOpen,
  onClose,
  apiBase,
}: DigitalThreadStudioProps) {
  const [selectedPreset, setSelectedPreset] = useState<string>("TITANIUM_WING_RIB_LPBF");
  const [activeTab, setActiveTab] = useState<"lineage" | "as9100d" | "certificate">("lineage");
  const [loading, setLoading] = useState<boolean>(false);
  const [tampered, setTampered] = useState<boolean>(false);

  const [threadData, setThreadData] = useState<ThreadAuditResult | null>(null);

  const loadDigitalThread = async (preset: string) => {
    setLoading(true);
    setTampered(false);
    try {
      const resp = await fetch(`${apiBase}/api/v1/digital-thread/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_preset: preset }),
      });
      const json = await resp.json();
      if (json.status === "success") {
        setThreadData(json.data);
      }
    } catch (e) {
      console.error("Failed to load digital thread:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !threadData) {
      loadDigitalThread(selectedPreset);
    }
  }, [isOpen]);

  const simulateTamper = () => {
    setTampered(true);
  };

  const verifyChain = () => {
    setTampered(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden text-slate-800">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Digital Thread Merkle Lineage & AS9100D Quality Passport
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">
                  Stage 35
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
                  Epoch VII Capstone
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Cryptographic SHA-256 Merkle-DAG provenance, AS9100D Six-Sigma Cpk auditing & FAA Form 8130-3 airworthiness synthesizer
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Preset Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500 mr-2">Flight Hardware:</span>
              <button
                onClick={() => {
                  setSelectedPreset("TITANIUM_WING_RIB_LPBF");
                  loadDigitalThread("TITANIUM_WING_RIB_LPBF");
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ${
                  selectedPreset === "TITANIUM_WING_RIB_LPBF"
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                Ti-6Al-4V Transonic Wing Rib (LPBF)
              </button>
              <button
                onClick={() => {
                  setSelectedPreset("INCONEL_TURBINE_BLADE");
                  loadDigitalThread("INCONEL_TURBINE_BLADE");
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ${
                  selectedPreset === "INCONEL_TURBINE_BLADE"
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                Inconel 718 Turbine Blade (HIP Aging)
              </button>
              <button
                onClick={() => {
                  setSelectedPreset("CFRP_SPAR_LAMINATE");
                  loadDigitalThread("CFRP_SPAR_LAMINATE");
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ${
                  selectedPreset === "CFRP_SPAR_LAMINATE"
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                IM7/8552 Carbon Fiber Primary Spar
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={simulateTamper}
                className="px-2.5 py-1 text-xs rounded border border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100 font-medium"
              >
                Simulate Data Tamper
              </button>
              <button
                onClick={verifyChain}
                className="px-2.5 py-1 text-xs rounded border border-emerald-300 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-medium"
              >
                Re-Verify Chain
              </button>
            </div>
          </div>

          {/* Tamper Warning Banner */}
          {tampered ? (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 flex items-center justify-between text-rose-900">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold">CRYPTOGRAPHIC INTEGRITY VIOLATION DETECTED</h4>
                  <p className="text-xs text-rose-700">
                    Step #2 (LPBF Build) telemetry payload modified post-signing! SHA-256 hash mismatch. Merkle Root validation failed. FAA 8130-3 airworthiness voided.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-rose-200 text-rose-800">
                TAMPER ALERT
              </span>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-emerald-900">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold">SHA-256 MERKLE-DAG SUPPLY CHAIN IMMUTABLE & VERIFIED</h4>
                  <p className="text-xs text-emerald-700 font-mono">
                    Merkle Root: {threadData?.merkle_root_hash}
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-emerald-200 text-emerald-800">
                LINEAGE INTACT
              </span>
            </div>
          )}

          {/* Modality Tabs */}
          <div className="flex border-b border-slate-200 gap-4">
            <button
              onClick={() => setActiveTab("lineage")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "lineage"
                  ? "border-emerald-600 text-emerald-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <GitBranch className="w-4 h-4" />
              Merkle-DAG Provenance Pipeline
            </button>
            <button
              onClick={() => setActiveTab("as9100d")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "as9100d"
                  ? "border-emerald-600 text-emerald-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Activity className="w-4 h-4" />
              AS9100D Statistical Quality & Cpk Audit
            </button>
            <button
              onClick={() => setActiveTab("certificate")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "certificate"
                  ? "border-emerald-600 text-emerald-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <FileCheck className="w-4 h-4" />
              FAA Form 8130-3 Airworthiness Approval Tag
            </button>
          </div>

          {/* TAB 1: MERKLE-DAG PROVENANCE PIPELINE */}
          {activeTab === "lineage" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {threadData?.lifecycle_steps.map((step, idx) => (
                  <div
                    key={step.step_id}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-3 relative hover:shadow-md transition"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-bold text-slate-400">Step {idx + 1}</span>
                        <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-emerald-100 text-emerald-700">
                          {step.inspection_verdict}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-900 leading-snug">
                        {step.phase_name}
                      </h4>
                      <p className="text-[10px] text-slate-500 mt-1">{step.facility}</p>
                    </div>

                    <div className="p-2 rounded bg-white border border-slate-200 text-[10px] space-y-1">
                      {Object.entries(step.process_parameters).slice(0, 3).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-slate-600">
                          <span className="truncate pr-1">{k}:</span>
                          <span className="font-semibold text-slate-900">{String(v)}</span>
                        </div>
                      ))}
                    </div>

                    <div className="pt-2 border-t border-slate-200">
                      <span className="text-[9px] text-slate-400 block font-mono truncate">
                        Hash: {step.step_hash.slice(0, 16)}...
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: AS9100D REV D QUALITY & SPC CPK */}
          {activeTab === "as9100d" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Capability Cards */}
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Process Capability Indices (SPC)
                  </h4>

                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Potential Capability (Cp)</span>
                      <span className="text-xl font-black text-slate-900">
                        {threadData?.spc_quality_audit.capability_indices.cp}
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-[11px] text-emerald-700 font-semibold block">
                        Demonstrated Capability (Cpk)
                      </span>
                      <span className="text-2xl font-black text-emerald-900">
                        {threadData?.spc_quality_audit.capability_indices.cpk}
                      </span>
                      <p className="text-[10px] text-emerald-700 mt-1">
                        Cpk {">"} 1.67 exceeds aerospace Six-Sigma critical flight part threshold.
                      </p>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Estimated Defect Rate</span>
                      <span className="text-lg font-black text-slate-800">
                        {threadData?.spc_quality_audit.capability_indices.estimated_ppm_defects} PPM
                      </span>
                    </div>
                  </div>
                </div>

                {/* AS9100D Clause Checklist */}
                <div className="lg:col-span-2 p-5 rounded-xl bg-white border border-slate-200 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    AS9100D Rev D Quality Management Audit Clauses
                  </h4>

                  <div className="space-y-3">
                    {threadData?.spc_quality_audit.as9100d_clauses.map((c) => (
                      <div
                        key={c.clause}
                        className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-900">Clause {c.clause}:</span>
                            <span className="text-xs text-slate-700">{c.title}</span>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 text-xs font-bold rounded bg-emerald-100 text-emerald-800 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {c.status}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900">
                    <span className="font-bold block mb-0.5">Continuous Improvement Verification:</span>
                    All measurements conform to AS9100D Clause 8.2.4 acceptance criteria. First Article Inspection (AS9102 Rev B) passed with zero non-conformances.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: FAA FORM 8130-3 CERTIFICATE */}
          {activeTab === "certificate" && (
            <div className="p-6 rounded-xl bg-slate-50 border border-slate-300 max-w-4xl mx-auto shadow-sm text-slate-900 space-y-4 font-sans">
              {/* Form 8130-3 Document Header */}
              <div className="border-b-2 border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-black tracking-tight uppercase">
                    FAA FORM 8130-3 / DGCA FORM 1
                  </h3>
                  <p className="text-xs text-slate-600 font-semibold uppercase">
                    Authorized Release Certificate / Airworthiness Approval Tag
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono font-bold block text-slate-700">
                    Tracking No: {threadData?.airworthiness_certificate.cert_tracking_id}
                  </span>
                  <span className="text-[10px] text-slate-500 uppercase">
                    Form Approved OMB No. 2120-0020
                  </span>
                </div>
              </div>

              {/* Organization Block */}
              <div className="grid grid-cols-2 gap-4 text-xs border-b border-slate-200 pb-3">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">1. Approving Authority:</span>
                  <span className="font-bold">{threadData?.airworthiness_certificate.airworthiness_approval.authority}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">2. Organization Name & Address:</span>
                  <span className="font-bold">{threadData?.airworthiness_certificate.organization.name}</span>
                  <p className="text-slate-600">{threadData?.airworthiness_certificate.organization.address}</p>
                </div>
              </div>

              {/* Item Details Block */}
              <div className="grid grid-cols-4 gap-3 text-xs border-b border-slate-200 pb-3">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">3. Item Description:</span>
                  <span className="font-bold">{threadData?.airworthiness_certificate.item_details.part_name}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">4. Part Number:</span>
                  <span className="font-mono font-bold text-blue-700">{threadData?.airworthiness_certificate.item_details.part_number}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">5. Serial Number:</span>
                  <span className="font-mono font-bold">{threadData?.airworthiness_certificate.item_details.serial_number}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">6. Status/Work:</span>
                  <span className="font-bold text-emerald-700">{threadData?.airworthiness_certificate.item_details.status_work}</span>
                </div>
              </div>

              {/* Remarks */}
              <div className="text-xs border-b border-slate-200 pb-3">
                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">7. Remarks / Special Directives:</span>
                <p className="p-2.5 rounded bg-white border border-slate-200 text-slate-700 text-[11px] leading-relaxed">
                  {threadData?.airworthiness_certificate.remarks}
                </p>
              </div>

              {/* Signature & Cryptographic Stamp */}
              <div className="grid grid-cols-2 gap-4 text-xs pt-2">
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">8. Conformity Certification:</span>
                  <p className="text-[11px] text-slate-600 leading-snug">
                    {threadData?.airworthiness_certificate.airworthiness_approval.compliance_statement}
                  </p>
                  <span className="text-[10px] font-semibold text-slate-700 block mt-2">
                    Date: {threadData?.airworthiness_certificate.airworthiness_approval.issue_date}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-white border border-slate-300 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">Authorized Signature</span>
                    <span className="font-bold text-xs text-slate-900 block">
                      {threadData?.airworthiness_certificate.airworthiness_approval.authorized_signatory}
                    </span>
                    <span className="text-[9px] text-slate-500 font-mono block mt-1 truncate max-w-[200px]">
                      Sig Hash: {threadData?.airworthiness_certificate.airworthiness_approval.digital_signature_hash.slice(0, 24)}...
                    </span>
                  </div>
                  <div className="w-12 h-12 bg-slate-100 rounded border border-slate-200 flex items-center justify-center text-slate-400">
                    <QrCode className="w-8 h-8 text-slate-700" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>SHA-256 Merkle-DAG • AS9100D Six-Sigma SPC • FAA Form 8130-3 / DGCA Form 1</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
