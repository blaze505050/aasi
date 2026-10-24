"""
AASI Benchmark Registry & Continuous Validation Framework.

Catalogs and executes published aerospace reference benchmarks across:
1. NACA 0012 (NASA TM-4083 / Abbott & von Doenhoff, thin airfoil theory slope, LTPT wind tunnel)
2. RAE 2822 Supercritical Airfoil (AGARD AR-138 Case 6 / Cook et al.)
3. Eppler E387 Low-Reynolds Section (NASA TM-4102 / McGhee et al. low-turbulence tunnel)
4. ONERA M6 3D Transonic/Subsonic Wing (AGARD AR-138 / Schmitt & Charpin)

Enforces strict CI validation gates: any benchmark whose error exceeds published tolerances
fails the verification gate.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.modules.base import (
    BenchmarkCase,
    BenchmarkEvaluation,
    FidelityLevel,
    ProblemModule,
    compute_sha256_provenance,
)
from backend.modules.airfoil_2d import Airfoil2DModule
from backend.modules.vlm_3d import VLM3DModule


class ModuleBenchmarkReport(BaseModel):
    module_id: str
    problem_id: int
    module_name: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    all_passed: bool
    evaluations: List[BenchmarkEvaluation]


class PlatformValidationSuiteReport(BaseModel):
    timestamp_utc: str
    suite_id: str
    total_modules: int
    total_benchmark_cases: int
    total_passed: int
    total_failed: int
    overall_status: str  # "ALL_BENCHMARKS_PASSED" | "BENCHMARK_REGRESSION_DETECTED"
    provenance_hash: str
    modules: Dict[str, ModuleBenchmarkReport]


class BenchmarkRegistry:
    """
    Central registry for aerospace validation reference benchmarks across all AASI modules.
    """

    def __init__(self):
        self._modules: Dict[str, ProblemModule] = {}
        # Register default Tier 1 modules
        self.register_module(Airfoil2DModule())
        self.register_module(VLM3DModule())

    def register_module(self, module: ProblemModule) -> None:
        """Registers a problem module in the platform benchmark suite."""
        self._modules[module.module_id] = module

    def get_module(self, module_id: str) -> Optional[ProblemModule]:
        return self._modules.get(module_id)

    def list_modules(self) -> List[Dict[str, Any]]:
        return [
            {
                "module_id": m.module_id,
                "problem_id": m.problem_id,
                "name": m.name,
                "tier": m.tier,
                "description": m.description,
                "benchmark_count": len(m.benchmarks()),
                "fidelities": [f.value for f in m.supported_fidelities],
            }
            for m in self._modules.values()
        ]

    def list_all_benchmarks(self) -> List[Dict[str, Any]]:
        """Returns flat list of all registered benchmark cases with citations."""
        cases = []
        for mod in self._modules.values():
            for b in mod.benchmarks():
                cases.append({
                    "module_id": mod.module_id,
                    "problem_id": mod.problem_id,
                    "case_id": b.case_id,
                    "name": b.name,
                    "reference_source": b.reference_source,
                    "citation": b.citation,
                    "expected_outputs": b.expected_outputs,
                    "tolerances": b.tolerances,
                    "regime": b.regime_description,
                })
        return cases

    def run_module_benchmarks(self, module_id: str) -> ModuleBenchmarkReport:
        mod = self._modules.get(module_id)
        if not mod:
            raise KeyError(f"Module '{module_id}' not found in BenchmarkRegistry.")

        evals = mod.verify_benchmarks()
        passed_count = sum(1 for e in evals if e.passed)
        failed_count = len(evals) - passed_count

        return ModuleBenchmarkReport(
            module_id=mod.module_id,
            problem_id=mod.problem_id,
            module_name=mod.name,
            total_cases=len(evals),
            passed_cases=passed_count,
            failed_cases=failed_count,
            all_passed=(failed_count == 0),
            evaluations=evals,
        )

    def run_all(self) -> PlatformValidationSuiteReport:
        """
        Executes continuous validation across all registered modules and benchmarks.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        reports: Dict[str, ModuleBenchmarkReport] = {}

        total_cases = 0
        total_passed = 0
        total_failed = 0

        for mod_id in self._modules:
            rep = self.run_module_benchmarks(mod_id)
            reports[mod_id] = rep
            total_cases += rep.total_cases
            total_passed += rep.passed_cases
            total_failed += rep.failed_cases

        suite_passed = (total_failed == 0)
        overall_status = "ALL_BENCHMARKS_PASSED" if suite_passed else "BENCHMARK_REGRESSION_DETECTED"

        prov_payload = {
            "timestamp_utc": now_utc,
            "total_cases": total_cases,
            "total_passed": total_passed,
            "overall_status": overall_status,
            "modules": {k: v.model_dump() for k, v in reports.items()},
        }
        prov_hash = compute_sha256_provenance(prov_payload)

        return PlatformValidationSuiteReport(
            timestamp_utc=now_utc,
            suite_id=f"VAL-SUITE-{prov_hash[:10].upper()}",
            total_modules=len(self._modules),
            total_benchmark_cases=total_cases,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_status=overall_status,
            provenance_hash=prov_hash,
            modules=reports,
        )


# Global singleton instance
benchmark_registry = BenchmarkRegistry()
