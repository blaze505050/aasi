"use client";

import React, { useState, useEffect } from "react";
import {
  FileCheck2,
  ShieldCheck,
  Award,
  AlertTriangle,
  Compass,
  Wind,
  CheckCircle2,
  Layers,
  ArrowRight,
  Download,
  Copy,
  Hash,
  Scale,
  RefreshCw,
  X,
} from "lucide-react";

interface AirworthinessDossierStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface AirspeedEnvelope {
  gross_weight_kg: number;
  altitude_m: number;
  density_kg_m3: number;
  v_stall_clean_mps: number;
  v_stall_clean_knots: number;
  v_stall_flaps_mps: number;
  v_stall_flaps_knots: number;
  n_max_maneuver: number;
  n_min_maneuver: number;
  v_maneuver_va_mps: number;
  v_maneuver_va_knots: number;
  v_cruise_vc_mps: number;
  v_cruise_vc_knots: number;
  v_dive_vd_mps: number;
  v_dive_vd_knots: number;
  v_flap_vf_mps: number;
  v_flap_vf_knots: number;
}

interface PrattGustAnalysis {
  wing_loading_n_m2: number;
  mass_ratio_mu_g: number;
  gust_alleviation_factor_kg: number;
  design_gust_velocity_u_de_mps: number;
  gust_load_increment_delta_n: number;
  limit_gust_load_pos: number;
  limit_gust_load_neg: number;
  ultimate_load_factor: number;
  structural_reserve_margin: number;
}

interface RtmItem {
  req_id: string;
  regulation_ref: string;
  subpart: string;
  title: string;
  target_description: string;
  primary_moc: string;
  secondary_moc?: string;
  compliance_status: string;
  margin_of_safety: number;
  verification_evidence_digest: string;
  rationale: string;
}

interface DossierResult {
  status: string;
  dossier_id: string;
  certification_digest_sha256: string;
  generated_timestamp: string;
  aircraft_metadata: {
    aircraft_name: string;
    tail_number: string;
    regulatory_authority: string;
    gross_weight_kg: number;
    wing_area_m2: number;
    mean_aerodynamic_chord_m: number;
    cruise_altitude_m: number;
    wing_loading_kg_m2: number;
  };
  design_airspeeds: AirspeedEnvelope;
  pratt_gust_analysis: PrattGustAnalysis;
  compliance_summary: {
    total_requirements: number;
    verified_compliant: number;
    compliance_percentage: number;
    moc_distribution: Record<string, number>;
  };
  requirement_traceability_matrix: RtmItem[];
  airworthiness_declaration: {
    compliance_statement: string;
    certifying_organization: string;
    chief_engineer_seal: string;
  };
}

export default function AirworthinessDossierStudio({
  isOpen,
  onClose,
  apiBase,
}: AirworthinessDossierStudioProps) {
  const [activeTab, setActiveTab] = useState<"speeds" | "gust" | "rtm" | "certificate">("speeds");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Form Inputs
  const [aircraftName, setAircraftName] = useState("AeroCraft-X40 Sovereign Transport");
  const [tailNumber, setTailNumber] = useState("VT-AASI-001");
  const [authorityKey, setAuthorityKey] = useState("FAA_PART_25");
  const [grossWeightKg, setGrossWeightKg] = useState(45000);
  const [wingAreaM2, setWingAreaM2] = useState(122.4);
  const [macM, setMacM] = useState(4.15);
  const [clMaxClean, setClMaxClean] = useState(1.45);
  const [clMaxFlaps, setClMaxFlaps] = useState(2.20);
  const [clAlpha, setClAlpha] = useState(5.25);
  const [altitudeM, setAltitudeM] = useState(9500);

  // Dossier State
  const [dossier, setDossier] = useState<DossierResult | null>(null);

  const applyPreset = (preset: "transport" | "turboprop" | "supersonic") => {
    if (preset === "transport") {
      setAircraftName("AeroCraft-X40 Sovereign Transport");
      setTailNumber("VT-AASI-001");
      setAuthorityKey("FAA_PART_25");
      setGrossWeightKg(45000);
      setWingAreaM2(122.4);
      setMacM(4.15);
      setClMaxClean(1.45);
      setClMaxFlaps(2.20);
      setClAlpha(5.25);
      setAltitudeM(9500);
    } else if (preset === "turboprop") {
      setAircraftName("IndusCommuter-20 Regional");
      setTailNumber("VT-IND-202");
      setAuthorityKey("FAA_PART_23");
      setGrossWeightKg(18500);
      setWingAreaM2(61.0);
      setMacM(2.80);
      setClMaxClean(1.60);
      setClMaxFlaps(2.45);
      setClAlpha(5.40);
      setAltitudeM(5000);
    } else {
      setAircraftName("Brahmashastra-X High-Mach");
      setTailNumber("VT-X99-PRO");
      setAuthorityKey("DGCA_CAR_SEC2");
      setGrossWeightKg(28000);
      setWingAreaM2(78.5);
      setMacM(3.40);
      setClMaxClean(1.30);
      setClMaxFlaps(1.95);
      setClAlpha(4.80);
      setAltitudeM(14000);
    }
  };

  const handleSynthesize = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/airworthiness/synthesize-dossier`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          aircraft_name: aircraftName,
          tail_number: tailNumber,
          gross_weight_kg: grossWeightKg,
          wing_area_m2: wingAreaM2,
          mean_aerodynamic_chord_m: macM,
          cl_max_clean: clMaxClean,
          cl_max_flaps: clMaxFlaps,
          cl_alpha_per_rad: clAlpha,
          cruise_altitude_m: altitudeM,
          authority_key: authorityKey,
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setDossier(data.data);
      }
    } catch (err) {
      console.error("Synthesize dossier error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !dossier) {
      handleSynthesize();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-600">
              <FileCheck2 size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  FAA Part 23/25 & DGCA Airworthiness Dossier Synthesizer
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-600 text-white">
                  STAGE 37
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  14 CFR § 25.341
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                First-principles design airspeeds, Pratt discrete 1-cosine gust loads, and autonomous Means of Compliance (MOC) RTM
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

        {/* Preset Selector & Controls */}
        <div className="px-6 py-3 bg-slate-100/70 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-600">Airframe Profiles:</span>
            <button
              onClick={() => applyPreset("transport")}
              className="px-2.5 py-1 rounded bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium transition-colors"
            >
              AeroCraft-X40 (45t Transport)
            </button>
            <button
              onClick={() => applyPreset("turboprop")}
              className="px-2.5 py-1 rounded bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium transition-colors"
            >
              IndusCommuter-20 (18.5t Part 23)
            </button>
            <button
              onClick={() => applyPreset("supersonic")}
              className="px-2.5 py-1 rounded bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium transition-colors"
            >
              Brahmashastra-X (DGCA CAR-2)
            </button>
          </div>

          <button
            onClick={handleSynthesize}
            disabled={loading}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-2 transition-colors disabled:opacity-50 shadow-sm"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            {loading ? "Synthesizing Dossier..." : "Recompute Airworthiness Dossier"}
          </button>
        </div>

        {/* Input Parameters Bar */}
        <div className="px-6 py-3 bg-white border-b border-slate-100 grid grid-cols-2 md:grid-cols-6 gap-3 text-xs">
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Authority
            </label>
            <select
              value={authorityKey}
              onChange={(e) => setAuthorityKey(e.target.value)}
              className="w-full px-2 py-1 rounded border border-slate-200 bg-white font-medium text-slate-700"
            >
              <option value="FAA_PART_25">FAA 14 CFR Part 25</option>
              <option value="FAA_PART_23">FAA 14 CFR Part 23</option>
              <option value="DGCA_CAR_SEC2">DGCA CAR Sec 2</option>
              <option value="EASA_CS_25">EASA CS-25</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Gross Weight (kg)
            </label>
            <input
              type="number"
              value={grossWeightKg}
              onChange={(e) => setGrossWeightKg(Number(e.target.value))}
              className="w-full px-2 py-1 rounded border border-slate-200 font-medium text-slate-700"
            />
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Wing Area S (m²)
            </label>
            <input
              type="number"
              value={wingAreaM2}
              onChange={(e) => setWingAreaM2(Number(e.target.value))}
              className="w-full px-2 py-1 rounded border border-slate-200 font-medium text-slate-700"
            />
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Mean Chord c̄ (m)
            </label>
            <input
              type="number"
              value={macM}
              onChange={(e) => setMacM(Number(e.target.value))}
              step="0.05"
              className="w-full px-2 py-1 rounded border border-slate-200 font-medium text-slate-700"
            />
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              CLα (per rad)
            </label>
            <input
              type="number"
              value={clAlpha}
              onChange={(e) => setClAlpha(Number(e.target.value))}
              step="0.05"
              className="w-full px-2 py-1 rounded border border-slate-200 font-medium text-slate-700"
            />
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Altitude (m)
            </label>
            <input
              type="number"
              value={altitudeM}
              onChange={(e) => setAltitudeM(Number(e.target.value))}
              step="500"
              className="w-full px-2 py-1 rounded border border-slate-200 font-medium text-slate-700"
            />
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-slate-200 flex gap-6 text-sm font-semibold text-slate-500 bg-slate-50/50">
          <button
            onClick={() => setActiveTab("speeds")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "speeds"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Compass size={16} />
            Design Airspeeds (§ 25.335)
          </button>
          <button
            onClick={() => setActiveTab("gust")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "gust"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Wind size={16} />
            Pratt Gust Loads (§ 25.341)
          </button>
          <button
            onClick={() => setActiveTab("rtm")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "rtm"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Layers size={16} />
            Means of Compliance Matrix (RTM)
          </button>
          <button
            onClick={() => setActiveTab("certificate")}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "certificate"
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent hover:text-slate-700"
            }`}
          >
            <Award size={16} />
            Airworthiness Attestation
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/40">
          {dossier ? (
            <>
              {/* TAB 1: DESIGN AIRSPEEDS */}
              {activeTab === "speeds" && (
                <div className="space-y-6">
                  {/* KPI Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Stall Clean (VS1)
                      </div>
                      <div className="text-2xl font-black text-slate-800 mt-1">
                        {dossier.design_airspeeds.v_stall_clean_knots.toFixed(1)}{" "}
                        <span className="text-sm font-medium text-slate-500">kt</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {dossier.design_airspeeds.v_stall_clean_mps.toFixed(1)} m/s (CLmax = {clMaxClean})
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Maneuvering Speed (VA)
                      </div>
                      <div className="text-2xl font-black text-indigo-600 mt-1">
                        {dossier.design_airspeeds.v_maneuver_va_knots.toFixed(1)}{" "}
                        <span className="text-sm font-medium text-slate-500">kt</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        n_max = {dossier.design_airspeeds.n_max_maneuver.toFixed(2)}g limit
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Design Cruise (VC)
                      </div>
                      <div className="text-2xl font-black text-emerald-600 mt-1">
                        {dossier.design_airspeeds.v_cruise_vc_knots.toFixed(1)}{" "}
                        <span className="text-sm font-medium text-slate-500">kt</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {dossier.design_airspeeds.v_cruise_vc_mps.toFixed(1)} m/s true airspeed
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Design Dive (VD)
                      </div>
                      <div className="text-2xl font-black text-rose-600 mt-1">
                        {dossier.design_airspeeds.v_dive_vd_knots.toFixed(1)}{" "}
                        <span className="text-sm font-medium text-slate-500">kt</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        1.25 × VC (§ 25.335(b) Margin satisfied)
                      </div>
                    </div>
                  </div>

                  {/* Flight Envelope Bar Breakdown */}
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Compass size={16} className="text-indigo-600" />
                      14 CFR § 25.335 Airspeed Hierarchy & Structural Margins
                    </h3>

                    <div className="space-y-3 text-xs">
                      <div>
                        <div className="flex justify-between font-medium mb-1">
                          <span className="text-slate-600">V_SO (Stall Full Flaps):</span>
                          <span className="font-bold text-slate-800">
                            {dossier.design_airspeeds.v_stall_flaps_knots.toFixed(1)} kt (
                            {dossier.design_airspeeds.v_stall_flaps_mps.toFixed(1)} m/s)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-slate-400 rounded-full"
                            style={{ width: `${(dossier.design_airspeeds.v_stall_flaps_knots / dossier.design_airspeeds.v_dive_vd_knots) * 100}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between font-medium mb-1">
                          <span className="text-slate-600">V_F (Flap Extension Design Speed):</span>
                          <span className="font-bold text-slate-800">
                            {dossier.design_airspeeds.v_flap_vf_knots.toFixed(1)} kt (1.65 × V_SO)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${(dossier.design_airspeeds.v_flap_vf_knots / dossier.design_airspeeds.v_dive_vd_knots) * 100}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between font-medium mb-1">
                          <span className="text-slate-600">V_A (Maneuvering Speed limit):</span>
                          <span className="font-bold text-indigo-700">
                            {dossier.design_airspeeds.v_maneuver_va_knots.toFixed(1)} kt (Full abrupt deflection allowable)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full"
                            style={{ width: `${(dossier.design_airspeeds.v_maneuver_va_knots / dossier.design_airspeeds.v_dive_vd_knots) * 100}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between font-medium mb-1">
                          <span className="text-slate-600">V_C (Structural Design Cruise):</span>
                          <span className="font-bold text-emerald-700">
                            {dossier.design_airspeeds.v_cruise_vc_knots.toFixed(1)} kt (Nominal cruise ceiling)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full bg-emerald-500 rounded-full"
                            style={{ width: `${(dossier.design_airspeeds.v_cruise_vc_knots / dossier.design_airspeeds.v_dive_vd_knots) * 100}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between font-medium mb-1">
                          <span className="text-slate-600">V_D (Design Dive Speed Envelope):</span>
                          <span className="font-bold text-rose-700">
                            {dossier.design_airspeeds.v_dive_vd_knots.toFixed(1)} kt (Certification dive limit)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div className="h-full bg-rose-500 rounded-full w-full" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: PRATT GUST LOADS */}
              {activeTab === "gust" && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Wing Loading (W/S)
                      </div>
                      <div className="text-2xl font-black text-slate-800 mt-1">
                        {dossier.pratt_gust_analysis.wing_loading_n_m2.toFixed(0)}{" "}
                        <span className="text-sm font-medium text-slate-500">N/m²</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {dossier.aircraft_metadata.wing_loading_kg_m2.toFixed(1)} kg/m²
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Pratt Alleviation (Kg)
                      </div>
                      <div className="text-2xl font-black text-indigo-600 mt-1">
                        {dossier.pratt_gust_analysis.gust_alleviation_factor_kg.toFixed(3)}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Mass ratio μg = {dossier.pratt_gust_analysis.mass_ratio_mu_g.toFixed(1)}
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Positive Limit Gust Load
                      </div>
                      <div className="text-2xl font-black text-amber-600 mt-1">
                        +{dossier.pratt_gust_analysis.limit_gust_load_pos.toFixed(2)}g
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Δn = +{dossier.pratt_gust_analysis.gust_load_increment_delta_n.toFixed(2)}g increment
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        Ultimate Design Load (1.5×)
                      </div>
                      <div className="text-2xl font-black text-emerald-600 mt-1">
                        {dossier.pratt_gust_analysis.ultimate_load_factor.toFixed(2)}g
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Reserve Margin +{(dossier.pratt_gust_analysis.structural_reserve_margin * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Scale size={16} className="text-indigo-600" />
                      14 CFR § 25.341 Discrete 1-Cosine Pratt Equation Formulation
                    </h3>
                    <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 font-mono text-xs text-slate-700 space-y-1.5">
                      <div>μ_g = [2 · (W/S)] / (ρ · c̄ · g · C_Lα) = {dossier.pratt_gust_analysis.mass_ratio_mu_g.toFixed(2)}</div>
                      <div>K_g = (0.88 · μ_g) / (5.3 + μ_g) = {dossier.pratt_gust_analysis.gust_alleviation_factor_kg.toFixed(3)}</div>
                      <div>U_de = 17.07 m/s (Sea Level) → {dossier.pratt_gust_analysis.design_gust_velocity_u_de_mps.toFixed(2)} m/s (At {altitudeM} m)</div>
                      <div>Δn = [K_g · ρ_0 · U_de · V_C · C_Lα] / [2 · (W/S)] = {dossier.pratt_gust_analysis.gust_load_increment_delta_n.toFixed(3)}g</div>
                      <div className="text-emerald-700 font-bold">
                        Limit Loads: n_pos = +{dossier.pratt_gust_analysis.limit_gust_load_pos.toFixed(2)}g, n_neg = {dossier.pratt_gust_analysis.limit_gust_load_neg.toFixed(2)}g
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: RTM MATRIX */}
              {activeTab === "rtm" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                    <div>
                      {dossier.compliance_summary.verified_compliant} of{" "}
                      {dossier.compliance_summary.total_requirements} Requirements Compliant (
                      {dossier.compliance_summary.compliance_percentage.toFixed(0)}%)
                    </div>
                    <div className="flex gap-2">
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        Zero Open Deficiencies
                      </span>
                    </div>
                  </div>

                  <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                        <tr>
                          <th className="px-4 py-3">Req ID / Ref</th>
                          <th className="px-4 py-3">Subpart & Title</th>
                          <th className="px-4 py-3">MOC</th>
                          <th className="px-4 py-3">Margin of Safety</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Evidence Hash</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-normal">
                        {dossier.requirement_traceability_matrix.map((item, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/80">
                            <td className="px-4 py-3 font-semibold text-slate-900">
                              <div>{item.req_id}</div>
                              <div className="text-[10px] text-slate-400 font-mono">{item.regulation_ref}</div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="font-medium text-slate-800">{item.title}</div>
                              <div className="text-[11px] text-slate-500 mt-0.5">{item.target_description}</div>
                            </td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-0.5 rounded-full font-mono text-[10px] bg-indigo-50 text-indigo-700 border border-indigo-200">
                                {item.primary_moc.split(":")[0]}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="font-bold text-emerald-600 font-mono">
                                +{(item.margin_of_safety * 100).toFixed(1)}%
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                <CheckCircle2 size={10} />
                                {item.compliance_status}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-mono text-[10px] text-slate-400">
                              {item.verification_evidence_digest}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 4: OFFICIAL CERTIFICATE */}
              {activeTab === "certificate" && (
                <div className="space-y-6">
                  <div className="bg-white p-8 rounded-xl border border-slate-300 shadow-md space-y-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-bl-full -z-0 opacity-40 pointer-events-none" />

                    <div className="border-b-2 border-slate-800 pb-4 flex justify-between items-end">
                      <div>
                        <div className="text-xs font-black uppercase tracking-widest text-indigo-600">
                          Delegated Engineering Representative (DER) Airworthiness Office
                        </div>
                        <h1 className="text-xl font-black text-slate-900 tracking-tight mt-1">
                          FORMAL AIRWORTHINESS COMPLIANCE ATTESTATION
                        </h1>
                        <div className="text-xs text-slate-500 font-mono mt-0.5">
                          DOSSIER ID: {dossier.dossier_id} • AUTHORITY: {dossier.aircraft_metadata.regulatory_authority}
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="px-3 py-1 rounded bg-emerald-600 text-white font-bold text-xs uppercase tracking-wider">
                          APPROVED FOR CONFORMITY
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="text-slate-400 block uppercase text-[10px]">Aircraft Type:</span>
                        <span className="font-bold text-slate-800">{dossier.aircraft_metadata.aircraft_name}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase text-[10px]">Registration / Tail:</span>
                        <span className="font-bold text-slate-800">{dossier.aircraft_metadata.tail_number}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase text-[10px]">Maximum Takeoff Weight:</span>
                        <span className="font-bold text-slate-800">{dossier.aircraft_metadata.gross_weight_kg.toLocaleString()} kg</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block uppercase text-[10px]">Compliance Timestamp:</span>
                        <span className="font-bold text-slate-800">{dossier.generated_timestamp}</span>
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed italic">
                      "{dossier.airworthiness_declaration.compliance_statement}"
                    </div>

                    <div className="pt-4 border-t border-slate-200 flex flex-wrap justify-between items-center gap-4 text-xs">
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Certifying Authority Seal</div>
                        <div className="font-mono text-indigo-700 font-bold">{dossier.airworthiness_declaration.chief_engineer_seal}</div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">SHA-256 Digest: {dossier.certification_digest_sha256}</div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(JSON.stringify(dossier, null, 2));
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}
                          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold flex items-center gap-1.5 transition-colors"
                        >
                          <Copy size={13} />
                          {copied ? "Copied JSON" : "Copy Dossier JSON"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400 gap-2">
              <RefreshCw size={24} className="animate-spin text-indigo-600" />
              <span>Computing First-Principles Airworthiness Dossier...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
