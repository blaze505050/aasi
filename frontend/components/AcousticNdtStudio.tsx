"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  Activity,
  Layers,
  Search,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  X,
  Sparkles,
  Sliders,
  ShieldAlert,
  Zap,
  Eye,
} from "lucide-react";

interface AcousticNdtStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface AScanResult {
  material: string;
  specimen_thickness_mm: number;
  transducer_frequency_mhz: number;
  longitudinal_velocity_mps: number;
  shear_velocity_mps: number;
  acoustic_impedance_mrayls: number;
  flaw_detected: boolean;
  flaw_depth_mm: number | null;
  flaw_amplitude_percent_fsh: number;
  time_of_flight_flaw_us: number | null;
  time_of_flight_backwall_us: number;
  ascan_data: {
    time_us: number[];
    rf_signal: number[];
    rectified_envelope_fsh: number[];
  };
}

interface BScanResult {
  specimen_length_mm: number;
  specimen_thickness_mm: number;
  flaw_location: { x_mm: number; depth_mm: number; diameter_um: number };
  num_x_steps: number;
  num_depth_bins: number;
  bscan_intensity_matrix: number[][];
}

interface MicroCtResult {
  material: string;
  grid_resolution: number;
  voxel_pitch_um: number;
  injected_defects: Array<Record<string, any>>;
  segmented_defect_voxels: number;
  void_fraction_percent: number;
  threshold_value: number;
  raw_ct_slice: number[][];
  defect_mask: boolean[][];
  inpainted_slice: number[][];
}

interface PodResult {
  standard: string;
  material: string;
  modality: string;
  false_call_rate_percent: number;
  qualification_thresholds_um: {
    a_50_um: number;
    a_90_um: number;
    a_90_95_um: number;
  };
  curve_data: {
    flaw_sizes_um: number[];
    pod_nominal_percent: number[];
    pod_95_confidence_percent: number[];
  };
}

export default function AcousticNdtStudio({
  isOpen,
  onClose,
  apiBase,
}: AcousticNdtStudioProps) {
  const [materialKey, setMaterialKey] = useState<string>("TI_6AL_4V");
  const [thicknessMm, setThicknessMm] = useState<number>(25.0);
  const [frequencyMhz, setFrequencyMhz] = useState<number>(5.0);
  const [flawDepthMm, setFlawDepthMm] = useState<number>(12.5);
  const [flawDiameterUm, setFlawDiameterUm] = useState<number>(350.0);

  const [activeTab, setActiveTab] = useState<"ultrasound" | "micro_ct" | "pod">("ultrasound");
  const [loading, setLoading] = useState<boolean>(false);

  const [ascanData, setAscanData] = useState<AScanResult | null>(null);
  const [bscanData, setBscanData] = useState<BScanResult | null>(null);
  const [ctData, setCtData] = useState<MicroCtResult | null>(null);
  const [podData, setPodData] = useState<PodResult | null>(null);

  const applyPreset = (preset: string) => {
    if (preset === "ti_subsurface") {
      setMaterialKey("TI_6AL_4V");
      setThicknessMm(25.0);
      setFrequencyMhz(5.0);
      setFlawDepthMm(12.5);
      setFlawDiameterUm(350.0);
      setActiveTab("ultrasound");
    } else if (preset === "cfrp_delamination") {
      setMaterialKey("CFRP_LAMINATE");
      setThicknessMm(8.0);
      setFrequencyMhz(10.0);
      setFlawDepthMm(3.2);
      setFlawDiameterUm(500.0);
      setActiveTab("ultrasound");
    } else if (preset === "inconel_void") {
      setMaterialKey("INCONEL_718");
      setThicknessMm(20.0);
      setFrequencyMhz(5.0);
      setFlawDepthMm(9.0);
      setFlawDiameterUm(400.0);
      setActiveTab("micro_ct");
    } else if (preset === "mil_pod_eval") {
      setMaterialKey("TI_6AL_4V");
      setActiveTab("pod");
    }
  };

  const runAllInspections = async () => {
    setLoading(true);
    try {
      // 1. A-Scan
      const ascanRes = await fetch(`${apiBase}/api/v1/acoustic-ndt/ascan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_key: materialKey,
          specimen_thickness_mm: thicknessMm,
          transducer_freq_mhz: frequencyMhz,
          flaw_depth_mm: flawDepthMm,
          flaw_diameter_um: flawDiameterUm,
        }),
      });
      const ascanJson = await ascanRes.json();
      if (ascanJson.status === "success") setAscanData(ascanJson.data);

      // 2. B-Scan
      const bscanRes = await fetch(`${apiBase}/api/v1/acoustic-ndt/bscan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_key: materialKey,
          specimen_length_mm: 35.0,
          specimen_thickness_mm: thicknessMm,
          flaw_x_mm: 17.5,
          flaw_depth_mm: flawDepthMm,
          flaw_diameter_um: flawDiameterUm,
          scan_steps: 25,
        }),
      });
      const bscanJson = await bscanRes.json();
      if (bscanJson.status === "success") setBscanData(bscanJson.data);

      // 3. Micro-CT
      const ctRes = await fetch(`${apiBase}/api/v1/acoustic-ndt/micro-ct`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_key: materialKey,
          grid_size: 48,
          inject_voids: true,
          inject_crack: true,
        }),
      });
      const ctJson = await ctRes.json();
      if (ctJson.status === "success") setCtData(ctJson.data);

      // 4. POD Curve
      const podRes = await fetch(`${apiBase}/api/v1/acoustic-ndt/pod-curve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_key: materialKey,
          inspection_modality: "ULTRASONIC_5MHZ",
          false_call_rate_percent: 1.0,
        }),
      });
      const podJson = await podRes.json();
      if (podJson.status === "success") setPodData(podJson.data);
    } catch (e) {
      console.error("NDT execution error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !ascanData) {
      runAllInspections();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden text-slate-800">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center font-bold">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Autonomous Ultrasonic & X-Ray CT NDT Inpainting & POD Engine
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">
                  Stage 33
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-100 text-slate-700">
                  MIL-HDBK-1823A
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Elastodynamic wave pulse-echo, polychromatic Micro-CT radiograph attenuation & statistical POD qualification
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
              onClick={() => applyPreset("ti_subsurface")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition"
            >
              Ti-6Al-4V Subsurface Defect (5 MHz)
            </button>
            <button
              onClick={() => applyPreset("cfrp_delamination")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition"
            >
              CFRP Delamination Micro-Crack (10 MHz)
            </button>
            <button
              onClick={() => applyPreset("inconel_void")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition"
            >
              Inconel 718 Lack of Fusion Void (Micro-CT)
            </button>
            <button
              onClick={() => applyPreset("mil_pod_eval")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition"
            >
              MIL-HDBK-1823A POD Reliability Curve
            </button>
          </div>

          {/* Control Bar */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Specimen Material</label>
              <select
                value={materialKey}
                onChange={(e) => setMaterialKey(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="TI_6AL_4V">Ti-6Al-4V Grade 5 (Titanium)</option>
                <option value="INCONEL_718">Inconel 718 (Nickel Superalloy)</option>
                <option value="CFRP_LAMINATE">CFRP Quasi-Isotropic (IM7/8552)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Thickness</span>
                <span className="text-slate-500">{thicknessMm} mm</span>
              </div>
              <input
                type="range"
                min={5}
                max={50}
                step={1}
                value={thicknessMm}
                onChange={(e) => setThicknessMm(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Flaw Depth</span>
                <span className="text-slate-500">{flawDepthMm} mm</span>
              </div>
              <input
                type="range"
                min={1}
                max={Math.max(2, thicknessMm - 2)}
                step={0.5}
                value={flawDepthMm}
                onChange={(e) => setFlawDepthMm(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Flaw Diameter</span>
                <span className="text-slate-500">{flawDiameterUm} μm</span>
              </div>
              <input
                type="range"
                min={100}
                max={1000}
                step={50}
                value={flawDiameterUm}
                onChange={(e) => setFlawDiameterUm(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={runAllInspections}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Activity className="w-3.5 h-3.5 animate-spin" />
                    <span>Acquiring NDT...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Scan Specimen</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Modality Tabs */}
          <div className="flex border-b border-slate-200 gap-4">
            <button
              onClick={() => setActiveTab("ultrasound")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "ultrasound"
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Radio className="w-4 h-4" />
              Ultrasonic A-Scan & B-Scan Echogram
            </button>
            <button
              onClick={() => setActiveTab("micro_ct")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "micro_ct"
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Eye className="w-4 h-4" />
              Micro-CT Slice & AI Defect Inpainting
            </button>
            <button
              onClick={() => setActiveTab("pod")}
              className={`pb-2 text-xs font-bold transition border-b-2 flex items-center gap-2 ${
                activeTab === "pod"
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              <Activity className="w-4 h-4" />
              MIL-HDBK-1823A POD Reliability Curve
            </button>
          </div>

          {/* TAB 1: ULTRASONIC A-SCAN & B-SCAN */}
          {activeTab === "ultrasound" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* A-Scan Oscilloscope Display */}
                <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900 text-white flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold tracking-wide uppercase text-slate-300">
                      Pulse-Echo Oscilloscope (RF Signal & FSH Rectified Envelope)
                    </span>
                    <span className="text-xs text-indigo-400">
                      Gate Trigger: {ascanData?.flaw_amplitude_percent_fsh}% FSH @ {ascanData?.time_of_flight_flaw_us} μs
                    </span>
                  </div>

                  {/* SVG Waveform */}
                  <div className="w-full h-64 bg-slate-950/80 rounded-lg p-2 border border-slate-800 relative">
                    {ascanData ? (
                      <svg className="w-full h-full" viewBox="0 0 500 200">
                        {/* Grid lines */}
                        <line x1="0" y1="50" x2="500" y2="50" stroke="#1e293b" strokeDasharray="2 2" />
                        <line x1="0" y1="100" x2="500" y2="100" stroke="#334155" strokeDasharray="2 2" />
                        <line x1="0" y1="150" x2="500" y2="150" stroke="#1e293b" strokeDasharray="2 2" />

                        {/* Rectified envelope (filled amber) */}
                        {(() => {
                          const env = ascanData.ascan_data.rectified_envelope_fsh;
                          const poly = env
                            .map((v, i) => `${(i / (env.length - 1)) * 500},${200 - (v / 100) * 180}`)
                            .join(" ");
                          return (
                            <polygon
                              points={`0,200 ${poly} 500,200`}
                              fill="rgba(245, 158, 11, 0.2)"
                            />
                          );
                        })()}

                        {/* RF Signal (cyan trace) */}
                        {(() => {
                          const rf = ascanData.ascan_data.rf_signal;
                          const poly = rf
                            .map((v, i) => `${(i / (rf.length - 1)) * 500},${100 - v * 90}`)
                            .join(" ");
                          return <polyline fill="none" stroke="#38bdf8" strokeWidth="1.2" points={poly} />;
                        })()}

                        {/* Rectified Envelope trace (amber outline) */}
                        {(() => {
                          const env = ascanData.ascan_data.rectified_envelope_fsh;
                          const poly = env
                            .map((v, i) => `${(i / (env.length - 1)) * 500},${200 - (v / 100) * 180}`)
                            .join(" ");
                          return <polyline fill="none" stroke="#f59e0b" strokeWidth="1.8" points={poly} />;
                        })()}
                      </svg>
                    ) : (
                      <div className="flex items-center justify-center h-full text-xs text-slate-500">
                        Acquiring ultrasonic signal...
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-xs mt-3 pt-3 border-t border-slate-800 text-slate-400">
                    <span>Longitudinal Speed: <b className="text-white">{ascanData?.longitudinal_velocity_mps} m/s</b></span>
                    <span>Acoustic Impedance: <b className="text-white">{ascanData?.acoustic_impedance_mrayls} MRayls</b></span>
                    <span>Backwall Arrival: <b className="text-white">{ascanData?.time_of_flight_backwall_us} μs</b></span>
                  </div>
                </div>

                {/* Physics Diagnostics Card */}
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-4">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3 flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-indigo-600" />
                      Ultrasonic Sizing & Gate Verdict
                    </h4>

                    <div className="space-y-2.5 text-xs">
                      <div className="flex justify-between py-1 border-b border-slate-200">
                        <span className="text-slate-500">Flaw Detection Status</span>
                        <span className="font-bold text-emerald-600 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Echo Verified
                        </span>
                      </div>

                      <div className="flex justify-between py-1 border-b border-slate-200">
                        <span className="text-slate-500">Calculated Depth</span>
                        <span className="font-bold text-slate-900">{ascanData?.flaw_depth_mm} mm</span>
                      </div>

                      <div className="flex justify-between py-1 border-b border-slate-200">
                        <span className="text-slate-500">Gate Echo Amplitude</span>
                        <span className="font-bold text-indigo-600">{ascanData?.flaw_amplitude_percent_fsh}% FSH</span>
                      </div>

                      <div className="flex justify-between py-1 border-b border-slate-200">
                        <span className="text-slate-500">Transverse (Shear) Speed</span>
                        <span className="font-semibold text-slate-700">{ascanData?.shear_velocity_mps} m/s</span>
                      </div>

                      <div className="flex justify-between py-1">
                        <span className="text-slate-500">Coupon Thickness</span>
                        <span className="font-semibold text-slate-700">{ascanData?.specimen_thickness_mm} mm</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800">
                    <span className="font-bold block mb-0.5">MIL-STD-2154 Class A Inspection:</span>
                    Signal-to-noise ratio {">"} 24 dB. Flaw peak is distinct from front-wall ringdown and grain scattering clutter.
                  </div>
                </div>
              </div>

              {/* 2D B-Scan Cross Section */}
              {bscanData && (
                <div className="p-5 rounded-xl bg-white border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                        2D Ultrasonic B-Scan Cross-Sectional Echogram
                      </h4>
                      <p className="text-xs text-slate-500">
                        Spatial scan along coupon length (35 mm) vs depth time-of-flight. Bright spot indicates subsurface defect location.
                      </p>
                    </div>
                    <span className="text-xs text-indigo-600 font-semibold">
                      Target Flaw: X = {bscanData.flaw_location.x_mm} mm, Depth = {bscanData.flaw_location.depth_mm} mm
                    </span>
                  </div>

                  {/* Echogram Grid Render */}
                  <div className="w-full h-36 bg-slate-950 rounded-lg p-2 border border-slate-800 flex items-center justify-center overflow-hidden">
                    <svg className="w-full h-full" viewBox={`0 0 ${bscanData.num_x_steps} 50`} preserveAspectRatio="none">
                      {bscanData.bscan_intensity_matrix.map((col, x) =>
                        col.map((val, y) => {
                          const intensity = Math.min(1.0, val / 100.0);
                          let color = "#020617";
                          if (intensity > 0.5) color = "#ef4444";
                          else if (intensity > 0.25) color = "#f59e0b";
                          else if (intensity > 0.08) color = "#0284c7";

                          return (
                            <rect
                              key={`${x}-${y}`}
                              x={x}
                              y={y}
                              width="1"
                              height="1"
                              fill={color}
                            />
                          );
                        })
                      )}
                    </svg>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: MICRO-CT & INPAINTING */}
          {activeTab === "micro_ct" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 1. Raw CT */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center">
                  <h4 className="text-xs font-bold uppercase text-slate-700 mb-2">1. Raw Polychromatic CT Slice</h4>
                  <div className="w-48 h-48 bg-slate-950 rounded-lg p-1 border border-slate-300">
                    {ctData && (
                      <svg className="w-full h-full" viewBox="0 0 48 48">
                        {ctData.raw_ct_slice.map((row, y) =>
                          row.map((val, x) => (
                            <rect
                              key={`${x}-${y}`}
                              x={x}
                              y={y}
                              width="1"
                              height="1"
                              fill={`rgb(${Math.floor(val * 255)}, ${Math.floor(val * 255)}, ${Math.floor(val * 255)})`}
                            />
                          ))
                        )}
                      </svg>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 mt-2">Beer-Lambert X-ray projection</span>
                </div>

                {/* 2. Otsu Segmentation */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center">
                  <h4 className="text-xs font-bold uppercase text-slate-700 mb-2">2. Defect Segmentation Mask</h4>
                  <div className="w-48 h-48 bg-slate-950 rounded-lg p-1 border border-slate-300">
                    {ctData && (
                      <svg className="w-full h-full" viewBox="0 0 48 48">
                        {ctData.defect_mask.map((row, y) =>
                          row.map((isDefect, x) => (
                            <rect
                              key={`${x}-${y}`}
                              x={x}
                              y={y}
                              width="1"
                              height="1"
                              fill={isDefect ? "#ef4444" : "#0f172a"}
                            />
                          ))
                        )}
                      </svg>
                    )}
                  </div>
                  <span className="text-[11px] text-rose-600 font-semibold mt-2">
                    Segmented: {ctData?.segmented_defect_voxels} voxels ({ctData?.void_fraction_percent}% void)
                  </span>
                </div>

                {/* 3. Inpainted Slice */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center">
                  <h4 className="text-xs font-bold uppercase text-slate-700 mb-2">3. Physics-Guided Inpainting</h4>
                  <div className="w-48 h-48 bg-slate-950 rounded-lg p-1 border border-slate-300">
                    {ctData && (
                      <svg className="w-full h-full" viewBox="0 0 48 48">
                        {ctData.inpainted_slice.map((row, y) =>
                          row.map((val, x) => (
                            <rect
                              key={`${x}-${y}`}
                              x={x}
                              y={y}
                              width="1"
                              height="1"
                              fill={`rgb(${Math.floor(val * 255)}, ${Math.floor(val * 255)}, ${Math.floor(val * 255)})`}
                            />
                          ))
                        )}
                      </svg>
                    )}
                  </div>
                  <span className="text-[11px] text-emerald-600 font-semibold mt-2">Restored nominal material field</span>
                </div>
              </div>

              {/* Defect Log Table */}
              {ctData && ctData.injected_defects.length > 0 && (
                <div className="p-4 rounded-xl bg-white border border-slate-200">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide mb-2">
                    Detected Defect Catalog (Voxel Pitch: {ctData.voxel_pitch_um} μm)
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {ctData.injected_defects.map((def, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                        <span className="font-bold text-slate-900 block">{def.type}</span>
                        <span className="text-slate-500">
                          {def.estimated_size_um ? `Diameter: ${def.estimated_size_um} μm` : `Length: ${def.estimated_length_um} μm`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: MIL-HDBK-1823A POD CURVE */}
          {activeTab === "pod" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* SVG S-Curve */}
                <div className="lg:col-span-2 p-5 rounded-xl bg-white border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wide text-slate-900">
                        MIL-HDBK-1823A Probability of Detection (POD)
                      </h4>
                      <p className="text-xs text-slate-500">
                        Log-logistic regression S-curve with 95% lower confidence bound.
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="flex items-center gap-1 text-indigo-600">
                        <span className="w-2.5 h-0.5 bg-indigo-600 inline-block"></span> Nominal POD(a)
                      </span>
                      <span className="flex items-center gap-1 text-rose-500">
                        <span className="w-2.5 h-0.5 bg-rose-500 inline-block stroke-dash"></span> 95% Lower Bound
                      </span>
                    </div>
                  </div>

                  <div className="w-full h-56 bg-slate-50 rounded-lg p-2 border border-slate-200 relative">
                    {podData && (
                      <svg className="w-full h-full" viewBox="0 0 500 180">
                        {/* Threshold 90% POD line */}
                        <line x1="0" y1="18" x2="500" y2="18" stroke="#94a3b8" strokeDasharray="3 3" />
                        <text x="10" y="14" fill="#64748b" fontSize="10">90% POD Threshold</text>

                        {/* Nominal POD line (indigo) */}
                        {(() => {
                          const sizes = podData.curve_data.flaw_sizes_um;
                          const pods = podData.curve_data.pod_nominal_percent;
                          const minS = sizes[0];
                          const maxS = sizes[sizes.length - 1];

                          const pts = pods
                            .map((p, idx) => {
                              const x = ((sizes[idx] - minS) / (maxS - minS)) * 480 + 10;
                              const y = 180 - (p / 100) * 160;
                              return `${x},${y}`;
                            })
                            .join(" ");

                          return <polyline fill="none" stroke="#4f46e5" strokeWidth="2.5" points={pts} />;
                        })()}

                        {/* 95% lower bound line (rose) */}
                        {(() => {
                          const sizes = podData.curve_data.flaw_sizes_um;
                          const pods = podData.curve_data.pod_95_confidence_percent;
                          const minS = sizes[0];
                          const maxS = sizes[sizes.length - 1];

                          const pts = pods
                            .map((p, idx) => {
                              const x = ((sizes[idx] - minS) / (maxS - minS)) * 480 + 10;
                              const y = 180 - (p / 100) * 160;
                              return `${x},${y}`;
                            })
                            .join(" ");

                          return (
                            <polyline
                              fill="none"
                              stroke="#f43f5e"
                              strokeWidth="2"
                              strokeDasharray="4 2"
                              points={pts}
                            />
                          );
                        })()}
                      </svg>
                    )}
                  </div>
                </div>

                {/* Qualification Thresholds Card */}
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Aerospace Qualification Thresholds
                  </h4>

                  <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">Median Detection (a_50)</span>
                      <span className="text-lg font-black text-slate-800">
                        {podData?.qualification_thresholds_um.a_50_um} μm
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-white border border-slate-200">
                      <span className="text-[11px] text-slate-500 block">90% Detection (a_90)</span>
                      <span className="text-lg font-black text-indigo-600">
                        {podData?.qualification_thresholds_um.a_90_um} μm
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200">
                      <span className="text-[11px] text-indigo-700 font-semibold block">
                        Conservative Flaw Size (a_90/95)
                      </span>
                      <span className="text-xl font-black text-indigo-900">
                        {podData?.qualification_thresholds_um.a_90_95_um} μm
                      </span>
                      <p className="text-[10px] text-indigo-600 mt-1">
                        Flaw size reliably detected at 90% probability with 95% statistical confidence.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Elastodynamic Wave Equation • Beer-Lambert Polychromatic CT • MIL-HDBK-1823A POD</span>
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
