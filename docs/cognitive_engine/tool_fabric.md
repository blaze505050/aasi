# Scientific Tool Fabric & MCP Architecture

## 1. Overview
The `ScientificToolRegistry` provides a unified, Model Context Protocol (MCP) compatible interface for all aerospace instruments, solvers, and databases.

## 2. Supported Instruments
1. **Discrete Vortex Panel Solver:** Katz & Plotkin 2D formulation with Helmbold thickness scaling, Karman-Tsien compressibility, and Schlichting-Squire-Young boundary layer drag in <3ms.
2. **OpenFOAM simpleFoam RANS Solver:** Conformal 6-block C-grid mesh generator with physical wall boundary patches (`(8 20 19 7)`, etc.) and $R_{grad}=15$ boundary layer resolution.
3. **ASME V&V 20-2009 Verifier:** Formal discretization error verifier computing $GCI_{fine}$, apparent order $p$, and Richardson extrapolation.
4. **Scientific Knowledge Catalog:** Abbott & von Doenhoff empirical wind-tunnel polars and NASA NTRS reports.

## 3. Execution Modes
- `LOCAL`: Native CPU execution.
- `COLAB`: Interactive cloud execution package for environments without local OpenFOAM.
- `REMOTE_HPC`: Slurm/PBS batch submission.
- `USER_EXECUTED`: Standalone case deck handed off to user workstation.
- `ANALYTICAL` / `SURROGATE` / `DATASET`: In-memory evaluation.
