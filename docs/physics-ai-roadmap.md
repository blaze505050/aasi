# AASI Physics-AI Framework & Ecosystem Roadmap

## 1. The 5-Layer Physics-AI Strategy

AASI rejects the notion of training a monolithic "Aerospace AGI" from scratch. Instead, it employs a modular 5-layer hierarchy:

```text
┌─────────────────────────────────────────────────────────────┐
│ LAYER 5: SPECIALIZED PHYSICS-AI SURROGATES                  │
│ AeroSurrogateV1 (Deployed) • FNO / GraphNet (Scaffolds)     │
├─────────────────────────────────────────────────────────────┤
│ LAYER 4: AUTHENTIC MULTI-FIDELITY AERODYNAMIC DATASETS      │
│ UIUC Wind Tunnel • NASA TMR 2D RANS • User OpenFOAM Decks   │
├─────────────────────────────────────────────────────────────┤
│ LAYER 3: DETERMINISTIC SCIENTIFIC COMPUTATION & SOLVERS     │
│ SymPy (Exact Math) • Pint (Units) • OpenFOAM (CFD Decks)    │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2: TWO-STAGE RETRIEVAL-AUGMENTED GENERATION (RAG)     │
│ Dense Retrieval • Epistemic Authority Reranker • Citations  │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1: GENERAL OPEN-WEIGHT LANGUAGE MODEL                 │
│ Ollama Runtime (Llama 3 / Mistral / Qwen)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Evaluation of External Physics-AI Frameworks

In accordance with AASI's truth-preserving doctrine, external frameworks are evaluated based on verified code availability, licensing, and computational requirements rather than promotional claims. **None of these frameworks are claimed as integrated until verified code and test suites exist in the repository.**

| Framework | Primary Literature | Repository & License | Target Physics Domain | Hardware Constraints | Integration Status in AASI |
|:---|:---|:---|:---|:---|:---:|
| **Fourier Neural Operators (FNO)** | Li et al., ICLR 2021 (*Fourier Neural Operator for Parametric PDEs*) | `neuraloperator/neuraloperator`<br>(MIT License) | Continuous 2D/3D pressure and velocity fields across mesh resolutions. | High VRAM GPU required for training ($\ge 16$ GB). | **SCAFFOLD** (`backend/physics/model_registry.py` defines graph structure; no weights on disk). |
| **MeshGraphNets** | Pfaff et al., ICML 2020 (*Learning Mesh-Based Simulation with Graph Networks*) | `deepmind/deepmind-research`<br>(Apache 2.0) | Arbitrary unstructured surface meshes; predicts node-level force vectors. | Multi-GPU cluster required for complex geometries; CPU inference is slow. | **SCAFFOLD** (`backend/physics/model_registry.py` architecture registered). |
| **DeepONet** | Lu et al., Nat. Mach. Intell. 2021 (*Learning nonlinear operators via DeepONet*) | `lululxvi/deepxde`<br>(LGPL / Apache 2.0) | Operator learning mapping input boundary functions to solution fields. | Manageable on moderate GPUs; limited out-of-distribution generalization. | **PLANNED** (Under evaluation for transient thermal/structural response). |
| **NVIDIA PhysicsNeMo / Modulus** | Hennigh et al., 2021 (*NVIDIA Modulus: Physics-ML Platform*) | `NVIDIA/modulus`<br>(Apache 2.0) | Industrial CFD surrogates, PINNs, and turbulent boundary layers. | Strictly requires NVIDIA CUDA GPUs with TensorRT; fails on CPU-only edge hosts. | **PLANNED FOR HPC** (Slurm job recipe generation only; absent on developer workstation). |
| **Physics-Informed Neural Networks (PINNs)** | Raissi et al., JCP 2019 (*Physics-informed neural networks*) | Open research implementations | Collocation-point PDE residual minimization without simulation data. | Extremely stiff optimization; prone to trivial/unphysical local minima in high-Re fluid flows. | **REJECTED FOR CFD** (Fails to converge on turbulent high-Reynolds Navier-Stokes; replaced by data-driven surrogates with ASME V&V 20 QC). |

---

## 3. Hardware-Aware Training Recipes

### A. Local Pure-CPU Training (Operational)
- **Model:** `AeroSurrogateV1`
- **Execution Script:** `backend/physics_ai/train_surrogate.py`
- **Runtime:** $\sim 2$ seconds on a 4-core CPU
- **Memory Footprint:** $< 150$ MB RAM
- **Output:** `aero_surrogate_v1.npz` and cryptographic sidecar manifest

### B. Remote Cloud / HPC Training (Slurm Recipe Generation)
- **Target Models:** 2D FNO and 3D MeshGraphNet
- **Workflow:**
  1. AASI exports normalized, leak-free training HDF5/NPZ datasets with SHA-256 manifests.
  2. AASI generates a reproducible Slurm job script (`run_training.slurm`) specifying GPU resource requirements (`--gpus=1`, `--mem=32G`).
  3. External cluster executes training; trained checkpoint is uploaded back to AASI for cryptographic ingestion and 4-gate promotion audit.
