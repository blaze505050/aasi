"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  X,
  Sliders,
  ShieldCheck,
  Zap,
  Box,
  TrendingDown,
  Info,
} from "lucide-react";

interface CompositeFractureStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface CltResult {
  material: string;
  num_plies: number;
  total_thickness_mm: number;
  is_symmetric: boolean;
  effective_engineering_constants: {
    ex_eff_gpa: number;
    ey_eff_gpa: number;
    gxy_eff_gpa: number;
    nu_xy_eff: number;
  };
  abd_matrices: {
    a_matrix_kn_per_mm: number[][];
    b_matrix_n: number[][];
    d_matrix_n_mm: number[][];
  };
  plies: Array<{
    ply_index: number;
    angle_deg: number;
    z_lower_mm: number;
    z_upper_mm: number;
    qbar_11_gpa: number;
    qbar_22_gpa: number;
  }>;
}

interface TsaiWuResult {
  material: string;
  input_stress_state_mpa: {
    sigma1_longitudinal: number;
    sigma2_transverse: number;
    tau12_inplane_shear: number;
  };
  tsai_wu_failure_index: number;
  is_failed: boolean;
  safety_factor: number;
  failure_margin_percent: number;
  envelope_2d_points: Array<{
    sigma1_mpa: number;
    sigma2_mpa: number;
  }>;
}

interface CzmResult {
  material: string;
  cohesive_interface: {
    mode1_fracture_energy_j_m2: number;
    mode2_fracture_energy_j_m2: number;
    bk_exponent_eta: number;
    mode_mixity_ratio_b: number;
    critical_mixed_energy_j_m2: number;
    damage_initiation_separation_um: number;
    ultimate_separation_um: number;
  };
  current_state: {
    applied_mixed_displacement_um: number;
    current_traction_mpa: number;
    damage_variable_d: number;
    is_delaminated: boolean;
  };
  traction_separation_curve: Array<{
    separation_um: number;
    traction_mpa: number;
    damage: number;
  }>;
}

export default function CompositeFractureStudio({
  isOpen,
  onClose,
  apiBase,
}: CompositeFractureStudioProps) {
  const [materialKey, setMaterialKey] = useState<string>("IM7_8552");
  const [activeTab, setActiveTab] = useState<"clt" | "tsai_wu" | "czm">("clt");

  // Stress State
  const [sigma1, setSigma1] = useState<number>(800.0);
  const [sigma2, setSigma2] = useState<number>(30.0);
  const [tau12, setTau12] = useState<number>(25.0);

  // CZM Displacements
  const [deltaN, setDeltaN] = useState<number>(8.0);
  const [deltaS, setDeltaS] = useState<number>(6.0);

  const [loading, setLoading] = useState<boolean>(false);

  const [cltData, setCltData] = useState<CltResult | null>(null);
  const [tsaiWuData, setTsaiWuData] = useState<TsaiWuResult | null>(null);
  const [czmData, setCzmData] = useState<CzmResult | null>(null);

  const applyPreset = (preset: string) => {
    if (preset === "quasi_isotropic") {
      setMaterialKey("IM7_8552");
      setSigma1(800.0);
      setSigma2(30.0);
      setTau12(25.0);
      setDeltaN(8.0);
      setDeltaS(6.0);
      setActiveTab("clt");
    } else if (preset === "hard_spar") {
      setMaterialKey("IM7_8552");
      setSigma1(1400.0);
      setSigma2(20.0);
      setTau12(15.0);
      setActiveTab("tsai_wu");
    } else if (preset === "delamination_onset") {
      setMaterialKey("IM7_8552");
      setDeltaN(14.0);
      setDeltaS(10.0);
      setActiveTab("czm");
    } else if (preset === "fiberglass_radome") {
      setMaterialKey("E_GLASS_913");
      setSigma1(450.0);
      setSigma2(25.0);
      setTau12(20.0);
      setActiveTab("clt");
    }
  };

  const runAnalysis = async () => {
    setLoading(true);
    try {
      // 1. CLT
      const cltRes = await fetch(`${apiBase}/api/v1/composite-fracture/clt-abd`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ material_key: materialKey }),
      });
      const cltJson = await cltRes.json();
      if (cltJson.status === "success") setCltData(cltJson.data);

      // 2. Tsai-Wu
      const twRes = await fetch(`${apiBase}/api/v1/composite-fracture/tsai-wu`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_key: materialKey,
          sigma1_mpa: sigma1,
          sigma2_mpa: sigma2,
          tau12_mpa: tau12,
        }),
      });
      const twJson = await twRes.json();
      if (twJson.status === "success") setTsaiWuData(twJson.data);

      // 3. CZM
      const czmRes = await fetch(`${apiBase}/api/v1/composite-fracture/czm-delamination`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_key: materialKey,
          applied_normal_opening_um: deltaN,
          applied_shear_sliding_um: deltaS,
        }),
      });
      const czmJson = await czmRes.json();
      if (czmJson.status === "success") setCzmData(czmJson.data);
    } catch (e) {
      console.error("Composite analysis error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !cltData) {
      runAnalysis();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden text-slate-800">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-600 flex items-center justify-center font-bold">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Composite Layup & Fracture Mechanics Cohesive Zone Twin
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">
                  Stage 34
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-100 text-slate-700">
                  CLT + Tsai-Wu + B-K CZM
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Classical Laminate Theory ABD stiffness tensor, 3D interactive failure & mixed-mode delamination fracture
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
            <span className="text-xs font-medium text-slate-500 mr-2">Presets:</span>
            <button
              onClick={() => applyPreset("quasi_isotropic")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-100 transition"
            >
              IM7/8552 Quasi-Isotropic Wing Skin [0/45/-45/90]2s
            </button>
            <button
              onClick={() => applyPreset("hard_spar")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition"
            >
              Hard Spar High-Tension Layup (1400 MPa)
            </button>
            <button
              onClick={() => applyPreset("delamination_onset")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition"
            >
              Delamination Cohesive Fracture Onset
            </button>
            <button
              onClick={() => applyPreset("fiberglass_radome")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition"
            >
              E-Glass/913 Radome Structural Laminate
            </button>
          </div>

          {/* Controls Bar */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Composite Material</label>
              <select
                value={materialKey}
                onChange={(e) => setMaterialKey(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="IM7_8552">Hexcel IM7/8552 (Carbon/Epoxy)</option>
                <option value="E_GLASS_913">E-Glass/913 (Fiberglass/Epoxy)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Longitudinal σ1</span>
                <span className="text-slate-500">{sigma1} MPa</span>
              </div>
              <input
                type="range"
                min={-1500}
                max={2500}
                step={50}
                value={sigma1}
                onChange={(e) => setSigma1(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Transverse σ2</span>
                <span className="text-slate-500">{sigma2} MPa</span>
              </div>
              <input
                type="range"
                min={-200}
                max={75}
                step={5}
                value={sigma2}
                onChange={(e) => setSigma2(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">CZM Opening δn</span>
                <span className="text-slate-500">{deltaN} μm</span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                step={1}
                value={deltaN}
                onChange={(e) => setDeltaN(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={runAnalysis}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Activity className="w-3.5 h-3.5 animate-spin" />
                    <span>Solving CLT...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Analysis</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-200 gap-4">
            <button
              onClick={() => setActiveTab("clt")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "clt"
                  ? "border-teal-600 text-teal-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Layers className="w-4 h-4" />
              CLT ABD Matrix & Layup Architecture
            </button>
            <button
              onClick={() => setActiveTab("tsai_wu")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "tsai_wu"
                  ? "border-teal-600 text-teal-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              Tsai-Wu 3D Failure Envelope
            </button>
            <button
              onClick={() => setActiveTab("czm")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "czm"
                  ? "border-teal-600 text-teal-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <TrendingDown className="w-4 h-4" />
              Bilinear CZM Interlaminar Delamination
            </button>
          </div>

          {/* TAB 1: CLT ABD MATRIX & PLY STACK */}
          {activeTab === "clt" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 3D Exploded Ply-Stack Visualizer */}
                <div className="p-5 rounded-xl bg-slate-900 text-white flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold uppercase tracking-wide text-slate-300">
                      16-Ply Exploded Laminate Stack
                    </span>
                    <span className="text-xs text-teal-400 font-semibold">
                      Total: {cltData?.total_thickness_mm} mm
                    </span>
                  </div>

                  {/* SVG Exploded Plies */}
                  <div className="w-full h-64 bg-slate-950 rounded-lg p-3 border border-slate-800 overflow-y-auto space-y-1 flex flex-col justify-center">
                    {cltData?.plies.map((p) => {
                      let color = "#3b82f6"; // 0 deg
                      if (p.angle_deg === 90) color = "#10b981";
                      else if (p.angle_deg === 45) color = "#f59e0b";
                      else if (p.angle_deg === -45) color = "#8b5cf6";

                      return (
                        <div
                          key={p.ply_index}
                          className="flex items-center justify-between px-3 py-1 rounded text-[11px] font-mono border border-slate-700/50"
                          style={{ backgroundColor: `${color}20`, borderLeft: `4px solid ${color}` }}
                        >
                          <span className="text-slate-300">Ply #{p.ply_index} [{p.angle_deg}°]</span>
                          <span className="text-slate-400">z: {p.z_lower_mm} → {p.z_upper_mm} mm</span>
                          <span className="text-slate-200 font-bold">Q11: {p.qbar_11_gpa} GPa</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="flex items-center justify-between text-xs mt-3 pt-3 border-t border-slate-800 text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span> 0° Axial
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span> ±45° Shear
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> 90° Hoop
                    </span>
                  </div>
                </div>

                {/* CLT Engineering Constants & ABD Tables */}
                <div className="lg:col-span-2 space-y-4">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
                      Effective In-Plane Laminate Moduli
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                      <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">Exx (Longitudinal)</span>
                        <span className="text-lg font-black text-slate-900">
                          {cltData?.effective_engineering_constants.ex_eff_gpa} GPa
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">Eyy (Transverse)</span>
                        <span className="text-lg font-black text-slate-900">
                          {cltData?.effective_engineering_constants.ey_eff_gpa} GPa
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">Gxy (In-Plane Shear)</span>
                        <span className="text-lg font-black text-teal-600">
                          {cltData?.effective_engineering_constants.gxy_eff_gpa} GPa
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">νxy (Poisson Ratio)</span>
                        <span className="text-lg font-black text-slate-900">
                          {cltData?.effective_engineering_constants.nu_xy_eff}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* ABD Matrix Inspector */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                        Extensional Stiffness Matrix [A] (kN/mm)
                      </h4>
                      <span className="text-xs font-bold text-emerald-600">
                        {cltData?.is_symmetric ? "Symmetric (Coupling [B] = 0)" : "Unsymmetric [B] ≠ 0"}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 font-mono text-xs">
                      {cltData?.abd_matrices.a_matrix_kn_per_mm.map((row, r) =>
                        row.map((val, c) => (
                          <div
                            key={`${r}-${c}`}
                            className={`p-2 rounded border text-center font-bold ${
                              r === c ? "bg-teal-50 border-teal-300 text-teal-900" : "bg-slate-50 border-slate-200 text-slate-700"
                            }`}
                          >
                            {val}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: TSAI-WU FAILURE CRITERION */}
          {activeTab === "tsai_wu" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 2D Tsai-Wu Stress Ellipse */}
                <div className="lg:col-span-2 p-5 rounded-xl bg-white border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-slate-900">
                        Tsai-Wu First-Ply Failure Envelope (σ1 vs σ2 @ τ12 = {tau12} MPa)
                      </h4>
                      <p className="text-xs text-slate-500">
                        Operating point inside ellipse represents safe flight envelope; outside indicates matrix cracking or fiber rupture.
                      </p>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      tsaiWuData?.is_failed ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"
                    }`}>
                      {tsaiWuData?.is_failed ? "First-Ply Failure" : "Flight Cleared"}
                    </span>
                  </div>

                  {/* SVG Ellipse */}
                  <div className="w-full h-64 bg-slate-50 rounded-lg p-2 border border-slate-200 relative">
                    {tsaiWuData && (
                      <svg className="w-full h-full" viewBox="-2000 -300 4500 500">
                        {/* Axes */}
                        <line x1="-2000" y1="0" x2="2500" y2="0" stroke="#cbd5e1" strokeWidth="20" />
                        <line x1="0" y1="-300" x2="0" y2="200" stroke="#cbd5e1" strokeWidth="20" />

                        {/* Envelope Polygon */}
                        {(() => {
                          const pts = tsaiWuData.envelope_2d_points;
                          const poly = pts.map((p) => `${p.sigma1_mpa},${-p.sigma2_mpa * 3}`).join(" ");
                          return (
                            <polygon
                              points={poly}
                              fill="rgba(13, 148, 136, 0.12)"
                              stroke="#0d9488"
                              strokeWidth="25"
                            />
                          );
                        })()}

                        {/* Current Stress State Marker */}
                        <circle
                          cx={sigma1}
                          cy={-sigma2 * 3}
                          r="50"
                          fill={tsaiWuData.is_failed ? "#f43f5e" : "#10b981"}
                          stroke="#ffffff"
                          strokeWidth="15"
                        />
                      </svg>
                    )}
                  </div>
                </div>

                {/* Margins Card */}
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Structural Reserve Margins
                  </h4>

                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Tsai-Wu Failure Index (IF)</span>
                      <span className={`text-xl font-black ${
                        tsaiWuData?.is_failed ? "text-rose-600" : "text-emerald-600"
                      }`}>
                        {tsaiWuData?.tsai_wu_failure_index}
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Reserve Safety Factor (SF)</span>
                      <span className="text-2xl font-black text-slate-900">
                        {tsaiWuData?.safety_factor}
                      </span>
                    </div>

                    <div className={`p-3 rounded-lg border ${
                      tsaiWuData?.is_failed ? "bg-rose-50 border-rose-200 text-rose-800" : "bg-emerald-50 border-emerald-200 text-emerald-800"
                    } text-xs`}>
                      <span className="font-bold block mb-1">FAA FAR 25.305 Compliance:</span>
                      {tsaiWuData?.is_failed
                        ? "Negative reserve margin. Plies will sustain permanent micro-buckling or matrix crazing."
                        : "Positive reserve margin (>1.5x ultimate factor of safety). Airframe structure fully compliant."}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: BILINEAR CZM DELAMINATION */}
          {activeTab === "czm" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Traction-Separation Chart */}
                <div className="lg:col-span-2 p-5 rounded-xl bg-white border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-slate-900">
                        Bilinear Cohesive Traction-Separation Law (t_n vs δ)
                      </h4>
                      <p className="text-xs text-slate-500">
                        Benzeggagh-Kenane mixed-mode fracture energy release rate softening curve.
                      </p>
                    </div>
                    <span className="text-xs font-bold text-teal-600">
                      Mixity B: {czmData?.cohesive_interface.mode_mixity_ratio_b}
                    </span>
                  </div>

                  <div className="w-full h-56 bg-slate-50 rounded-lg p-2 border border-slate-200 relative">
                    {czmData && (
                      <svg className="w-full h-full" viewBox="0 0 500 180">
                        {/* Traction curve */}
                        {(() => {
                          const pts = czmData.traction_separation_curve;
                          const maxDisp = pts[pts.length - 1].separation_um;
                          const maxTrac = 75.0;

                          const poly = pts
                            .map((p) => {
                              const x = (p.separation_um / maxDisp) * 480 + 10;
                              const y = 180 - (p.traction_mpa / maxTrac) * 160;
                              return `${x},${y}`;
                            })
                            .join(" ");

                          return (
                            <polyline
                              fill="none"
                              stroke="#0d9488"
                              strokeWidth="3"
                              points={poly}
                            />
                          );
                        })()}

                        {/* Current state marker */}
                        {(() => {
                          const maxDisp = czmData.traction_separation_curve[czmData.traction_separation_curve.length - 1].separation_um;
                          const maxTrac = 75.0;
                          const curDisp = czmData.current_state.applied_mixed_displacement_um;
                          const curTrac = czmData.current_state.current_traction_mpa;

                          const cx = (curDisp / maxDisp) * 480 + 10;
                          const cy = 180 - (curTrac / maxTrac) * 160;

                          return (
                            <circle
                              cx={cx}
                              cy={cy}
                              r="6"
                              fill="#ef4444"
                              stroke="#ffffff"
                              strokeWidth="2"
                            />
                          );
                        })()}
                      </svg>
                    )}
                  </div>
                </div>

                {/* CZM Delamination Metrics */}
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Interlaminar Delamination State
                  </h4>

                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Critical Energy Gc (B-K)</span>
                      <span className="text-lg font-black text-slate-900">
                        {czmData?.cohesive_interface.critical_mixed_energy_j_m2} J/m²
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Damage Variable (d)</span>
                      <span className="text-xl font-black text-teal-600">
                        {czmData?.current_state.damage_variable_d}
                      </span>
                      <div className="w-full bg-slate-200 h-2 rounded-full mt-1.5 overflow-hidden">
                        <div
                          className="bg-teal-600 h-full rounded-full transition-all"
                          style={{ width: `${(czmData?.current_state.damage_variable_d ?? 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Current Interfacial Traction</span>
                      <span className="text-lg font-black text-slate-800">
                        {czmData?.current_state.current_traction_mpa} MPa
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Classical Laminate Theory • 3D Tsai-Wu Quadratic Envelope • Bilinear Cohesive Zone Modeling</span>
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
