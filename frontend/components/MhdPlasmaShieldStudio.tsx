"use client";

import React, { useState, useEffect } from "react";
import {
  Zap,
  Radio,
  Flame,
  ShieldCheck,
  Activity,
  Download,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Layers,
  TrendingDown,
  RotateCcw,
  Sliders,
  Copy,
  Check,
} from "lucide-react";

interface TrajectorySweepPoint {
  mach_number: number;
  velocity_mps: number;
  stuart_number: number;
  heat_flux_baseline_mw_m2: number;
  heat_flux_mhd_mw_m2: number;
  heat_flux_reduction_pct: number;
  plasma_frequency_ghz: number;
  rf_attenuation_db: number;
  rf_blackout_mitigated: boolean;
  mhd_power_extracted_kw: number;
}

interface MHDMissionDossier {
  mission_id: string;
  preset_key: string;
  target_vehicle: string;
  nominal_rf_band: string;
  magnetic_coil_field_tesla: number;
  baseline_heat_flux_mw_m2: number;
  mitigated_heat_flux_mw_m2: number;
  heat_flux_reduction_pct: number;
  shock_standoff_extension_pct: number;
  rf_blackout_eliminated: boolean;
  rf_transmission_efficiency_pct: number;
  power_generated_kw: number;
  trajectory_profile: TrajectorySweepPoint[];
  merkle_provenance_hash: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

const MHD_PRESETS_META: Record<string, { label: string; vehicle: string; b_field: number; rf_band: string; desc: string }> = {
  ISRO_GAGANYAAN_MHD_REENTRY: {
    label: "ISRO Gaganyaan 1.25 T S-Band Shield",
    vehicle: "Gaganyaan Crewed Reentry Module",
    b_field: 1.25,
    rf_band: "S-Band (2.2 GHz)",
    desc: "Superconducting magnetic coil opens Whistler RF window, mitigating 4.5-min telemetry blackout and reducing TPS heat flux by 42%.",
  },
  HGV_SHAVIT_GLIDE_MACH20: {
    label: "Hypersonic Glide Vehicle 2.0 T Trim",
    vehicle: "Mach 20 Sovereign Glide Vehicle",
    b_field: 2.00,
    rf_band: "X-Band (8.4 GHz)",
    desc: "MHD boundary layer control and Lorentz aerodynamic trim without mechanical control surface thermal ablation.",
  },
  STARSHIP_SUPER_HEAVY_ENTRY_MACH25: {
    label: "Starship 1.8 T & 220 kW MHD Generator",
    vehicle: "Orbital Steel Reentry Vehicle",
    b_field: 1.80,
    rf_band: "Ka-Band (32.0 GHz)",
    desc: "Plasma deceleration shield protecting leeward steel structure and extracting 220 kW Faraday electrical power.",
  },
  VENUS_PROBE_MHD_MAGNETOPAUSE: {
    label: "Venus Hyper-Enthalpy 2.5 T Shield",
    vehicle: "Venus Deep Atmospheric Entry Probe",
    b_field: 2.50,
    rf_band: "X-Band (8.4 GHz)",
    desc: "Extreme 11.5 km/s entry into dense CO2 atmosphere, pushing the bow shock standoff away from extreme 24 MW/m² radiation.",
  },
};

export default function MhdPlasmaShieldStudio({ isOpen, onClose, apiBase }: Props) {
  const [selectedPreset, setSelectedPreset] = useState("ISRO_GAGANYAAN_MHD_REENTRY");
  const [magneticB, setMagneticB] = useState<number>(1.25);
  const [dossier, setDossier] = useState<MHDMissionDossier | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  const runSimulation = async (presetKey: string, bField: number) => {
    setLoading(true);
    try {
      const resp = await fetch(`${apiBase}/api/v1/mhd/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: presetKey,
          override_magnetic_field_tesla: bField,
        }),
      });
      if (resp.ok) {
        const data: MHDMissionDossier = await resp.json();
        setDossier(data);
      }
    } catch (err) {
      console.error("MHD shield simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !dossier) {
      runSimulation(selectedPreset, magneticB);
    }
  }, [isOpen]);

  const handlePresetChange = (key: string) => {
    setSelectedPreset(key);
    const meta = MHD_PRESETS_META[key];
    const newB = meta ? meta.b_field : 1.25;
    setMagneticB(newB);
    runSimulation(key, newB);
  };

  const copyMerkle = () => {
    if (!dossier) return;
    navigator.clipboard.writeText(dossier.merkle_provenance_hash);
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
            <div className="w-10 h-10 rounded-xl bg-cyan-50 border border-cyan-200 flex items-center justify-center text-cyan-600 shadow-sm">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-600 text-white">
                  Stage 23 Sovereign
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Lorentz J×B Shock Push
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Whistler RF Blackout Window
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">
                Magnetohydrodynamic (MHD) Hypersonic Plasma Shielding &amp; Blackout Mitigation
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => runSimulation(selectedPreset, magneticB)}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {loading ? "Solving Maxwell-NS..." : "Recompute MHD Shield"}
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
            {Object.entries(MHD_PRESETS_META).map(([key, meta]) => {
              const isSelected = selectedPreset === key;
              return (
                <button
                  key={key}
                  onClick={() => handlePresetChange(key)}
                  className={`p-3.5 rounded-xl text-left border transition-all ${
                    isSelected
                      ? "border-cyan-600 bg-cyan-50/50 shadow-sm ring-1 ring-cyan-600"
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-900">{meta.b_field} T Dipole</span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      {meta.rf_band.split(" ")[0]}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-slate-800 line-clamp-1">{meta.label}</div>
                  <div className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">{meta.desc}</div>
                </button>
              );
            })}
          </div>

          {/* Interactive B-Field Slider Bar */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Onboard Superconducting Magnetic Field B₀: <span className="text-cyan-600 font-bold">{magneticB.toFixed(2)} Tesla</span>
                </label>
                <input
                  type="range"
                  min={0.0}
                  max={3.0}
                  step={0.1}
                  value={magneticB}
                  onChange={(e) => setMagneticB(Number(e.target.value))}
                  onMouseUp={() => runSimulation(selectedPreset, magneticB)}
                  className="w-64 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-cyan-600"
                />
              </div>

              <div className="h-8 w-px bg-slate-200" />

              <div className="flex items-center gap-4 text-xs font-semibold text-slate-700">
                <span>Lorentz Force: <strong className="text-cyan-700 font-mono">F = j × B</strong></span>
                <span>Whistler Dispersion: <strong className="text-indigo-700 font-mono">ωce &gt; ωp</strong></span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 rounded-md text-xs font-bold font-mono ${
                dossier?.rf_blackout_eliminated ? "bg-emerald-100 text-emerald-800 border border-emerald-300" : "bg-rose-100 text-rose-800 border border-rose-300"
              }`}>
                {dossier?.rf_blackout_eliminated ? "✓ RF BLACKOUT MITIGATED" : "⚠ RF CUTOFF ACTIVE"}
              </span>
            </div>
          </div>

          {/* ─── PLASMA SHEATH & MAGNETIC DIPOLE VECTOR VISUALIZER ─── */}
          <div className="relative border border-slate-200 rounded-2xl bg-slate-950 overflow-hidden shadow-inner flex flex-col items-center">
            <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-200 border border-slate-800">
                Plasma Domain: Hypersonic Stagnation &amp; Forebody
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-cyan-400 border border-slate-800">
                MHD Shock Standoff: +{dossier?.shock_standoff_extension_pct || 0}% Extension
              </span>
            </div>

            <div className="absolute top-3 right-4 z-10 flex items-center gap-3 text-[11px] text-slate-300 font-mono bg-slate-900/90 px-3 py-1 rounded border border-slate-800">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" /> Baseline Shock (B=0)
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" /> MHD Pushed Shock
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> RF Whistler Channel
              </span>
            </div>

            <svg
              viewBox="0 0 840 400"
              className="w-full h-[380px] select-none"
              style={{ background: "radial-gradient(ellipse at center, #082f49 0%, #020617 100%)" }}
            >
              <defs>
                <radialGradient id="plasmaGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.8" />
                  <stop offset="60%" stopColor="#f97316" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#0f172a" stopOpacity="0.0" />
                </radialGradient>
                <linearGradient id="rfBeam" x1="0%" y1="50%" x2="100%" y2="50%">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.1" />
                </linearGradient>
              </defs>

              {/* Hypersonic Freestream Flow Vectors */}
              {[-120, -80, -40, 0, 40, 80, 120].map((yOff, i) => (
                <g key={`flow-${i}`}>
                  <line
                    x1="60"
                    y1={200 + yOff}
                    x2="220"
                    y2={200 + yOff}
                    stroke="#38bdf8"
                    strokeWidth="1.2"
                    strokeDasharray="4 4"
                    strokeOpacity="0.5"
                  />
                  <polygon
                    points={`225,${200 + yOff} 217,${197 + yOff} 217,${203 + yOff}`}
                    fill="#38bdf8"
                    opacity="0.6"
                  />
                </g>
              ))}

              {/* Baseline Shock Position (Without MHD) - Red dashed arc */}
              <path
                d="M 280 40 Q 230 200 280 360"
                fill="none"
                stroke="#f43f5e"
                strokeWidth="2.2"
                strokeDasharray="5 3"
                opacity="0.85"
              />
              <text x="260" y="55" fill="#f43f5e" fontSize="10" fontFamily="monospace" textAnchor="end">
                Baseline Shock δ₀
              </text>

              {/* MHD Pushed Shock Position (With Magnetic Field) - Cyan glowing arc */}
              {(() => {
                const extensionPush = Math.min(80, (dossier?.shock_standoff_extension_pct || 0) * 0.9);
                const pushX = 230 - extensionPush;
                return (
                  <path
                    d={`M 280 30 Q ${pushX} 200 280 370`}
                    fill="none"
                    stroke="#06b6d4"
                    strokeWidth="3.2"
                    strokeLinecap="round"
                    className="filter drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]"
                  />
                );
              })()}
              <text x="180" y="45" fill="#38bdf8" fontSize="11" fontFamily="monospace" fontWeight="bold">
                MHD Shock Standoff (+{dossier?.shock_standoff_extension_pct}%)
              </text>

              {/* Plasma Sheath Region */}
              <path
                d="M 280 40 Q 220 200 280 360 L 380 360 Q 330 200 380 40 Z"
                fill="url(#plasmaGlow)"
              />

              {/* Magnetic Dipole Field Lines (B-field) */}
              {[-110, -70, -35, 35, 70, 110].map((rVal, idx) => (
                <path
                  key={`mag-${idx}`}
                  d={`M 400 200 C ${300 - Math.abs(rVal) * 0.8} ${200 + rVal * 1.8}, ${310 - Math.abs(rVal) * 0.8} ${200 + rVal * 0.8}, 400 200`}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1.2"
                  strokeOpacity="0.45"
                  strokeDasharray="3 2"
                />
              ))}

              {/* Capsule Blunt Body Nose (Heatshield) */}
              <path
                d="M 370 70 Q 320 200 370 330 L 520 300 L 520 100 Z"
                fill="#1e293b"
                stroke="#64748b"
                strokeWidth="2.5"
              />
              <circle cx="370" cy="200" r="14" fill="#0284c7" stroke="#38bdf8" strokeWidth="2" />
              <text x="370" y="204" fill="#ffffff" fontSize="9" textAnchor="middle" fontWeight="bold">
                B₀ Coil
              </text>

              {/* RF Antenna & Whistler Window Beam */}
              <rect x="420" y="105" width="16" height="8" fill="#10b981" rx="2" />
              <path
                d="M 436 109 L 800 60 L 800 130 Z"
                fill="url(#rfBeam)"
              />
              <text x="600" y="85" fill="#34d399" fontSize="11" fontFamily="monospace" fontWeight="bold">
                Whistler Mode RF Telemetry Link (Active)
              </text>

              {/* Faraday Power Extraction Indicator */}
              <g transform="translate(560, 260)">
                <rect width="180" height="50" rx="8" fill="rgba(15, 23, 42, 0.85)" stroke="#0284c7" strokeWidth="1" />
                <text x="14" y="22" fill="#94a3b8" fontSize="10" fontFamily="sans-serif">
                  Faraday MHD Power:
                </text>
                <text x="14" y="42" fill="#38bdf8" fontSize="16" fontFamily="monospace" fontWeight="bold">
                  {dossier?.power_generated_kw.toFixed(1)} kW
                </text>
              </g>
            </svg>
          </div>

          {/* ─── KPI TELEMETRY DECK ─── */}
          {dossier && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Heat Flux Reduction</div>
                <div className="text-base font-bold text-emerald-600 mt-0.5 flex items-center gap-1">
                  <TrendingDown className="w-4 h-4" /> {dossier.heat_flux_reduction_pct.toFixed(1)}%
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Bush-Kemp-Petschek</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Mitigated Heat Flux</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.mitigated_heat_flux_mw_m2.toFixed(3)} MW/m²</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Base: {dossier.baseline_heat_flux_mw_m2.toFixed(3)} MW/m²</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Shock Standoff Extension</div>
                <div className="text-base font-bold text-cyan-600 mt-0.5">+{dossier.shock_standoff_extension_pct.toFixed(1)}%</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Lorentz J×B Standoff</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">RF Transmission</div>
                <div className="text-base font-bold text-emerald-600 mt-0.5">{dossier.rf_transmission_efficiency_pct.toFixed(1)}%</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{dossier.nominal_rf_band.split(" ")[0]} Link Active</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Faraday Generator</div>
                <div className="text-base font-bold text-indigo-600 mt-0.5">{dossier.power_generated_kw.toFixed(1)} kW</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Auxiliary Avionics Power</div>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Magnetic Field B₀</div>
                <div className="text-base font-bold text-slate-900 mt-0.5">{dossier.magnetic_coil_field_tesla.toFixed(2)} T</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Superconducting Coil</div>
              </div>
            </div>
          )}

          {/* ─── MACH SWEEP TRAJECTORY TABLE ─── */}
          {dossier && (
            <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-cyan-600" />
                  MHD Plasma Sheath &amp; RF Attenuation Profile Across Reentry Mach Numbers
                </h3>
                <span className="text-[11px] font-mono text-slate-500">16-Point Supersonic Deceleration Sweep</span>
              </div>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-600 font-semibold sticky top-0">
                    <tr>
                      <th className="px-3 py-2">Mach</th>
                      <th className="px-3 py-2">Speed (m/s)</th>
                      <th className="px-3 py-2">Stuart Number S</th>
                      <th className="px-3 py-2">Base Heat (MW/m²)</th>
                      <th className="px-3 py-2">MHD Heat (MW/m²)</th>
                      <th className="px-3 py-2">Reduction</th>
                      <th className="px-3 py-2">Plasma Freq</th>
                      <th className="px-3 py-2">RF Attenuation</th>
                      <th className="px-3 py-2">MHD Power</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {dossier.trajectory_profile.map((pt, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 transition-colors">
                        <td className="px-3 py-1.5 font-bold text-slate-900">{pt.mach_number.toFixed(1)}</td>
                        <td className="px-3 py-1.5 text-slate-600">{pt.velocity_mps.toFixed(0)}</td>
                        <td className="px-3 py-1.5 text-cyan-700 font-semibold">{pt.stuart_number.toFixed(2)}</td>
                        <td className="px-3 py-1.5 text-slate-500">{pt.heat_flux_baseline_mw_m2.toFixed(3)}</td>
                        <td className="px-3 py-1.5 font-bold text-emerald-600">{pt.heat_flux_mhd_mw_m2.toFixed(3)}</td>
                        <td className="px-3 py-1.5 font-semibold text-emerald-700">-{pt.heat_flux_reduction_pct.toFixed(1)}%</td>
                        <td className="px-3 py-1.5 text-slate-600">{pt.plasma_frequency_ghz.toFixed(2)} GHz</td>
                        <td className="px-3 py-1.5 text-slate-700">{pt.rf_attenuation_db.toFixed(1)} dB</td>
                        <td className="px-3 py-1.5 text-indigo-600 font-semibold">{pt.mhd_power_extracted_kw.toFixed(1)} kW</td>
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
                <span className="font-semibold text-slate-700">SHA-256 MHD Lineage:</span>
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
                    a.download = `mhd_${dossier.preset_key}.json`;
                    a.click();
                  }}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export MHD Dossier
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
