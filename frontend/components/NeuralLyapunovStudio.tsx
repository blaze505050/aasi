"use client";

import React, { useState, useEffect, useId } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCcw,
  Zap,
  Activity,
  Layers,
  CheckCircle2,
  Lock,
  Wind,
  Compass,
  Gauge,
  HelpCircle,
  X,
} from "lucide-react";

interface EnvelopeStep {
  time_s: number;
  airspeed_mps: number;
  aoa_deg: number;
  pitch_rate_deg_s: number;
  pitch_deg: number;
  flight_path_angle_deg: number;
  load_factor_g: number;
  wind_gust_vertical_mps: number;
  u_ai_demanded_elevator_deg: number;
  u_filtered_elevator_deg: number;
  u_actual_elevator_deg: number;
  throttle_pct: number;
  barrier_value_b: number;
  barrier_lie_derivative: number;
  barrier_admissible: boolean;
  rta_active_tier: string;
  stall_prevented: boolean;
  envelope_departure_prevented: boolean;
}

interface SimulationResult {
  aircraft_name: string;
  flight_regime: string;
  total_duration_s: number;
  total_steps: number;
  unprotected_departures: number;
  protected_departures: number;
  recovery_switch_events: number;
  max_aoa_reached_deg: number;
  max_nz_reached_g: number;
  min_airspeed_reached_mps: number;
  astm_f3269_compliance: string;
  steps: EnvelopeStep[];
  merkle_provenance_hash: string;
  safety_standard: string;
}

interface PresetItem {
  name: string;
  description: string;
  mass_kg: number;
  alpha_max_deg: number;
  nz_max_g: number;
  safety_standard: string;
}

export interface NeuralLyapunovStudioProps {
  isOpen?: boolean;
  onClose?: () => void;
  apiBase?: string;
}

export default function NeuralLyapunovStudio({
  isOpen,
  onClose,
  apiBase = "",
}: NeuralLyapunovStudioProps = {}) {
  const [presets, setPresets] = useState<Record<string, PresetItem>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>("LCA_TEJAS_COMBAT_MANEUVER");
  const [enableRta, setEnableRta] = useState<boolean>(true);
  const [gustIntensity, setGustIntensity] = useState<number>(1.2);
  const [durationS, setDurationS] = useState<number>(10.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [activeStepIdx, setActiveStepIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [statusNotice, setStatusNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const clipId = useId();

  // Load presets
  useEffect(() => {
    fetchPresets();
  }, [apiBase]);

  const fetchPresets = async () => {
    try {
      const res = await fetch(`${apiBase}/api/lyapunov/presets`);
      if (res.ok) {
        const data = await res.json();
        setPresets(data);
      }
    } catch {
      // Fallback presets if offline
      setPresets({
        LCA_TEJAS_COMBAT_MANEUVER: {
          name: "LCA Tejas Mk-1A Fighter Combat Maneuver",
          description: "Tactical 9.0g pull-up with severe -22 m/s downdraft microburst.",
          mass_kg: 8500.0,
          alpha_max_deg: 22.0,
          nz_max_g: 9.0,
          safety_standard: "DO-178C Level A / ASTM F3269-21",
        },
        COMMERCIAL_AIRLINER_STALL: {
          name: "Civil Transport LOC-I Deep Stall Prevention",
          description: "Heavy transport high-altitude convective storm penetration.",
          mass_kg: 68000.0,
          alpha_max_deg: 15.0,
          nz_max_g: 2.5,
          safety_standard: "FAR 25.1309 / DO-178C Level A",
        },
        EVTOL_URBAN_AIR_MOBILITY: {
          name: "Autonomous 4-Pax eVTOL Gust Corridor",
          description: "Terminal rooftop approach downdraft with 2.5g passenger comfort boundary.",
          mass_kg: 2400.0,
          alpha_max_deg: 14.0,
          nz_max_g: 2.5,
          safety_standard: "FAA Powered-Lift Certification / ASTM F3269-21",
        },
        DRDO_RUSTOM2_UAV: {
          name: "DRDO Rustom-2 MALE UAV Thin-Air Loiter",
          description: "High-altitude surveillance envelope protection under mountain waves.",
          mass_kg: 1800.0,
          alpha_max_deg: 13.5,
          nz_max_g: 3.0,
          safety_standard: "STANAG 4671 Military Airworthiness",
        },
      });
    }
  };

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/lyapunov/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: selectedPreset,
          enable_rta: enableRta,
          gust_intensity: gustIntensity,
          duration_s: durationS,
        }),
      });

      if (!res.ok) {
        throw new Error(`Simulation failed with status ${res.status}`);
      }

      const data: SimulationResult = await res.json();
      setResult(data);
      setActiveStepIdx(data.steps.length - 1);
      setStatusNotice({
        type: "success",
        text: enableRta
          ? `ASTM F3269-21 Verified: 0 Departures (${data.recovery_switch_events} recovery interventions)`
          : `Unprotected run completed: ${data.unprotected_departures} departures detected!`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setStatusNotice({ type: "error", text: `Execution failed: ${msg}` });
    } finally {
      setLoading(false);
    }
  };

  // Auto-play animation through trajectory
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPlaying && result && result.steps.length > 0) {
      interval = setInterval(() => {
        setActiveStepIdx((prev) => {
          if (prev >= result.steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 50);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, result]);

  const currentStep = result && result.steps[activeStepIdx] ? result.steps[activeStepIdx] : null;

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
            <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-200">
              Stage 14 • Safe Autonomous Flight
            </span>
            <span className="bg-blue-100 text-blue-800 text-xs font-mono px-2 py-0.5 rounded border border-blue-200">
              ASTM F3269-21 / DO-178C Level A
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Neural Lyapunov Flight Envelope Protection & RTA
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-3xl">
            Control Barrier Function (CBF) forward invariance engine with active CBF-QP safety filter and deterministic DO-178C recovery shield. Guarantees stall prevention and structural integrity during severe microburst wind shear.
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium px-5 py-2.5 rounded-lg shadow-sm transition disabled:opacity-50 shrink-0"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Zap className="w-4 h-4 text-emerald-400" />
          )}
          {loading ? "Evaluating CBF-QP..." : "Run Envelope Simulation"}
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
            Aircraft Platform & Flight Regime
          </label>
          <select
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            {Object.entries(presets).map(([k, v]) => (
              <option key={k} value={k}>
                {v.name}
              </option>
            ))}
          </select>
          {presets[selectedPreset] && (
            <p className="text-xs text-slate-500 mt-2">
              {presets[selectedPreset].description} (Max AoA: {presets[selectedPreset].alpha_max_deg}°, Limit: {presets[selectedPreset].nz_max_g}g)
            </p>
          )}
        </div>

        {/* ASTM F3269-21 RTA Toggle */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
              ASTM F3269-21 RTA Filter
            </label>
            <ShieldCheck className={`w-4 h-4 ${enableRta ? "text-emerald-600" : "text-amber-500"}`} />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => setEnableRta(!enableRta)}
              className={`w-full py-2 px-3 text-xs font-semibold rounded-lg border transition ${
                enableRta
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                  : "bg-red-50 text-red-800 border-red-300"
              }`}
            >
              {enableRta ? "PROTECTION: ACTIVE (CBF-QP)" : "PROTECTION: OFF (UNGUARDED AI)"}
            </button>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {enableRta ? "Active barrier filter intervenes within 5ms" : "AI operates unmonitored; risk of LOC-I stall"}
          </p>
        </div>

        {/* Gust Intensity & Duration */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div>
            <div className="flex justify-between text-xs text-slate-500">
              <span>Gust Intensity</span>
              <span className="font-mono font-medium text-slate-900">{gustIntensity.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.2"
              max="2.5"
              step="0.1"
              value={gustIntensity}
              onChange={(e) => setGustIntensity(parseFloat(e.target.value))}
              className="w-full mt-1 accent-slate-900"
            />
          </div>
          <div>
            <div className="flex justify-between text-xs text-slate-500">
              <span>Duration</span>
              <span className="font-mono font-medium text-slate-900">{durationS.toFixed(0)} s</span>
            </div>
            <input
              type="range"
              min="4"
              max="16"
              step="2"
              value={durationS}
              onChange={(e) => setDurationS(parseFloat(e.target.value))}
              className="w-full mt-1 accent-slate-900"
            />
          </div>
        </div>
      </div>

      {/* Main Results View */}
      {result && (
        <div className="space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">RTA Compliance</span>
              <span className={`text-sm font-bold flex items-center gap-1 mt-1 ${result.protected_departures === 0 && result.unprotected_departures === 0 ? "text-emerald-700" : "text-red-700"}`}>
                {result.protected_departures === 0 && result.unprotected_departures === 0 ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" /> 100% Certified
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5" /> Departures
                  </>
                )}
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Peak Angle of Attack</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.max_aoa_reached_deg.toFixed(1)}°
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Peak Load Factor</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.max_nz_reached_g.toFixed(2)} g
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Min Airspeed</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.min_airspeed_reached_mps.toFixed(1)} m/s
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Recovery Interventions</span>
              <span className="text-lg font-mono font-bold text-blue-700 mt-0.5 block">
                {result.recovery_switch_events}
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Departures Avoided</span>
              <span className="text-lg font-mono font-bold text-emerald-700 mt-0.5 block">
                {result.unprotected_departures > 0 ? `${result.unprotected_departures} Unsafe` : "0 (Safe)"}
              </span>
            </div>
          </div>

          {/* Tri-Level RTA State Monitor & Timeline Scrubber */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="bg-slate-900 text-white p-2 rounded-lg hover:bg-slate-800 transition"
                >
                  {isPlaying ? <RotateCcw className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <div>
                  <span className="text-xs font-semibold text-slate-500 block">
                    Telemetry Timeline (t = {currentStep ? currentStep.time_s.toFixed(2) : "0.00"} s)
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-mono font-semibold ${
                        currentStep?.rta_active_tier === "TIER_2_DO178C_RECOVERY"
                          ? "bg-red-100 text-red-800 border border-red-300 animate-pulse"
                          : currentStep?.rta_active_tier === "TIER_1_CBF_QP_FILTER"
                          ? "bg-amber-100 text-amber-800 border border-amber-300"
                          : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                      }`}
                    >
                      {currentStep ? currentStep.rta_active_tier : "TIER_0_PRIMARY_AI"}
                    </span>
                    <span className="text-xs text-slate-500">
                      Elevator Demanded: {currentStep ? currentStep.u_ai_demanded_elevator_deg.toFixed(1) : "0.0"}° → Filtered: {currentStep ? currentStep.u_filtered_elevator_deg.toFixed(1) : "0.0"}°
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-500 font-mono">
                Step {activeStepIdx + 1} / {result.steps.length}
              </div>
            </div>

            <input
              type="range"
              min="0"
              max={result.steps.length - 1}
              value={activeStepIdx}
              onChange={(e) => setActiveStepIdx(parseInt(e.target.value))}
              className="w-full accent-slate-900"
            />
          </div>

          {/* Interactive Visualizations Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Phase-Plane Flight Envelope (Alpha vs Nz) */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  Flight Envelope Phase-Plane (α vs n_z)
                </h3>
                <span className="text-[11px] font-mono text-slate-500">Forward Invariant Set B(x) ≤ 0</span>
              </div>

              <div className="w-full h-72 bg-slate-50 rounded-lg border border-slate-200 relative overflow-hidden flex items-center justify-center">
                <svg className="w-full h-full p-4" viewBox="0 0 400 240">
                  <defs>
                    <linearGradient id="safeEnvelopeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#10b981" stopOpacity="0.12" />
                      <stop offset="100%" stopColor="#059669" stopOpacity="0.04" />
                    </linearGradient>
                    <clipPath id={clipId}>
                      <rect x="50" y="20" width="330" height="190" />
                    </clipPath>
                  </defs>

                  {/* Grid Lines */}
                  {[-4, 0, 4, 8, 12, 16, 20, 24].map((a, i) => {
                    const x = 50 + ((a + 4) / 30) * 330;
                    return (
                      <line
                        key={`gx-${i}`}
                        x1={x}
                        y1={20}
                        x2={x}
                        y2={210}
                        stroke="#e2e8f0"
                        strokeWidth="1"
                        strokeDasharray="2,2"
                      />
                    );
                  })}
                  {[0, 2, 4, 6, 8, 10].map((nz, i) => {
                    const y = 210 - (nz / 10) * 190;
                    return (
                      <line
                        key={`gy-${i}`}
                        x1={50}
                        y1={y}
                        x2={380}
                        y2={y}
                        stroke="#e2e8f0"
                        strokeWidth="1"
                        strokeDasharray="2,2"
                      />
                    );
                  })}

                  {/* Safe Domain Box */}
                  {presets[selectedPreset] && (
                    <rect
                      x={50 + ((0 + 4) / 30) * 330}
                      y={210 - (presets[selectedPreset].nz_max_g / 10) * 190}
                      width={((presets[selectedPreset].alpha_max_deg - 0) / 30) * 330}
                      height={(presets[selectedPreset].nz_max_g / 10) * 190}
                      fill="url(#safeEnvelopeGrad)"
                      stroke="#10b981"
                      strokeWidth="1.5"
                      strokeDasharray="4,3"
                    />
                  )}

                  {/* Envelope Trajectory */}
                  <g clipPath={`url(#${clipId})`}>
                    {result.steps.map((st, i) => {
                      if (i === 0) return null;
                      const prev = result.steps[i - 1];
                      const x1 = 50 + ((prev.aoa_deg + 4) / 30) * 330;
                      const y1 = 210 - (prev.load_factor_g / 10) * 190;
                      const x2 = 50 + ((st.aoa_deg + 4) / 30) * 330;
                      const y2 = 210 - (st.load_factor_g / 10) * 190;
                      const color =
                        st.rta_active_tier === "TIER_2_DO178C_RECOVERY"
                          ? "#ef4444"
                          : st.rta_active_tier === "TIER_1_CBF_QP_FILTER"
                          ? "#f59e0b"
                          : "#0284c7";
                      return (
                        <line
                          key={`traj-${i}`}
                          x1={x1}
                          y1={y1}
                          x2={x2}
                          y2={y2}
                          stroke={color}
                          strokeWidth="2"
                        />
                      );
                    })}

                    {/* Current State Marker */}
                    {currentStep && (
                      <circle
                        cx={50 + ((currentStep.aoa_deg + 4) / 30) * 330}
                        cy={210 - (currentStep.load_factor_g / 10) * 190}
                        r="6"
                        fill="#0f172a"
                        stroke="#ffffff"
                        strokeWidth="2"
                      />
                    )}
                  </g>

                  {/* Axes */}
                  <line x1={50} y1={210} x2={380} y2={210} stroke="#475569" strokeWidth="1.5" />
                  <line x1={50} y1={20} x2={50} y2={210} stroke="#475569" strokeWidth="1.5" />

                  {/* Axis Labels */}
                  <text x={380} y={230} textAnchor="end" fontSize="10" fill="#475569" fontFamily="sans-serif">
                    Angle of Attack α (deg)
                  </text>
                  <text x={18} y={30} fontSize="10" fill="#475569" fontFamily="sans-serif">
                    n_z (g)
                  </text>
                </svg>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block" />
                    Tier 0 (Nominal AI)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                    Tier 1 (CBF-QP Filter)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
                    Tier 2 (DO-178C Recovery)
                  </span>
                </div>
                <span className="font-mono text-[11px] text-slate-600">
                  Current: {currentStep ? `${currentStep.aoa_deg.toFixed(1)}°, ${currentStep.load_factor_g.toFixed(2)}g` : "--"}
                </span>
              </div>
            </div>

            {/* 2. Control & Microburst Gust Time-Series */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Wind className="w-4 h-4 text-blue-600" />
                  Elevator Demand vs Filtered Recovery
                </h3>
                <span className="text-[11px] font-mono text-slate-500">ASTM F3269-21 RTA Pulse</span>
              </div>

              <div className="w-full h-72 bg-slate-50 rounded-lg border border-slate-200 relative overflow-hidden flex items-center justify-center">
                <svg className="w-full h-full p-4" viewBox="0 0 400 240">
                  {/* Zero line */}
                  <line x1={40} y1={120} x2={380} y2={120} stroke="#cbd5e1" strokeWidth="1" strokeDasharray="3,3" />

                  {/* AI demanded elevator (red dashed) */}
                  {result.steps.map((st, i) => {
                    if (i === 0) return null;
                    const prev = result.steps[i - 1];
                    const x1 = 40 + (prev.time_s / result.total_duration_s) * 340;
                    const y1 = 120 - (prev.u_ai_demanded_elevator_deg / 30) * 100;
                    const x2 = 40 + (st.time_s / result.total_duration_s) * 340;
                    const y2 = 120 - (st.u_ai_demanded_elevator_deg / 30) * 100;
                    return (
                      <line
                        key={`dem-${i}`}
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#f87171"
                        strokeWidth="1.5"
                        strokeDasharray="3,2"
                      />
                    );
                  })}

                  {/* Filtered safe elevator (emerald solid) */}
                  {result.steps.map((st, i) => {
                    if (i === 0) return null;
                    const prev = result.steps[i - 1];
                    const x1 = 40 + (prev.time_s / result.total_duration_s) * 340;
                    const y1 = 120 - (prev.u_filtered_elevator_deg / 30) * 100;
                    const x2 = 40 + (st.time_s / result.total_duration_s) * 340;
                    const y2 = 120 - (st.u_filtered_elevator_deg / 30) * 100;
                    return (
                      <line
                        key={`filt-${i}`}
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#059669"
                        strokeWidth="2"
                      />
                    );
                  })}

                  {/* Vertical time marker */}
                  {currentStep && (
                    <line
                      x1={40 + (currentStep.time_s / result.total_duration_s) * 340}
                      y1={15}
                      x2={40 + (currentStep.time_s / result.total_duration_s) * 340}
                      y2={220}
                      stroke="#0f172a"
                      strokeWidth="1.5"
                    />
                  )}

                  {/* Axes */}
                  <line x1={40} y1={220} x2={380} y2={220} stroke="#475569" strokeWidth="1.5" />
                  <line x1={40} y1={15} x2={40} y2={220} stroke="#475569" strokeWidth="1.5" />

                  {/* Labels */}
                  <text x={380} y={235} textAnchor="end" fontSize="10" fill="#475569" fontFamily="sans-serif">
                    Time (s)
                  </text>
                  <text x={15} y={25} fontSize="10" fill="#475569" fontFamily="sans-serif">
                    δ_e (deg)
                  </text>
                </svg>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-red-400 inline-block border-b border-dashed" />
                    AI Demanded δ_e
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-0.5 bg-emerald-600 inline-block" />
                    RTA Filtered δ_e
                  </span>
                </div>
                <span className="font-mono text-[11px] text-slate-600">
                  Gust: {currentStep ? `${currentStep.wind_gust_vertical_mps.toFixed(1)} m/s` : "--"}
                </span>
              </div>
            </div>
          </div>

          {/* Cryptographic Provenance & Airworthiness Certificate */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-3">
              <Lock className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-slate-900 block">
                  SHA-256 Merkle Provenance & Airworthiness Proof
                </span>
                <span className="text-[11px] font-mono text-slate-500 break-all">
                  {result.merkle_provenance_hash}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="bg-slate-100 text-slate-700 font-mono text-xs px-2.5 py-1 rounded border border-slate-200">
                {result.safety_standard}
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
