"use client";

import React, { useState } from "react";
import {
  Compass,
  Zap,
  Layers,
  Database,
  Brain,
  Cpu,
  Sliders,
  FileText,
  Lightbulb,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Command,
  HelpCircle,
  HardDrive,
  Activity,
  Award,
  Wind,
  ArrowLeftRight,
  CreditCard,
} from "lucide-react";

export type WorkspaceNavMode =
  | "INVESTIGATION"
  | "CONNECTED_PIPELINE"
  | "POLAR_STUDIO"
  | "COMPARISON"
  | "ENTERPRISE"
  | "COGNITIVE_BRAIN"
  | "AERODB"
  | "HYPOTHESES"
  | "COMPUTE"
  | "SURROGATE"
  | "MEMORY"
  | "MODEL_ZOO";

interface MissionControlSidebarProps {
  activeMode: WorkspaceNavMode;
  onSelectMode: (mode: WorkspaceNavMode) => void;
  onOpenCommandPalette: () => void;
  onOpenTour: () => void;
  onOpenExport: () => void;
  hardwareSafe?: boolean;
}

export const MissionControlSidebar: React.FC<MissionControlSidebarProps> = ({
  activeMode,
  onSelectMode,
  onOpenCommandPalette,
  onOpenTour,
  onOpenExport,
  hardwareSafe = true,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    {
      id: "INVESTIGATION" as WorkspaceNavMode,
      label: "Investigation Flow",
      shortLabel: "Inquiry",
      icon: <Compass size={18} />,
      badge: "Core",
    },
    {
      id: "CONNECTED_PIPELINE" as WorkspaceNavMode,
      label: "Connected Pipeline",
      shortLabel: "Pipeline",
      icon: <Zap size={18} />,
      badge: "Auto",
    },
    {
      id: "POLAR_STUDIO" as WorkspaceNavMode,
      label: "Polar & Flow Studio",
      shortLabel: "Polar",
      icon: <Wind size={18} />,
      badge: "Interactive",
    },
    {
      id: "COMPARISON" as WorkspaceNavMode,
      label: "Portfolio Compare",
      shortLabel: "Compare",
      icon: <ArrowLeftRight size={18} />,
      badge: "Diff",
    },
    {
      id: "HYPOTHESES" as WorkspaceNavMode,
      label: "Hypotheses & Plan",
      shortLabel: "Hypothesis",
      icon: <Lightbulb size={18} />,
    },
    {
      id: "MODEL_ZOO" as WorkspaceNavMode,
      label: "Neural Model Zoo",
      shortLabel: "Model Zoo",
      icon: <Layers size={18} />,
      badge: "15 Models",
    },
    {
      id: "AERODB" as WorkspaceNavMode,
      label: "Universal Aero DB",
      shortLabel: "Aero DB",
      icon: <Database size={18} />,
      badge: "Oracle",
    },
    {
      id: "COGNITIVE_BRAIN" as WorkspaceNavMode,
      label: "Cognitive Brain",
      shortLabel: "Cognitive",
      icon: <Brain size={18} />,
    },
    {
      id: "SURROGATE" as WorkspaceNavMode,
      label: "Surrogate Studio",
      shortLabel: "Surrogate",
      icon: <Sliders size={18} />,
    },
    {
      id: "COMPUTE" as WorkspaceNavMode,
      label: "Compute Fabric",
      shortLabel: "Compute",
      icon: <Cpu size={18} />,
    },
    {
      id: "ENTERPRISE" as WorkspaceNavMode,
      label: "Enterprise & Quotas",
      shortLabel: "Enterprise",
      icon: <CreditCard size={18} />,
      badge: "Commercial",
    },
  ];

  return (
    <aside
      style={{
        width: collapsed ? "72px" : "260px",
        minWidth: collapsed ? "72px" : "260px",
        height: "100vh",
        position: "sticky",
        top: 0,
        background: "linear-gradient(180deg, rgba(12, 17, 29, 0.95), rgba(7, 10, 18, 0.98))",
        borderRight: "1px solid rgba(255, 255, 255, 0.08)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        display: "flex",
        flexDirection: "column",
        transition: "width 240ms cubic-bezier(0.16, 1, 0.3, 1), min-width 240ms cubic-bezier(0.16, 1, 0.3, 1)",
        zIndex: 90,
        userSelect: "none",
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: collapsed ? "16px 10px" : "18px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", overflow: "hidden" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, rgba(0, 119, 237, 0.35), rgba(0, 210, 255, 0.2))",
              border: "1px solid rgba(100, 210, 255, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#64d2ff",
              fontSize: "1.1rem",
              fontWeight: 700,
              boxShadow: "0 0 15px rgba(0, 210, 255, 0.2)",
              flexShrink: 0,
            }}
          >
            ◈
          </div>
          {!collapsed && (
            <div style={{ whiteSpace: "nowrap" }}>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontWeight: 800,
                  fontSize: "1.05rem",
                  letterSpacing: "0.08em",
                  color: "#f8fafc",
                }}
              >
                AASI
              </div>
              <div
                style={{
                  fontSize: "0.66rem",
                  color: "#64d2ff",
                  letterSpacing: "0.04em",
                  fontWeight: 600,
                }}
              >
                ENTERPRISE AEROSPACE
              </div>
            </div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "6px",
            color: "#94a3b8",
            width: "24px",
            height: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "all 140ms ease",
          }}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Command Palette Trigger */}
      <div style={{ padding: collapsed ? "12px 8px" : "12px 14px" }}>
        <button
          onClick={onOpenCommandPalette}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "space-between",
            padding: collapsed ? "10px" : "9px 12px",
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "8px",
            color: "#94a3b8",
            fontSize: "0.78rem",
            cursor: "pointer",
            transition: "all 140ms ease",
          }}
          title="Search or jump to command (Cmd+K)"
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Command size={14} color="#64d2ff" />
            {!collapsed && <span>Search &amp; Jump...</span>}
          </div>
          {!collapsed && (
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.68rem",
                padding: "2px 5px",
                borderRadius: "4px",
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              ⌘K
            </span>
          )}
        </button>
      </div>

      {/* Navigation List */}
      <nav
        style={{
          flex: 1,
          padding: collapsed ? "8px 6px" : "8px 10px",
          display: "flex",
          flexDirection: "column",
          gap: "4px",
          overflowY: "auto",
        }}
      >
        {!collapsed && (
          <div
            style={{
              padding: "4px 8px 8px",
              fontSize: "0.64rem",
              fontWeight: 700,
              letterSpacing: "0.08em",
              color: "#475569",
              textTransform: "uppercase",
            }}
          >
            Engineering Workspaces
          </div>
        )}

        {navItems.map((item) => {
          const isActive = activeMode === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectMode(item.id)}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: collapsed ? "center" : "space-between",
                padding: collapsed ? "11px" : "10px 12px",
                borderRadius: "9px",
                border: isActive
                  ? "1px solid rgba(100, 210, 255, 0.35)"
                  : "1px solid transparent",
                background: isActive
                  ? "linear-gradient(90deg, rgba(0, 119, 237, 0.22), rgba(0, 210, 255, 0.1))"
                  : "transparent",
                color: isActive ? "#ffffff" : "#94a3b8",
                fontSize: "0.82rem",
                fontWeight: isActive ? 600 : 500,
                cursor: "pointer",
                transition: "all 140ms ease",
                whiteSpace: "nowrap",
                position: "relative",
              }}
              title={collapsed ? item.label : undefined}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ color: isActive ? "#64d2ff" : "#64748b" }}>
                  {item.icon}
                </span>
                {!collapsed && <span>{item.label}</span>}
              </div>

              {!collapsed && item.badge && (
                <span
                  style={{
                    fontSize: "0.64rem",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    background: isActive
                      ? "rgba(0, 210, 255, 0.2)"
                      : "rgba(255, 255, 255, 0.05)",
                    color: isActive ? "#64d2ff" : "#64748b",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Action Shortcuts */}
        <div style={{ marginTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.06)", paddingTop: "12px" }}>
          {!collapsed && (
            <div
              style={{
                padding: "4px 8px 8px",
                fontSize: "0.64rem",
                fontWeight: 700,
                letterSpacing: "0.08em",
                color: "#475569",
                textTransform: "uppercase",
              }}
            >
              Deliverables &amp; Help
            </div>
          )}

          <button
            onClick={onOpenExport}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-start",
              gap: "10px",
              padding: collapsed ? "11px" : "10px 12px",
              borderRadius: "9px",
              border: "1px solid transparent",
              background: "transparent",
              color: "#94a3b8",
              fontSize: "0.82rem",
              cursor: "pointer",
              transition: "all 140ms ease",
            }}
            title="Export Certification Dossier"
          >
            <FileText size={18} color="#14b8a6" />
            {!collapsed && <span>Export Dossier (ASME)</span>}
          </button>

          <button
            onClick={onOpenTour}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-start",
              gap: "10px",
              padding: collapsed ? "11px" : "10px 12px",
              borderRadius: "9px",
              border: "1px solid transparent",
              background: "transparent",
              color: "#94a3b8",
              fontSize: "0.82rem",
              cursor: "pointer",
              transition: "all 140ms ease",
            }}
            title="Guided System Tour"
          >
            <HelpCircle size={18} color="#a855f7" />
            {!collapsed && <span>Guided System Tour</span>}
          </button>
        </div>
      </nav>

      {/* Telemetry Footer */}
      <div
        style={{
          padding: collapsed ? "12px 8px" : "14px 16px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          background: "rgba(5, 8, 15, 0.7)",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "space-between",
            fontSize: "0.72rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                background: hardwareSafe ? "#10b981" : "#f59e0b",
                boxShadow: hardwareSafe ? "0 0 8px rgba(16, 185, 129, 0.6)" : "none",
              }}
            />
            {!collapsed && (
              <span style={{ color: "#94a3b8", fontWeight: 500 }}>
                Safety Guard Active
              </span>
            )}
          </div>
          {!collapsed && (
            <span
              style={{
                fontFamily: "var(--font-mono)",
                color: "#10b981",
                fontSize: "0.68rem",
              }}
            >
              PROTECTED
            </span>
          )}
        </div>

        {!collapsed && (
          <div
            style={{
              fontSize: "0.65rem",
              color: "#475569",
              lineHeight: 1.4,
              borderTop: "1px dashed rgba(255, 255, 255, 0.06)",
              paddingTop: "6px",
            }}
          >
            Zero Hardware Bloat • ASME V&amp;V 20 • Epistemic Integrity
          </div>
        )}
      </div>
    </aside>
  );
};
