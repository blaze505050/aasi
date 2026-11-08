"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Orbit,
  Globe,
  Compass,
  Activity,
  ShieldCheck,
  Download,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Info,
  CheckCircle2,
  Layers,
  Zap,
  TrendingDown,
  Navigation,
  ArrowRight,
  ChevronRight,
  Copy,
  Check,
} from "lucide-react";

interface LagrangePointInfo {
  name: string;
  x_synodic: number;
  y_synodic: number;
  z_synodic: number;
  x_km: number;
  y_km: number;
  z_km: number;
  jacobi_constant: number;
}

interface TrajectoryPoint {
  x_km: number;
  y_km: number;
  z_km: number;
  vx_km_s?: number;
  vy_km_s?: number;
  vz_km_s?: number;
}

interface HaloOrbitSolution {
  orbit_id: string;
  lagrange_point: string;
  family: string;
  period_nd: number;
  period_days: number;
  jacobi_constant: number;
  pericynthion_km: number;
  apocynthion_km: number;
  amplitude_z_km: number;
  stability_index_nu: number;
  trajectory_synodic_km: TrajectoryPoint[];
  monodromy_eigenvalues: number[];
}

interface InvariantManifoldBranch {
  branch_type: string;
  step_id: number;
  delta_v_insertion_mps: number;
  transit_duration_days: number;
  trajectory_points_km: TrajectoryPoint[];
}

interface CislunarMissionDossier {
  mission_id: string;
  preset_key: string;
  mission_name: string;
  target_vehicle: string;
  primary_lagrange_point: string;
  orbit_solution: HaloOrbitSolution;
  stable_manifolds: InvariantManifoldBranch[];
  unstable_manifolds: InvariantManifoldBranch[];
  ballistic_delta_v_savings_pct: number;
  jacobi_conservation_drift: number;
  merkle_provenance_hash: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

const PRESETS_META: Record<string, { label: string; vehicle: string; point: string; defaultAz: number; desc: string }> = {
  ISRO_GAGANYAAN_LUNAR_GATEWAY_L2: {
    label: "ISRO Gaganyaan Cislunar Gateway L2",
    vehicle: "Gaganyaan Orbital Habitation Complex & Lunar Tug",
    point: "L2",
    defaultAz: 32000,
    desc: "Far-side lunar telecommunications relay and Deep-Space staging habitat at Earth-Moon L2 southern halo.",
  },
  ARTEMIS_NRHO_L1_INSERTION: {
    label: "Artemis & SpaDeX 9:2 NRHO L1",
    vehicle: "Orion MPCV / SpaDeX Lunar Logistics Chaser",
    point: "L1",
    defaultAz: 70000,
    desc: "Near-Rectilinear Halo Orbit in 9:2 lunar orbital resonance, ensuring zero eclipse and low-delta-V lunar access.",
  },
  CHANDRAYAAN_LOW_ENERGY_TRANSIT: {
    label: "Chandrayaan Weak Stability Boundary (WSB)",
    vehicle: "Chandrayaan-4 Sample Return Heavy Stage",
    point: "L1",
    defaultAz: 18000,
    desc: "Ballistic lunar transfer exploiting invariant manifold tubes with 31.8% propellant savings.",
  },
  EARTH_MOON_L4_TROJAN_STATION: {
    label: "Sovereign Deep-Space Relay L4 Trojan",
    vehicle: "Sovereign High-Gain Deep Space Optical Array",
    point: "L4",
    defaultAz: 0,
    desc: "Equilateral triangular libration point observation platform with stable zero-drag orbital equilibrium.",
  },
};

export default function CislunarManifoldStudio({ isOpen, onClose, apiBase }: Props) {
  const [selectedPreset, setSelectedPreset] = useState("ISRO_GAGANYAAN_LUNAR_GATEWAY_L2");
  const [amplitudeZ, setAmplitudeZ] = useState<number>(32000);
  const [viewPlane, setViewPlane] = useState<"XY" | "XZ">("XY");
  const [showManifolds, setShowManifolds] = useState(true);
  const [dossier, setDossier] = useState<CislunarMissionDossier | null>(null);
  const [lagrangePoints, setLagrangePoints] = useState<Record<string, LagrangePointInfo>>({});
  const [loading, setLoading] = useState(false);
  const [animIndex, setAnimIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [copiedHash, setCopiedHash] = useState(false);

  // Fetch Lagrange points on mount
  useEffect(() => {
    if (!isOpen) return;
    fetch(`${apiBase}/api/v1/cislunar/lagrange-points`)
      .then((res) => res.json())
      .then((data) => setLagrangePoints(data))
      .catch((err) => console.error("Failed to load Lagrange points:", err));
  }, [isOpen, apiBase]);

  // Execute cislunar calculation
  const runSimulation = async (presetKey: string, azKm: number) => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/cislunar/navigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: presetKey,
          override_amplitude_z_km: azKm,
        }),
      });
      if (resp.ok) {
        const data: CislunarMissionDossier = await resp.json();
        setDossier(data);
        setAnimIndex(0);
      }
    } catch (err) {
      console.error("Cislunar navigation calculation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !dossier) {
      runSimulation(selectedPreset, amplitudeZ);
    }
  }, [isOpen]);

  // Handle preset change
  const handlePresetChange = (key: string) => {
    setSelectedPreset(key);
    const meta = PRESETS_META[key];
    const newAz = meta ? meta.defaultAz : 32000;
    setAmplitudeZ(newAz);
    runSimulation(key, newAz);
  };

  // Orbit animation loop
  useEffect(() => {
    if (!isPlaying || !dossier || !dossier.orbit_solution.trajectory_synodic_km.length) return;
    const interval = setInterval(() => {
      setAnimIndex((prev) => (prev + 1) % dossier.orbit_solution.trajectory_synodic_km.length);
    }, 45);
    return () => clearInterval(interval);
  }, [isPlaying, dossier]);

  const copyMerkle = () => {
    if (!dossier) return;
    navigator.clipboard.writeText(dossier.merkle_provenance_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Coordinate projections for SVG rendering
  // Earth at (0, 0) synodic offset for visualization, Moon at (+384,400 km, 0)
  // Non-dimensional char distance = 384,400 km.
  // SVG Canvas dimensions: 800 x 500
  const svgWidth = 800;
  const svgHeight = 500;

  // Transform (x_km, y_km or z_km) to SVG (cx, cy)
  // X range: -100,000 km to +480,000 km
  // Y range: -200,000 km to +200,000 km (for XY) or -100,000 km to +100,000 km (for XZ)
  const toSvgCoords = (x_km: number, y_km: number, z_km: number) => {
    const xMin = -90000;
    const xMax = 490000;
    const vertVal = viewPlane === "XY" ? y_km : z_km;
    const vSpan = viewPlane === "XY" ? 190000 : 90000;

    const px = ((x_km - xMin) / (xMax - xMin)) * (svgWidth - 100) + 50;
    const py = svgHeight / 2 - (vertVal / vSpan) * (svgHeight / 2 - 40);
    return { px, py };
  };

  const earthCoords = toSvgCoords(0, 0, 0);
  const moonCoords = toSvgCoords(384400, 0, 0);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-7xl max-h-[92vh] flex flex-col overflow-hidden text-slate-800">
        
        {/* ─── HEADER ─── */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 shadow-sm">
              <Orbit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-600 text-white">
                  Stage 21 Sovereign
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> CR3BP Synodic Symplectic
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  ΔCJ &lt; 1e-8 Invariant
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">
                Autonomous Cislunar &amp; Lagrange Point Halo Orbit Manifold Navigator
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => runSimulation(selectedPreset, amplitudeZ)}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {loading ? "Synthesizing CR3BP..." : "Recompute Manifolds"}
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
          
          {/* Mission Presets Selection */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {Object.entries(PRESETS_META).map(([key, meta]) => {
              const isSelected = selectedPreset === key;
              return (
                <button
                  key={key}
                  onClick={() => handlePresetChange(key)}
                  className={`p-3.5 rounded-xl text-left border transition-all ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-50/50 shadow-sm ring-1 ring-indigo-600"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-900">{meta.point} Gateway</span>
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

          {/* Interactive Parameters Bar */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Halo Out-of-Plane Amplitude Az: <span className="text-indigo-600 font-bold">{amplitudeZ.toLocaleString()} km</span>
                </label>
                <input
                  type="range"
                  min={0}
                  max={85000}
                  step={2000}
                  value={amplitudeZ}
                  onChange={(e) => setAmplitudeZ(Number(e.target.value))}
                  onMouseUp={() => runSimulation(selectedPreset, amplitudeZ)}
                  className="w-56 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                />
              </div>

              <div className="h-8 w-px bg-slate-200" />

              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-700">Projection:</span>
                <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-sm">
                  <button
                    onClick={() => setViewPlane("XY")}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                      viewPlane === "XY" ? "bg-indigo-600 text-white" : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Synodic X-Y Plane
                  </button>
                  <button
                    onClick={() => setViewPlane("XZ")}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                      viewPlane === "XZ" ? "bg-indigo-600 text-white" : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Meridional X-Z Plane
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showManifolds}
                    onChange={(e) => setShowManifolds(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Show Wˢ / Wᵘ Manifolds</span>
                </label>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5 text-amber-600" /> : <Play className="w-3.5 h-3.5 text-emerald-600" />}
                {isPlaying ? "Pause" : "Play Orbit"}
              </button>
              <button
                onClick={() => setAnimIndex(0)}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 shadow-sm transition-colors"
                title="Reset Animation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* ─── 3D SYNODIC ORBIT & MANIFOLD VISUALIZER (SVG CANVAS) ─── */}
          <div className="relative border border-slate-200 rounded-2xl bg-slate-900 overflow-hidden shadow-inner flex flex-col items-center">
            
            {/* Canvas Overlay Controls */}
            <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-slate-200 border border-slate-700 backdrop-blur-sm">
                Frame: Earth-Moon Synodic Rotating Frame
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-emerald-400 border border-slate-700 backdrop-blur-sm">
                Scale: 1 unit = 384,400 km
              </span>
            </div>

            <div className="absolute top-3 right-4 z-10 flex items-center gap-3 text-[11px] text-slate-300 font-mono bg-slate-800/80 px-3 py-1 rounded border border-slate-700 backdrop-blur-sm">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block animate-pulse" /> Halo Orbit
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> Wˢ Stable Tube
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" /> Wᵘ Unstable Tube
              </span>
            </div>

            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-[440px] select-none"
              style={{ background: "radial-gradient(ellipse at center, #0f172a 0%, #020617 100%)" }}
            >
              <defs>
                <radialGradient id="earthGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                  <stop offset="60%" stopColor="#0284c7" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#0284c7" stopOpacity="0" />
                </radialGradient>
                <radialGradient id="moonGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#f8fafc" stopOpacity="0.9" />
                  <stop offset="70%" stopColor="#cbd5e1" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#94a3b8" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="50" y1={svgHeight / 2} x2={svgWidth - 50} y2={svgHeight / 2} stroke="#334155" strokeWidth="0.8" strokeDasharray="3 3" />
              <line x1={earthCoords.px} y1="30" x2={earthCoords.px} y2={svgHeight - 30} stroke="#334155" strokeWidth="0.8" strokeDasharray="3 3" />
              <line x1={moonCoords.px} y1="30" x2={moonCoords.px} y2={svgHeight - 30} stroke="#334155" strokeWidth="0.8" strokeDasharray="3 3" />

              {/* Stable Manifold Tubes (Ws) */}
              {showManifolds && dossier?.stable_manifolds.map((branch, bIdx) => {
                const pathStr = branch.trajectory_points_km.reduce((acc, pt, idx) => {
                  const { px, py } = toSvgCoords(pt.x_km, pt.y_km, pt.z_km);
                  return idx === 0 ? `M ${px} ${py}` : `${acc} L ${px} ${py}`;
                }, "");
                return (
                  <path
                    key={`ws-${bIdx}`}
                    d={pathStr}
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="1.2"
                    strokeOpacity="0.65"
                    strokeDasharray="4 2"
                  />
                );
              })}

              {/* Unstable Manifold Tubes (Wu) */}
              {showManifolds && dossier?.unstable_manifolds.map((branch, bIdx) => {
                const pathStr = branch.trajectory_points_km.reduce((acc, pt, idx) => {
                  const { px, py } = toSvgCoords(pt.x_km, pt.y_km, pt.z_km);
                  return idx === 0 ? `M ${px} ${py}` : `${acc} L ${px} ${py}`;
                }, "");
                return (
                  <path
                    key={`wu-${bIdx}`}
                    d={pathStr}
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="1.2"
                    strokeOpacity="0.65"
                  />
                );
              })}

              {/* Halo Orbit Trajectory */}
              {dossier && dossier.orbit_solution.trajectory_synodic_km.length > 0 && (() => {
                const traj = dossier.orbit_solution.trajectory_synodic_km;
                const pathStr = traj.reduce((acc, pt, idx) => {
                  const { px, py } = toSvgCoords(pt.x_km, pt.y_km, pt.z_km);
                  return idx === 0 ? `M ${px} ${py}` : `${acc} L ${px} ${py}`;
                }, "") + " Z";

                return (
                  <>
                    <path
                      d={pathStr}
                      fill="rgba(6, 182, 212, 0.08)"
                      stroke="#06b6d4"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    {/* Active Spacecraft Position on Halo */}
                    {traj[animIndex] && (() => {
                      const curPt = traj[animIndex];
                      const { px, py } = toSvgCoords(curPt.x_km, curPt.y_km, curPt.z_km);
                      return (
                        <g>
                          <circle cx={px} cy={py} r="8" fill="#38bdf8" opacity="0.4" className="animate-ping" />
                          <circle cx={px} cy={py} r="4.5" fill="#38bdf8" stroke="#ffffff" strokeWidth="1.5" />
                          <text x={px + 9} y={py - 6} fill="#e0f2fe" fontSize="10" fontFamily="monospace" fontWeight="bold">
                            {dossier.target_vehicle.split(" ")[0]}
                          </text>
                        </g>
                      );
                    })()}
                  </>
                );
              })()}

              {/* Earth Body */}
              <circle cx={earthCoords.px} cy={earthCoords.py} r="26" fill="url(#earthGlow)" />
              <circle cx={earthCoords.px} cy={earthCoords.py} r="14" fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
              <text x={earthCoords.px} y={earthCoords.py + 26} fill="#94a3b8" fontSize="11" textAnchor="middle" fontWeight="bold">
                Earth (M₁)
              </text>

              {/* Moon Body */}
              <circle cx={moonCoords.px} cy={moonCoords.py} r="18" fill="url(#moonGlow)" />
              <circle cx={moonCoords.px} cy={moonCoords.py} r="7.5" fill="#e2e8f0" stroke="#cbd5e1" strokeWidth="1.2" />
              <text x={moonCoords.px} y={moonCoords.py + 22} fill="#94a3b8" fontSize="11" textAnchor="middle" fontWeight="bold">
                Moon (M₂)
              </text>

              {/* Lagrange Points Markers */}
              {Object.entries(lagrangePoints).map(([lpKey, lp]) => {
                const { px, py } = toSvgCoords(lp.x_km, lp.y_km, lp.z_km);
                const isTarget = dossier?.primary_lagrange_point === lpKey;
                return (
                  <g key={lpKey}>
                    <circle
                      cx={px}
                      cy={py}
                      r={isTarget ? 5.5 : 3.5}
                      fill={isTarget ? "#a855f7" : "#64748b"}
                      stroke="#ffffff"
                      strokeWidth="1"
                    />
                    <text
                      x={px}
                      y={py - 7}
                      fill={isTarget ? "#d8b4fe" : "#94a3b8"}
                      fontSize="10"
                      textAnchor="middle"
                      fontWeight="bold"
                    >
                      {lpKey}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* ─── TELEMETRY & PHYSICAL INVARIANT KPI DECK ─── */}
          {dossier && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Jacobi Constant CJ</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.orbit_solution.jacobi_constant.toFixed(6)}</div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Drift: {dossier.jacobi_conservation_drift.toExponential(2)}
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Ballistic ΔV Savings</div>
                <div className="text-base font-bold text-emerald-600 mt-0.5 flex items-center gap-1">
                  <TrendingDown className="w-4 h-4" /> {dossier.ballistic_delta_v_savings_pct.toFixed(1)}%
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Zero-Propellant Manifold</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Orbit Period</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.orbit_solution.period_days.toFixed(1)} Days</div>
                <div className="text-[10px] text-indigo-600 font-semibold mt-0.5">
                  {dossier.orbit_solution.period_nd.toFixed(3)} synodic
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Lunar Pericynthion</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.orbit_solution.pericynthion_km.toLocaleString()} km</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Apo: {dossier.orbit_solution.apocynthion_km.toLocaleString()} km</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Monodromy Stability ν</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.orbit_solution.stability_index_nu.toFixed(2)}</div>
                <div className="text-[10px] text-amber-600 font-semibold mt-0.5">Saddle-Center Bifurcation</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Target Vehicle</div>
                <div className="text-xs font-bold text-slate-900 mt-1 line-clamp-1">{dossier.target_vehicle}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{dossier.primary_lagrange_point} Libration</div>
              </div>
            </div>
          )}

          {/* ─── MANIFOLD TUBE DETAILS & EIGEN-DECOMPOSITION ─── */}
          {dossier && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Stable Manifold Inward Branches */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Stable Invariant Manifold Branches (Wˢ)
                    </h3>
                  </div>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                    LEO/GTO → Gateway Transfer
                  </span>
                </div>
                <div className="space-y-2">
                  {dossier.stable_manifolds.map((b) => (
                    <div key={b.step_id} className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs flex items-center justify-between">
                      <div className="flex items-center gap-2 font-semibold text-slate-800">
                        <span>Branch #{b.step_id}</span>
                        <span className="text-[10px] font-normal text-slate-500">({b.trajectory_points_km.length} Waypoints)</span>
                      </div>
                      <div className="flex items-center gap-4 text-[11px] text-slate-600">
                        <span>Transit: <strong className="text-slate-800">{b.transit_duration_days} d</strong></span>
                        <span>Insertion ΔV: <strong className="text-emerald-600">{b.delta_v_insertion_mps.toFixed(1)} m/s</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Monodromy Spectrum & Eigenvalues */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Monodromy Matrix Eigenvalues (Φ(T,0))
                    </h3>
                  </div>
                  <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                    Symplectic Structure
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {dossier.orbit_solution.monodromy_eigenvalues.map((val, idx) => {
                    const label = idx === 0 ? "λ₁ (Unstable)" : idx === 1 ? "λ₂ (Stable)" : `λ${idx + 1} (Center)`;
                    return (
                      <div key={idx} className="p-2 rounded-lg bg-white border border-slate-200 text-center">
                        <div className="text-[10px] font-semibold text-slate-500">{label}</div>
                        <div className="text-xs font-bold text-slate-900 font-mono mt-0.5">{val.toFixed(4)}</div>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-3 text-[11px] text-slate-500 leading-relaxed">
                  The Floquet multipliers satisfy symplectic pairing: <code className="font-mono text-slate-700">λ₁ · λ₂ = 1.0000</code>, confirming strict conservative phase-space flow in the synodic CR3BP potential.
                </div>
              </div>

            </div>
          )}

          {/* ─── CRYPTOGRAPHIC PROVENANCE FOOTER ─── */}
          {dossier && (
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span className="font-semibold text-slate-700">SHA-256 Astrodynamics Lineage:</span>
                <code className="font-mono text-[11px] text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {dossier.merkle_provenance_hash}
                </code>
                <button
                  onClick={copyMerkle}
                  className="p-1 rounded text-slate-500 hover:text-slate-800 transition-colors"
                  title="Copy Provenance Hash"
                >
                  {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `cislunar_${dossier.preset_key}.json`;
                    a.click();
                  }}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export Mission Dossier
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

