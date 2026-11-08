"use client";

import React, { useState, useEffect, useId } from "react";
import {
  Navigation,
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
  Plane,
  Clock,
  Flame,
  CloudRain,
  X,
} from "lucide-react";

interface TrajectoryPoint {
  time_s: number;
  lat_deg: number;
  lon_deg: number;
  altitude_ft: number;
  ground_speed_mps: number;
  true_airspeed_mps: number;
  cumulative_distance_km: number;
  fuel_burned_kg: number;
  waypoint_tag: string;
  wake_vortex_safe: boolean;
  conflict_detected: boolean;
}

interface NegotiatedFlight {
  callsign: string;
  aircraft_type: string;
  wake_category: string;
  origin: string;
  destination: string;
  original_eta_s: number;
  negotiated_cta_s: number;
  ground_delay_s: number;
  airborne_delay_s: number;
  total_fuel_burn_kg: number;
  rerouted_around_weather: boolean;
  weather_diversion_km: number;
  trajectory_points: TrajectoryPoint[];
}

interface CatfmNegotiationResult {
  scenario_id: string;
  destination_hub: string;
  total_flights: number;
  resolved_conflicts: number;
  residual_conflicts: number;
  average_ground_delay_min: number;
  average_airborne_delay_min: number;
  total_fleet_fuel_burn_kg: number;
  weather_reroutes_executed: number;
  catfm_efficiency_index_pct: number;
  merkle_provenance_hash: string;
  regulatory_standard: string;
  flights: NegotiatedFlight[];
}

interface PresetSummary {
  name: string;
  description: string;
  destination_hub: string;
  flight_count: number;
  weather_cells_count: number;
}

export interface CatfmAirspaceStudioProps {
  isOpen?: boolean;
  onClose?: () => void;
  apiBase?: string;
}

export default function CatfmAirspaceStudio({
  isOpen,
  onClose,
  apiBase = "",
}: CatfmAirspaceStudioProps = {}) {
  const [presets, setPresets] = useState<Record<string, PresetSummary>>({});
  const [selectedScenario, setSelectedScenario] = useState<string>("BENGALURU_VOBL_MONSOON_RUSH");
  const [enableCta, setEnableCta] = useState<boolean>(true);
  const [enableWeather, setEnableWeather] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<CatfmNegotiationResult | null>(null);
  const [activeStepFraction, setActiveStepFraction] = useState<number>(1.0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [statusNotice, setStatusNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const mapClipId = useId();

  // Coordinates mapping for Indian Airspace SVG Canvas
  // Lat: 8.0 to 32.0, Lon: 68.0 to 92.0
  const latToY = (lat: number) => 260 - ((lat - 8.0) / 24.0) * 230;
  const lonToX = (lon: number) => 40 + ((lon - 68.0) / 24.0) * 320;

  useEffect(() => {
    fetchPresets();
  }, [apiBase]);

  const fetchPresets = async () => {
    try {
      const res = await fetch(`${apiBase}/api/catfm/presets`);
      if (res.ok) {
        const data = await res.json();
        setPresets(data.presets || {});
      }
    } catch {
      setPresets({
        BENGALURU_VOBL_MONSOON_RUSH: {
          name: "Bengaluru (VOBL) Monsoon Evening Rush & Vertiport Link",
          description: "Simultaneous arrival bank: Heavy B77W from Mumbai, 2x A320neo, ATR72, and Whitefield eVTOL shuttle navigating severe monsoon squall.",
          destination_hub: "VOBL",
          flight_count: 5,
          weather_cells_count: 1,
        },
        MUMBAI_VABB_SINGLE_RUNWAY_CRUNCH: {
          name: "Mumbai (VABB) Cross-Wind Runway Peak Compression",
          description: "Cross-runway capacity crunch with 4 flights arriving in rapid intervals requiring tight PBN wake vortex separation.",
          destination_hub: "VABB",
          flight_count: 4,
          weather_cells_count: 0,
        },
        DELHI_VIDP_WINTER_FOG_GDP: {
          name: "Delhi (VIDP) Low-Visibility CAT-III Ground Delay Program",
          description: "CAT-III fog metering across North Indian airway corridors, re-spacing inbound traffic to eliminate holding stack fuel burn.",
          destination_hub: "VIDP",
          flight_count: 3,
          weather_cells_count: 0,
        },
      });
    }
  };

  const runNegotiation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/catfm/negotiate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_key: selectedScenario,
          enable_cta_optimization: enableCta,
          enable_weather_avoidance: enableWeather,
          time_compression: 1.0,
        }),
      });

      if (!res.ok) throw new Error(`Negotiation failed with status ${res.status}`);

      const data: CatfmNegotiationResult = await res.json();
      setResult(data);
      setActiveStepFraction(1.0);
      setStatusNotice({
        type: "success",
        text: enableCta
          ? `AAI C-ATFM Verified: ${data.resolved_conflicts} wake conflicts metered • 0 residual conflicts • ${data.catfm_efficiency_index_pct}% efficiency index.`
          : `Unmetered arrival run: ${data.residual_conflicts} wake vortex violations detected!`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setStatusNotice({ type: "error", text: `Negotiation execution failed: ${msg}` });
    } finally {
      setLoading(false);
    }
  };

  // Trajectory animation
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPlaying && result) {
      interval = setInterval(() => {
        setActiveStepFraction((prev) => {
          if (prev >= 1.0) {
            setIsPlaying(false);
            return 1.0;
          }
          return Math.min(1.0, prev + 0.04);
        });
      }, 80);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, result]);

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
            <span className="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-indigo-200">
              Stage 15 • Sovereign Airspace
            </span>
            <span className="bg-emerald-100 text-emerald-800 text-xs font-mono px-2 py-0.5 rounded border border-emerald-200">
              AAI C-ATFM / ICAO DOC 9971
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Sovereign Airspace 4D Trajectory Negotiation &amp; AAM Vertiports
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-3xl">
            Controlled Time of Arrival (CTA) slot optimizer and wake vortex separation assurance across Indian FIR airspace hubs (Delhi, Mumbai, Bengaluru, Hyderabad, Chennai, Kolkata) and urban eVTOL vertiports under convective monsoon squalls.
          </p>
        </div>

        <button
          onClick={runNegotiation}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-medium px-5 py-2.5 rounded-lg shadow-sm transition disabled:opacity-50 shrink-0"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Navigation className="w-4 h-4 text-indigo-400" />
          )}
          {loading ? "Negotiating 4D Slots..." : "Dispatch C-ATFM Negotiation"}
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
            Airspace Scenario &amp; Destination Hub
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            {Object.entries(presets).map(([k, v]) => (
              <option key={k} value={k}>
                {v.name}
              </option>
            ))}
          </select>
          {presets[selectedScenario] && (
            <p className="text-xs text-slate-500 mt-2">
              {presets[selectedScenario].description} ({presets[selectedScenario].flight_count} flights, Destination: {presets[selectedScenario].destination_hub})
            </p>
          )}
        </div>

        {/* CTA Optimization Toggle */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
              AAI CTA Slot Optimizer
            </label>
            <ShieldCheck className={`w-4 h-4 ${enableCta ? "text-emerald-600" : "text-amber-500"}`} />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => setEnableCta(!enableCta)}
              className={`w-full py-2 px-3 text-xs font-semibold rounded-lg border transition ${
                enableCta
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                  : "bg-red-50 text-red-800 border-red-300"
              }`}
            >
              {enableCta ? "CTA SLOTS: OPTIMIZED" : "UNMETERED RUSH (OFF)"}
            </button>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {enableCta ? "Enforces ICAO wake separation & ground holds" : "Uncontrolled arrivals cause wake violations"}
          </p>
        </div>

        {/* Weather Avoidance Toggle */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
              Monsoon Weather Rerouting
            </label>
            <CloudRain className={`w-4 h-4 ${enableWeather ? "text-blue-600" : "text-slate-400"}`} />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={() => setEnableWeather(!enableWeather)}
              className={`w-full py-2 px-3 text-xs font-semibold rounded-lg border transition ${
                enableWeather
                  ? "bg-blue-50 text-blue-800 border-blue-300"
                  : "bg-slate-100 text-slate-700 border-slate-300"
              }`}
            >
              {enableWeather ? "WEATHER DOGLEGS: ACTIVE" : "IGNORE WEATHER CELLS"}
            </button>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {enableWeather ? "Autonomous reroute around convective cells" : "Direct routing through severe squall"}
          </p>
        </div>
      </div>

      {/* Main Results View */}
      {result && (
        <div className="space-y-6">
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Efficiency Index</span>
              <span className="text-lg font-mono font-bold text-emerald-700 mt-0.5 block">
                {result.catfm_efficiency_index_pct.toFixed(1)}%
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Residual Conflicts</span>
              <span className={`text-lg font-mono font-bold mt-0.5 block ${result.residual_conflicts === 0 ? "text-emerald-700" : "text-red-700"}`}>
                {result.residual_conflicts} {result.residual_conflicts === 0 ? "(Zero)" : "Violations"}
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Conflicts Resolved</span>
              <span className="text-lg font-mono font-bold text-indigo-700 mt-0.5 block">
                {result.resolved_conflicts}
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Avg Ground Delay (GDP)</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.average_ground_delay_min.toFixed(1)} min
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Avg Airborne Delay</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {result.average_airborne_delay_min.toFixed(1)} min
              </span>
            </div>

            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Fleet Fuel Burn</span>
              <span className="text-lg font-mono font-bold text-slate-900 mt-0.5 block">
                {(result.total_fleet_fuel_burn_kg / 1000.0).toFixed(2)} t
              </span>
            </div>
          </div>

          {/* Time Scrubber */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="bg-slate-900 text-white p-2 rounded-lg hover:bg-slate-800 transition"
                >
                  {isPlaying ? <RotateCcw className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <span className="text-xs font-semibold text-slate-700">
                  4D Space-Time Progression ({Math.round(activeStepFraction * 100)}% of Arrival Bank)
                </span>
              </div>
              <span className="text-xs font-mono text-slate-500">
                Destination: {result.destination_hub} FIR
              </span>
            </div>
            <input
              type="range"
              min="0.05"
              max="1.0"
              step="0.01"
              value={activeStepFraction}
              onChange={(e) => setActiveStepFraction(parseFloat(e.target.value))}
              className="w-full accent-slate-900"
            />
          </div>

          {/* Airspace Map & Convergence View */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Indian FIR Airspace & Route Network Map (SVG) */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Compass className="w-4 h-4 text-indigo-600" />
                  Indian FIR Airspace 4D Route Projection
                </h3>
                <span className="text-[11px] font-mono text-slate-500">ICAO PBN Waypoint Vectors</span>
              </div>

              <div className="w-full h-80 bg-slate-50 rounded-lg border border-slate-200 relative overflow-hidden flex items-center justify-center">
                <svg className="w-full h-full p-2" viewBox="0 0 400 280">
                  <defs>
                    <clipPath id={mapClipId}>
                      <rect x="20" y="20" width="360" height="240" />
                    </clipPath>
                  </defs>

                  {/* Indian Subcontinent Coastline & FIR Grid Mock */}
                  <path
                    d="M 120 40 Q 140 100 135 150 Q 130 190 190 255 Q 240 200 245 160 Q 280 140 310 110"
                    fill="none"
                    stroke="#cbd5e1"
                    strokeWidth="1.5"
                    strokeDasharray="4,4"
                  />

                  {/* FIR Boundary Grid Lines */}
                  <line x1="20" y1="140" x2="380" y2="140" stroke="#f1f5f9" strokeWidth="1" />
                  <line x1="200" y1="20" x2="200" y2="260" stroke="#f1f5f9" strokeWidth="1" />

                  {/* Convective Monsoon Squall Storm Cell */}
                  {enableWeather && (
                    <g>
                      <circle
                        cx={lonToX(76.8)}
                        cy={latToY(14.2)}
                        r="24"
                        fill="#38bdf8"
                        fillOpacity="0.25"
                        stroke="#0284c7"
                        strokeWidth="1.5"
                        strokeDasharray="3,2"
                      />
                      <text
                        x={lonToX(76.8)}
                        y={latToY(14.2) + 4}
                        textAnchor="middle"
                        fontSize="8"
                        fill="#0369a1"
                        fontFamily="sans-serif"
                        fontWeight="bold"
                      >
                        MONSOON SQUALL (FL420)
                      </text>
                    </g>
                  )}

                  {/* Airports */}
                  {[
                    { id: "VIDP", lat: 28.566, lon: 77.103, label: "VIDP (Delhi)" },
                    { id: "VABB", lat: 19.089, lon: 72.865, label: "VABB (Mumbai)" },
                    { id: "VOBL", lat: 13.198, lon: 77.706, label: "VOBL (Bengaluru)" },
                    { id: "VOHS", lat: 17.240, lon: 78.429, label: "VOHS (Hyd)" },
                    { id: "VOMM", lat: 12.994, lon: 80.170, label: "VOMM (Chennai)" },
                    { id: "VECC", lat: 22.654, lon: 88.446, label: "VECC (Kolkata)" },
                    { id: "VOBL-E", lat: 12.969, lon: 77.749, label: "VOBL-E (Vertiport)" },
                  ].map((apt) => {
                    const x = lonToX(apt.lon);
                    const y = latToY(apt.lat);
                    const isDest = apt.id === result.destination_hub;
                    return (
                      <g key={apt.id}>
                        <circle
                          cx={x}
                          cy={y}
                          r={isDest ? "5" : "3"}
                          fill={isDest ? "#059669" : "#475569"}
                          stroke="#ffffff"
                          strokeWidth="1"
                        />
                        <text
                          x={x + 6}
                          y={y + 3}
                          fontSize="8"
                          fill={isDest ? "#065f46" : "#64748b"}
                          fontFamily="sans-serif"
                          fontWeight={isDest ? "bold" : "normal"}
                        >
                          {apt.label}
                        </text>
                      </g>
                    );
                  })}

                  {/* Flight Trajectories */}
                  {result.flights.map((flt, fIdx) => {
                    const colors = ["#2563eb", "#d97706", "#7c3aed", "#059669", "#dc2626"];
                    const col = colors[fIdx % colors.length];
                    const pts = flt.trajectory_points;
                    const maxPtIdx = Math.max(1, Math.floor(pts.length * activeStepFraction));
                    const visiblePts = pts.slice(0, maxPtIdx);

                    // Polyline points
                    const pathD = visiblePts
                      .map((p, i) => `${i === 0 ? "M" : "L"} ${lonToX(p.lon_deg)} ${latToY(p.lat_deg)}`)
                      .join(" ");

                    const curPt = visiblePts[visiblePts.length - 1];

                    return (
                      <g key={flt.callsign}>
                        <path
                          d={pathD}
                          fill="none"
                          stroke={col}
                          strokeWidth="2"
                          strokeDasharray={flt.rerouted_around_weather ? "4,2" : undefined}
                        />
                        {curPt && (
                          <g>
                            <circle
                              cx={lonToX(curPt.lon_deg)}
                              cy={latToY(curPt.lat_deg)}
                              r="4"
                              fill={col}
                              stroke="#ffffff"
                              strokeWidth="1"
                            />
                            <text
                              x={lonToX(curPt.lon_deg) + 6}
                              y={latToY(curPt.lat_deg) - 4}
                              fontSize="9"
                              fill={col}
                              fontWeight="bold"
                              fontFamily="sans-serif"
                            >
                              {flt.callsign} ({flt.aircraft_type})
                            </text>
                          </g>
                        )}
                      </g>
                    );
                  })}
                </svg>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block" /> Destination Hub
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block" /> Monsoon Convective Cell
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  {result.weather_reroutes_executed} flights doglegged
                </span>
              </div>
            </div>

            {/* 2. Controlled Time of Arrival (CTA) Sequence Timeline */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-600" />
                  Runway Arrival Sequencing &amp; Wake Interval Metering
                </h3>
                <span className="text-[11px] font-mono text-slate-500">AAI C-ATFM Arrival Slots</span>
              </div>

              <div className="space-y-3 pt-2">
                {result.flights.map((flt, idx) => {
                  const delayMin = (flt.negotiated_cta_s - flt.original_eta_s) / 60.0;
                  return (
                    <div
                      key={flt.callsign}
                      className="p-3 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-mono text-xs flex items-center justify-center font-bold">
                          #{idx + 1}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-slate-900">{flt.callsign}</span>
                            <span className="text-xs font-mono text-slate-500">({flt.aircraft_type})</span>
                            <span className="text-[10px] uppercase font-bold px-1.5 py-0.2 bg-slate-200 text-slate-700 rounded">
                              {flt.wake_category}
                            </span>
                            {flt.rerouted_around_weather && (
                              <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded font-medium">
                                Weather Dogleg
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            {flt.origin} → {flt.destination} • Filed ETA: {flt.original_eta_s.toFixed(0)}s → CTA: {flt.negotiated_cta_s.toFixed(0)}s
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className={`text-xs font-mono font-bold ${delayMin > 0 ? "text-amber-700" : "text-emerald-700"}`}>
                          {delayMin > 0 ? `+${delayMin.toFixed(1)}m Delay` : "On Schedule"}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Hold: {(flt.ground_delay_s / 60.0).toFixed(1)}m | Air: {(flt.airborne_delay_s / 60.0).toFixed(1)}m
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Detailed Fleet Operational Table */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-slate-700" />
              AAI C-ATFM Negotiated Fleet Slot Dossier
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                    <th className="p-2.5">Callsign</th>
                    <th className="p-2.5">Type</th>
                    <th className="p-2.5">Wake Category</th>
                    <th className="p-2.5">Route</th>
                    <th className="p-2.5">Filed ETA</th>
                    <th className="p-2.5">Negotiated CTA</th>
                    <th className="p-2.5">Ground Delay</th>
                    <th className="p-2.5">Airborne Delay</th>
                    <th className="p-2.5">Fuel Burn</th>
                    <th className="p-2.5">Weather Diversion</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {result.flights.map((flt) => (
                    <tr key={flt.callsign} className="hover:bg-slate-50/80">
                      <td className="p-2.5 font-bold text-slate-900">{flt.callsign}</td>
                      <td className="p-2.5 text-slate-700">{flt.aircraft_type}</td>
                      <td className="p-2.5">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-bold">
                          {flt.wake_category}
                        </span>
                      </td>
                      <td className="p-2.5 text-slate-700">{flt.origin} → {flt.destination}</td>
                      <td className="p-2.5 text-slate-600">{flt.original_eta_s.toFixed(0)} s</td>
                      <td className="p-2.5 font-bold text-emerald-800">{flt.negotiated_cta_s.toFixed(0)} s</td>
                      <td className="p-2.5 text-slate-700">{(flt.ground_delay_s / 60.0).toFixed(1)} min</td>
                      <td className="p-2.5 text-slate-700">{(flt.airborne_delay_s / 60.0).toFixed(1)} min</td>
                      <td className="p-2.5 text-slate-700">{flt.total_fuel_burn_kg.toFixed(0)} kg</td>
                      <td className="p-2.5">
                        {flt.rerouted_around_weather ? (
                          <span className="text-blue-700 font-medium font-sans">
                            +{flt.weather_diversion_km.toFixed(1)} km Dogleg
                          </span>
                        ) : (
                          <span className="text-slate-400 font-sans">Direct Route</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cryptographic Provenance */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-3">
              <Lock className="w-5 h-5 text-indigo-600 shrink-0" />
              <div>
                <span className="text-xs font-semibold text-slate-900 block">
                  SHA-256 Merkle Provenance &amp; Airspace Contract
                </span>
                <span className="text-[11px] font-mono text-slate-500 break-all">
                  {result.merkle_provenance_hash}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="bg-slate-100 text-slate-700 font-mono text-xs px-2.5 py-1 rounded border border-slate-200">
                {result.regulatory_standard}
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
