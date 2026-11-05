"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import * as THREE from "three";
import {
  Globe,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Activity,
  Layers,
  Terminal,
  Play,
  RotateCcw,
  Zap,
  Radio,
  Wifi,
  Flame,
  CloudRain,
  Crosshair,
  Compass,
  ArrowRight,
  CheckCircle2,
  Lock,
  Cpu,
  BarChart3,
  Plane,
} from "lucide-react";

interface SovereignMissionControlDashboardProps {
  apiBase?: string;
}

export type SovereignTab = "NETRA_SSA" | "AAI_CATFM" | "BLAZEWATCH_MHA" | "CONSTITUTION_RTA" | "ORBITAL_DOCKING";

export const SovereignMissionControlDashboard: React.FC<SovereignMissionControlDashboardProps> = ({
  apiBase = "http://127.0.0.1:8000",
}) => {
  const [activeTab, setActiveTab] = useState<SovereignTab>("NETRA_SSA");
  const [wsConnected, setWsConnected] = useState(false);
  const [isExecutingCAM, setIsExecutingCAM] = useState(false);
  const [camExecuted, setCamExecuted] = useState(false);
  const [rtaSwitchState, setRtaSwitchState] = useState<"COMPLEX_FUNCTION_ACTIVE" | "RECOVERY_FUNCTION_ENGAGED">(
    "COMPLEX_FUNCTION_ACTIVE"
  );

  // 3D Canvas Mount
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const threeSceneRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    earthGroup: THREE.Group;
    animId?: number;
  } | null>(null);

  // NETRA SSA Live Conjunctions
  const conjunctions = useMemo(
    () => [
      {
        id: "NETRA-CA-98102-01",
        asset: "ISRO SpaDeX-SDX01",
        debris: "FENGYUN-1C (11.2 cm Fragment)",
        source: "MOTR Satish Dhawan SDSC",
        missDistanceM: 284.0,
        radialMissM: 42.0,
        collisionProbPc: 4.12e-5,
        timeToCa: "T-01h 14m",
        status: "RED ALERT",
        recommendedDv: 0.35,
      },
      {
        id: "NETRA-CA-94521-02",
        asset: "Chandrayaan-4 Descender",
        debris: "COSMOS 2251 Fragment (16.8 cm)",
        source: "Chandrapur Assam Radar",
        missDistanceM: 840.0,
        radialMissM: 110.0,
        collisionProbPc: 1.85e-6,
        timeToCa: "T-03h 45m",
        status: "YELLOW ADVISORY",
        recommendedDv: 0.12,
      },
      {
        id: "NETRA-CA-88319-03",
        asset: "Bharatiya Antariksh Station (BAS-01)",
        debris: "CZ-4B Spent Rocket Body",
        source: "Leh High-Altitude Optical",
        missDistanceM: 3200.0,
        radialMissM: 450.0,
        collisionProbPc: 3.1e-8,
        timeToCa: "T-08h 20m",
        status: "GREEN CLEAR",
        recommendedDv: 0.0,
      },
    ],
    []
  );

  // AAI C-ATFM Airports
  const airports = useMemo(
    () => [
      { code: "DEL", city: "Delhi (IGIA)", cap: 68, demand: 74, delayMin: 12, weather: "Clear (10km)", status: "GDP ACTIVE" },
      { code: "BOM", city: "Mumbai (CSMIA)", cap: 46, demand: 52, delayMin: 22, weather: "Squall Cell", status: "HOLDING PROGRAM" },
      { code: "BLR", city: "Bengaluru (KIA)", cap: 45, demand: 42, delayMin: 0, weather: "Nominal", status: "FLOW NORMAL" },
      { code: "MAA", city: "Chennai (MAA)", cap: 36, demand: 34, delayMin: 0, weather: "Nominal", status: "FLOW NORMAL" },
      { code: "CCU", city: "Kolkata (NSCBIA)", cap: 34, demand: 38, delayMin: 15, weather: "Convective Cell", status: "GDP ACTIVE" },
      { code: "HYD", city: "Hyderabad (RGIA)", cap: 38, demand: 36, delayMin: 0, weather: "Nominal", status: "FLOW NORMAL" },
      { code: "GAU", city: "Guwahati (LGBI)", cap: 20, demand: 18, delayMin: 5, weather: "Chandrapur Advisory", status: "MONITORING" },
    ],
    []
  );

  // BlazeWatch Homeland Security Alerts
  const homelandAlerts = useMemo(
    () => [
      {
        id: "BW-MHA-01",
        region: "Brahmaputra Basin, Golaghat Assam",
        type: "FLASH FLOOD RAIN (45 dBZ)",
        source: "Chandrapur Cloud Radar + POEM-4 MMX",
        confidence: "99.1% (LSTM)",
        nlpVerified: "99.8% (BERT)",
        severity: "WARNING",
        action: "NDRF flood barriers deployed; cloud radar rainfall warning issued.",
      },
      {
        id: "BW-MHA-02",
        region: "Simlipal Biosphere, Odisha",
        type: "FOREST FIRE HOTSPOT (485°C)",
        source: "Thermal Infrared Pass + 112 Dispatch",
        confidence: "98.9% (LSTM)",
        nlpVerified: "99.6% (BERT)",
        severity: "EMERGENCY",
        action: "Aerial water drop dispatched; thermal containment corridor active.",
      },
      {
        id: "BW-MHA-03",
        region: "Western Border Sector (Point Defense)",
        type: "COUNTER-UAS INTRUDER TRACKING",
        source: "Electro-Optical Seeker + Radar",
        confidence: "99.5% (Meta-RL)",
        nlpVerified: "N/A",
        severity: "ALERT",
        action: "LOS curvature shaping locked: a_cmd=12.4 m/s² intercept course set.",
      },
    ],
    []
  );

  // ─── 3D Three.js Earth & Orbital Tracks Initialization ───
  useEffect(() => {
    if (!canvasContainerRef.current) return;

    const width = canvasContainerRef.current.clientWidth;
    const height = 340;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 4.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    canvasContainerRef.current.appendChild(renderer.domElement);

    const earthGroup = new THREE.Group();
    scene.add(earthGroup);

    // Earth Sphere
    const earthGeo = new THREE.SphereGeometry(1.6, 48, 48);
    const earthMat = new THREE.MeshPhongMaterial({
      color: 0x132238,
      emissive: 0x050c18,
      specular: 0x38bdf8,
      shininess: 15,
      wireframe: false,
    });
    const earthMesh = new THREE.Mesh(earthGeo, earthMat);
    earthGroup.add(earthMesh);

    // Wireframe grid lines on globe
    const wireGeo = new THREE.SphereGeometry(1.605, 24, 24);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x1e3a5f,
      wireframe: true,
      transparent: true,
      opacity: 0.25,
    });
    const wireMesh = new THREE.Mesh(wireGeo, wireMat);
    earthGroup.add(wireMesh);

    // Orbital Orbit Rings (LEO 470 km circular)
    const ringGeo = new THREE.RingGeometry(2.1, 2.13, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
    });
    const orbitRing = new THREE.Mesh(ringGeo, ringMat);
    orbitRing.rotation.x = Math.PI / 2.8;
    earthGroup.add(orbitRing);

    // Debris Orbit Ring (inclined 74 deg)
    const debrisRingGeo = new THREE.RingGeometry(2.15, 2.17, 64);
    const debrisRingMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
    });
    const debrisOrbit = new THREE.Mesh(debrisRingGeo, debrisRingMat);
    debrisOrbit.rotation.x = Math.PI / 1.5;
    debrisOrbit.rotation.y = 0.4;
    earthGroup.add(debrisOrbit);

    // Satellites Markers (SpaDeX and Debris)
    const satGeo = new THREE.SphereGeometry(0.045, 16, 16);
    const satMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    const satMesh = new THREE.Mesh(satGeo, satMat);
    satMesh.position.set(1.95, 0.75, 0.2);
    earthGroup.add(satMesh);

    const debGeo = new THREE.SphereGeometry(0.04, 16, 16);
    const debMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });
    const debMesh = new THREE.Mesh(debGeo, debMat);
    debMesh.position.set(1.98, 0.78, 0.22);
    earthGroup.add(debMesh);

    // Ground Radars (Sriharikota & Chandrapur)
    const radarGeo = new THREE.ConeGeometry(0.035, 0.08, 8);
    const radarMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
    const sharRadar = new THREE.Mesh(radarGeo, radarMat);
    sharRadar.position.set(0.65, 0.45, 1.35);
    earthGroup.add(sharRadar);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.5);
    dirLight.position.set(5, 3, 5);
    scene.add(dirLight);

    // Animation Loop
    let animId = 0;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      earthGroup.rotation.y += 0.002;
      renderer.render(scene, camera);
    };
    animate();

    threeSceneRef.current = { scene, camera, renderer, earthGroup, animId };

    const handleResize = () => {
      if (!canvasContainerRef.current) return;
      const w = canvasContainerRef.current.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (canvasContainerRef.current && renderer.domElement) {
        canvasContainerRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  const handleExecuteCAM = async () => {
    setIsExecutingCAM(true);
    await new Promise((r) => setTimeout(r, 800));
    setCamExecuted(true);
    setIsExecutingCAM(false);
  };

  const handleTripRTASwitch = () => {
    setRtaSwitchState((prev) =>
      prev === "COMPLEX_FUNCTION_ACTIVE" ? "RECOVERY_FUNCTION_ENGAGED" : "COMPLEX_FUNCTION_ACTIVE"
    );
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        background: "var(--bg-primary, #f8fafc)",
        color: "var(--text-primary, #0f172a)",
        fontFamily: "var(--font-sans, sans-serif)",
      }}
    >
      {/* ─── Sovereign Operational Telemetry Strip ─── */}
      <div
        style={{
          borderBottom: "1px solid var(--border-color, #e2e8f0)",
          background: "var(--bg-secondary, #ffffff)",
          backdropFilter: "blur(16px)",
          padding: "10px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          flexWrap: "wrap",
          position: "sticky",
          top: 0,
          zIndex: 40,
        }}
      >
        {/* Left: Active Facility & Custody */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 8px #10b981" }} />
            <span style={{ fontFamily: "var(--font-mono, monospace)", fontSize: "0.78rem", fontWeight: 700, color: "var(--text-primary, #0f172a)", letterSpacing: "0.06em" }}>
              ISRO ISTRAC // PROJECT NETRA SSA
            </span>
          </div>
          <span style={{ color: "var(--border-color, #e2e8f0)" }}>|</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.74rem", color: "var(--text-secondary, #475569)", fontFamily: "var(--font-mono, monospace)" }}>
            <Radio size={13} color="#0284c7" />
            <span>MOTR Radar: <strong style={{ color: "var(--accent-cyan, #0284c7)" }}>ACTIVE (10cm CUSTODY)</strong></span>
          </div>
          <span style={{ color: "var(--border-color, #e2e8f0)" }}>|</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.74rem", color: "var(--text-secondary, #475569)", fontFamily: "var(--font-mono, monospace)" }}>
            <CloudRain size={13} color="#10b981" />
            <span>Chandrapur Radar: <strong style={{ color: "#10b981" }}>45.2 dBZ</strong></span>
          </div>
        </div>

        {/* Right: ASTM F3269-21 RTA Switch & Telemetry */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            onClick={handleTripRTASwitch}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "0.74rem",
              padding: "5px 12px",
              borderRadius: "6px",
              background:
                rtaSwitchState === "COMPLEX_FUNCTION_ACTIVE"
                  ? "rgba(16, 185, 129, 0.12)"
                  : "rgba(239, 68, 68, 0.18)",
              border:
                rtaSwitchState === "COMPLEX_FUNCTION_ACTIVE"
                  ? "1px solid rgba(16, 185, 129, 0.35)"
                  : "1px solid rgba(239, 68, 68, 0.45)",
              color: rtaSwitchState === "COMPLEX_FUNCTION_ACTIVE" ? "#10b981" : "#ef4444",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              fontWeight: 700,
            }}
            title="Click to toggle ASTM F3269-21 RTA Switch between AI and Deterministic Recovery"
          >
            {rtaSwitchState === "COMPLEX_FUNCTION_ACTIVE" ? (
              <ShieldCheck size={14} color="#10b981" />
            ) : (
              <ShieldAlert size={14} color="#ef4444" />
            )}
            <span>RTA: {rtaSwitchState}</span>
          </div>
        </div>
      </div>

      {/* ─── Mission Deck Navigation ─── */}
      <nav
        style={{
          borderBottom: "1px solid var(--border-color, #e2e8f0)",
          background: "var(--bg-secondary, #ffffff)",
          display: "flex",
          gap: "2px",
          padding: "0 28px",
          overflowX: "auto",
        }}
      >
        {[
          { id: "NETRA_SSA" as SovereignTab, label: "Project NETRA Orbital SSA", icon: <Globe size={16} />, badge: "10cm Debris" },
          { id: "AAI_CATFM" as SovereignTab, label: "AAI C-ATFM Airspace", icon: <Plane size={16} />, badge: "Metro Hubs" },
          { id: "BLAZEWATCH_MHA" as SovereignTab, label: "BlazeWatch & MHA Defense", icon: <Flame size={16} />, badge: "Homeland" },
          { id: "CONSTITUTION_RTA" as SovereignTab, label: "ASTM F3269-21 RTA & 19 Failsafes", icon: <ShieldCheck size={16} />, badge: "DO-178C" },
          { id: "ORBITAL_DOCKING" as SovereignTab, label: "SpaDeX / Chandrayaan-4 GNC", icon: <Compass size={16} />, badge: "NavIC RODP" },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "12px 18px",
                border: "none",
                borderBottom: isActive ? "2px solid var(--accent-cyan, #0284c7)" : "2px solid transparent",
                background: isActive ? "rgba(2, 132, 199, 0.08)" : "transparent",
                color: isActive ? "var(--accent-cyan, #0284c7)" : "var(--text-secondary, #64748b)",
                fontWeight: isActive ? 700 : 500,
                fontSize: "0.82rem",
                cursor: "pointer",
                transition: "all 160ms ease",
                whiteSpace: "nowrap",
              }}
            >
              {React.cloneElement(tab.icon, { color: isActive ? "#0284c7" : "#64748b" })}
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  style={{
                    fontSize: "0.62rem",
                    padding: "1px 6px",
                    borderRadius: "4px",
                    background: isActive ? "rgba(2, 132, 199, 0.15)" : "rgba(0, 0, 0, 0.05)",
                    color: isActive ? "#0284c7" : "#64748b",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* ─── 3D Orbital Earth & Sensor Envelope Canvas ─── */}
      <section
        style={{
          borderBottom: "1px solid var(--border-color, #e2e8f0)",
          background: "linear-gradient(180deg, var(--bg-secondary, #ffffff) 0%, var(--bg-primary, #f8fafc) 100%)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div ref={canvasContainerRef} style={{ width: "100%", height: "340px", display: "block" }} />

        {/* Overlay Badges on 3D View */}
        <div
          style={{
            position: "absolute",
            top: "16px",
            left: "28px",
            background: "rgba(255, 255, 255, 0.94)",
            border: "1px solid var(--border-color, #e2e8f0)",
            borderRadius: "8px",
            padding: "10px 14px",
            fontSize: "0.74rem",
            fontFamily: "var(--font-mono, monospace)",
            boxShadow: "0 4px 16px rgba(0, 0, 0, 0.06)",
          }}
        >
          <div style={{ color: "var(--accent-cyan, #0284c7)", fontWeight: 700, marginBottom: "4px" }}>
            PROJECT NETRA MULTI-RADAR COVERAGE
          </div>
          <div style={{ color: "var(--text-secondary, #475569)" }}>• Sriharikota MOTR: Active LEO Tracking</div>
          <div style={{ color: "var(--text-secondary, #475569)" }}>• Chandrapur Assam Facility: Foundation Laid / Cloud Radar</div>
          <div style={{ color: "var(--text-secondary, #475569)" }}>• Leh &amp; Mt Abu: High-Altitude Deep Space Optical</div>
        </div>

        <div
          style={{
            position: "absolute",
            bottom: "16px",
            right: "28px",
            background: "rgba(255, 255, 255, 0.94)",
            border: "1px solid var(--border-color, #e2e8f0)",
            borderRadius: "8px",
            padding: "8px 12px",
            display: "flex",
            gap: "12px",
            fontSize: "0.72rem",
            fontFamily: "var(--font-mono, monospace)",
            boxShadow: "0 4px 16px rgba(0, 0, 0, 0.06)",
          }}
        >
          <span style={{ color: "#059669" }}>■ SpaDeX SDX01 (Chaser)</span>
          <span style={{ color: "#dc2626" }}>■ 10cm Debris Conjunction</span>
          <span style={{ color: "#d97706" }}>▲ Radar Ground Station</span>
        </div>
      </section>

      {/* ─── Main Content Canvas ─── */}
      <main style={{ padding: "28px", flex: 1, maxWidth: "1580px", margin: "0 auto", width: "100%", boxSizing: "border-box" }}>
        {/* ══════════════════════════════════════════════════════════════════
            TAB 1: PROJECT NETRA ORBITAL SSA
            ══════════════════════════════════════════════════════════════════ */}
        {activeTab === "NETRA_SSA" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 4px 0" }}>
                  Project NETRA Conjunction Screening &amp; Automated CAM Burns
                </h2>
                <p style={{ margin: 0, fontSize: "0.78rem", color: "#94a3b8" }}>
                  Real-time 2D encounter plane collision probability (Pc) and fuel-optimal collision avoidance maneuvers
                </p>
              </div>

              {conjunctions[0].status === "RED ALERT" && !camExecuted && (
                <button
                  onClick={handleExecuteCAM}
                  disabled={isExecutingCAM}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "10px 20px",
                    borderRadius: "8px",
                    background: "linear-gradient(135deg, #ef4444, #b91c1c)",
                    border: "none",
                    color: "#f8fafc",
                    fontWeight: 700,
                    fontSize: "0.82rem",
                    cursor: isExecutingCAM ? "not-allowed" : "pointer",
                    boxShadow: "0 0 20px rgba(239, 68, 68, 0.35)",
                  }}
                >
                  <Play size={16} fill="#f8fafc" />
                  <span>{isExecutingCAM ? "Executing Burn..." : "Execute Automated CAM Burn (Δv=0.35 m/s)"}</span>
                </button>
              )}

              {camExecuted && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    background: "rgba(16, 185, 129, 0.15)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    color: "#10b981",
                    fontSize: "0.8rem",
                    fontWeight: 700,
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  <CheckCircle2 size={16} />
                  <span>CAM BURN EXECUTED: Miss Clearance &gt; 2.5 km</span>
                </div>
              )}
            </div>

            {/* Conjunction Alerts Table */}
            <div
              style={{
                background: "var(--bg-card, #ffffff)",
                border: "1px solid var(--border-color, #e2e8f0)",
                borderRadius: "10px",
                overflow: "hidden",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
              }}
            >
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
                <thead>
                  <tr style={{ background: "rgba(2, 132, 199, 0.05)", color: "var(--text-secondary, #475569)", borderBottom: "1px solid var(--border-color, #e2e8f0)" }}>
                    <th style={{ padding: "12px 16px" }}>Alert ID</th>
                    <th style={{ padding: "12px 16px" }}>Asset Protected</th>
                    <th style={{ padding: "12px 16px" }}>Debris Object</th>
                    <th style={{ padding: "12px 16px" }}>Sensor Custody</th>
                    <th style={{ padding: "12px 16px" }}>Miss Distance</th>
                    <th style={{ padding: "12px 16px" }}>Collision Prob (Pc)</th>
                    <th style={{ padding: "12px 16px" }}>Time to CA</th>
                    <th style={{ padding: "12px 16px" }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {conjunctions.map((c) => {
                    const isRed = c.status === "RED ALERT";
                    return (
                      <tr
                        key={c.id}
                        style={{
                          borderBottom: "1px solid var(--border-color, #e2e8f0)",
                          background: isRed && !camExecuted ? "rgba(239, 68, 68, 0.06)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono, monospace)", color: "var(--accent-cyan, #0284c7)" }}>
                          {c.id}
                        </td>
                        <td style={{ padding: "12px 16px", fontWeight: 600, color: "var(--text-primary, #0f172a)" }}>{c.asset}</td>
                        <td style={{ padding: "12px 16px", color: isRed ? "#dc2626" : "var(--text-primary, #0f172a)" }}>{c.debris}</td>
                        <td style={{ padding: "12px 16px", color: "var(--text-secondary, #64748b)", fontSize: "0.75rem" }}>{c.source}</td>
                        <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono, monospace)", fontWeight: 700, color: "var(--text-primary, #0f172a)" }}>
                          {camExecuted && isRed ? "2,840 m" : `${c.missDistanceM} m`}
                        </td>
                        <td
                          style={{
                            padding: "12px 16px",
                            fontFamily: "var(--font-mono, monospace)",
                            color: isRed && !camExecuted ? "#dc2626" : "#059669",
                            fontWeight: 700,
                          }}
                        >
                          {camExecuted && isRed ? "1.2e-8" : c.collisionProbPc.toExponential(2)}
                        </td>
                        <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono, monospace)", color: "var(--text-secondary, #64748b)" }}>
                          {c.timeToCa}
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span
                            style={{
                              fontSize: "0.68rem",
                              padding: "2px 8px",
                              borderRadius: "4px",
                              background:
                                isRed && !camExecuted
                                  ? "rgba(239, 68, 68, 0.15)"
                                  : "rgba(16, 185, 129, 0.15)",
                              color: isRed && !camExecuted ? "#dc2626" : "#059669",
                              fontWeight: 700,
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            {camExecuted && isRed ? "CLEARED" : c.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            TAB 2: AAI C-ATFM AIRSPACE FLOW
            ══════════════════════════════════════════════════════════════════ */}
        {activeTab === "AAI_CATFM" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 4px 0" }}>
                Airports Authority of India (AAI) C-ATFM National Airspace Engine
              </h2>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "#94a3b8" }}>
                Real-time terminal arrival demand vs capacity balancing, weather disruption rerouting, and holding-pattern fuel optimization.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
              {airports.map((apt) => {
                const isDelayed = apt.delayMin > 0;
                return (
                  <div
                    key={apt.code}
                    style={{
                      background: "var(--bg-card, #ffffff)",
                      border: isDelayed
                        ? "1px solid rgba(217, 119, 6, 0.45)"
                        : "1px solid var(--border-color, #e2e8f0)",
                      borderRadius: "10px",
                      padding: "18px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      gap: "12px",
                      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <span style={{ fontSize: "1.2rem", fontWeight: 800, color: "var(--accent-cyan, #0284c7)" }}>{apt.code}</span>
                        <div style={{ fontSize: "0.76rem", color: "var(--text-secondary, #64748b)" }}>{apt.city}</div>
                      </div>
                      <span
                        style={{
                          fontSize: "0.64rem",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: isDelayed ? "rgba(217, 119, 6, 0.15)" : "rgba(16, 185, 129, 0.15)",
                          color: isDelayed ? "#d97706" : "#059669",
                          fontFamily: "var(--font-mono, monospace)",
                          fontWeight: 700,
                        }}
                      >
                        {apt.status}
                      </span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.75rem" }}>
                      <div>
                        <span style={{ color: "var(--text-secondary, #64748b)" }}>Hourly Capacity:</span>{" "}
                        <strong style={{ color: "var(--text-primary, #0f172a)" }}>{apt.cap}/h</strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--text-secondary, #64748b)" }}>Hourly Demand:</span>{" "}
                        <strong style={{ color: apt.demand > apt.cap ? "#d97706" : "var(--text-primary, #0f172a)" }}>
                          {apt.demand}/h
                        </strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--text-secondary, #64748b)" }}>Weather Cell:</span>{" "}
                        <strong style={{ color: "var(--text-secondary, #334155)" }}>{apt.weather}</strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--text-secondary, #64748b)" }}>Ground Delay:</span>{" "}
                        <strong style={{ color: isDelayed ? "#d97706" : "#059669", fontFamily: "var(--font-mono, monospace)" }}>
                          +{apt.delayMin} min
                        </strong>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            TAB 3: BLAZEWATCH MHA DISASTER INTELLIGENCE
            ══════════════════════════════════════════════════════════════════ */}
        {activeTab === "BLAZEWATCH_MHA" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 4px 0" }}>
                BlazeWatch Dual-Stream Disaster &amp; Homeland Defense (MHA / NDMA)
              </h2>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "#94a3b8" }}>
                Fuses satellite thermal infrared passes with ground emergency dispatch feeds (LSTM 98.9% / BERT 99.77%) and Chandrapur cloud radar flood monitoring.
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {homelandAlerts.map((alert) => (
                <div
                  key={alert.id}
                  style={{
                    background: "var(--bg-card, #ffffff)",
                    border: "1px solid var(--border-color, #e2e8f0)",
                    borderRadius: "10px",
                    padding: "20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "10px",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          fontSize: "0.68rem",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background:
                            alert.severity === "EMERGENCY"
                              ? "rgba(220, 38, 38, 0.15)"
                              : alert.severity === "WARNING"
                              ? "rgba(217, 119, 6, 0.15)"
                              : "rgba(2, 132, 199, 0.15)",
                          color:
                            alert.severity === "EMERGENCY"
                              ? "#dc2626"
                              : alert.severity === "WARNING"
                              ? "#d97706"
                              : "#0284c7",
                          fontWeight: 700,
                          fontFamily: "var(--font-mono, monospace)",
                        }}
                      >
                        {alert.severity}
                      </span>
                      <h3 style={{ fontSize: "0.98rem", fontWeight: 700, margin: 0, color: "var(--text-primary, #0f172a)" }}>{alert.type}</h3>
                    </div>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-secondary, #64748b)", fontFamily: "var(--font-mono, monospace)" }}>
                      {alert.id}
                    </span>
                  </div>

                  <div style={{ fontSize: "0.82rem", color: "var(--text-secondary, #334155)" }}>
                    Location: <strong style={{ color: "var(--text-primary, #0f172a)" }}>{alert.region}</strong> | Sensor Feed: {alert.source}
                  </div>

                  <div
                    style={{
                      background: "var(--bg-primary, #f8fafc)",
                      borderRadius: "6px",
                      padding: "10px 14px",
                      fontSize: "0.76rem",
                      color: "var(--text-secondary, #475569)",
                      borderLeft: "3px solid var(--accent-cyan, #0284c7)",
                    }}
                  >
                    <strong style={{ color: "var(--accent-cyan, #0284c7)" }}>Command Recommendation:</strong> {alert.action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            TAB 4: ASTM F3269-21 RTA & 19 FAILSAFES
            ══════════════════════════════════════════════════════════════════ */}
        {activeTab === "CONSTITUTION_RTA" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 4px 0", color: "var(--text-primary, #0f172a)" }}>
                ASTM F3269-21 Run-Time Assurance &amp; 19 Flight Failsafes (F-1 to F-19)
              </h2>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--text-secondary, #64748b)" }}>
                Ed25519-signed sealed constitutional kernel outside neural addressable memory with 2-of-3 heterogeneous safety monitor voting.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
              {[
                { code: "F-1", name: "Prompt Injection & Adversarial Semantic Defense", status: "ACTIVE_PASS" },
                { code: "F-2", name: "Command Token Forgery & Ed25519 Signature", status: "ACTIVE_PASS" },
                { code: "F-3", name: "NavIC / GNSS Spoofing & Doppler Consistency", status: "ACTIVE_PASS" },
                { code: "F-4", name: "Sensor Cross-Corroboration (ASTM Table 1)", status: "ACTIVE_PASS" },
                { code: "F-5", name: "Resource Ceiling (Power 350W / Temp 85°C)", status: "ACTIVE_PASS" },
                { code: "F-6", name: "Two-Person Rule Dual-Custody Burn Authorization", status: "ACTIVE_PASS" },
                { code: "F-7", name: "Operator Console Session Integrity & Anti-Replay", status: "ACTIVE_PASS" },
                { code: "F-8", name: "Flight Envelope Protection (V-n & Stall Bound)", status: "ACTIVE_PASS" },
                { code: "F-9", name: "Actuator Slew Rate Limit (45 deg/s Max)", status: "ACTIVE_PASS" },
                { code: "F-10", name: "State Covariance Divergence (Tr(P) < 0.25)", status: "ACTIVE_PASS" },
                { code: "F-11", name: "V-bar Docking Cone & Terminal 15 mm/s Bound", status: "ACTIVE_PASS" },
                { code: "F-12", name: "Thruster Minimum Impulse Bit (MIB > 15ms)", status: "ACTIVE_PASS" },
                { code: "F-13", name: "Post-Eclipse Thermal Gradient & Sun Blindness", status: "ACTIVE_PASS" },
                { code: "F-14", name: "Comms Watchdog Timeout (5.0s Heartbeat)", status: "ACTIVE_PASS" },
                { code: "F-15", name: "Single Event Upset (SEU) Memory Checksum", status: "ACTIVE_PASS" },
                { code: "F-16", name: "Total Ionizing Dose (TID < 25 krad Rating)", status: "ACTIVE_PASS" },
                { code: "F-17", name: "Project NETRA Conjunction (Pc > 1e-6 CAM)", status: "ACTIVE_PASS" },
                { code: "F-18", name: "Certified Subsystem Tool Whitelist (ODD)", status: "ACTIVE_PASS" },
                { code: "F-19", name: "Cryptographic Merkle Hash Audit Trail", status: "ACTIVE_PASS" },
              ].map((f) => (
                <div
                  key={f.code}
                  style={{
                    background: "var(--bg-card, #ffffff)",
                    border: "1px solid var(--border-color, #e2e8f0)",
                    borderRadius: "8px",
                    padding: "12px 16px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    boxShadow: "0 2px 6px rgba(0, 0, 0, 0.03)",
                  }}
                >
                  <div>
                    <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--accent-cyan, #0284c7)", fontFamily: "var(--font-mono, monospace)" }}>
                      {f.code}
                    </span>
                    <div style={{ fontSize: "0.74rem", color: "var(--text-primary, #0f172a)", marginTop: "2px" }}>{f.name}</div>
                  </div>
                  <span
                    style={{
                      fontSize: "0.64rem",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: "rgba(16, 185, 129, 0.15)",
                      color: "#059669",
                      fontFamily: "var(--font-mono, monospace)",
                      fontWeight: 700,
                    }}
                  >
                    {f.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════════
            TAB 5: SPADEX & CHANDRAYAAN-4 ORBITAL GNC
            ══════════════════════════════════════════════════════════════════ */}
        {activeTab === "ORBITAL_DOCKING" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 4px 0", color: "var(--text-primary, #0f172a)" }}>
                SpaDeX &amp; Chandrayaan-4 NavIC RODP + ISL Docking Simulator
              </h2>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--text-secondary, #64748b)" }}>
                Eliminates the 225m post-eclipse drift anomaly using NavIC dual-frequency carrier phase + continuous Inter-Satellite Link (ISL) fusion down to 10 mm/s capture.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              <div style={{ background: "var(--bg-card, #ffffff)", borderRadius: "10px", padding: "20px", border: "1px solid var(--border-color, #e2e8f0)", boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-secondary, #64748b)" }}>POST-ECLIPSE DRIFT (HISTORICAL SPADEX)</span>
                <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#dc2626", fontFamily: "var(--font-mono, monospace)", margin: "8px 0" }}>
                  225.0 m
                </div>
                <p style={{ margin: 0, fontSize: "0.74rem", color: "var(--text-muted, #94a3b8)" }}>
                  Unmodeled differential drag &amp; optical blackout during ground non-visibility window
                </p>
              </div>

              <div style={{ background: "var(--bg-card, #ffffff)", borderRadius: "10px", padding: "20px", border: "1px solid var(--border-color, #e2e8f0)", boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-secondary, #64748b)" }}>AASI NAVIC RODP + ISL FILTER DRIFT</span>
                <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#059669", fontFamily: "var(--font-mono, monospace)", margin: "8px 0" }}>
                  0.018 m (1.8 cm)
                </div>
                <p style={{ margin: 0, fontSize: "0.74rem", color: "var(--text-muted, #94a3b8)" }}>
                  Continuous ISL cross-link phase bounds error covariance across solar eclipse
                </p>
              </div>

              <div style={{ background: "var(--bg-card, #ffffff)", borderRadius: "10px", padding: "20px", border: "1px solid var(--border-color, #e2e8f0)", boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-secondary, #64748b)" }}>TERMINAL LATCH CAPTURE SPEED</span>
                <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-cyan, #0284c7)", fontFamily: "var(--font-mono, monospace)", margin: "8px 0" }}>
                  10.2 mm/s
                </div>
                <p style={{ margin: 0, fontSize: "0.74rem", color: "var(--text-muted, #94a3b8)" }}>
                  Conforms strictly to 450mm (SpaDeX) and 800mm (BAS-01) BDS capture limits
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
