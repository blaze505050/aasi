"use client";

import React, { useState, useEffect } from "react";
import {
  Cpu,
  Layers,
  Zap,
  ShieldCheck,
  ShieldAlert,
  CreditCard,
  Lock,
  FileCheck2,
  RefreshCw,
  X,
  CheckCircle2,
  Clock,
  ArrowRight,
  Database,
  Building,
  Key,
} from "lucide-react";

interface SovereignGatewayStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface TenantData {
  tenant_id: string;
  tenant_name: string;
  tier: string;
  token_capacity: number;
  token_refill_rate_per_sec: number;
  current_tokens: number;
  total_consumed_tokens: number;
  total_spend_usd: number;
  compute_hours_allocated: number;
  compute_hours_used: number;
  itar_clearance_active: boolean;
}

interface ConsumptionRecord {
  transaction_id: string;
  tenant_id: string;
  task_type: string;
  tokens_deducted: number;
  cost_usd: number;
  remaining_tokens: number;
  timestamp: string;
  cryptographic_receipt_sha256: string;
}

interface ExportClearanceResult {
  clearance_status: string;
  clearance_ticket_id?: string;
  tenant_id: string;
  tenant_name?: string;
  asset_name: string;
  export_classification?: string;
  air_gapped_vault_seal?: string;
  cryptographic_hash_sha256?: string;
  reason?: string;
  compliance_standards?: string[];
  issued_timestamp: string;
}

export default function SovereignGatewayStudio({
  isOpen,
  onClose,
  apiBase,
}: SovereignGatewayStudioProps) {
  const [tenants, setTenants] = useState<TenantData[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState("TENANT-DEFENSE-DRDO");
  const [selectedTask, setSelectedTask] = useState("SCIML_FNO_INFERENCE");
  const [selectedRole, setSelectedRole] = useState("AERODYNAMICS_SPECIALIST");
  const [loading, setLoading] = useState(false);
  const [consuming, setConsuming] = useState(false);
  const [clearingExport, setClearingExport] = useState(false);
  const [history, setHistory] = useState<ConsumptionRecord[]>([]);

  // Export Clearance Form
  const [exportAsset, setExportAsset] = useState("Hypersonic_Scramjet_Aero_Polar_Deck_v4.h5");
  const [exportClassification, setExportClassification] = useState("DEFENSE_ITAR_RESTRICTED");
  const [clearanceResult, setClearanceResult] = useState<ExportClearanceResult | null>(null);

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/sovereign-gateway/tenants`);
      const data = await res.json();
      if (data.status === "success") {
        setTenants(data.data.tenants);
      }
    } catch (err) {
      console.error("Fetch tenants error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTenants();
    }
  }, [isOpen]);

  const activeTenant = tenants.find((t) => t.tenant_id === selectedTenantId) || tenants[0];

  const handleConsume = async () => {
    if (!activeTenant) return;
    setConsuming(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/sovereign-gateway/consume-tokens`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: activeTenant.tenant_id,
          task_type_key: selectedTask,
          user_role_key: selectedRole,
        }),
      });
      const data = await res.json();
      if (data.status === "success" && data.data.authorized) {
        const item: ConsumptionRecord = {
          transaction_id: data.data.transaction_id,
          tenant_id: data.data.tenant_id,
          task_type: data.data.task_type,
          tokens_deducted: data.data.tokens_deducted,
          cost_usd: data.data.cost_usd,
          remaining_tokens: data.data.remaining_tokens,
          timestamp: data.data.timestamp,
          cryptographic_receipt_sha256: data.data.cryptographic_receipt_sha256,
        };
        setHistory((prev) => [item, ...prev].slice(0, 15));
        fetchTenants();
      } else if (data.data?.status === "RATE_LIMIT_EXCEEDED") {
        alert(`Rate Limit Exceeded! Refill required. Wait ~${data.data.wait_seconds_to_refill}s.`);
      }
    } catch (err) {
      console.error("Consume error:", err);
    } finally {
      setConsuming(false);
    }
  };

  const handleExportClearance = async () => {
    if (!activeTenant) return;
    setClearingExport(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/sovereign-gateway/export-clearance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: activeTenant.tenant_id,
          asset_name: exportAsset,
          classification: exportClassification,
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setClearanceResult(data.data);
      }
    } catch (err) {
      console.error("Export clearance error:", err);
    } finally {
      setClearingExport(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-sky-50 border border-sky-200 text-sky-600">
              <Zap size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  Enterprise Sovereign Cloud SaaS Gateway & Token Metering
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-600 text-white">
                  STAGE 38
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  NIST SP 800-53
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Token-bucket rate limiting, micro-invoicing consumption ledger, and air-gapped ITAR/EAR export clearance vault
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-slate-200 text-slate-500 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tenant Selection Strip */}
        <div className="px-6 py-3 bg-slate-100/70 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-600">Active Tenant Organization:</span>
            {tenants.map((t) => (
              <button
                key={t.tenant_id}
                onClick={() => setSelectedTenantId(t.tenant_id)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                  selectedTenantId === t.tenant_id
                    ? "bg-sky-600 text-white border-sky-600 shadow-sm"
                    : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                }`}
              >
                {t.tenant_name.split(" ")[0]} ({t.tier})
              </button>
            ))}
          </div>

          <button
            onClick={fetchTenants}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium flex items-center gap-1.5 transition-colors text-xs"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Sync Balance
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/40 space-y-6">
          {activeTenant ? (
            <>
              {/* Tenant KPI Overview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Token Bucket Balance
                  </div>
                  <div className="text-2xl font-black text-sky-600 mt-1">
                    {Math.round(activeTenant.current_tokens).toLocaleString()}{" "}
                    <span className="text-xs font-normal text-slate-400">
                      / {activeTenant.token_capacity.toLocaleString()}
                    </span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mt-2">
                    <div
                      className="h-full bg-sky-500 rounded-full"
                      style={{
                        width: `${Math.min(100, (activeTenant.current_tokens / activeTenant.token_capacity) * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Refill: +{activeTenant.token_refill_rate_per_sec} tokens/sec continuous
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Cumulative Invoiced
                  </div>
                  <div className="text-2xl font-black text-slate-800 mt-1">
                    ${activeTenant.total_spend_usd.toFixed(2)}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {activeTenant.total_consumed_tokens.toLocaleString()} tokens billed
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Compute Hours Used
                  </div>
                  <div className="text-2xl font-black text-indigo-600 mt-1">
                    {activeTenant.compute_hours_used.toFixed(1)}{" "}
                    <span className="text-xs font-medium text-slate-400">
                      / {activeTenant.compute_hours_allocated}h
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Dedicated Sovereign Isolation
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    ITAR / EAR Status
                  </div>
                  <div className="mt-1 flex items-center gap-1.5">
                    {activeTenant.itar_clearance_active ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <ShieldCheck size={14} /> ACTIVE DEFENSE CLEARANCE
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                        <Lock size={14} /> COMMERCIAL / UNRESTRICTED ONLY
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    22 CFR § 120-130 Dual-Use Enclave
                  </div>
                </div>
              </div>

              {/* Action Bar: Compute Simulation & Metering */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Cpu size={16} className="text-sky-600" />
                  Sovereign Compute Task Metering Simulator
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div>
                    <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Target Aerospace Task
                    </label>
                    <select
                      value={selectedTask}
                      onChange={(e) => setSelectedTask(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white font-medium text-slate-700"
                    >
                      <option value="SCIML_FNO_INFERENCE">SciML FNO Inference (2 tokens / $0.09)</option>
                      <option value="CFD_PANEL_SOLVER_PASS">CFD Panel Solver (10 tokens / $0.45)</option>
                      <option value="MDO_TOPOLOGY_OPTIMIZATION">MDO Topology Optimization (50 tokens / $2.25)</option>
                      <option value="AIRWORTHINESS_DOSSIER_SYNTHESIS">Airworthiness Dossier (25 tokens / $1.13)</option>
                      <option value="ORBITAL_PROPAGATION_RUN">Orbital Propagation Run (5 tokens / $0.23)</option>
                      <option value="NDT_CT_INSPECTION_SCAN">Micro-CT NDT Scan Pass (15 tokens / $0.68)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Authorized User Role (RBAC)
                    </label>
                    <select
                      value={selectedRole}
                      onChange={(e) => setSelectedRole(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white font-medium text-slate-700"
                    >
                      <option value="DEFENSE_CHIEF_ENGINEER">Defense Chief Engineer (Full Access)</option>
                      <option value="CERTIFICATION_AUDITOR">Certification Auditor (Inspection Only)</option>
                      <option value="AERODYNAMICS_SPECIALIST">Aerodynamics Specialist (Compute Access)</option>
                      <option value="SOVEREIGN_ADMIN">Sovereign Administrator (Root Quota)</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleConsume}
                      disabled={consuming}
                      className="w-full py-2 px-4 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 shadow-sm"
                    >
                      <Zap size={14} className={consuming ? "animate-spin" : ""} />
                      {consuming ? "Metering Task..." : "Authorize & Deduct Tokens"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Micro-Invoicing Consumption Ledger Table */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-800">
                    Live Sovereign Micro-Invoicing Ledger
                  </span>
                  <span className="text-slate-500 font-mono text-[11px]">
                    NIST SP 800-53 Cryptographic Audit Trail
                  </span>
                </div>

                <div className="overflow-x-auto max-h-60">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-400 uppercase font-semibold text-[10px] sticky top-0">
                      <tr>
                        <th className="px-4 py-2.5">TX ID</th>
                        <th className="px-4 py-2.5">Task Description</th>
                        <th className="px-4 py-2.5">Tokens Deducted</th>
                        <th className="px-4 py-2.5">Micro-Cost</th>
                        <th className="px-4 py-2.5">Remaining</th>
                        <th className="px-4 py-2.5">Cryptographic Receipt</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-normal">
                      {history.length > 0 ? (
                        history.map((rec) => (
                          <tr key={rec.transaction_id} className="hover:bg-slate-50/80">
                            <td className="px-4 py-2.5 font-mono font-semibold text-slate-800">
                              {rec.transaction_id}
                            </td>
                            <td className="px-4 py-2.5 text-slate-700 font-medium">
                              {rec.task_type}
                            </td>
                            <td className="px-4 py-2.5 font-bold text-sky-600">
                              -{rec.tokens_deducted} tok
                            </td>
                            <td className="px-4 py-2.5 text-emerald-600 font-semibold font-mono">
                              ${rec.cost_usd.toFixed(4)}
                            </td>
                            <td className="px-4 py-2.5 text-slate-500 font-mono">
                              {rec.remaining_tokens.toFixed(1)}
                            </td>
                            <td className="px-4 py-2.5 font-mono text-[10px] text-slate-400">
                              {rec.cryptographic_receipt_sha256.substring(0, 16)}...
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={6} className="px-4 py-6 text-center text-slate-400 text-xs italic">
                            No compute tasks executed in this session. Click "Authorize & Deduct Tokens" to test token bucket metering.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Air-Gapped Export Clearance Vault */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Lock size={16} className="text-amber-600" />
                  Air-Gapped ITAR/EAR Export Clearance Vault
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div>
                    <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Artifact Designation
                    </label>
                    <input
                      type="text"
                      value={exportAsset}
                      onChange={(e) => setExportAsset(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 font-medium text-slate-700"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                      Classification Regime
                    </label>
                    <select
                      value={exportClassification}
                      onChange={(e) => setExportClassification(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white font-medium text-slate-700"
                    >
                      <option value="DEFENSE_ITAR_RESTRICTED">DEFENSE ITAR RESTRICTED (22 CFR § 121)</option>
                      <option value="COMMERCIAL_UNRESTRICTED">COMMERCIAL UNRESTRICTED (EAR99)</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleExportClearance}
                      disabled={clearingExport}
                      className="w-full py-2 px-4 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 shadow-sm"
                    >
                      <FileCheck2 size={14} className={clearingExport ? "animate-spin" : ""} />
                      {clearingExport ? "Validating ITAR..." : "Generate Export Clearance Ticket"}
                    </button>
                  </div>
                </div>

                {clearanceResult && (
                  <div
                    className={`p-4 rounded-lg border text-xs space-y-2 ${
                      clearanceResult.clearance_status === "EXPORT_APPROVED"
                        ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                        : "bg-rose-50 border-rose-200 text-rose-900"
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold">
                      <span className="flex items-center gap-1.5">
                        {clearanceResult.clearance_status === "EXPORT_APPROVED" ? (
                          <CheckCircle2 size={16} className="text-emerald-600" />
                        ) : (
                          <ShieldAlert size={16} className="text-rose-600" />
                        )}
                        STATUS: {clearanceResult.clearance_status}
                      </span>
                      {clearanceResult.clearance_ticket_id && (
                        <span className="font-mono text-emerald-800">
                          {clearanceResult.clearance_ticket_id}
                        </span>
                      )}
                    </div>

                    {clearanceResult.clearance_status === "EXPORT_APPROVED" ? (
                      <div className="font-mono text-[11px] space-y-1 text-emerald-800">
                        <div>Air-Gapped Vault Seal: {clearanceResult.air_gapped_vault_seal}</div>
                        <div>SHA-256 Digest: {clearanceResult.cryptographic_hash_sha256}</div>
                        <div className="text-[10px] text-emerald-600">
                          Standards: {clearanceResult.compliance_standards?.join(" • ")}
                        </div>
                      </div>
                    ) : (
                      <div className="text-rose-700">
                        Reason: {clearanceResult.reason}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400 gap-2">
              <RefreshCw size={24} className="animate-spin text-sky-600" />
              <span>Loading Sovereign Enterprise Tenants...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
