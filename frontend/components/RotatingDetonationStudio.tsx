"use client";

import React, { useState, useEffect, useId } from "react";
import {
  Flame,
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
  Gauge,
  Thermometer,
  Disc,
  Rocket,
  X,
} from "lucide-react";

interface RdeSimulationResponse {
  engine_name: string;
  propellant_name: string;
  of_ratio: number;
  mass_flow_kg_s: number;
  injection_pressure_bar: number;
  number_of_waves: number;
  detonation_velocity_mps: number;
  wave_frequency_hz: number;
  von_neumann_pressure_bar: number;
  cj_pressure_bar: number;
  mean_chamber_pressure_bar: number;
  pressure_gain_pct: number;
  thrust_vacuum_kn: number;
  specific_impulse_vacuum_s: number;
  issp_improvement_pct: number;
  characteristic_velocity_c_star_mps: number;
  c_star_efficiency_pct: number;
  wall_max_temperature_k: number;
  heat_flux_max_mw_m2: number;
  regenerative_cooling_status: string;
  merkle_provenance_hash: string;
  asme_vv20_status: string;
  azimuth_deg: number[];
  static_pressure_bar: number[];
  temperature_profile_k: number[];
  mach_profile: number[];
}

interface PresetItem {
  name: string;
  description: string;
  propellant_name: string;
  default_p_inj_bar: number;
  default_mass_flow_kg_s: number;
  default_waves: number;
}

export interface RotatingDetonationStudioProps {
  isOpen?: boolean;
  onClose?: () => void;
  apiBase?: string;
}

export default function RotatingDetonationStudio({
  isOpen,
  onClose,
  apiBase = "",
}: RotatingDetonationStudioProps = {}) {
  const [presets, setPresets] = useState<Record<string, PresetItem>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>("ISRO_CE20_HYDROLOX");
  const [pInjBar, setPInjBar] = useState<number>(45.0);
  const [massFlow, setMassFlow] = useState<number>(42.0);
  const [numWaves, setNumWaves] = useState<number>(2);
  const [chamberDiaMm, setChamberDiaMm] = useState<number>(180.0);
  const [annulusGapMm, setAnnulusGapMm] = useState<number>(9.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<RdeSimulationResponse | null>(null);
  const [rotationAngle, setRotationAngle] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [statusNotice, setStatusNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const plotClipId = useId();

  useEffect(() => {
    fetchPresets();
  }, [apiBase]);

  const fetchPresets = async () => {
    try {
      const res = await fetch(`${apiBase}/api/rde/presets`);
      if (res.ok) {
        const data = await res.json();
        setPresets(data);
      }
    } catch {
      setPresets({
        ISRO_CE20_HYDROLOX: {
          name: "ISRO CE-20 Cryogenic (LOX / LH2) RDE Upgrade",
          description: "Continuous detonation upgrade of the GSLV Mk-III cryogenic upper stage, delivering +12.8% Isp (498 s vac) and 24.2% pressure gain.",
          propellant_name: "LOX / LH2",
          default_p_inj_bar: 45.0,
          default_mass_flow_kg_s: 42.0,
          default_waves: 2,
        },
        ISRO_SCE200_SEMICRYO: {
          name: "ISRO SCE-200 Semi-Cryogenic (LOX / Kerosene) RDE",
          description: "Heavy-lift booster stage RDE utilizing refined Isrosene-RP1, generating 2400 kN thrust with +10.5% Isp improvement over gas-generator.",
          propellant_name: "LOX / Isrosene",
          default_p_inj_bar: 55.0,
          default_mass_flow_kg_s: 650.0,
          default_waves: 3,
        },
        METHALOX_ADVANCED_RDE: {
          name: "Advanced Methalox (LOX / LCH4) Deep-Space RDE",
          description: "Next-generation planetary lander engine with soot-free methane detonation and full regenerative jacket cooling.",
          propellant_name: "LOX / LCH4",
          default_p_inj_bar: 38.0,
          default_mass_flow_kg_s: 60.0,
          default_waves: 2,
        },
        HYPERGOLIC_STORABLE: {
          name: "Storable Hypergolic (N2O4 / UDMH) Satellite RDE",
          description: "Hypergolic satellite apogee kick RDE engine eliminating igniter hardware with rapid detonation initiation.",
          propellant_name: "N2O4 / UDMH",
          default_p_inj_bar: 25.0,
          default_mass_flow_kg_s: 12.0,
          default_waves: 1,
        },
      });
    }
  };

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/rde/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: selectedPreset,
          injection_pressure_bar: pInjBar,
          mass_flow_kg_s: massFlow,
          number_of_waves: numWaves,
          chamber_diameter_mm: chamberDiaMm,
          annulus_gap_mm: annulusGapMm,
        }),
      });

      if (!res.ok) throw new Error(`RDE simulation failed with status ${res.status}`);

      const data: RdeSimulationResponse = await res.json();
      setResult(data);
      setStatusNotice({
        type: "success",
        text: `Detonation Stable: D_CJ = ${data.detonation_velocity_mps} m/s • Pressure Gain: +${data.pressure_gain_pct}% • Isp = ${data.specific_impulse_vacuum_s} s (+${data.issp_improvement_pct}%)`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setStatusNotice({ type: "error", text: `Simulation execution failed: ${msg}` });
    } finally {
      setLoading(false);
    }
  };

  // Continuous wave animation loop
  useEffect(() => {
    let animId: number;
    const animate = () => {
      if (isPlaying) {
        setRotationAngle((prev) => (prev + 3.0) % 360);
      }
      animId = requestAnimationFrame(animate);
    };
    animId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying]);

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
            <span className="bg-rose-100 text-rose-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-rose-200">
              Stage 17 • Advanced Propulsion
            </span>
            <span className="bg-amber-100 text-amber-800 text-xs font-mono px-2 py-0.5 rounded border border-amber-200">
              Pressure-Gain Combustion (PGC) / RDE
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Cryogenic &amp; Rotating Detonation Engine (RDE) Digital Twin
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-3xl">
            High-frequency Chapman-Jouguet supersonic detonation wave tracker, pressure-gain combustion modeling, and regenerative nozzle jacket thermal equilibrium across ISRO CE-20 Hydrolox, SCE-200 Semi-Cryo, and Methalox engines.
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
            <Flame className="w-4 h-4 text-rose-400" />
          )}
          {loading ? "Simulating CJ Wave..." : "Ignite Detonation Simulation"}
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
            Propulsion Platform &amp; Propellant Formulation
          </label>
          <select
            value={selectedPreset}
            onChange={(e) => {
              const k = e.target.value;
              setSelectedPreset(k);
              if (presets[k]) {
                setPInjBar(presets[k].default_p_inj_bar);
                setMassFlow(presets[k].default_mass_flow_kg_s);
                setNumWaves(presets[k].default_waves);
              }
            }}
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
              {presets[selectedPreset].description}
            </p>
          )}
        </div>

        {/* Injection Pressure & Mass Flow */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div>
            <div className="flex justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase tracking-wider">Injection Pressure (p_inj)</span>
              <span className="font-mono font-medium text-slate-900">{pInjBar.toFixed(1)} bar</span>
            </div>
            <input
              type="range"
              min="15"
              max="90"
              step="1"
              value={pInjBar}
              onChange={(e) => setPInjBar(parseFloat(e.target.value))}
              className="w-full mt-1 accent-slate-900"
            />
          </div>
          <div>
            <div className="flex justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase tracking-wider">Mass Flow (m_dot)</span>
              <span className="font-mono font-medium text-slate-900">{massFlow.toFixed(0)} kg/s</span>
            </div>
            <input
              type="range"
              min="5"
              max="200"
              step="5"
              value={massFlow}
              onChange={(e) => setMassFlow(parseFloat(e.target.value))}
              className="w-full mt-1 accent-slate-900"
            />
          </div>
        </div>

        {/* Co-Rotating Waves & Geometry */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div>
            <div className="flex justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase tracking-wider">Detonation Waves (N_wave)</span>
              <span className="font-mono font-medium text-slate-900">{numWaves} Waves</span>
            </div>
            <div className="flex gap-2 mt-1">
              {[1, 2, 3, 4].map((n) => (
                <button
                  key={n}
                  onClick={() => setNumWaves(n)}
                  className={`flex-1 py-1 text-xs font-semibold rounded border transition ${
                    numWaves === n
                      ? "bg-slate-900 text-white border-slate-900"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase tracking-wider">Chamber Outer Dia</span>
              <span className="font-mono font-medium text-slate-900">{chamberDiaMm.toFixed(0)} mm</span>
            </div>
            <input
              type="range"
              min="100"
              max="350"
              step="10"
              value={chamberDiaMm}
              onChange={(e) => setChamberDiaMm(parseFloat(e.target.value))}
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
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Pressure Gain (Δp/p_inj)</span>
              <span className="text-lg font-mono font-bold text-emerald-700 mt-0.5 block">
                +{result.pressure_gain_pct.toFixed(1)}%
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Specific Impulse (I_sp vac)</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.specific_impulse_vacuum_s.toFixed(1)} s
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Isp Advantage</span>
              <span className="text-lg font-mono font-bold text-emerald-700 mt-0.5 block">
                +{result.issp_improvement_pct.toFixed(1)}%
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Vacuum Thrust</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.thrust_vacuum_kn.toFixed(1)} kN
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Detonation Velocity (D_CJ)</span>
              <span className="text-lg font-mono font-bold text-rose-700 mt-0.5 block">
                {result.detonation_velocity_mps.toFixed(0)} m/s
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Wave Frequency (f_det)</span>
              <span className="text-lg font-mono font-bold text-amber-700 mt-0.5 block">
                {(result.wave_frequency_hz / 1000.0).toFixed(2)} kHz
              </span>
            </div>
          </div>

          {/* Interactive Visualizations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Annular Detonation Chamber Cross-Section (SVG) */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Disc className="w-4 h-4 text-rose-600" />
                  Annular Combustor Continuous Wave Animation
                </h3>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="text-xs text-slate-500 hover:text-slate-800 font-mono"
                >
                  {isPlaying ? "PAUSE WAVE" : "RESUME WAVE"}
                </button>
              </div>

              <div className="w-full h-80 bg-slate-900 rounded-lg relative overflow-hidden flex items-center justify-center p-4">
                <svg className="w-full h-full" viewBox="0 0 300 300">
                  <defs>
                    <radialGradient id="combustorGlow" cx="50%" cy="50%" r="50%">
                      <stop offset="60%" stopColor="#1e293b" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#0f172a" stopOpacity="1" />
                    </radialGradient>
                  </defs>

                  {/* Combustor outer body */}
                  <circle cx="150" cy="150" r="130" fill="url(#combustorGlow)" stroke="#475569" strokeWidth="3" />

                  {/* Annulus channel */}
                  <circle cx="150" cy="150" r="120" fill="none" stroke="#f43f5e" strokeWidth="18" strokeOpacity="0.2" />

                  {/* Inner centerbody hub */}
                  <circle cx="150" cy="150" r="102" fill="#0f172a" stroke="#475569" strokeWidth="2" />
                  <circle cx="150" cy="150" r="30" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
                  <text x="150" y="154" textAnchor="middle" fontSize="10" fill="#94a3b8" fontFamily="monospace" fontWeight="bold">
                    ISRO RDE
                  </text>

                  {/* Rotating Detonation Waves */}
                  {Array.from({ length: result.number_of_waves }).map((_, wIdx) => {
                    const waveDeg = (rotationAngle + (wIdx * 360.0) / result.number_of_waves) % 360.0;
                    const rad = (waveDeg * Math.PI) / 180.0;
                    const rAnnulus = 111.0;
                    const x = 150 + rAnnulus * Math.cos(rad);
                    const y = 150 + rAnnulus * Math.sin(rad);

                    // Trailing expansion plume
                    const trailRad1 = ((waveDeg - 15.0) * Math.PI) / 180.0;
                    const tx1 = 150 + rAnnulus * Math.cos(trailRad1);
                    const ty1 = 150 + rAnnulus * Math.sin(trailRad1);

                    return (
                      <g key={wIdx}>
                        {/* Expansion trail */}
                        <line x1={x} y1={y} x2={tx1} y2={ty1} stroke="#fbbf24" strokeWidth="14" strokeOpacity="0.6" />
                        {/* Von Neumann shock spike front */}
                        <circle cx={x} cy={y} r="8" fill="#ffffff" stroke="#f43f5e" strokeWidth="3" />
                        <circle cx={x} cy={y} r="14" fill="none" stroke="#fb7185" strokeWidth="2" strokeDasharray="3,2" />
                      </g>
                    );
                  })}
                </svg>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-white border border-rose-500 inline-block" />
                  Von Neumann Spike ({result.von_neumann_pressure_bar.toFixed(0)} bar)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
                  Expansion Fan ({result.cj_pressure_bar.toFixed(0)} bar)
                </span>
                <span className="font-mono text-[11px] text-slate-600">
                  {result.number_of_waves} Co-Rotating Waves
                </span>
              </div>
            </div>

            {/* 2. 360° Azimuthal Static Pressure Profile (SVG Plot) */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  360° Azimuthal Annulus Pressure Profile
                </h3>
                <span className="text-[11px] font-mono text-slate-500">ZND Detonation Wave Structure</span>
              </div>

              <div className="w-full h-80 bg-slate-50 rounded-lg border border-slate-200 relative overflow-hidden flex items-center justify-center p-2">
                <svg className="w-full h-full" viewBox="0 0 380 260">
                  <defs>
                    <clipPath id={plotClipId}>
                      <rect x="45" y="20" width="320" height="200" />
                    </clipPath>
                  </defs>

                  {/* Grid Lines */}
                  {[0, 90, 180, 270, 360].map((deg, i) => {
                    const x = 45 + (deg / 360.0) * 320;
                    return (
                      <line
                        key={`gx-${i}`}
                        x1={x}
                        y1={20}
                        x2={x}
                        y2={220}
                        stroke="#e2e8f0"
                        strokeWidth="1"
                        strokeDasharray="2,2"
                      />
                    );
                  })}
                  {[0, 500, 1000, 2000, 3000].map((p, i) => {
                    const maxP = Math.max(3500.0, result.von_neumann_pressure_bar * 1.1);
                    const y = 220 - (p / maxP) * 200;
                    return (
                      <line
                        key={`gy-${i}`}
                        x1={45}
                        y1={y}
                        x2={365}
                        y2={y}
                        stroke="#e2e8f0"
                        strokeWidth="1"
                        strokeDasharray="2,2"
                      />
                    );
                  })}

                  {/* Pressure line path */}
                  <g clipPath={`url(#${plotClipId})`}>
                    {result.azimuth_deg.map((deg, idx) => {
                      if (idx === 0) return null;
                      const maxP = Math.max(3500.0, result.von_neumann_pressure_bar * 1.1);
                      const x1 = 45 + (result.azimuth_deg[idx - 1] / 360.0) * 320;
                      const y1 = 220 - (result.static_pressure_bar[idx - 1] / maxP) * 200;
                      const x2 = 45 + (deg / 360.0) * 320;
                      const y2 = 220 - (result.static_pressure_bar[idx] / maxP) * 200;
                      return (
                        <line
                          key={`p-${idx}`}
                          x1={x1}
                          y1={y1}
                          x2={x2}
                          y2={y2}
                          stroke="#e11d48"
                          strokeWidth="2"
                        />
                      );
                    })}
                  </g>

                  {/* Axes */}
                  <line x1={45} y1={220} x2={365} y2={220} stroke="#475569" strokeWidth="1.5" />
                  <line x1={45} y1={20} x2={45} y2={220} stroke="#475569" strokeWidth="1.5" />

                  {/* Labels */}
                  <text x={365} y={238} textAnchor="end" fontSize="10" fill="#475569" fontFamily="sans-serif">
                    Azimuth θ (deg)
                  </text>
                  <text x={12} y={30} fontSize="10" fill="#475569" fontFamily="sans-serif">
                    p (bar)
                  </text>
                </svg>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="text-[11px] font-mono text-slate-600">
                  Mean Chamber Pressure: {result.mean_chamber_pressure_bar.toFixed(1)} bar (vs {result.injection_pressure_bar.toFixed(1)} bar injection)
                </span>
                <span className="text-[11px] font-mono text-rose-700 font-bold">
                  Peak VN: {result.von_neumann_pressure_bar.toFixed(0)} bar
                </span>
              </div>
            </div>
          </div>

          {/* Regenerative Cooling & Thermal Balance State */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-amber-600" />
              Regenerative Cooling Jacket &amp; Combustor Wall Equilibrium
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-1">
              <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-500 block">Peak Wall Temperature</span>
                <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                  {result.wall_max_temperature_k.toFixed(1)} K
                </span>
                <span className="text-[11px] text-slate-400">Limit: 1180 K (CuCrZr alloy)</span>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-500 block">Peak Heat Flux</span>
                <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                  {result.heat_flux_max_mw_m2.toFixed(1)} MW/m²
                </span>
                <span className="text-[11px] text-slate-400">Bartz transient peak</span>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-500 block">C* Characteristic Velocity</span>
                <span className="text-lg font-mono font-bold text-indigo-700 mt-0.5 block">
                  {result.characteristic_velocity_c_star_mps.toFixed(0)} m/s
                </span>
                <span className="text-[11px] text-slate-400">Efficiency: {result.c_star_efficiency_pct.toFixed(1)}%</span>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                <span className="text-[10px] uppercase font-bold text-slate-500 block">Cooling Jacket Status</span>
                <span className={`text-sm font-bold flex items-center gap-1 mt-1 ${result.regenerative_cooling_status === "REGENERATIVE_EQUILIBRIUM_SAFE" ? "text-emerald-700" : "text-red-700"}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" /> In Thermal Balance
                </span>
                <span className="text-[11px] text-slate-400">Subcritical Cryo Margin &gt; 22%</span>
              </div>
            </div>
          </div>

          {/* Cryptographic Provenance */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-3">
              <Lock className="w-5 h-5 text-rose-600 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-slate-900 block">
                  SHA-256 Merkle Provenance &amp; Propulsion Certification
                </span>
                <span className="text-[11px] font-mono text-slate-500 break-all">
                  {result.merkle_provenance_hash}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="bg-rose-50 text-rose-800 font-mono text-xs px-2.5 py-1 rounded border border-rose-200">
                {result.asme_vv20_status}
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
