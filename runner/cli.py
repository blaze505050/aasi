"""
AASI Local Runner Command-Line Interface.
Usage:
    python -m runner.cli probe
    python -m runner.cli register --server http://127.0.0.1:8000
    python -m runner.cli info
"""

from __future__ import annotations

import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

from runner.agent import LocalRunnerAgent
from runner.detector.capabilities import HostCapabilityDetector


def cmd_probe(args: argparse.Namespace) -> None:
    """Probe and print local workstation compute/solver capabilities."""
    caps = HostCapabilityDetector.detect()
    print("=" * 60)
    print("AASI Local Workstation Capability Audit")
    print("=" * 60)
    print(f"Runner ID:          {caps.runner_id}")
    print(f"Host Name:          {caps.host_name} ({caps.os_platform})")
    print(f"WSL2 Environment:   {'YES' if caps.is_wsl2 else 'NO'}")
    print(f"Python Version:     {caps.python_version}")
    print(f"CPU Cores:          {caps.cpu_cores_logical} logical")
    print(f"RAM Total / Avail:  {caps.ram_total_gb:.1f} GB / {caps.ram_available_gb:.1f} GB")
    print(f"Disk Free:          {caps.disk_free_gb:.1f} GB")
    print(f"CUDA GPU:           {'YES (' + caps.cuda_device_name + ')' if caps.has_cuda else 'NO'}")
    print(f"MPI Runtime:        {'YES (' + str(caps.mpi_version) + ')' if caps.has_mpi else 'NO'}")
    print(f"OpenFOAM Detected:  {'YES (' + str(caps.openfoam_version) + ')' if caps.openfoam_available else 'NO'}")
    print(f"Supported Solvers:  {', '.join(caps.supported_solvers) if caps.supported_solvers else 'None'}")
    print("=" * 60)

    if args.json:
        print(json.dumps(caps.model_dump(), indent=2))


def cmd_register(args: argparse.Namespace) -> None:
    """Register runner with the AASI control plane."""
    agent = LocalRunnerAgent(workspace_root=Path(args.workspace))
    reg_payload = agent.get_registration_payload().model_dump()

    url = f"{args.server.rstrip('/')}/api/runner/register"
    req_data = json.dumps(reg_payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
            print(f"✓ Local Runner successfully registered with {args.server}:")
            print(json.dumps(resp_body, indent=2))
    except urllib.error.URLError as err:
        print(f"✗ Failed to connect to control plane at {url}: {err}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aasi-runner",
        description="AASI Local Runner — Host CFD Execution Agent",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # probe
    p_probe = subparsers.add_parser("probe", help="Probe workstation capabilities")
    p_probe.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p_probe.set_defaults(func=cmd_probe)

    # register
    p_reg = subparsers.add_parser("register", help="Register with AASI control plane")
    p_reg.add_argument("--server", default="http://127.0.0.1:8000", help="Control plane URL")
    p_reg.add_argument("--workspace", default="./aasi_runner_workspace", help="Fixed workspace directory")
    p_reg.set_defaults(func=cmd_register)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
