"use client";

import React, { useState, useMemo } from "react";
import { Wind, Activity, Eye, Sliders, ChevronDown, ChevronUp } from "lucide-react";

interface AerodynamicFlowfieldVisualizerProps {
  geometry: string;
  alphaDeg: number;
  reynolds?: number;
  mach?: number;
}

export const AerodynamicFlowfieldVisualizer: React.FC<AerodynamicFlowfieldVisualizerProps> = ({
  geometry,
  alphaDeg,
  reynolds = 3e6,
  mach = 0.15,
}) => {
  const [showCpDistribution, setShowCpDistribution] = useState(true);
  const [streamlineDensity, setStreamlineDensity] = useState<"NORMAL" | "HIGH">("NORMAL");

  // Determine geometry parameters
  const { camber, thickness, name } = useMemo(() => {
    let c = 0.0;
    let t = 0.12;
    const match = geometry.match(/NACA\s*([0-9]{4})/i);
    if (match) {
      const d = match[1];
      c = parseInt(d[0], 10) / 100.0;
      t = parseInt(d.slice(2), 10) / 100.0;
    } else if (geometry.toUpperCase().includes("2822")) {
      c = 0.014;
      t = 0.121;
    } else if (geometry.toUpperCase().includes("CLARK")) {
      c = 0.034;
      t = 0.117;
    }
    return { camber: c, thickness: t, name: geometry.toUpperCase() || "NACA 0012" };
  }, [geometry]);

  // Is the airfoil experiencing stall / flow detachment?
  const stallAngle = 13.0 + 15.0 * thickness;
  const isStalled = alphaDeg > stallAngle;
  const isNearStall = alphaDeg > stallAngle - 2.5 && !isStalled;

  // SVG dimensions
  const svgWidth = 720;
  const svgHeight = 260;
  const originX = 140;
  const originY = 130;
  const chordPx = 360;

  // Angle in radians (for SVG rotation)
  const rad = (-alphaDeg * Math.PI) / 180;
  const cosA = Math.cos(rad);
  const sinA = Math.sin(rad);

  const rotatePoint = (xFrac: number, yFrac: number): [number, number] => {
    const px = xFrac - 0.25;
    const py = yFrac;
    const rx = px * cosA - py * sinA + 0.25;
    const ry = px * sinA + py * cosA;
    return [originX + rx * chordPx, originY - ry * chordPx];
  };

  // Generate 40 airfoil surface points
  const { upperSurface, lowerSurface, contourSvgPath } = useMemo(() => {
    const numPts = 36;
    const up: [number, number][] = [];
    const low: [number, number][] = [];

    for (let i = 0; i <= numPts; i++) {
      const beta = (Math.PI * i) / numPts;
      const x = 0.5 * (1 - Math.cos(beta));
      const yt =
        5 *
        thickness *
        (0.2969 * Math.sqrt(Math.max(x, 0)) -
          0.126 * x -
          0.3516 * Math.pow(x, 2) +
          0.2843 * Math.pow(x, 3) -
          0.1015 * Math.pow(x, 4));

      let yc = 0.0;
      if (camber > 0) {
        yc = camber * (1 - Math.pow(x - 0.4, 2));
      }

      up.push(rotatePoint(x, yc + yt));
      low.push(rotatePoint(x, yc - yt));
    }

    const fullContour = [...up, ...[...low].reverse()];
    const pathStr =
      fullContour.length > 0
        ? `M ${fullContour[0][0].toFixed(1)},${fullContour[0][1].toFixed(1)} ` +
          fullContour.slice(1).map(([px, py]) => `L ${px.toFixed(1)},${py.toFixed(1)}`).join(" ") +
          " Z"
        : "";

    return { upperSurface: up, lowerSurface: low, contourSvgPath: pathStr };
  }, [camber, thickness, alphaDeg]);

  // Compute streamlines
  const streamlines = useMemo(() => {
    const lines: Array<{ path: string; color: string; isSeparated: boolean }> = [];
    const yOffsets = streamlineDensity === "HIGH"
      ? [-60, -45, -30, -18, -8, 8, 20, 35, 50, 65]
      : [-50, -30, -15, 15, 30, 50];

    yOffsets.forEach((yOff, idx) => {
      const isUpper = yOff < 0;
      let path = `M 30,${originY + yOff} `;

      if (isUpper) {
        // Upper stream curve over suction side
        const leX = originX - 10;
        const crestX = originX + chordPx * 0.35;
        const crestY = originY + yOff - (alphaDeg > 0 ? alphaDeg * 2.8 : 0);
        const teX = originX + chordPx + 40;
        const teY = originY + yOff + (alphaDeg * 1.5);

        if (isStalled) {
          // Turbulent vortex curl behind crest
          path += `C ${leX},${originY + yOff} ${crestX - 30},${crestY - 15} ${crestX},${crestY} `;
          path += `C ${crestX + 40},${crestY - 20} ${crestX + 70},${crestY + 30} ${crestX + 110},${crestY + 10} `;
          path += `S ${teX},${teY + 25} ${svgWidth - 20},${teY + 35}`;
          lines.push({ path, color: "#ff453a", isSeparated: true });
        } else {
          // Attached smooth streamline
          path += `C ${leX},${originY + yOff} ${crestX - 20},${crestY} ${crestX},${crestY} `;
          path += `C ${crestX + 60},${crestY + 5} ${teX - 20},${teY} ${svgWidth - 20},${teY}`;
          lines.push({ path, color: isNearStall ? "#ffd60a" : "#64d2ff", isSeparated: false });
        }
      } else {
        // Lower compression stream
        const leX = originX;
        const bellyX = originX + chordPx * 0.4;
        const bellyY = originY + yOff + (alphaDeg > 0 ? alphaDeg * 1.2 : 0);
        const teX = originX + chordPx;
        const teY = originY + yOff + (alphaDeg * 1.8);

        path += `C ${leX},${originY + yOff} ${bellyX - 30},${bellyY} ${bellyX},${bellyY} `;
        path += `C ${bellyX + 50},${bellyY} ${teX},${teY} ${svgWidth - 20},${teY + 10}`;
        lines.push({ path, color: "#30d158", isSeparated: false });
      }
    });

    return lines;
  }, [alphaDeg, isStalled, isNearStall, streamlineDensity]);

  // Chordwise Pressure Coefficient distribution curve data (Cp vs x/c)
  const cpCurveData = useMemo(() => {
    const pts: Array<{ xFrac: number; cpUpper: number; cpLower: number }> = [];
    const suctionPeak = -(0.5 + 0.35 * Math.max(0, alphaDeg));

    for (let i = 0; i <= 20; i++) {
      const xf = i / 20;
      // Upper suction peak at leading edge tapering to 0 at TE
      let cpu = suctionPeak * Math.exp(-xf * 4.5) + (1 - xf) * -0.15;
      if (isStalled && xf > 0.4) {
        // Plateau in separated zone
        cpu = -0.4;
      }
      // Lower compression positive near stagnation point
      const cpl = 0.8 * Math.exp(-xf * 6.0) + (1 - xf) * 0.12;

      pts.push({ xFrac: xf, cpUpper: Number(cpu.toFixed(3)), cpLower: Number(cpl.toFixed(3)) });
    }
    return pts;
  }, [alphaDeg, isStalled]);

  return (
    <div
      style={{
        background: "linear-gradient(180deg, rgba(17, 24, 39, 0.75), rgba(11, 16, 28, 0.85))",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "16px",
        padding: "20px",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.35)",
        backdropFilter: "blur(20px)",
      }}
    >
      {/* Top Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "14px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "rgba(0, 210, 255, 0.18)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#64d2ff",
            }}
          >
            <Wind size={18} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
                Interactive Aerodynamic Flowfield &amp; Pressure Profiler
              </span>
              <span
                style={{
                  padding: "2px 7px",
                  borderRadius: "5px",
                  background: isStalled
                    ? "rgba(255, 69, 58, 0.2)"
                    : isNearStall
                    ? "rgba(255, 214, 10, 0.2)"
                    : "rgba(48, 209, 88, 0.2)",
                  color: isStalled ? "#ff453a" : isNearStall ? "#ffd60a" : "#30d158",
                  fontSize: "0.68rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                }}
              >
                {isStalled ? "FLOW SEPARATED (STALL)" : isNearStall ? "TRANSITION / HIGH α" : "ATTACHED LAMINAR"}
              </span>
            </div>
            <div style={{ fontSize: "0.76rem", color: "#94a3b8" }}>
              {name} • Angle of Attack α = {alphaDeg.toFixed(1)}° • t/c = {(thickness * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            onClick={() => setStreamlineDensity(streamlineDensity === "NORMAL" ? "HIGH" : "NORMAL")}
            style={{
              padding: "5px 10px",
              borderRadius: "6px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#cbd5e1",
              fontSize: "0.72rem",
              cursor: "pointer",
            }}
          >
            Density: {streamlineDensity}
          </button>

          <button
            onClick={() => setShowCpDistribution(!showCpDistribution)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              padding: "5px 10px",
              borderRadius: "6px",
              background: showCpDistribution ? "rgba(0, 210, 255, 0.2)" : "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(0, 210, 255, 0.3)",
              color: showCpDistribution ? "#64d2ff" : "#cbd5e1",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <Activity size={13} />
            <span>Cp Distribution</span>
            {showCpDistribution ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>
      </div>

      {/* Flowfield SVG Canvas */}
      <div
        style={{
          width: "100%",
          borderRadius: "12px",
          background: "radial-gradient(ellipse at 50% 50%, rgba(13, 20, 36, 0.95), rgba(7, 10, 18, 0.98))",
          border: "1px solid rgba(255, 255, 255, 0.06)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", height: "auto", display: "block" }}
        >
          <defs>
            {/* Pressure Contour Fill Gradient */}
            <linearGradient id="suctionPressureGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0284c7" stopOpacity="0.85" />
              <stop offset="30%" stopColor="#0077ed" stopOpacity="0.75" />
              <stop offset="70%" stopColor="#00c7be" stopOpacity="0.65" />
              <stop offset="100%" stopColor="#30d158" stopOpacity="0.55" />
            </linearGradient>

            {/* Turbulent separation marker */}
            <radialGradient id="recirculationGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ff453a" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#ff453a" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Streamlines */}
          {streamlines.map((st, idx) => (
            <path
              key={`st-${idx}`}
              d={st.path}
              fill="none"
              stroke={st.color}
              strokeWidth={st.isSeparated ? "2" : "1.2"}
              strokeDasharray={st.isSeparated ? "4 3" : undefined}
              opacity="0.65"
            />
          ))}

          {/* Separation Bubble if Stalled */}
          {isStalled && (
            <ellipse
              cx={originX + chordPx * 0.7}
              cy={originY - 35}
              rx="60"
              ry="30"
              fill="url(#recirculationGlow)"
            />
          )}

          {/* Airfoil Skin Contour with Dynamic Pressure Surface Coloring */}
          <path
            d={contourSvgPath}
            fill="url(#suctionPressureGrad)"
            stroke="#64d2ff"
            strokeWidth="2"
            style={{
              filter: "drop-shadow(0 4px 14px rgba(0, 210, 255, 0.35))",
            }}
          />

          {/* Stagnation Point Marker (Red dot at LE) */}
          <circle
            cx={originX - 2}
            cy={originY + (alphaDeg * 0.8)}
            r="4.5"
            fill="#ff453a"
            stroke="#ffffff"
            strokeWidth="1.5"
            style={{ filter: "drop-shadow(0 0 6px #ff453a)" }}
          />

          {/* Freestream Incoming Velocity Vector */}
          <line
            x1="35"
            y1={originY}
            x2="95"
            y2={originY}
            stroke="#64d2ff"
            strokeWidth="2"
          />
          <polygon
            points={`95,${originY - 4} 103,${originY} 95,${originY + 4}`}
            fill="#64d2ff"
          />
          <text
            x="40"
            y={originY - 8}
            fill="#64d2ff"
            fontSize="10"
            fontFamily="var(--font-mono)"
            fontWeight="bold"
          >
            V∞ = {(mach * 340).toFixed(0)} m/s
          </text>
        </svg>
      </div>

      {/* Chordwise Pressure Coefficient Cp(x/c) Plot */}
      {showCpDistribution && (
        <div
          style={{
            marginTop: "14px",
            padding: "14px",
            background: "rgba(10, 14, 24, 0.6)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
            borderRadius: "10px",
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
            <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#f8fafc" }}>
              Chordwise Pressure Coefficient Distribution Cp(x/c)
            </span>
            <div style={{ display: "flex", gap: "12px", fontSize: "0.7rem", fontFamily: "var(--font-mono)" }}>
              <span style={{ color: "#38bdf8" }}>— Upper Surface (Suction)</span>
              <span style={{ color: "#30d158" }}>— Lower Surface (Pressure)</span>
            </div>
          </div>

          {/* Micro SVG for Cp vs x/c */}
          <svg viewBox="0 0 640 100" style={{ width: "100%", height: "auto" }}>
            {/* Zero axis */}
            <line x1="40" y1="40" x2="600" y2="40" stroke="rgba(255, 255, 255, 0.15)" />

            {/* Upper Surface Cp path (Inverted aerodynamic convention: suction -Cp UP) */}
            <path
              d={
                "M " +
                cpCurveData
                  .map((p) => {
                    const px = 40 + p.xFrac * 560;
                    const py = 40 + p.cpUpper * 25; // Negative Cp goes UP
                    return `${px.toFixed(1)},${py.toFixed(1)}`;
                  })
                  .join(" L ")
              }
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2"
            />

            {/* Lower Surface Cp path */}
            <path
              d={
                "M " +
                cpCurveData
                  .map((p) => {
                    const px = 40 + p.xFrac * 560;
                    const py = 40 + p.cpLower * 25;
                    return `${px.toFixed(1)},${py.toFixed(1)}`;
                  })
                  .join(" L ")
              }
              fill="none"
              stroke="#30d158"
              strokeWidth="2"
            />

            {/* Labels */}
            <text x="40" y="95" fill="#64748b" fontSize="9" fontFamily="var(--font-mono)">
              x/c = 0.0 (LE)
            </text>
            <text x="560" y="95" fill="#64748b" fontSize="9" fontFamily="var(--font-mono)">
              x/c = 1.0 (TE)
            </text>
            <text x="10" y="44" fill="#94a3b8" fontSize="9" fontFamily="var(--font-mono)">
              Cp=0
            </text>
            <text x="10" y="16" fill="#38bdf8" fontSize="9" fontFamily="var(--font-mono)">
              -Cp
            </text>
          </svg>
        </div>
      )}
    </div>
  );
};
