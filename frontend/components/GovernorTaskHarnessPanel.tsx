"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertOctagon,
  Cpu,
  Database,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Hash,
  Terminal,
  Activity,
  Layers,
  ChevronRight,
  ExternalLink,
} from "lucide-react";

interface ResourceTelemetry {
  cpu_percent: number;
  cpu_ema_percent: number;
  available_ram_gb: number;
  total_ram_gb: number;
  is_ram_critical: boolean;
  is_cpu_saturated: boolean;
  status: string;
}

interface GovernorStatus {
  armed: boolean;
  halted: boolean;
  last_halt_reason: string | null;
  cooldown_remaining_sec: number;
  audit_chain_length: number;
  merkle_root: string;
}

interface TaskStep {
  step_index: number;
  state: string;
  action_name: string;
  success: boolean;
  epistemic_tier?: string;
  error?: string;
}

interface TaskExecutionResult {
  task_id: string;
  question: string;
  final_state: string;
  success: boolean;
  answer: string;
  evidence_record: any;
  steps: TaskStep[];
  provenance_chain_hash: string;
  duration_seconds: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function GovernorTaskHarnessPanel() {
  const [telemetry, setTelemetry] = useState<ResourceTelemetry | null>(null);
  const [governorStatus, setGovernorStatus] = useState<GovernorStatus | null>(null);
  const [taskQuery, setTaskQuery] = useState("Calculate aerodynamic lift and drag for NACA 0012 at alpha 4.0 degrees");
  const [isRunning, setIsRunning] = useState(false);
  const [taskResult, setTaskResult] = useState<TaskExecutionResult | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Poll system resources and governor state
  const fetchStatus = async () => {
    try {
      const [resTele, resGov] = await Promise.all([
        fetch(`${API_BASE}/api/system/resources`).then((r) => (r.ok ? r.json() : null)),
        fetch(`${API_BASE}/api/system/governor/status`).then((r) => (r.ok ? r.json() : null)),
      ]);
      if (resTele) setTelemetry(resTele);
      if (resGov) setGovernorStatus(resGov);
    } catch (e) {
      // offline / mock fallback
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  // Emergency Halt
  const handleEmergencyHalt = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/system/emergency-halt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Manual Emergency Halt triggered from Mission Control UI" }),
      });
      const data = await res.json();
      setActionMessage("EMERGENCY HALT TRIGGERED: All background processes cancelled.");
      fetchStatus();
    } catch (e) {
      setActionMessage("Failed to signal emergency halt: " + e);
    }
  };

  // Reset Emergency Halt
  const handleResetHalt = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/system/emergency-halt/reset?force=true`, {
        method: "POST",
      });
      const data = await res.json();
      setActionMessage("Emergency Halt Reset: Governor is ARMED.");
      fetchStatus();
    } catch (e) {
      setActionMessage("Failed to reset halt: " + e);
    }
  };

  // Execute Task Harness
  const handleExecuteTask = async () => {
    if (!taskQuery.trim() || isRunning) return;
    setIsRunning(true);
    setTaskResult(null);
    setActionMessage(null);

    try {
      const res = await fetch(`${API_BASE}/api/agent/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: taskQuery,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP Error: ${res.status} ${res.statusText}`);
      }

      const data: TaskExecutionResult = await res.json();
      setTaskResult(data);
      fetchStatus();
    } catch (e: any) {
      setActionMessage(`Task dispatch failed: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const isHalted = governorStatus?.halted ?? false;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-2xl space-y-6">
      {/* Header & Governor HUD */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <h2 className="text-lg font-bold tracking-tight text-white">
              AASI 2.0 Autonomous Harness & Safety Governor
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic fail-closed resource bounds, ASME V&V 20 verification & Merkle lineage DAG
          </p>
        </div>

        {/* Live Telemetry Pills */}
        <div className="flex items-center gap-3">
          {telemetry && (
            <div className="flex items-center gap-4 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
              <div className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-slate-400">CPU:</span>
                <span className="font-mono font-semibold text-white">
                  {telemetry.cpu_percent.toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                <span className="text-slate-400">RAM:</span>
                <span className="font-mono font-semibold text-white">
                  {telemetry.available_ram_gb.toFixed(2)} GB free
                </span>
              </div>
            </div>
          )}

          {/* Kill Switch Controls */}
          {isHalted ? (
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 bg-rose-950 text-rose-300 border border-rose-800 rounded text-xs font-bold animate-pulse">
                HALTED
              </span>
              <button
                onClick={handleResetHalt}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reset Halt
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 bg-emerald-950 text-emerald-300 border border-emerald-800 rounded text-xs font-bold">
                ARMED
              </span>
              <button
                onClick={handleEmergencyHalt}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold shadow-lg shadow-rose-950 transition"
              >
                <AlertOctagon className="w-3.5 h-3.5" />
                Emergency Halt
              </button>
            </div>
          )}
        </div>
      </div>

      {actionMessage && (
        <div className="bg-slate-950 border border-amber-800/60 text-amber-300 px-4 py-2.5 rounded text-xs font-mono">
          {actionMessage}
        </div>
      )}

      {/* Task Harness Input Prompt */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          Autonomous Scientific Inquiry Loop (Question → Plan → Execute → Verify → Reconcile → Decide)
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={taskQuery}
            onChange={(e) => setTaskQuery(e.target.value)}
            disabled={isRunning || isHalted}
            placeholder="Enter research or engineering question..."
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
          />
          <button
            onClick={handleExecuteTask}
            disabled={isRunning || isHalted || !taskQuery.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition shadow-lg shadow-cyan-950"
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Executing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Dispatch
              </>
            )}
          </button>
        </div>
      </div>

      {/* Task Execution Progress & State Machine */}
      {taskResult && (
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-cyan-400">{taskResult.task_id}</span>
              <span
                className={`px-2 py-0.5 rounded font-bold uppercase ${
                  taskResult.success
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    : "bg-rose-950 text-rose-400 border border-rose-800"
                }`}
              >
                {taskResult.final_state}
              </span>
            </div>
            <div className="text-slate-400 font-mono">
              Duration: {taskResult.duration_seconds}s
            </div>
          </div>

          {/* Stepper Timeline */}
          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-400 uppercase">Cognitive Phase Sequence</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-1">
              {taskResult.steps.map((step) => (
                <div
                  key={step.step_index}
                  className={`p-2 rounded border text-xs flex flex-col justify-between ${
                    step.success
                      ? "bg-slate-900 border-slate-800 text-slate-200"
                      : "bg-rose-950/40 border-rose-800 text-rose-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-slate-400">#{step.step_index}</span>
                    <span className="font-bold text-[10px] uppercase text-cyan-400">{step.state}</span>
                  </div>
                  <div className="font-mono text-[11px] truncate mt-1 text-slate-300">
                    {step.action_name}
                  </div>
                  {step.epistemic_tier && (
                    <span className="mt-1 text-[9px] text-amber-400 font-mono uppercase">
                      [{step.epistemic_tier}]
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Decision Summary */}
          <div className="space-y-1">
            <div className="text-xs font-semibold text-slate-400 uppercase">Synthesized Decision</div>
            <div className="p-3 bg-slate-900 border border-slate-800 rounded font-mono text-xs text-emerald-300 whitespace-pre-wrap">
              {taskResult.answer}
            </div>
          </div>

          {/* Merkle Cryptographic Fingerprint */}
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono pt-2 border-t border-slate-800">
            <div className="flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-indigo-400" />
              <span>Merkle Chain:</span>
              <span className="text-slate-300 truncate max-w-xs">{taskResult.provenance_chain_hash}</span>
            </div>
            {taskResult.evidence_record?.merkle_node_id && (
              <div className="text-cyan-400">
                Lineage Node: {taskResult.evidence_record.merkle_node_id.slice(0, 12)}...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
