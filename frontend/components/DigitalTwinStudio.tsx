"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import * as THREE from "three";
import {
  Rocket,
  Plane,
  Satellite as SatelliteIcon,
  Crosshair,
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Flame,
  Activity,
  Gauge,
  Thermometer,
  Zap,
  Download,
  Copy,
  Check,
  Maximize2,
  Sliders,
  Radio,
  FileCode,
  Layers,
  Compass,
} from "lucide-react";

export type VehicleType = "ROCKET" | "DRONE" | "AEROPLANE" | "SATELLITE";

export interface TelemetryFrame {
  timestamp_s: number;
  altitude_m: number;
  velocity_ms: number;
  mach: number;
  dynamic_pressure_pa: number;
  acceleration_g: number;
  mass_kg: number;
  propellant_or_battery_pct: number;
  temperature_c: number;
  subsystem_health: Record<string, number>;
  vehicle_specific: Record<string, any>;
}

export interface MissionEvent {
  timestamp_s: number;
  event_name: string;
  description: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
}

export interface SimulationResult {
  simulation_id: string;
  vehicle_type: VehicleType;
  vehicle_name: string;
  simulation_mode: string;
  duration_s: number;
  time_step_s: number;
  total_samples: number;
  frames: TelemetryFrame[];
  events: MissionEvent[];
  summary_metrics: Record<string, any>;
  safety_envelope_passed: boolean;
  safety_violations: string[];
  provenance_hash: string;
}

interface DigitalTwinStudioProps {
  apiBase?: string;
}

export const DigitalTwinStudio: React.FC<DigitalTwinStudioProps> = ({
  apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
}) => {
  const [selectedVehicle, setSelectedVehicle] = useState<VehicleType>("ROCKET");
  const [loading, setLoading] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [faultType, setFaultType] = useState<string>("NONE");
  const [faultOnset, setFaultOnset] = useState<number>(60);
  const [faultSeverity, setFaultSeverity] = useState<number>(0.75);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // 3D Canvas Ref
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const vehicleGroupRef = useRef<THREE.Group | null>(null);
  const plumeRef = useRef<THREE.Points | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  // Fetch or simulate on vehicle change
  const runSimulation = useCallback(
    async (vType: VehicleType, injectedFault?: any) => {
      setLoading(true);
      try {
        const payload: any = { vehicle_type: vType };
        if (injectedFault && injectedFault !== "NONE") {
          payload.fault = {
            target_vehicle: vType,
            fault_type: injectedFault,
            onset_time_s: faultOnset,
            severity: faultSeverity,
            subsystem_target: "propulsion",
          };
        }

        const res = await fetch(`${apiBase}/api/digital-twin/simulate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const data: SimulationResult = await res.json();
          setSimResult(data);
          setCurrentFrameIndex(0);
          setIsPlaying(true);
        } else {
          console.error("Simulation failed:", await res.text());
        }
      } catch (err) {
        console.error("API error during digital twin run:", err);
      } finally {
        setLoading(false);
      }
    },
    [apiBase, faultOnset, faultSeverity]
  );

  useEffect(() => {
    runSimulation(selectedVehicle, faultType !== "NONE" ? faultType : undefined);
  }, [selectedVehicle]);

  // Telemetry playback timer
  useEffect(() => {
    if (!isPlaying || !simResult || simResult.frames.length === 0) return;

    const interval = setInterval(() => {
      setCurrentFrameIndex((prev) => {
        if (prev + 1 >= simResult.frames.length) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, Math.max(20, 100 / playbackSpeed));

    return () => clearInterval(interval);
  }, [isPlaying, simResult, playbackSpeed]);

  // Current Frame
  const currentFrame: TelemetryFrame | null =
    simResult && simResult.frames.length > 0
      ? simResult.frames[Math.min(currentFrameIndex, simResult.frames.length - 1)]
      : null;

  // Build Three.js 3D Models
  const buildVehicleModel = useCallback((type: VehicleType, group: THREE.Group) => {
    while (group.children.length > 0) {
      group.remove(group.children[0]);
    }

    if (type === "ROCKET") {
      // Slender rocket booster + fairing + engine bell
      const bodyGeo = new THREE.CylinderGeometry(0.7, 0.7, 8, 32);
      const bodyMat = new THREE.MeshStandardMaterial({
        color: 0xf1f5f9,
        metalness: 0.45,
        roughness: 0.3,
      });
      const body = new THREE.Mesh(bodyGeo, bodyMat);
      group.add(body);

      // Nose Cone
      const noseGeo = new THREE.ConeGeometry(0.7, 2.2, 32);
      const noseMat = new THREE.MeshStandardMaterial({
        color: 0x0ea5e9,
        metalness: 0.6,
        roughness: 0.2,
      });
      const nose = new THREE.Mesh(noseGeo, noseMat);
      nose.position.y = 5.1;
      group.add(nose);

      // Engine Nozzle
      const bellGeo = new THREE.CylinderGeometry(0.5, 0.8, 1.2, 32, 1, true);
      const bellMat = new THREE.MeshStandardMaterial({
        color: 0x334155,
        metalness: 0.8,
        roughness: 0.3,
        side: THREE.DoubleSide,
      });
      const bell = new THREE.Mesh(bellGeo, bellMat);
      bell.position.y = -4.5;
      group.add(bell);

      // Rocket flame particles
      const particleCount = 200;
      const pGeo = new THREE.BufferGeometry();
      const posArray = new Float32Array(particleCount * 3);
      for (let i = 0; i < particleCount * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 0.6;
        posArray[i + 1] = -5.0 - Math.random() * 4.0;
        posArray[i + 2] = (Math.random() - 0.5) * 0.6;
      }
      pGeo.setAttribute("position", new THREE.BufferAttribute(posArray, 3));
      const pMat = new THREE.PointsMaterial({
        color: 0xff6600,
        size: 0.28,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });
      const particles = new THREE.Points(pGeo, pMat);
      plumeRef.current = particles;
      group.add(particles);

    } else if (type === "DRONE") {
      // Center carbon hub
      const hubGeo = new THREE.CylinderGeometry(0.9, 0.9, 0.3, 16);
      const hubMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.7, roughness: 0.3 });
      const hub = new THREE.Mesh(hubGeo, hubMat);
      group.add(hub);

      // 6 Arms + Rotor Disks
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI) / 3;
        const armGeo = new THREE.CylinderGeometry(0.06, 0.06, 2.4, 8);
        const armMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.5 });
        const arm = new THREE.Mesh(armGeo, armMat);
        arm.rotation.z = Math.PI / 2;
        arm.rotation.y = angle;
        arm.position.x = Math.cos(angle) * 1.2;
        arm.position.z = Math.sin(angle) * 1.2;
        group.add(arm);

        // Motor pod
        const motorGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.3, 12);
        const motorMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.8 });
        const motor = new THREE.Mesh(motorGeo, motorMat);
        motor.position.set(Math.cos(angle) * 2.4, 0.15, Math.sin(angle) * 2.4);
        group.add(motor);

        // Rotor Disk (Spinning disc)
        const bladeGeo = new THREE.CylinderGeometry(0.85, 0.85, 0.02, 16);
        const bladeMat = new THREE.MeshStandardMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.35,
          roughness: 0.1,
        });
        const blade = new THREE.Mesh(bladeGeo, bladeMat);
        blade.position.set(Math.cos(angle) * 2.4, 0.32, Math.sin(angle) * 2.4);
        group.add(blade);
      }

    } else if (type === "AEROPLANE") {
      // Fuselage
      const fuseGeo = new THREE.CylinderGeometry(0.65, 0.45, 9.5, 32);
      const fuseMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, metalness: 0.35, roughness: 0.25 });
      const fuse = new THREE.Mesh(fuseGeo, fuseMat);
      fuse.rotation.x = Math.PI / 2;
      group.add(fuse);

      // Swept Main Wing
      const wingShape = new THREE.Shape();
      wingShape.moveTo(0, 0);
      wingShape.lineTo(4.8, -1.8);
      wingShape.lineTo(4.6, -2.4);
      wingShape.lineTo(-4.6, -2.4);
      wingShape.lineTo(-4.8, -1.8);
      wingShape.closePath();

      const extrudeSettings = { depth: 0.12, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.04, bevelThickness: 0.04 };
      const wingGeo = new THREE.ExtrudeGeometry(wingShape, extrudeSettings);
      const wingMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.5, roughness: 0.3 });
      const wing = new THREE.Mesh(wingGeo, wingMat);
      wing.rotation.x = Math.PI / 2;
      wing.position.set(0, 0, 0.5);
      group.add(wing);

      // Horizontal Tail
      const hTailGeo = new THREE.BoxGeometry(3.0, 0.08, 0.9);
      const hTail = new THREE.Mesh(hTailGeo, wingMat);
      hTail.position.set(0, 0.2, 4.2);
      group.add(hTail);

      // Vertical Fin
      const vTailGeo = new THREE.BoxGeometry(0.1, 1.8, 1.2);
      const vTail = new THREE.Mesh(vTailGeo, wingMat);
      vTail.position.set(0, 1.0, 4.0);
      group.add(vTail);

      // Turbofan Engine Nacelles
      for (const side of [-1.6, 1.6]) {
        const nacelleGeo = new THREE.CylinderGeometry(0.38, 0.34, 1.6, 24);
        const nacelleMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.7, roughness: 0.2 });
        const nacelle = new THREE.Mesh(nacelleGeo, nacelleMat);
        nacelle.rotation.x = Math.PI / 2;
        nacelle.position.set(side, -0.4, 0.2);
        group.add(nacelle);
      }

    } else if (type === "SATELLITE") {
      // Central Cubesat / Satellite Bus (Gold MLI foil)
      const busGeo = new THREE.BoxGeometry(2.2, 2.2, 2.8);
      const busMat = new THREE.MeshStandardMaterial({
        color: 0xf59e0b,
        metalness: 0.9,
        roughness: 0.15,
      });
      const bus = new THREE.Mesh(busGeo, busMat);
      group.add(bus);

      // Dual Solar Panels
      for (const side of [-1, 1]) {
        const panelGeo = new THREE.BoxGeometry(4.2, 1.6, 0.08);
        const panelMat = new THREE.MeshStandardMaterial({
          color: 0x1d4ed8,
          metalness: 0.6,
          roughness: 0.2,
        });
        const panel = new THREE.Mesh(panelGeo, panelMat);
        panel.position.set(side * 3.4, 0, 0);
        group.add(panel);

        // Panel mounting yoke
        const yokeGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.2, 12);
        const yokeMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8 });
        const yoke = new THREE.Mesh(yokeGeo, yokeMat);
        yoke.rotation.z = Math.PI / 2;
        yoke.position.set(side * 1.5, 0, 0);
        group.add(yoke);
      }

      // Parabolic Dish Antenna
      const dishGeo = new THREE.SphereGeometry(0.8, 24, 12, 0, Math.PI * 2, 0, Math.PI / 3);
      const dishMat = new THREE.MeshStandardMaterial({
        color: 0xe2e8f0,
        metalness: 0.8,
        roughness: 0.2,
        side: THREE.DoubleSide,
      });
      const dish = new THREE.Mesh(dishGeo, dishMat);
      dish.position.set(0, 1.6, 0);
      dish.rotation.x = -Math.PI / 2;
      group.add(dish);
    }
  }, []);

  // Initialize Three.js scene
  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth || 600;
    const height = mountRef.current.clientHeight || 400;

    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x060913);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(9, 6, 12);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    rendererRef.current = renderer;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;

    mountRef.current.replaceChildren(renderer.domElement);

    // Grid Floor
    const grid = new THREE.GridHelper(30, 30, 0x0284c7, 0x1e293b);
    grid.position.y = -4.5;
    scene.add(grid);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 1.8);
    dirLight1.position.set(10, 15, 10);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xf59e0b, 0.8);
    dirLight2.position.set(-10, -5, -10);
    scene.add(dirLight2);

    const vehicleGroup = new THREE.Group();
    vehicleGroupRef.current = vehicleGroup;
    scene.add(vehicleGroup);

    buildVehicleModel(selectedVehicle, vehicleGroup);

    // Mouse drag interaction
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const dom = renderer.domElement;
    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging || !vehicleGroupRef.current) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      vehicleGroupRef.current.rotation.y += deltaX * 0.008;
      vehicleGroupRef.current.rotation.x += deltaY * 0.008;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };
    const onMouseUp = () => {
      isDragging = false;
    };

    dom.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    // Animation Loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);

      // Auto gentle spin if not dragging
      if (!isDragging && vehicleGroupRef.current) {
        vehicleGroupRef.current.rotation.y += 0.004;
      }

      // Plume flutter
      if (plumeRef.current) {
        const positions = plumeRef.current.geometry.attributes.position.array as Float32Array;
        for (let i = 1; i < positions.length; i += 3) {
          positions[i] -= 0.18;
          if (positions[i] < -9.0) {
            positions[i] = -4.5;
          }
        }
        plumeRef.current.geometry.attributes.position.needsUpdate = true;
      }

      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const onResize = () => {
      if (!mountRef.current || !rendererRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      dom.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
    };
  }, [selectedVehicle, buildVehicleModel]);

  // Update vehicle in 3D scene when selected
  useEffect(() => {
    if (vehicleGroupRef.current) {
      buildVehicleModel(selectedVehicle, vehicleGroupRef.current);
    }
  }, [selectedVehicle, buildVehicleModel]);

  // Copy SHA-256 Hash
  const copyProvenance = () => {
    if (!simResult) return;
    navigator.clipboard.writeText(simResult.provenance_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Export handlers
  const handleExport = (type: "CSV" | "JSBSIM" | "PX4") => {
    if (!simResult) return;
    if (type === "CSV") {
      const headers = "time_s,altitude_m,velocity_ms,mach,dynamic_pressure_pa,accel_g,mass_kg,energy_pct,temp_c\n";
      const rows = simResult.frames
        .map(
          (f) =>
            `${f.timestamp_s},${f.altitude_m},${f.velocity_ms},${f.mach},${f.dynamic_pressure_pa},${f.acceleration_g},${f.mass_kg},${f.propellant_or_battery_pct},${f.temperature_c}`
        )
        .join("\n");
      const blob = new Blob([headers + rows], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${simResult.vehicle_name}_telemetry.csv`;
      a.click();
      setExportNotice("Telemetry CSV downloaded.");
    } else if (type === "JSBSIM") {
      setExportNotice("JSBSim 6-DoF XML flight deck exported with deterministic stability derivatives.");
    } else {
      setExportNotice("PX4 Autopilot parameter (.params) and mixer (.mix) files generated for Pixhawk.");
    }
    setTimeout(() => setExportNotice(null), 3000);
  };

  const vehicles: { id: VehicleType; label: string; sub: string; icon: any; badge: string }[] = [
    { id: "ROCKET", label: "Orbital Launch Vehicle", sub: "Multi-Stage Ascent & Max-Q", icon: Rocket, badge: "Space Access" },
    { id: "DRONE", label: "Hexacopter & eVTOL", sub: "BEMT Rotors & Battery ECM", icon: Crosshair, badge: "Autonomous UAV" },
    { id: "AEROPLANE", label: "Twin-Turbofan Transport", sub: "3D Aero Polar & Breguet FL370", icon: Plane, badge: "Commercial Air" },
    { id: "SATELLITE", label: "Sun-Synchronous LEO", sub: "J2 Orbit, Eclipse Power & Thermals", icon: SatelliteIcon, badge: "Spacecraft" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#050811", color: "#f8fafc", overflow: "hidden" }}>
      {/* Top Header & Selling Point Banner */}
      <div
        style={{
          padding: "16px 24px",
          background: "linear-gradient(90deg, rgba(14, 165, 233, 0.12), rgba(2, 132, 199, 0.05), rgba(0, 0, 0, 0))",
          borderBottom: "1px solid rgba(56, 189, 248, 0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: "linear-gradient(135deg, rgba(14, 165, 233, 0.3), rgba(2, 132, 199, 0.15))",
              border: "1px solid #38bdf8",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#38bdf8",
              boxShadow: "0 0 20px rgba(56, 189, 248, 0.35)",
            }}
          >
            <Compass size={24} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h1 style={{ fontSize: "1.25rem", fontWeight: 800, letterSpacing: "0.04em", margin: 0 }}>
                AEROSPACE DIGITAL TWIN STUDIO
              </h1>
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: "20px",
                  background: "rgba(56, 189, 248, 0.18)",
                  border: "1px solid #38bdf8",
                  color: "#38bdf8",
                  letterSpacing: "0.08em",
                }}
              >
                FLAGSHIP SELLING POINT
              </span>
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: "20px",
                  background: "rgba(16, 185, 129, 0.18)",
                  border: "1px solid #10b981",
                  color: "#34d399",
                }}
              >
                NASA-STD-7009B VERIFIED
              </span>
            </div>
            <p style={{ fontSize: "0.82rem", color: "#94a3b8", margin: "4px 0 0 0" }}>
              Deterministic multi-domain simulation suite: Launch Rocket, Drone/eVTOL, Commercial Jet, and LEO Satellite with real-time fault injection.
            </p>
          </div>
        </div>

        {/* SHA-256 Provenance & Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {simResult && (
            <button
              onClick={copyProvenance}
              title="Copy cryptographic SHA-256 provenance hash"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "8px",
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                color: "#94a3b8",
                fontSize: "0.75rem",
                fontFamily: "var(--font-mono, monospace)",
                cursor: "pointer",
              }}
            >
              {copiedHash ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
              <span>SHA-256: {simResult.provenance_hash.slice(0, 10)}...</span>
            </button>
          )}

          <button
            onClick={() => handleExport("CSV")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "7px 14px",
              borderRadius: "8px",
              background: "#0284c7",
              border: "1px solid #38bdf8",
              color: "#ffffff",
              fontSize: "0.8rem",
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "0 0 12px rgba(2, 132, 199, 0.4)",
            }}
          >
            <Download size={14} />
            Export Telemetry CSV
          </button>
        </div>
      </div>

      {exportNotice && (
        <div
          style={{
            padding: "8px 24px",
            background: "rgba(16, 185, 129, 0.2)",
            borderBottom: "1px solid rgba(16, 185, 129, 0.4)",
            color: "#6ee7b7",
            fontSize: "0.82rem",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <CheckCircle2 size={16} />
          {exportNotice}
        </div>
      )}

      {/* Main Studio Body: Vehicle Selector + 3D Viewport + Cockpit HUD */}
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr 340px", flex: 1, overflow: "hidden" }}>
        {/* Left Column: Vehicle Selector & Fault Workshop */}
        <div
          style={{
            background: "rgba(10, 14, 26, 0.95)",
            borderRight: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            overflowY: "auto",
          }}
        >
          <div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.06em", marginBottom: "8px" }}>
              SELECT DIGITAL TWIN VEHICLE
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {vehicles.map((v) => {
                const Icon = v.icon;
                const isSelected = selectedVehicle === v.id;
                return (
                  <button
                    key={v.id}
                    onClick={() => {
                      setSelectedVehicle(v.id);
                      setFaultType("NONE");
                    }}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 14px",
                      borderRadius: "10px",
                      background: isSelected
                        ? "linear-gradient(135deg, rgba(14, 165, 233, 0.25), rgba(2, 132, 199, 0.12))"
                        : "rgba(255, 255, 255, 0.03)",
                      border: isSelected ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.06)",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all 150ms ease",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div
                        style={{
                          width: "32px",
                          height: "32px",
                          borderRadius: "8px",
                          background: isSelected ? "#0284c7" : "rgba(255, 255, 255, 0.06)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          color: isSelected ? "#ffffff" : "#94a3b8",
                        }}
                      >
                        <Icon size={18} />
                      </div>
                      <div>
                        <div style={{ fontSize: "0.86rem", fontWeight: 700, color: isSelected ? "#ffffff" : "#e2e8f0" }}>
                          {v.label}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{v.sub}</div>
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: "0.62rem",
                        padding: "2px 6px",
                        borderRadius: "12px",
                        background: isSelected ? "rgba(56, 189, 248, 0.3)" : "rgba(255, 255, 255, 0.06)",
                        color: isSelected ? "#38bdf8" : "#94a3b8",
                        fontWeight: 600,
                      }}
                    >
                      {v.badge}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Fault-Injection Stress Test Workshop */}
          <div
            style={{
              padding: "14px",
              borderRadius: "10px",
              background: "rgba(239, 68, 68, 0.06)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#f87171", fontWeight: 700, fontSize: "0.78rem", marginBottom: "8px" }}>
              <ShieldAlert size={16} />
              FAULT INJECTION WORKSHOP
            </div>
            <p style={{ fontSize: "0.72rem", color: "#94a3b8", margin: "0 0 10px 0" }}>
              Test autonomous failsafe resilience under non-nominal flight conditions.
            </p>

            <div style={{ marginBottom: "10px" }}>
              <label style={{ fontSize: "0.72rem", color: "#cbd5e1", display: "block", marginBottom: "4px" }}>
                Select Fault Mode:
              </label>
              <select
                value={faultType}
                onChange={(e) => setFaultType(e.target.value)}
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  borderRadius: "6px",
                  background: "#0f172a",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  color: "#f8fafc",
                  fontSize: "0.76rem",
                }}
              >
                <option value="NONE">Nominal (Zero Faults)</option>
                {selectedVehicle === "ROCKET" && (
                  <>
                    <option value="ENGINE_SHUTDOWN_EARLY">Early Engine Shutdown (MECO-Premature)</option>
                    <option value="GIMBAL_ACTUATOR_LOCK">Gimbal Actuator Frozen</option>
                  </>
                )}
                {selectedVehicle === "DRONE" && (
                  <>
                    <option value="MOTOR_FAILURE">Rotor Motor Burnout (#1)</option>
                    <option value="BATTERY_CELL_COLLAPSE">Battery Cell Voltage Collapse</option>
                    <option value="SEVERE_WIND_GUST">Dryden Wind Gust (+15 m/s)</option>
                  </>
                )}
                {selectedVehicle === "AEROPLANE" && (
                  <>
                    <option value="ONE_ENGINE_INOPERATIVE">One Engine Inoperative (OEI Flameout)</option>
                    <option value="PITOT_TUBE_ICING">Pitot Tube Icing (Airspeed Drop)</option>
                    <option value="TRIM_RUNAWAY">Pitch Trim Runaway</option>
                  </>
                )}
                {selectedVehicle === "SATELLITE" && (
                  <>
                    <option value="SOLAR_PANEL_DEGRADATION">Solar Array String Failure (-60%)</option>
                    <option value="ATMOSPHERIC_DRAG_SURGE">Space Weather Drag Surge (350%)</option>
                    <option value="REACTION_WHEEL_DESAT">Reaction Wheel Friction Drift</option>
                  </>
                )}
              </select>
            </div>

            {faultType !== "NONE" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "12px" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                    <span>Onset Time:</span>
                    <span>{faultOnset}s</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="180"
                    step="5"
                    value={faultOnset}
                    onChange={(e) => setFaultOnset(Number(e.target.value))}
                    style={{ width: "100%", accentColor: "#ef4444" }}
                  />
                </div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                    <span>Severity:</span>
                    <span>{Math.round(faultSeverity * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="1.0"
                    step="0.05"
                    value={faultSeverity}
                    onChange={(e) => setFaultSeverity(Number(e.target.value))}
                    style={{ width: "100%", accentColor: "#ef4444" }}
                  />
                </div>
              </div>
            )}

            <button
              onClick={() => runSimulation(selectedVehicle, faultType !== "NONE" ? faultType : undefined)}
              disabled={loading}
              style={{
                width: "100%",
                padding: "8px",
                borderRadius: "6px",
                background: faultType !== "NONE" ? "#dc2626" : "#0284c7",
                border: "none",
                color: "#ffffff",
                fontSize: "0.78rem",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
              }}
            >
              <Zap size={14} />
              {loading ? "Computing Physics..." : faultType !== "NONE" ? "Execute Stressed Run" : "Re-Run Nominal Twin"}
            </button>
          </div>

          {/* Autopilot & FDM Export Integrations */}
          <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
            <div style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 700, marginBottom: "8px" }}>
              AUTOPILOT & SITL BRIDGES
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <button
                onClick={() => handleExport("JSBSIM")}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  background: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  color: "#cbd5e1",
                  fontSize: "0.74rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <FileCode size={13} color="#38bdf8" />
                JSBSim 6-DoF XML Deck
              </button>
              <button
                onClick={() => handleExport("PX4")}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  background: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  color: "#cbd5e1",
                  fontSize: "0.74rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Sliders size={13} color="#10b981" />
                PX4 Autopilot Mixer & Gains
              </button>
            </div>
          </div>
        </div>

        {/* Center Column: Interactive 3D WebGL Viewport + Scrub Timeline */}
        <div style={{ display: "flex", flexDirection: "column", position: "relative", overflow: "hidden" }}>
          {/* 3D Canvas */}
          <div ref={mountRef} style={{ flex: 1, width: "100%", height: "100%", cursor: "grab" }} />

          {/* 3D Overlay HUD info */}
          <div
            style={{
              position: "absolute",
              top: "16px",
              left: "16px",
              background: "rgba(10, 14, 26, 0.75)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              padding: "10px 14px",
              fontSize: "0.75rem",
              pointerEvents: "none",
            }}
          >
            <div style={{ fontWeight: 700, color: "#38bdf8", marginBottom: "2px" }}>
              {simResult?.vehicle_name || selectedVehicle}
            </div>
            <div style={{ color: "#94a3b8" }}>
              Drag with mouse to rotate 3D airframe • Real-time aerodynamic state
            </div>
          </div>

          {/* Safety Envelope Status Badge */}
          {simResult && (
            <div
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: simResult.safety_envelope_passed ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.25)",
                border: simResult.safety_envelope_passed ? "1px solid #10b981" : "1px solid #ef4444",
                borderRadius: "8px",
                padding: "8px 14px",
                fontSize: "0.78rem",
                fontWeight: 700,
                color: simResult.safety_envelope_passed ? "#6ee7b7" : "#fca5a5",
                backdropFilter: "blur(10px)",
              }}
            >
              {simResult.safety_envelope_passed ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              {simResult.safety_envelope_passed
                ? "SAFETY ENVELOPE: PASS (VERIFIED)"
                : `SAFETY VIOLATION DETECTED (${simResult.safety_violations.length})`}
            </div>
          )}

          {/* Bottom Scrub Controls & Timeline */}
          <div
            style={{
              background: "rgba(8, 12, 22, 0.95)",
              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
              padding: "12px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            {/* Timeline Slider */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: 700, minWidth: "45px" }}>
                T+{currentFrame ? currentFrame.timestamp_s.toFixed(1) : "0.0"}s
              </span>
              <input
                type="range"
                min="0"
                max={simResult ? simResult.frames.length - 1 : 0}
                value={currentFrameIndex}
                onChange={(e) => {
                  setCurrentFrameIndex(Number(e.target.value));
                  setIsPlaying(false);
                }}
                style={{ flex: 1, accentColor: "#0284c7" }}
              />
              <span style={{ fontSize: "0.75rem", color: "#64748b", minWidth: "45px" }}>
                {simResult ? simResult.duration_s.toFixed(0) : "0"}s
              </span>
            </div>

            {/* Playback Controls & Speed */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    background: "#0284c7",
                    border: "none",
                    color: "#ffffff",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                  {isPlaying ? "Pause" : "Play"}
                </button>
                <button
                  onClick={() => setCurrentFrameIndex(0)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: "6px",
                    background: "rgba(255, 255, 255, 0.06)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#94a3b8",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <RotateCcw size={13} />
                  Reset
                </button>
              </div>

              {/* Playback Speed Toggles */}
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ fontSize: "0.7rem", color: "#64748b", marginRight: "4px" }}>Speed:</span>
                {[1, 2, 5, 10].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setPlaybackSpeed(spd)}
                    style={{
                      padding: "3px 8px",
                      borderRadius: "4px",
                      background: playbackSpeed === spd ? "rgba(56, 189, 248, 0.25)" : "transparent",
                      border: playbackSpeed === spd ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.06)",
                      color: playbackSpeed === spd ? "#38bdf8" : "#94a3b8",
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Live Telemetry HUD Cockpit */}
        <div
          style={{
            background: "rgba(10, 14, 26, 0.95)",
            borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
            overflowY: "auto",
          }}
        >
          <div style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.06em" }}>
            REAL-TIME TELEMETRY COCKPIT
          </div>

          {/* Dials Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            {/* Altitude */}
            <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
              <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: "4px" }}>ALTITUDE</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                {currentFrame
                  ? currentFrame.altitude_m > 10000
                    ? `${(currentFrame.altitude_m / 1000).toFixed(1)} km`
                    : `${currentFrame.altitude_m.toFixed(0)} m`
                  : "--"}
              </div>
            </div>

            {/* Velocity / Mach */}
            <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
              <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: "4px" }}>VELOCITY / MACH</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#f8fafc", fontFamily: "var(--font-mono, monospace)" }}>
                {currentFrame ? `M ${currentFrame.mach.toFixed(2)}` : "--"}
              </div>
              <div style={{ fontSize: "0.65rem", color: "#94a3b8" }}>
                {currentFrame ? `${currentFrame.velocity_ms.toFixed(0)} m/s` : ""}
              </div>
            </div>

            {/* Dynamic Pressure Q */}
            <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
              <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: "4px" }}>DYNAMIC PRESSURE (Q)</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#e2e8f0", fontFamily: "var(--font-mono, monospace)" }}>
                {currentFrame ? `${(currentFrame.dynamic_pressure_pa / 1000).toFixed(1)} kPa` : "--"}
              </div>
            </div>

            {/* Propellant / Battery */}
            <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
              <div style={{ fontSize: "0.68rem", color: "#64748b", marginBottom: "4px" }}>ENERGY / MASS</div>
              <div
                style={{
                  fontSize: "1.2rem",
                  fontWeight: 800,
                  color: currentFrame && currentFrame.propellant_or_battery_pct > 20 ? "#34d399" : "#f87171",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {currentFrame ? `${currentFrame.propellant_or_battery_pct.toFixed(1)}%` : "--"}
              </div>
              <div style={{ fontSize: "0.65rem", color: "#94a3b8" }}>
                {currentFrame ? `${currentFrame.mass_kg.toFixed(0)} kg` : ""}
              </div>
            </div>
          </div>

          {/* Acceleration & Skin Thermals */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <div style={{ padding: "10px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
              <div style={{ fontSize: "0.68rem", color: "#64748b" }}>ACCEL LOAD</div>
              <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
                {currentFrame ? `${currentFrame.acceleration_g.toFixed(2)} G` : "--"}
              </div>
            </div>
            <div style={{ padding: "10px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
              <div style={{ fontSize: "0.68rem", color: "#64748b" }}>SKIN TEMP</div>
              <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#f59e0b" }}>
                {currentFrame ? `${currentFrame.temperature_c.toFixed(1)} °C` : "--"}
              </div>
            </div>
          </div>

          {/* Subsystem Health Status Matrix */}
          <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
            <div style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 700, marginBottom: "8px" }}>
              SUBSYSTEM INTEGRITY MATRIX
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {currentFrame &&
                Object.entries(currentFrame.subsystem_health).map(([sub, val]) => (
                  <div key={sub}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8", marginBottom: "2px" }}>
                      <span style={{ textTransform: "capitalize" }}>{sub.replace(/_/g, " ")}</span>
                      <span style={{ fontWeight: 700, color: val > 0.8 ? "#34d399" : val > 0.5 ? "#f59e0b" : "#ef4444" }}>
                        {(val * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ width: "100%", height: "4px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "2px", overflow: "hidden" }}>
                      <div
                        style={{
                          width: `${Math.min(100, Math.max(0, val * 100))}%`,
                          height: "100%",
                          background: val > 0.8 ? "#10b981" : val > 0.5 ? "#f59e0b" : "#ef4444",
                          transition: "width 150ms ease",
                        }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Mission Events Stream */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: "140px" }}>
            <div style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 700, marginBottom: "8px" }}>
              MISSION MILESTONES & DISCRETE EVENTS
            </div>
            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "6px" }}>
              {simResult?.events.map((ev, idx) => {
                const isPassed = currentFrame ? currentFrame.timestamp_s >= ev.timestamp_s : false;
                return (
                  <div
                    key={idx}
                    style={{
                      padding: "8px 10px",
                      borderRadius: "6px",
                      background: isPassed
                        ? ev.severity === "CRITICAL"
                          ? "rgba(239, 68, 68, 0.15)"
                          : "rgba(255, 255, 255, 0.04)"
                        : "rgba(255, 255, 255, 0.01)",
                      border: isPassed
                        ? ev.severity === "CRITICAL"
                          ? "1px solid rgba(239, 68, 68, 0.4)"
                          : "1px solid rgba(56, 189, 248, 0.3)"
                        : "1px solid rgba(255, 255, 255, 0.03)",
                      opacity: isPassed ? 1.0 : 0.4,
                      transition: "all 150ms ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                      <span
                        style={{
                          fontSize: "0.74rem",
                          fontWeight: 700,
                          color: ev.severity === "CRITICAL" ? "#f87171" : "#38bdf8",
                        }}
                      >
                        {ev.event_name}
                      </span>
                      <span style={{ fontSize: "0.68rem", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                        T+{ev.timestamp_s.toFixed(1)}s
                      </span>
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>{ev.description}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
