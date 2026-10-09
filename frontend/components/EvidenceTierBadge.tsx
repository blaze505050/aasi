"use client";

import React, { useState } from "react";

export type EvidenceTier = "TIER_1_VERIFIED" | "TIER_2_SURROGATE" | "TIER_3_PANEL" | "TIER_4_ATTRIBUTED" | "TIER_PENDING";

export interface EvidenceTierBadgeProps {
  tier?: EvidenceTier;
  sourceType?: string; // e.g. "live_cfd", "surrogate", "analytical", "database"
  status?: string;
  uncertainty?: number | null;
  discrepancyPct?: number | null;
  gciPct?: number | null;
  caseHash?: string | null;
  compact?: boolean;
}

export function classifyEvidenceTier(
  sourceType?: string,
  status?: string,
  gciPct?: number | null
): EvidenceTier {
  const s = (status || "").toLowerCase();
  const src = (sourceType || "").toLowerCase();

  if (s.includes("unverified") || s.includes("diverged") || s.includes("discrepant") || s.includes("contradiction")) {
    return "TIER_4_ATTRIBUTED";
  }
  if (src.includes("cfd") || src.includes("openfoam") || src.includes("rans") || (gciPct !== undefined && gciPct !== null && gciPct < 3.0)) {
    if (s.includes("verified") || s.includes("converged") || s.includes("completed")) {
      return "TIER_1_VERIFIED";
    }
  }
  if (src.includes("surrogate") || src.includes("neural") || src.includes("fno") || src.includes("ml")) {
    return "TIER_2_SURROGATE";
  }
  if (src.includes("panel") || src.includes("analytical") || src.includes("inviscid") || src.includes("potential")) {
    return "TIER_3_PANEL";
  }
  if (s.includes("verified")) return "TIER_1_VERIFIED";
  return "TIER_PENDING";
}

export const EvidenceTierBadge: React.FC<EvidenceTierBadgeProps> = ({
  tier,
  sourceType,
  status,
  uncertainty,
  discrepancyPct,
  gciPct,
  caseHash,
  compact = false,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const resolvedTier = tier || classifyEvidenceTier(sourceType, status, gciPct);

  const tierConfig = {
    TIER_1_VERIFIED: {
      label: "Tier 1: ASME V&V 20",
      shortLabel: "T1 Verified",
      color: "#30d158",
      bg: "rgba(48, 209, 88, 0.12)",
      border: "rgba(48, 209, 88, 0.3)",
      dotColor: "#30d158",
      description: "Grid-converged RANS CFD with ASME V&V 20 numerical verification. GCI < 3%. Epistemically bounded.",
    },
    TIER_2_SURROGATE: {
      label: "Tier 2: Neural Operator",
      shortLabel: "T2 Surrogate",
      color: "#f59e0b",
      bg: "rgba(245, 158, 11, 0.12)",
      border: "rgba(245, 158, 11, 0.3)",
      dotColor: "#f59e0b",
      description: "Physics-Informed Deep Neural Operator / FNO inference with calibrated latent uncertainty envelope.",
    },
    TIER_3_PANEL: {
      label: "Tier 3: Discrete Vortex",
      shortLabel: "T3 Panel",
      color: "#64d2ff",
      bg: "rgba(100, 210, 255, 0.12)",
      border: "rgba(100, 210, 255, 0.3)",
      dotColor: "#64d2ff",
      description: "Fast potential flow discrete vortex panel solver. Inviscid boundary layer theoretical approximation.",
    },
    TIER_4_ATTRIBUTED: {
      label: "Tier 4: Attributed / Discrepant",
      shortLabel: "T4 Discrepant",
      color: "#ffd60a",
      bg: "rgba(255, 214, 10, 0.12)",
      border: "rgba(255, 214, 10, 0.3)",
      dotColor: "#ffd60a",
      description: "Physical contradiction or divergence detected. Epistemic discrepancy attributed (e.g. boundary layer separation).",
    },
    TIER_PENDING: {
      label: "Tier Pending",
      shortLabel: "Pending",
      color: "#98989d",
      bg: "rgba(152, 152, 157, 0.12)",
      border: "rgba(152, 152, 157, 0.25)",
      dotColor: "#98989d",
      description: "Computational evaluation or verification check is in progress.",
    },
  }[resolvedTier];

  return (
    <div
      style={{ position: "relative", display: "inline-flex", alignItems: "center" }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "6px",
          padding: compact ? "2px 8px" : "4px 10px",
          borderRadius: "9999px",
          background: tierConfig.bg,
          border: `1px solid ${tierConfig.border}`,
          color: tierConfig.color,
          fontSize: compact ? "0.62rem" : "0.72rem",
          fontWeight: 700,
          fontFamily: "var(--font-mono)",
          letterSpacing: "0.04em",
          cursor: "help",
          transition: "all 150ms ease",
        }}
      >
        <span
          style={{
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            background: tierConfig.dotColor,
            boxShadow: `0 0 6px ${tierConfig.dotColor}`,
          }}
        />
        {compact ? tierConfig.shortLabel : tierConfig.label}
        {uncertainty !== undefined && uncertainty !== null && (
          <span style={{ opacity: 0.8, fontWeight: 500, marginLeft: "2px" }}>
            ±{(uncertainty * 100).toFixed(1)}%
          </span>
        )}
      </span>

      {/* Tooltip on Hover */}
      {showTooltip && (
        <div
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1000,
            width: "280px",
            padding: "12px 14px",
            borderRadius: "10px",
            background: "rgba(18, 24, 38, 0.95)",
            backdropFilter: "blur(20px)",
            border: `1px solid ${tierConfig.border}`,
            boxShadow: "0 12px 32px rgba(0, 0, 0, 0.6)",
            color: "#ffffff",
            fontSize: "0.72rem",
            pointerEvents: "none",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
            <span style={{ fontWeight: 700, color: tierConfig.color, fontFamily: "var(--font-mono)" }}>
              {tierConfig.label}
            </span>
            {caseHash && (
              <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                #{caseHash.slice(0, 8)}
              </span>
            )}
          </div>
          <p style={{ margin: "0 0 8px 0", color: "var(--text-secondary)", lineHeight: 1.4 }}>
            {tierConfig.description}
          </p>
          {(discrepancyPct !== undefined && discrepancyPct !== null) && (
            <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "6px", fontSize: "0.66rem" }}>
              <span style={{ color: "var(--text-muted)" }}>Attributed Discrepancy:</span>
              <span style={{ color: Math.abs(discrepancyPct) > 10 ? "#ffd60a" : "#30d158", fontWeight: 600 }}>
                {discrepancyPct > 0 ? `+${discrepancyPct.toFixed(2)}%` : `${discrepancyPct.toFixed(2)}%`}
              </span>
            </div>
          )}
          {(gciPct !== undefined && gciPct !== null) && (
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.66rem", marginTop: "2px" }}>
              <span style={{ color: "var(--text-muted)" }}>Mesh Convergence GCI:</span>
              <span style={{ color: gciPct < 3.0 ? "#30d158" : "#ffd60a", fontWeight: 600 }}>
                {gciPct.toFixed(2)}% (Target &lt; 3.0%)
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
