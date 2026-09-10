"""
AASI LLM Instruction-Tuning Dataset Generator & Schema.

Formats high-quality aerospace training and evaluation samples across:
- Engineering tool selection
- Unit reasoning and dimensional analysis
- Physics derivations & scientific QA
- Simulation workflow generation
- Error diagnosis and result interpretation
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import hashlib
from datetime import datetime, timezone


class InstructionSample(BaseModel):
    sample_id: str
    category: str  # "TOOL_SELECTION", "PHYSICS_DERIVATION", "SIMULATION_WORKFLOW", "UNIT_REASONING"
    instruction: str
    input_context: Optional[str] = None
    expected_output: str
    system_prompt: Optional[str] = None
    provenance_source: str
    checksum: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



class InstructionDatasetManager:
    """Manages curated aerospace instruction-tuning datasets and evaluation benchmarks."""

    def __init__(self):
        self.samples: List[InstructionSample] = []
        self._seed_benchmark_samples()

    def _seed_benchmark_samples(self):
        # 1. Tool Selection Benchmark
        s1 = "Calculate the orbital speed of a spacecraft in a 400 km circular orbit around Earth."
        o1 = "Execute Astropy circular_orbit tool with altitude_km=400.0, central_body='Earth'. Verified orbital velocity: ~7.67 km/s."
        self.add_sample(InstructionSample(
            sample_id="INST-TOOL-ORBIT-001",
            category="TOOL_SELECTION",
            instruction=s1,
            expected_output=o1,
            provenance_source="Astropy Two-Body Mechanics Ground Truth",
            checksum=hashlib.sha256(f"{s1}:{o1}".encode()).hexdigest()
        ))

        # 2. Unit Reasoning Benchmark
        s2 = "Convert thrust from 7,500 kilonewtons to pound-force (lbf)."
        o2 = "Execute Pint units tool with value=7500, from_unit='kN', to_unit='lbf'. Result: ~1,686,063 lbf."
        self.add_sample(InstructionSample(
            sample_id="INST-UNIT-THRUST-002",
            category="UNIT_REASONING",
            instruction=s2,
            expected_output=o2,
            provenance_source="Pint Standard Dimensional Conversion",
            checksum=hashlib.sha256(f"{s2}:{o2}".encode()).hexdigest()
        ))

        # 3. Simulation Workflow Benchmark
        s3 = "Create a steady RANS OpenFOAM simulation deck for NACA 0012 at Mach 0.15, Re=3e6, AoA=4°."
        o3 = "Invoke UserProvidedCaseGenerator to emit simpleFoam case with 0/U, 0/p, system/controlDict, k-omega SST closure, and 14-section README."
        self.add_sample(InstructionSample(
            sample_id="INST-SIM-OPENFOAM-003",
            category="SIMULATION_WORKFLOW",
            instruction=s3,
            expected_output=o3,
            provenance_source="OpenFOAM Aerodynamic Case Factory",
            checksum=hashlib.sha256(f"{s3}:{o3}".encode()).hexdigest()
        ))

    def add_sample(self, sample: InstructionSample) -> bool:
        self.samples.append(sample)
        return True

    def get_evaluation_set(self) -> List[InstructionSample]:
        return self.samples
