"""OpenFOAM adapter for 2D aerodynamic RANS simulations (simpleFoam)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import BaseSolverAdapter
from ..artifacts import SimulationArtifactManager
from ..detector import solver_detector
from ..models import SimulationCase, SimulationManifest, SimulationRunMode, SolverInfo
from ..parsers import OpenFOAMLogParser
from ..sandbox import SimulationSecuritySandbox
from ..validators import SimulationCaseValidator


class OpenFOAMAdapter(BaseSolverAdapter):
    """Adapter for setting up, validating, and running OpenFOAM simpleFoam cases."""

    def __init__(
        self,
        artifact_manager: Optional[SimulationArtifactManager] = None,
        sandbox: Optional[SimulationSecuritySandbox] = None,
        validator: Optional[SimulationCaseValidator] = None,
        parser: Optional[OpenFOAMLogParser] = None,
    ):
        self.artifact_manager = artifact_manager or SimulationArtifactManager()
        self.sandbox = sandbox or SimulationSecuritySandbox()
        self.validator = validator or SimulationCaseValidator()
        self.parser = parser or OpenFOAMLogParser()

    def detect(self) -> SolverInfo:
        """Detect OpenFOAM binary on host Windows and WSL2."""
        return solver_detector.detect_openfoam()

    def generate_case_files(self, case: SimulationCase, target_dir: Path) -> Path:
        """Generate complete OpenFOAM case structure (0/, constant/, system/)."""
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "0").mkdir(exist_ok=True)
        (target_dir / "constant").mkdir(exist_ok=True)
        (target_dir / "system").mkdir(exist_ok=True)

        # Calculate freestream velocity components from Mach and AoA
        speed_of_sound = 340.294  # Sea level standard temperature (m/s)
        u_mag = case.mach * speed_of_sound
        rad = math.radians(case.aoa_deg)
        ux = u_mag * math.cos(rad)
        uy = u_mag * math.sin(rad)

        # 1. system/controlDict
        control_dict = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  | Case:     {case.case_id}                        |
\\*---------------------------------------------------------------------------*/
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
endTime         {case.max_iterations if case.run_mode == SimulationRunMode.FULL_RUN else (10 if case.run_mode == SimulationRunMode.VALIDATION_RUN else 0)};
deltaT          1;
writeControl    timeStep;
writeInterval   100;
purgeWrite      2;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
    forces
    {{
        type            forceCoeffs;
        libs            ("libforces.so");
        writeControl    timeStep;
        writeInterval   1;
        patches         (airfoil);
        rho             rhoInf;
        rhoInf          1.225;
        liftDir         (-{math.sin(rad):.6f} {math.cos(rad):.6f} 0);
        dragDir         ({math.cos(rad):.6f} {math.sin(rad):.6f} 0);
        CofR            (0.25 0 0);
        pitchAxis       (0 0 1);
        magUInf         {u_mag:.4f};
        lRef            1.0;
        Aref            1.0;
    }}
}}
"""
        (target_dir / "system" / "controlDict").write_text(control_dict, encoding="utf-8")

        # 2. system/fvSchemes
        fv_schemes = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}

ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; grad(U) cellLimited Gauss linear 1; }
divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    div(phi,k)      bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
"""
        (target_dir / "system" / "fvSchemes").write_text(fv_schemes, encoding="utf-8")

        # 3. system/fvSolution
        fv_solution = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}}

solvers
{{
    p
    {{
        solver          GAMG;
        tolerance       {case.convergence_tolerance};
        relTol          0.01;
        smoother        GaussSeidel;
    }}
    "(U|k|omega)"
    {{
        solver          smoothSolver;
        smoother        GaussSeidel;
        tolerance       {case.convergence_tolerance};
        relTol          0.01;
    }}
}}

SIMPLE
{{
    nNonOrthogonalCorrectors 1;
    consistent      yes;
    residualControl
    {{
        p               {case.convergence_tolerance};
        U               {case.convergence_tolerance};
        k               {case.convergence_tolerance};
        omega           {case.convergence_tolerance};
    }}
}}

relaxationFactors
{{
    equations
    {{
        U               0.7;
        k               0.7;
        omega           0.7;
    }}
    fields
    {{
        p               0.3;
    }}
}}
"""
        (target_dir / "system" / "fvSolution").write_text(fv_solution, encoding="utf-8")

        # 4. constant/turbulenceProperties
        turb_props = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      turbulenceProperties;
}}

simulationType  RAS;

RAS
{{
    RASModel        {"kOmegaSST" if "sst" in case.turbulence_model.lower() else "SpalartAllmaras"};
    turbulence      on;
    printCoeffs     on;
}}
"""
        (target_dir / "constant" / "turbulenceProperties").write_text(turb_props, encoding="utf-8")

        # 5. 0/U boundary condition
        u_file = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       volVectorField;
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
        type            zeroGradient;
    }}
    airfoil
    {{
        type            noSlip;
    }}
    frontAndBack
    {{
        type            empty;
    }}
}}
"""
        (target_dir / "0" / "U").write_text(u_file, encoding="utf-8")

        # 6. 0/p boundary condition
        p_file = """FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      p;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    inlet { type zeroGradient; }
    outlet { type fixedValue; value uniform 0; }
    airfoil { type zeroGradient; }
    frontAndBack { type empty; }
}
"""
        (target_dir / "0" / "p").write_text(p_file, encoding="utf-8")

        return target_dir

    def execute_run(
        self,
        case: SimulationCase,
        case_dir: Path,
        run_mode: SimulationRunMode,
    ) -> SimulationManifest:
        """Execute OpenFOAM case under sandbox security or generate dry-run verification."""
        # 1. Pre-flight case validation
        is_valid, validation_errors = self.validator.validate_case(case)
        if not is_valid:
            return self.artifact_manager.create_manifest(
                case=case,
                run_mode=run_mode,
                input_checksum="validation-failed",
                result_status=f"VALIDATION_ERROR: {'; '.join(validation_errors)}",
                logs=validation_errors,
            )

        # 2. Generate case dictionaries
        self.generate_case_files(case, case_dir)
        input_hash = self.artifact_manager.compute_directory_hash(case_dir)

        # 3. DRY_RUN Mode: Pure verification without expensive solver execution
        if run_mode == SimulationRunMode.DRY_RUN:
            manifest = self.artifact_manager.create_manifest(
                case=case,
                run_mode=run_mode,
                input_checksum=input_hash,
                is_converged=False,
                result_status="DRY_RUN_VERIFIED",
                logs=[
                    "Pre-flight case validation PASSED",
                    f"Generated OpenFOAM dictionaries in {case_dir}",
                    f"Freestream Mach {case.mach}, AoA {case.aoa_deg} deg",
                    f"Turbulence model: {case.turbulence_model}",
                    f"Input directory SHA-256: {input_hash}",
                    "DRY RUN completed successfully without solver execution.",
                ],
                result_files=[
                    str(case_dir / "system" / "controlDict"),
                    str(case_dir / "system" / "fvSchemes"),
                    str(case_dir / "system" / "fvSolution"),
                    str(case_dir / "0" / "U"),
                    str(case_dir / "0" / "p"),
                ],
            )
            self.artifact_manager.save_manifest(manifest, case_dir)
            return manifest

        # 4. For VALIDATION_RUN or FULL_RUN, check solver availability
        solver_status = self.detect()
        if not solver_status.is_available:
            manifest = self.artifact_manager.create_manifest(
                case=case,
                run_mode=run_mode,
                input_checksum=input_hash,
                result_status="SOLVER_UNAVAILABLE",
                logs=[
                    "Pre-flight case validation PASSED",
                    f"OpenFOAM solver is not executable on host system: {solver_status.detection_diagnostic}",
                    "To execute real solver runs, attach WSL2 disk or install OpenFOAM on Windows.",
                ],
            )
            self.artifact_manager.save_manifest(manifest, case_dir)
            return manifest

        # 5. If solver is available, execute under sandbox
        try:
            exe_cmd = "simpleFoam"
            args: List[str] = ["-case", str(case_dir)]
            ret_code, stdout_text, stderr_text = self.sandbox.execute_sandboxed(
                executable=exe_cmd,
                arguments=args,
                working_directory=case_dir,
                timeout_seconds=30.0,
            )

            residuals = self.parser.parse_residuals(stdout_text)
            cl, cd, cm = self.parser.parse_force_coefficients(stdout_text)
            is_conv = self.parser.check_convergence(residuals, case.convergence_tolerance)

            manifest = self.artifact_manager.create_manifest(
                case=case,
                run_mode=run_mode,
                input_checksum=input_hash,
                is_converged=is_conv,
                cl=cl,
                cd=cd,
                cm=cm,
                residuals=residuals,
                result_status="CONVERGED" if is_conv else "SOLVED_UNCONVERGED",
                logs=[stdout_text[-2000:] if len(stdout_text) > 2000 else stdout_text],
            )
            self.artifact_manager.save_manifest(manifest, case_dir)
            return manifest

        except Exception as exc:
            manifest = self.artifact_manager.create_manifest(
                case=case,
                run_mode=run_mode,
                input_checksum=input_hash,
                result_status=f"EXECUTION_ERROR: {str(exc)}",
                logs=[f"Error during sandboxed execution: {str(exc)}"],
            )
            self.artifact_manager.save_manifest(manifest, case_dir)
            return manifest
