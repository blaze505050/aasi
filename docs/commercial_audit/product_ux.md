# AASI Product UX — Phase 13 & 14

> **Audit Date:** 2026-09-25

---

## Current UX Assessment

### What Works Well
1. **Investigation Workspace** (72KB) — comprehensive, shows investigation state, evidence, experiments
2. **Cognitive Brain Workspace** — shows state machine, world model, hypotheses visually
3. **Hypothesis Card Deck** — good card-based presentation of competing hypotheses
4. **Scientific Result Panel** — clear evidence presentation with epistemic tiers
5. **Design system** (globals.css, 50KB) — polished dark theme, glassmorphism, consistent design tokens
6. **Scientific disclaimer footer** — honest, builds trust

### UX Issues for Paying Customers

| Issue | Severity | Detail |
|---|---|---|
| No clear onboarding flow | **HIGH** | New user lands on investigation workspace with no guidance |
| Investigation state not immediately obvious | **HIGH** | Current state (UNDERSTANDING, VERIFYING, etc.) needs prominent display |
| Cannot distinguish evidence types at a glance | **MEDIUM** | Epistemic tier badges exist but need visual hierarchy |
| No investigation timeline | **MEDIUM** | ExecutionTimeline exists but not prominently featured |
| Chat is secondary to investigation | ✅ CORRECT | Chat panel is a floating assistant, not the main interface |
| No "Demo Mode" | **HIGH** | No way for prospects to understand the product without account |
| Cannot share investigations | **MEDIUM** | No shareable investigation URLs |
| Cannot export report from UI | **MEDIUM** | Report generation exists in backend but not in frontend |
| No project/organization navigation | **HIGH** | No way to organize investigations |

---

## Product Experience Specification

### Primary Interface: Scientific Mission Control

The main interface should convey:

```
┌─────────────────────────────────────────────────────────────────┐
│ AASI — Investigation: "NACA 0012 Drag at Re=500K"              │
│ Status: VERIFYING    Cycle: 2/3    Autonomy: Level 4           │
├─────────────────┬───────────────────────────────────────────────┤
│                 │                                               │
│  INVESTIGATION  │  MAIN PANEL (context-dependent)               │
│  NAVIGATION     │  ┌─────────────────────────────────┐         │
│                 │  │ World Model / Hypotheses /       │         │
│  ◉ Question     │  │ Evidence / Experiments /         │         │
│  ◉ World Model  │  │ Verification / Decision /        │         │
│  ◉ Hypotheses   │  │ Report                           │         │
│  ◉ Experiments  │  └─────────────────────────────────┘         │
│  ◉ Evidence     │                                               │
│  ◉ Tools        │  ┌─────────────────────────────────┐         │
│  ◉ Verification │  │ Investigation Timeline            │         │
│  ◉ Decision     │  │ [UNDERSTAND]→[MODEL]→[RETRIEVE]→ │         │
│  ● Next Action  │  │ [HYPOTHESIZE]→[VERIFY]→...       │         │
│                 │  └─────────────────────────────────┘         │
│  ─────────────  │                                               │
│  💬 Chat Assist │                                               │
│                 │                                               │
├─────────────────┴───────────────────────────────────────────────┤
│ Evidence: 3 VERIFIED / 1 ANALYTICAL / 2 UNVERIFIED    Trust: ██░│
└─────────────────────────────────────────────────────────────────┘
```

### Key UX Principles

1. **Investigation is the hero, not chat** — chat supports investigation
2. **State is always visible** — current cognitive state, cycle number, autonomy level
3. **Evidence type is visually distinct** — color-coded badges for each epistemic tier
4. **Next action is prominent** — what AASI will do next (or needs from user)
5. **Trust is quantified** — evidence quality meter, not vague "confidence"
6. **Timeline shows history** — every state transition is visible
7. **Investigation is reproducible** — provenance hashes visible, export available

### Evidence Type Visual Language

| Tier | Color | Icon | Badge |
|---|---|---|---|
| VERIFIED | Green | ✓ | Solid green |
| EXPERIMENTAL | Blue | 🔬 | Solid blue |
| ANALYTICAL | Cyan | ∑ | Outline cyan |
| SIMULATED | Orange | ⚡ | Outline orange |
| SURROGATE | Yellow | 🧠 | Outline yellow |
| MODEL_GENERATED | Gray | 💭 | Dashed gray |
| UNVERIFIED | Red outline | ⚠ | Dashed red |

---

## Onboarding Flow (Phase 15)

### Target: Time-to-first-value < 10 minutes

```
Step 1: Create account (email + password) .................. 1 min
Step 2: Welcome screen — "What would you like to investigate?" 
Step 3: Enter engineering question in natural language ...... 1 min
        Example: "What is the drag coefficient of NACA 0012 at Re=500K and 8° angle of attack?"
Step 4: AASI normalizes conditions, builds world model ..... 30 sec
Step 5: Review assumptions and world model ................. 1 min
Step 6: AASI generates hypotheses and experiment plan ...... 30 sec
Step 7: Panel solver executes immediately (< 3 sec) ........ 3 sec
Step 8: First result with verification ..................... instant
Step 9: AASI recommends next experiment (CFD) .............. 30 sec
Step 10: User sees complete investigation state ............ 
                                              Total: ~5 min
```

**Note:** CFD experiments require external compute (Colab/HPC), which adds user-dependent time.
