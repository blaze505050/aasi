"use client";

import React from "react";
import { Building2, ShieldCheck, HelpCircle, FileText, Activity } from "lucide-react";

export interface InvestigationStatusBarProps {
  organizationName?: string;
  projectName?: string;
  planName?: string;
  investigationsUsed?: number;
  investigationsLimit?: number;
  engineState: "IDLE" | "HYPOTHESIZING" | "PLANNING" | "EXECUTING" | "VERIFYING" | "COMPLETED" | "RECOVERING" | "ERROR";
  currentCycle?: number;
  maxCycles?: number;
  activeGeometry?: string;
  onOpenTour?: () => void;
  onOpenExport?: () => void;
  hasResults?: boolean;
}

export const InvestigationStatusBar: React.FC<InvestigationStatusBarProps> = ({
  organizationName = "AeroTech Aerospace",
  projectName = "Transonic Wing Discovery",
  planName = "Enterprise",
  investigationsUsed = 4,
  investigationsLimit = 25,
  engineState,
  currentCycle = 1,
  maxCycles = 2,
  activeGeometry = "NACA 0012",
  onOpenTour,
  onOpenExport,
  hasResults = false,
}) => {
  const stateConfig = {
    IDLE: {
      label: "STANDBY // READY",
      color: "#94a3b8",
      bg: "rgba(148, 163, 184, 0.1)",
      dotColor: "#94a3b8",
      pulse: false,
    },
    HYPOTHESIZING: {
      label: "HYPOTHESIS FORMULATION",
      color: "#38bdf8",
      bg: "rgba(56, 189, 248, 0.12)",
      dotColor: "#38bdf8",
      pulse: true,
    },
    PLANNING: {
      label: "SCIENTIFIC EXPERIMENT PLAN",
      color: "#f59e0b",
      bg: "rgba(245, 158, 11, 0.12)",
      dotColor: "#f59e0b",
      pulse: true,
    },
    EXECUTING: {
      label: "MULTI-FIDELITY SOLVER EXECUTION",
      color: "#00d2ff",
      bg: "rgba(0, 210, 255, 0.12)",
      dotColor: "#00d2ff",
      pulse: true,
    },
    VERIFYING: {
      label: "ASME V&V 20 NUMERICAL AUDIT",
      color: "#10b981",
      bg: "rgba(16, 185, 129, 0.12)",
      dotColor: "#10b981",
      pulse: true,
    },
    COMPLETED: {
      label: "INVESTIGATION COMPLETE // VERIFIED",
      color: "#10b981",
      bg: "rgba(16, 185, 129, 0.12)",
      dotColor: "#10b981",
      pulse: false,
    },
    RECOVERING: {
      label: "ANOMALY ATTRIBUTION & RECOVERY",
      color: "#f59e0b",
      bg: "rgba(245, 158, 11, 0.14)",
      dotColor: "#f59e0b",
      pulse: true,
    },
    ERROR: {
      label: "DISCREPANCY ALERT // REVIEW REQUIRED",
      color: "#ef4444",
      bg: "rgba(239, 68, 68, 0.14)",
      dotColor: "#ef4444",
      pulse: false,
    },
  }[engineState] || {
    label: engineState,
    color: "#94a3b8",
    bg: "rgba(148, 163, 184, 0.1)",
    dotColor: "#94a3b8",
    pulse: false,
  };

  const usagePct = Math.min(100, Math.round((investigationsUsed / investigationsLimit) * 100));

  return (
    <div
      style={{
        width: "100%",
        background: "rgba(10, 15, 28, 0.72)",
        backdropFilter: "blur(24px) saturate(180%)",
        WebkitBackdropFilter: "blur(24px) saturate(180%)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "12px",
        padding: "8px 16px",
        marginBottom: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "10px",
        boxShadow: "inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 8px 24px rgba(0, 0, 0, 0.35)",
      }}
    >
      {/* Left: Organization & Project Context */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "0.76rem",
            color: "#f8fafc",
            fontWeight: 600,
          }}
        >
          <Building2 size={13} color="#38bdf8" />
          <span>{organizationName}</span>
          <span style={{ color: "#475569", fontSize: "0.7rem" }}>/</span>
          <span style={{ color: "#94a3b8", fontWeight: 500 }}>{projectName}</span>
        </div>

        {/* Plan & Quota Pill */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "2px 8px",
            borderRadius: "6px",
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.07)",
            fontSize: "0.66rem",
            color: "#94a3b8",
            fontFamily: "var(--font-mono)",
          }}
          title={`${investigationsUsed} of ${investigationsLimit} monthly investigations used`}
        >
          <span style={{ color: "#10b981", fontWeight: 700 }}>{planName}</span>
          <span style={{ color: "#475569" }}>·</span>
          <span>{investigationsUsed}/{investigationsLimit} RUNS</span>
          <div
            style={{
              width: "32px",
              height: "3px",
              borderRadius: "2px",
              background: "rgba(255, 255, 255, 0.1)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${usagePct}%`,
                height: "100%",
                background: usagePct > 85 ? "#f59e0b" : "#10b981",
                borderRadius: "2px",
              }}
            />
          </div>
        </div>
      </div>

      {/* Center: Mission Control State Ribbon */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "5px 12px",
            borderRadius: "9999px",
            background: stateConfig.bg,
            border: `1px solid ${stateConfig.color}40`,
            fontSize: "0.72rem",
            fontWeight: 700,
            fontFamily: "var(--font-mono)",
            color: stateConfig.color,
            letterSpacing: "0.05em",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: stateConfig.dotColor,
              boxShadow: `0 0 8px ${stateConfig.dotColor}`,
              animation: stateConfig.pulse ? "pulse 1.5s infinite" : "none",
            }}
          />
          {stateConfig.label}
        </div>

        {/* Cycle indicator */}
        <span
          style={{
            fontSize: "0.68rem",
            fontFamily: "var(--font-mono)",
            color: "var(--text-muted)",
            background: "rgba(255, 255, 255, 0.03)",
            padding: "4px 8px",
            borderRadius: "6px",
            border: "1px solid rgba(255, 255, 255, 0.05)",
          }}
        >
          Cycle {currentCycle} / {maxCycles}
        </span>
      </div>

      {/* Right: Solvers & Action Shortcuts */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {/* Solver health indicators */}
        <div style={{ display: "flex", gap: "6px", fontSize: "0.62rem", fontFamily: "var(--font-mono)" }}>
          <span style={{ color: "#30d158" }} title="Fast Panel Discrete Vortex Solver Operational">● Panel (0.04s)</span>
          <span style={{ color: "#f59e0b" }} title="Physics-Informed Neural Operator Online">● Surrogate</span>
          <span style={{ color: "#0a84ff" }} title="OpenFOAM Conformal C-Grid Cloud Compute Staged">● OpenFOAM</span>
        </div>

        {/* Quick Tour Button */}
        {onOpenTour && (
          <button
            onClick={onOpenTour}
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: "8px",
              padding: "5px 10px",
              color: "#64d2ff",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              transition: "all 150ms ease",
            }}
            title="Open Interactive Guided Tour"
          >
            <span>💡</span> Tour
          </button>
        )}

        {/* Export Report Quick Trigger */}
        {hasResults && onOpenExport && (
          <button
            onClick={onOpenExport}
            style={{
              background: "linear-gradient(135deg, rgba(48, 209, 88, 0.2), rgba(0, 199, 190, 0.2))",
              border: "1px solid rgba(48, 209, 88, 0.4)",
              borderRadius: "8px",
              padding: "5px 12px",
              color: "#70ff9c",
              fontSize: "0.72rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 2px 10px rgba(48, 209, 88, 0.2)",
            }}
            title="Generate and Export ASME V&V 20 Certification Dossier"
          >
            <span>📜</span> Export Dossier
          </button>
        )}
      </div>
    </div>
  );
};
