# OpenFOAM Simulation Case: CASE-CAND-001
Airfoil: NACA 4415
AoA: 14.0 deg
Reynolds: 3000000.0
Kinematic Viscosity nu: 1.66666667e-05 m^2/s

## Execution Instructions
In a supported Linux or WSL2 OpenFOAM environment:
```bash
blockMesh
simpleFoam > log.simpleFoam 2>&1
```
