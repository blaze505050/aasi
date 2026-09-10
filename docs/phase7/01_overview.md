# 01 - Autonomous Research Loop Overview

## 1. Scientific Mission

Phase 7 transforms AASI into an autonomous, closed-loop aerospace science assistant. Static machine learning models in CFD suffer from out-of-distribution hallucinations, hidden extrapolation errors, and lack of accountability to physical conservation laws.

AASI resolves this by establishing an explicit, verifiable loop:

$$\text{Active Surrogate} \xrightarrow{\text{Audit}} \text{Active Learning 2.0} \xrightarrow{\text{Plan}} \text{CFDJobSpec} \xrightarrow{\text{Run}} \text{QC \& Ingest} \xrightarrow{\text{Version}} \text{Retraining} \xrightarrow{\text{Gate}} \text{Promote}$$

## 2. Architectural Components

```
                   +-------------------------------------------------+
                   |           AASI PHASE 7 CORE ARCHITECTURE        |
                   +-------------------------------------------------+
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  Multi-Fidelity  │             │  Active Learning │             │ Simulation & QC  │
│      Fabric      │             │       2.0        │             │      Engine      │
│                  │             │                  │             │                  │
│ • 5-Tier Cascade │             │ • Cost-Aware Acq │             │ • Canonical Spec │
│ • Discrepancy    │             │ • Coverage Grid  │             │ • ASME V&V 20 QC │
│ • Calibration    │             │ • Void Detection │             │ • Residual Audit │
│ • Co-Kriging Fus │             │ • State Machine  │             │ • Force Stability│
└────────┬─────────┘             └────────┬─────────┘             └────────┬─────────┘
         │                                │                                │
         └────────────────────────────────┼────────────────────────────────┘
                                          ▼
                         ┌──────────────────────────────────┐
                         │   Research Pipeline & Promotion  │
                         │                                  │
                         │ • Objective Lifecycle           │
                         │ • Dataset Versioning (V1 ➔ V2)   │
                         │ • Fine-Tuning & Retraining       │
                         │ • 4-Gate Model Promotion         │
                         │ • Peer-Review Report Generator   │
                         └──────────────────────────────────┘
```

## 3. Epistemic Transparency and Accountability

In compliance with AASI's foundational zero-fabrication pledge:
1. Every prediction explicitly reveals its data origin tier (`OFFICIAL_EXPERIMENT`, `VALIDATED_CFD`, `SURROGATE`, `ANALYTICAL`, or `PLANNER`).
2. Computational costs and mesh requirements are accurately forecasted based on cell density and turbulent wall resolution ($y^+ \le 1$).
3. Models can never self-promote without passing non-regression checks on standard NASA benchmark cases.
