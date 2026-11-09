"use client";

import React, { useState, useEffect } from "react";
import {
  Fuel,
  Leaf,
  ShieldCheck,
  AlertTriangle,
  Award,
  DollarSign,
  TrendingUp,
  RefreshCw,
  X,
  CheckCircle2,
  Cloud,
  FileCheck2,
  Copy,
  Sliders,
} from "lucide-react";

interface SafCarbonTwinStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface BlendResult {
  saf_pathway: string;
  blend_ratio_saf_pct: number;
  astm_d7566_compliant: boolean;
  compliance_warning?: string;
  blended_density_kg_m3: number;
  blended_lhv_mj_kg: number;
  blended_aromatics_pct: number;
  sfc_improvement_pct: number;
  lifecycle_ci_gco2e_mj: number;
  co2_lifecycle_reduction_pct: number;
  soot_reduction_pct: number;
  contrail_radiative_forcing_reduction_pct: number;
}

interface MissionResult {
  flight_distance_km: number;
  aircraft_type: string;
  blend_ratio_saf_pct: number;
  saf_pathway: string;
  conventional_fuel_burn_kg: number;
  saf_blend_fuel_burn_kg: number;
  fuel_saved_due_to_lhv_kg: number;
  direct_flight_co2_tonnes: number;
  baseline_lifecycle_co2_tonnes: number;
  saf_lifecycle_co2_tonnes: number;
  net_co2_avoided_tonnes: number;
  corsia_offset_credits_earned: number;
  monetized_corsia_credit_usd: number;
  corsia_cef_certificate_id: string;
  cryptographic_seal_sha256: string;
  timestamp: string;
}

export default function SafCarbonTwinStudio({
  isOpen,
  onClose,
  apiBase,
}: SafCarbonTwinStudioProps) {
  const [safPathway, setSafPathway] = useState("HEFA_SPK");
  const [blendRatio, setBlendRatio] = useState(50);
  const [distanceKm, setDistanceKm] = useState(3800);
  const [aircraftType, setAircraftType] = useState("AeroCraft-X40 Sovereign Transport");
  const [carbonPrice, setCarbonPrice] = useState(48.0);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const [blendData, setBlendData] = useState<BlendResult | null>(null);
  const [missionData, setMissionData] = useState<MissionResult | null>(null);

  const fetchBlendAndMission = async () => {
    setLoading(true);
    try {
      // 1. Evaluate blend
      const resBlend = await fetch(`${apiBase}/api/v1/saf-carbon/evaluate-blend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          saf_pathway_key: safPathway,
          blend_ratio_saf_pct: blendRatio,
        }),
      });
      const dBlend = await resBlend.json();
      if (dBlend.status === "success") {
        setBlendData(dBlend.data);
      }

      // 2. Simulate mission
      const resMiss = await fetch(`${apiBase}/api/v1/saf-carbon/simulate-mission`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          flight_distance_km: distanceKm,
          aircraft_type: aircraftType,
          payload_kg: 18000.0,
          blend_ratio_saf_pct: blendRatio,
          saf_pathway_key: safPathway,
          carbon_price_usd_per_tonne: carbonPrice,
        }),
      });
      const dMiss = await resMiss.json();
      if (dMiss.status === "success") {
        setMissionData(dMiss.data);
      }
    } catch (err) {
      console.error("SAF Twin calculation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchBlendAndMission();
    }
  }, [isOpen, safPathway, blendRatio]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600">
              <Leaf size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  Sustainable Aviation Fuel (SAF) & ICAO CORSIA Carbon Twin
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-600 text-white">
                  STAGE 39
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  ASTM D7566 DROP-IN
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Drop-in kinetics, Breguet LHV payload benefits, non-CO2 contrail mitigation & monetized CORSIA credit certificates
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

        {/* Pathway Selector & Controls Strip */}
        <div className="px-6 py-3 bg-slate-100/70 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-600">SAF Feedstock Pathway:</span>
            <button
              onClick={() => setSafPathway("HEFA_SPK")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                safPathway === "HEFA_SPK"
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              HEFA-SPK (UCO / Bio-Fats)
            </button>
            <button
              onClick={() => setSafPathway("PTL_E_KEROSENE")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                safPathway === "PTL_E_KEROSENE"
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              PtL e-Kerosene (DAC CO2 + H2)
            </button>
            <button
              onClick={() => setSafPathway("FT_SPK")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                safPathway === "FT_SPK"
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              FT-SPK (Waste Biomass)
            </button>
            <button
              onClick={() => setSafPathway("ATJ_SPK")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all border ${
                safPathway === "ATJ_SPK"
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              ATJ-SPK (Alcohol Isobutanol)
            </button>
          </div>

          <button
            onClick={fetchBlendAndMission}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center gap-1.5 transition-colors text-xs shadow-sm"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Recompute Carbon Twin
          </button>
        </div>

        {/* Blend Ratio Interactive Slider */}
        <div className="px-6 py-4 bg-white border-b border-slate-200 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-800">SAF Blend Ratio:</span>
              <span className="text-base font-black text-emerald-600">{blendRatio}%</span>
              <span className="text-slate-400 font-normal">
                ({100 - blendRatio}% Conventional Fossil Jet A-1)
              </span>
            </div>

            <div>
              {blendData?.astm_d7566_compliant ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 size={13} /> ASTM D7566 Certified Drop-In
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                  <AlertTriangle size={13} /> {blendData?.compliance_warning || "Non-Drop-In Configuration"}
                </span>
              )}
            </div>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={blendRatio}
            onChange={(e) => setBlendRatio(Number(e.target.value))}
            className="w-full accent-emerald-600 h-2 bg-slate-200 rounded-lg cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>0% (Neat Jet A-1)</span>
            <span className="text-emerald-700 font-bold">50% ASTM D7566 Drop-In Limit</span>
            <span>100% Neat SAF (Unblended)</span>
          </div>
        </div>

        {/* Main Content Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/40 space-y-6">
          {blendData && (
            <>
              {/* Physical Property & Climate Impact KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Lower Heating Value (LHV)
                  </div>
                  <div className="text-2xl font-black text-emerald-600 mt-1">
                    {blendData.blended_lhv_mj_kg.toFixed(2)}{" "}
                    <span className="text-sm font-medium text-slate-500">MJ/kg</span>
                  </div>
                  <div className="text-xs text-emerald-700 font-semibold mt-0.5">
                    +{blendData.sfc_improvement_pct.toFixed(2)}% energy density advantage
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Lifecycle Carbon Intensity
                  </div>
                  <div className="text-2xl font-black text-slate-800 mt-1">
                    {blendData.lifecycle_ci_gco2e_mj.toFixed(1)}{" "}
                    <span className="text-xs font-normal text-slate-400">gCO2e/MJ</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    -{blendData.co2_lifecycle_reduction_pct.toFixed(1)}% vs fossil baseline (89.0)
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Soot Particle Reduction
                  </div>
                  <div className="text-2xl font-black text-sky-600 mt-1">
                    -{blendData.soot_reduction_pct.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Ice-nucleating aerosol abatement
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Contrail Radiative Forcing
                  </div>
                  <div className="text-2xl font-black text-indigo-600 mt-1">
                    -{blendData.contrail_radiative_forcing_reduction_pct.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Non-CO2 cirrus cooling effect
                  </div>
                </div>
              </div>

              {/* Mission Simulator & Flight Burn Card */}
              {missionData && (
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Fuel size={16} className="text-emerald-600" />
                      Flight Stage Simulation: {distanceKm.toLocaleString()} km Cruise Profile
                    </h3>
                    <div className="text-xs text-slate-500">
                      Aircraft: <span className="font-semibold text-slate-700">{aircraftType}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-400 block uppercase text-[10px]">Baseline Fuel Burn:</span>
                      <span className="font-bold text-slate-800 text-sm">
                        {missionData.conventional_fuel_burn_kg.toLocaleString()} kg
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-slate-400 block uppercase text-[10px]">SAF Blend Fuel Burn:</span>
                      <span className="font-bold text-emerald-700 text-sm">
                        {missionData.saf_blend_fuel_burn_kg.toLocaleString()} kg
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-emerald-600 block uppercase text-[10px] font-bold">LHV Fuel Mass Saved:</span>
                      <span className="font-bold text-emerald-800 text-sm">
                        {missionData.fuel_saved_due_to_lhv_kg.toFixed(1)} kg saved
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-emerald-600 block uppercase text-[10px] font-bold">Net Avoided CO2:</span>
                      <span className="font-bold text-emerald-800 text-sm">
                        {missionData.net_co2_avoided_tonnes.toFixed(2)} tonnes
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* ICAO CORSIA Certificate & Monetization Card */}
              {missionData && (
                <div className="bg-white p-6 rounded-xl border border-emerald-300 shadow-md space-y-5 relative overflow-hidden">
                  <div className="border-b border-slate-200 pb-3 flex justify-between items-end">
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-widest text-emerald-600">
                        International Civil Aviation Organization (ICAO)
                      </div>
                      <h3 className="text-lg font-black text-slate-900 tracking-tight mt-0.5">
                        CORSIA ELIGIBLE FUEL (CEF) COMPLIANCE CERTIFICATE
                      </h3>
                      <div className="text-xs text-slate-500 font-mono">
                        CERTIFICATE ID: {missionData.corsia_cef_certificate_id} • TIMESTAMPS: {missionData.timestamp}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">
                        Monetized Carbon Value (@ ${carbonPrice}/t)
                      </div>
                      <div className="text-2xl font-black text-emerald-600">
                        +${missionData.monetized_corsia_credit_usd.toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-emerald-50/60 border border-emerald-200 text-xs text-emerald-900 font-mono space-y-1">
                    <div>Feedstock Pathway: {missionData.saf_pathway} ({blendRatio}% Volumetric Blend)</div>
                    <div>Certified Net Lifecycle Reduction: -{blendData.co2_lifecycle_reduction_pct}%</div>
                    <div>CORSIA Eligible Offset Credits Earned: {missionData.corsia_offset_credits_earned} CEF Credits</div>
                    <div>Cryptographic Proof: {missionData.cryptographic_seal_sha256}</div>
                  </div>

                  <div className="flex justify-between items-center text-xs pt-1">
                    <span className="text-slate-400">
                      Standard: ICAO Document 16 / CORSIA Default Life Cycle Emissions Values (LSV)
                    </span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(missionData, null, 2));
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold flex items-center gap-1.5 transition-colors"
                    >
                      <Copy size={13} />
                      {copied ? "Copied Certificate" : "Copy CEF Certificate JSON"}
                    </button>
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
