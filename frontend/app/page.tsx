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
  Globe,
  Sun,
  Moon,
  Waves,
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
import { SovereignMissionControlDashboard } from "../components/SovereignMissionControlDashboard";
import { AeroCraftStudio } from "../components/AeroCraftStudio";
import { TransonicTransolverStudio } from "../components/TransonicTransolverStudio";
import TurbulenceSciMLStudio from "../components/TurbulenceSciMLStudio";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function AASIApp() {
  const [chatOpen, setChatOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [activeNavMode, setActiveNavMode] = useState<WorkspaceNavMode>("SOVEREIGN_MISSION_CONTROL");
  const [toolsMenuOpen, setToolsMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);
  const [enterpriseModalOpen, setEnterpriseModalOpen] = useState(false);
  const [mesh3DOpen, setMesh3DOpen] = useState(false);
  const [optStudioOpen, setOptStudioOpen] = useState(false);
  const [transonicStudioOpen, setTransonicStudioOpen] = useState(false);
  const [turbulenceStudioOpen, setTurbulenceStudioOpen] = useState(false);
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const [subdomainBenchmarkOpen, setSubdomainBenchmarkOpen] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [hardwareStatus, setHardwareStatus] = useState<{ protected: boolean; ram_free_gb?: number }>({
    protected: true,
  });
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Sync theme with document attribute on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("aasi_theme") as "light" | "dark" | null;
      const initial = stored || "light";
      setTheme(initial);
      document.documentElement.setAttribute("data-theme", initial);
    } catch {
      document.documentElement.setAttribute("data-theme", "light");
    }
  }, []);

  const handleToggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("aasi_theme", next);
    } catch {
      /* ignore */
    }
  };

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
            upper === "SOVEREIGN_MISSION_CONTROL" ||
            upper === "SOVEREIGN" ||
            upper === "AEROCRAFT_STUDIO" ||
            upper === "AEROCRAFT" ||
            upper === "CRAFT" ||
            upper === "NETRA" ||
            upper === "CATFM" ||
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
            else if (upper === "AEROCRAFT" || upper === "CRAFT") setActiveNavMode("AEROCRAFT_STUDIO");
            else if (upper === "SOVEREIGN" || upper === "NETRA" || upper === "CATFM")
              setActiveNavMode("SOVEREIGN_MISSION_CONTROL");
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
      id: "cmd-ws-transonic",
      category: "Workspaces",
      title: "Launch Transonic Shock-Capturing Neural Operator (Stage 2)",
      description: "Continuous-space Transolver-3D / FNO, Rankine-Hugoniot jump relations, and AGARD AR-138 benchmarks.",
      badge: "Stage 2 Breakthrough",
      icon: <Zap size={16} />,
      action: () => setTransonicStudioOpen(true),
    },
    {
      id: "cmd-ws-turbulence",
      category: "Workspaces",
      title: "Launch High-Reynolds Turbulence SciML Studio (Stage 3)",
      description: "Pope's 10-tensor integrity basis, Lumley realizability projection, Menter k-omega SST coupling, and boundary layer separation marching.",
      badge: "Stage 3 SciML",
      icon: <Waves size={16} />,
      action: () => setTurbulenceStudioOpen(true),
    },
    {
      id: "cmd-ws-aerocraft",
      category: "Workspaces",
      title: "Launch AeroCraft Reverse-Engineering Studio",
      description: "Clean-room 4-step loop (Study -> Build -> Check -> Ready), ASME V&V 20 Richardson GCI, and ASTM F3269-21 RTA flight approval cards.",
      badge: "Sovereign CAE",
      icon: <Cpu size={16} />,
      action: () => setActiveNavMode("AEROCRAFT_STUDIO"),
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
        defaultCollapsed={true}
      />

      {/* ─── Main Viewport Area ─── */}
      <div className="mission-control-viewport">
        {/* ─── Top Mission Control Bar (SpaceX + Apple Glassmorphic Flight Deck) ─── */}
        <header className="spacex-flight-deck">
          {/* Left: Mission Identity & Real-Time Telemetry */}
          <div style={{ display: "flex", alignItems: "center", gap: "14px", minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "6px",
                  background: "rgba(56, 189, 248, 0.12)",
                  border: "1px solid rgba(56, 189, 248, 0.3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Globe size={18} color="#38bdf8" />
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "1.05rem",
                      fontWeight: 800,
                      color: "#f8fafc",
                      letterSpacing: "0.12em",
                    }}
                  >
                    AASI
                  </span>
                  <span
                    style={{
                      fontSize: "0.62rem",
                      padding: "1px 6px",
                      borderRadius: "4px",
                      background: "rgba(16, 185, 129, 0.12)",
                      color: "#10b981",
                      border: "1px solid rgba(16, 185, 129, 0.25)",
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                    }}
                  >
                    SOVEREIGN V2.0
                  </span>
                </div>
                <div
                  className="header-breadcrumb-sub"
                  style={{
                    fontSize: "0.62rem",
                    color: "#64748b",
                    fontWeight: 600,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                  }}
                >
                  BHARATIYA AUTONOMOUS AEROSPACE INTELLIGENCE
                </div>
              </div>
            </div>
          </div>

          {/* Center: The 6 Core Executive Aerospace Pillars (Segmented Controller) */}
          <nav className="flight-tools-capsule" aria-label="Aerospace Pillars Deck">
            <button
              onClick={() => setActiveNavMode("SOVEREIGN_MISSION_CONTROL")}
              className={`flight-tool-btn ${activeNavMode === "SOVEREIGN_MISSION_CONTROL" ? "active" : ""}`}
              title="ISRO Project NETRA Orbital Conjunctions, AAI National Airspace Flow, BlazeWatch MHA Crisis Radar"
            >
              <Globe size={13} color={activeNavMode === "SOVEREIGN_MISSION_CONTROL" ? "#38bdf8" : "#94a3b8"} />
              <span className="flight-tool-label">Mission Control</span>
            </button>

            <button
              onClick={() => setActiveNavMode("AEROCRAFT_STUDIO")}
              className={`flight-tool-btn ${activeNavMode === "AEROCRAFT_STUDIO" ? "active" : ""}`}
              title="AASI-Craft: Clean-Room Reverse-Engineering, 4-Step Loop (Study->Build->Check->Ready), ASME V&V 20 & ASTM F3269-21 RTA"
            >
              <Cpu size={13} color={activeNavMode === "AEROCRAFT_STUDIO" ? "#38bdf8" : "#94a3b8"} />
              <span className="flight-tool-label">AeroCraft Studio</span>
            </button>

            <button
              onClick={() => setActiveNavMode("AUTONOMOUS_COCKPIT")}
              className={`flight-tool-btn ${activeNavMode === "AUTONOMOUS_COCKPIT" ? "active" : ""}`}
              title="8 Autonomous Aerospace Agents, Flagship NACA 4412 Investigation, Neural Operator Surrogates"
            >
              <Brain size={13} color={activeNavMode === "AUTONOMOUS_COCKPIT" ? "#f59e0b" : "#94a3b8"} />
              <span className="flight-tool-label">Autonomous AI</span>
            </button>

            <button
              onClick={() => setActiveNavMode("VIRTUAL_WIND_TUNNEL")}
              className={`flight-tool-btn ${activeNavMode === "VIRTUAL_WIND_TUNNEL" ? "active" : ""}`}
              title="Turnkey 3D Virtual Wind Tunnel, CFD Mesh Deformations, Aerodynamic Polars"
            >
              <Wind size={13} color={activeNavMode === "VIRTUAL_WIND_TUNNEL" ? "#38bdf8" : "#94a3b8"} />
              <span className="flight-tool-label">3D Wind Tunnel</span>
            </button>

            <button
              onClick={() => setActiveNavMode("DIGITAL_TWIN")}
              className={`flight-tool-btn ${activeNavMode === "DIGITAL_TWIN" ? "active" : ""}`}
              title="6-DOF SpaDeX Rendezvous & Docking, Chandrayaan-4 Lunar Lander, Aircraft Flight Dynamics"
            >
              <Rocket size={13} color={activeNavMode === "DIGITAL_TWIN" ? "#10b981" : "#94a3b8"} />
              <span className="flight-tool-label">Digital Twin &amp; GNC</span>
            </button>

            <button
              onClick={() => setActiveNavMode("SHOWCASE")}
              className={`flight-tool-btn ${activeNavMode === "SHOWCASE" ? "active" : ""}`}
              title="Executive Platform Briefing, ASME V&V 20 & RTCA DO-178C Certification Matrices"
            >
              <FileText size={13} color={activeNavMode === "SHOWCASE" ? "#38bdf8" : "#94a3b8"} />
              <span className="flight-tool-label">Executive Briefing</span>
            </button>
          </nav>

          {/* Right: Tools Dropdown, Command Palette, Analysis Console, Clearance */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", position: "relative" }}>
            {/* Quick Tools Dropdown */}
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setToolsMenuOpen(!toolsMenuOpen)}
                className="flight-action-btn"
                style={{
                  borderColor: toolsMenuOpen ? "rgba(56, 189, 248, 0.4)" : "rgba(255, 255, 255, 0.08)",
                  background: toolsMenuOpen ? "rgba(56, 189, 248, 0.12)" : "rgba(18, 26, 44, 0.6)",
                  color: toolsMenuOpen ? "#38bdf8" : "#cbd5e1",
                }}
                title="Secondary Aerospace Studios & Turnkey Utilities"
              >
                <Layers size={12} color="#38bdf8" />
                <span className="flight-tool-label">CAE Studios ▾</span>
              </button>

              {/* Tools Popover Menu */}
              {toolsMenuOpen && (
                <div
                  style={{
                    position: "absolute",
                    top: "calc(100% + 8px)",
                    right: 0,
                    width: "260px",
                    background: "var(--bg-card, #ffffff)",
                    border: "1px solid var(--border-color, #e2e8f0)",
                    borderRadius: "10px",
                    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.12)",
                    zIndex: 200,
                    padding: "6px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "2px",
                  }}
                >
                  <button
                    onClick={() => {
                      setTransonicStudioOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "rgba(2, 132, 199, 0.08)",
                      border: "1px solid rgba(2, 132, 199, 0.3)",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Zap size={14} color="var(--accent-cyan, #0284c7)" />
                    <div>
                      <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                        <span>Transonic Transolver 3D</span>
                        <span style={{ fontSize: "0.6rem", background: "#0284c7", color: "#fff", padding: "1px 4px", borderRadius: "3px" }}>STAGE 2</span>
                      </div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>Rankine-Hugoniot Shock Capturing FNO</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setTurbulenceStudioOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "rgba(13, 148, 136, 0.08)",
                      border: "1px solid rgba(13, 148, 136, 0.3)",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Waves size={14} color="#0d9488" />
                    <div>
                      <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                        <span>Turbulence SciML Studio</span>
                        <span style={{ fontSize: "0.6rem", background: "#0d9488", color: "#fff", padding: "1px 4px", borderRadius: "3px" }}>STAGE 3</span>
                      </div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>TBNN • Lumley Realizability • SST</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setMesh3DOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Box size={14} color="var(--accent-cyan, #0284c7)" />
                    <div>
                      <div style={{ fontWeight: 600 }}>3D Surface Pressure (Cp)</div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>Interactive WebGL pressure grid</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setOptStudioOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Sparkles size={14} color="#d97706" />
                    <div>
                      <div style={{ fontWeight: 600 }}>Airfoil Shape Optimizer</div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>Genetic algorithm L/D maximizing</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setActiveNavMode("AERODB");
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Database size={14} color="var(--accent-cyan, #0284c7)" />
                    <div>
                      <div style={{ fontWeight: 600 }}>Aero Database &amp; Exporter</div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>Turnkey ArduPilot / PX4 param tables</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setSubdomainBenchmarkOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Compass size={14} color="#059669" />
                    <div>
                      <div style={{ fontWeight: 600 }}>Subdomain Benchmark Hub</div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>NASA CRM, UIUC, CMAPSS cases</div>
                    </div>
                  </button>

                  <div style={{ height: "1px", background: "var(--border-color, #e2e8f0)", margin: "4px 0" }} />

                  <button
                    onClick={() => {
                      setExportOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <FileText size={14} color="#059669" />
                    <div>
                      <div style={{ fontWeight: 600 }}>ASME V&amp;V 20 Dossier</div>
                      <div style={{ fontSize: "0.66rem", color: "var(--text-secondary, #64748b)" }}>Export certification evidence package</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setAuditModalOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-primary, #0f172a)",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Lock size={14} color="#38bdf8" />
                    <div>
                      <div style={{ fontWeight: 600 }}>SHA-256 Merkle Audit Trail</div>
                      <div style={{ fontSize: "0.66rem", color: "#64748b" }}>Immutable cryptographic execution logs</div>
                    </div>
                  </button>

                  <button
                    onClick={() => {
                      setTelemetryOpen(true);
                      setToolsMenuOpen(false);
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "transparent",
                      border: "none",
                      color: "#f8fafc",
                      fontSize: "0.78rem",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <Activity size={14} color="#10b981" />
                    <div>
                      <div style={{ fontWeight: 600 }}>Engine Telemetry &amp; Health</div>
                      <div style={{ fontSize: "0.66rem", color: "#64748b" }}>P50/P95 latency &amp; memory metrics</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* Quick Command Trigger (Cmd+K) */}
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

            {/* Theme Switcher: White & Light Mode / Dark Avionics */}
            <button
              onClick={handleToggleTheme}
              className="flight-action-btn"
              title={`Switch to ${theme === "light" ? "Dark Avionics" : "Sovereign White"} Mode`}
              style={{
                borderColor: theme === "light" ? "#e2e8f0" : "rgba(255, 255, 255, 0.12)",
              }}
            >
              {theme === "light" ? <Sun size={13} color="#d97706" /> : <Moon size={13} color="#38bdf8" />}
              <span className="flight-tool-label">
                {theme === "light" ? "Light" : "Dark"}
              </span>
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
                borderColor: authUser ? "rgba(16, 185, 129, 0.3)" : "rgba(255, 255, 255, 0.08)",
                background: authUser ? "rgba(16, 185, 129, 0.08)" : "rgba(18, 26, 44, 0.6)",
              }}
              title="Manage authentication session and team clearance"
            >
              <UserIcon size={12} color={authUser ? "#10b981" : "#94a3b8"} />
              <span style={{ fontSize: "0.72rem", color: authUser ? "#10b981" : "#cbd5e1", fontWeight: 600 }}>
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
                  CLEARED
                </span>
              )}
            </button>
          </div>
        </header>

        {/* ─── Main Content Canvas ─── */}
        <main
          className={
            activeNavMode === "SHOWCASE" ||
            activeNavMode === "SOVEREIGN_MISSION_CONTROL" ||
            activeNavMode === "AEROCRAFT_STUDIO" ||
            activeNavMode === "AUTONOMOUS_COCKPIT" ||
            activeNavMode === "VIRTUAL_WIND_TUNNEL" ||
            activeNavMode === "ISRO_NASA_MISSION"
              ? "mission-control-main-full"
              : "mission-control-main"
          }
        >
          {activeNavMode === "SHOWCASE" ? (
            <AasiPublicShowcase
              onLaunchCockpit={() => setActiveNavMode("SOVEREIGN_MISSION_CONTROL")}
              onOpenWindTunnel={() => setActiveNavMode("VIRTUAL_WIND_TUNNEL")}
              onOpenDigitalTwin={() => setActiveNavMode("DIGITAL_TWIN")}
              onOpenMissionPlanner={() => setActiveNavMode("ISRO_NASA_MISSION")}
              onOpenAeroDb={() => setActiveNavMode("AERODB")}
            />
          ) : activeNavMode === "SOVEREIGN_MISSION_CONTROL" ? (
            <SovereignMissionControlDashboard apiBase={API_BASE} />
          ) : activeNavMode === "AEROCRAFT_STUDIO" ? (
            <AeroCraftStudio />
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

      {/* ─── Stage 2: Transonic Shock-Capturing Neural Operator Studio Modal ─── */}
      <TransonicTransolverStudio
        isOpen={transonicStudioOpen}
        onClose={() => setTransonicStudioOpen(false)}
        apiBase={API_BASE}
      />

      {/* ─── Stage 3: High-Reynolds Turbulence SciML Studio Modal ─── */}
      <TurbulenceSciMLStudio
        isOpen={turbulenceStudioOpen}
        onClose={() => setTurbulenceStudioOpen(false)}
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
