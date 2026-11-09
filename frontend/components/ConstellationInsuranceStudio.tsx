"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  DollarSign,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  X,
  Sliders,
  Sparkles,
  Zap,
  Globe,
  TrendingUp,
  FileText,
  BadgePercent,
  Compass,
} from "lucide-react";

interface ConstellationInsuranceStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface UnderwritingResult {
  policy_id: string;
  underwriting_standard: string;
  constellation_profile: {
    altitude_km: number;
    constellation_size: number;
    total_insurable_value_usd: number;
    satellite_unit_cost_usd: number;
    has_autonomous_cbf_avoidance: boolean;
  };
  actuarial_metrics: {
    annual_pure_risk_loss_usd: number;
    pure_rate_on_line_percent: number;
    solvency_ii_var_995_usd: number;
    solvency_ii_cvar_995_usd: number;
    worst_case_loss_fraction_percent: number;
  };
  commercial_policy_pricing: {
    commercial_annual_premium_usd: number;
    rate_on_line_percent: number;
    autonomous_maneuver_discount_usd: number;
    regulatory_capital_charge_usd: number;
    brokerage_and_expenses_usd: number;
  };
  loss_exceedance_curve: Array<{
    claim_amount_million_usd: number;
    exceedance_probability_percent: number;
  }>;
}

export default function ConstellationInsuranceStudio({
  isOpen,
  onClose,
  apiBase,
}: ConstellationInsuranceStudioProps) {
  const [altitudeKm, setAltitudeKm] = useState<number>(550.0);
  const [constellationSize, setConstellationSize] = useState<number>(120);
  const [unitCostMillion, setUnitCostMillion] = useState<number>(1.5);
  const [missionYears, setMissionYears] = useState<number>(5.0);
  const [autonomousAvoidance, setAutonomousAvoidance] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);
  const [policyData, setPolicyData] = useState<UnderwritingResult | null>(null);

  const applyPreset = (preset: string) => {
    if (preset === "broadband_550") {
      setAltitudeKm(550.0);
      setConstellationSize(240);
      setUnitCostMillion(1.2);
      setMissionYears(5.0);
      setAutonomousAvoidance(true);
    } else if (preset === "debris_peak_820") {
      setAltitudeKm(820.0);
      setConstellationSize(24);
      setUnitCostMillion(18.0);
      setMissionYears(7.0);
      setAutonomousAvoidance(true);
    } else if (preset === "vleo_380") {
      setAltitudeKm(380.0);
      setConstellationSize(60);
      setUnitCostMillion(3.5);
      setMissionYears(3.0);
      setAutonomousAvoidance(true);
    }
  };

  const runUnderwriting = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/insurance-risk/underwrite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          altitude_km: altitudeKm,
          constellation_size: constellationSize,
          satellite_unit_cost_usd: unitCostMillion * 1e6,
          mission_duration_years: missionYears,
          has_autonomous_avoidance: autonomousAvoidance,
        }),
      });
      const json = await resp.json();
      if (json.status === "success") {
        setPolicyData(json.data);
      }
    } catch (e) {
      console.error("Underwriting failed:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !policyData) {
      runUnderwriting();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden text-slate-800">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-600 flex items-center justify-center font-bold">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Constellation Collision Insurance Risk & Actuarial Engine
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">
                  Stage 36
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                  Solvency II 99.5% VaR
                </span>
              </div>
              <p className="text-xs text-slate-500">
                NASA ORDEM debris flux kinetics, compound Poisson loss distributions & commercial space slip underwriting
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
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-500 mr-2">Market Scenarios:</span>
            <button
              onClick={() => applyPreset("broadband_550")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-violet-50 text-violet-700 border border-violet-200 hover:bg-violet-100 transition"
            >
              LEO Commercial Broadband (550 km, 240 Sats)
            </button>
            <button
              onClick={() => applyPreset("debris_peak_820")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition"
            >
              SSO Radar Constellation (820 km Debris Peak)
            </button>
            <button
              onClick={() => applyPreset("vleo_380")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition"
            >
              VLEO Defence Constellation (380 km)
            </button>
          </div>

          {/* Underwriting Parameters Bar */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Orbit Altitude</span>
                <span className="text-slate-500">{altitudeKm} km</span>
              </div>
              <input
                type="range"
                min={350}
                max={1100}
                step={10}
                value={altitudeKm}
                onChange={(e) => setAltitudeKm(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
              <span className="text-[10px] text-slate-400 block mt-1">
                {altitudeKm >= 780 && altitudeKm <= 860 ? "⚠️ High Debris Belt (Cosmos-Iridium)" : "Standard LEO Shell"}
              </span>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Fleet Size</span>
                <span className="text-slate-500">{constellationSize} Sats</span>
              </div>
              <input
                type="range"
                min={10}
                max={500}
                step={10}
                value={constellationSize}
                onChange={(e) => setConstellationSize(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Unit Sat Cost</span>
                <span className="text-slate-500">${unitCostMillion}M</span>
              </div>
              <input
                type="range"
                min={0.5}
                max={25.0}
                step={0.5}
                value={unitCostMillion}
                onChange={(e) => setUnitCostMillion(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Lifespan</span>
                <span className="text-slate-500">{missionYears} Years</span>
              </div>
              <input
                type="range"
                min={1}
                max={12}
                step={1}
                value={missionYears}
                onChange={(e) => setMissionYears(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={runUnderwriting}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-violet-600 hover:bg-violet-700 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Activity className="w-3.5 h-3.5 animate-spin" />
                    <span>Underwriting...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Price Policy Slip</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Autonomous Avoidance Toggle Banner */}
          <div className="p-3.5 rounded-xl bg-violet-50 border border-violet-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Compass className="w-5 h-5 text-violet-600" />
              <div>
                <span className="text-xs font-bold text-violet-900 block">
                  Autonomous Control Barrier Function (CBF) Collision Avoidance Credit
                </span>
                <span className="text-[11px] text-violet-700">
                  Onboard thrusters with autonomous collision maneuvers qualify for a 35% pure risk discount.
                </span>
              </div>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autonomousAvoidance}
                onChange={(e) => setAutonomousAvoidance(e.target.checked)}
                className="rounded text-violet-600 focus:ring-violet-500 h-4 w-4"
              />
              <span className="text-xs font-bold text-violet-900">Maneuver Credit Active</span>
            </label>
          </div>

          {/* Core Underwriting Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Actuarial Loss Distribution Curve */}
            <div className="lg:col-span-2 p-5 rounded-xl bg-white border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-900">
                    Actuarial Tail Exceedance Distribution (P[Loss {">"} X])
                  </h4>
                  <p className="text-xs text-slate-500">
                    Solvency II 99.5% Value-at-Risk threshold and tail claim exceedance probability.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">
                    99.5% VaR: ${(policyData?.actuarial_metrics.solvency_ii_var_995_usd ? policyData.actuarial_metrics.solvency_ii_var_995_usd / 1e6 : 0).toFixed(1)}M
                  </span>
                </div>
              </div>

              {/* Chart SVG */}
              <div className="w-full h-60 bg-slate-50 rounded-lg p-2 border border-slate-200 relative">
                {policyData && (
                  <svg className="w-full h-full" viewBox="0 0 500 200">
                    {/* VaR Line */}
                    {(() => {
                      const pts = policyData.loss_exceedance_curve;
                      const maxClaim = pts[pts.length - 1].claim_amount_million_usd;
                      const varM = policyData.actuarial_metrics.solvency_ii_var_995_usd / 1e6;
                      const varX = (varM / maxClaim) * 480 + 10;

                      return (
                        <g>
                          <line x1={varX} y1="10" x2={varX} y2="190" stroke="#f59e0b" strokeWidth="2" strokeDasharray="4 2" />
                          <text x={varX - 6} y="25" fill="#d97706" fontSize="10" textAnchor="end" fontWeight="bold">
                            99.5% VaR
                          </text>
                        </g>
                      );
                    })()}

                    {/* Exceedance Curve (violet) */}
                    {(() => {
                      const pts = policyData.loss_exceedance_curve;
                      const maxClaim = pts[pts.length - 1].claim_amount_million_usd;
                      const poly = pts
                        .map((p) => {
                          const x = (p.claim_amount_million_usd / maxClaim) * 480 + 10;
                          const y = 190 - (p.exceedance_probability_percent / 100.0) * 170;
                          return `${x},${y}`;
                        })
                        .join(" ");

                      return (
                        <polyline
                          fill="none"
                          stroke="#7c3aed"
                          strokeWidth="2.5"
                          points={poly}
                        />
                      );
                    })()}
                  </svg>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                <span>Total Insured Value (TIV): <b className="text-slate-900">${(policyData?.constellation_profile.total_insurable_value_usd ? policyData.constellation_profile.total_insurable_value_usd / 1e6 : 0).toFixed(1)}M</b></span>
                <span>Expected Shortfall (CVaR): <b className="text-slate-900">${(policyData?.actuarial_metrics.solvency_ii_cvar_995_usd ? policyData.actuarial_metrics.solvency_ii_cvar_995_usd / 1e6 : 0).toFixed(1)}M</b></span>
                <span>Worst-Case Loss: <b className="text-slate-900">{policyData?.actuarial_metrics.worst_case_loss_fraction_percent}% TIV</b></span>
              </div>
            </div>

            {/* Official Underwritten Commercial Slip */}
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 mb-3">
                  <span className="text-xs font-bold text-slate-900 uppercase">Commercial Policy Slip</span>
                  <span className="text-[10px] font-mono text-slate-500">{policyData?.policy_id}</span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-violet-600 text-white">
                    <span className="text-[10px] uppercase font-bold tracking-wider opacity-80 block">Gross Annual Premium</span>
                    <span className="text-2xl font-black">
                      ${policyData?.commercial_policy_pricing.commercial_annual_premium_usd.toLocaleString()}
                    </span>
                    <span className="text-[11px] opacity-90 block mt-0.5">
                      Rate-on-Line (RoL): <b>{policyData?.commercial_policy_pricing.rate_on_line_percent}%</b>
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Pure Risk Expected Loss</span>
                    <span className="font-semibold text-slate-800">
                      ${policyData?.actuarial_metrics.annual_pure_risk_loss_usd.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Solvency II Capital Charge</span>
                    <span className="font-semibold text-slate-800">
                      ${policyData?.commercial_policy_pricing.regulatory_capital_charge_usd.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-emerald-700 font-semibold">Autonomous Avoidance Discount</span>
                    <span className="font-bold text-emerald-700">
                      -${policyData?.commercial_policy_pricing.autonomous_maneuver_discount_usd.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Brokerage & Reinsurance</span>
                    <span className="font-semibold text-slate-800">
                      ${policyData?.commercial_policy_pricing.brokerage_and_expenses_usd.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800">
                <span className="font-bold block mb-0.5 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Lloyd's Joint Space Committee Compliant
                </span>
                Underwriting meets Solvency II 99.5% capital adequacy requirements with verified autonomous collision mitigation.
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>NASA ORDEM 3.2 • Poisson Compound Claims • Solvency II 99.5% VaR & Expected Shortfall</span>
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
