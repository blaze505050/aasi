# AASI Competitive Landscape — Phase 2

> **Audit Date:** 2026-09-25
> **Sources:** Public product pages, market reports, industry analysis (2025-2026)

---

## Market Context (2026)

The aerospace engineering software market is transitioning from passive CAE tools to **agentic AI workflows**. Key trends:

1. **AI-native simulation** — surrogate models replacing/augmenting solver runs (SimScale PhysicsAI, Ansys SimAI)
2. **Agentic engineering** — AI agents coordinating multi-stage simulation workflows
3. **Cloud-native engineering** — browser-based CFD/FEA replacing desktop installations
4. **Autonomous scientific discovery** — AI systems that plan and execute experiments (The AI Scientist, ERA, MIRA)
5. **Value-based pricing** — shifting from seat licenses to usage/outcome-based models

AASI sits at the intersection of autonomous scientific discovery and aerospace engineering software — a space with **no established competitor offering the full investigation loop**.

---

## Competitor Analysis

### Tier 1: Established CAE/Simulation Leaders

| Competitor | Classification | Target Customer | Core JTBD | Pricing Model | Deployment | Strength | Weakness | AASI Differentiation | AASI Threat Level |
|---|---|---|---|---|---|---|---|---|---|
| **Ansys** (Synopsys) | ADJACENT | Large enterprise OEMs | Production simulation & validation | Enterprise license ($50K-$500K+/yr) | On-prem, cloud | Comprehensive physics, industry standard, ecosystem | Expensive, complex, no autonomous investigation | AASI orchestrates *above* Ansys, not against it | LOW |
| **Siemens Simcenter** | ADJACENT | Automotive, aerospace OEMs | Multi-physics simulation in PLM | Enterprise license | On-prem, cloud | Integrated with Teamcenter PLM, broad physics | Monolithic, no scientific reasoning | AASI adds scientific brain to Simcenter workflows | LOW |
| **Dassault 3DEXPERIENCE** | ADJACENT | Large OEMs, defense | End-to-end product lifecycle | Enterprise license | Cloud, on-prem | Full PLM integration | Extremely complex, no investigation intelligence | Complementary — AASI could integrate as investigation layer | LOW |
| **Altair** | ADJACENT | Multi-industry engineering | HPC simulation, optimization | Enterprise license, units | Cloud, HPC | Strong HPC, optimization | No scientific reasoning layer | AASI adds investigation intelligence to Altair compute | LOW |
| **COMSOL** | ADJACENT | University, specialized physics | Multi-physics modeling | Seat license ($5K-$30K/yr) | Desktop | Excellent multi-physics coupling | No autonomous workflow, desktop-only | AASI could orchestrate COMSOL as a tool | LOW |

### Tier 2: Cloud-Native Simulation

| Competitor | Classification | Target Customer | Core JTBD | Pricing Model | Deployment | Strength | Weakness | AASI Differentiation | AASI Threat Level |
|---|---|---|---|---|---|---|---|---|---|
| **SimScale** | FUTURE COMPETITOR | SME engineers, startups | Browser-based CFD/FEA | Freemium, usage-based | Cloud SaaS | Physics AI surrogates, cloud-native, accessible | No scientific investigation loop, no hypothesis reasoning | AASI has cognitive loop; SimScale has better onboarding UX | **MEDIUM** |
| **Cadence (Numeca)** | ADJACENT | Turbomachinery, aerospace | Specialized CFD for turbomachinery | Enterprise license | On-prem, cloud | Domain-specific accuracy | Narrow focus, no AI investigation | AASI is broader in investigation capability | LOW |

### Tier 3: AI-Native Engineering

| Competitor | Classification | Target Customer | Core JTBD | Pricing Model | Deployment | Strength | Weakness | AASI Differentiation | AASI Threat Level |
|---|---|---|---|---|---|---|---|---|---|
| **PhysicsX** | FUTURE COMPETITOR | Enterprise R&D | Deep-physics AI for design optimization | Enterprise, custom | Cloud | Strong ML physics models, well-funded | No investigation loop, no provenance, proprietary | AASI has full cognitive loop + provenance + verification | **MEDIUM** |
| **Neural Concept** | ADJACENT | Automotive, aerospace | AI-accelerated design exploration | Enterprise license | Cloud | Good 3D deep learning | No scientific reasoning, limited to shape optimization | AASI investigates *why*, not just *what shape* | LOW |
| **Monolith** | ADJACENT | Automotive, industrial | Self-service AI for engineering data | Subscription | Cloud | No-code ML, good for test data | No simulation orchestration, no scientific method | AASI has full scientific workflow vs. data analysis | LOW |

### Tier 4: Autonomous Scientific AI

| Competitor | Classification | Target Customer | Core JTBD | Pricing Model | Deployment | Strength | Weakness | AASI Differentiation | AASI Threat Level |
|---|---|---|---|---|---|---|---|---|---|
| **The AI Scientist** (Sakana AI) | FUTURE COMPETITOR | AI/ML researchers | Automated paper writing + experiments | Open-source | Self-hosted | Fully autonomous research cycle | Not domain-specific, no engineering tool integration, no verification | AASI is aerospace-native with engineering tools + verification | **LOW-MEDIUM** |
| **Elicit** | COMPLEMENTARY | Academic researchers | Literature review + evidence synthesis | Subscription ($10-50/mo) | Cloud | Good literature discovery | No simulation, no investigation execution | AASI does investigation; Elicit does literature | LOW |
| **General LLMs (GPT, Claude)** | ADJACENT | Everyone | General-purpose reasoning | API pricing | Cloud | Broad knowledge, fast iteration | Fabricate results, no tool execution, no provenance, no persistence | AASI: verification-first, tool execution, scientific memory | **MEDIUM** |

---

## Competitive Position Map

```
                    INVESTIGATION INTELLIGENCE
                    ↑
                    │
          AASI ●    │
                    │
                    │     ● AI Scientist
                    │
     PhysicsX ●     │           ● Elicit
                    │
  SimScale ●        │     ● Monolith
                    │
    Ansys ●    COMSOL ●    ● Neural Concept
                    │
   Siemens ●        │
                    │
  ──────────────────┼──────────────────→ ENGINEERING TOOL DEPTH
                    │
```

---

## Key Insight

**AASI has no direct competitor** that combines:
1. Autonomous scientific investigation loop
2. Aerospace-domain physics tools
3. Multi-fidelity evidence reconciliation
4. Scientific provenance and verification
5. Persistent scientific memory
6. BYOC compute architecture

The closest threats are:
- **SimScale** expanding into AI investigation (currently tool-only)
- **PhysicsX** adding investigation workflow (currently optimization-only)
- **General LLMs** improving at engineering tasks (but lacking tool execution and verification)

AASI's moat is the **complete cognitive loop with verification and provenance** — something that requires deep domain engineering, not just AI capabilities.
