"""
AASI Remote Compute Backend.

Generates remote HPC / cluster submission templates (Slurm, PBS, SSH commands)
for running simulation cases on institutional clusters or cloud nodes.
"""

from typing import Dict, Any
from backend.compute.models import ComputeRequest


class RemoteComputeBackend:
    """Generates Slurm/PBS batch scripts and SSH execution commands for remote clusters."""

    def generate_slurm_job_script(self, request: ComputeRequest, nodes: int = 1, ntasks: int = 16) -> str:
        """Generates a reproducible Slurm batch submission script."""
        return f"""#!/bin/bash
#SBATCH --job-name=aasi_{request.case_id}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={ntasks}
#SBATCH --time=04:00:00
#SBATCH --partition=standard
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

echo "=== AASI Remote HPC Job: {request.case_id} ==="
echo "Node: $(hostname)"
echo "Date: $(date)"

# 1. Load OpenFOAM environment
module purge
module load openfoam/v2312 || module load openfoam/11 || source /opt/openfoam/etc/bashrc

# 2. Decompose and run in parallel
cd aasi_{request.case_id}
chmod +x scripts/run.sh

echo "Starting mesh generation..."
blockMesh > log.blockMesh 2>&1

echo "Running solver with srun..."
srun simpleFoam -parallel > log.simpleFoam 2>&1

echo "Reconstructing solution..."
reconstructPar -latestTime > log.reconstruct 2>&1

echo "Job completed. Package logs for AASI upload."
tar -czvf results_{request.case_id}.tar.gz log.* postProcessing/
"""

    def generate_ssh_dispatch_command(self, request: ComputeRequest, remote_host: str = "cluster.nitk.ac.in", remote_user: str = "researcher") -> str:
        """Generates command to rsync case and trigger execution remotely."""
        return f"rsync -avz ./data/cases/{request.case_id} {remote_user}@{remote_host}:~/aasi_runs/ && ssh {remote_user}@{remote_host} 'cd ~/aasi_runs/{request.case_id} && sbatch slurm_job.sh'"
