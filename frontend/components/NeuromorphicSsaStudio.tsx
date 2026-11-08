"use client";

import React, { useState, useEffect } from "react";
import {
  Eye,
  Activity,
  ShieldCheck,
  ShieldAlert,
  Download,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Crosshair,
  TrendingDown,
  RotateCcw,
  Zap,
  Play,
  Pause,
  Copy,
  Check,
} from "lucide-react";

interface DetectedDebrisObject {
  object_id: string;
  target_name: string;
  regime: string;
  estimated_diameter_cm: number;
  relative_velocity_km_s: number;
  range_km: number;
  angular_rate_deg_s: number;
  event_count: number;
  semi_major_axis_km: number;
  eccentricity: number;
  inclination_deg: number;
  collision_probability_pc: number;
  covariance_pos_1sigma_m: number;
  covariance_vel_1sigma_mps: number;
}

interface SpatioTemporalStreak {
  streak_id: string;
  object_id: string;
  start_px: [number, number];
  end_px: [number, number];
  duration_us: number;
  event_density_per_ms: number;
  hough_snr_db: number;
}

interface SSAMissionDossier {
  mission_id: string;
  preset_key: string;
  tracking_scenario: string;
  sensor_model: string;
  temporal_resolution_us: number;
  dynamic_range_db: number;
  sensor_power_mw: number;
  total_events_processed: number;
  debris_objects_detected: DetectedDebrisObject[];
  spatio_temporal_streaks: SpatioTemporalStreak[];
  angles_only_iod_method: string;
  provenance_hash: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

const SSA_PRESETS_META: Record<string, { label: string; regime: string; target_count: number; threat: string; desc: string }> = {
  LEO_STARLINK_CONSTELLATION_DEBRIS: {
    label: "LEO Megaconstellation Micro-Debris",
    regime: "LEO (550 km)",
    target_count: 3,
    threat: "Lethal Non-Trackable (0.8 - 8.0 cm)",
    desc: "Asynchronous microsecond DVS event processing detecting sub-centimeter debris traveling at 11-14 km/s.",
  },
  ISRO_NETRA_OPTICAL_DVS_ORBIT: {
    label: "ISRO Project NETRA Spaceborne DVS",
    regime: "GEO / GTO Corridor",
    target_count: 2,
    threat: "Apogee Kick Fragmentation",
    desc: "ISRO NETRA high-dynamic-range event camera tracking GEO upper stage delamination shards without star clutter.",
  },
  APOPHIS_PLANETARY_DEFENSE_ASTEROID: {
    label: "Near-Earth Asteroid 99942 Apophis",
    regime: "Planetary Defense Interplanetary",
    target_count: 2,
    threat: "Hazardous NEO Core & Shards",
    desc: "High-cadence microsecond astrometry during Earth close encounter, collapsing Keplerian semi-major axis uncertainty.",
  },
  LUNAR_GATEWAY_MICROMETEOROID_SWARM: {
    label: "Cislunar NRHO Micrometeoroid Flux",
    regime: "Cislunar Space (Halo Orbit)",
    target_count: 2,
    threat: "Hypervelocity Sporadic Streams",
    desc: "High-speed sporadic meteoroids (24-28 km/s) impacting the Artemis Gateway cislunar transit corridor.",
  },
};

export default function NeuromorphicSsaStudio({ isOpen, onClose, apiBase }: Props) {
  const [selectedPreset, setSelectedPreset] = useState("LEO_STARLINK_CONSTELLATION_DEBRIS");
  const [dossier, setDossier] = useState<SSAMissionDossier | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [animProgress, setAnimProgress] = useState(0);
  const [copiedHash, setCopiedHash] = useState(false);

  const runTracking = async (presetKey: string) => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/ssa/track`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset_key: presetKey }),
      });
      if (resp.ok) {
        const data: SSAMissionDossier = await resp.json();
        setDossier(data);
        setAnimProgress(0);
      }
    } catch (err) {
      console.error("Neuromorphic SSA tracking error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !dossier) {
      runTracking(selectedPreset);
    }
  }, [isOpen]);

  const handlePresetChange = (key: string) => {
    setSelectedPreset(key);
    runTracking(key);
  };

  // Streak animation loop
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setAnimProgress((prev) => (prev >= 1.0 ? 0.0 : prev + 0.04));
    }, 50);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const copyMerkle = () => {
    if (!dossier) return;
    navigator.clipboard.writeText(dossier.provenance_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-7xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        
        {/* ─── HEADER ─── */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-50 border border-violet-200 flex items-center justify-center text-violet-600 shadow-sm">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-violet-600 text-white">
                  Stage 24 Sovereign
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> 1.0 μs Asynchronous DVS
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                  124 dB Dynamic Range • 14.5 mW
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">
                Neuromorphic Event-Camera Micro-Debris &amp; Asteroid SSA Tracker
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => runTracking(selectedPreset)}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {loading ? "Processing DVS Events..." : "Acquire Event Stream"}
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
            {Object.entries(SSA_PRESETS_META).map(([key, meta]) => {
              const isSelected = selectedPreset === key;
              return (
                <button
                  key={key}
                  onClick={() => handlePresetChange(key)}
                  className={`p-3.5 rounded-xl text-left border transition-all ${
                    isSelected
                      ? "border-violet-600 bg-violet-50/50 shadow-sm ring-1 ring-violet-600"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-900">{meta.regime.split(" ")[0]}</span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      {meta.target_count} Targets
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-slate-800 line-clamp-1">{meta.label}</div>
                  <div className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">{meta.desc}</div>
                </button>
              );
            })}
          </div>

          {/* ─── DVS FOCAL PLANE ASYNCHRONOUS EVENT STREAM CANVAS ─── */}
          <div className="relative border border-slate-200 rounded-2xl bg-slate-950 overflow-hidden shadow-inner flex flex-col items-center">
            
            {/* Top Status Overlay */}
            <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-200 border border-slate-800">
                Sensor: Prophesee Gen4 DVS (1280×720)
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-emerald-400 border border-slate-800">
                Events: {dossier?.total_events_processed || 0} Spikes / 100 ms
              </span>
            </div>

            <div className="absolute top-3 right-4 z-10 flex items-center gap-2">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-300 border border-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" /> ON (+1)
                <span className="w-2 h-2 rounded-full bg-rose-400 inline-block ml-1" /> OFF (-1)
              </span>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-2 py-1 rounded bg-slate-800/90 hover:bg-slate-700 text-slate-200 text-xs font-mono border border-slate-700 transition-colors flex items-center gap-1"
              >
                {isPlaying ? <Pause className="w-3 h-3 text-amber-400" /> : <Play className="w-3 h-3 text-emerald-400" />}
                {isPlaying ? "Pause" : "Play"}
              </button>
              <button
                onClick={() => setAnimProgress(0)}
                className="p-1 rounded bg-slate-800/90 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>

            {/* SVG Visualizer */}
            <svg
              viewBox="0 0 1280 720"
              className="w-full h-[400px] select-none"
              style={{ background: "radial-gradient(ellipse at center, #0f172a 0%, #020617 100%)" }}
            >
              <defs>
                <pattern id="pixelGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" />
                </pattern>
              </defs>

              <rect width="1280" height="720" fill="url(#pixelGrid)" />

              {/* Star Background Clutter (Stationary / Suppressed by DVS temporal contrast) */}
              {[
                [180, 120], [340, 280], [560, 140], [780, 220], [920, 110], [1080, 260],
                [240, 480], [420, 620], [680, 540], [890, 610], [1150, 510],
              ].map(([sx, sy], i) => (
                <circle key={`star-${i}`} cx={sx} cy={sy} r="1.5" fill="#475569" opacity="0.4" />
              ))}

              {/* Spatiotemporal Hough Streak Lines */}
              {dossier?.spatio_temporal_streaks.map((stk, sIdx) => {
                const x1 = stk.start_px[0];
                const y1 = stk.start_px[1];
                const x2 = stk.end_px[0];
                const y2 = stk.end_px[1];

                // Animated current position along streak
                const curX = x1 + (x2 - x1) * animProgress;
                const curY = y1 + (y2 - y1) * animProgress;

                const debObj = dossier.debris_objects_detected[sIdx];

                return (
                  <g key={stk.streak_id}>
                    {/* Full Streak Ray */}
                    <line
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#8b5cf6"
                      strokeWidth="1.5"
                      strokeDasharray="4 3"
                      strokeOpacity="0.4"
                    />

                    {/* Active Microsecond Event Wavefront */}
                    <line
                      x1={Math.max(x1, curX - (x2 - x1) * 0.25)}
                      y1={Math.max(y1, curY - (y2 - y1) * 0.25)}
                      x2={curX}
                      y2={curY}
                      stroke="#38bdf8"
                      strokeWidth="3.0"
                      strokeLinecap="round"
                    />

                    {/* Target Tracking Reticle */}
                    <circle cx={curX} cy={curY} r="18" fill="none" stroke="#a855f7" strokeWidth="1.5" strokeDasharray="3 2" />
                    <circle cx={curX} cy={curY} r="4" fill="#38bdf8" />

                    {/* Target HUD Tag */}
                    <g transform={`translate(${curX + 22}, ${curY - 12})`}>
                      <rect width="190" height="42" rx="6" fill="rgba(15, 23, 42, 0.88)" stroke="#8b5cf6" strokeWidth="1" />
                      <text x="8" y="16" fill="#f8fafc" fontSize="11" fontFamily="sans-serif" fontWeight="bold">
                        {debObj ? debObj.target_name.split(" ")[0] : stk.object_id} ({debObj?.estimated_diameter_cm} cm)
                      </text>
                      <text x="8" y="32" fill="#a855f7" fontSize="10" fontFamily="monospace">
                        v={debObj?.relative_velocity_km_s} km/s • R={debObj?.range_km} km
                      </text>
                    </g>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* ─── SENSOR & TELEMETRY KPI DECK ─── */}
          {dossier && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Temporal Resolution</div>
                <div className="text-base font-bold text-violet-600 mt-0.5">{dossier.temporal_resolution_us.toFixed(1)} μs</div>
                <div className="text-[10px] text-slate-500 mt-0.5">1,000,000 fps Equiv</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Dynamic Range</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.dynamic_range_db.toFixed(0)} dB</div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">Zero Motion Blur</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Sensor Power</div>
                <div className="text-base font-bold text-emerald-600 mt-0.5">{dossier.sensor_power_mw.toFixed(1)} mW</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Edge Event Processor</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Debris Detected</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.debris_objects_detected.length} Objects</div>
                <div className="text-[10px] text-amber-600 font-semibold mt-0.5">Sub-Centimeter Tracked</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">1-σ Position Covariance</div>
                <div className="text-base font-bold text-indigo-600 mt-0.5">
                  &lt; {Math.max(...dossier.debris_objects_detected.map((o) => o.covariance_pos_1sigma_m)).toFixed(1)} m
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Microsecond Collapse</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Event Spikes</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.total_events_processed.toLocaleString()}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Asynchronous Packets</div>
              </div>
            </div>
          )}

          {/* ─── ORBIT DETERMINATION & DEBRIS CATALOG TABLE ─── */}
          {dossier && (
            <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-violet-600" />
                  Angles-Only Initial Orbit Determination (IOD) &amp; Collision Probability
                </h3>
                <span className="text-[11px] font-mono text-slate-500">{dossier.angles_only_iod_method}</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-600 font-semibold">
                    <tr>
                      <th className="px-3 py-2">ID</th>
                      <th className="px-3 py-2">Target Name</th>
                      <th className="px-3 py-2">Size</th>
                      <th className="px-3 py-2">Rel Speed</th>
                      <th className="px-3 py-2">Range</th>
                      <th className="px-3 py-2">Semi-Major a</th>
                      <th className="px-3 py-2">Eccentricity e</th>
                      <th className="px-3 py-2">Inc i</th>
                      <th className="px-3 py-2">Pos 1-σ</th>
                      <th className="px-3 py-2">Collision Prob (Pc)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {dossier.debris_objects_detected.map((obj) => (
                      <tr key={obj.object_id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-3 py-2 font-bold text-slate-900">{obj.object_id}</td>
                        <td className="px-3 py-2 font-sans font-semibold text-slate-800">{obj.target_name}</td>
                        <td className="px-3 py-2 text-slate-700">{obj.estimated_diameter_cm} cm</td>
                        <td className="px-3 py-2 text-violet-700 font-semibold">{obj.relative_velocity_km_s} km/s</td>
                        <td className="px-3 py-2 text-slate-600">{obj.range_km} km</td>
                        <td className="px-3 py-2 text-slate-800">{obj.semi_major_axis_km.toLocaleString()} km</td>
                        <td className="px-3 py-2 text-slate-600">{obj.eccentricity.toFixed(4)}</td>
                        <td className="px-3 py-2 text-slate-600">{obj.inclination_deg.toFixed(1)}°</td>
                        <td className="px-3 py-2 text-emerald-600 font-semibold">±{obj.covariance_pos_1sigma_m} m</td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            obj.collision_probability_pc > 1e-4 ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"
                          }`}>
                            {obj.collision_probability_pc.toExponential(2)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ─── CRYPTOGRAPHIC PROVENANCE FOOTER ─── */}
          {dossier && (
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span className="font-semibold text-slate-700">SHA-256 Astrometric Lineage:</span>
                <code className="font-mono text-[11px] text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {dossier.provenance_hash}
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
                    a.download = `ssa_${dossier.preset_key}.json`;
                    a.click();
                  }}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export SSA Dossier
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
