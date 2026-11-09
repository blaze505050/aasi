"use client";

import React, { useState, useEffect } from "react";
import {
  Flame,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Activity,
  DollarSign,
  TrendingDown,
  RefreshCw,
  X,
  CheckCircle2,
  Clock,
  Layers,
  Wrench,
  Copy,
  Sliders,
  Plane,
} from "lucide-react";

interface TurbofanFleetRulStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface DiagnosisResult {
  engine_model: string;
  designation: string;
  engine_serial_number: string;
  flight_cycles_completed: number;
  egt_margin_celsius: number;
  egt_degradation_pct: number;
  hpc_efficiency_loss_pct: number;
  hpt_efficiency_loss_pct: number;
  disk_crack_length_mm: number;
  critical_crack_length_mm: number;
  crack_growth_rate_mm_per_cycle: number;
  stress_intensity_range_mpa_sqrt_m: number;
  weibull_reliability_rt: number;
  hazard_rate_per_cycle: number;
  rul_cycles_remaining: number;
  maintenance_status: string;
  maintenance_action_recommended: string;
  avoided_aog_savings_usd: number;
  cryptographic_diagnosis_digest: string;
  timestamp: string;
}

interface FleetOverview {
  fleet_id: string;
  total_engines_monitored: number;
  engines_in_nominal_service: number;
  engines_requiring_inspection: number;
  fleet_mean_rul_cycles: number;
  total_avoided_aog_savings_usd: number;
  engines: DiagnosisResult[];
}

export default function TurbofanFleetRulStudio({
  isOpen,
  onClose,
  apiBase,
}: TurbofanFleetRulStudioProps) {
  const [engineModel, setEngineModel] = useState("CFM_LEAP_1A");
  const [flightCycles, setFlightCycles] = useState(6800);
  const [serialNumber, setSerialNumber] = useState("ESN-LEAP-98421");
  const [activeTab, setActiveTab] = useState<"diagnostics" | "lcf" | "fleet">("diagnostics");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [fleetData, setFleetData] = useState<FleetOverview | null>(null);

  const fetchDiagnosisAndFleet = async () => {
    setLoading(true);
    try {
      // 1. Single engine diagnosis
      const resDiag = await fetch(`${apiBase}/api/v1/fleet-rul/diagnose-engine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          engine_model_key: engineModel,
          flight_cycles: flightCycles,
          serial_number: serialNumber,
        }),
      });
      const dDiag = await resDiag.json();
      if (dDiag.status === "success") {
        setDiagnosis(dDiag.data);
      }

      // 2. Fleet overview
      const resFleet = await fetch(`${apiBase}/api/v1/fleet-rul/fleet-overview`);
      const dFleet = await resFleet.json();
      if (dFleet.status === "success") {
        setFleetData(dFleet.data);
      }
    } catch (err) {
      console.error("Turbofan RUL error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDiagnosisAndFleet();
    }
  }, [isOpen, engineModel, flightCycles]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-600">
              <Flame size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  Turbofan Fleet Predictive Maintenance & RUL Digital Twin
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-600 text-white">
                  STAGE 40 CAPSTONE
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  EPOCH VIII FINAL
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                NASA C-MAPSS EGT margin erosion, Paris-Erdogan HPT disk crack growth, and Weibull hazard survival
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

        {/* Engine Model Controls Strip */}
        <div className="px-6 py-3 bg-slate-100/70 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-600">Turbofan Powerplant:</span>
            <button
              onClick={() => {
                setEngineModel("CFM_LEAP_1A");
                setSerialNumber("ESN-LEAP-98421");
              }}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                engineModel === "CFM_LEAP_1A"
                  ? "bg-amber-600 text-white border-amber-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              CFM LEAP-1A26 (Narrowbody)
            </button>
            <button
              onClick={() => {
                setEngineModel("GE90_115B");
                setSerialNumber("ESN-GE90-70110");
              }}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                engineModel === "GE90_115B"
                  ? "bg-amber-600 text-white border-amber-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              GE90-115B (Widebody 512 kN)
            </button>
            <button
              onClick={() => {
                setEngineModel("KAVERI_GTX_35VS");
                setSerialNumber("ESN-KAV-3501");
              }}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                engineModel === "KAVERI_GTX_35VS"
                  ? "bg-amber-600 text-white border-amber-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              GTX-35VS Kaveri (Defense)
            </button>
          </div>

          <button
            onClick={fetchDiagnosisAndFleet}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold flex items-center gap-1.5 transition-colors text-xs shadow-sm"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Recompute Engine Health
          </button>
        </div>

        {/* Flight Cycle Slider Strip */}
        <div className="px-6 py-4 bg-white border-b border-slate-200 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-800">Flight Cycles Completed:</span>
              <span className="text-base font-black text-amber-600">{flightCycles.toLocaleString()} cycles</span>
              <span className="text-slate-400 font-mono">({serialNumber})</span>
            </div>

            {diagnosis && (
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  diagnosis.maintenance_status === "NOMINAL_FLIGHT_SERVICE"
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : diagnosis.maintenance_status === "SCHEDULE_A_CHECK"
                    ? "bg-blue-50 text-blue-700 border border-blue-200"
                    : diagnosis.maintenance_status === "EXPEDITE_C_CHECK"
                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                    : "bg-rose-50 text-rose-700 border border-rose-200"
                }`}
              >
                {diagnosis.maintenance_status === "NOMINAL_FLIGHT_SERVICE" ? (
                  <CheckCircle2 size={13} />
                ) : (
                  <AlertTriangle size={13} />
                )}
                {diagnosis.maintenance_status}
              </span>
            )}
          </div>

          <input
            type="range"
            min="0"
            max="14000"
            step="200"
            value={flightCycles}
            onChange={(e) => setFlightCycles(Number(e.target.value))}
            className="w-full accent-amber-600 h-2 bg-slate-200 rounded-lg cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>0 Cycles (Factory Fresh)</span>
            <span>6,000 Cycles (Mid-Life Line Check)</span>
            <span className="text-rose-600 font-bold">14,000 Cycles (Overhaul / Shop Visit)</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-slate-200 flex gap-6 text-sm font-semibold text-slate-500 bg-slate-50/50">
          <button
            onClick={() => setActiveTab("diagnostics")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "diagnostics"
                ? "border-amber-600 text-amber-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Activity size={16} />
            EGT Margin & RUL Diagnostics
          </button>
          <button
            onClick={() => setActiveTab("lcf")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "lcf"
                ? "border-amber-600 text-amber-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Wrench size={16} />
            Paris-Erdogan LCF Crack Growth
          </button>
          <button
            onClick={() => setActiveTab("fleet")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "fleet"
                ? "border-amber-600 text-amber-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Plane size={16} />
            Airline Commercial Fleet Deck ({fleetData?.total_engines_monitored || 12} Engines)
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/40 space-y-6">
          {diagnosis && (
            <>
              {/* TAB 1: EGT MARGIN & RUL DIAGNOSTICS */}
              {activeTab === "diagnostics" && (
                <div className="space-y-6">
                  {/* KPI Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Remaining Useful Life (RUL)
                      </div>
                      <div className="text-2xl font-black text-amber-600 mt-1">
                        {diagnosis.rul_cycles_remaining.toLocaleString()}{" "}
                        <span className="text-sm font-medium text-slate-500">cycles</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Weibull Reliability R(t) = {(diagnosis.weibull_reliability_rt * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        EGT Margin Remaining
                      </div>
                      <div className="text-2xl font-black text-slate-800 mt-1">
                        {diagnosis.egt_margin_celsius.toFixed(1)}°C
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Erosion: -{diagnosis.egt_degradation_pct.toFixed(1)}% from factory
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        HPT Disk Crack Length
                      </div>
                      <div className="text-2xl font-black text-indigo-600 mt-1">
                        {diagnosis.disk_crack_length_mm.toFixed(2)}{" "}
                        <span className="text-sm font-medium text-slate-500">
                          / {diagnosis.critical_crack_length_mm} mm
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        ΔK = {diagnosis.stress_intensity_range_mpa_sqrt_m.toFixed(1)} MPa√m
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Avoided AOG Downtime Cost
                      </div>
                      <div className="text-2xl font-black text-emerald-600 mt-1">
                        ${diagnosis.avoided_aog_savings_usd.toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Prevented unscheduled shop visit
                      </div>
                    </div>
                  </div>

                  {/* Recommendation Action Card */}
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Wrench size={16} className="text-amber-600" />
                      Prescriptive Maintenance Advisory
                    </h3>
                    <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-mono">
                      {diagnosis.maintenance_action_recommended}
                    </div>
                    <div className="flex justify-between items-center text-[11px] text-slate-400 font-mono">
                      <span>SHA-256 Diagnosis Seal: {diagnosis.cryptographic_diagnosis_digest}</span>
                      <span>Recorded: {diagnosis.timestamp}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: PARIS-ERDOGAN LCF CRACK GROWTH */}
              {activeTab === "lcf" && (
                <div className="space-y-6">
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Sliders size={16} className="text-amber-600" />
                      Paris-Erdogan Low-Cycle Fatigue (LCF) Mechanics
                    </h3>

                    <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 font-mono text-xs text-slate-700 space-y-2">
                      <div>Equation: da/dN = C · (ΔK)^m = C · (Y · Δσ · √(π·a))^m</div>
                      <div>Material: Inconel 718 / CMSX-4 Single-Crystal Superalloy</div>
                      <div>Initial Flaw Size: a_0 = 0.50 mm → Current: a = {diagnosis.disk_crack_length_mm.toFixed(3)} mm</div>
                      <div>Critical Threshold (K_Ic = 95 MPa√m): a_c = {diagnosis.critical_crack_length_mm.toFixed(1)} mm</div>
                      <div>Crack Growth Velocity: da/dN = {diagnosis.crack_growth_rate_mm_per_cycle} mm/cycle</div>
                      <div>Compressor Efficiency Loss: -{diagnosis.hpc_efficiency_loss_pct}% | Turbine Loss: -{diagnosis.hpt_efficiency_loss_pct}%</div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: AIRLINE FLEET OVERVIEW DECK */}
              {activeTab === "fleet" && fleetData && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center text-xs font-semibold text-slate-700">
                    <div>
                      Fleet Mean RUL:{" "}
                      <span className="font-bold text-amber-600">
                        {fleetData.fleet_mean_rul_cycles.toLocaleString()} cycles
                      </span>{" "}
                      • {fleetData.engines_in_nominal_service} in Green Service •{" "}
                      {fleetData.engines_requiring_inspection} Flagged
                    </div>
                    <div className="text-emerald-700 font-bold">
                      Total Avoided AOG Savings: ${fleetData.total_avoided_aog_savings_usd.toLocaleString()}
                    </div>
                  </div>

                  <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                        <tr>
                          <th className="px-4 py-3">Engine Serial</th>
                          <th className="px-4 py-3">Model</th>
                          <th className="px-4 py-3">Cycles</th>
                          <th className="px-4 py-3">EGT Margin</th>
                          <th className="px-4 py-3">Crack Length</th>
                          <th className="px-4 py-3">RUL Cycles</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Savings</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-normal">
                        {fleetData.engines.map((eng) => (
                          <tr key={eng.engine_serial_number} className="hover:bg-slate-50/80">
                            <td className="px-4 py-3 font-mono font-bold text-slate-900">
                              {eng.engine_serial_number}
                            </td>
                            <td className="px-4 py-3 text-slate-600 font-medium">
                              {eng.engine_model}
                            </td>
                            <td className="px-4 py-3 text-slate-700 font-mono">
                              {eng.flight_cycles_completed.toLocaleString()}
                            </td>
                            <td className="px-4 py-3 font-mono font-semibold text-slate-800">
                              {eng.egt_margin_celsius.toFixed(1)}°C
                            </td>
                            <td className="px-4 py-3 font-mono text-slate-700">
                              {eng.disk_crack_length_mm.toFixed(2)} mm
                            </td>
                            <td className="px-4 py-3 font-mono font-bold text-amber-600">
                              {eng.rul_cycles_remaining.toLocaleString()}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  eng.maintenance_status === "NOMINAL_FLIGHT_SERVICE"
                                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                    : eng.maintenance_status === "SCHEDULE_A_CHECK"
                                    ? "bg-blue-50 text-blue-700 border border-blue-200"
                                    : eng.maintenance_status === "EXPEDITE_C_CHECK"
                                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                                    : "bg-rose-50 text-rose-700 border border-rose-200"
                                }`}
                              >
                                {eng.maintenance_status.split("_")[0]}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-mono font-bold text-emerald-600">
                              ${eng.avoided_aog_savings_usd.toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
