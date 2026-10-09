"use client";

import React from "react";

interface AerodynamicKpiCardsProps {
  cl?: number | null;
  cd?: number | null;
  cm?: number | null;
  surrogateCl?: number | null;
  surrogateCd?: number | null;
  status?: string;
  isExtrapolation?: boolean;
}

export const AerodynamicKpiCards: React.FC<AerodynamicKpiCardsProps> = ({
  cl,
  cd,
  cm,
  surrogateCl,
  surrogateCd,
  status = "VERIFIED_CFD",
  isExtrapolation = false,
}) => {
  // Compute Lift-to-Drag Ratio
  const ldRatio =
    cl !== null && cl !== undefined && cd !== null && cd !== undefined && cd > 0
      ? cl / cd
      : null;

  // Discrepancy calculations
  const clDelta =
    cl !== null && cl !== undefined && surrogateCl !== null && surrogateCl !== undefined
      ? ((cl - surrogateCl) / surrogateCl) * 100
      : null;

  const cdDelta =
    cd !== null && cd !== undefined && surrogateCd !== null && surrogateCd !== undefined
      ? ((cd - surrogateCd) / surrogateCd) * 100
      : null;

  return (
    <div className="aero-kpi-grid animate-fade-in">
      {/* 1. Lift Coefficient CL */}
      <div className="aero-kpi-card">
        <div className="aero-kpi-header">
          <span className="aero-kpi-label">LIFT COEFFICIENT</span>
          <span className="aero-kpi-chip aero-kpi-chip-blue">C_L</span>
        </div>
        <div className="aero-kpi-value-row">
          <span className="aero-kpi-value">
            {cl !== null && cl !== undefined ? cl.toFixed(4) : "—"}
          </span>
          {clDelta !== null && (
            <span
              className={`aero-kpi-delta ${
                Math.abs(clDelta) < 3.0
                  ? "aero-kpi-delta-good"
                  : "aero-kpi-delta-neutral"
              }`}
            >
              {clDelta >= 0 ? `+${clDelta.toFixed(1)}%` : `${clDelta.toFixed(1)}%`} vs surr
            </span>
          )}
        </div>
        <div className="aero-kpi-footer">
          <span className="aero-kpi-sub">
            Surrogate baseline:{" "}
            <strong>{surrogateCl !== null && surrogateCl !== undefined ? surrogateCl.toFixed(4) : "—"}</strong>
          </span>
          <span className="aero-kpi-status-dot green" title="Monotonic attached lift" />
        </div>
      </div>

      {/* 2. Drag Coefficient CD */}
      <div className="aero-kpi-card">
        <div className="aero-kpi-header">
          <span className="aero-kpi-label">DRAG COEFFICIENT</span>
          <span className="aero-kpi-chip aero-kpi-chip-teal">C_D</span>
        </div>
        <div className="aero-kpi-value-row">
          <span className="aero-kpi-value">
            {cd !== null && cd !== undefined ? cd.toFixed(4) : "—"}
          </span>
          {cdDelta !== null && (
            <span
              className={`aero-kpi-delta ${
                Math.abs(cdDelta) < 5.0
                  ? "aero-kpi-delta-good"
                  : Math.abs(cdDelta) < 15.0
                  ? "aero-kpi-delta-neutral"
                  : "aero-kpi-delta-warn"
              }`}
            >
              {cdDelta >= 0 ? `+${cdDelta.toFixed(1)}%` : `${cdDelta.toFixed(1)}%`} vs surr
            </span>
          )}
        </div>
        <div className="aero-kpi-footer">
          <span className="aero-kpi-sub">
            Second Law:{" "}
            <strong style={{ color: cd !== null && cd !== undefined && cd > 0 ? "var(--status-green)" : "var(--status-red)" }}>
              {cd !== null && cd !== undefined ? (cd > 0 ? "CD > 0 (PASSED)" : "NEGATIVE DRAG (VIOLATION)") : "Pending"}
            </strong>
          </span>
          <span className={`aero-kpi-status-dot ${cd && cd > 0 ? "green" : "amber"}`} />
        </div>
      </div>

      {/* 3. Pitching Moment CM */}
      <div className="aero-kpi-card">
        <div className="aero-kpi-header">
          <span className="aero-kpi-label">PITCHING MOMENT (c/4)</span>
          <span className="aero-kpi-chip aero-kpi-chip-purple">C_M</span>
        </div>
        <div className="aero-kpi-value-row">
          <span className="aero-kpi-value">
            {cm !== null && cm !== undefined ? cm.toFixed(4) : "—"}
          </span>
          <span className="aero-kpi-delta aero-kpi-delta-neutral">
            {cm !== null && cm !== undefined && cm < 0 ? "Nose-down stability" : "Trim neutral"}
          </span>
        </div>
        <div className="aero-kpi-footer">
          <span className="aero-kpi-sub">
            Reference axis: <strong>c/4 quarter-chord</strong>
          </span>
          <span className="aero-kpi-status-dot blue" />
        </div>
      </div>

      {/* 4. Aerodynamic Efficiency L/D */}
      <div className="aero-kpi-card">
        <div className="aero-kpi-header">
          <span className="aero-kpi-label">GLIDE EFFICIENCY</span>
          <span className="aero-kpi-chip aero-kpi-chip-indigo">L / D</span>
        </div>
        <div className="aero-kpi-value-row">
          <span className="aero-kpi-value" style={{ color: "#a5f3fc" }}>
            {ldRatio !== null ? ldRatio.toFixed(1) : "—"}
          </span>
          {ldRatio !== null && (
            <span className="aero-kpi-delta aero-kpi-delta-good">
              {ldRatio > 40 ? "High efficiency" : ldRatio > 20 ? "Cruising regime" : "Separated/stall"}
            </span>
          )}
        </div>
        <div className="aero-kpi-footer">
          <span className="aero-kpi-sub">
            Epistemic Tier: <strong>{status}</strong>
          </span>
          <span className="aero-kpi-status-dot green" />
        </div>
      </div>
    </div>
  );
};
