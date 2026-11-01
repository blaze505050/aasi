"use client";

import React, { useState, useEffect } from "react";
import { InvestigationWorkspace } from "../components/InvestigationWorkspace";
import { ChatPanel } from "../components/ChatPanel";
import { MissionControlSidebar, WorkspaceNavMode } from "../components/MissionControlSidebar";
import { CommandPaletteModal, CommandItem } from "../components/CommandPaletteModal";
import {
  Search,
  Command,
  FileText,
  HelpCircle,
  Activity,
  ShieldCheck,
  Layers,
  Cpu,
  Database,
  Terminal,
  Zap,
  Compass,
  Wind,
  ArrowLeftRight,
  CreditCard,
  User as UserIcon,
  Lock,
  Box,
  Sparkles,
  Rocket,
  Brain,
} from "lucide-react";
import { AuthModal, AuthUser } from "../components/AuthModal";
import { AuditTrailModal } from "../components/AuditTrailModal";
import { EnterpriseOverviewModal } from "../components/EnterpriseOverviewModal";
import { ThreeDimensionalPressureMesh } from "../components/ThreeDimensionalPressureMesh";
import { AirfoilOptimizationStudio } from "../components/AirfoilOptimizationStudio";
import { EnterpriseTelemetryDashboard } from "../components/EnterpriseTelemetryDashboard";
import { GovernorTaskHarnessPanel } from "../components/GovernorTaskHarnessPanel";
import { DigitalTwinStudio } from "../components/DigitalTwinStudio";
import { AeroDbPanel } from "../components/AeroDbPanel";
import { EpistemicRadarPanel } from "../components/EpistemicRadarPanel";
import { SubdomainBenchmarkModal } from "../components/SubdomainBenchmarkModal";
import { AasiPublicShowcase } from "../components/AasiPublicShowcase";
import { VirtualWindTunnelStudio } from "../components/VirtualWindTunnelStudio";
import { IsroNasaMissionStudio } from "../components/IsroNasaMissionStudio";
import { AutonomousResearchCockpit } from "../components/AutonomousResearchCockpit";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function AASIApp() {
  const [chatOpen, setChatOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [activeNavMode, setActiveNavMode] = useState<WorkspaceNavMode>("INVESTIGATION");
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);
  const [enterpriseModalOpen, setEnterpriseModalOpen] = useState(false);
  const [mesh3DOpen, setMesh3DOpen] = useState(false);
  const [optStudioOpen, setOptStudioOpen] = useState(false);
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const [subdomainBenchmarkOpen, setSubdomainBenchmarkOpen] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [hardwareStatus, setHardwareStatus] = useState<{ protected: boolean; ram_free_gb?: number }>({
    protected: true,
  });

  // Check stored auth session and URL deep-link mode on startup
  useEffect(() => {
    try {
      const stored = localStorage.getItem("aasi_user");
      if (stored) {
        setAuthUser(JSON.parse(stored));
      } else {
        // Fallback default researcher profile
        setAuthUser({
          user_id: "USR-DEFAULT-01",
          username: "researcher",
          email: "researcher@aasi.aero",
          role: "RESEARCHER",
        });
      }

      // Deep-linking via query parameter (e.g. ?mode=showcase, ?mode=windtunnel)
      if (typeof window !== "undefined") {
        const params = new URLSearchParams(window.location.search);
        const modeParam = params.get("mode");
        if (modeParam) {
          const upper = modeParam.toUpperCase();
          if (
            upper === "SHOWCASE" ||
            upper === "AUTONOMOUS_COCKPIT" ||
            upper === "COCKPIT" ||
            upper === "VIRTUAL_WIND_TUNNEL" ||
            upper === "WINDTUNNEL" ||
            upper === "ISRO_NASA_MISSION" ||
            upper === "MISSION" ||
            upper === "DIGITAL_TWIN" ||
            upper === "AERODB"
          ) {
            if (upper === "WINDTUNNEL") setActiveNavMode("VIRTUAL_WIND_TUNNEL");
            else if (upper === "MISSION") setActiveNavMode("ISRO_NASA_MISSION");
            else if (upper === "COCKPIT") setActiveNavMode("AUTONOMOUS_COCKPIT");
            else setActiveNavMode(upper as WorkspaceNavMode);
          }
        }
      }
    } catch {
      /* ignore */
    }
  }, []);

  // Check hardware safety status from backend API
  useEffect(() => {
    fetch(`${API_BASE}/api/datasets/safety-status`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.metrics) {
          setHardwareStatus({
            protected: data.safe_operating_mode,
            ram_free_gb: data.metrics.ram_free_gb,
          });
        }
      })
      .catch(() => {
        /* fallback to safe mode */
      });
  }, []);

  // Global Keyboard Shortcuts (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Command palette catalog
  const commands: CommandItem[] = [
    {
      id: "cmd-inquiry-1",
      category: "Inquiries",
      title: "NACA 0012 Subsonic Cruise Audit (α=6°)",
      description: "Reconcile verified RANS CFD (CL=0.6480) with ML surrogate (CL=0.6363).",
      badge: "EXP 1",
      icon: <Compass size={16} />,
      action: () => setActiveNavMode("INVESTIGATION"),
    },
    {
      id: "cmd-inquiry-2",
      category: "Inquiries",
      title: "NACA 4412 Post-Stall Detachment (α=20°)",
      description: "Severe post-stall detachment audit with divergence mitigation.",
      badge: "EXP 2",
      icon: <Activity size={16} />,
      action: () => setActiveNavMode("INVESTIGATION"),
    },
    {
      id: "cmd-inquiry-3",
      category: "Inquiries",
      title: "Inviscid Potential vs. Viscous RANS Contradiction",
      description: "d'Alembert paradox attribution & shear stress decomposition.",
      badge: "EXP 3",
      icon: <Zap size={16} />,
      action: () => setActiveNavMode("INVESTIGATION"),
    },
    {
      id: "cmd-ws-cockpit",
      category: "Workspaces",
      title: "Launch Autonomous Aerospace Cockpit",
      description: "AASI 2.0 8-agent intelligence core, NACA 4412 flagship loop, CFD boundary layer lab, and FNO neural operators.",
      badge: "Flagship AI",
      icon: <Brain size={16} />,
      action: () => setActiveNavMode("AUTONOMOUS_COCKPIT"),
    },
    {
      id: "cmd-ws-showcase",
      category: "Workspaces",
      title: "Open Executive Platform Showcase",
      description: "Overview of AASI autonomous aerospace intelligence, benchmarks, and problem statement.",
      badge: "Executive",
      icon: <Sparkles size={16} />,
      action: () => setActiveNavMode("SHOWCASE"),
    },
    {
      id: "cmd-ws-windtunnel",
      category: "Workspaces",
      title: "Launch 3D Virtual Wind Tunnel",
      description: "SimScale/Airshaper automated CAE: drag-and-drop CAD, real-time WebGL flowfield, surface Cp, and forces.",
      badge: "Turnkey CAE",
      icon: <Wind size={16} />,
      action: () => setActiveNavMode("VIRTUAL_WIND_TUNNEL"),
    },
    {
      id: "cmd-ws-isronasa",
      category: "Workspaces",
      title: "Launch ISRO & NASA Mission Architecture Deck",
      description: "Launch vehicle ascent, dynamic pressure Max-Q, aerothermal heating, and satellite orbit decay lifetime.",
      badge: "Mission Grade",
      icon: <Rocket size={16} />,
      action: () => setActiveNavMode("ISRO_NASA_MISSION"),
    },
    {
      id: "cmd-ws-digitaltwin",
      category: "Workspaces",
      title: "Launch Aerospace Digital Twin Studio",
      description: "Interactive 3D simulation for Rocket, Drone/eVTOL, Commercial Jet, and Satellite with real-time fault injection.",
      badge: "Flagship",
      icon: <Rocket size={16} />,
      action: () => setActiveNavMode("DIGITAL_TWIN"),
    },
    {
      id: "cmd-ws-pipeline",
      category: "Workspaces",
      title: "Switch to Connected Pipeline Workspace",
      description: "Launch end-to-end 6-stage autonomous aerodynamic workflow.",
      badge: "Automated",
      icon: <Zap size={16} />,
      action: () => setActiveNavMode("CONNECTED_PIPELINE"),
    },
    {
      id: "cmd-ws-modelzoo",
      category: "Workspaces",
      title: "Explore Neural Model Zoo (15 Architectures)",
      description: "Inspect MeshGraphNet, Transolver, DPOT, and DoMINO neural operators.",
      badge: "Model Zoo",
      icon: <Layers size={16} />,
      action: () => setActiveNavMode("MODEL_ZOO"),
    },
    {
      id: "cmd-ws-aerodb",
      category: "Workspaces",
      title: "Search Universal CFD & Polar Catalog",
      description: "12 verified aerospace benchmarks, 1,500+ airfoil polars, NASA TMR & AGARD.",
      badge: "Oracle",
      icon: <Database size={16} />,
      action: () => setActiveNavMode("AERODB"),
    },
    {
      id: "cmd-ws-polarstudio",
      category: "Workspaces",
      title: "Open Polar & Flowfield Studio",
      description: "Interactive SVG polar curves, live operating points, and streamline flowfields.",
      badge: "Vector Studio",
      icon: <Wind size={16} />,
      action: () => setActiveNavMode("POLAR_STUDIO"),
    },
    {
      id: "cmd-ws-comparison",
      category: "Workspaces",
      title: "Open Portfolio Comparison Matrix",
      description: "Multi-airfoil differential comparison across NACA and supercritical sections.",
      badge: "Comparison",
      icon: <ArrowLeftRight size={16} />,
      action: () => setActiveNavMode("COMPARISON"),
    },
    {
      id: "cmd-ws-enterprise",
      category: "Workspaces",
      title: "Commercial Tier & Enterprise Quotas",
      description: "Manage subscription plans, API credit usage, and ASME V&V 20 signoffs.",
      badge: "Enterprise",
      icon: <CreditCard size={16} />,
      action: () => setActiveNavMode("ENTERPRISE"),
    },
    {
      id: "cmd-action-export",
      category: "Actions",
      title: "Export ASME V&V 20 Certification Dossier",
      description: "Generate compliant aerospace engineering report (HTML/PDF/JSON).",
      badge: "ASME V&V 20",
      icon: <FileText size={16} />,
      action: () => setExportOpen(true),
    },
    {
      id: "cmd-action-tour",
      category: "Actions",
      title: "Open Guided System Tour",
      description: "Interactive onboarding walkthrough of AASI autonomous aerospace intelligence.",
      badge: "Guide",
      icon: <HelpCircle size={16} />,
      action: () => setTourOpen(true),
    },
  ];

  return (
    <div className="mission-control-layout">
      {/* ─── Mission Control Collapsible Sidebar ─── */}
      <MissionControlSidebar
        activeMode={activeNavMode}
        onSelectMode={(mode) => setActiveNavMode(mode)}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        onOpenTour={() => setTourOpen(true)}
        onOpenExport={() => setExportOpen(true)}
        hardwareSafe={hardwareStatus.protected}
      />

      {/* ─── Main Viewport Area ─── */}
      <div className="mission-control-viewport">
        {/* ─── Top Mission Control Bar (SpaceX + Apple Glassmorphic Flight Deck) ─── */}
        <header className="spacex-flight-deck">
          {/* Left: Mission Identity & Real-Time Telemetry */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.78rem",
                color: "#38bdf8",
                fontWeight: 700,
                letterSpacing: "0.04em",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                whiteSpace: "nowrap",
              }}
            >
              <span>AASI // FLIGHT CONTROL</span>
              <span className="header-breadcrumb-sub" style={{ color: "#475569" }}>/</span>
              <span className="header-breadcrumb-sub" style={{ color: "#94a3b8", fontWeight: 500, fontSize: "0.72rem" }}>
                AERODYNAMICS FABRIC
              </span>
            </div>

            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "3px 8px",
                borderRadius: "9999px",
                background: "rgba(16, 185, 129, 0.08)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                color: "#10b981",
                fontSize: "0.66rem",
                fontWeight: 600,
                fontFamily: "var(--font-mono)",
                letterSpacing: "0.03em",
                whiteSpace: "nowrap",
              }}
              title="Real-time operational status and physics dataset integrity"
            >
              <span
                style={{
                  width: "5px",
                  height: "5px",
                  borderRadius: "50%",
                  background: "#10b981",
                  boxShadow: "0 0 6px rgba(16, 185, 129, 0.6)",
                }}
              />
              SYS: NOMINAL
            </span>
          </div>

          {/* Center: SpaceX Capsule Flight Tools (Frosted Glass Segmented Pill) */}
          <nav className="flight-tools-capsule" aria-label="Flight Tools Deck">
            {/* 3D Surface Pressure (Cp) & Mesh */}
            <button
              onClick={() => setMesh3DOpen(true)}
              className="flight-tool-btn cyan"
              title="Launch interactive 3D WebGL CFD surface mesh and Cp pressure distribution"
            >
              <Box size={13} color="#38bdf8" />
              <span className="flight-tool-label">3D Flowfield</span>
            </button>

            {/* Shape Optimization Studio */}
            <button
              onClick={() => setOptStudioOpen(true)}
              className="flight-tool-btn amber"
              title="Autonomous airfoil shape optimization to maximize L/D under structural constraints"
            >
              <Sparkles size={13} color="#f59e0b" />
              <span className="flight-tool-label">Shape Studio</span>
            </button>

            {/* Mission Telemetry & Observability */}
            <button
              onClick={() => setTelemetryOpen(true)}
              className="flight-tool-btn emerald"
              title="View live P50/P95/P99 latency, cognitive engine telemetry, and system health"
            >
              <Activity size={13} color="#10b981" />
              <span className="flight-tool-label">Telemetry</span>
            </button>

            {/* Cryptographic SHA-256 Audit Trail */}
            <button
              onClick={() => setAuditModalOpen(true)}
              className="flight-tool-btn cyan"
              title="Inspect tamper-evident SHA-256 cryptographic audit trail"
            >
              <Lock size={13} color="#38bdf8" />
              <span className="flight-tool-label">Audit Trail</span>
            </button>

            {/* Enterprise & V&V Certification */}
            <button
              onClick={() => setEnterpriseModalOpen(true)}
              className="flight-tool-btn amber"
              title="Enterprise architecture, ASME V&V 20 compliance, and licensing tiers"
            >
              <ShieldCheck size={13} color="#f59e0b" />
              <span className="flight-tool-label">ASME V&amp;V</span>
            </button>
          </nav>

          {/* Right: Mission Actions & Security Clearance Dock */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", whiteSpace: "nowrap" }}>
            {/* Quick Command Trigger (Apple Spotlight Style) */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flight-action-btn"
              title="Search commands, benchmarks, or airfoils (Cmd+K)"
            >
              <Search size={12} color="#38bdf8" />
              <span className="flight-tool-label">Search</span>
              <kbd
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.62rem",
                  padding: "1px 4px",
                  borderRadius: "4px",
                  background: "rgba(255, 255, 255, 0.08)",
                  color: "#94a3b8",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                }}
              >
                ⌘K
              </kbd>
            </button>

            {/* Export Dossier Button */}
            <button
              onClick={() => setExportOpen(true)}
              className="flight-action-btn"
              style={{ color: "#14b8a6" }}
              title="Export ASME V&V 20 Certification Dossier"
            >
              <FileText size={12} color="#14b8a6" />
              <span className="flight-tool-label">Dossier</span>
            </button>

            {/* Executive Showcase Trigger */}
            <button
              onClick={() => setActiveNavMode("SHOWCASE")}
              className="flight-action-btn"
              style={{
                borderColor: activeNavMode === "SHOWCASE" ? "rgba(56, 189, 248, 0.4)" : "rgba(255, 255, 255, 0.08)",
                background: activeNavMode === "SHOWCASE" ? "rgba(56, 189, 248, 0.15)" : "rgba(18, 26, 44, 0.6)",
                color: activeNavMode === "SHOWCASE" ? "#38bdf8" : "#94a3b8",
              }}
              title="Open Executive Platform Showcase & Overview"
            >
              <Sparkles size={12} color="#38bdf8" />
              <span className="flight-tool-label">Showcase</span>
            </button>

            {/* Autonomous Cockpit Trigger */}
            <button
              onClick={() => setActiveNavMode("AUTONOMOUS_COCKPIT")}
              className="flight-action-btn"
              style={{
                borderColor: activeNavMode === "AUTONOMOUS_COCKPIT" ? "rgba(245, 158, 11, 0.5)" : "rgba(255, 255, 255, 0.08)",
                background: activeNavMode === "AUTONOMOUS_COCKPIT" ? "rgba(245, 158, 11, 0.18)" : "rgba(18, 26, 44, 0.6)",
                color: activeNavMode === "AUTONOMOUS_COCKPIT" ? "#f59e0b" : "#94a3b8",
                fontWeight: activeNavMode === "AUTONOMOUS_COCKPIT" ? 700 : 500,
              }}
              title="Launch AASI 2.0 Autonomous Aerospace Intelligence Cockpit (8 Agents & Flagship Inquiry)"
            >
              <Brain size={12} color="#f59e0b" />
              <span className="flight-tool-label">Autonomous Cockpit</span>
            </button>

            {/* 3D Virtual Wind Tunnel Trigger */}
            <button
              onClick={() => setActiveNavMode("VIRTUAL_WIND_TUNNEL")}
              className="flight-action-btn"
              style={{
                borderColor: activeNavMode === "VIRTUAL_WIND_TUNNEL" ? "rgba(56, 189, 248, 0.4)" : "rgba(255, 255, 255, 0.08)",
                background: activeNavMode === "VIRTUAL_WIND_TUNNEL" ? "rgba(56, 189, 248, 0.15)" : "rgba(18, 26, 44, 0.6)",
                color: activeNavMode === "VIRTUAL_WIND_TUNNEL" ? "#38bdf8" : "#94a3b8",
              }}
              title="Launch 3D Virtual Wind Tunnel (SimScale/Airshaper automated CAE)"
            >
              <Wind size={12} color="#38bdf8" />
              <span className="flight-tool-label">3D Wind Tunnel</span>
            </button>

            {/* ISRO & NASA Mission Deck Trigger */}
            <button
              onClick={() => setActiveNavMode("ISRO_NASA_MISSION")}
              className="flight-action-btn"
              style={{
                borderColor: activeNavMode === "ISRO_NASA_MISSION" ? "rgba(245, 158, 11, 0.4)" : "rgba(255, 255, 255, 0.08)",
                background: activeNavMode === "ISRO_NASA_MISSION" ? "rgba(245, 158, 11, 0.15)" : "rgba(18, 26, 44, 0.6)",
                color: activeNavMode === "ISRO_NASA_MISSION" ? "#f59e0b" : "#94a3b8",
              }}
              title="Launch ISRO & NASA Mission Architecture Deck (Ascent, Max-Q, Orbit Decay)"
            >
              <Rocket size={12} color="#f59e0b" />
              <span className="flight-tool-label">ISRO / NASA</span>
            </button>

            {/* Digital Twin Studio Quick Trigger */}
            <button
              onClick={() => setActiveNavMode("DIGITAL_TWIN")}
              className="flight-action-btn"
              style={{
                borderColor: activeNavMode === "DIGITAL_TWIN" ? "rgba(56, 189, 248, 0.4)" : "rgba(255, 255, 255, 0.08)",
                background: activeNavMode === "DIGITAL_TWIN" ? "rgba(56, 189, 248, 0.12)" : "rgba(18, 26, 44, 0.6)",
                color: activeNavMode === "DIGITAL_TWIN" ? "#38bdf8" : "#94a3b8",
              }}
              title="Open Aerospace Digital Twin Studio (Rocket, Drone, Jet, Satellite)"
            >
              <Rocket size={12} color="#38bdf8" />
              <span className="flight-tool-label">Digital Twin</span>
            </button>

            {/* Aero DB & Turnkey Study Trigger */}
            <button
              onClick={() => setActiveNavMode("AERODB")}
              className="flight-action-btn"
              style={{
                borderColor: activeNavMode === "AERODB" ? "rgba(56, 189, 248, 0.4)" : "rgba(255, 255, 255, 0.08)",
                background: activeNavMode === "AERODB" ? "rgba(56, 189, 248, 0.12)" : "rgba(18, 26, 44, 0.6)",
                color: activeNavMode === "AERODB" ? "#38bdf8" : "#94a3b8",
              }}
              title="Open Autonomous Aerodynamic Database & Turnkey Client Package Generator"
            >
              <Database size={12} color="#38bdf8" />
              <span className="flight-tool-label">Aero DB &amp; Turnkey</span>
            </button>

            {/* Subdomain Benchmark Hub Trigger */}
            <button
              onClick={() => setSubdomainBenchmarkOpen(true)}
              className="flight-action-btn"
              style={{
                borderColor: "rgba(52, 211, 153, 0.25)",
                background: "rgba(52, 211, 153, 0.08)",
                color: "#34d399",
              }}
              title="Open Aerospace Subdomain Benchmark Hub (NASA CRM, UIUC, CMAPSS, SHM, AirSim)"
            >
              <Compass size={12} color="#34d399" />
              <span className="flight-tool-label">Benchmark Hub</span>
            </button>

            {/* Analysis Console Trigger */}
            <button
              onClick={() => setChatOpen(true)}
              className="flight-action-btn"
              title="Open Aerodynamic Analysis Console"
            >
              <Terminal size={12} color="#38bdf8" />
              <span className="flight-tool-label">Console</span>
            </button>

            {/* User Clearance Badge */}
            <button
              onClick={() => setAuthModalOpen(true)}
              className="flight-action-btn"
              style={{
                borderColor: authUser ? "rgba(245, 158, 11, 0.3)" : "rgba(255, 255, 255, 0.08)",
                background: authUser ? "rgba(245, 158, 11, 0.08)" : "rgba(18, 26, 44, 0.6)",
              }}
              title="Manage authentication session and team clearance"
            >
              <UserIcon size={12} color={authUser ? "#f59e0b" : "#94a3b8"} />
              <span style={{ fontSize: "0.72rem", color: authUser ? "#f59e0b" : "#cbd5e1" }}>
                {authUser ? authUser.username : "Sign In"}
              </span>
              {authUser && (
                <span
                  style={{
                    fontSize: "0.58rem",
                    padding: "1px 4px",
                    borderRadius: "3px",
                    background: "rgba(56, 189, 248, 0.2)",
                    color: "#38bdf8",
                    fontFamily: "var(--font-mono)",
                    fontWeight: 700,
                  }}
                >
                  {authUser.role.replace("AERODYNAMICIST", "AERO")}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* ─── Main Content Canvas ─── */}
        <main
          className={
            activeNavMode === "SHOWCASE" ||
            activeNavMode === "AUTONOMOUS_COCKPIT" ||
            activeNavMode === "VIRTUAL_WIND_TUNNEL" ||
            activeNavMode === "ISRO_NASA_MISSION"
              ? "mission-control-main-full"
              : "mission-control-main"
          }
        >
          {activeNavMode === "SHOWCASE" ? (
            <AasiPublicShowcase
              onLaunchCockpit={() => setActiveNavMode("AUTONOMOUS_COCKPIT")}
              onOpenWindTunnel={() => setActiveNavMode("VIRTUAL_WIND_TUNNEL")}
              onOpenDigitalTwin={() => setActiveNavMode("DIGITAL_TWIN")}
              onOpenMissionPlanner={() => setActiveNavMode("ISRO_NASA_MISSION")}
              onOpenAeroDb={() => setActiveNavMode("AERODB")}
            />
          ) : activeNavMode === "AUTONOMOUS_COCKPIT" ? (
            <AutonomousResearchCockpit
              apiBase={API_BASE}
              onOpenWindTunnel={() => setActiveNavMode("VIRTUAL_WIND_TUNNEL")}
              onOpenDigitalTwin={() => setActiveNavMode("DIGITAL_TWIN")}
              onOpenMissionPlanner={() => setActiveNavMode("ISRO_NASA_MISSION")}
            />
          ) : activeNavMode === "VIRTUAL_WIND_TUNNEL" ? (
            <VirtualWindTunnelStudio apiBase={API_BASE} />
          ) : activeNavMode === "ISRO_NASA_MISSION" ? (
            <IsroNasaMissionStudio apiBase={API_BASE} />
          ) : activeNavMode === "GOVERNOR_HARNESS" ? (
            <div className="p-6 max-w-7xl mx-auto w-full">
              <GovernorTaskHarnessPanel />
            </div>
          ) : activeNavMode === "DIGITAL_TWIN" ? (
            <DigitalTwinStudio apiBase={API_BASE} />
          ) : activeNavMode === "AERODB" ? (
            <div className="p-6 max-w-7xl mx-auto w-full" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <EpistemicRadarPanel apiBase={API_BASE} />
              <AeroDbPanel apiBase={API_BASE} />
            </div>
          ) : (
            <InvestigationWorkspace
              apiBase={API_BASE}
              externalMode={activeNavMode}
              onModeChange={(mode) => setActiveNavMode(mode)}
              externalExportOpen={exportOpen}
              onExportClose={() => setExportOpen(false)}
              externalTourOpen={tourOpen}
              onTourClose={() => setTourOpen(false)}
            />
          )}
        </main>

        {/* ─── Footer Telemetry Notice ─── */}
        <footer
          style={{
            borderTop: "1px solid rgba(255, 255, 255, 0.06)",
            padding: "12px 24px",
            background: "rgba(7, 10, 18, 0.9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
            fontSize: "0.7rem",
            color: "#64748b",
          }}
        >
          <div>
            <strong style={{ color: "#94a3b8" }}>AASI Mission Control v1.0 Enterprise:</strong>{" "}
            Multi-fidelity epistemic validation • Zero numerical fabrication • ASME V&amp;V 20 Principles
          </div>
          <div style={{ display: "flex", gap: "16px", fontFamily: "var(--font-mono)" }}>
            <span>ORACLE: ACTIVE (12 BENCHMARKS)</span>
            <span>MEMORY: CANONICAL</span>
            <span>COMPUTE: READY</span>
          </div>
        </footer>
      </div>

      {/* ─── Command Palette Modal ─── */}
      <CommandPaletteModal
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        commands={commands}
      />

      {/* ─── Floating Chat Assistant ─── */}
      <ChatPanel
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        apiBase={API_BASE}
      />

      {/* ─── User Authentication Modal ─── */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        apiBase={API_BASE}
        currentUser={authUser}
        onAuthSuccess={(user, token) => setAuthUser(user)}
        onLogout={() => setAuthUser(null)}
      />

      {/* ─── Cryptographic Audit Trail Modal ─── */}
      <AuditTrailModal
        isOpen={auditModalOpen}
        onClose={() => setAuditModalOpen(false)}
        orgId={authUser?.org_id || "default"}
        apiBase={API_BASE}
      />

      {/* ─── Enterprise Overview & V&V Certification Modal ─── */}
      <EnterpriseOverviewModal
        isOpen={enterpriseModalOpen}
        onClose={() => setEnterpriseModalOpen(false)}
      />

      {/* ─── 3D Surface Pressure & Mesh Contour Visualizer Modal ─── */}
      <ThreeDimensionalPressureMesh
        isOpen={mesh3DOpen}
        onClose={() => setMesh3DOpen(false)}
        apiBase={API_BASE}
      />

      {/* ─── Autonomous Airfoil Shape Optimization Studio Modal ─── */}
      <AirfoilOptimizationStudio
        isOpen={optStudioOpen}
        onClose={() => setOptStudioOpen(false)}
        apiBase={API_BASE}
      />

      {/* ─── Mission Telemetry & Observability Modal ─── */}
      <EnterpriseTelemetryDashboard
        isOpen={telemetryOpen}
        onClose={() => setTelemetryOpen(false)}
        apiBase={API_BASE}
      />

      {/* ─── Aerospace Subdomain Benchmark Hub Modal ─── */}
      <SubdomainBenchmarkModal
        isOpen={subdomainBenchmarkOpen}
        onClose={() => setSubdomainBenchmarkOpen(false)}
      />
    </div>
  );
}
