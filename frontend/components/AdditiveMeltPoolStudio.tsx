"use client";

import React, { useState, useEffect } from "react";
import {
  Flame,
  Zap,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Sliders,
  Play,
  RotateCcw,
  X,
  Sparkles,
  Layers,
  Thermometer,
  ShieldCheck,
} from "lucide-react";

interface AdditiveMeltPoolStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

interface MeltPoolResult {
  alloy: string;
  laser_power_w: number;
  scan_speed_mps: number;
  dimensions: {
    depth_um: number;
    width_um: number;
    length_um: number;
    aspect_ratio_d_w: number;
    length_to_width_ratio: number;
  };
  thermal_field: {
    peak_temperature_k: number;
    peak_temperature_c: number;
    melting_point_c: number;
    boiling_point_c: number;
    marangoni_velocity_mps: number;
    marangoni_stress_kpa: number;
  };
  process_window: {
    regime: string;
    defect_description: string;
    normalized_enthalpy: number;
    volumetric_energy_density_j_per_mm3: number;
    relative_density_prediction_percent: number;
  };
}

interface TelemetryPoint {
  time_us: number;
  position_x_mm: number;
  laser_power_w: number;
  pyrometer_temp_c: number;
  melt_depth_um: number;
  melt_width_um: number;
  regime: string;
  is_overhang_zone: boolean;
}

interface PyrometerResult {
  simulation_id: string;
  alloy: string;
  process_settings: {
    nominal_laser_power_w: number;
    scan_speed_mps: number;
    feedforward_active: boolean;
    overhang_injected: boolean;
  };
  summary: {
    overall_quality_score_percent: number;
    conduction_mode_percent: number;
    keyhole_risk_percent: number;
    lack_of_fusion_risk_percent: number;
  };
  telemetry: TelemetryPoint[];
}

export default function AdditiveMeltPoolStudio({
  isOpen,
  onClose,
  apiBase,
}: AdditiveMeltPoolStudioProps) {
  const [alloyKey, setAlloyKey] = useState<string>("TI_6AL_4V");
  const [laserPower, setLaserPower] = useState<number>(280);
  const [scanSpeed, setScanSpeed] = useState<number>(1.2);
  const [beamRadius, setBeamRadius] = useState<number>(50);
  const [layerThickness, setLayerThickness] = useState<number>(40);

  const [enableFeedforward, setEnableFeedforward] = useState<boolean>(true);
  const [injectOverhang, setInjectOverhang] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);

  const [meltResult, setMeltResult] = useState<MeltPoolResult | null>(null);
  const [pyroResult, setPyroResult] = useState<PyrometerResult | null>(null);

  // Preset scenarios
  const applyPreset = (preset: string) => {
    if (preset === "conduction_optimal") {
      setAlloyKey("TI_6AL_4V");
      setLaserPower(280);
      setScanSpeed(1.2);
      setBeamRadius(50);
      setLayerThickness(40);
      setEnableFeedforward(true);
      setInjectOverhang(true);
    } else if (preset === "inconel_overhang") {
      setAlloyKey("INCONEL_718");
      setLaserPower(300);
      setScanSpeed(1.0);
      setBeamRadius(55);
      setLayerThickness(40);
      setEnableFeedforward(true);
      setInjectOverhang(true);
    } else if (preset === "keyhole_porosity") {
      setAlloyKey("TI_6AL_4V");
      setLaserPower(550);
      setScanSpeed(0.4);
      setBeamRadius(45);
      setLayerThickness(40);
      setEnableFeedforward(false);
      setInjectOverhang(false);
    } else if (preset === "lack_of_fusion") {
      setAlloyKey("TI_6AL_4V");
      setLaserPower(110);
      setScanSpeed(2.8);
      setBeamRadius(65);
      setLayerThickness(60);
      setEnableFeedforward(false);
      setInjectOverhang(false);
    }
  };

  const runSimulation = async () => {
    setLoading(true);
    try {
      // 1. Solve static melt-pool
      const solveRes = await fetch(`${apiBase}/api/v1/lpbf-meltpool/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          laser_power_w: laserPower,
          scan_speed_mps: scanSpeed,
          beam_radius_um: beamRadius,
          layer_thickness_um: layerThickness,
          alloy_key: alloyKey,
        }),
      });
      const solveJson = await solveRes.json();
      if (solveJson.status === "success") {
        setMeltResult(solveJson.data);
      }

      // 2. Solve pyrometer track
      const pyroRes = await fetch(`${apiBase}/api/v1/lpbf-meltpool/pyrometer-scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alloy_key: alloyKey,
          nominal_laser_power_w: laserPower,
          scan_speed_mps: scanSpeed,
          enable_feedforward_control: enableFeedforward,
          inject_overhang_geometry: injectOverhang,
          scan_track_length_mm: 20.0,
        }),
      });
      const pyroJson = await pyroRes.json();
      if (pyroJson.status === "success") {
        setPyroResult(pyroJson.data);
      }
    } catch (e) {
      console.error("Melt-pool simulation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !meltResult) {
      runSimulation();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const regime = meltResult?.process_window.regime || "OPTIMAL_CONDUCTION";
  const isOptimal = regime === "OPTIMAL_CONDUCTION";
  const isKeyhole = regime === "KEYHOLE_POROSITY";
  const isLof = regime === "LACK_OF_FUSION";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden text-slate-800">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  In-Situ LPBF Melt-Pool PINN Digital Twin
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">
                  Stage 32
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-100 text-slate-700">
                  Rosenthal 3D + 100 kHz Pyrometry
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Physics-informed thermal field, Marangoni thermocapillary flow & coaxial closed-loop feedforward adaptation
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
              onClick={() => applyPreset("conduction_optimal")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition"
            >
              Ti-6Al-4V Optimal Conduction
            </button>
            <button
              onClick={() => applyPreset("inconel_overhang")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition"
            >
              Inconel 718 Overhang Feedforward
            </button>
            <button
              onClick={() => applyPreset("keyhole_porosity")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition"
            >
              Trigger Keyhole Porosity
            </button>
            <button
              onClick={() => applyPreset("lack_of_fusion")}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition"
            >
              Trigger Lack of Fusion
            </button>
          </div>

          {/* Control Bar */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Alloy Material
              </label>
              <select
                value={alloyKey}
                onChange={(e) => setAlloyKey(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="TI_6AL_4V">Ti-6Al-4V (Aerospace Titanium)</option>
                <option value="INCONEL_718">Inconel 718 (Turbine Superalloy)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Laser Power</span>
                <span className="text-slate-500">{laserPower} W</span>
              </div>
              <input
                type="range"
                min={80}
                max={600}
                step={10}
                value={laserPower}
                onChange={(e) => setLaserPower(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Scan Speed</span>
                <span className="text-slate-500">{scanSpeed.toFixed(2)} m/s</span>
              </div>
              <input
                type="range"
                min={0.2}
                max={3.0}
                step={0.1}
                value={scanSpeed}
                onChange={(e) => setScanSpeed(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Beam Radius</span>
                <span className="text-slate-500">{beamRadius} μm</span>
              </div>
              <input
                type="range"
                min={30}
                max={120}
                step={5}
                value={beamRadius}
                onChange={(e) => setBeamRadius(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={runSimulation}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition shadow-sm disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Activity className="w-3.5 h-3.5 animate-spin" />
                    <span>Solving PINN...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Simulation</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Regime Status Banner */}
          {meltResult && (
            <div
              className={`p-4 rounded-xl border flex items-center justify-between ${
                isOptimal
                  ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                  : isKeyhole
                  ? "bg-rose-50 border-rose-200 text-rose-900"
                  : "bg-amber-50 border-amber-200 text-amber-900"
              }`}
            >
              <div className="flex items-center gap-3">
                {isOptimal ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-rose-600" />
                )}
                <div>
                  <h4 className="text-sm font-bold">
                    Regime: {regime.replace(/_/g, " ")}
                  </h4>
                  <p className="text-xs opacity-90">
                    {meltResult.process_window.defect_description}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs uppercase tracking-wide opacity-75 font-semibold block">
                  Predicted Relative Density
                </span>
                <span className="text-lg font-black">
                  {meltResult.process_window.relative_density_prediction_percent.toFixed(1)}%
                </span>
              </div>
            </div>
          )}

          {/* Melt Pool Cross Section & Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* SVG Visualizer */}
            <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900 text-white flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-bold tracking-wide uppercase text-slate-300">
                    3D Rosenthal Thermal Field & Marangoni Convection Vector
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block"></span> Vapor Keyhole Core
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span> Liquidus Isotherm
                  </span>
                </div>
              </div>

              {/* Dynamic SVG Cross Section */}
              <div className="w-full h-64 bg-slate-950/60 rounded-lg p-2 relative flex items-center justify-center overflow-hidden border border-slate-800">
                {meltResult ? (
                  <svg className="w-full h-full" viewBox="0 0 500 220">
                    {/* Powder layer boundary */}
                    <rect x="20" y="40" width="460" height="25" fill="#334155" opacity="0.4" />
                    <line x1="20" y1="65" x2="480" y2="65" stroke="#64748b" strokeDasharray="3 3" strokeWidth="1" />
                    <text x="25" y="58" fill="#94a3b8" fontSize="10">Powder Layer ({layerThickness} μm)</text>

                    {/* Substrate line */}
                    <text x="25" y="80" fill="#64748b" fontSize="10">Solid Substrate</text>

                    {/* Incident Laser Beam */}
                    <polygon
                      points="230,0 270,0 252,65 248,65"
                      fill="url(#laserGrad)"
                      opacity="0.85"
                    />

                    {/* Melt Pool Profile */}
                    {(() => {
                      const scaleW = Math.min(180, (meltResult.dimensions.width_um / 200) * 140);
                      const scaleD = Math.min(120, (meltResult.dimensions.depth_um / 150) * 100);
                      const cx = 250;
                      const cy = 65;

                      return (
                        <g>
                          {/* Liquid Melt Pool Ellipsoid */}
                          <path
                            d={`M ${cx - scaleW} ${cy} C ${cx - scaleW} ${cy + scaleD * 1.1}, ${cx + scaleW} ${cy + scaleD * 1.1}, ${cx + scaleW} ${cy} Z`}
                            fill="url(#meltGrad)"
                            stroke={isOptimal ? "#10b981" : isKeyhole ? "#f43f5e" : "#f59e0b"}
                            strokeWidth="2"
                          />

                          {/* Keyhole depression if high power */}
                          {isKeyhole && (
                            <path
                              d={`M ${cx - 20} ${cy} Q ${cx} ${cy + scaleD * 0.9} ${cx + 20} ${cy} Z`}
                              fill="#1e1b4b"
                              stroke="#ec4899"
                              strokeWidth="1.5"
                            />
                          )}

                          {/* Marangoni Flow Arrows */}
                          <line x1={cx - 15} y1={cy + 15} x2={cx - scaleW * 0.7} y2={cy + 10} stroke="#38bdf8" strokeWidth="2" markerEnd="url(#arrow)" />
                          <line x1={cx + 15} y1={cy + 15} x2={cx + scaleW * 0.7} y2={cy + 10} stroke="#38bdf8" strokeWidth="2" markerEnd="url(#arrow)" />

                          {/* Dimension Annotations */}
                          <line x1={cx - scaleW} y1={cy - 10} x2={cx + scaleW} y2={cy - 10} stroke="#38bdf8" strokeWidth="1" />
                          <text x={cx} y={cy - 14} fill="#38bdf8" fontSize="10" textAnchor="middle">
                            Width: {meltResult.dimensions.width_um} μm
                          </text>

                          <line x1={cx + scaleW + 15} y1={cy} x2={cx + scaleW + 15} y2={cy + scaleD} stroke="#f59e0b" strokeWidth="1" />
                          <text x={cx + scaleW + 20} y={cy + scaleD / 2} fill="#f59e0b" fontSize="10" alignmentBaseline="middle">
                            Depth: {meltResult.dimensions.depth_um} μm
                          </text>
                        </g>
                      );
                    })()}

                    {/* Laser gradient definition */}
                    <defs>
                      <linearGradient id="laserGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                        <stop offset="100%" stopColor="#f43f5e" stopOpacity="1" />
                      </linearGradient>
                      <linearGradient id="meltGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.9" />
                        <stop offset="60%" stopColor="#ef4444" stopOpacity="0.75" />
                        <stop offset="100%" stopColor="#881337" stopOpacity="0.6" />
                      </linearGradient>
                    </defs>
                  </svg>
                ) : (
                  <span className="text-xs text-slate-500">Run simulation to visualize melt pool cross-section</span>
                )}
              </div>

              {/* Bottom live stats */}
              <div className="flex items-center justify-between text-xs mt-3 pt-3 border-t border-slate-800 text-slate-400">
                <span>Marangoni Surface Velocity: <b className="text-white">{meltResult?.thermal_field.marangoni_velocity_mps ?? "--"} m/s</b></span>
                <span>Aspect Ratio (D/W): <b className="text-white">{meltResult?.dimensions.aspect_ratio_d_w ?? "--"}</b></span>
                <span>Length/Width: <b className="text-white">{meltResult?.dimensions.length_to_width_ratio ?? "--"}</b></span>
              </div>
            </div>

            {/* Thermal & Physical Parameters */}
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-2">
                  <Thermometer className="w-4 h-4 text-blue-600" />
                  Thermal Field Solutions
                </h4>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Peak Temperature</span>
                    <span className="font-bold text-slate-900">
                      {meltResult?.thermal_field.peak_temperature_c} °C ({meltResult?.thermal_field.peak_temperature_k} K)
                    </span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Melting Point (T_melt)</span>
                    <span className="font-semibold text-slate-700">{meltResult?.thermal_field.melting_point_c} °C</span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Boiling Point (T_boil)</span>
                    <span className="font-semibold text-slate-700">{meltResult?.thermal_field.boiling_point_c} °C</span>
                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Thermocapillary Stress</span>
                    <span className="font-semibold text-slate-700">{meltResult?.thermal_field.marangoni_stress_kpa} kPa</span>
                  </div>

                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Normalized Enthalpy (β)</span>
                    <span className="font-bold text-slate-900">{meltResult?.process_window.normalized_enthalpy}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 space-y-2 text-xs text-blue-900">
                <div className="flex items-center gap-2 font-bold">
                  <ShieldCheck className="w-4 h-4 text-blue-600" />
                  Feedforward Pyrometer Controls
                </div>
                <label className="flex items-center gap-2 cursor-pointer mt-2">
                  <input
                    type="checkbox"
                    checked={enableFeedforward}
                    onChange={(e) => setEnableFeedforward(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span>Active Feedforward Laser Modulation</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={injectOverhang}
                    onChange={(e) => setInjectOverhang(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                  <span>Inject Thin-Wall / Overhang Geometry (8-14 mm)</span>
                </label>
              </div>
            </div>
          </div>

          {/* 100 kHz Pyrometer Telemetry Chart */}
          {pyroResult && pyroResult.telemetry.length > 0 && (
            <div className="p-5 rounded-xl bg-white border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-600" />
                    100 kHz Coaxial Pyrometer Telemetry & Laser Power Modulation
                  </h4>
                  <p className="text-xs text-slate-500">
                    Real-time temperature feedback along scan track. Blue shaded band represents simulated overhang region.
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs font-medium">
                  <span className="text-emerald-600">Conduction: {pyroResult.summary.conduction_mode_percent}%</span>
                  <span className="text-rose-600">Keyhole Risk: {pyroResult.summary.keyhole_risk_percent}%</span>
                  <span className="text-amber-600">LOF Risk: {pyroResult.summary.lack_of_fusion_risk_percent}%</span>
                </div>
              </div>

              {/* Chart SVG */}
              <div className="w-full h-44 bg-slate-50 rounded-lg p-2 border border-slate-200 relative">
                <svg className="w-full h-full" viewBox="0 0 600 120" preserveAspectRatio="none">
                  {/* Overhang region highlight (x=8 to 14 mm -> 40% to 70% of 600) */}
                  {injectOverhang && (
                    <rect x="240" y="0" width="180" height="120" fill="#fef3c7" opacity="0.6" />
                  )}

                  {/* Temperature trace (red) */}
                  {(() => {
                    const pts = pyroResult.telemetry;
                    const maxT = 3200;
                    const minT = 1600;
                    const poly = pts
                      .map((p, idx) => {
                        const x = (idx / (pts.length - 1)) * 600;
                        const y = 120 - ((p.pyrometer_temp_c - minT) / (maxT - minT)) * 110;
                        return `${x},${Math.max(5, Math.min(115, y))}`;
                      })
                      .join(" ");

                    return <polyline fill="none" stroke="#ef4444" strokeWidth="2" points={poly} />;
                  })()}

                  {/* Laser Power trace (blue) */}
                  {(() => {
                    const pts = pyroResult.telemetry;
                    const maxP = 600;
                    const minP = 100;
                    const poly = pts
                      .map((p, idx) => {
                        const x = (idx / (pts.length - 1)) * 600;
                        const y = 120 - ((p.laser_power_w - minP) / (maxP - minP)) * 90;
                        return `${x},${Math.max(10, Math.min(110, y))}`;
                      })
                      .join(" ");

                    return (
                      <polyline
                        fill="none"
                        stroke="#2563eb"
                        strokeWidth="2"
                        strokeDasharray="4 2"
                        points={poly}
                      />
                    );
                  })()}
                </svg>

                <div className="absolute bottom-2 left-4 flex items-center gap-4 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-0.5 bg-red-500 inline-block"></span> Pyrometer Temperature (°C)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-0.5 bg-blue-600 inline-block"></span> Adapted Laser Power (W)
                  </span>
                  {injectOverhang && (
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-amber-200 inline-block border border-amber-300"></span> Overhang Zone (Lower Dissipation)
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Rosenthal Point Source 3D Heat Conduction • King Normalized Enthalpy • Marangoni Convection</span>
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
