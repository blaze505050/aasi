"""
AASI Phase 21: Concrete OpenFOAM Solver Runner.
Governing Rule: Absolute Anti-Fabrication Rule.
Executes OpenFOAM simulation when supported environment is present, or returns fail-closed USER_EXECUTED_REQUIRED.
"""

import math
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.cfd.case_validator import CFDCaseValidator
from backend.cfd.convergence import CFDConvergenceEvaluator
from backend.cfd.environment_probe import CFDEnvironmentProbe
from backend.cfd.force_parser import CFDForceParser
from backend.cfd.provenance import CFDProvenanceEngine
from backend.cfd.residual_parser import CFDResidualParser
from backend.cfd.result_ingestor import CFDResultIngestor
from backend.cfd.solver_interface import (
    CFDExecutionResult,
    CFDSolverAdapter,
    ConvergenceState,
    PhysicalValidationState,
    SolverMode,
)


class OpenFOAMRunner(CFDSolverAdapter):
    """
    Concrete runner for OpenFOAM simpleFoam incompressible RANS simulations.
    Strictly fail-closed: never fabricates execution, convergence, or aerodynamic outputs.
    """

    def __init__(self, default_output_dir: Optional[Path] = None):
        self.default_output_dir = default_output_dir or Path("data/cases/staged")
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

    def probe_environment(self) -> Dict[str, Any]:
        """Query host execution capabilities."""
        return CFDEnvironmentProbe.probe_all()

    def prepare_case(
        self,
        case_name: str,
        airfoil_name: str,
        coordinates: List[List[float]],
        alpha_deg: float,
        reynolds: float,
        mach: float = 0.15,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Synthesize a complete OpenFOAM simpleFoam case deck."""
        target_base = output_dir or self.default_output_dir
        case_dir = target_base / case_name
        case_dir.mkdir(parents=True, exist_ok=True)

        for subdir in ["0", "constant", "system"]:
            (case_dir / subdir).mkdir(exist_ok=True)

        # 1. geometry.dat
        geom_path = case_dir / "geometry.dat"
        with open(geom_path, "w", encoding="utf-8") as f:
            f.write(f"# Airfoil: {airfoil_name}, Points: {len(coordinates)}\n")
            for pt in coordinates:
                f.write(f"{pt[0]:.8f} {pt[1]:.8f}\n")

        # 2. Velocity vector from alpha
        rad = math.radians(alpha_deg)
        u_inf = 50.0  # nominal reference speed m/s
        ux = u_inf * math.cos(rad)
        uy = u_inf * math.sin(rad)
        nu = (u_inf * 1.0) / reynolds  # chord = 1.0 m

        # 3. system/controlDict
        (case_dir / "system/controlDict").write_text(
            f"""/* OpenFOAM 2.4 / 6 / 9 / v2212 simpleFoam controlDict */
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}}

application     simpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         1000;
deltaT          1;
writeControl    timeStep;
writeInterval   200;
purgeWrite      2;
writeFormat     ascii;
writePrecision  7;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
    forceCoeffs
    {{
        type            forceCoeffs;
        libs            ("libforces.so");
        writeControl    timeStep;
        writeInterval   1;
        patches         ("airfoil");
        pName           p;
        UName           U;
        log             true;
        rho             rhoInf;
        rhoInf          1.225;
        liftDir         ({-math.sin(rad):.6f} {math.cos(rad):.6f} 0);
        dragDir         ({math.cos(rad):.6f} {math.sin(rad):.6f} 0);
        CofR            (0.25 0 0);
        pitchAxis       (0 0 1);
        magUInf         {u_inf:.2f};
        lRef            1.0;
        Aref            1.0;
    }}
}}
""",
            encoding="utf-8",
        )

        # 4. system/fvSchemes
        (case_dir / "system/fvSchemes").write_text(
            """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}

ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
    grad(p)         Gauss linear;
    grad(U)         cellLimited Gauss linear 1;
}

divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    div(phi,k)      bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}
""",
            encoding="utf-8",
        )

        # 5. system/fvSolution
        (case_dir / "system/fvSolution").write_text(
            """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}

solvers
{
    p
    {
        solver          GAMG;
        tolerance       1e-06;
        relTol          0.01;
        smoother        GaussSeidel;
    }

    "(U|k|omega)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-06;
        relTol          0.05;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 2;
    consistent      yes;
    residualControl
    {
        p               1e-4;
        U               1e-4;
        k               1e-4;
        omega           1e-4;
    }
}

relaxationFactors
{
    equations
    {
        U               0.7;
        k               0.7;
        omega           0.7;
    }
    fields
    {
        p               0.3;
    }
}
""",
            encoding="utf-8",
        )

        # 6. constant/transportProperties
        (case_dir / "constant/transportProperties").write_text(
            f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      transportProperties;
}}

transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] {nu:.8e};
""",
            encoding="utf-8",
        )

        # 7. constant/turbulenceProperties
        (case_dir / "constant/turbulenceProperties").write_text(
            """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      turbulenceProperties;
}

simulationType  RAS;

RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
""",
            encoding="utf-8",
        )

        # 8. 0/U
        (case_dir / "0/U").write_text(
            f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "0";
    object      U;
}}

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform ({ux:.4f} {uy:.4f} 0);

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform ({ux:.4f} {uy:.4f} 0);
    }}
    outlet
    {{
        type            inletOutlet;
        inletValue      uniform (0 0 0);
        value           uniform ({ux:.4f} {uy:.4f} 0);
    }}
    topAndBottom
    {{
        type            slip;
    }}
    airfoil
    {{
        type            noSlip;
    }}
}}
""",
            encoding="utf-8",
        )

        # 9. 0/p
        (case_dir / "0/p").write_text(
            """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "0";
    object      p;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    inlet
    {
        type            zeroGradient;
    }
    outlet
    {
        type            fixedValue;
        value           uniform 0;
    }
    topAndBottom
    {
        type            slip;
    }
    airfoil
    {
        type            zeroGradient;
    }
}
""",
            encoding="utf-8",
        )

        # 10. Execution README instructions
        (case_dir / "README.md").write_text(
            f"""# OpenFOAM Simulation Case: {case_name}
Airfoil: {airfoil_name}
AoA: {alpha_deg} deg
Reynolds: {reynolds}
Kinematic Viscosity nu: {nu:.8e} m^2/s

## Execution Instructions
In a supported Linux or WSL2 OpenFOAM environment:
```bash
blockMesh
simpleFoam > log.simpleFoam 2>&1
```
""",
            encoding="utf-8",
        )

        return case_dir

    def validate_case(self, case_dir: Path) -> Dict[str, Any]:
        """Validate case dictionary and geometry."""
        return CFDCaseValidator.validate_case_directory(case_dir)

    def execute(self, case_dir: Path, timeout_sec: int = 600) -> CFDExecutionResult:
        """
        Execute simulation or return fail-closed degraded state.
        Never fabricates convergence or outputs.
        """
        case_path = Path(case_dir)
        env = self.probe_environment()
        mode = SolverMode(env["selected_mode"])

        run_id = f"CFD-RUN-{case_path.name}-{int(time.time())}"

        # If solver is not available on host, fail closed honestly
        if mode == SolverMode.MODE_E_NO_SOLVER:
            return CFDExecutionResult(
                run_id=run_id,
                case_name=case_path.name,
                case_dir=str(case_path),
                solver_mode=mode,
                solver_name="OpenFOAM_simpleFoam",
                solver_version="UNAVAILABLE_ON_HOST",
                exit_code=None,
                status="USER_EXECUTED_REQUIRED",
                convergence_state=ConvergenceState.NOT_RUN,
                physical_state=PhysicalValidationState.NOT_EVALUATED,
                execution_time_sec=0.0,
                provenance_hash=self.hash_case_provenance(case_path),
                error_message=(
                    "Host PATH lacks native simpleFoam.exe and WSL2 Ubuntu virtual disk is detached. "
                    "Case deck is staged for user or external runner execution."
                ),
            )

        # If Native Linux is available, execute via subprocess
        if mode == SolverMode.MODE_A_NATIVE_LINUX:
            start_t = time.time()
            log_file = case_path / "log.simpleFoam"
            try:
                with open(log_file, "w", encoding="utf-8") as out:
                    proc = subprocess.run(
                        ["simpleFoam"],
                        cwd=case_path,
                        stdout=out,
                        stderr=subprocess.STDOUT,
                        timeout=timeout_sec,
                    )
                elapsed = time.time() - start_t
                residuals = self.parse_residuals(case_path)
                forces = self.parse_forces(case_path)
                convergence = self.check_convergence(residuals, forces)
                physics = self.validate_physics({"forces": forces})

                return CFDExecutionResult(
                    run_id=run_id,
                    case_name=case_path.name,
                    case_dir=str(case_path),
                    solver_mode=mode,
                    solver_name="OpenFOAM_simpleFoam",
                    solver_version="Native_Linux",
                    exit_code=proc.returncode,
                    status="REAL_EXECUTED",
                    convergence_state=ConvergenceState(convergence["convergence_state"]),
                    physical_state=PhysicalValidationState(physics["state"]),
                    execution_time_sec=round(elapsed, 2),
                    residuals=residuals.get("residuals", {}),
                    forces=forces,
                    convergence_evidence=convergence.get("evidence", {}),
                    physical_checks=physics.get("checks", {}),
                    provenance_hash=self.hash_case_provenance(case_path),
                )
            except Exception as e:
                return CFDExecutionResult(
                    run_id=run_id,
                    case_name=case_path.name,
                    case_dir=str(case_path),
                    solver_mode=mode,
                    solver_name="OpenFOAM_simpleFoam",
                    solver_version="Native_Linux",
                    exit_code=-1,
                    status="SOLVER_FAILED",
                    convergence_state=ConvergenceState.SOLVER_FAILED,
                    physical_state=PhysicalValidationState.NOT_EVALUATED,
                    execution_time_sec=0.0,
                    error_message=str(e),
                )

        # Other modes (WSL2 / Docker) if detected active
        return CFDExecutionResult(
            run_id=run_id,
            case_name=case_path.name,
            case_dir=str(case_path),
            solver_mode=mode,
            solver_name="OpenFOAM_simpleFoam",
            solver_version=f"Mode_{mode.value}",
            exit_code=None,
            status="USER_EXECUTED_REQUIRED",
            convergence_state=ConvergenceState.NOT_RUN,
            physical_state=PhysicalValidationState.NOT_EVALUATED,
            execution_time_sec=0.0,
            error_message="Environment requires external daemon activation.",
        )

    def parse_residuals(self, case_dir: Path) -> Dict[str, Any]:
        """Parse residual logs."""
        log_path = Path(case_dir) / "log.simpleFoam"
        return CFDResidualParser.parse_log_file(log_path)

    def parse_forces(self, case_dir: Path) -> Dict[str, Any]:
        """Parse force coefficient histories."""
        return CFDForceParser.find_and_parse_forces(case_dir)

    def check_convergence(
        self, residual_data: Dict[str, Any], force_data: Dict[str, Any], exit_code: Optional[int] = 0
    ) -> Dict[str, Any]:
        """Check multi-criteria convergence."""
        return CFDConvergenceEvaluator.evaluate_convergence(residual_data, force_data, exit_code)

    def validate_physics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate physical sanity."""
        forces = result.get("forces", {})
        flow_condition = result.get("flow_condition", {})
        return CFDResultIngestor.validate_physics(forces, flow_condition)

    def hash_case_provenance(self, case_dir: Path) -> str:
        """Compute Merkle tree hash."""
        prov = CFDProvenanceEngine.compute_case_provenance(case_dir, "simpleFoam", "OpenFOAM")
        return prov["merkle_root"]
