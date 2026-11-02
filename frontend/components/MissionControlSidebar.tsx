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
  ShieldAlert,
  Rocket,
  Globe,
} from "lucide-react";

export type WorkspaceNavMode =
  | "SHOWCASE"
  | "SOVEREIGN_MISSION_CONTROL"
  | "AUTONOMOUS_COCKPIT"
  | "VIRTUAL_WIND_TUNNEL"
  | "ISRO_NASA_MISSION"
  | "INVESTIGATION"
  | "DIGITAL_TWIN"
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
  | "MODEL_ZOO"
  | "GOVERNOR_HARNESS";

interface MissionControlSidebarProps {
  activeMode: WorkspaceNavMode;
  onSelectMode: (mode: WorkspaceNavMode) => void;
  onOpenCommandPalette: () => void;
  onOpenTour: () => void;
  onOpenExport: () => void;
  hardwareSafe?: boolean;
  defaultCollapsed?: boolean;
}

export const MissionControlSidebar: React.FC<MissionControlSidebarProps> = ({
  activeMode,
  onSelectMode,
  onOpenCommandPalette,
  onOpenTour,
  onOpenExport,
  hardwareSafe = true,
  defaultCollapsed = false,
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const navItems = [
    {
      id: "SHOWCASE" as WorkspaceNavMode,
      label: "Mission Briefing & Overview",
      shortLabel: "Briefing",
      icon: <Layers size={18} />,
      badge: "Architecture",
    },
    {
      id: "SOVEREIGN_MISSION_CONTROL" as WorkspaceNavMode,
      label: "Sovereign Mission Control",
      shortLabel: "Mission Deck",
      icon: <Globe size={18} />,
      badge: "MoCA / ISRO",
    },
    {
      id: "AUTONOMOUS_COCKPIT" as WorkspaceNavMode,
      label: "Autonomous Research Cockpit",
      shortLabel: "Cockpit",
      icon: <Brain size={18} />,
      badge: "Flagship AI",
    },
    {
      id: "VIRTUAL_WIND_TUNNEL" as WorkspaceNavMode,
      label: "3D Virtual Wind Tunnel",
      shortLabel: "Wind Tunnel",
      icon: <Wind size={18} />,
      badge: "Turnkey CAE",
    },
    {
      id: "ISRO_NASA_MISSION" as WorkspaceNavMode,
      label: "ISRO & NASA Mission Deck",
      shortLabel: "Mission Deck",
      icon: <Globe size={18} />,
      badge: "Agency",
    },
    {
      id: "INVESTIGATION" as WorkspaceNavMode,
      label: "Investigation Flow",
      shortLabel: "Inquiry",
      icon: <Compass size={18} />,
      badge: "Core",
    },
    {
      id: "DIGITAL_TWIN" as WorkspaceNavMode,
      label: "Aerospace Digital Twin",
      shortLabel: "Digital Twin",
      icon: <Rocket size={18} />,
      badge: "Flagship",
    },
    {
      id: "GOVERNOR_HARNESS" as WorkspaceNavMode,
      label: "Safety Governor & Agent",
      shortLabel: "Governor",
      icon: <ShieldAlert size={18} />,
      badge: "2.0 Active",
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
      label: "Scientific Reasoning Engine",
      shortLabel: "Reasoning",
      icon: <Brain size={18} />,
      badge: "Epistemic",
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
      className="apple-glass"
      style={{
        width: collapsed ? "72px" : "260px",
        minWidth: collapsed ? "72px" : "260px",
        height: "100vh",
        position: "sticky",
        top: 0,
        background: "rgba(10, 15, 26, 0.88)",
        borderRight: "1px solid rgba(255, 255, 255, 0.09)",
        boxShadow: "inset 0 1px 0 0 rgba(255, 255, 255, 0.12)",
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
              borderRadius: "8px",
              background: "linear-gradient(135deg, #1a2030 0%, #0e111a 100%)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#f59e0b",
              fontSize: "1.1rem",
              fontWeight: 800,
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.4)",
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
                  fontSize: "1rem",
                  letterSpacing: "0.08em",
                  color: "#f8fafc",
                }}
              >
                AASI
              </div>
              <div
                style={{
                  fontSize: "0.64rem",
                  color: "#f59e0b",
                  letterSpacing: "0.06em",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono)",
                }}
              >
                AEROSPACE CAE &amp; V&amp;V
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
                padding: collapsed ? "10px" : "9px 12px",
                borderRadius: "6px",
                border: isActive
                  ? "1px solid rgba(245, 158, 11, 0.35)"
                  : "1px solid transparent",
                background: isActive
                  ? "rgba(245, 158, 11, 0.08)"
                  : "transparent",
                boxShadow: isActive
                  ? "0 2px 8px rgba(0, 0, 0, 0.25)"
                  : "none",
                color: isActive ? "#f8fafc" : "#94a3b8",
                fontSize: "0.82rem",
                fontWeight: isActive ? 600 : 500,
                cursor: "pointer",
                transition: "all 140ms cubic-bezier(0.16, 1, 0.3, 1)",
                whiteSpace: "nowrap",
                position: "relative",
              }}
              title={collapsed ? item.label : undefined}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ color: isActive ? "#f59e0b" : "#64748b" }}>
                  {item.icon}
                </span>
                {!collapsed && <span>{item.label}</span>}
              </div>

              {!collapsed && item.badge && (
                <span
                  style={{
                    fontSize: "0.64rem",
                    padding: "2px 7px",
                    borderRadius: "3px",
                    background: isActive
                      ? "rgba(245, 158, 11, 0.15)"
                      : "rgba(255, 255, 255, 0.06)",
                    color: isActive ? "#f59e0b" : "#64748b",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 600,
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
            <HelpCircle size={18} color="#38bdf8" />
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
