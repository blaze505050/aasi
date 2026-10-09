"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import * as THREE from "three";
import {
  Box,
  Layers,
  RotateCcw,
  Zap,
  Sliders,
  ChevronRight,
  Download,
  X,
  Eye,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

interface ChordwiseSlicePoint {
  xc: number;
  cp_upper: number;
  cp_lower: number;
  is_shock: boolean;
}

interface MeshStats {
  nodes_total: number;
  triangles_count: number;
  quad_panels: number;
  aspect_ratio: number;
  span_m: number;
  sweep_deg: number;
}

interface Surface3DData {
  airfoil: string;
  alpha_deg: number;
  mach: number;
  reynolds: number;
  cl: number;
  cd: number;
  cm: number;
  lift_to_drag: number;
  has_shock: boolean;
  shock_xc: number | null;
  stagnation_xc: number;
  vertices: number[];
  normals: number[];
  colors: number[];
  indices: number[];
  cp_min: number;
  cp_max: number;
  slice_data: ChordwiseSlicePoint[];
  mesh_stats: MeshStats;
}

interface ThreeDimensionalPressureMeshProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

export const ThreeDimensionalPressureMesh: React.FC<ThreeDimensionalPressureMeshProps> = ({
  isOpen,
  onClose,
  apiBase,
}) => {
  // Flight & Geometry parameters
  const [airfoil, setAirfoil] = useState("RAE 2822");
  const [alpha, setAlpha] = useState(2.31);
  const [mach, setMach] = useState(0.729);
  const [sweep, setSweep] = useState(15);
  const [sliceEta, setSliceEta] = useState(0.5);
  const [showWireframe, setShowWireframe] = useState(true);

  // Data & loading state
  const [surfaceData, setSurfaceData] = useState<Surface3DData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Three.js canvas container ref
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const meshGroupRef = useRef<THREE.Group | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);

  // Mouse interaction state for orbit controls
  const isDraggingRef = useRef(false);
  const prevMouseRef = useRef({ x: 0, y: 0 });
  const rotationRef = useRef({ x: 0.35, y: -0.65 });
  const zoomRef = useRef(3.5);

  // Fetch surface mesh from backend
  const fetchMesh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/aerodb/surface-pressure-3d`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          airfoil,
          alpha_deg: alpha,
          mach,
          reynolds: 6.5e6,
          span: 3.2,
          aspect_ratio: 6.5,
          sweep_deg: sweep,
          taper_ratio: 0.68,
          nx: 48,
          ny: 22,
          slice_eta: sliceEta,
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to generate 3D surface mesh (HTTP ${res.status})`);
      }

      const data: Surface3DData = await res.json();
      setSurfaceData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load aerodynamic mesh.");
    } finally {
      setLoading(false);
    }
  }, [airfoil, alpha, mach, sweep, sliceEta, apiBase]);

  // Initial fetch and trigger on geometry change
  useEffect(() => {
    if (isOpen) {
      fetchMesh();
    }
  }, [isOpen, airfoil, alpha, mach, sweep, sliceEta, fetchMesh]);

  // Initialize Three.js Scene
  useEffect(() => {
    if (!isOpen || !canvasContainerRef.current) return;

    const container = canvasContainerRef.current;
    const width = container.clientWidth || 700;
    const height = container.clientHeight || 500;

    // Create Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060911);
    sceneRef.current = scene;

    // Create Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 1.2, zoomRef.current);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Create Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Ambient and Directional Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.7);
    dirLight1.position.set(5, 10, 7);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.35);
    dirLight2.position.set(-5, -5, -5);
    scene.add(dirLight2);

    // Coordinate Grid Helper
    const grid = new THREE.GridHelper(5, 20, 0x1e293b, 0x0f172a);
    grid.position.y = -0.8;
    scene.add(grid);

    // Mesh Group
    const meshGroup = new THREE.Group();
    scene.add(meshGroup);
    meshGroupRef.current = meshGroup;

    // Animation loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (meshGroupRef.current) {
        meshGroupRef.current.rotation.x = rotationRef.current.x;
        meshGroupRef.current.rotation.y = rotationRef.current.y;
      }
      if (cameraRef.current) {
        cameraRef.current.position.z = zoomRef.current;
      }
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!container || !camera || !renderer) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
    };
  }, [isOpen]);

  // Update Three.js Mesh when surfaceData changes
  useEffect(() => {
    if (!surfaceData || !meshGroupRef.current) return;

    const group = meshGroupRef.current;
    // Clear previous children
    while (group.children.length > 0) {
      const child = group.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      group.remove(child);
    }

    const { vertices, normals, colors, indices } = surfaceData;
    if (vertices.length === 0 || indices.length === 0) return;

    // Create BufferGeometry
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(new Float32Array(vertices), 3)
    );
    geometry.setAttribute(
      "normal",
      new THREE.Float32BufferAttribute(new Float32Array(normals), 3)
    );
    geometry.setAttribute(
      "color",
      new THREE.Float32BufferAttribute(new Float32Array(colors), 3)
    );
    geometry.setIndex(indices);
    geometry.computeVertexNormals();

    // Material with Vertex Colors
    const material = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.35,
      metalness: 0.15,
      side: THREE.DoubleSide,
      wireframe: false,
    });

    const surfaceMesh = new THREE.Mesh(geometry, material);
    // Center mesh around origin
    surfaceMesh.position.set(-0.8, 0, 0);
    group.add(surfaceMesh);

    // Optional Wireframe overlay
    if (showWireframe) {
      const wireframeMaterial = new THREE.MeshBasicMaterial({
        color: 0x0f172a,
        wireframe: true,
        transparent: true,
        opacity: 0.3,
      });
      const wireMesh = new THREE.Mesh(geometry, wireframeMaterial);
      wireMesh.position.set(-0.8, 0, 0);
      group.add(wireMesh);
    }

    // Shock wave marker if present
    if (surfaceData.has_shock && surfaceData.shock_xc) {
      const shockGeo = new THREE.BufferGeometry();
      const b = surfaceData.mesh_stats.span_m;
      const xShock = surfaceData.shock_xc;
      const shockPts = new Float32Array([
        xShock - 0.8, -b * 0.45, 0.08,
        xShock - 0.8, b * 0.45, 0.08,
      ]);
      shockGeo.setAttribute("position", new THREE.BufferAttribute(shockPts, 3));
      const shockMat = new THREE.LineBasicMaterial({
        color: 0xef4444,
        linewidth: 2,
      });
      const shockLine = new THREE.Line(shockGeo, shockMat);
      group.add(shockLine);
    }
  }, [surfaceData, showWireframe]);

  // Orbit controls mouse event handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    prevMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - prevMouseRef.current.x;
    const dy = e.clientY - prevMouseRef.current.y;
    rotationRef.current.y += dx * 0.008;
    rotationRef.current.x += dy * 0.008;
    // Clamp pitch to avoid flip
    rotationRef.current.x = Math.max(-1.4, Math.min(1.4, rotationRef.current.x));
    prevMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    zoomRef.current += e.deltaY * 0.003;
    zoomRef.current = Math.max(1.8, Math.min(7.0, zoomRef.current));
  };

  const handleResetCamera = () => {
    rotationRef.current = { x: 0.35, y: -0.65 };
    zoomRef.current = 3.5;
  };

  // Export Mesh as Wavefront OBJ
  const handleExportOBJ = () => {
    if (!surfaceData) return;
    const { vertices, indices, airfoil, alpha_deg, mach } = surfaceData;
    let obj = `# AASI Transonic CFD Mesh Export\n# Geometry: ${airfoil}, Alpha: ${alpha_deg} deg, Mach: ${mach}\n`;
    for (let i = 0; i < vertices.length; i += 3) {
      obj += `v ${vertices[i]} ${vertices[i + 1]} ${vertices[i + 2]}\n`;
    }
    for (let i = 0; i < indices.length; i += 3) {
      obj += `f ${indices[i] + 1} ${indices[i + 1] + 1} ${indices[i + 2] + 1}\n`;
    }
    const blob = new Blob([obj], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `AASI_${airfoil.replace(/[^a-zA-Z0-9]/g, "_")}_Alpha${alpha_deg}_M${mach}.obj`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="aerospace-modal-overlay" onClick={onClose}>
      <div
        className="aerospace-modal-container"
        style={{
          maxWidth: "1350px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 20px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            background: "rgba(10, 15, 28, 0.95)",
            backdropFilter: "blur(20px)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "34px",
                height: "34px",
                borderRadius: "8px",
                background: "rgba(56, 189, 248, 0.15)",
                border: "1px solid rgba(56, 189, 248, 0.35)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#38bdf8",
              }}
            >
              <Box size={18} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700 }}>
                  3D Surface Pressure (Cp) &amp; Mesh Contour Visualizer
                </h3>
                <span
                  style={{
                    fontSize: "0.68rem",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(245, 158, 11, 0.15)",
                    border: "1px solid rgba(245, 158, 11, 0.35)",
                    color: "#f59e0b",
                    fontWeight: 700,
                  }}
                >
                  ASME V&amp;V 20 / Transonic Shock Capturing
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.72rem", color: "#64748b" }}>
                Interactive 3D finite wing surface mesh with high-contrast Cp colormap, suction peak, and chordwise 2D slice sync.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={handleExportOBJ}
              disabled={!surfaceData}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "6px",
                background: "#1e293b",
                border: "1px solid #334155",
                color: "#f8fafc",
                fontSize: "0.76rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
              title="Download 3D CFD Surface Mesh as Wavefront OBJ"
            >
              <Download size={13} />
              <span>Export OBJ Mesh</span>
            </button>

            <button
              onClick={onClose}
              style={{
                background: "none",
                border: "none",
                color: "#64748b",
                cursor: "pointer",
                padding: "4px",
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Modal Main Body: Left 3D Viewport, Right Controls & 2D Cp Slice */}
        <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
          {/* Left: 3D WebGL Canvas */}
          <div
            style={{
              flex: 1,
              position: "relative",
              background: "#060911",
              borderRight: "1px solid #1e293b",
              userSelect: "none",
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onWheel={handleWheel}
          >
            <div ref={canvasContainerRef} style={{ width: "100%", height: "100%" }} />

            {/* Overlaid Viewport HUD Controls */}
            <div
              style={{
                position: "absolute",
                top: "14px",
                left: "14px",
                display: "flex",
                gap: "8px",
                background: "rgba(12, 17, 29, 0.8)",
                backdropFilter: "blur(6px)",
                padding: "6px 10px",
                borderRadius: "8px",
                border: "1px solid #1e293b",
                fontSize: "0.72rem",
                color: "#94a3b8",
              }}
            >
              <button
                onClick={handleResetCamera}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  background: "none",
                  border: "none",
                  color: "#cbd5e1",
                  cursor: "pointer",
                  fontSize: "0.72rem",
                }}
                title="Reset Camera Orientation"
              >
                <RotateCcw size={12} />
                <span>Reset Orbit</span>
              </button>
              <span style={{ color: "#334155" }}>|</span>
              <button
                onClick={() => setShowWireframe(!showWireframe)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  background: "none",
                  border: "none",
                  color: showWireframe ? "#38bdf8" : "#64748b",
                  cursor: "pointer",
                  fontSize: "0.72rem",
                }}
              >
                <Layers size={12} />
                <span>CFD Grid Lines: {showWireframe ? "ON" : "OFF"}</span>
              </button>
            </div>

            {/* Colormap Legend */}
            <div
              style={{
                position: "absolute",
                bottom: "16px",
                left: "16px",
                background: "rgba(12, 17, 29, 0.85)",
                backdropFilter: "blur(6px)",
                padding: "8px 12px",
                borderRadius: "8px",
                border: "1px solid #1e293b",
              }}
            >
              <div style={{ fontSize: "0.68rem", color: "#94a3b8", fontWeight: 700, marginBottom: "4px" }}>
                PRESSURE COEFFICIENT (Cp)
              </div>
              <div
                style={{
                  width: "180px",
                  height: "10px",
                  borderRadius: "3px",
                  background: "linear-gradient(to right, #0284c7, #38bdf8, #475569, #f59e0b, #ef4444)",
                  marginBottom: "4px",
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "0.65rem",
                  color: "#94a3b8",
                  fontFamily: "var(--font-mono)",
                }}
              >
                <span style={{ color: "#38bdf8" }}>{surfaceData ? surfaceData.cp_min : -3.5} (Suction)</span>
                <span>0.0</span>
                <span style={{ color: "#ef4444" }}>+1.0 (Stagnation)</span>
              </div>
            </div>

            {/* Transonic Shock Badge */}
            {surfaceData?.has_shock && (
              <div
                style={{
                  position: "absolute",
                  top: "14px",
                  right: "14px",
                  background: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid rgba(239, 68, 68, 0.4)",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "#ef4444",
                  fontSize: "0.74rem",
                  fontWeight: 700,
                }}
              >
                <Zap size={14} />
                <span>Transonic Normal Shock (x/c ≈ {surfaceData.shock_xc})</span>
              </div>
            )}
          </div>

          {/* Right: Controls & Synchronized 2D Chordwise Slice Plot */}
          <div
            style={{
              width: "min(400px, 34vw)",
              minWidth: "300px",
              background: "rgba(10, 15, 28, 0.95)",
              borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              flexDirection: "column",
              padding: "14px",
              overflowY: "auto",
              gap: "14px",
            }}
          >
            {/* Aerodynamic Controls Panel */}
            <div
              style={{
                background: "#111827",
                border: "1px solid #1f2937",
                borderRadius: "8px",
                padding: "12px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  color: "#38bdf8",
                  fontSize: "0.76rem",
                  fontWeight: 700,
                  marginBottom: "12px",
                }}
              >
                <Sliders size={14} />
                <span>Aerodynamic &amp; Planform Parameters</span>
              </div>

              {/* Geometry Profile */}
              <div style={{ marginBottom: "10px" }}>
                <label style={{ fontSize: "0.7rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                  Airfoil Geometry Profile
                </label>
                <select
                  value={airfoil}
                  onChange={(e) => setAirfoil(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "6px 10px",
                    borderRadius: "6px",
                    background: "#0c111d",
                    border: "1px solid #1f2937",
                    color: "#f8fafc",
                    fontSize: "0.78rem",
                    cursor: "pointer",
                  }}
                >
                  <option value="RAE 2822">RAE 2822 Transonic Supercritical</option>
                  <option value="NASA SC(2)-0714">NASA SC(2)-0714 Supercritical Transport</option>
                  <option value="NACA 0012">NACA 0012 Classic Symmetric</option>
                  <option value="Clark Y">Clark Y General Aviation</option>
                </select>
              </div>

              {/* Angle of Attack Slider */}
              <div style={{ marginBottom: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                  <span>Angle of Attack (α)</span>
                  <span style={{ color: "#f59e0b", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                    {alpha.toFixed(2)}°
                  </span>
                </div>
                <input
                  type="range"
                  min="-4.0"
                  max="16.0"
                  step="0.25"
                  value={alpha}
                  onChange={(e) => setAlpha(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#f59e0b", cursor: "pointer" }}
                />
              </div>

              {/* Mach Number Slider */}
              <div style={{ marginBottom: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                  <span>Mach Number (M∞)</span>
                  <span style={{ color: mach >= 0.7 ? "#ef4444" : "#38bdf8", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                    {mach.toFixed(3)} {mach >= 0.7 ? "(Transonic Shock)" : "(Subsonic)"}
                  </span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.85"
                  step="0.01"
                  value={mach}
                  onChange={(e) => setMach(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: mach >= 0.7 ? "#ef4444" : "#38bdf8", cursor: "pointer" }}
                />
              </div>

              {/* Sweep Angle Slider */}
              <div style={{ marginBottom: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                  <span>Leading Edge Sweep (Λ)</span>
                  <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono)" }}>{sweep}°</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="35"
                  step="1"
                  value={sweep}
                  onChange={(e) => setSweep(parseInt(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8", cursor: "pointer" }}
                />
              </div>

              {/* Span Station Slice Slider */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                  <span>Chordwise Cut Station (η = 2y/b)</span>
                  <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono)" }}>
                    {(sliceEta * 100).toFixed(0)}% Span
                  </span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.95"
                  step="0.05"
                  value={sliceEta}
                  onChange={(e) => setSliceEta(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8", cursor: "pointer" }}
                />
              </div>
            </div>

            {/* Aerodynamic Coefficients Bar */}
            {surfaceData && (
              <div
                style={{
                  background: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "8px",
                  padding: "12px",
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr 1fr",
                  gap: "8px",
                  textAlign: "center",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.62rem", color: "#64748b" }}>CL (LIFT)</div>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#38bdf8", fontFamily: "var(--font-mono)" }}>
                    {surfaceData.cl.toFixed(3)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.62rem", color: "#64748b" }}>CD (DRAG)</div>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f59e0b", fontFamily: "var(--font-mono)" }}>
                    {surfaceData.cd.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.62rem", color: "#64748b" }}>L/D RATIO</div>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#10b981", fontFamily: "var(--font-mono)" }}>
                    {surfaceData.lift_to_drag.toFixed(1)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.62rem", color: "#64748b" }}>CM (PITCH)</div>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                    {surfaceData.cm.toFixed(3)}
                  </div>
                </div>
              </div>
            )}

            {/* Synchronized 2D Chordwise Cp Slice Plot */}
            <div
              style={{
                flex: 1,
                background: "#111827",
                border: "1px solid #1f2937",
                borderRadius: "8px",
                padding: "12px",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "8px",
                }}
              >
                <span style={{ fontSize: "0.74rem", fontWeight: 700, color: "#cbd5e1" }}>
                  Chordwise Slice: -Cp vs x/c (η = {(sliceEta * 100).toFixed(0)}%)
                </span>
                <span style={{ fontSize: "0.66rem", color: "#64748b" }}>Standard Aero Inverted</span>
              </div>

              {/* SVG 2D Cp Plot */}
              {surfaceData?.slice_data && (
                <div style={{ flex: 1, minHeight: "180px", position: "relative" }}>
                  <svg
                    viewBox="0 0 360 170"
                    style={{ width: "100%", height: "100%", display: "block" }}
                  >
                    {/* Plot Background & Grid */}
                    <rect x="35" y="10" width="315" height="135" fill="#0c111d" rx="4" />
                    <line x1="35" y1="77" x2="350" y2="77" stroke="#1f2937" strokeDasharray="3 3" />
                    <line x1="192" y1="10" x2="192" y2="145" stroke="#1f2937" strokeDasharray="3 3" />

                    {/* Zero Cp line */}
                    <line x1="35" y1="110" x2="350" y2="110" stroke="#334155" strokeWidth="1" />
                    <text x="10" y="113" fill="#64748b" fontSize="8" fontFamily="monospace">
                      0.0
                    </text>
                    <text x="5" y="25" fill="#38bdf8" fontSize="8" fontFamily="monospace">
                      -3.0
                    </text>
                    <text x="5" y="145" fill="#ef4444" fontSize="8" fontFamily="monospace">
                      +1.0
                    </text>

                    {/* Upper Surface Path (-Cp inverted, higher means more suction) */}
                    {(() => {
                      const pts = surfaceData.slice_data;
                      const uPath = pts
                        .map((pt, i) => {
                          const px = 35 + pt.xc * 315;
                          // Inverted Cp mapping: cp = -3.0 maps to y=20, cp = +1.0 maps to y=140
                          const py = 110 + pt.cp_upper * 30;
                          return `${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`;
                        })
                        .join(" ");

                      const lPath = pts
                        .map((pt, i) => {
                          const px = 35 + pt.xc * 315;
                          const py = 110 + pt.cp_lower * 30;
                          return `${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`;
                        })
                        .join(" ");

                      return (
                        <>
                          <path
                            d={uPath}
                            fill="none"
                            stroke="#38bdf8"
                            strokeWidth="2"
                            strokeLinecap="round"
                          />
                          <path
                            d={lPath}
                            fill="none"
                            stroke="#f59e0b"
                            strokeWidth="1.8"
                            strokeDasharray="4 2"
                            strokeLinecap="round"
                          />
                        </>
                      );
                    })()}

                    {/* Shock Discontinuity Callout */}
                    {surfaceData.has_shock && surfaceData.shock_xc && (
                      <g>
                        <line
                          x1={35 + surfaceData.shock_xc * 315}
                          y1="10"
                          x2={35 + surfaceData.shock_xc * 315}
                          y2="145"
                          stroke="#ef4444"
                          strokeWidth="1.5"
                          strokeDasharray="2 2"
                        />
                        <text
                          x={35 + surfaceData.shock_xc * 315 + 4}
                          y="24"
                          fill="#ef4444"
                          fontSize="8"
                          fontWeight="bold"
                        >
                          Shock
                        </text>
                      </g>
                    )}

                    {/* X axis labels */}
                    <text x="35" y="160" fill="#64748b" fontSize="8">
                      0.0 (LE)
                    </text>
                    <text x="180" y="160" fill="#64748b" fontSize="8">
                      x/c = 0.5
                    </text>
                    <text x="320" y="160" fill="#64748b" fontSize="8">
                      1.0 (TE)
                    </text>
                  </svg>

                  {/* Curve Legend */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "center",
                      gap: "14px",
                      marginTop: "4px",
                      fontSize: "0.68rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                      <span style={{ width: "12px", height: "2px", background: "#38bdf8" }} />
                      <span style={{ color: "#38bdf8" }}>Upper Suction Surface</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                      <span style={{ width: "12px", height: "2px", background: "#f59e0b", borderTop: "1px dashed #f59e0b" }} />
                      <span style={{ color: "#f59e0b" }}>Lower Pressure Surface</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Mesh Statistics Footer */}
              {surfaceData && (
                <div
                  style={{
                    borderTop: "1px solid #1f2937",
                    marginTop: "10px",
                    paddingTop: "8px",
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.66rem",
                    color: "#64748b",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  <span>Nodes: {surfaceData.mesh_stats.nodes_total}</span>
                  <span>Faces: {surfaceData.mesh_stats.triangles_count}</span>
                  <span>AR: {surfaceData.mesh_stats.aspect_ratio}</span>
                  <span>Sweep: {surfaceData.mesh_stats.sweep_deg}°</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
