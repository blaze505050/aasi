"use client";

import React, { useState } from "react";
import { ArrowLeftRight, CheckCircle2, TrendingUp, AlertTriangle, ShieldCheck, Compass } from "lucide-react";

export interface ComparisonCandidate {
  id: string;
  name: string;
  category: string;
  alpha_deg: number;
  cl: number;
  cd: number;
  cm: number;
  lod: number;
  stall_alpha: number;
  camber_pct: number;
  thickness_pct: number;
  verification_status: "VERIFIED" | "SYNTHETIC" | "DATABASE";
}

interface InvestigationComparisonPanelProps {
  onSelectCandidate?: (candidate: ComparisonCandidate) => void;
}

const DEFAULT_CANDIDATES: ComparisonCandidate[] = [
  {
    id: "naca-0012",
    name: "NACA 0012",
    category: "Symmetric Benchmark",
    alpha_deg: 4.0,
    cl: 0.441,
    cd: 0.0084,
    cm: -0.005,
    lod: 52.5,
    stall_alpha: 15.0,
    camber_pct: 0.0,
    thickness_pct: 12.0,
    verification_status: "VERIFIED",
  },
  {
    id: "naca-2412",
    name: "NACA 2412",
    category: "Moderate Camber GA",
    alpha_deg: 4.0,
    cl: 0.651,
    cd: 0.0091,
    cm: -0.052,
    lod: 71.5,
    stall_alpha: 16.0,
    camber_pct: 2.0,
    thickness_pct: 12.0,
    verification_status: "VERIFIED",
  },
  {
    id: "naca-4412",
    name: "NACA 4412",
    category: "High-Lift Subsonic",
    alpha_deg: 4.0,
    cl: 0.862,
    cd: 0.0108,
    cm: -0.098,
    lod: 79.8,
    stall_alpha: 15.5,
    camber_pct: 4.0,
    thickness_pct: 12.0,
    verification_status: "VERIFIED",
  },
  {
    id: "clark-y",
    name: "Clark Y",
    category: "Flat-Bottom Airfoil",
    alpha_deg: 4.0,
    cl: 0.795,
    cd: 0.0102,
    cm: -0.075,
    lod: 77.9,
    stall_alpha: 17.0,
    camber_pct: 3.4,
    thickness_pct: 11.7,
    verification_status: "DATABASE",
  },
  {
    id: "rae-2822",
    name: "RAE 2822",
    category: "Transonic Supercritical",
    alpha_deg: 2.79,
    cl: 0.743,
    cd: 0.0127,
    cm: -0.082,
    lod: 58.5,
    stall_alpha: 12.0,
    camber_pct: 1.4,
    thickness_pct: 12.1,
    verification_status: "VERIFIED",
  },
];

export const InvestigationComparisonPanel: React.FC<InvestigationComparisonPanelProps> = ({
  onSelectCandidate,
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>(["naca-0012", "naca-2412", "naca-4412"]);

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length > 2) {
        setSelectedIds(selectedIds.filter((item) => item !== id));
      }
    } else {
      if (selectedIds.length < 4) {
        setSelectedIds([...selectedIds, id]);
      }
    }
  };

  const activeCandidates = DEFAULT_CANDIDATES.filter((c) => selectedIds.includes(c.id));
  const baseline = activeCandidates[0];

  return (
    <div
      style={{
        background: "linear-gradient(180deg, rgba(17, 24, 39, 0.8), rgba(11, 16, 28, 0.9))",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "16px",
        padding: "24px",
        boxShadow: "0 12px 36px rgba(0, 0, 0, 0.35)",
        backdropFilter: "blur(20px)",
      }}
    >
      {/* Top Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, rgba(0, 119, 237, 0.3), rgba(0, 210, 255, 0.2))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#64d2ff",
            }}
          >
            <ArrowLeftRight size={20} />
          </div>
          <div>
            <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#f8fafc" }}>
              Aerodynamic Portfolio Comparison Studio
            </div>
            <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
              Multi-airfoil differential performance evaluation across lift, drag polars, and pitch stability.
            </div>
          </div>
        </div>

        {/* Candidate selector pills */}
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
          {DEFAULT_CANDIDATES.map((cand) => {
            const isSelected = selectedIds.includes(cand.id);
            return (
              <button
                key={cand.id}
                onClick={() => toggleSelect(cand.id)}
                style={{
                  padding: "5px 12px",
                  borderRadius: "8px",
                  border: isSelected ? "1px solid rgba(0, 210, 255, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
                  background: isSelected ? "rgba(0, 210, 255, 0.18)" : "rgba(255, 255, 255, 0.04)",
                  color: isSelected ? "#64d2ff" : "#94a3b8",
                  fontSize: "0.76rem",
                  fontWeight: isSelected ? 700 : 500,
                  cursor: "pointer",
                  transition: "all 140ms ease",
                }}
              >
                {cand.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Grid Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.82rem",
            color: "#e2e8f0",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.1)", textAlign: "left" }}>
              <th style={{ padding: "12px 14px", color: "#94a3b8", fontWeight: 600 }}>METRIC / PROPERTY</th>
              {activeCandidates.map((cand, idx) => (
                <th key={cand.id} style={{ padding: "12px 14px" }}>
                  <div style={{ fontWeight: 700, color: "#ffffff", fontSize: "0.95rem" }}>
                    {cand.name}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#64d2ff", fontWeight: 500 }}>
                    {cand.category}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Lift Coefficient CL */}
            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
              <td style={{ padding: "12px 14px", fontWeight: 600, color: "#cbd5e1" }}>
                Lift Coefficient (CL @ α)
              </td>
              {activeCandidates.map((cand, idx) => {
                const diff = idx > 0 ? cand.cl - baseline.cl : 0;
                return (
                  <td key={cand.id} style={{ padding: "12px 14px" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#f8fafc" }}>
                      {cand.cl.toFixed(4)}
                    </div>
                    {idx > 0 && (
                      <div
                        style={{
                          fontSize: "0.68rem",
                          fontFamily: "var(--font-mono)",
                          color: diff >= 0 ? "#30d158" : "#ff453a",
                        }}
                      >
                        {diff >= 0 ? `+${diff.toFixed(4)}` : diff.toFixed(4)} vs baseline
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>

            {/* Drag Coefficient CD */}
            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
              <td style={{ padding: "12px 14px", fontWeight: 600, color: "#cbd5e1" }}>
                Drag Coefficient (CD @ α)
              </td>
              {activeCandidates.map((cand, idx) => {
                const diff = idx > 0 ? cand.cd - baseline.cd : 0;
                return (
                  <td key={cand.id} style={{ padding: "12px 14px" }}>
                    <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#f8fafc" }}>
                      {cand.cd.toFixed(5)}
                    </div>
                    {idx > 0 && (
                      <div
                        style={{
                          fontSize: "0.68rem",
                          fontFamily: "var(--font-mono)",
                          color: diff <= 0 ? "#30d158" : "#ffd60a",
                        }}
                      >
                        {diff >= 0 ? `+${diff.toFixed(5)}` : diff.toFixed(5)}
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>

            {/* Aerodynamic Efficiency L/D */}
            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)", background: "rgba(0, 210, 255, 0.03)" }}>
              <td style={{ padding: "12px 14px", fontWeight: 700, color: "#64d2ff" }}>
                Glide Efficiency (L/D)
              </td>
              {activeCandidates.map((cand, idx) => (
                <td key={cand.id} style={{ padding: "12px 14px" }}>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "1.1rem",
                      fontWeight: 800,
                      color: cand.lod > 70 ? "#30d158" : "#f8fafc",
                    }}
                  >
                    {cand.lod.toFixed(1)}
                  </div>
                </td>
              ))}
            </tr>

            {/* Quarter Chord Pitching Moment CM */}
            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
              <td style={{ padding: "12px 14px", fontWeight: 600, color: "#cbd5e1" }}>
                Pitching Moment (CM c/4)
              </td>
              {activeCandidates.map((cand) => (
                <td key={cand.id} style={{ padding: "12px 14px", fontFamily: "var(--font-mono)" }}>
                  {cand.cm.toFixed(4)}
                </td>
              ))}
            </tr>

            {/* Geometry Characteristics */}
            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
              <td style={{ padding: "12px 14px", fontWeight: 600, color: "#cbd5e1" }}>
                Geometry Camber / Thickness
              </td>
              {activeCandidates.map((cand) => (
                <td key={cand.id} style={{ padding: "12px 14px", fontSize: "0.76rem" }}>
                  <div>m/c = {cand.camber_pct.toFixed(1)}%</div>
                  <div>t/c = {cand.thickness_pct.toFixed(1)}%</div>
                </td>
              ))}
            </tr>

            {/* Action Buttons */}
            <tr>
              <td style={{ padding: "16px 14px", fontWeight: 600, color: "#94a3b8" }}>
                INVESTIGATION ACTION
              </td>
              {activeCandidates.map((cand) => (
                <td key={cand.id} style={{ padding: "16px 14px" }}>
                  <button
                    onClick={() => onSelectCandidate?.(cand)}
                    style={{
                      padding: "7px 14px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, rgba(0, 119, 237, 0.3), rgba(0, 210, 255, 0.2))",
                      border: "1px solid rgba(100, 210, 255, 0.4)",
                      color: "#64d2ff",
                      fontSize: "0.76rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      transition: "all 140ms ease",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <Compass size={13} />
                    <span>Investigate</span>
                  </button>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
