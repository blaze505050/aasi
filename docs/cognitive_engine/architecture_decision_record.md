# AASI Cognitive Engine: Architecture Decision Record (ADR-001)

## Status
**ACCEPTED / RATIFIED**

## Context
AASI has completed its initial computational foundation (discrete vortex panel solvers, conformal 6-block C-grid OpenFOAM mesher, ASME V&V 20-2009 verification, NASA-STD-7009B dossier generator, and aerodynamic database exporters). The system must now undergo its next major architectural evolution: introducing the **AASI Cognitive Engine** to govern autonomous scientific reasoning, world-model maintenance, hypothesis generation, adversarial critique, experiment planning, and multi-fidelity evidence reconciliation.

---

## 10 Core Architectural Questions & Authoritative Decisions

### 1. What makes AASI different from a generic AI agent?
Generic AI agents (e.g., AutoGPT, generic ReAct loops) operate on loose semantic loops without conservation-law invariants, physical ontology, or rigorous verification gates. They treat tool outputs as unquestioned text strings and suffer from compounding hallucinations. 
AASI differs fundamentally because:
- **Physical Invariants & Truth Semantics:** `PLANNED != STAGED != EXECUTED != VERIFIED`. No output is promoted to verified evidence without passing formal numerical audits (residual convergence $< 10^{-4}$, conservation of mass/momentum, physical sign conventions).
- **Epistemic Trust Hierarchy:** AASI embeds an immutable hierarchy where empirical wind-tunnel data and audited Navier-Stokes CFD strictly outrank neural surrogates, which in turn strictly outrank LLM text assertions.

### 2. What makes it different from a chatbot?
A chatbot is a conversational interface optimized for linguistic plausibility and human pleasantry. It has no persistent world model, no notion of physical causality, and no capability to test its own assertions.
AASI is an **investigation machine**, not a conversationalist:
- Its primary artifact is a versioned, machine-readable **Aerospace World Model** and **Scientific Investigation Graph**, not chat dialogue.
- It proactively challenges premises, refuses ungrounded speculation, identifies unknown parameters, designs discriminating experiments, and halts safely when evidence is missing.

### 3. What makes it different from an AI coding agent?
AI coding agents (e.g., Devin, SWE-bench agents) are optimized for syntax correctness, test passing, and git diff generation within software codebases.
AASI does not optimize for software code generation; it optimizes for **scientific truth and aerodynamic discovery**:
- Its problem space consists of Navier-Stokes continuum mechanics, compressible shock physics, boundary layer separation, and flight envelope stability derivatives.
- Passing a software test is merely a prerequisite; AASI validates whether numerical discretization converges asymptotically ($R_{asymptotic} \approx 1.0$), whether physical drag divergence matches transonic compressibility theory, and whether turbulence model closure assumptions are valid.

### 4. What makes it different from an autonomous scientific research system?
Broad scientific research systems (e.g., Sakana AI Scientist, ChemOS) attempt unconstrained end-to-end literature crawling, paper writing, or chemical compound screening across arbitrary domains. They often produce trivial variations, reward-hack metrics, or generate synthetically convincing but physically ungrounded papers.
AASI is **domain-disciplined and safety-critical**:
- It does not generate vacuous research papers for publication volume.
- It produces verifiable flight databases, ASME V&V 20 uncertainty analyses, and NASA-STD-7009B airworthiness certification dossiers directly ingested into aerospace flight simulation and vehicle design toolchains.

### 5. What is uniquely aerospace-native about it?
AASI's entire cognitive ontology is structured around aerospace engineering principles:
- **Aerospace World Model:** Formally captures chord-normalized airfoil geometries ($c=1.0$), freestream Reynolds numbers ($Re$), Mach numbers ($M$), angles of attack ($\alpha$), boundary layer transition trips, and compressible shock regimes.
- **Flight Mechanics Formats:** Direct native integration with USAF DATCOM ($FLTCON, $OPTINS cards), NASA S/HABP ($TABLE records), and 6-DOF simulation matrices.
- **Aerodynamic Contradiction Engine:** Encodes domain-specific physical principles (e.g., D'Alembert's paradox in potential flow, transonic shock-induced separation, stall hysteresis, Squire-Young profile drag vs induced drag).

### 6. Which parts must be deterministic?
The following components are strictly deterministic and **never touch an LLM**:
1. Physics solvers (discrete vortex panel methods, Helmbold-Keune 3D corrections, Karman-Tsien compressibility, Squire-Young boundary layer).
2. Numerical verification audits (residual checks, mesh quality metrics, conservation audits).
3. ASME V&V 20-2009 calculations ($GCI_{fine}$, apparent order $p$, Richardson extrapolation).
4. Stability derivative extraction ($C_{L_\alpha}, \alpha_{0L}, C_{D0}, x_{ac}/c$).
5. File and format serialization (USAF DATCOM, NASA S/HABP, 6-DOF CSV).
6. Provenance hashing (SHA-256 Merkle-dag digests).

### 7. Which parts can use LLM reasoning?
LLM inference is restricted strictly to semantic interpretation and hypothesis synthesis:
1. Natural language query interpretation and extraction of flight regime parameters.
2. Generating competing physical hypotheses from multi-source literature context.
3. Formulating qualitative physical mechanisms ("shock-induced separation near 65% chord").
4. Synthesizing human-readable technical explanations from verified numerical data.

### 8. Which parts require external evidence?
No scientific claim can be accepted without external evidence from:
1. Validated physical wind-tunnel experiments (e.g., NACA Report 824, AGARD benchmarks).
2. Converged, residual-verified CFD simulations (OpenFOAM / SU2) run locally or on staged Colab/HPC clusters.
3. Peer-reviewed literature from authentic public repositories (NASA NTRS, AIAA, ESA).

### 9. What is the minimum viable cognitive architecture?
The MVP Cognitive Architecture consists of:
1. **`AerospaceWorldModel`:** Persistent, structured data model representing the problem, geometry, regime, hypotheses, evidence, and next actions.
2. **`CognitiveState`:** Explicit 17-state finite state machine.
3. **`HypothesisEngine` & `ScientificCritic`:** Dual-perspective generation and adversarial critique.
4. **`ExperimentPlanner` & Utility Engine:** Transparent multi-criteria heuristic ranking candidate experiments.
5. **`ScientificToolRegistry`:** Standard interface wrapping panel solvers, OpenFOAM, datasets, and literature.
6. **`ContradictionEngine`:** Detecting physical divergence across theoretical, numerical, and empirical tiers.
7. **`CognitiveMemory` & `ScientificSkill`:** Retaining verified lessons, failure modes, and reusable aerospace investigation workflows.
8. **`CognitiveOrchestrator`:** Bounded execution loop with strict stopping conditions and human approval gates.

### 10. What must NOT be built yet?
To prevent distraction and superficial complexity, the following are explicitly deferred:
- No humanoid persona, synthetic emotion, or conversational small-talk.
- No unbounded or infinite autonomous simulation loops.
- No decorative 3D neural brain visualizations or ungrounded "confidence percentage" animations.
- No complex multi-agent swarms with unconstrained inter-agent chat.
- No proprietary cloud GPU dependencies; all core cognitive logic must run locally on standard CPU hardware.
