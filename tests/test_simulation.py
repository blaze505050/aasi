"""Tests for simulation execution fabric, solver detection, sandbox security, and log parsing."""

from pathlib import Path
import pytest
from backend.simulation.adapters.openfoam import OpenFOAMAdapter
from backend.simulation.detector import solver_detector
from backend.simulation.models import SimulationCase, SimulationRunMode
from backend.simulation.parsers import OpenFOAMLogParser
from backend.simulation.registry import solver_registry
from backend.simulation.runner import simulation_runner
from backend.simulation.sandbox import SecuritySandboxViolation, SimulationSecuritySandbox
from backend.simulation.validators import SimulationCaseValidator


class TestSolverDiscovery:
    """Test solver discovery and host inspection."""

    def test_detector_probes_all_solvers(self):
        detected = solver_detector.detect_all()
        assert "OpenFOAM" in detected
        assert "SU2" in detected
        assert "XFOIL" in detected
        assert "XFLR5" in detected

    def test_registry_returns_adapters(self):
        adapter = solver_registry.get_adapter("OpenFOAM")
        assert adapter is not None
        assert isinstance(adapter, OpenFOAMAdapter)

    def test_unknown_solver_returns_none(self):
        adapter = solver_registry.get_adapter("NonExistentSolver")
        assert adapter is None


class TestSimulationSecuritySandbox:
    """Test security sandbox safeguards against injection and path traversal."""

    @pytest.fixture
    def sandbox(self):
        return SimulationSecuritySandbox(default_timeout_seconds=5.0)

    def test_unallowlisted_executable_blocked(self, sandbox, tmp_path):
        with pytest.raises(SecuritySandboxViolation) as exc:
            sandbox.validate_command("powershell.exe", ["-Command", "echo hacked"], tmp_path)
        assert "approved simulation allowlist" in str(exc.value)

    def test_shell_chaining_blocked(self, sandbox, tmp_path):
        with pytest.raises(SecuritySandboxViolation) as exc:
            sandbox.validate_command("simpleFoam", ["-case", "case; rm -rf /"], tmp_path)
        assert "Dangerous pattern detected" in str(exc.value)

    def test_path_traversal_blocked(self, sandbox, tmp_path):
        with pytest.raises(SecuritySandboxViolation) as exc:
            sandbox.validate_command("simpleFoam", ["-case", "../../secret"], tmp_path)
        assert "Dangerous pattern detected" in str(exc.value)

    def test_system32_access_blocked(self, sandbox, tmp_path):
        with pytest.raises(SecuritySandboxViolation) as exc:
            sandbox.validate_command("simpleFoam", ["-case", "C:\\Windows\\System32"], tmp_path)
        assert "windows" in str(exc.value).lower() or "system" in str(exc.value).lower()


class TestOpenFOAMAdapterAndDryRun:
    """Test OpenFOAM case generation and dry run validation."""

    def test_openfoam_dry_run_generates_verified_manifest(self, tmp_path):
        adapter = OpenFOAMAdapter()
        case = SimulationCase(
            case_id="TEST-NACA0012-DRYRUN",
            solver="OpenFOAM",
            geometry="NACA 0012",
            mach=0.3,
            reynolds=500000.0,
            aoa_deg=8.0,
            turbulence_model="k-omega SST",
            mesh_cells=16384,
            run_mode=SimulationRunMode.DRY_RUN,
        )

        manifest = adapter.execute_run(case, tmp_path, SimulationRunMode.DRY_RUN)

        assert manifest.result_status == "DRY_RUN_VERIFIED"
        assert manifest.solver == "OpenFOAM"
        assert manifest.run_mode == SimulationRunMode.DRY_RUN
        assert (tmp_path / "system" / "controlDict").exists()
        assert (tmp_path / "system" / "fvSchemes").exists()
        assert (tmp_path / "0" / "U").exists()
        assert (tmp_path / f"EXP-{case.case_id}.manifest.json").exists()

    def test_case_validator_rejects_invalid_parameters(self):
        validator = SimulationCaseValidator()
        case = SimulationCase(
            case_id="INVALID-CASE",
            solver="OpenFOAM",
            geometry="NACA 0012",
            mach=-0.5,  # Negative Mach
            reynolds=-1000,  # Negative Reynolds
            aoa_deg=180.0,  # Extreme AoA
            turbulence_model="non_existent_model",
            mesh_cells=10,  # Inadequate cells
        )
        is_valid, errors = validator.validate_case(case)
        assert is_valid is False
        assert len(errors) >= 3


class TestLogParsers:
    """Test OpenFOAM residual extraction and force coefficient parsing."""

    def test_residual_parser(self):
        parser = OpenFOAMLogParser()
        log_sample = """
Time = 100
smoothSolver:  Solving for Ux, Initial residual = 0.0054, Final residual = 0.00012, No Iterations 5
smoothSolver:  Solving for Uy, Initial residual = 0.0042, Final residual = 0.00008, No Iterations 5
GAMG:  Solving for p, Initial residual = 0.0120, Final residual = 0.00004, No Iterations 12
smoothSolver:  Solving for k, Initial residual = 0.000008, Final residual = 0.000001, No Iterations 3
smoothSolver:  Solving for omega, Initial residual = 0.000007, Final residual = 0.000001, No Iterations 3
"""
        res = parser.parse_residuals(log_sample)
        assert res["Ux"] == 0.0054
        assert res["Uy"] == 0.0042
        assert res["p"] == 0.0120
        assert res["k"] == 0.000008
        assert res["omega"] == 0.000007

    def test_force_coefficients_parser(self):
        parser = OpenFOAMLogParser()
        log_sample = """
forces forces:
    sum of forces:
        pressure : (14.2 815.1 0)
        viscous  : (0.3 0.1 0)
        porous   : (0 0 0)
    coefficients:
        Cl = 0.8152
        Cd = 0.0145
        Cm = -0.0028
"""
        cl, cd, cm = parser.parse_force_coefficients(log_sample)
        assert cl == pytest.approx(0.8152, rel=1e-3)
        assert cd == pytest.approx(0.0145, rel=1e-3)
        assert cm == pytest.approx(-0.0028, rel=1e-3)
