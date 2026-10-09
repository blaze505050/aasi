"use client";

import React, { useMemo } from "react";

interface AirfoilVisualizerProps {
  geometry: string;
  alphaDeg: number;
  reynolds?: number;
  mach?: number;
}

/**
 * Computes NACA 4-digit coordinates (Upper & Lower surfaces + Camber line)
 */
function computeNacaCoordinates(geometryName: string, numPoints: number = 60) {
  // Default to NACA 0012
  let m = 0.0;    // Max camber
  let p = 0.0;    // Location of max camber
  let t = 0.12;   // Max thickness as fraction of chord

  const match = geometryName.match(/NACA\s*([0-9]{4})/i);
  if (match) {
    const digits = match[1];
    m = parseInt(digits[0], 10) / 100.0;
    p = parseInt(digits[1], 10) / 10.0;
    t = parseInt(digits.slice(2), 10) / 100.0;
  }

  const upper: [number, number][] = [];
  const lower: [number, number][] = [];
  const camber: [number, number][] = [];

  for (let i = 0; i <= numPoints; i++) {
    // Cosine spacing for higher resolution at leading and trailing edges
    const beta = (Math.PI * i) / numPoints;
    const x = 0.5 * (1 - Math.cos(beta));

    // Thickness distribution
    const yt =
      5 *
      t *
      (0.2969 * Math.sqrt(Math.max(x, 0)) -
        0.126 * x -
        0.3516 * Math.pow(x, 2) +
        0.2843 * Math.pow(x, 3) -
        0.1015 * Math.pow(x, 4));

    // Camber line and slope
    let yc = 0.0;
    let dyc_dx = 0.0;

    if (p > 0 && m > 0) {
      if (x < p) {
        yc = (m / Math.pow(p, 2)) * (2 * p * x - Math.pow(x, 2));
        dyc_dx = ((2 * m) / Math.pow(p, 2)) * (p - x);
      } else {
        yc = (m / Math.pow(1 - p, 2)) * (1 - 2 * p + 2 * p * x - Math.pow(x, 2));
        dyc_dx = ((2 * m) / Math.pow(1 - p, 2)) * (p - x);
      }
    }

    const theta = Math.atan(dyc_dx);

    const xu = x - yt * Math.sin(theta);
    const yu = yc + yt * Math.cos(theta);

    const xl = x + yt * Math.sin(theta);
    const yl = yc - yt * Math.cos(theta);

    upper.push([xu, yu]);
    lower.push([xl, yl]);
    camber.push([x, yc]);
  }

  return { upper, lower, camber, t, m, p };
}

export const AirfoilVisualizer: React.FC<AirfoilVisualizerProps> = ({
  geometry,
  alphaDeg,
  reynolds = 3e6,
  mach = 0.15,
}) => {
  const { upper, lower, camber, t, m } = useMemo(
    () => computeNacaCoordinates(geometry),
    [geometry]
  );

  // SVG dimensions & coordinate transforms
  const svgWidth = 560;
  const svgHeight = 220;
  const paddingX = 70;
  const paddingY = 40;
  const chordLength = svgWidth - 2 * paddingX;
  const originX = paddingX;
  const originY = svgHeight / 2;

  // Scale factor: chord = chordLength px, 1 chord unit = chordLength
  const scale = chordLength;

  // Rotate coordinates around aerodynamic center (quarter-chord x=0.25, y=0)
  // Standard aerodynamic pitch: positive alpha pitches leading edge UP, trailing edge DOWN
  const rad = (-alphaDeg * Math.PI) / 180;
  const cosA = Math.cos(rad);
  const sinA = Math.sin(rad);
  const pivotX = 0.25;
  const pivotY = 0.0;

  const transformPoint = (x: number, y: number): [number, number] => {
    // Translate relative to pivot, rotate, translate back, scale
    const dx = x - pivotX;
    const dy = y - pivotY;
    const rx = dx * cosA - dy * sinA + pivotX;
    const ry = dx * sinA + dy * cosA + pivotY;

    // In SVG, y axis points DOWN, so invert ry
    const px = originX + rx * scale;
    const py = originY - ry * scale;
    return [px, py];
  };

  // Construct closed contour path for airfoil: Upper leading->trailing, then Lower trailing->leading
  const upperPts = upper.map(([x, y]) => transformPoint(x, y));
  const lowerPts = lower.map(([x, y]) => transformPoint(x, y)).reverse();
  const allContour = [...upperPts, ...lowerPts];

  const contourPath =
    allContour.length > 0
      ? `M ${allContour[0][0].toFixed(2)},${allContour[0][1].toFixed(2)} ` +
        allContour
          .slice(1)
          .map(([px, py]) => `L ${px.toFixed(2)},${py.toFixed(2)}`)
          .join(" ") +
        " Z"
      : "";

  // Camber line path
  const camberPts = camber.map(([x, y]) => transformPoint(x, y));
  const camberPath =
    camberPts.length > 0
      ? `M ${camberPts[0][0].toFixed(2)},${camberPts[0][1].toFixed(2)} ` +
        camberPts
          .slice(1)
          .map(([px, py]) => `L ${px.toFixed(2)},${py.toFixed(2)}`)
          .join(" ")
      : "";

  // Chord line from rotated LE to TE
  const lePt = transformPoint(0, 0);
  const tePt = transformPoint(1, 0);
  const acPt = transformPoint(0.25, 0);

  // Incoming freestream velocity vector arrow
  const vectorLength = 48;
  const vectorStartX = originX - 35;
  const vectorStartY = originY;
  const vectorEndX = vectorStartX + vectorLength;
  const vectorEndY = vectorStartY;

  return (
    <div className="airfoil-visualizer-card">
      <div className="airfoil-visualizer-header">
        <div className="airfoil-visualizer-title-group">
          <div className="airfoil-visualizer-tag">GEOMETRIC PROFILER</div>
          <div className="airfoil-visualizer-name">
            {geometry.toUpperCase() || "NACA 0012"}
            <span className="airfoil-visualizer-alpha">
              α = {alphaDeg.toFixed(1)}°
            </span>
          </div>
        </div>

        <div className="airfoil-visualizer-meta-chips">
          <span className="meta-chip">
            <span className="meta-chip-label">Thickness t/c:</span>
            <span className="meta-chip-val">{(t * 100).toFixed(0)}%</span>
          </span>
          <span className="meta-chip">
            <span className="meta-chip-label">Camber m/c:</span>
            <span className="meta-chip-val">{(m * 100).toFixed(1)}%</span>
          </span>
          <span className="meta-chip">
            <span className="meta-chip-label">Reynolds:</span>
            <span className="meta-chip-val">{reynolds.toExponential(1)}</span>
          </span>
          <span className="meta-chip">
            <span className="meta-chip-label">Mach:</span>
            <span className="meta-chip-val">{mach.toFixed(2)}</span>
          </span>
        </div>
      </div>

      <div className="airfoil-svg-container">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="airfoil-svg"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <linearGradient id="airfoilSkinGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0077ED" stopOpacity="0.28" />
              <stop offset="50%" stopColor="#00C7BE" stopOpacity="0.16" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0.22" />
            </linearGradient>

            <linearGradient id="airfoilBorderGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#64D2FF" stopOpacity="0.9" />
              <stop offset="50%" stopColor="#30D158" stopOpacity="0.75" />
              <stop offset="100%" stopColor="#0077ED" stopOpacity="0.85" />
            </linearGradient>

            {/* Velocity arrow marker */}
            <marker
              id="velocityArrow"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#64D2FF" opacity="0.85" />
            </marker>

            {/* Subtle grid pattern */}
            <pattern id="airfoilGrid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                stroke="rgba(255, 255, 255, 0.035)"
                strokeWidth="1"
              />
            </pattern>
          </defs>

          {/* Background Grid */}
          <rect width={svgWidth} height={svgHeight} fill="url(#airfoilGrid)" />

          {/* Reference Zero Horizontal Line */}
          <line
            x1={paddingX - 20}
            y1={originY}
            x2={svgWidth - paddingX + 20}
            y2={originY}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeDasharray="3 3"
            strokeWidth="1"
          />

          {/* Rotated Chord Reference Line */}
          <line
            x1={lePt[0]}
            y1={lePt[1]}
            x2={tePt[0]}
            y2={tePt[1]}
            stroke="rgba(255, 255, 255, 0.22)"
            strokeDasharray="4 4"
            strokeWidth="1.2"
          />

          {/* Mean Camber Line */}
          {m > 0 && (
            <path
              d={camberPath}
              fill="none"
              stroke="rgba(255, 159, 10, 0.65)"
              strokeWidth="1.5"
              strokeDasharray="2 2"
            />
          )}

          {/* Airfoil Cross-Section Contour */}
          <path
            d={contourPath}
            fill="url(#airfoilSkinGradient)"
            stroke="url(#airfoilBorderGradient)"
            strokeWidth="1.8"
            className="airfoil-contour"
          />

          {/* Aerodynamic Center Indicator (c/4) */}
          <circle
            cx={acPt[0]}
            cy={acPt[1]}
            r="3.5"
            fill="#FFD60A"
            stroke="#1C1C1E"
            strokeWidth="1.5"
          />
          <text
            x={acPt[0]}
            y={acPt[1] - 8}
            fill="#FFD60A"
            fontSize="8.5"
            fontFamily="var(--font-mono)"
            textAnchor="middle"
            opacity="0.85"
          >
            c/4
          </text>

          {/* Freestream Incoming Velocity Vector */}
          <line
            x1={vectorStartX}
            y1={vectorStartY}
            x2={vectorEndX}
            y2={vectorEndY}
            stroke="#64D2FF"
            strokeWidth="1.5"
            markerEnd="url(#velocityArrow)"
          />
          <text
            x={vectorStartX + 20}
            y={vectorStartY - 7}
            fill="#64D2FF"
            fontSize="9"
            fontFamily="var(--font-mono)"
            fontWeight="600"
            letterSpacing="0.05em"
          >
            V_∞
          </text>
        </svg>
      </div>

      <div className="airfoil-visualizer-footer">
        <span>Flow angle: <strong style={{ color: alphaDeg >= 12 ? "var(--status-amber)" : "var(--accent-cyan)" }}>{alphaDeg > 0 ? `+${alphaDeg.toFixed(1)}°` : `${alphaDeg.toFixed(1)}°`}</strong></span>
        <span>Theoretical 2π lift slope: <strong style={{ color: "#a5f3fc" }}>dC_L/dα ≈ 0.110 deg⁻¹</strong></span>
        <span>Boundary layer: <strong style={{ color: "#a7f3d0" }}>{alphaDeg >= 15 ? "Severe Post-Stall Separation" : alphaDeg >= 10 ? "Adverse Pressure Detachment Zone" : "Attached Turbulent Flow"}</strong></span>
      </div>
    </div>
  );
};
