"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Target,
  Zap,
  Activity,
  Layers,
  Download,
  Play,
  RotateCcw,
  Compass,
  Radio,
  Clock,
  Sparkles,
  Flame,
  CheckCircle2,
} from "lucide-react";

interface DebrisObject {
  norad_id: number;
  object_name: string;
  radar_cross_section_m2: number;
  estimated_size_cm: number;
  perigee_altitude_km: number;
  apogee_altitude_km: number;
  inclination_deg: number;
  semi_major_axis_km: number;
  eccentricity: number;
  tracking_sensor: string;
}

interface BPlaneEncounter {
  tca_seconds_from_now: number;
  relative_velocity_km_s: number;
  miss_distance_m: number;
  miss_xi_m: number;
  miss_zeta_m: number;
  sigma_xi_m: number;
  sigma_zeta_m: number;
  correlation_rho: number;
  hard_body_radius_m: number;
  foster_pc: number;
  alfriend_akella_pc: number;
  pc_upper_95_bound: number;
  pc_lower_95_bound: number;
  alert_level: string;
}

interface CamBurn {
  burn_direction: string;
  delta_v_vector_mps: [number, number, number];
  delta_v_magnitude_mps: number;
  lead_time_hours: number;
  post_burn_miss_distance_m: number;
  post_burn_foster_pc: number;
  propellant_consumed_kg: number;
  secondary_conjunction_risk: string;
}

interface NetraEvaluationResponse {
  conjunction_id: string;
  primary_asset_name: string;
  primary_mass_kg: number;
  debris_object: DebrisObject;
  encounter: BPlaneEncounter;
  recommended_cam: CamBurn;
  alternative_burns: CamBurn[];
  isro_safety_clearance: string;
  merkle_provenance_hash: string;
  mitigation_standard: string;
}

interface ProjectNetraSSAStudioProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase?: string;
}

const PRESET_OPTIONS = [
  {
    key: "RISAT1B_FENGYUN",
    label: "ISRO RISAT-1B vs Fengyun-1C Debris",
    badge: "High Risk LEO",
    desc: "Hypervelocity 14.25 km/s encounter, miss 83 m, Pc = 2.8e-3, TCA in 14.2h.",
  },
  {
    key: "CARTOSAT3_COSMOS2251",
    label: "ISRO Cartosat-3 vs Cosmos-2251 Fragment",
    badge: "SSO Recon",
    desc: "Encounter velocity 11.80 km/s, miss 111 m, Pc = 1.8e-3, TCA in 6.5h.",
  },
  {
    key: "SPADEX_ROCKET_STAGE",
    label: "SpaDeX Docked Stack vs Spent CZ-4B Stage",
    badge: "Close In-Track",
    desc: "Spent 3.2m upper stage, miss 184 m, Pc = 4.5e-4, TCA in 2.8h.",
  },
  {
    key: "GSAT24_GEO_DEBRIS",
    label: "ISRO GSAT-24 vs GEO Graveyard Drifter",
    badge: "GEO Belt",
    desc: "Derelict apogee kick motor, miss 318 m, Pc = 8.2e-5, TCA in 36.0h.",
  },
];

export default function ProjectNetraSSAStudio({
  isOpen,
  onClose,
  apiBase = "http://127.0.0.1:8000",
}: ProjectNetraSSAStudioProps) {
  const [selectedPreset, setSelectedPreset] = useState("RISAT1B_FENGYUN");
  const [targetClearanceM, setTargetClearanceM] = useState(3000.0);
  const [selectedBurnIndex, setSelectedBurnIndex] = useState(0); // 0 = optimal, 1 = alt1, 2 = alt2
  const [burnDispatched, setBurnDispatched] = useState(false);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NetraEvaluationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const runEvaluation = async (presetKey: string) => {
    setLoading(true);
    setErrorMsg(null);
    setBurnDispatched(false);
    setSelectedBurnIndex(0);
    try {
      const resp = await fetch(`${apiBase}/api/netra/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_key: presetKey,
          target_clearance_m: targetClearanceM,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP Error ${resp.status}`);
      }
      const data: NetraEvaluationResponse = await resp.json();
      setResult(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to evaluate Project NETRA conjunction.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !result && !loading) {
      runEvaluation(selectedPreset);
    }
  }, [isOpen]);

  const activeBurn = useMemo<CamBurn | null>(() => {
    if (!result) return null;
    if (selectedBurnIndex === 0) return result.recommended_cam;
    const altIdx = selectedBurnIndex - 1;
    if (result.alternative_burns && result.alternative_burns[altIdx]) {
      return result.alternative_burns[altIdx];
    }
    return result.recommended_cam;
  }, [result, selectedBurnIndex]);

  // Scaled coordinates for B-Plane SVG (200, 200 = Primary Spacecraft)
  const bplaneSvgCoordinates = useMemo(() => {
    if (!result) return { missX: 200, missY: 200, postX: 200, postY: 200, sigX: 40, sigY: 70 };
    // Normalization scale: map ~3500m to 150 SVG pixels (0.043 px/m)
    const scale = 0.043;
    const missX = 200 + result.encounter.miss_xi_m * scale;
    const missY = 200 - result.encounter.miss_zeta_m * scale;

    const postDist = activeBurn ? activeBurn.post_burn_miss_distance_m : 3000.0;
    // Post-burn location along same bearing or deflected outward
    const ang = Math.atan2(result.encounter.miss_zeta_m, result.encounter.miss_xi_m);
    const postX = 200 + Math.cos(ang) * postDist * scale;
    const postY = 200 - Math.sin(ang) * postDist * scale;

    return {
      missX,
      missY,
      postX,
      postY,
      sigX: Math.max(15, result.encounter.sigma_xi_m * scale),
      sigY: Math.max(25, result.encounter.sigma_zeta_m * scale),
    };
  }, [result, activeBurn]);

  const exportDossierCSV = () => {
    if (!result) return;
    const rows = [
      ["Metric", "Value"],
      ["Conjunction_ID", result.conjunction_id],
      ["Primary_Asset", result.primary_asset_name],
      ["Debris_Object", result.debris_object.object_name],
      ["Debris_NORAD_ID", result.debris_object.norad_id.toString()],
      ["TCA_Hours", (result.encounter.tca_seconds_from_now / 3600.0).toFixed(2)],
      ["Relative_Velocity_km_s", result.encounter.relative_velocity_km_s.toFixed(2)],
      ["Nominal_Miss_Distance_m", result.encounter.miss_distance_m.toFixed(1)],
      ["Foster_Collision_Probability", result.encounter.foster_pc.toExponential(4)],
      ["Alfriend_Akella_Probability", result.encounter.alfriend_akella_pc.toExponential(4)],
      ["Pc_95_Confidence_Upper", result.encounter.pc_upper_95_bound.toExponential(4)],
      ["Alert_Level", result.encounter.alert_level],
      ["ISRO_Clearance", result.isro_safety_clearance],
      ["Recommended_Burn_Direction", result.recommended_cam.burn_direction],
      ["Recommended_Delta_V_mps", result.recommended_cam.delta_v_magnitude_mps.toFixed(4)],
      ["Post_Burn_Miss_Clearance_m", result.recommended_cam.post_burn_miss_distance_m.toFixed(1)],
      ["Post_Burn_Foster_Pc", result.recommended_cam.post_burn_foster_pc.toExponential(4)],
      ["Propellant_Cost_kg", result.recommended_cam.propellant_consumed_kg.toFixed(3)],
      ["Merkle_Root_Hash", result.merkle_provenance_hash],
    ];
    const csvContent = rows.map((e) => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `AASI_NETRA_CAM_${result.conjunction_id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1380px",
          maxHeight: "94vh",
          background: "#ffffff",
          borderRadius: "16px",
          border: "1px solid #e2e8f0",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          color: "#0f172a",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "18px 24px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#f8fafc",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                boxShadow: "0 4px 12px rgba(220, 38, 38, 0.3)",
              }}
            >
              <ShieldAlert size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h2 style={{ fontSize: "1.2rem", fontWeight: 800, color: "#0f172a", margin: 0 }}>
                  Project NETRA Orbital Conjunction &amp; Swarm CAM Synthesizer
                </h2>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#dc2626",
                    color: "#ffffff",
                    letterSpacing: "0.05em",
                  }}
                >
                  STAGE 13 SOVEREIGN
                </span>
                <span
                  style={{
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: "#fef2f2",
                    color: "#dc2626",
                    border: "1px solid #fecaca",
                  }}
                >
                  FOSTER 2D B-PLANE Pc &le; 10⁻⁷
                </span>
              </div>
              <p style={{ fontSize: "0.78rem", color: "#64748b", margin: "2px 0 0 0" }}>
                Real-time screening against 100,000+ catalog debris, Foster-1992 integration, and propellant-optimal CAM burns.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={exportDossierCSV}
              disabled={!result}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#f1f5f9",
                border: "1px solid #cbd5e1",
                color: "#334155",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: result ? "pointer" : "not-allowed",
              }}
            >
              <Download size={14} />
              Export CAM Dossier (CSV)
            </button>
            <button
              onClick={onClose}
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "#f1f5f9",
                border: "1px solid #e2e8f0",
                color: "#475569",
                fontSize: "1.1rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Studio Content */}
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          {/* Left Column: Preset Conjunction Selector & Constraints */}
          <div
            style={{
              width: "360px",
              borderRight: "1px solid #e2e8f0",
              background: "#ffffff",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              overflowY: "auto",
            }}
          >
            <div>
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                Active NETRA Conjunction Events
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                {PRESET_OPTIONS.map((p) => {
                  const active = selectedPreset === p.key;
                  return (
                    <div
                      key={p.key}
                      onClick={() => {
                        setSelectedPreset(p.key);
                        runEvaluation(p.key);
                      }}
                      style={{
                        padding: "10px 12px",
                        borderRadius: "10px",
                        border: active ? "2px solid #dc2626" : "1px solid #e2e8f0",
                        background: active ? "#fef2f2" : "#ffffff",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span style={{ fontSize: "0.82rem", fontWeight: 700, color: active ? "#991b1b" : "#1e293b" }}>
                          {p.label.split("vs")[0]}
                        </span>
                        <span
                          style={{
                            fontSize: "0.62rem",
                            fontWeight: 700,
                            padding: "1px 6px",
                            borderRadius: "4px",
                            background: active ? "#dc2626" : "#e2e8f0",
                            color: active ? "#ffffff" : "#475569",
                          }}
                        >
                          {p.badge}
                        </span>
                      </div>
                      <p style={{ fontSize: "0.7rem", color: "#64748b", margin: "4px 0 0 0" }}>{p.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* CAM Clearance Target */}
            <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
              <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                CAM Clearance Distance
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#475569" }}>
                    <span>Target Miss Clearance:</span>
                    <strong style={{ color: "#0f172a" }}>{(targetClearanceM / 1000.0).toFixed(1)} km</strong>
                  </div>
                  <input
                    type="range"
                    min="1000"
                    max="6000"
                    step="250"
                    value={targetClearanceM}
                    onChange={(e) => setTargetClearanceM(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: "#dc2626" }}
                  />
                </div>
              </div>
            </div>

            {/* Tracking Facility Info */}
            {result && (
              <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
                <label style={{ fontSize: "0.75rem", fontWeight: 700, color: "#334155", textTransform: "uppercase" }}>
                  Tracking Custody Radar/Optical
                </label>
                <div
                  style={{
                    padding: "10px",
                    background: "#f8fafc",
                    borderRadius: "8px",
                    border: "1px solid #f1f5f9",
                    marginTop: "8px",
                  }}
                >
                  <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "#0f172a" }}>
                    {result.debris_object.tracking_sensor}
                  </div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "2px" }}>
                    Size: {result.debris_object.estimated_size_cm.toFixed(1)} cm • RCS: {result.debris_object.radar_cross_section_m2.toFixed(3)} m²
                  </div>
                  <div style={{ fontSize: "0.68rem", color: "#64748b" }}>
                    NORAD ID #{result.debris_object.norad_id} • Inc: {result.debris_object.inclination_deg.toFixed(1)}°
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={() => runEvaluation(selectedPreset)}
              disabled={loading}
              style={{
                marginTop: "auto",
                padding: "12px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)",
                color: "#ffffff",
                border: "none",
                fontWeight: 700,
                fontSize: "0.85rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 4px 14px rgba(220, 38, 38, 0.35)",
              }}
            >
              {loading ? <RotateCcw size={16} className="animate-spin" /> : <Play size={16} />}
              {loading ? "Evaluating Conjunction..." : "Re-evaluate NETRA Risk"}
            </button>
          </div>

          {/* Right Column: Visualization & Mitigation Action */}
          <div
            style={{
              flex: 1,
              background: "#f8fafc",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
              overflowY: "auto",
            }}
          >
            {errorMsg && (
              <div
                style={{
                  padding: "12px 16px",
                  borderRadius: "10px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  fontSize: "0.82rem",
                }}
              >
                <strong>Evaluation Error:</strong> {errorMsg}
              </div>
            )}

            {/* Top Cards: Conjunction Risk Metrics */}
            {result && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px" }}>
                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>COLLISION PROBABILITY (Pc)</div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 800,
                      color: result.encounter.alert_level === "RED" ? "#dc2626" : "#d97706",
                      marginTop: "4px",
                    }}
                  >
                    {result.encounter.foster_pc.toExponential(3)}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                    Threshold: 1.00e-4 (IADC Red)
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>MISS DISTANCE</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {result.encounter.miss_distance_m.toFixed(1)} <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>m</span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#2563eb", fontWeight: 600, marginTop: "2px" }}>
                    Relative V: {result.encounter.relative_velocity_km_s.toFixed(2)} km/s
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>TIME TO TCA</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", marginTop: "4px" }}>
                    {(result.encounter.tca_seconds_from_now / 3600.0).toFixed(1)} <span style={{ fontSize: "0.8rem", fontWeight: 500 }}>Hours</span>
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#059669", fontWeight: 600, marginTop: "2px" }}>
                    {(result.encounter.tca_seconds_from_now / 60.0).toFixed(0)} min lead window
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px",
                    background: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>ISRO SAFETY DIRECTIVE</div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.95rem",
                      fontWeight: 800,
                      color: result.isro_safety_clearance === "CAM_DISPATCH_MANDATED" ? "#dc2626" : "#059669",
                      marginTop: "4px",
                    }}
                  >
                    {result.isro_safety_clearance === "CAM_DISPATCH_MANDATED" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
                    <span>{result.isro_safety_clearance.replace(/_/g, " ")}</span>
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
                    Post-CAM: &le; 10⁻⁷ Pc Required
                  </div>
                </div>
              </div>
            )}

            {/* Middle Section: SVG B-Plane Encounter Viewport & Burn Plan */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.1fr", gap: "16px" }}>
              {/* B-Plane SVG Viewport */}
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "14px",
                  border: "1px solid #e2e8f0",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>
                    2D Encounter B-Plane Geometry (&xi; - &zeta; Frame)
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                    Hard-Body Radius: {result ? result.encounter.hard_body_radius_m.toFixed(1) : 5} m
                  </div>
                </div>

                <div
                  style={{
                    width: "100%",
                    height: "360px",
                    background: "#090d16",
                    borderRadius: "10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  <svg viewBox="0 0 400 400" style={{ width: "100%", height: "100%" }}>
                    {/* B-Plane Coordinate Axes */}
                    <line x1="20" y1="200" x2="380" y2="200" stroke="rgba(255,255,255,0.12)" />
                    <line x1="200" y1="20" x2="200" y2="380" stroke="rgba(255,255,255,0.12)" />
                    <text x="370" y="195" fill="#64748b" fontSize="8" textAnchor="end">
                      +&xi; (Cross-Track)
                    </text>
                    <text x="205" y="30" fill="#64748b" fontSize="8">
                      +&zeta; (Radial)
                    </text>

                    {/* Safety Clearance Perimeter Circle (3000m) */}
                    <circle cx="200" cy="200" r="130" fill="none" stroke="rgba(5, 150, 105, 0.25)" strokeDasharray="3 3" />
                    <text x="200" y="340" fill="#059669" fontSize="8" textAnchor="middle">
                      SAFETY CLEARANCE BOUNDARY (3.0 KM)
                    </text>

                    {/* 1-sigma, 2-sigma, 3-sigma Combined Covariance Ellipses */}
                    <ellipse
                      cx="200"
                      cy="200"
                      rx={bplaneSvgCoordinates.sigX * 3}
                      ry={bplaneSvgCoordinates.sigY * 3}
                      fill="rgba(220, 38, 38, 0.05)"
                      stroke="rgba(220, 38, 38, 0.2)"
                      strokeDasharray="2 2"
                    />
                    <ellipse
                      cx="200"
                      cy="200"
                      rx={bplaneSvgCoordinates.sigX * 2}
                      ry={bplaneSvgCoordinates.sigY * 2}
                      fill="rgba(220, 38, 38, 0.08)"
                      stroke="rgba(220, 38, 38, 0.4)"
                    />
                    <ellipse
                      cx="200"
                      cy="200"
                      rx={bplaneSvgCoordinates.sigX}
                      ry={bplaneSvgCoordinates.sigY}
                      fill="rgba(220, 38, 38, 0.15)"
                      stroke="rgba(220, 38, 38, 0.7)"
                    />

                    {/* Primary Asset at Center (0, 0) */}
                    <circle cx="200" cy="200" r="6" fill="#38bdf8" stroke="#ffffff" strokeWidth="1.5" />
                    <text x="200" y="215" fill="#38bdf8" fontSize="8" fontWeight="700" textAnchor="middle">
                      PRIMARY ASSET
                    </text>

                    {/* Nominal Encounter Position (Pre-CAM) */}
                    <line
                      x1="200"
                      y1="200"
                      x2={bplaneSvgCoordinates.missX}
                      y2={bplaneSvgCoordinates.missY}
                      stroke="#dc2626"
                      strokeWidth="1.5"
                      strokeDasharray="3 3"
                    />
                    <circle
                      cx={bplaneSvgCoordinates.missX}
                      cy={bplaneSvgCoordinates.missY}
                      r="6"
                      fill="#dc2626"
                      stroke="#ffffff"
                      strokeWidth="1.5"
                    />
                    <text
                      x={bplaneSvgCoordinates.missX + 8}
                      y={bplaneSvgCoordinates.missY - 4}
                      fill="#ef4444"
                      fontSize="8"
                      fontWeight="700"
                    >
                      PRE-CAM MISS ({result ? result.encounter.miss_distance_m.toFixed(0) : 0}m)
                    </text>

                    {/* Post-CAM Position after Burn */}
                    {activeBurn && (
                      <>
                        <line
                          x1={bplaneSvgCoordinates.missX}
                          y1={bplaneSvgCoordinates.missY}
                          x2={bplaneSvgCoordinates.postX}
                          y2={bplaneSvgCoordinates.postY}
                          stroke="#10b981"
                          strokeWidth="2"
                        />
                        <circle
                          cx={bplaneSvgCoordinates.postX}
                          cy={bplaneSvgCoordinates.postY}
                          r="6"
                          fill="#10b981"
                          stroke="#ffffff"
                          strokeWidth="1.5"
                        />
                        <text
                          x={bplaneSvgCoordinates.postX}
                          y={bplaneSvgCoordinates.postY - 8}
                          fill="#10b981"
                          fontSize="8"
                          fontWeight="700"
                          textAnchor="middle"
                        >
                          POST-CAM SAFE CLEARANCE ({(activeBurn.post_burn_miss_distance_m / 1000.0).toFixed(1)} km)
                        </text>
                      </>
                    )}
                  </svg>
                </div>
              </div>

              {/* CAM Burn Options & Dispatch Card */}
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "14px",
                  border: "1px solid #e2e8f0",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1e293b" }}>
                  Synthesized Collision Avoidance Burn Candidates
                </div>

                {result && activeBurn && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {[result.recommended_cam, ...(result.alternative_burns || [])].map((burn, idx) => {
                      const selected = selectedBurnIndex === idx;
                      const isOpt = idx === 0;
                      return (
                        <div
                          key={idx}
                          onClick={() => setSelectedBurnIndex(idx)}
                          style={{
                            padding: "10px 12px",
                            borderRadius: "10px",
                            border: selected ? "2px solid #059669" : "1px solid #e2e8f0",
                            background: selected ? "#ecfdf5" : "#f8fafc",
                            cursor: "pointer",
                            transition: "all 0.15s ease",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <span style={{ fontSize: "0.82rem", fontWeight: 800, color: "#0f172a" }}>
                                {burn.burn_direction} BURN
                              </span>
                              {isOpt && (
                                <span
                                  style={{
                                    fontSize: "0.6rem",
                                    fontWeight: 700,
                                    padding: "1px 6px",
                                    borderRadius: "3px",
                                    background: "#059669",
                                    color: "#ffffff",
                                  }}
                                >
                                  FUEL OPTIMAL
                                </span>
                              )}
                            </div>
                            <span style={{ fontSize: "0.85rem", fontWeight: 800, color: "#059669" }}>
                              &Delta;V: {burn.delta_v_magnitude_mps.toFixed(4)} m/s
                            </span>
                          </div>

                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#64748b", marginTop: "4px" }}>
                            <span>Post-CAM Clearance: <strong>{(burn.post_burn_miss_distance_m / 1000.0).toFixed(2)} km</strong></span>
                            <span>Post-CAM Pc: <strong>{burn.post_burn_foster_pc.toExponential(2)}</strong></span>
                          </div>
                          <div style={{ fontSize: "0.7rem", color: "#64748b" }}>
                            Propellant: <strong>{burn.propellant_consumed_kg.toFixed(3)} kg</strong> • Lead Time: {burn.lead_time_hours.toFixed(1)}h before TCA
                          </div>
                        </div>
                      );
                    })}

                    {/* Dispatch Button */}
                    <button
                      onClick={() => setBurnDispatched(true)}
                      disabled={burnDispatched}
                      style={{
                        marginTop: "10px",
                        padding: "12px",
                        borderRadius: "10px",
                        background: burnDispatched
                          ? "#059669"
                          : "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)",
                        color: "#ffffff",
                        border: "none",
                        fontWeight: 800,
                        fontSize: "0.85rem",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "8px",
                        cursor: burnDispatched ? "default" : "pointer",
                        boxShadow: "0 4px 14px rgba(220, 38, 38, 0.35)",
                      }}
                    >
                      {burnDispatched ? <CheckCircle2 size={16} /> : <Flame size={16} />}
                      {burnDispatched
                        ? "CAM MANEUVER DISPATCHED TO ISTRAC TELEMETRY"
                        : "CONFIRM & DISPATCH CAM BURN TO SATELLITE"}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Card: Epistemic Covariance Scaling & Merkle Provenance */}
            {result && (
              <div
                style={{
                  background: "#ffffff",
                  borderRadius: "14px",
                  border: "1px solid #e2e8f0",
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "16px",
                  flexWrap: "wrap",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "8px",
                      background: "#ecfdf5",
                      border: "1px solid #a7f3d0",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#059669",
                    }}
                  >
                    <ShieldCheck size={20} />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#065f46" }}>
                      Epistemic Covariance Uncertainty Bound (&alpha; &isin; [0.5, 2.0]):{" "}
                      [{result.encounter.pc_lower_95_bound.toExponential(2)}, {result.encounter.pc_upper_95_bound.toExponential(2)}]
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                      Secondary Conjunction Screening: ZERO HAZARDS WITHIN 72-HOUR HORIZON
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "#64748b" }}>
                  <span>MERKLE ROOT:</span>
                  <span
                    style={{
                      padding: "2px 8px",
                      background: "#f1f5f9",
                      borderRadius: "4px",
                      border: "1px solid #e2e8f0",
                      color: "#0f172a",
                    }}
                  >
                    {result.merkle_provenance_hash.slice(0, 16)}...{result.merkle_provenance_hash.slice(-8)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

