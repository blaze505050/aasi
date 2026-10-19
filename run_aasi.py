#!/usr/bin/env python3
"""
================================================================================
AASI — Autonomous Aerospace Scientific Intelligence
Unified Industrial System Launcher
================================================================================
Starts the FastAPI Backend and Next.js Frontend concurrently, validates health
endpoints, and launches the interactive engineering dashboard in your default browser.
================================================================================
"""

import os
import sys
import time
import socket
import signal
import subprocess
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

# ANSI colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def is_port_in_use(port: int) -> bool:
    """Check if a local TCP port is already open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_python_executable() -> str:
    """Detect virtual environment Python or fallback to current sys.executable."""
    if os.name == "nt":
        venv_py = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT_DIR / ".venv" / "bin" / "python"
    
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def wait_for_service(url: str, timeout: int = 30, desc: str = "Service") -> bool:
    """Poll an HTTP endpoint until responsive or timed out."""
    import urllib.request
    import urllib.error

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AASI-Launcher"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status in (200, 304):
                    return True
        except (urllib.error.URLError, ConnectionRefusedError, socket.timeout):
            pass
        time.sleep(0.5)
    return False


def main():
    print(f"\n{CYAN}{BOLD}" + "=" * 70)
    print("       AASI — AUTONOMOUS AEROSPACE SCIENTIFIC INTELLIGENCE")
    print("      Preliminary Aerodynamic Database & ASME V&V 20 Verification")
    print("=" * 70 + f"{RESET}\n")

    py_exe = get_python_executable()
    print(f"[{CYAN}INFO{RESET}] Python runtime: {py_exe}")
    print(f"[{CYAN}INFO{RESET}] Workspace root: {ROOT_DIR}")

    # Check port conflicts
    if is_port_in_use(BACKEND_PORT):
        print(f"[{YELLOW}WARN{RESET}] Port {BACKEND_PORT} is already in use. Ensure existing backend is closed or re-used.")
    if is_port_in_use(FRONTEND_PORT):
        print(f"[{YELLOW}WARN{RESET}] Port {FRONTEND_PORT} is already in use. Next.js may attempt an alternate port (e.g. 3001).")

    backend_proc = None
    frontend_proc = None

    try:
        # 1. Launch Backend
        print(f"\n[{CYAN}1/3{RESET}] Launching FastAPI Physics Backend (Port {BACKEND_PORT})...")
        backend_cmd = [
            py_exe, "-m", "uvicorn", "backend.main:app",
            "--host", "0.0.0.0",
            "--port", str(BACKEND_PORT),
            "--log-level", "info"
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Wait for backend health check
        backend_health_url = f"http://localhost:{BACKEND_PORT}/api/health"
        print(f"[{CYAN}INFO{RESET}] Awaiting backend initialization at {backend_health_url}...")
        if wait_for_service(backend_health_url, timeout=15, desc="Backend"):
            print(f"[{GREEN}OK{RESET}] Backend is healthy and ready.")
        else:
            print(f"[{YELLOW}WARN{RESET}] Backend took longer than expected to report healthy, continuing...")

        # 2. Launch Frontend
        print(f"\n[{CYAN}2/3{RESET}] Launching Next.js Engineering Dashboard (Port {FRONTEND_PORT})...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(FRONTEND_DIR),
            shell=(os.name == "nt")
        )

        # Wait for frontend
        frontend_url = f"http://localhost:{FRONTEND_PORT}"
        print(f"[{CYAN}INFO{RESET}] Awaiting frontend server at {frontend_url}...")
        if wait_for_service(frontend_url, timeout=25, desc="Frontend"):
            print(f"[{GREEN}OK{RESET}] Frontend is responsive.")
        else:
            print(f"[{YELLOW}WARN{RESET}] Frontend initialization continuing in background...")

        # 3. Open Browser
        print(f"\n[{CYAN}3/3{RESET}] Opening AASI Mission Control in default browser...")
        time.sleep(1.0)
        webbrowser.open(frontend_url)

        print(f"\n{GREEN}{BOLD}" + "=" * 70)
        print("   AASI INDUSTRIAL PLATFORM ACTIVE & OPERATIONAL")
        print("=" * 70 + f"{RESET}")
        print(f"  • Mission Control UI:   {CYAN}{frontend_url}{RESET}")
        print(f"  • OpenAPI Specification: {CYAN}http://localhost:{BACKEND_PORT}/docs{RESET}")
        print(f"  • Aero DB Engine:       {CYAN}http://localhost:{BACKEND_PORT}/api/aerodb/generate{RESET}")
        print(f"  • ASME V&V 20 Engine:   {CYAN}http://localhost:{BACKEND_PORT}/api/investigate/study/asme-vv20{RESET}")
        print(f"  • NASA-STD-7009B Dossier: {CYAN}http://localhost:{BACKEND_PORT}/api/investigate/{{job_id}}/dossier{RESET}")
        print(f"\n[{YELLOW}NOTE{RESET}] Press {BOLD}Ctrl+C{RESET} to cleanly terminate all services.\n")

        # Keep alive and pipe backend output
        while True:
            line = backend_proc.stdout.readline() if backend_proc.stdout else None
            if line:
                if "error" in line.lower() or "exception" in line.lower():
                    sys.stderr.write(f"[{RED}BACKEND{RESET}] {line}")
                elif "GET /" in line or "POST /" in line:
                    sys.stdout.write(f"[{CYAN}API{RESET}] {line}")
            time.sleep(0.05)

    except KeyboardInterrupt:
        print(f"\n\n[{YELLOW}SHUTDOWN{RESET}] Termination signal received. Stopping services...")

    finally:
        if backend_proc:
            print(f"[{CYAN}INFO{RESET}] Terminating FastAPI backend...")
            try:
                backend_proc.terminate()
                backend_proc.wait(timeout=3)
            except Exception:
                backend_proc.kill()

        if frontend_proc:
            print(f"[{CYAN}INFO{RESET}] Terminating Next.js frontend...")
            try:
                if os.name == "nt":
                    # On Windows, kill the whole process tree spawned by shell
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)], capture_output=True)
                else:
                    frontend_proc.terminate()
                    frontend_proc.wait(timeout=3)
            except Exception:
                try:
                    frontend_proc.kill()
                except Exception:
                    pass

        print(f"[{GREEN}DONE{RESET}] All AASI services successfully stopped.\n")


if __name__ == "__main__":
    main()
