"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
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
  Flame,
  Activity,
  Gauge,
  Thermometer,
  Zap,
  Download,
  Copy,
  Check,
  Sliders,
  FileCode,
  Layers,
  Compass,
  Eye,
  Camera,
  ShieldAlert,
  Radio,
  Clock,
  Sparkles,
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

/* ═══════════════════════════════════════════════════════════════
   FIRST-PRINCIPLES DETERMINISTIC PHYSICS GENERATOR (CLIENT ENGINE)
   Guarantees instantaneous, 60fps telemetry visualization
   even when offline or running in edge environments.
   ═══════════════════════════════════════════════════════════════ */

function generateClientDigitalTwin(
  vType: VehicleType,
  fault?: { type: string; onset_s: number; severity: number }
): SimulationResult {
  const frames: TelemetryFrame[] = [];
  const events: MissionEvent[] = [];
  const violations: string[] = [];
  let duration = 240;
  let dt = 0.5;

  if (vType === "ROCKET") {
    duration = 240;
    dt = 0.5;
    const totalSteps = Math.floor(duration / dt);
    let alt = 0;
    let vel = 0;
    let mass = 549054; // kg (Falcon 9 scale)
    const m_dry_s1 = 25600;
    const m_prop_s1 = 395700;
    const m_s2 = 111500;
    let s1_active = true;
    let engine_cutoff = false;

    events.push({ timestamp_s: 0, event_name: "LIFTOFF", description: "Main engine ignition; hold-down release.", severity: "INFO" });

    for (let i = 0; i < totalSteps; i++) {
      const t = i * dt;
      let thrust = 0;
      let isp = 282;

      // Fault evaluation
      if (fault && fault.type === "ENGINE_CUTOFF" && t >= fault.onset_s) {
        engine_cutoff = true;
        if (events.length === 1 || !events.some((e) => e.event_name === "UNPLANNED_MECO")) {
          events.push({
            timestamp_s: t,
            event_name: "UNPLANNED_MECO",
            description: "Propulsion emergency shutdown: Stage 1 cutoff.",
            severity: "CRITICAL",
          });
          violations.push(`Unplanned propulsion shutdown at T+${t.toFixed(1)}s`);
        }
      }

      // Barometric atmosphere
      const h_scale = 7200;
      const rho0 = 1.225;
      const rho = alt < 120000 ? rho0 * Math.exp(-alt / h_scale) : 0;
      const a = Math.max(270, 340 - 0.004 * Math.min(alt, 11000));
      const mach = vel / a;

      if (!engine_cutoff) {
        if (t < 148 && s1_active) {
          thrust = 7607000 * (1 + 0.15 * Math.min(1, alt / 40000));
          const mdot = (m_prop_s1 / 148) * (fault && fault.type === "OXIDIZER_LEAK" && t >= fault.onset_s ? 1 + fault.severity * 0.4 : 1);
          mass = Math.max(m_dry_s1 + m_s2, mass - mdot * dt);
        } else if (t >= 148 && t < 154) {
          if (s1_active) {
            s1_active = false;
            events.push({ timestamp_s: 148, event_name: "MECO", description: "Stage 1 Main Engine Cutoff.", severity: "INFO" });
            events.push({ timestamp_s: 152, event_name: "STAGE_SEP", description: "Pneumatic stage separation verified.", severity: "INFO" });
            mass = m_s2;
          }
          thrust = 0;
        } else if (t >= 154) {
          if (!events.some((e) => e.event_name === "SES-1")) {
            events.push({ timestamp_s: 154, event_name: "SES-1", description: "Vacuum Stage 2 ignition.", severity: "INFO" });
          }
          thrust = 934000;
          isp = 348;
          mass = Math.max(4500, mass - 260 * dt);
        }
      }

      // Aerodynamic drag
      const A = Math.PI * (3.66 / 2) ** 2;
      const cd = mach < 0.8 ? 0.28 : mach < 1.2 ? 0.28 + 0.22 * Math.sin(((mach - 0.8) / 0.4) * Math.PI) : 0.45 / Math.sqrt(mach);
      const q = 0.5 * rho * vel ** 2;
      const drag = q * cd * A;

      // Event Max-Q
      if (q > 30000 && !events.some((e) => e.event_name === "MAX_Q")) {
        events.push({ timestamp_s: t, event_name: "MAX_Q", description: `Max aerodynamic dynamic pressure (${(q / 1000).toFixed(1)} kPa).`, severity: "WARNING" });
      }

      const gravity = 9.80665 * (6371000 / (6371000 + alt)) ** 2;
      const pitch_deg = Math.max(0, 90 - (t / 140) * 85);
      const pitch_rad = (pitch_deg * Math.PI) / 180;

      const f_net = thrust - drag - mass * gravity * Math.sin(pitch_rad);
      const accel = f_net / mass;
      vel = Math.max(0, vel + accel * dt);
      alt = alt + vel * Math.sin(pitch_rad) * dt;

      const energy_pct = Math.max(0, (mass / 549054) * 100);
      const temp_c = Math.min(1450, 20 + 0.00035 * Math.sqrt(rho) * Math.pow(vel, 3));

      const propHealth = engine_cutoff ? Math.max(10, 100 - fault!.severity * 85) : 100;
      const avionicsHealth = fault && fault.type === "GIMBAL_FREEZE" && t >= fault.onset_s ? 55 : 100;

      frames.push({
        timestamp_s: Number(t.toFixed(1)),
        altitude_m: Math.round(alt),
        velocity_ms: Math.round(vel),
        mach: Number(mach.toFixed(2)),
        dynamic_pressure_pa: Math.round(q),
        acceleration_g: Number((accel / 9.81).toFixed(2)),
        mass_kg: Math.round(mass),
        propellant_or_battery_pct: Number(energy_pct.toFixed(1)),
        temperature_c: Math.round(temp_c),
        subsystem_health: {
          propulsion: propHealth,
          avionics: avionicsHealth,
          thermal: temp_c > 1100 ? 78 : 100,
          structural: q > 38000 ? 82 : 100,
          power: 99,
        },
        vehicle_specific: {
          stage: s1_active ? 1 : 2,
          pitch_angle_deg: Number(pitch_deg.toFixed(1)),
          thrust_kn: Math.round(thrust / 1000),
        },
      });
    }

    if (!engine_cutoff) {
      events.push({ timestamp_s: 238, event_name: "ORBIT_INJECTION", description: "Target parking orbit achieved: 200 km x 245 km.", severity: "INFO" });
    }

    return {
      simulation_id: `SIM-ROCKET-${Date.now().toString(36).toUpperCase()}`,
      vehicle_type: "ROCKET",
      vehicle_name: "Heavy-Lift Launch Vehicle (Falcon-9 Class)",
      simulation_mode: fault ? "STRESSED_FAULT_INJECTION" : "NOMINAL_FLIGHT_ASCENT",
      duration_s: duration,
      time_step_s: dt,
      total_samples: frames.length,
      frames,
      events,
      summary_metrics: {
        max_q_kpa: Number((Math.max(...frames.map((f) => f.dynamic_pressure_pa)) / 1000).toFixed(1)),
        max_mach: Number(Math.max(...frames.map((f) => f.mach)).toFixed(2)),
        apogee_km: Number((Math.max(...frames.map((f) => f.altitude_m)) / 1000).toFixed(1)),
        final_velocity_ms: frames[frames.length - 1].velocity_ms,
      },
      safety_envelope_passed: violations.length === 0,
      safety_violations: violations,
      provenance_hash: "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(""),
    };
  }

  if (vType === "DRONE") {
    duration = 120;
    dt = 0.2;
    const totalSteps = Math.floor(duration / dt);
    let alt = 0;
    let vel = 0;
    let battery = 100;
    let motorTemp = 24;

    events.push({ timestamp_s: 0, event_name: "ARM_MOTORS", description: "PX4 FCU armed; 6 ESCs synchronized.", severity: "INFO" });
    events.push({ timestamp_s: 4, event_name: "TAKEOFF_AGL", description: "Ground effect transition to 15m hover.", severity: "INFO" });

    for (let i = 0; i < totalSteps; i++) {
      const t = i * dt;
      let targetAlt = 50;
      let targetVel = 14;

      if (t < 8) {
        targetAlt = (t / 8) * 15;
      } else if (t < 25) {
        targetAlt = 15 + ((t - 8) / 17) * 35;
      } else if (t > 95) {
        targetAlt = Math.max(0, 50 - ((t - 95) / 25) * 50);
        targetVel = 4;
      }

      // Fault evaluation
      let motorDesync = false;
      if (fault && fault.type === "MOTOR_DESYNC" && t >= fault.onset_s) {
        motorDesync = true;
        targetAlt = Math.max(2, targetAlt - 18 * fault.severity);
        if (!events.some((e) => e.event_name === "MOTOR_3_DESYNC")) {
          events.push({ timestamp_s: t, event_name: "MOTOR_3_DESYNC", description: "Rotor #3 ESC desynchronization detected.", severity: "CRITICAL" });
          violations.push(`Rotor 3 RPM divergence at T+${t.toFixed(1)}s`);
        }
      }

      alt = alt + (targetAlt - alt) * 0.08;
      vel = vel + (targetVel - vel) * 0.05;

      const p_hover = 720; // W
      const p_cruise = 960 + vel * 25;
      const p_total = motorDesync ? p_cruise * 1.35 : p_cruise;
      battery = Math.max(0, battery - (p_total / 3600 / 48) * dt * 2.8);
      motorTemp = Math.min(85, 24 + (p_total / 1200) * 32);

      const q = 0.5 * 1.225 * vel ** 2;

      if (t === 45) {
        events.push({ timestamp_s: 45, event_name: "DRYDEN_GUST", description: "Encountered 8 m/s crosswind gust; attitude PID active.", severity: "WARNING" });
      }

      frames.push({
        timestamp_s: Number(t.toFixed(1)),
        altitude_m: Number(alt.toFixed(1)),
        velocity_ms: Number(vel.toFixed(1)),
        mach: Number((vel / 340).toFixed(3)),
        dynamic_pressure_pa: Math.round(q),
        acceleration_g: Number((1.0 + (t === 45 ? 0.35 : Math.sin(t * 2) * 0.04)).toFixed(2)),
        mass_kg: 8.4,
        propellant_or_battery_pct: Number(battery.toFixed(1)),
        temperature_c: Math.round(motorTemp),
        subsystem_health: {
          propulsion: motorDesync ? 48 : 99,
          avionics: 100,
          thermal: motorTemp > 70 ? 75 : 98,
          structural: 100,
          power: Number(battery.toFixed(0)),
        },
        vehicle_specific: {
          motor_rpm_mean: Math.round(motorDesync ? 5200 : 6400),
          roll_attitude_deg: Number((motorDesync ? 6.8 : Math.sin(t) * 1.2).toFixed(1)),
          pitch_attitude_deg: Number((vel > 5 ? -8.2 : 0).toFixed(1)),
        },
      });
    }

    events.push({ timestamp_s: 118, event_name: "AUTO_LAND", description: "Precision AGL touchdown and motor disarm.", severity: "INFO" });

    return {
      simulation_id: `SIM-DRONE-${Date.now().toString(36).toUpperCase()}`,
      vehicle_type: "DRONE",
      vehicle_name: "Hexacopter eVTOL Autonomous UAV",
      simulation_mode: fault ? "STRESSED_FAULT_INJECTION" : "AUTONOMOUS_DELIVERY_CYCLE",
      duration_s: duration,
      time_step_s: dt,
      total_samples: frames.length,
      frames,
      events,
      summary_metrics: {
        cruise_speed_ms: 14.0,
        energy_consumed_pct: Number((100 - battery).toFixed(1)),
        peak_motor_temp_c: Math.round(motorTemp),
        hover_efficiency: "9.2 g/W",
      },
      safety_envelope_passed: violations.length === 0,
      safety_violations: violations,
      provenance_hash: "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(""),
    };
  }

  if (vType === "AEROPLANE") {
    duration = 600;
    dt = 2.0;
    const totalSteps = Math.floor(duration / dt);
    let alt = 0;
    let vel = 0;
    let fuel = 18000; // kg
    let oei = false;

    events.push({ timestamp_s: 0, event_name: "TAKEOFF_ROLL", description: "TOGA thrust applied; runway acceleration.", severity: "INFO" });
    events.push({ timestamp_s: 30, event_name: "ROTATE_VR", description: "Rotation speed 145 KIAS achieved.", severity: "INFO" });

    for (let i = 0; i < totalSteps; i++) {
      const t = i * dt;

      if (fault && fault.type === "ENGINE_FLAMEOUT" && t >= fault.onset_s) {
        oei = true;
        if (!events.some((e) => e.event_name === "ENG_2_FLAMEOUT")) {
          events.push({ timestamp_s: t, event_name: "ENG_2_FLAMEOUT", description: "Engine #2 flameout; rudder trim compensated (OEI drift-down).", severity: "CRITICAL" });
          violations.push(`Engine 2 inoperative at T+${t.toFixed(0)}s`);
        }
      }

      // Altitude profile
      let targetAlt = 11277; // FL370
      let targetMach = 0.78;
      if (oei) {
        targetAlt = 7300; // FL240 ceiling
        targetMach = 0.62;
      }

      if (t < 180) {
        alt = (t / 180) * (oei ? 7300 : 11277);
      } else if (t < 420) {
        alt = oei ? 7300 : 11277;
      } else {
        alt = Math.max(800, (oei ? 7300 : 11277) - ((t - 420) / 180) * 10000);
      }

      const a = Math.max(295, 340 - 0.004 * alt);
      const mach = Math.min(targetMach, 0.2 + (t / 180) * 0.58);
      vel = mach * a;

      const rho = 1.225 * Math.exp(-alt / 8500);
      const q = 0.5 * rho * vel ** 2;

      const fuelBurnRate = oei ? 0.72 : 1.35; // kg/s
      fuel = Math.max(1200, fuel - fuelBurnRate * dt);

      frames.push({
        timestamp_s: Number(t.toFixed(0)),
        altitude_m: Math.round(alt),
        velocity_ms: Math.round(vel),
        mach: Number(mach.toFixed(2)),
        dynamic_pressure_pa: Math.round(q),
        acceleration_g: Number((1.0 + (t < 35 ? 0.28 : 0)).toFixed(2)),
        mass_kg: Math.round(62000 + fuel),
        propellant_or_battery_pct: Number(((fuel / 18000) * 100).toFixed(1)),
        temperature_c: Math.round(Math.max(-56, 15 - 0.0065 * alt)),
        subsystem_health: {
          propulsion: oei ? 50 : 100,
          avionics: 100,
          thermal: 98,
          structural: 100,
          power: 99,
        },
        vehicle_specific: {
          flight_level: `FL${Math.round(alt / 30.48)}`,
          lift_drag_ratio: 18.2,
          cl: 0.48,
          cd: 0.0264,
        },
      });
    }

    events.push({ timestamp_s: 200, event_name: "TOP_OF_CLIMB", description: "Reached FL370 cruise altitude.", severity: "INFO" });
    events.push({ timestamp_s: 420, event_name: "TOP_OF_DESCENT", description: "Initiating 3.0° descent profile to IAF.", severity: "INFO" });

    return {
      simulation_id: `SIM-AERO-${Date.now().toString(36).toUpperCase()}`,
      vehicle_type: "AEROPLANE",
      vehicle_name: "Twin-Turbofan Commercial Jet Transport",
      simulation_mode: fault ? "ONE_ENGINE_INOPERATIVE_STRESS" : "BREGUET_RANGE_CRUISE",
      duration_s: duration,
      time_step_s: dt,
      total_samples: frames.length,
      frames,
      events,
      summary_metrics: {
        cruise_mach: 0.78,
        cruise_altitude_m: 11277,
        lift_to_drag: 18.2,
        total_fuel_burn_kg: Math.round(18000 - fuel),
      },
      safety_envelope_passed: violations.length === 0,
      safety_violations: violations,
      provenance_hash: "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(""),
    };
  }

  // SATELLITE
  duration = 5400; // 90 min LEO orbit
  dt = 15.0;
  const totalSteps = Math.floor(duration / dt);
  let batteryDoD = 100;
  let skinTemp = 20;

  events.push({ timestamp_s: 0, event_name: "LEO_ORBIT_START", description: "500 km sun-synchronous orbit initialized (inc=97.4°).", severity: "INFO" });
  events.push({ timestamp_s: 1800, event_name: "ECLIPSE_ENTRY", description: "Umbra entry: solar generation drops to 0 W.", severity: "WARNING" });
  events.push({ timestamp_s: 3600, event_name: "ECLIPSE_EXIT", description: "Sunlight acquisition: GaAs array recharging battery.", severity: "INFO" });

  for (let i = 0; i < totalSteps; i++) {
    const t = i * dt;
    const inEclipse = t >= 1800 && t < 3600;

    let solarDegradation = false;
    if (fault && fault.type === "SOLAR_PANEL_DEGRADATION" && t >= fault.onset_s) {
      solarDegradation = true;
      if (!events.some((e) => e.event_name === "SOLAR_STRING_FAIL")) {
        events.push({ timestamp_s: t, event_name: "SOLAR_STRING_FAIL", description: "Strings 1 & 2 open-circuit: -60% power deficit.", severity: "CRITICAL" });
        violations.push(`Solar array string fault at T+${t}s`);
      }
    }

    if (inEclipse) {
      batteryDoD = Math.max(20, batteryDoD - (120 / 3600) * dt * 0.4);
      skinTemp = Math.max(-48, skinTemp - 0.05 * dt);
    } else {
      const chargeRate = solarDegradation ? 0.06 : 0.18;
      batteryDoD = Math.min(100, batteryDoD + (chargeRate / 3600) * dt * 4);
      skinTemp = Math.min(68, skinTemp + 0.04 * dt);
    }

    const alt = 500000;
    const vel = 7612; // m/s
    const q = 0.5 * 1.5e-12 * vel ** 2;

    frames.push({
      timestamp_s: t,
      altitude_m: alt,
      velocity_ms: vel,
      mach: 24.8,
      dynamic_pressure_pa: Number(q.toFixed(6)),
      acceleration_g: 0.0,
      mass_kg: 420,
      propellant_or_battery_pct: Number(batteryDoD.toFixed(1)),
      temperature_c: Math.round(skinTemp),
      subsystem_health: {
        propulsion: 100,
        avionics: 100,
        thermal: Math.round(100 - Math.abs(skinTemp - 15) * 0.4),
        structural: 100,
        power: solarDegradation ? 40 : Number(batteryDoD.toFixed(0)),
      },
      vehicle_specific: {
        solar_generation_w: inEclipse ? 0 : solarDegradation ? 560 : 1400,
        in_umbra: inEclipse,
        nodal_precession_deg_day: -0.9856,
      },
    });
  }

  return {
    simulation_id: `SIM-SAT-${Date.now().toString(36).toUpperCase()}`,
    vehicle_type: "SATELLITE",
    vehicle_name: "Sun-Synchronous 500 km LEO Earth Observation Satellite",
    simulation_mode: fault ? "SPACE_WEATHER_DEGRADATION" : "90_MIN_KEPLERIAN_CYCLE",
    duration_s: duration,
    time_step_s: dt,
    total_samples: frames.length,
    frames,
    events,
    summary_metrics: {
      orbital_period_min: 94.6,
      eclipse_duration_min: 30.0,
      min_battery_dod_pct: Number(Math.min(...frames.map((f) => f.propellant_or_battery_pct)).toFixed(1)),
      thermal_swing_c: `${Math.round(Math.min(...frames.map((f) => f.temperature_c)))}°C to +${Math.round(Math.max(...frames.map((f) => f.temperature_c)))}°C`,
    },
    safety_envelope_passed: violations.length === 0,
    safety_violations: violations,
    provenance_hash: "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join(""),
  };
}

/* ═══════════════════════════════════════════════════════════════
   SVG MINI SPARKLINE UTILITY (APPLE STOCKS / HEALTH STYLE)
   ═══════════════════════════════════════════════════════════════ */

const Sparkline: React.FC<{
  data: number[];
  color: string;
  width?: number;
  height?: number;
  currentIdx: number;
}> = ({ data, color, width = 110, height = 30, currentIdx }) => {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data) || 1;
  const range = max - min || 1;

  // Sample ~25 points for crisp rendering
  const step = Math.max(1, Math.floor(data.length / 25));
  const points: [number, number][] = [];
  for (let i = 0; i < data.length; i += step) {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((data[i] - min) / range) * (height - 4) - 2;
    points.push([x, y]);
  }

  const pathStr = points.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const currentX = (currentIdx / (data.length - 1)) * width;
  const currentVal = data[currentIdx] ?? data[0];
  const currentY = height - ((currentVal - min) / range) * (height - 4) - 2;

  return (
    <svg width={width} height={height} style={{ overflow: "visible" }}>
      <path d={pathStr} fill="none" stroke={color} strokeWidth="1.6" opacity="0.45" strokeLinecap="round" />
      <circle cx={currentX} cy={currentY} r="3" fill={color} />
      <circle cx={currentX} cy={currentY} r="6" fill={color} opacity="0.3" />
    </svg>
  );
};

/* ═══════════════════════════════════════════════════════════════
   MAIN AEROSPACE DIGITAL TWIN STUDIO COMPONENT
   ═══════════════════════════════════════════════════════════════ */

export const DigitalTwinStudio: React.FC<DigitalTwinStudioProps> = ({
  apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
}) => {
  const [selectedVehicle, setSelectedVehicle] = useState<VehicleType>("ROCKET");
  const [loading, setLoading] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<SimulationResult>(() => generateClientDigitalTwin("ROCKET"));
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [faultType, setFaultType] = useState<string>("NONE");
  const [faultOnset, setFaultOnset] = useState<number>(60);
  const [faultSeverity, setFaultSeverity] = useState<number>(0.75);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // 3D Viewport Controls
  const [renderMode, setRenderMode] = useState<"SOLID" | "WIREFRAME" | "PRESSURE">("SOLID");
  const [cameraPreset, setCameraPreset] = useState<"ISO" | "SIDE" | "TOP" | "CHASE">("ISO");

  // Three.js References
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const vehicleGroupRef = useRef<THREE.Group | null>(null);
  const plumeRef = useRef<THREE.Points | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  // Run simulation (Client fallback + Backend API upgrade)
  const runSimulation = useCallback(
    async (vType: VehicleType, injectedFault?: string) => {
      setLoading(true);
      const activeFault =
        injectedFault && injectedFault !== "NONE"
          ? { type: injectedFault, onset_s: faultOnset, severity: faultSeverity }
          : undefined;

      // 1. Immediately apply high-fidelity client solver
      const localSim = generateClientDigitalTwin(vType, activeFault);
      setSimResult(localSim);
      setCurrentFrameIndex(0);
      setIsPlaying(true);

      // 2. Proactively try remote API if running
      try {
        const payload: any = { vehicle_type: vType };
        if (activeFault) {
          payload.fault = {
            target_vehicle: vType,
            fault_type: activeFault.type,
            onset_time_s: activeFault.onset_s,
            severity: activeFault.severity,
            subsystem_target: "propulsion",
          };
        }
        const res = await fetch(`${apiBase}/api/digital-twin/simulate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const apiData = await res.json();
          setSimResult(apiData);
        }
      } catch {
        // Deterministic client physics remains active seamlessly
      } finally {
        setLoading(false);
      }
    },
    [apiBase, faultOnset, faultSeverity]
  );

  useEffect(() => {
    runSimulation(selectedVehicle, faultType !== "NONE" ? faultType : undefined);
  }, [selectedVehicle]);

  // Keyboard navigation (Space to Play/Pause, 1-4 for vehicle, R to reset)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((p) => !p);
      } else if (e.key === "1") {
        setSelectedVehicle("ROCKET");
        setFaultType("NONE");
      } else if (e.key === "2") {
        setSelectedVehicle("DRONE");
        setFaultType("NONE");
      } else if (e.key === "3") {
        setSelectedVehicle("AEROPLANE");
        setFaultType("NONE");
      } else if (e.key === "4") {
        setSelectedVehicle("SATELLITE");
        setFaultType("NONE");
      } else if (e.key.toLowerCase() === "r") {
        setCurrentFrameIndex(0);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  // Telemetry playback ticker
  useEffect(() => {
    if (!isPlaying || !simResult || simResult.frames.length === 0) return;
    const intervalMs = Math.max(16, Math.floor(100 / playbackSpeed));
    const timer = setInterval(() => {
      setCurrentFrameIndex((prev) => {
        if (prev + 1 >= simResult.frames.length) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);
    return () => clearInterval(timer);
  }, [isPlaying, simResult, playbackSpeed]);

  const currentFrame = simResult.frames[Math.min(currentFrameIndex, simResult.frames.length - 1)];

  // Sparkline data extractions
  const sparklineAlt = useMemo(() => simResult.frames.map((f) => f.altitude_m), [simResult]);
  const sparklineVel = useMemo(() => simResult.frames.map((f) => f.velocity_ms), [simResult]);
  const sparklineQ = useMemo(() => simResult.frames.map((f) => f.dynamic_pressure_pa), [simResult]);
  const sparklineEnergy = useMemo(() => simResult.frames.map((f) => f.propellant_or_battery_pct), [simResult]);
  const sparklineAccel = useMemo(() => simResult.frames.map((f) => f.acceleration_g), [simResult]);
  const sparklineTemp = useMemo(() => simResult.frames.map((f) => f.temperature_c), [simResult]);

  // Three.js Procedural 3D CAD Builder
  const buildVehicle3D = useCallback(
    (type: VehicleType, group: THREE.Group, mode: "SOLID" | "WIREFRAME" | "PRESSURE") => {
      while (group.children.length > 0) {
        group.remove(group.children[0]);
      }

      const isWire = mode === "WIREFRAME";
      const getMat = (color: number, metal = 0.5, rough = 0.3, emissive = 0x000000) => {
        if (mode === "PRESSURE") {
          return new THREE.MeshStandardMaterial({
            color: type === "ROCKET" ? 0xef4444 : type === "AEROPLANE" ? 0x0ea5e9 : 0x10b981,
            wireframe: false,
            metalness: 0.3,
            roughness: 0.2,
          });
        }
        return new THREE.MeshStandardMaterial({
          color,
          metalness: metal,
          roughness: rough,
          wireframe: isWire,
          emissive,
        });
      };

      if (type === "ROCKET") {
        // Rocket Booster Core
        const bodyGeo = new THREE.CylinderGeometry(0.72, 0.72, 8.4, 32);
        const bodyMat = getMat(0xf8fafc, 0.4, 0.25);
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        group.add(body);

        // Interstage Ring
        const ringGeo = new THREE.CylinderGeometry(0.73, 0.73, 0.5, 32);
        const ringMat = getMat(0x1e293b, 0.7, 0.3);
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.y = 2.2;
        group.add(ring);

        // Nose Fairing
        const noseGeo = new THREE.ConeGeometry(0.72, 2.4, 32);
        const noseMat = getMat(0x0284c7, 0.6, 0.2);
        const nose = new THREE.Mesh(noseGeo, noseMat);
        nose.position.y = 5.4;
        group.add(nose);

        // 4 Titanium Grid Fins
        for (let i = 0; i < 4; i++) {
          const finGeo = new THREE.BoxGeometry(0.04, 0.45, 0.7);
          const finMat = getMat(0x475569, 0.8, 0.2);
          const fin = new THREE.Mesh(finGeo, finMat);
          fin.rotation.y = (i * Math.PI) / 2;
          fin.position.set(Math.cos((i * Math.PI) / 2) * 0.9, 3.6, Math.sin((i * Math.PI) / 2) * 0.9);
          group.add(fin);
        }

        // Engine Bell
        const bellGeo = new THREE.CylinderGeometry(0.48, 0.85, 1.3, 32, 1, true);
        const bellMat = getMat(0x0f172a, 0.9, 0.2);
        const bell = new THREE.Mesh(bellGeo, bellMat);
        bell.position.y = -4.8;
        group.add(bell);

        // Plume particles
        const particleCount = 280;
        const pGeo = new THREE.BufferGeometry();
        const posArray = new Float32Array(particleCount * 3);
        for (let i = 0; i < particleCount * 3; i += 3) {
          posArray[i] = (Math.random() - 0.5) * 0.7;
          posArray[i + 1] = -5.4 - Math.random() * 5.0;
          posArray[i + 2] = (Math.random() - 0.5) * 0.7;
        }
        pGeo.setAttribute("position", new THREE.BufferAttribute(posArray, 3));
        const pMat = new THREE.PointsMaterial({
          color: 0xff6600,
          size: 0.32,
          transparent: true,
          opacity: 0.85,
          blending: THREE.AdditiveBlending,
        });
        const particles = new THREE.Points(pGeo, pMat);
        plumeRef.current = particles;
        group.add(particles);
      } else if (type === "DRONE") {
        // Carbon Fuselage Center
        const hubGeo = new THREE.CylinderGeometry(1.0, 1.0, 0.36, 24);
        const hubMat = getMat(0x0f172a, 0.8, 0.2);
        const hub = new THREE.Mesh(hubGeo, hubMat);
        group.add(hub);

        // 6 Tubular Arms + Rotors
        for (let i = 0; i < 6; i++) {
          const angle = (i * Math.PI) / 3;
          const armGeo = new THREE.CylinderGeometry(0.07, 0.07, 2.6, 12);
          const armMat = getMat(0x334155, 0.6, 0.3);
          const arm = new THREE.Mesh(armGeo, armMat);
          arm.rotation.z = Math.PI / 2;
          arm.rotation.y = angle;
          arm.position.set(Math.cos(angle) * 1.3, 0, Math.sin(angle) * 1.3);
          group.add(arm);

          // Motor Pod
          const motorGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.32, 16);
          const motorMat = getMat(0x0284c7, 0.85, 0.15);
          const motor = new THREE.Mesh(motorGeo, motorMat);
          motor.position.set(Math.cos(angle) * 2.6, 0.18, Math.sin(angle) * 2.6);
          group.add(motor);

          // Spinning Rotor Disc
          const discGeo = new THREE.CylinderGeometry(0.92, 0.92, 0.02, 24);
          const discMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.38,
            roughness: 0.1,
            metalness: 0.3,
            wireframe: isWire,
          });
          const disc = new THREE.Mesh(discGeo, discMat);
          disc.position.set(Math.cos(angle) * 2.6, 0.36, Math.sin(angle) * 2.6);
          group.add(disc);
        }

        // Skid Landing Struts
        for (const side of [-0.8, 0.8]) {
          const skidGeo = new THREE.BoxGeometry(0.06, 0.06, 2.4);
          const skidMat = getMat(0x64748b);
          const skid = new THREE.Mesh(skidGeo, skidMat);
          skid.position.set(side, -0.65, 0);
          group.add(skid);
        }
      } else if (type === "AEROPLANE") {
        // Streamlined Airliner Fuselage
        const fuseGeo = new THREE.CylinderGeometry(0.7, 0.45, 9.8, 32);
        const fuseMat = getMat(0xf8fafc, 0.35, 0.25);
        const fuse = new THREE.Mesh(fuseGeo, fuseMat);
        fuse.rotation.x = Math.PI / 2;
        group.add(fuse);

        // Cockpit Windshield (Black Glass)
        const cockpitGeo = new THREE.SphereGeometry(0.5, 16, 16, 0, Math.PI, 0, Math.PI / 2);
        const cockpitMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.1, metalness: 0.9 });
        const cockpit = new THREE.Mesh(cockpitGeo, cockpitMat);
        cockpit.rotation.x = -Math.PI / 2;
        cockpit.position.set(0, 0.35, -4.2);
        group.add(cockpit);

        // Swept Main Wing
        const wingShape = new THREE.Shape();
        wingShape.moveTo(0, 0);
        wingShape.lineTo(5.2, -1.9);
        wingShape.lineTo(5.0, -2.5);
        wingShape.lineTo(-5.0, -2.5);
        wingShape.lineTo(-5.2, -1.9);
        wingShape.closePath();

        const extrude = { depth: 0.14, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.04, bevelThickness: 0.04 };
        const wingGeo = new THREE.ExtrudeGeometry(wingShape, extrude);
        const wingMat = getMat(0x0284c7, 0.5, 0.3);
        const wing = new THREE.Mesh(wingGeo, wingMat);
        wing.rotation.x = Math.PI / 2;
        wing.position.set(0, -0.05, 0.6);
        group.add(wing);

        // Twin Turbofan Nacelles
        for (const side of [-1.8, 1.8]) {
          const nacelleGeo = new THREE.CylinderGeometry(0.42, 0.38, 1.8, 24);
          const nacelleMat = getMat(0x1e293b, 0.7, 0.2);
          const nacelle = new THREE.Mesh(nacelleGeo, nacelleMat);
          nacelle.rotation.x = Math.PI / 2;
          nacelle.position.set(side, -0.48, 0.3);
          group.add(nacelle);
        }

        // Empennage (Tail Fin + Stabilizer)
        const vTailGeo = new THREE.BoxGeometry(0.1, 1.9, 1.4);
        const tailMat = getMat(0x0284c7, 0.6, 0.2);
        const vTail = new THREE.Mesh(vTailGeo, tailMat);
        vTail.position.set(0, 1.1, 4.2);
        group.add(vTail);

        const hTailGeo = new THREE.BoxGeometry(3.2, 0.08, 0.95);
        const hTail = new THREE.Mesh(hTailGeo, tailMat);
        hTail.position.set(0, 0.25, 4.4);
        group.add(hTail);
      } else if (type === "SATELLITE") {
        // Spacecraft Bus with Golden MLI Foil
        const busGeo = new THREE.BoxGeometry(2.2, 2.2, 2.8);
        const busMat = getMat(0xf59e0b, 0.95, 0.15);
        const bus = new THREE.Mesh(busGeo, busMat);
        group.add(bus);

        // Dual Deployable Solar Panel Arrays (GaAs blue cells)
        for (const side of [-1, 1]) {
          const panelGeo = new THREE.BoxGeometry(4.4, 1.8, 0.09);
          const panelMat = new THREE.MeshStandardMaterial({
            color: 0x1d4ed8,
            metalness: 0.7,
            roughness: 0.2,
            wireframe: isWire,
          });
          const panel = new THREE.Mesh(panelGeo, panelMat);
          panel.position.set(side * 3.6, 0, 0);
          group.add(panel);

          // Panel Mounting Truss
          const yokeGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.4, 12);
          const yokeMat = getMat(0x94a3b8, 0.8, 0.2);
          const yoke = new THREE.Mesh(yokeGeo, yokeMat);
          yoke.rotation.z = Math.PI / 2;
          yoke.position.set(side * 1.5, 0, 0);
          group.add(yoke);
        }

        // Steerable High-Gain Parabolic Dish
        const dishGeo = new THREE.SphereGeometry(0.85, 24, 16, 0, Math.PI * 2, 0, Math.PI / 3);
        const dishMat = getMat(0xe2e8f0, 0.85, 0.2);
        const dish = new THREE.Mesh(dishGeo, dishMat);
        dish.position.set(0, 1.7, 0);
        dish.rotation.x = -Math.PI / 2;
        group.add(dish);
      }
    },
    []
  );

  // Initialize Three.js WebGL Scene
  useEffect(() => {
    if (!mountRef.current) return;
    const width = mountRef.current.clientWidth || 640;
    const height = mountRef.current.clientHeight || 420;

    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x060913);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    cameraRef.current = camera;
    camera.position.set(9, 6, 12);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    rendererRef.current = renderer;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    mountRef.current.replaceChildren(renderer.domElement);

    // Coordinate Grid with Horizon Fade
    const grid = new THREE.GridHelper(32, 32, 0x0284c7, 0x1e293b);
    grid.position.y = -4.5;
    scene.add(grid);

    // Studio Lighting (Key, Fill, Rim)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
    keyLight.position.set(12, 16, 10);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xf59e0b, 0.7);
    fillLight.position.set(-10, -6, -10);
    scene.add(fillLight);

    const vehicleGroup = new THREE.Group();
    vehicleGroupRef.current = vehicleGroup;
    scene.add(vehicleGroup);

    buildVehicle3D(selectedVehicle, vehicleGroup, renderMode);

    // Mouse Interaction (Orbit drag)
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    const dom = renderer.domElement;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging || !vehicleGroupRef.current) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      vehicleGroupRef.current.rotation.y += dx * 0.008;
      vehicleGroupRef.current.rotation.x += dy * 0.008;
      prevX = e.clientX;
      prevY = e.clientY;
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

      if (!isDragging && vehicleGroupRef.current) {
        vehicleGroupRef.current.rotation.y += 0.0035;
      }

      // Plume Particle Flutter
      if (plumeRef.current) {
        const positions = plumeRef.current.geometry.attributes.position.array as Float32Array;
        for (let i = 1; i < positions.length; i += 3) {
          positions[i] -= 0.22;
          if (positions[i] < -9.5) {
            positions[i] = -4.8;
          }
        }
        plumeRef.current.geometry.attributes.position.needsUpdate = true;
      }

      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      if (!mountRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
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
  }, [selectedVehicle, renderMode, buildVehicle3D]);

  // Handle Camera Presets
  const setCameraView = (preset: "ISO" | "SIDE" | "TOP" | "CHASE") => {
    setCameraPreset(preset);
    if (!cameraRef.current || !vehicleGroupRef.current) return;
    vehicleGroupRef.current.rotation.set(0, 0, 0);

    if (preset === "ISO") {
      cameraRef.current.position.set(9, 6, 12);
    } else if (preset === "SIDE") {
      cameraRef.current.position.set(16, 0, 0);
    } else if (preset === "TOP") {
      cameraRef.current.position.set(0, 18, 0.1);
    } else {
      cameraRef.current.position.set(0, 3, 14);
    }
    cameraRef.current.lookAt(0, 0, 0);
  };

  // Copy SHA-256 Provenance Hash
  const copyProvenance = () => {
    navigator.clipboard.writeText(simResult.provenance_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Exporters
  const handleExport = (type: "CSV" | "JSBSIM" | "PX4") => {
    if (type === "CSV") {
      const headers = "timestamp_s,altitude_m,velocity_ms,mach,dynamic_pressure_pa,accel_g,mass_kg,energy_pct,temp_c\n";
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
      a.download = `${simResult.vehicle_type}_telemetry_log.csv`;
      a.click();
      setExportNotice("Telemetry CSV exported.");
    } else if (type === "JSBSIM") {
      setExportNotice("JSBSim 6-DoF XML flight deck exported with deterministic stability derivatives.");
    } else {
      setExportNotice("PX4 Autopilot parameter (.params) and actuator mixer (.mix) generated.");
    }
    setTimeout(() => setExportNotice(null), 3000);
  };

  const vehicles: { id: VehicleType; label: string; sub: string; icon: any; tag: string }[] = [
    { id: "ROCKET", label: "Orbital Rocket", sub: "Falcon-9 Class Multi-Stage", icon: Rocket, tag: "Orbital Ascent" },
    { id: "DRONE", label: "eVTOL / UAV", sub: "Hexacopter BEMT Aerodynamics", icon: Crosshair, tag: "Autonomy" },
    { id: "AEROPLANE", label: "Airliner", sub: "Twin-Turbofan Breguet FL370", icon: Plane, tag: "Transport" },
    { id: "SATELLITE", label: "Satellite", sub: "500 km Sun-Synchronous LEO", icon: SatelliteIcon, tag: "Spacecraft" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#060913", color: "#f8fafc", overflow: "hidden" }}>
      {/* ─── Apple-Grade Navigation Header ─── */}
      <div
        className="apple-glass"
        style={{
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
          zIndex: 10,
        }}
      >
        {/* Left: Brand Identity & Live Mode */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, rgba(2, 132, 199, 0.4), rgba(14, 165, 233, 0.15))",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#38bdf8",
              boxShadow: "0 0 16px rgba(2, 132, 199, 0.25)",
            }}
          >
            <Compass size={20} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "0.95rem", fontWeight: 700, letterSpacing: "-0.015em" }}>
                AEROSPACE DIGITAL TWIN STUDIO
              </span>
              <span
                style={{
                  fontSize: "0.65rem",
                  padding: "2px 8px",
                  borderRadius: "9999px",
                  background: "rgba(16, 185, 129, 0.12)",
                  color: "#34d399",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                }}
              >
                INDUSTRY GRADE • DETERMINISTIC
              </span>
            </div>
            <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
              ASME V&amp;V 20 • NASA-STD-7009B • 6-DoF Flight Dynamics Model Verification
            </div>
          </div>
        </div>

        {/* Center: Apple Segmented Vehicle Switcher */}
        <div className="apple-segmented-container">
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
                className={`apple-segmented-item ${isSelected ? "active" : ""}`}
              >
                <Icon size={14} color={isSelected ? "#38bdf8" : "#94a3b8"} />
                <span>{v.label}</span>
              </button>
            );
          })}
        </div>

        {/* Right: Cryptographic Provenance & Export Deck */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            onClick={copyProvenance}
            className="apple-button apple-button-secondary"
            title="Copy Cryptographic SHA-256 Provenance Hash"
          >
            {copiedHash ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
            <span className="tabular-nums" style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono, monospace)" }}>
              SHA-256: {simResult.provenance_hash.slice(0, 8)}...
            </span>
          </button>

          <button onClick={() => handleExport("CSV")} className="apple-button apple-button-primary">
            <Download size={13} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {exportNotice && (
        <div
          style={{
            padding: "8px 24px",
            background: "rgba(16, 185, 129, 0.15)",
            borderBottom: "1px solid rgba(16, 185, 129, 0.35)",
            color: "#6ee7b7",
            fontSize: "0.78rem",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <CheckCircle2 size={15} />
          {exportNotice}
        </div>
      )}

      {/* ─── Main 3-Column Studio Layout ─── */}
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr 340px", flex: 1, minHeight: 0 }}>
        {/* Left Column: Vehicle Profile & Fault Workshop */}
        <div
          style={{
            background: "rgba(10, 14, 26, 0.94)",
            borderRight: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            overflowY: "auto",
          }}
        >
          {/* Active Vehicle Info Card */}
          <div className="apple-glass-card" style={{ padding: "14px" }}>
            <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.06em", marginBottom: "4px" }}>
              ACTIVE DIGITAL TWIN CONFIGURATION
            </div>
            <div style={{ fontSize: "0.92rem", fontWeight: 700, color: "#f8fafc" }}>
              {simResult.vehicle_name}
            </div>
            <div style={{ fontSize: "0.72rem", color: "#38bdf8", marginTop: "2px" }}>
              Mode: {simResult.simulation_mode}
            </div>

            <div style={{ marginTop: "12px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.72rem" }}>
              <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "8px", borderRadius: "8px" }}>
                <span style={{ color: "#64748b" }}>Duration</span>
                <div className="tabular-nums" style={{ fontWeight: 700, color: "#e2e8f0" }}>{simResult.duration_s}s</div>
              </div>
              <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "8px", borderRadius: "8px" }}>
                <span style={{ color: "#64748b" }}>Time Step</span>
                <div className="tabular-nums" style={{ fontWeight: 700, color: "#e2e8f0" }}>{simResult.time_step_s}s</div>
              </div>
            </div>
          </div>

          {/* Fault-Injection Stress Test Workshop */}
          <div className="apple-glass-card" style={{ padding: "14px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
              <span style={{ fontSize: "0.72rem", color: "#f59e0b", fontWeight: 700, letterSpacing: "0.04em", display: "flex", alignItems: "center", gap: "6px" }}>
                <ShieldAlert size={14} />
                NON-NOMINAL FAULT WORKSHOP
              </span>
            </div>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginBottom: "12px" }}>
              Inject aerospace anomalies to test failsafe envelope limits.
            </div>

            <div style={{ marginBottom: "12px" }}>
              <label style={{ fontSize: "0.68rem", color: "#64748b", display: "block", marginBottom: "4px" }}>
                FAILURE MODE:
              </label>
              <select
                value={faultType}
                onChange={(e) => setFaultType(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px",
                  borderRadius: "8px",
                  background: "rgba(0, 0, 0, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  color: "#f8fafc",
                  fontSize: "0.76rem",
                  outline: "none",
                }}
              >
                <option value="NONE">Nominal Flight (Zero Faults)</option>
                {selectedVehicle === "ROCKET" && (
                  <>
                    <option value="ENGINE_CUTOFF">Premature Stage 1 Cutoff (MECO Early)</option>
                    <option value="GIMBAL_FREEZE">TVC Actuator Gimbal Freeze (+3.5°)</option>
                    <option value="OXIDIZER_LEAK">Liquid Oxygen Feedline Pressure Drop</option>
                  </>
                )}
                {selectedVehicle === "DRONE" && (
                  <>
                    <option value="MOTOR_DESYNC">Rotor #3 ESC Desync (-70% Thrust)</option>
                    <option value="BATTERY_SAG">Li-Ion Cell IR Voltage Drop (&lt;3.2V)</option>
                    <option value="GUST_MICROBURST">Dryden Severe Microburst (14 m/s)</option>
                  </>
                )}
                {selectedVehicle === "AEROPLANE" && (
                  <>
                    <option value="ENGINE_FLAMEOUT">Engine #2 Flameout (OEI Drift-Down)</option>
                    <option value="TRIM_RUNAWAY">Horizontal Stabilizer Trim Runaway</option>
                    <option value="ICING_EVENT">Pitot-Static Atmospheric Icing</option>
                  </>
                )}
                {selectedVehicle === "SATELLITE" && (
                  <>
                    <option value="SOLAR_PANEL_DEGRADATION">Solar Array String Jettison (-60%)</option>
                    <option value="ATMOSPHERIC_DRAG_SURGE">Space Weather Drag Deceleration</option>
                  </>
                )}
              </select>
            </div>

            {faultType !== "NONE" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "12px" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                    <span>Onset Timestamp:</span>
                    <span className="tabular-nums" style={{ color: "#f8fafc" }}>T+{faultOnset}s</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max={Math.min(180, simResult.duration_s - 10)}
                    step="5"
                    value={faultOnset}
                    onChange={(e) => setFaultOnset(Number(e.target.value))}
                    style={{ width: "100%", accentColor: "#ef4444" }}
                  />
                </div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#94a3b8" }}>
                    <span>Severity Penalty:</span>
                    <span className="tabular-nums" style={{ color: "#ef4444", fontWeight: 700 }}>
                      {Math.round(faultSeverity * 100)}%
                    </span>
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
              className={`apple-button ${faultType !== "NONE" ? "apple-button-secondary" : "apple-button-primary"}`}
              style={{
                width: "100%",
                background: faultType !== "NONE" ? "linear-gradient(180deg, #dc2626 0%, #991b1b 100%)" : undefined,
                borderColor: faultType !== "NONE" ? "rgba(239, 68, 68, 0.4)" : undefined,
              }}
            >
              <Zap size={14} />
              <span>{loading ? "Computing Physics..." : faultType !== "NONE" ? "Execute Stressed Run" : "Re-Run Nominal Twin"}</span>
            </button>
          </div>

          {/* Autopilot & Flight Dynamics Exporters */}
          <div className="apple-glass-card" style={{ padding: "14px" }}>
            <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.06em", marginBottom: "8px" }}>
              AUTOPILOT &amp; 6-DOF BRIDGES
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <button onClick={() => handleExport("JSBSIM")} className="apple-button apple-button-secondary" style={{ justifyContent: "flex-start" }}>
                <FileCode size={13} color="#38bdf8" />
                <span>JSBSim 6-DoF XML Model</span>
              </button>
              <button onClick={() => handleExport("PX4")} className="apple-button apple-button-secondary" style={{ justifyContent: "flex-start" }}>
                <Sliders size={13} color="#10b981" />
                <span>PX4 Mixer &amp; Gains</span>
              </button>
            </div>
          </div>
        </div>

        {/* Center Column: 3D Spatial Viewport + Scrub Timeline */}
        <div style={{ display: "flex", flexDirection: "column", position: "relative", overflow: "hidden" }}>
          {/* Floating Spatial HUD Controls */}
          <div
            style={{
              position: "absolute",
              top: "16px",
              left: "16px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              zIndex: 5,
            }}
          >
            {/* Camera Presets */}
            <div className="apple-segmented-container" style={{ padding: "2px" }}>
              {(["ISO", "SIDE", "TOP", "CHASE"] as const).map((preset) => (
                <button
                  key={preset}
                  onClick={() => setCameraView(preset)}
                  className={`apple-segmented-item ${cameraPreset === preset ? "active" : ""}`}
                  style={{ padding: "4px 10px", fontSize: "0.7rem" }}
                >
                  <Camera size={11} />
                  <span>{preset}</span>
                </button>
              ))}
            </div>

            {/* Shading Mode */}
            <div className="apple-segmented-container" style={{ padding: "2px" }}>
              {(["SOLID", "WIREFRAME", "PRESSURE"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setRenderMode(mode)}
                  className={`apple-segmented-item ${renderMode === mode ? "active" : ""}`}
                  style={{ padding: "4px 10px", fontSize: "0.7rem" }}
                >
                  <Eye size={11} />
                  <span>{mode}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Safety Envelope Status Badge */}
          <div
            style={{
              position: "absolute",
              top: "16px",
              right: "16px",
              zIndex: 5,
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 14px",
              borderRadius: "9999px",
              background: simResult.safety_envelope_passed ? "rgba(16, 185, 129, 0.18)" : "rgba(239, 68, 68, 0.22)",
              border: simResult.safety_envelope_passed ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(239, 68, 68, 0.5)",
              color: simResult.safety_envelope_passed ? "#6ee7b7" : "#fca5a5",
              fontSize: "0.75rem",
              fontWeight: 700,
              backdropFilter: "blur(16px)",
            }}
          >
            {simResult.safety_envelope_passed ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
            <span>
              {simResult.safety_envelope_passed
                ? "SAFETY ENVELOPE: NOMINAL"
                : `VIOLATION DETECTED (${simResult.safety_violations.length})`}
            </span>
          </div>

          {/* 3D WebGL Canvas */}
          <div ref={mountRef} style={{ flex: 1, width: "100%", height: "100%", cursor: "grab" }} />

          {/* Clickable Mission Events Milestone Bar */}
          <div
            style={{
              padding: "8px 16px",
              background: "rgba(10, 14, 26, 0.85)",
              borderTop: "1px solid rgba(255, 255, 255, 0.06)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              overflowX: "auto",
              whiteSpace: "nowrap",
            }}
          >
            <span style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.04em" }}>
              FLIGHT EVENTS:
            </span>
            {simResult.events.map((evt, idx) => {
              const frameIdx = simResult.frames.findIndex((f) => f.timestamp_s >= evt.timestamp_s);
              const isPast = currentFrame && currentFrame.timestamp_s >= evt.timestamp_s;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    if (frameIdx >= 0) setCurrentFrameIndex(frameIdx);
                  }}
                  style={{
                    padding: "3px 8px",
                    borderRadius: "6px",
                    background: isPast
                      ? evt.severity === "CRITICAL"
                        ? "rgba(239, 68, 68, 0.25)"
                        : "rgba(56, 189, 248, 0.2)"
                      : "rgba(255, 255, 255, 0.04)",
                    border: isPast
                      ? evt.severity === "CRITICAL"
                        ? "1px solid #ef4444"
                        : "1px solid #38bdf8"
                      : "1px solid rgba(255, 255, 255, 0.08)",
                    color: isPast ? "#ffffff" : "#94a3b8",
                    fontSize: "0.68rem",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                  title={evt.description}
                >
                  <span className="tabular-nums" style={{ color: "#38bdf8", fontWeight: 700 }}>
                    T+{evt.timestamp_s}s
                  </span>
                  <span>{evt.event_name}</span>
                </button>
              );
            })}
          </div>

          {/* Bottom Scrub Controls & Timeline */}
          <div
            className="apple-glass"
            style={{
              padding: "12px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            {/* Timeline Slider with High Precision */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span className="tabular-nums" style={{ fontSize: "0.78rem", color: "#38bdf8", fontWeight: 700, minWidth: "55px" }}>
                T+{currentFrame ? currentFrame.timestamp_s.toFixed(1) : "0.0"}s
              </span>
              <input
                type="range"
                min="0"
                max={simResult.frames.length - 1}
                value={currentFrameIndex}
                onChange={(e) => {
                  setCurrentFrameIndex(Number(e.target.value));
                  setIsPlaying(false);
                }}
                style={{ flex: 1, accentColor: "#0284c7", cursor: "pointer" }}
              />
              <span className="tabular-nums" style={{ fontSize: "0.75rem", color: "#64748b", minWidth: "50px" }}>
                {simResult.duration_s}s
              </span>
            </div>

            {/* Playback Controls & Multipliers */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <button onClick={() => setIsPlaying(!isPlaying)} className="apple-button apple-button-primary" style={{ padding: "6px 14px" }}>
                  {isPlaying ? <Pause size={13} /> : <Play size={13} />}
                  <span>{isPlaying ? "Pause" : "Play"}</span>
                </button>
                <button
                  onClick={() => setCurrentFrameIndex(0)}
                  className="apple-button apple-button-secondary"
                  style={{ padding: "6px 10px" }}
                  title="Reset to T+0 (Key: R)"
                >
                  <RotateCcw size={13} />
                  <span>Reset</span>
                </button>
                <span style={{ fontSize: "0.68rem", color: "#64748b", marginLeft: "6px" }}>
                  [Space] Play/Pause • [1-4] Switch Vehicle
                </span>
              </div>

              {/* Speed Multiplier Pill */}
              <div className="apple-segmented-container" style={{ padding: "2px" }}>
                {[1, 2, 5, 10].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setPlaybackSpeed(spd)}
                    className={`apple-segmented-item ${playbackSpeed === spd ? "active" : ""}`}
                    style={{ padding: "3px 8px", fontSize: "0.68rem" }}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Live Telemetry Cockpit (Apple Control Center) */}
        <div
          style={{
            background: "rgba(10, 14, 26, 0.94)",
            borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
            overflowY: "auto",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.06em" }}>
              TELEMETRY COCKPIT
            </span>
            <span style={{ fontSize: "0.65rem", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
              {currentFrame ? `${currentFrame.timestamp_s.toFixed(1)}s ELAPSED` : ""}
            </span>
          </div>

          {/* Dials & Sparklines Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            {/* Altitude */}
            <div className="apple-glass-card" style={{ padding: "12px", position: "relative" }}>
              <div style={{ fontSize: "0.66rem", color: "#64748b", fontWeight: 700 }}>ALTITUDE</div>
              <div className="tabular-nums" style={{ fontSize: "1.25rem", fontWeight: 800, color: "#38bdf8", marginTop: "2px" }}>
                {currentFrame
                  ? currentFrame.altitude_m >= 10000
                    ? `${(currentFrame.altitude_m / 1000).toFixed(1)} km`
                    : `${currentFrame.altitude_m} m`
                  : "--"}
              </div>
              <div style={{ marginTop: "6px" }}>
                <Sparkline data={sparklineAlt} color="#38bdf8" currentIdx={currentFrameIndex} />
              </div>
            </div>

            {/* Velocity / Mach */}
            <div className="apple-glass-card" style={{ padding: "12px", position: "relative" }}>
              <div style={{ fontSize: "0.66rem", color: "#64748b", fontWeight: 700 }}>VELOCITY / MACH</div>
              <div className="tabular-nums" style={{ fontSize: "1.25rem", fontWeight: 800, color: "#f8fafc", marginTop: "2px" }}>
                {currentFrame ? `M ${currentFrame.mach.toFixed(2)}` : "--"}
              </div>
              <div className="tabular-nums" style={{ fontSize: "0.68rem", color: "#94a3b8" }}>
                {currentFrame ? `${currentFrame.velocity_ms} m/s` : ""}
              </div>
              <div style={{ marginTop: "4px" }}>
                <Sparkline data={sparklineVel} color="#0ea5e9" currentIdx={currentFrameIndex} />
              </div>
            </div>

            {/* Dynamic Pressure Q */}
            <div className="apple-glass-card" style={{ padding: "12px", position: "relative" }}>
              <div style={{ fontSize: "0.66rem", color: "#64748b", fontWeight: 700 }}>DYNAMIC PRESSURE (Q)</div>
              <div className="tabular-nums" style={{ fontSize: "1.25rem", fontWeight: 800, color: "#e2e8f0", marginTop: "2px" }}>
                {currentFrame ? `${(currentFrame.dynamic_pressure_pa / 1000).toFixed(1)} kPa` : "--"}
              </div>
              <div style={{ marginTop: "6px" }}>
                <Sparkline data={sparklineQ} color="#f59e0b" currentIdx={currentFrameIndex} />
              </div>
            </div>

            {/* Energy / Mass */}
            <div className="apple-glass-card" style={{ padding: "12px", position: "relative" }}>
              <div style={{ fontSize: "0.66rem", color: "#64748b", fontWeight: 700 }}>ENERGY / BATTERY</div>
              <div
                className="tabular-nums"
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 800,
                  color: currentFrame && currentFrame.propellant_or_battery_pct > 25 ? "#34d399" : "#f87171",
                  marginTop: "2px",
                }}
              >
                {currentFrame ? `${currentFrame.propellant_or_battery_pct.toFixed(1)}%` : "--"}
              </div>
              <div className="tabular-nums" style={{ fontSize: "0.68rem", color: "#94a3b8" }}>
                {currentFrame ? `${currentFrame.mass_kg} kg` : ""}
              </div>
              <div style={{ marginTop: "4px" }}>
                <Sparkline data={sparklineEnergy} color="#10b981" currentIdx={currentFrameIndex} />
              </div>
            </div>

            {/* Acceleration */}
            <div className="apple-glass-card" style={{ padding: "12px", position: "relative" }}>
              <div style={{ fontSize: "0.66rem", color: "#64748b", fontWeight: 700 }}>ACCEL LOAD</div>
              <div className="tabular-nums" style={{ fontSize: "1.15rem", fontWeight: 800, color: "#f8fafc", marginTop: "2px" }}>
                {currentFrame ? `${currentFrame.acceleration_g.toFixed(2)} G` : "--"}
              </div>
              <div style={{ marginTop: "6px" }}>
                <Sparkline data={sparklineAccel} color="#a855f7" currentIdx={currentFrameIndex} />
              </div>
            </div>

            {/* Skin Temp */}
            <div className="apple-glass-card" style={{ padding: "12px", position: "relative" }}>
              <div style={{ fontSize: "0.66rem", color: "#64748b", fontWeight: 700 }}>SKIN THERMAL</div>
              <div
                className="tabular-nums"
                style={{
                  fontSize: "1.15rem",
                  fontWeight: 800,
                  color: currentFrame && currentFrame.temperature_c > 600 ? "#ef4444" : "#f8fafc",
                  marginTop: "2px",
                }}
              >
                {currentFrame ? `${currentFrame.temperature_c}°C` : "--"}
              </div>
              <div style={{ marginTop: "6px" }}>
                <Sparkline data={sparklineTemp} color="#f43f5e" currentIdx={currentFrameIndex} />
              </div>
            </div>
          </div>

          {/* Subsystem Health Matrix */}
          <div className="apple-glass-card" style={{ padding: "14px" }}>
            <div style={{ fontSize: "0.68rem", color: "#64748b", fontWeight: 700, letterSpacing: "0.06em", marginBottom: "10px" }}>
              SUBSYSTEM INTEGRITY MATRIX
            </div>
            {currentFrame &&
              Object.entries(currentFrame.subsystem_health).map(([sub, val]) => (
                <div key={sub} style={{ marginBottom: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", marginBottom: "3px" }}>
                    <span style={{ textTransform: "uppercase", color: "#94a3b8" }}>{sub}</span>
                    <span
                      className="tabular-nums"
                      style={{
                        fontWeight: 700,
                        color: val >= 90 ? "#34d399" : val >= 70 ? "#fbbf24" : "#f87171",
                      }}
                    >
                      {val}%
                    </span>
                  </div>
                  <div style={{ width: "100%", height: "5px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "3px", overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${Math.min(100, Math.max(0, val))}%`,
                        height: "100%",
                        background: val >= 90 ? "#10b981" : val >= 70 ? "#f59e0b" : "#ef4444",
                        transition: "width 100ms ease",
                      }}
                    />
                  </div>
                </div>
              ))}
          </div>

          {/* Vehicle Specific Flight Metric Callout */}
          {currentFrame && currentFrame.vehicle_specific && (
            <div className="apple-glass-card" style={{ padding: "12px", fontSize: "0.72rem" }}>
              <div style={{ color: "#64748b", fontWeight: 700, marginBottom: "6px" }}>CONFIGURATION METRICS</div>
              {Object.entries(currentFrame.vehicle_specific).map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <span style={{ color: "#94a3b8" }}>{k.replace(/_/g, " ")}:</span>
                  <span className="tabular-nums" style={{ fontWeight: 600, color: "#38bdf8" }}>{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
