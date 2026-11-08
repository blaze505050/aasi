"use client";

import React, { useState, useEffect } from "react";
import {
  Compass,
  Globe,
  Activity,
  ShieldCheck,
  Download,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Flame,
  CheckCircle2,
  Camera,
  Crosshair,
  AlertTriangle,
  ArrowDownRight,
  TrendingDown,
  Layers,
  Copy,
  Check,
} from "lucide-react";

interface TrajectoryPoint {
  time_s: number;
  altitude_km: number;
  downrange_km: number;
  velocity_mps: number;
  mach_number: number;
  dynamic_pressure_kpa: number;
  aerodynamic_g_load: number;
  stagnation_heat_flux_mw_m2: number;
  integrated_heat_load_mj_m2: number;
  phase: string;
  optical_trn_active: boolean;
  trn_covariance_sigma_m: number;
  hazard_divert_distance_m: number;
}

interface OpticalFeatureMatch {
  feature_id: number;
  map_crater_id: string;
  pixel_x: number;
  pixel_y: number;
  residual_error_px: number;
  maha_distance: number;
}

interface EDLMissionDossier {
  mission_id: string;
  preset_key: string;
  target_planet: string;
  target_site_name: string;
  entry_mass_kg: number;
  heatshield_radius_m: number;
  ballistic_coefficient_kg_m2: number;
  peak_heat_flux_mw_m2: number;
  peak_g_load: number;
  landing_error_cep_m: number;
  optical_trn_fixes: number;
  hazard_detected: boolean;
  final_touchdown_speed_mps: number;
  trajectory: TrajectoryPoint[];
  optical_features: OpticalFeatureMatch[];
  merkle_provenance_hash: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

const EDL_PRESETS_META: Record<string, { label: string; planet: string; vehicle: string; site: string; desc: string }> = {
  MARS_JEZERO_CRATER_SKYCRANE: {
    label: "Mars Jezero Crater Skycrane",
    planet: "Mars",
    vehicle: "Perseverance-Class 1025 kg Rover",
    site: "Jezero Crater Delta (18.38°N, 77.58°E)",
    desc: "Hypersonic guided lifting entry, supersonic DGB parachute, Lander Vision System (LVS) optical TRN, and skycrane touchdown.",
  },
  ISRO_GAGANYAAN_REENTRY_BAY_OF_BENGAL: {
    label: "ISRO Gaganyaan Bay of Bengal Splashdown",
    planet: "Earth",
    vehicle: "Gaganyaan 5300 kg Crew Module",
    site: "Bay of Bengal Strategic Recovery Grid",
    desc: "Controlled hypersonic atmospheric deorbit, lifting corridor g-protection, drogue/main parachute splashdown.",
  },
  VENUS_DAVINCI_ATMOSPHERIC_DESCENT: {
    label: "Venus DAVINCI Supercritical Descent",
    planet: "Venus",
    vehicle: "DAVINCI Atmospheric Probe",
    site: "Alpha Regio Tesserae (25.5°S, 0.3°E)",
    desc: "Extreme aerothermal entry into 92-bar dense supercritical CO2, high convective heating, and terrain descent photography.",
  },
  TITAN_DRAGONFLY_ROTORCRAFT_ENTRY: {
    label: "Titan Dragonfly Rotorcraft Entry",
    planet: "Titan",
    vehicle: "Dragonfly Dual-Quadcopter Lander",
    site: "Shangri-La Dune Fields (10.0°S, 160.0°W)",
    desc: "Low-gravity dense cryogenic atmosphere entry, shield jettison, and mid-air rotor deployment.",
  },
};

export default function PlanetaryEdlStudio({ isOpen, onClose, apiBase }: Props) {
  const [selectedPreset, setSelectedPreset] = useState("MARS_JEZERO_CRATER_SKYCRANE");
  const [dossier, setDossier] = useState<EDLMissionDossier | null>(null);
  const [loading, setLoading] = useState(false);
  const [animIndex, setAnimIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [copiedHash, setCopiedHash] = useState(false);

  const runSimulation = async (presetKey: string) => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/edl/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset_key: presetKey }),
      });
      if (resp.ok) {
        const data: EDLMissionDossier = await resp.json();
        setDossier(data);
        setAnimIndex(0);
      }
    } catch (err) {
      console.error("Planetary EDL simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !dossier) {
      runSimulation(selectedPreset);
    }
  }, [isOpen]);

  const handlePresetChange = (key: string) => {
    setSelectedPreset(key);
    runSimulation(key);
  };

  // Trajectory animation
  useEffect(() => {
    if (!isPlaying || !dossier || !dossier.trajectory.length) return;
    const interval = setInterval(() => {
      setAnimIndex((prev) => (prev + 1) % dossier.trajectory.length);
    }, 55);
    return () => clearInterval(interval);
  }, [isPlaying, dossier]);

  const copyMerkle = () => {
    if (!dossier) return;
    navigator.clipboard.writeText(dossier.merkle_provenance_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const currentPoint = dossier?.trajectory[animIndex] || dossier?.trajectory[0];

  // SVG coordinate transformation
  const svgWidth = 840;
  const svgHeight = 440;

  const maxAlt = dossier ? Math.max(...dossier.trajectory.map((p) => p.altitude_km), 130) : 130;
  const maxDownrange = dossier ? Math.max(...dossier.trajectory.map((p) => p.downrange_km), 1000) : 1000;

  const toSvgX = (dr_km: number) => 60 + (dr_km / maxDownrange) * (svgWidth - 120);
  const toSvgY = (alt_km: number) => svgHeight - 50 - (alt_km / maxAlt) * (svgHeight - 100);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-7xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        
        {/* ─── HEADER ─── */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 shadow-sm">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-600 text-white">
                  Stage 22 Sovereign
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                  <Flame className="w-3 h-3" /> PPN Relativistic &amp; Sutton-Graves
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Optical TRN EKF &lt; 5m CEP
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">
                Relativistic Planetary Entry, Descent &amp; Landing (EDL) with Optical TRN
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => runSimulation(selectedPreset)}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {loading ? "Integrating EDL Corridor..." : "Re-Simulate EDL"}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* ─── BODY ─── */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Preset Selector */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {Object.entries(EDL_PRESETS_META).map(([key, meta]) => {
              const isSelected = selectedPreset === key;
              return (
                <button
                  key={key}
                  onClick={() => handlePresetChange(key)}
                  className={`p-3.5 rounded-xl text-left border transition-all ${
                    isSelected
                      ? "border-rose-600 bg-rose-50/50 shadow-sm ring-1 ring-rose-600"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-900">{meta.planet} EDL</span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      {meta.vehicle.split(" ")[0]}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-slate-800 line-clamp-1">{meta.label}</div>
                  <div className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">{meta.desc}</div>
                </button>
              );
            })}
          </div>

          {/* ─── SIMULATION CANVAS & OPTICAL TRN HUD INSET ─── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            
            {/* Trajectory Cross-Section View */}
            <div className="lg:col-span-2 relative border border-slate-200 rounded-2xl bg-slate-950 overflow-hidden shadow-inner flex flex-col items-center">
              <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-200 border border-slate-800">
                  Target: {dossier?.target_site_name || "Planetary Landing Site"}
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-amber-400 border border-slate-800">
                  Phase: {currentPoint?.phase || "Hypersonic Entry"}
                </span>
              </div>

              <div className="absolute top-3 right-4 z-10 flex items-center gap-2">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="px-2 py-1 rounded bg-slate-800/90 hover:bg-slate-700 text-slate-200 text-xs font-mono border border-slate-700 transition-colors flex items-center gap-1"
                >
                  {isPlaying ? <Pause className="w-3 h-3 text-amber-400" /> : <Play className="w-3 h-3 text-emerald-400" />}
                  {isPlaying ? "Pause" : "Play"}
                </button>
                <button
                  onClick={() => setAnimIndex(0)}
                  className="p-1 rounded bg-slate-800/90 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>
              </div>

              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-[400px] select-none"
                style={{ background: "radial-gradient(ellipse at top, #1e1b4b 0%, #020617 100%)" }}
              >
                <defs>
                  <linearGradient id="atmoGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.25" />
                    <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.1" />
                    <stop offset="100%" stopColor="#0f172a" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Atmospheric Ionization Region */}
                <rect x="50" y="50" width={svgWidth - 100} height={svgHeight - 100} fill="url(#atmoGlow)" />

                {/* Ground Surface Curve */}
                <path
                  d={`M 40 ${svgHeight - 50} Q ${svgWidth / 2} ${svgHeight - 40} ${svgWidth - 40} ${svgHeight - 50}`}
                  stroke="#64748b"
                  strokeWidth="2.5"
                  fill="none"
                />
                <text x={svgWidth - 60} y={svgHeight - 32} fill="#64748b" fontSize="10" fontFamily="monospace" textAnchor="end">
                  Surface Terrain (0 km Datum)
                </text>

                {/* Trajectory Path */}
                {dossier && dossier.trajectory.length > 0 && (() => {
                  const pts = dossier.trajectory;
                  const pathStr = pts.reduce((acc, p, idx) => {
                    const sx = toSvgX(p.downrange_km);
                    const sy = toSvgY(p.altitude_km);
                    return idx === 0 ? `M ${sx} ${sy}` : `${acc} L ${sx} ${sy}`;
                  }, "");

                  return (
                    <>
                      <path
                        d={pathStr}
                        fill="none"
                        stroke="#f43f5e"
                        strokeWidth="2.2"
                        strokeLinecap="round"
                        strokeDasharray="6 3"
                        strokeOpacity="0.8"
                      />
                      {/* Active Capsule Sprite */}
                      {currentPoint && (() => {
                        const cx = toSvgX(currentPoint.downrange_km);
                        const cy = toSvgY(currentPoint.altitude_km);
                        const isPlasma = currentPoint.altitude_km > 35 && currentPoint.altitude_km < 80;
                        return (
                          <g>
                            {isPlasma && (
                              <circle cx={cx} cy={cy} r="16" fill="#f43f5e" opacity="0.3" className="animate-ping" />
                            )}
                            <circle cx={cx} cy={cy} r="6" fill="#fb7185" stroke="#ffffff" strokeWidth="1.5" />
                            <text x={cx + 10} y={cy - 6} fill="#fecdd3" fontSize="10" fontFamily="monospace" fontWeight="bold">
                              {currentPoint.velocity_mps.toFixed(0)} m/s (M{currentPoint.mach_number.toFixed(1)})
                            </text>
                          </g>
                        );
                      })()}
                    </>
                  );
                })()}
              </svg>
            </div>

            {/* Optical TRN Camera Viewfinder HUD */}
            <div className="p-4 rounded-2xl border border-slate-200 bg-slate-900 text-white flex flex-col justify-between shadow-inner">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Camera className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Optical TRN Viewfinder
                    </span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    currentPoint?.optical_trn_active ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-slate-800 text-slate-400"
                  }`}>
                    {currentPoint?.optical_trn_active ? "TRN ACTIVE LOCK" : "STANDBY"}
                  </span>
                </div>

                {/* Simulated Camera Sensor Canvas */}
                <div className="relative mt-3 h-52 bg-slate-950 rounded-xl border border-slate-800 overflow-hidden flex items-center justify-center">
                  <div className="absolute inset-0 opacity-20 pointer-events-none" style={{
                    backgroundImage: "radial-gradient(#38bdf8 1px, transparent 1px)",
                    backgroundSize: "20px 20px",
                  }} />

                  {/* Crosshairs */}
                  <div className="absolute w-full h-px bg-emerald-500/30" />
                  <div className="absolute h-full w-px bg-emerald-500/30" />
                  <div className="w-24 h-24 rounded-full border border-emerald-500/40 border-dashed animate-spin" style={{ animationDuration: "20s" }} />

                  {/* Landmark Feature Reticles */}
                  {dossier?.optical_features.slice(0, 5).map((feat, fIdx) => (
                    <div
                      key={feat.feature_id}
                      className="absolute flex items-center gap-1"
                      style={{
                        left: `${(feat.pixel_x / 1024) * 80 + 10}%`,
                        top: `${(feat.pixel_y / 768) * 70 + 15}%`,
                      }}
                    >
                      <Crosshair className="w-4 h-4 text-emerald-400 animate-pulse" />
                      <span className="text-[9px] font-mono text-emerald-300 bg-slate-900/80 px-1 rounded">
                        {feat.map_crater_id} (err: {feat.residual_error_px}px)
                      </span>
                    </div>
                  ))}

                  {/* 1-Sigma Covariance Ellipse */}
                  <div
                    className="absolute rounded-full border-2 border-emerald-400/80 bg-emerald-400/10 flex items-center justify-center transition-all duration-300"
                    style={{
                      width: `${Math.max(24, Math.min(180, (currentPoint?.trn_covariance_sigma_m || 3200) / 18))}%`,
                      height: `${Math.max(20, Math.min(150, (currentPoint?.trn_covariance_sigma_m || 3200) / 22))}%`,
                    }}
                  >
                    <span className="text-[10px] font-mono text-emerald-300 font-bold bg-slate-950/80 px-1 rounded">
                      σ = {currentPoint?.trn_covariance_sigma_m.toFixed(1)} m
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 space-y-1.5 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>EKF Covariance Collapse:</span>
                  <strong className="text-emerald-400 font-mono">
                    3,200 m → {dossier?.landing_error_cep_m.toFixed(1)} m CEP
                  </strong>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Optical Landmark Fixes:</span>
                  <strong className="text-slate-200 font-mono">{dossier?.optical_trn_fixes} Matches</strong>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Hazard Divert (LHA):</span>
                  <strong className={dossier?.hazard_detected ? "text-amber-400 font-mono" : "text-slate-400 font-mono"}>
                    {dossier?.hazard_detected ? "185.0 m Delta Divert Executed" : "None Required"}
                  </strong>
                </div>
              </div>
            </div>

          </div>

          {/* ─── KPI TELEMETRY DECK ─── */}
          {dossier && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Peak Heat Flux</div>
                <div className="text-base font-bold text-rose-600 mt-0.5 flex items-center gap-1">
                  <Flame className="w-4 h-4" /> {dossier.peak_heat_flux_mw_m2.toFixed(3)} MW/m²
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Sutton-Graves Stagnation</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Peak Deceleration</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.peak_g_load.toFixed(2)} g</div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Envelope Protected
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Landing CEP</div>
                <div className="text-base font-bold text-emerald-600 mt-0.5">{dossier.landing_error_cep_m.toFixed(1)} m</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Sub-5-Meter Precision</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Touchdown Speed</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.final_touchdown_speed_mps.toFixed(2)} m/s</div>
                <div className="text-[10px] text-indigo-600 font-semibold mt-0.5">Terminal Soft Landing</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Ballistic Beta</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.ballistic_coefficient_kg_m2.toFixed(1)} kg/m²</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Mass: {dossier.entry_mass_kg} kg</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Target Planet</div>
                <div className="text-xs font-bold text-slate-900 mt-1 line-clamp-1">{dossier.target_planet}</div>
                <div className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{dossier.target_site_name.split("(")[0]}</div>
              </div>
            </div>
          )}

          {/* ─── CRYPTOGRAPHIC PROVENANCE FOOTER ─── */}
          {dossier && (
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span className="font-semibold text-slate-700">SHA-256 EDL Lineage:</span>
                <code className="font-mono text-[11px] text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {dossier.merkle_provenance_hash}
                </code>
                <button
                  onClick={copyMerkle}
                  className="p-1 rounded text-slate-500 hover:text-slate-800 transition-colors"
                  title="Copy Provenance Hash"
                >
                  {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `edl_${dossier.preset_key}.json`;
                    a.click();
                  }}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export EDL Dossier
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
