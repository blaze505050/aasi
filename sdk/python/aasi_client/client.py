"""
AASI Client — High-Performance Aerospace Aerodynamics & ASME V&V 20 Certification SDK.
Provides zero-dependency HTTP interface to AASI physics surrogates, Navier-Stokes solvers,
and wind tunnel validation benchmarks.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List, Optional


class AASIClientError(Exception):
    """Base exception for AASI client errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AASIClient:
    """
    Programmatic Python client for Autonomous Aerospace Scientific Intelligence (AASI).
    
    Example:
    >>> from aasi_client import AASIClient
    >>> client = AASIClient(base_url="http://127.0.0.1:8000")
    >>> pred = client.predict(geometry="NACA 0012", mach=0.15, reynolds=3e6, aoa_deg=4.0)
    >>> print(f"CL: {pred['cl']:.4f}, CD: {pred['cd']:.5f}")
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        api_key: Optional[str] = None,
        org_id: str = "default",
        timeout_seconds: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.org_id = org_id
        self.timeout = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream_response: bool = False,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            url = f"{url}?{urllib.parse.urlencode(clean_params)}"

        headers = {
            "User-Agent": "aasi-client-python/0.3.0",
            "X-Organization-Id": self.org_id,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data_bytes = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if stream_response:
                    return resp.read()
                content = resp.read().decode("utf-8")
                if not content.strip():
                    return {}
                return json.loads(content)
        except urllib.error.HTTPError as e:
            raw_err = e.read().decode("utf-8", errors="replace")
            try:
                parsed_err = json.loads(raw_err)
            except Exception:
                parsed_err = {"detail": raw_err}
            raise AASIClientError(
                f"HTTP {e.code}: {parsed_err.get('detail', e.reason)}",
                status_code=e.code,
                details=parsed_err,
            ) from e
        except urllib.error.URLError as e:
            raise AASIClientError(f"Connection failed to {url}: {e.reason}") from e

    def health(self) -> Dict[str, Any]:
        """Check system health, runtime connectivity, and version status."""
        return self._request("GET", "/api/health")

    def predict(
        self,
        geometry: str = "NACA 0012",
        mach: float = 0.15,
        reynolds: float = 3_000_000.0,
        aoa_deg: float = 4.0,
    ) -> Dict[str, Any]:
        """
        Fast physics surrogate inference (<15ms) for aerodynamic force coefficients.
        Returns CL, CD, CM, and epistemic uncertainty bounds.
        """
        payload = {
            "geometry": geometry,
            "mach": mach,
            "reynolds": reynolds,
            "aoa_deg": aoa_deg,
        }
        return self._request("POST", "/api/physics/aerodynamics/predict", body=payload)

    def generate_polar(
        self,
        geometry: str = "NACA 0012",
        alpha_min: float = -6.0,
        alpha_max: float = 16.0,
        alpha_step: float = 1.0,
        reynolds_list: Optional[List[float]] = None,
        mach_list: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Execute multi-fidelity flight envelope sweep and compute stability derivatives.
        """
        payload = {
            "geometry": geometry,
            "alpha_min": alpha_min,
            "alpha_max": alpha_max,
            "alpha_step": alpha_step,
            "reynolds_list": reynolds_list or [3_000_000.0],
            "mach_list": mach_list or [0.15],
            "fidelity": "MULTI_FIDELITY",
        }
        return self._request("POST", "/api/aerodb/generate", body=payload)

    def get_experimental_benchmark(
        self,
        geometry: str = "NACA 0012",
        reynolds: Optional[float] = None,
        mach: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve ground-truth experimental wind tunnel polar (NASA Langley LTPT, AGARD, UIUC)
        with standard instrumentation uncertainty bands (+/- sigma).
        """
        params = {"reynolds": reynolds, "mach": mach}
        return self._request("GET", f"/api/aerodb/experimental/{urllib.parse.quote(geometry)}", params=params)

    def compare_against_wind_tunnel(
        self,
        geometry: str,
        predicted_points: List[Dict[str, float]],
        reynolds: Optional[float] = None,
        mach: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Validate predicted polar against experimental wind tunnel measurements
        under the ASME V&V 20-2009 standard.
        """
        payload = {
            "geometry": geometry,
            "reynolds": reynolds,
            "mach": mach,
            "predicted_points": predicted_points,
        }
        return self._request("POST", "/api/aerodb/experimental/compare", body=payload)

    def run_simulation(
        self,
        case_id: str,
        geometry: str = "NACA 0012",
        aoa_deg: float = 8.0,
        reynolds: float = 3_000_000.0,
        mach: float = 0.15,
        solver: str = "OpenFOAM",
        run_mode: str = "FULL_RUN",
        max_iterations: int = 1000,
        convergence_tolerance: float = 1e-6,
    ) -> Dict[str, Any]:
        """
        Stage and execute deterministic aerodynamic / OpenFOAM simulation case.
        """
        payload = {
            "case_id": case_id,
            "solver": solver,
            "geometry": geometry,
            "aoa_deg": aoa_deg,
            "reynolds": reynolds,
            "mach": mach,
            "run_mode": run_mode,
            "max_iterations": max_iterations,
            "convergence_tolerance": convergence_tolerance,
        }
        return self._request("POST", "/api/simulations", body=payload)

    def get_residuals(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieve iterative L2 residual convergence history (p, Ux, Uy, k, omega) for case.
        """
        return self._request("GET", f"/api/simulations/{case_id}/residuals")

    def download_asme_certificate(
        self,
        job_id: str,
        output_path: str = "asme_certification_dossier.pdf",
        geometry: Optional[str] = None,
        alpha: Optional[float] = None,
        reynolds: Optional[float] = None,
        mach: Optional[float] = None,
    ) -> str:
        """
        Generate and save a cryptographically sealed ASME V&V 20 flight certification PDF.
        """
        params = {
            "geometry": geometry,
            "alpha": alpha,
            "reynolds": reynolds,
            "mach": mach,
        }
        pdf_bytes = self._request("GET", f"/api/export/pdf/{job_id}", params=params, stream_response=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return output_path

    def verify_audit_trail(self) -> Dict[str, Any]:
        """
        Verify mathematical integrity of the SHA-256 cryptographic audit chain from genesis to head.
        """
        return self._request("POST", "/api/observability/audit-log/verify")

    def get_audit_log(self, limit: int = 50) -> Dict[str, Any]:
        """
        Query append-only cryptographic audit log records.
        """
        return self._request("GET", "/api/observability/audit-log", params={"org_id": self.org_id, "limit": limit})

    def run_autonomous_investigation(
        self,
        objective_prompt: str = "Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency.",
        airfoil: str = "NACA 4412",
        alpha_deg: float = 4.0,
        reynolds: float = 1_500_000.0,
        mach: float = 0.18,
        aspect_ratio: float = 8.0,
        auto_approve_human_gate: bool = True,
    ) -> Dict[str, Any]:
        """
        Dispatches end-to-end autonomous research investigation across the 8 specialist agents:
        Supervisory Orchestrator, Literature Intelligence, Aerospace Research,
        Physics & Mathematics, CFD Specialist, Scientific ML, Design Optimization, and Verification.
        """
        payload = {
            "objective_prompt": objective_prompt,
            "airfoil": airfoil,
            "alpha_deg": alpha_deg,
            "reynolds": reynolds,
            "mach": mach,
            "aspect_ratio": aspect_ratio,
            "auto_approve_human_gate": auto_approve_human_gate,
        }
        return self._request("POST", "/api/v1/investigation/flagship/run", body=payload)

    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        Retrieves the engineering Model Context Protocol (MCP) tool catalog.
        """
        return self._request("GET", "/api/v1/investigation/mcp/tools")

    def call_mcp_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Directly executes an engineering MCP tool via standard JSON-RPC interface.
        """
        payload = {
            "name": name,
            "arguments": arguments,
        }
        return self._request("POST", "/api/v1/investigation/mcp/call", body=payload)
