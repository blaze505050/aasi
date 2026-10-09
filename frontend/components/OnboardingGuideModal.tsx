"use client";

import React, { useState } from "react";
import { Cpu, Layers, ShieldCheck } from "lucide-react";

export interface OnboardingGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectScenario: (scenario: {
    prompt: string;
    geometry: string;
    alpha: number;
    re: number;
    mach: number;
  }) => void;
}

export const OnboardingGuideModal: React.FC<OnboardingGuideModalProps> = ({
  isOpen,
  onClose,
  onSelectScenario,
}) => {
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  if (!isOpen) return null;

  const handleDismiss = () => {
    if (dontShowAgain && typeof window !== "undefined") {
      localStorage.setItem("aasi_onboarding_completed", "true");
    }
    onClose();
  };

  const scenarios = [
    {
      badge: "CANONICAL 1",
      badgeColor: "#64d2ff",
      title: "NACA 0012 Multi-Fidelity Verification",
      desc: "Reconciles analytical thin airfoil theory with discrete vortex panel solver, deep neural surrogate, and ASME V&V 20 verified OpenFOAM CFD.",
      geometry: "NACA 0012",
      alpha: 6.0,
      re: 6000000,
      mach: 0.15,
      prompt: "Analyze the lift, drag and pitching moment of NACA 0012 at Re = 6e6 and alpha = 6° with multi-fidelity verification.",
    },
    {
      badge: "FAULT RECOVERY 2",
      badgeColor: "#ffd60a",
      title: "NACA 4412 Post-Stall Separation & Recovery",
      desc: "Detects numerical divergence and boundary layer detachment at alpha = 20°. Automatically triggers diagnostic repair and bounds epistemic uncertainty.",
      geometry: "NACA 4412",
      alpha: 20.0,
      re: 3000000,
      mach: 0.15,
      prompt: "Analyze post-stall separation and adverse pressure gradients of NACA 4412 at Re = 3x10^6 and alpha = 20°.",
    },
    {
      badge: "CONTRADICTION 3",
      badgeColor: "#f59e0b",
      title: "Inviscid vs. Viscous Contradiction Attribution",
      desc: "Decomposes d'Alembert's paradox: compares inviscid potential flow (CD=0) against viscous boundary layer shear stress (CD=0.0082).",
      geometry: "NACA 0012",
      alpha: 0.0,
      re: 6000000,
      mach: 0.15,
      prompt: "Compare Inviscid Potential Flow (CD=0) vs. Viscous RANS (CD=0.0082) for NACA 0012 at alpha = 0° and attribute physical discrepancy.",
    },
  ];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        background: "rgba(5, 8, 15, 0.8)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
      }}
      onClick={handleDismiss}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "800px",
          maxHeight: "90vh",
          overflowY: "auto",
          background: "rgba(18, 24, 38, 0.95)",
          border: "1px solid rgba(100, 210, 255, 0.25)",
          borderRadius: "20px",
          padding: "32px",
          boxShadow: "0 24px 64px rgba(0, 0, 0, 0.7), 0 0 40px rgba(0, 210, 255, 0.1)",
          color: "#ffffff",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "14px",
                background: "linear-gradient(135deg, rgba(0, 119, 237, 0.35), rgba(0, 199, 190, 0.2))",
                border: "1px solid rgba(100, 210, 255, 0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.4rem",
                color: "#64d2ff",
                boxShadow: "0 4px 16px rgba(0, 0, 0, 0.4)",
              }}
            >
              ◈
            </div>
            <div>
              <span style={{ fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.14em", color: "#64d2ff", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                QUICKSTART &amp; ARCHITECTURE GUIDE
              </span>
              <h2 style={{ fontSize: "1.4rem", fontWeight: 700, margin: "2px 0 0 0", letterSpacing: "-0.02em" }}>
                Welcome to AASI
              </h2>
              <p style={{ margin: "2px 0 0 0", color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                Autonomous Aerospace Scientific Intelligence Platform
              </p>
            </div>
          </div>

          <button
            onClick={handleDismiss}
            style={{
              background: "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "var(--text-muted)",
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            ✕
          </button>
        </div>

        {/* 3 Core Scientific Pillars */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px", marginBottom: "28px" }}>
          <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "16px" }}>
            <div style={{ marginBottom: "8px", color: "#38bdf8" }}><Cpu size={20} /></div>
            <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "#38bdf8", marginBottom: "4px" }}>
              Autonomous Reasoning
            </h4>
            <p style={{ fontSize: "0.74rem", color: "var(--text-secondary)", lineHeight: 1.45, margin: 0 }}>
              Formulates structured scientific hypotheses, designs experiment chains, and reconciles multi-fidelity discrepancies without human hand-holding.
            </p>
          </div>

          <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "16px" }}>
            <div style={{ marginBottom: "8px", color: "#f59e0b" }}><Layers size={20} /></div>
            <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f59e0b", marginBottom: "4px" }}>
              Multi-Fidelity Solvers
            </h4>
            <p style={{ fontSize: "0.74rem", color: "var(--text-secondary)", lineHeight: 1.45, margin: 0 }}>
              Chains fast discrete vortex panels (0.04s), neural operator surrogates, and remote OpenFOAM 10 RANS CFD (k-omega SST) on conformal meshes.
            </p>
          </div>

          <div style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: "8px", padding: "16px" }}>
            <div style={{ marginBottom: "8px", color: "#10b981" }}><ShieldCheck size={20} /></div>
            <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "#10b981", marginBottom: "4px" }}>
              ASME V&amp;V 20 Integrity
            </h4>
            <p style={{ fontSize: "0.74rem", color: "var(--text-secondary)", lineHeight: 1.45, margin: 0 }}>
              Enforces zero numerical fabrication: checks mesh grid convergence indices (GCI &lt; 3%), preserves negative evidence, and signs SHA-256 archives.
            </p>
          </div>
        </div>

        {/* Canonical Starter Scenarios */}
        <div style={{ marginBottom: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "0.74rem", fontWeight: 700, color: "#ffffff", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              🚀 Launch a Pre-Configured Benchmark Investigation:
            </span>
            <span style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>
              One click to populate and begin
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {scenarios.map((sc, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  background: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "14px 18px",
                  cursor: "pointer",
                  transition: "all 150ms ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(100, 210, 255, 0.08)";
                  e.currentTarget.style.borderColor = "rgba(100, 210, 255, 0.3)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                  e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
                }}
                onClick={() => {
                  onSelectScenario(sc);
                  handleDismiss();
                }}
              >
                <div style={{ maxWidth: "80%" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span
                      style={{
                        fontSize: "0.6rem",
                        fontWeight: 700,
                        fontFamily: "var(--font-mono)",
                        color: sc.badgeColor,
                        background: `${sc.badgeColor}1a`,
                        border: `1px solid ${sc.badgeColor}40`,
                        padding: "2px 6px",
                        borderRadius: "4px",
                      }}
                    >
                      {sc.badge}
                    </span>
                    <strong style={{ fontSize: "0.85rem", color: "#ffffff" }}>{sc.title}</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.74rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                    {sc.desc}
                  </p>
                </div>

                <button
                  style={{
                    background: "linear-gradient(135deg, rgba(0, 119, 237, 0.4), rgba(0, 199, 190, 0.3))",
                    border: "1px solid rgba(100, 210, 255, 0.5)",
                    borderRadius: "8px",
                    color: "#ffffff",
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    padding: "8px 16px",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  Run Benchmark →
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            paddingTop: "18px",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.74rem", color: "var(--text-muted)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              style={{ cursor: "pointer", accentColor: "#0077ed" }}
            />
            Don't show this guide on startup
          </label>

          <button
            onClick={handleDismiss}
            style={{
              background: "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "#ffffff",
              fontSize: "0.78rem",
              fontWeight: 600,
              padding: "8px 20px",
              borderRadius: "8px",
              cursor: "pointer",
            }}
          >
            Enter Workspace
          </button>
        </div>
      </div>
    </div>
  );
};
