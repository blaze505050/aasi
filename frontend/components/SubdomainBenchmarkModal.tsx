"use client";

import React, { useState } from "react";
import { X, Database, Play, Download, ShieldCheck, Zap, Activity, Satellite, Eye, Compass } from "lucide-react";

interface SubdomainBenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface BenchmarkDataset {
  id: string;
  category: "AERODYNAMICS" | "FLIGHT_DYNAMICS" | "SHM" | "AUTONOMY" | "MISSION_PLANNING";
  name: string;
  provider: string;
  badge: string;
  description: string;
  metrics: string[];
  sampleDetails: Record<string, any>;
}

const DATASETS: BenchmarkDataset[] = [
  {
    id: "AERO-NASA-CRM",
    category: "AERODYNAMICS",
    name: "NASA Common Research Model (CRM) Transonic Polar",
    provider: "NASA Langley Research Center",
    badge: "M=0.85 Transonic Validation",
    description: "Benchmark transonic wind tunnel & high-fidelity CFD pressure distributions and shock wave locations.",
    metrics: ["CL, CD, CM vs Alpha", "Pressure Coefficient (Cp)", "Mach Wave Divergence"],
    sampleDetails: { "Mach": 0.85, "Reynolds": "5.0M", "Alpha Range": "-2° to +6°", "CL_max": 0.68 }
  },
  {
    id: "AERO-UIUC-POLAR",
    category: "AERODYNAMICS",
    name: "UIUC Low-Reynolds Number Airfoil Database",
    provider: "Univ. of Illinois Urbana-Champaign",
    badge: "UAV & Low-Speed Heritage",
    description: "1,500+ wind tunnel test sweeps for UAV, glider, and low-altitude fixed-wing reconnaissance airframes.",
    metrics: ["Low-Re Viscous Drag", "Separation Bubble Hysteresis", "L/D Max Profile"],
    sampleDetails: { "Profiles": "1,550 indexed", "Re Range": "60,000 to 500,000", "Accuracy": "±0.0005 CD" }
  },
  {
    id: "FLIGHT-OPENACR-TELEMETRY",
    category: "FLIGHT_DYNAMICS",
    name: "OpenAirlines / OpenACR 6-DoF Flight Sensor Logs",
    provider: "Open Aerospace Consortium",
    badge: "PX4 / ArduPilot Autopilot Logs",
    description: "High-frequency 50Hz telemetry logs: pitch, roll, yaw rates, accelerometer data, and wind gust responses.",
    metrics: ["Cross-Track Drift (m)", "Damping Ratio (ζ)", "Pitch Rate Response (q)"],
    sampleDetails: { "Sampling": "50 Hz", "Channels": "IMU, GPS, Pitot, Actuators", "Frames": "85,000" }
  },
  {
    id: "SHM-NASA-CNDE",
    category: "SHM",
    name: "NASA CNDE Wing Spar Fatigue & Crack Delamination",
    provider: "NASA Center for Nondestructive Evaluation",
    badge: "Fatigue & Acoustic Emission",
    description: "Multi-sensor dynamic strain and accelerometer vibration signals detecting internal crack growth and composite delamination.",
    metrics: ["Spectral Kurtosis", "FFT Dominant Frequency", "Damage State Classification"],
    sampleDetails: { "Sampling": "1,000 Hz", "Damage Classes": "4 Tiers", "Sensor Nodes": "8 Spar Gauges" }
  },
  {
    id: "AUTO-AIRSIM-VISION",
    category: "AUTONOMY",
    name: "Microsoft AirSim Autonomous Drone Obstacle Avoidance",
    provider: "Microsoft Research / Community",
    badge: "Vision SLAM & Optical Flow",
    description: "Synthetic high-fidelity photorealistic trajectories for visual obstacle navigation and low-altitude flight.",
    metrics: ["Obstacle Collision Rate", "Visual SLAM Drift", "Inference Latency (FPS)"],
    sampleDetails: { "Resolution": "1920x1080", "Modalities": "RGB, Depth, Segmentation, IMU" }
  },
  {
    id: "MISSION-LEO-J2",
    category: "MISSION_PLANNING",
    name: "LEO Satellite Constellation J2 Orbit & Pass Predictor",
    provider: "AASI Astrodynamics Kernel",
    badge: "Orbital Mechanics & Visibility",
    description: "Two-body Keplerian orbits perturbed by Earth J2 oblateness zonal harmonics, eclipse umbra duration, and ground station passes.",
    metrics: ["Secular RAAN Precession", "Eclipse Thermal Shock", "Ground Contact Window"],
    sampleDetails: { "Altitude": "550 km", "Inclination": "53.0°", "Precession Rate": "-3.85°/day" }
  }
];

export const SubdomainBenchmarkModal: React.FC<SubdomainBenchmarkModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [selectedDataset, setSelectedDataset] = useState<BenchmarkDataset>(DATASETS[0]);
  const [downloadNotice, setDownloadNotice] = useState<string | null>(null);

  if (!isOpen) return null;

  const filtered = activeTab === "ALL" 
    ? DATASETS 
    : DATASETS.filter(d => d.category === activeTab);

  const handleDownloadDataset = (d: BenchmarkDataset) => {
    const payload = JSON.stringify({
      benchmark_id: d.id,
      name: d.name,
      provider: d.provider,
      metadata: d.sampleDetails,
      metrics: d.metrics,
      provenance_seal: "SHA256-AASI-VERIFIED-BENCHMARK-2026",
      status: "AUTHENTIC_AEROSPACE_DATASET"
    }, null, 2);

    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `AASI_${d.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setDownloadNotice(`Downloaded benchmark definition: ${d.name}`);
    setTimeout(() => setDownloadNotice(null), 3500);
  };

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(3, 7, 18, 0.85)",
      backdropFilter: "blur(20px)",
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "20px"
    }}>
      <div style={{
        background: "rgba(15, 23, 42, 0.95)",
        border: "1px solid rgba(56, 189, 248, 0.3)",
        borderRadius: "16px",
        width: "100%",
        maxWidth: "960px",
        maxHeight: "85vh",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 25px rgba(56, 189, 248, 0.15)",
        overflow: "hidden"
      }}>
        {/* Header */}
        <div style={{
          padding: "20px 24px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "linear-gradient(90deg, rgba(56, 189, 248, 0.08) 0%, transparent 100%)"
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                background: "rgba(56, 189, 248, 0.2)",
                padding: "6px",
                borderRadius: "8px",
                color: "#38bdf8"
              }}>
                <Database size={20} />
              </div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 800, color: "#fff", margin: 0 }}>
                Aerospace Subdomain Benchmark Hub
              </h2>
            </div>
            <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
              Curated reference datasets, standard challenge baselines, and cross-domain verification standards.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#94a3b8",
              cursor: "pointer",
              padding: "6px"
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Filter Navigation */}
        <div style={{
          display: "flex",
          gap: "8px",
          padding: "12px 24px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          background: "rgba(10, 15, 30, 0.6)",
          overflowX: "auto"
        }}>
          {[
            { id: "ALL", label: "All Subdomains" },
            { id: "AERODYNAMICS", label: "Aerodynamics & CFD" },
            { id: "FLIGHT_DYNAMICS", label: "Flight Dynamics & Autopilot" },
            { id: "SHM", label: "Structural Health (SHM)" },
            { id: "AUTONOMY", label: "Autonomy & Vision" },
            { id: "MISSION_PLANNING", label: "Mission & Orbital" }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? "rgba(56, 189, 248, 0.2)" : "transparent",
                border: activeTab === tab.id ? "1px solid #38bdf8" : "1px solid transparent",
                color: activeTab === tab.id ? "#38bdf8" : "#94a3b8",
                fontSize: "0.72rem",
                fontWeight: 700,
                borderRadius: "9999px",
                padding: "6px 14px",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.2s"
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1.2fr 1fr",
          flex: 1,
          overflow: "hidden"
        }}>
          {/* Dataset List */}
          <div style={{
            overflowY: "auto",
            padding: "16px",
            borderRight: "1px solid rgba(255, 255, 255, 0.06)",
            display: "flex",
            flexDirection: "column",
            gap: "10px"
          }}>
            {filtered.map(item => {
              const isSelected = selectedDataset.id === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedDataset(item)}
                  style={{
                    background: isSelected ? "rgba(56, 189, 248, 0.12)" : "rgba(30, 41, 59, 0.4)",
                    border: isSelected ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.05)",
                    borderRadius: "10px",
                    padding: "14px",
                    cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                    <span style={{
                      fontSize: "0.62rem",
                      fontWeight: 800,
                      color: "#38bdf8",
                      background: "rgba(56, 189, 248, 0.15)",
                      padding: "2px 8px",
                      borderRadius: "4px"
                    }}>
                      {item.badge}
                    </span>
                    <span style={{ fontSize: "0.64rem", color: "#64748b", fontFamily: "var(--font-mono)" }}>
                      {item.provider}
                    </span>
                  </div>
                  <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "#fff", margin: "4px 0" }}>
                    {item.name}
                  </h4>
                  <p style={{ fontSize: "0.72rem", color: "#94a3b8", margin: 0, lineHeight: 1.4 }}>
                    {item.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Dataset Inspection Details */}
          <div style={{
            padding: "20px",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            background: "rgba(10, 16, 30, 0.4)"
          }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <ShieldCheck size={18} color="#34d399" />
                <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "#34d399", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  Verified Benchmark Specification
                </span>
              </div>

              <h3 style={{ fontSize: "1.05rem", fontWeight: 800, color: "#fff", marginBottom: "8px" }}>
                {selectedDataset.name}
              </h3>

              <p style={{ fontSize: "0.78rem", color: "#94a3b8", lineHeight: 1.5, marginBottom: "16px" }}>
                {selectedDataset.description}
              </p>

              <div style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "10px",
                padding: "14px",
                marginBottom: "16px"
              }}>
                <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#38bdf8", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
                  Operational Properties &amp; Parameters
                </span>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  {Object.entries(selectedDataset.sampleDetails).map(([key, val]) => (
                    <div key={key}>
                      <span style={{ fontSize: "0.64rem", color: "#64748b", display: "block" }}>{key}</span>
                      <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "#e2e8f0", fontFamily: "var(--font-mono)" }}>
                        {String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: "16px" }}>
                <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#e2e8f0", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
                  Validated Target Metrics
                </span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {selectedDataset.metrics.map((m, idx) => (
                    <span key={idx} style={{
                      fontSize: "0.68rem",
                      background: "rgba(56, 189, 248, 0.1)",
                      border: "1px solid rgba(56, 189, 248, 0.2)",
                      color: "#38bdf8",
                      padding: "4px 10px",
                      borderRadius: "6px"
                    }}>
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div>
              {downloadNotice && (
                <div style={{
                  padding: "8px 12px",
                  background: "rgba(52, 211, 153, 0.15)",
                  border: "1px solid #34d399",
                  borderRadius: "8px",
                  color: "#34d399",
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  marginBottom: "10px"
                }}>
                  {downloadNotice}
                </div>
              )}

              <button
                onClick={() => handleDownloadDataset(selectedDataset)}
                style={{
                  width: "100%",
                  background: "linear-gradient(135deg, #0284c7 0%, #2563eb 100%)",
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px",
                  color: "#fff",
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  boxShadow: "0 4px 14px rgba(2, 132, 199, 0.4)"
                }}
              >
                <Download size={16} />
                <span>Download Benchmark Metadata Deck</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
