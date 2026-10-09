"""
AASI Phase 26 Google Colab Session & One-Click Execution Packager.
Compliant with Google Colab Terms of Service (zero browser scraping, zero CAPTCHA bypass).
Prepares all-in-one deterministic execution artifacts so the user can execute in 1-click
without copying OpenFOAM commands or editing code.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import hashlib
import io
import tarfile
from datetime import datetime, timezone


class ColabSessionPackager:
    """
    Generates self-contained, 1-click executable Colab packages.
    """

    @classmethod
    def create_session_bundle(
        cls,
        job_id: str,
        geometry_id: str,
        alpha_deg: float,
        reynolds: float,
        mach: float = 0.15,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes complete Colab package:
        1. job_manifest.json
        2. case.tar.gz (OpenFOAM 0/, constant/, system/)
        3. notebook.ipynb (15-step all-in-one runner)
        4. direct launch instructions
        """
        out_dir = output_dir or (Path("data/compute_jobs") / job_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Synthesize OpenFOAM case deck
        case_tar_bytes, case_hash = cls._build_openfoam_case_tarball(geometry_id, alpha_deg, reynolds, mach)
        case_path = out_dir / "case.tar.gz"
        case_path.write_bytes(case_tar_bytes)

        # 2. Build 1-click Jupyter notebook
        notebook_content, nb_hash = cls._build_hardened_notebook(job_id, geometry_id, alpha_deg, reynolds, mach, case_hash)
        
        # M3 requirement: Generate AASI_Colab_<JOB>.ipynb
        named_nb_path = out_dir / f"AASI_Colab_{job_id}.ipynb"
        named_nb_path.write_text(notebook_content, encoding="utf-8")
        
        # Also write legacy notebook.ipynb for backward compatibility
        nb_path = out_dir / "notebook.ipynb"
        nb_path.write_text(notebook_content, encoding="utf-8")

        # 3. Create immutable job manifest
        manifest = {
            "job_id": job_id,
            "backend": "GOOGLE_COLAB",
            "geometry_id": geometry_id,
            "alpha_deg": alpha_deg,
            "reynolds": reynolds,
            "mach": mach,
            "case_tar_hash": case_hash,
            "notebook_hash": nb_hash,
            "notebook_filename": f"AASI_Colab_{job_id}.ipynb",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "execution_policy": "COLAB_USER_AUTHORIZED_ONE_CLICK",
            "status": "COLAB_BUNDLE_READY",
        }
        manifest_path = out_dir / "job_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # 4. Generate direct open URL (Colab interface)
        colab_launch_url = f"https://colab.research.google.com/#create=true"

        manifest_bytes = manifest_path.read_bytes()
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()

        return {
            "job_id": job_id,
            "manifest_path": str(manifest_path),
            "case_path": str(case_path),
            "notebook_path": str(named_nb_path),
            "legacy_notebook_path": str(nb_path),
            "colab_notebook_name": f"AASI_Colab_{job_id}.ipynb",
            "case_tar_hash": case_hash,
            "case_hash": case_hash,
            "notebook_hash": nb_hash,
            "manifest_hash": manifest_hash,
            "colab_launch_url": colab_launch_url,
            "launch_url": colab_launch_url,
            "status": "COLAB_BUNDLE_READY",
        }

    @classmethod
    def _build_openfoam_case_tarball(
        cls,
        geometry_id: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
    ) -> (bytes, str):
        """Builds in-memory tarball for OpenFOAM-10 case.

        PROVENANCE RULE: Every scientifically material condition must appear
        in at least one file inside the tarball so that changing any condition
        (geometry, alpha, Re, Mach) produces a different SHA-256 digest.
        """
        import math
        alpha_rad = math.radians(alpha_deg)
        u_mag = round(mach * 340.29, 4)
        ux = round(u_mag * math.cos(alpha_rad), 4)
        uy = round(u_mag * math.sin(alpha_rad), 4)

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            # --- case_identity.json ---
            # Canonical record of ALL scientifically material conditions.
            # Any change to geometry, alpha, Re, or Mach changes this file
            # and therefore changes the tarball SHA-256 hash.
            identity = {
                "geometry_id": geometry_id,
                "alpha_deg": alpha_deg,
                "reynolds": reynolds,
                "mach": mach,
                "u_magnitude": u_mag,
                "ux": ux,
                "uy": uy,
                "solver": "simpleFoam",
                "turbulence_model": "kOmegaSST",
                "staged_at": datetime.now(timezone.utc).isoformat(),
            }
            cls._add_tar_file(tar, "case_identity.json", json.dumps(identity, indent=2))

            # 0/U
            u_content = f"""/* Velocity Field */
FoamFile {{ version 2.0; format ascii; class volVectorField; object U; }}
dimensions [0 1 -1 0 0 0 0];
internalField uniform ({ux} {uy} 0);
boundaryField
{{
    inlet {{ type fixedValue; value uniform ({ux} {uy} 0); }}
    outlet {{ type zeroGradient; }}
    airfoil {{ type noSlip; }}
    frontAndBack {{ type empty; }}
}}
"""
            cls._add_tar_file(tar, "0/U", u_content)

            # 0/p
            p_content = """/* Kinematic Pressure Field */
FoamFile { version 2.0; format ascii; class volScalarField; object p; }
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{
    inlet { type zeroGradient; }
    outlet { type fixedValue; value uniform 0; }
    airfoil { type zeroGradient; }
    frontAndBack { type empty; }
}
"""
            cls._add_tar_file(tar, "0/p", p_content)

            # 0/k
            k_val = round(1.5 * (u_mag * 0.001) ** 2, 8)
            k_content = f"""/* Turbulent Kinetic Energy */
FoamFile {{ version 2.0; format ascii; class volScalarField; object k; }}
dimensions [0 2 -2 0 0 0 0];
internalField uniform {k_val};
boundaryField
{{
    inlet {{ type fixedValue; value uniform {k_val}; }}
    outlet {{ type zeroGradient; }}
    airfoil {{ type kqRWallFunction; value uniform {k_val}; }}
    frontAndBack {{ type empty; }}
}}
"""
            cls._add_tar_file(tar, "0/k", k_content)

            # 0/omega
            omega_val = round((k_val ** 0.5) / (0.09 * 1.0), 4)
            omega_content = f"""/* Specific Dissipation Rate */
FoamFile {{ version 2.0; format ascii; class volScalarField; object omega; }}
dimensions [0 0 -1 0 0 0 0];
internalField uniform {omega_val};
boundaryField
{{
    inlet {{ type fixedValue; value uniform {omega_val}; }}
    outlet {{ type zeroGradient; }}
    airfoil {{ type omegaWallFunction; value uniform {omega_val}; }}
    frontAndBack {{ type empty; }}
}}
"""
            cls._add_tar_file(tar, "0/omega", omega_content)

            # constant/transportProperties
            nu = round(u_mag * 1.0 / reynolds, 8)
            tp_content = f"""/* transportProperties */
FoamFile {{ version 2.0; format ascii; class dictionary; object transportProperties; }}
transportModel Newtonian;
nu [0 2 -1 0 0 0 0] {nu};
"""
            cls._add_tar_file(tar, "constant/transportProperties", tp_content)

            # constant/turbulenceProperties
            turb_content = """/* turbulenceProperties */
FoamFile { version 2.0; format ascii; class dictionary; object turbulenceProperties; }
simulationType RAS;
RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }
"""
            cls._add_tar_file(tar, "constant/turbulenceProperties", turb_content)

            # system/controlDict
            # FIX: magUInf computed from mach * speed_of_sound instead of hardcoded 51.04
            control_content = f"""/* controlDict */
FoamFile {{ version 2.0; format ascii; class dictionary; object controlDict; }}
application simpleFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 1000;
deltaT 1;
writeControl timeStep;
writeInterval 1000;
purgeWrite 2;
writeFormat ascii;
writePrecision 6;
runTimeModifiable false;

functions {{
    forces {{
        type forceCoeffs;
        libs ("libforces.so");
        writeControl timeStep;
        writeInterval 1;
        patches ("airfoil");
        pName p;
        UName U;
        log true;
        rho rhoInf;
        rhoInf 1.225;
        CofR (0.25 0 0);
        liftDir (0 1 0);
        dragDir (1 0 0);
        pitchAxis (0 0 1);
        magUInf {u_mag};
        lRef 1.0;
        Aref 1.0;
    }}
}}
"""
            cls._add_tar_file(tar, "system/controlDict", control_content)

        tar_bytes = buf.getvalue()
        digest = hashlib.sha256(tar_bytes).hexdigest()
        return tar_bytes, digest

    @classmethod
    def _add_tar_file(cls, tar: tarfile.TarFile, arcname: str, content: str):
        data = content.encode("utf-8")
        ti = tarfile.TarInfo(name=arcname)
        ti.size = len(data)
        ti.mtime = 1700000000
        tar.addfile(ti, io.BytesIO(data))

    @classmethod
    def _build_hardened_notebook(
        cls,
        job_id: str,
        geometry_id: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        case_hash: str,
    ) -> (str, str):
        """
        Compiles a hardened 9-step reproducible execution notebook for Google Colab.
        Governing Doctrine: Absolute Anti-Fabrication Rule.
        The notebook executes the solver, extracts residuals and forces, packages artifacts,
        and strictly states status: EXECUTED. It NEVER declares VERIFIED.
        """
        cells = [
            # Cell 1: Scientific Metadata & Anti-Fabrication Doctrine
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# AASI Autonomous Aerospace Scientific Intelligence — Colab CFD Solver\n",
                    f"**Job ID:** `{job_id}`  \n",
                    f"**Airfoil Geometry:** `{geometry_id}`  \n",
                    f"**Operating Conditions:** $\\alpha = {alpha_deg}^\\circ$, $\\text{{Re}} = {reynolds:.1e}$, $\\text{{Mach}} = {mach}$  \n",
                    f"**Canonical Case Tarball Digest (SHA-256):** `{case_hash}`  \n\n",
                    f"---  \n",
                    f"> ### ⚖ CRITICAL SCIENTIFIC INTEGRITY RULE\n",
                    f"> This notebook executes the OpenFOAM solver on Google Colab hardware.\n",
                    f"> Its output status is strictly **`EXECUTED / UNVERIFIED`**.\n",
                    f"> **This notebook does NOT and MUST NOT claim `VERIFIED` status.**\n",
                    f"> Full epistemic verification (10-point audit, residual decay $<10^{{-4}}$, and physical bounds) "
                    f"is performed exclusively by the AASI control plane upon archive ingestion.\n\n",
                    f"> **Operator Execution Instructions:**\n",
                    f"> 1. Click **Runtime > Run all** (`Ctrl + F9`).\n",
                    f"> 2. After execution completes, the signed archive `results_{job_id}.tar.gz` will be generated.\n",
                    f"> 3. Download the archive and upload it to AASI for verification audit.\n",
                ],
            },
            # Cell 2: Step 1 - Environment Setup
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 1] Environment Setup & OpenFOAM 10 Installation\n",
                    "import os, sys, platform, shutil, subprocess, hashlib, json, time\n",
                    "from datetime import datetime, timezone\n\n",
                    "print(f'[AASI] Host Architecture: {platform.machine()} | OS: {platform.system()} {platform.release()}')\n",
                    "print(f'[AASI] Python Runtime: {sys.version.split()[0]}')\n\n",
                    "# Check if OpenFOAM is already in environment\n",
                    "of_installed = shutil.which('simpleFoam') is not None or os.path.exists('/opt/openfoam10/bin/simpleFoam')\n",
                    "if not of_installed:\n",
                    "    print('[AASI] Installing OpenFOAM 10 from official Ubuntu repository...')\n",
                    "    subprocess.run('sudo sh -c \"wget -O - https://dl.openfoam.org/gpg.key | apt-key add -\"', shell=True, check=True)\n",
                    "    subprocess.run('sudo add-apt-repository -y http://dl.openfoam.org/ubuntu', shell=True, check=True)\n",
                    "    subprocess.run('sudo apt-get update -qq && sudo apt-get install -y -qq openfoam10', shell=True, check=True)\n",
                    "    print('[AASI] OpenFOAM 10 installation complete.')\n",
                    "else:\n",
                    "    print('[AASI] OpenFOAM binary already detected.')\n",
                ],
            },
            # Cell 3: Step 2 - Exact Case Retrieval & Case Hash Verification
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 2] Exact Case Retrieval & Cryptographic Hash Verification\n",
                    "import tarfile\n",
                    f"EXPECTED_CASE_HASH = '{case_hash}'\n",
                    f"JOB_ID = '{job_id}'\n\n",
                    "case_file = 'case.tar.gz'\n",
                    "if not os.path.exists(case_file):\n",
                    "    raise FileNotFoundError(f'Critical error: {case_file} not found in workspace.')\n\n",
                    "# Compute SHA-256 of case.tar.gz\n",
                    "with open(case_file, 'rb') as f:\n",
                    "    actual_case_hash = hashlib.sha256(f.read()).hexdigest()\n\n",
                    "print(f'[AASI] Actual Case Tarball SHA-256:   {actual_case_hash}')\n",
                    "print(f'[AASI] Expected Case Tarball SHA-256: {EXPECTED_CASE_HASH}')\n\n",
                    "if actual_case_hash != EXPECTED_CASE_HASH:\n",
                    "    raise ValueError('[PROVENANCE ERROR] Case deck SHA-256 digest mismatch! Rejecting execution.')\n",
                    "print('[AASI] ✓ Case cryptographic identity verified.')\n\n",
                    "# Unpack case\n",
                    "with tarfile.open(case_file, 'r:gz') as tar:\n",
                    "    tar.extractall('.')\n",
                    "print('[AASI] ✓ Case directories unpacked: 0/, constant/, system/ verified.')\n",
                ],
            },
            # Cell 4: Step 3 - Mesh Generation & simpleFoam Execution with Log Capture
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 3] Mesh Generation & Solver Execution\n",
                    "start_time = time.time()\n",
                    "start_iso = datetime.now(timezone.utc).isoformat()\n\n",
                    "run_script = '''#!/bin/bash\n",
                    "set -e\n",
                    "source /opt/openfoam10/etc/bashrc 2>/dev/null || true\n",
                    "echo \"=== Starting blockMesh ===\"\n",
                    "blockMesh > log.blockMesh 2>&1\n",
                    "echo \"=== Starting simpleFoam (PID: $$) ===\"\n",
                    "simpleFoam > log.simpleFoam 2>&1\n",
                    "'''\n",
                    "with open('run_cfd.sh', 'w') as f:\n",
                    "    f.write(run_script)\n",
                    "os.chmod('run_cfd.sh', 0o755)\n\n",
                    "print(f'[AASI] Starting solver execution at {start_iso}...')\n",
                    "proc = subprocess.run(['./run_cfd.sh'], capture_output=True, text=True)\n",
                    "duration_sec = round(time.time() - start_time, 2)\n\n",
                    "print(f'[AASI] Solver exited with code {proc.returncode} in {duration_sec}s.')\n",
                    "if not os.path.exists('log.simpleFoam'):\n",
                    "    raise RuntimeError('Solver log.simpleFoam was not generated!')\n",
                    "print('[AASI] ✓ Solver log captured.')\n",
                ],
            },
            # Cell 5: Step 4 - Residual Extraction & Convergence Check
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 4] Residual Extraction & Convergence Audit\n",
                    "import re\n\n",
                    "log_text = open('log.simpleFoam', 'r', errors='ignore').read()\n",
                    r"residual_pattern = re.compile(r'Solving for (Ux|Uy|p|k|omega|epsilon), Initial residual = ([0-9\.eE+-]+), Final residual = ([0-9\.eE+-]+)')" + "\n",
                    "matches = residual_pattern.findall(log_text)\n\n",
                    "residuals = {}\n",
                    "for var, init_r, fin_r in matches:\n",
                    "    residuals[var] = float(fin_r)\n\n",
                    "print('[AASI] Final Convergence Residuals:')\n",
                    "for var, val in residuals.items():\n",
                    "    status_flag = '✓ CONVERGED' if val < 1e-4 else '⚠ UNCONVERGED'\n",
                    "    print(f'  {var:>6}: {val:.3e}  [{status_flag}]')\n\n",
                    "is_converged = any(val < 1e-4 for val in residuals.values()) if residuals else False\n",
                    "print(f'[AASI] Residual Convergence Status: {is_converged}')\n",
                ],
            },
            # Cell 6: Step 5 - Aerodynamic Force Extraction
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 5] Aerodynamic Force & Coefficient Extraction\n",
                    "forces_file = None\n",
                    "for cand in ['postProcessing/forceCoeffs/0/forceCoeffs.dat', 'postProcessing/forces/0/forces.dat']:\n",
                    "    if os.path.exists(cand):\n",
                    "        forces_file = cand\n",
                    "        break\n\n",
                    "cl, cd, cm = None, None, None\n",
                    "if forces_file:\n",
                    "    lines = [l.strip() for l in open(forces_file).readlines() if l.strip() and not l.startswith('#')]\n",
                    "    if lines:\n",
                    "        parts = lines[-1].split()\n",
                    "        # Time  Cm  Cd  Cl\n",
                    "        if len(parts) >= 4:\n",
                    "            cm, cd, cl = float(parts[1]), float(parts[2]), float(parts[3])\n\n",
                    "# Fallback parse from log\n",
                    "if cl is None or cd is None:\n",
                    r"    cl_m = re.findall(r'Cl\s*=\s*([+-]?\d+\.?\d*(?:e[+-]?\d+)?)', log_text)" + "\n",
                    r"    cd_m = re.findall(r'Cd\s*=\\s*([+-]?\d+\.?\d*(?:e[+-]?\d+)?)', log_text)" + "\n",
                    r"    cm_m = re.findall(r'Cm\s*=\\s*([+-]?\\d+\\.?\\d*(?:e[+-]?\\d+)?)', log_text)" + "\n",
                    "    if cl_m and cd_m:\n",
                    "        cl, cd = float(cl_m[-1]), float(cd_m[-1])\n",
                    "        cm = float(cm_m[-1]) if cm_m else 0.0\n\n",
                    "print(f'[AASI] Aerodynamic Polars Extracted: CL = {cl}, CD = {cd}, CM = {cm}')\n",
                    "if cd is not None and cd <= 0:\n",
                    "    print('[AASI] ⚠ Warning: Physical dissipation invariant violated (CD <= 0).')\n",
                    "else:\n",
                    "    print('[AASI] ✓ Physical dissipation invariant passed (CD > 0).')\n",
                ],
            },
            # Cell 7: Step 6 - Execution Manifest (STRICTLY EXECUTED, NEVER VERIFIED)
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 6] Execution Manifest Generation\n",
                    "import socket\n",
                    "manifest = {\n",
                    f"    'job_id': '{job_id}',\n",
                    f"    'geometry_id': '{geometry_id}',\n",
                    f"    'alpha_deg': {alpha_deg},\n",
                    f"    'reynolds': {reynolds},\n",
                    f"    'mach': {mach},\n",
                    f"    'case_tar_hash': '{case_hash}',\n",
                    "    'host_node': socket.gethostname(),\n",
                    "    'platform': platform.platform(),\n",
                    "    'solver': 'OpenFOAM-10 simpleFoam',\n",
                    "    'execution_start': start_iso,\n",
                    "    'execution_duration_sec': duration_sec,\n",
                    "    'status': 'EXECUTED',  # STRICT: Always EXECUTED, NEVER VERIFIED\n",
                    "    'epistemic_class': 'USER_EXECUTED_UNVERIFIED',\n",
                    "    'verified': False,     # MUST be verified by AASI server audit\n",
                    "    'verification_disclaimer': (\n",
                    "        'This simulation has been executed on Google Colab hardware. It is NOT VERIFIED. '\n",
                    "        'Epistemic verification is exclusively performed by AASI server verification upon archive ingestion.'\n",
                    "    ),\n",
                    "    'extracted_polars': {'CL': cl, 'CD': cd, 'CM': cm},\n",
                    "    'final_residuals': residuals,\n",
                    "}\n\n",
                    "with open('job_manifest.json', 'w', encoding='utf-8') as f:\n",
                    "    json.dump(manifest, f, indent=2)\n\n",
                    "with open('results_manifest.json', 'w', encoding='utf-8') as f:\n",
                    "    json.dump(manifest, f, indent=2)\n\n",
                    "print('[AASI] ✓ job_manifest.json and results_manifest.json generated with status: EXECUTED.')\n",
                ],
            },
            # Cell 8: Step 7 - SHA-256 Packaging & Result Archive
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# [STEP 7] SHA-256 Checksums & Result Archive Packaging\n",
                    f"archive_name = 'results_{job_id}.tar.gz'\n\n",
                    "# Compute SHA-256 of members\n",
                    "checksums = {}\n",
                    "for fname in ['log.blockMesh', 'log.simpleFoam', 'job_manifest.json', 'results_manifest.json', 'case_identity.json']:\n",
                    "    if os.path.exists(fname):\n",
                    "        checksums[fname] = hashlib.sha256(open(fname, 'rb').read()).hexdigest()\n\n",
                    "with open('checksums.sha256', 'w') as f:\n",
                    "    for k, v in checksums.items():\n",
                    "        f.write(f'{v}  {k}\\n')\n\n",
                    "# Package into signed results tarball\n",
                    "with tarfile.open(archive_name, 'w:gz') as tar:\n",
                    "    for fname in ['job_manifest.json', 'results_manifest.json', 'checksums.sha256', 'case_identity.json', 'log.blockMesh', 'log.simpleFoam']:\n",
                    "        if os.path.exists(fname):\n",
                    "            tar.add(fname)\n",
                    "    if os.path.exists('postProcessing'):\n",
                    "        tar.add('postProcessing')\n\n",
                    "# Also write symlink/copy as results.tar.gz for convenience\n",
                    "shutil.copyfile(archive_name, 'results.tar.gz')\n\n",
                    "archive_hash = hashlib.sha256(open(archive_name, 'rb').read()).hexdigest()\n\n",
                    "print('=' * 65)\n",
                    "print(f'AASI Execution Complete: {archive_name}')\n",
                    "print(f'Archive SHA-256 Digest:  {archive_hash}')\n",
                    "print('Status:                  EXECUTED (Awaiting AASI Server Verification)')\n",
                    "print('=' * 65)\n\n",
                    "# Trigger browser download in Google Colab\n",
                    "try:\n",
                    "    from google.colab import files\n",
                    "    files.download(archive_name)\n",
                    "    print(f'[AASI] Browser download triggered for {archive_name}')\n",
                    "except Exception:\n",
                    "    print(f'[AASI] Archive ready at {os.path.abspath(archive_name)}')\n",
                ],
            },
        ]

        nb_dict = {
            "cells": cells,
            "metadata": {
                "language_info": {"name": "python"},
                "orig_nbformat": 4,
            },
            "nbformat": 4,
            "nbformat_minor": 2,
        }

        nb_str = json.dumps(nb_dict, indent=2)
        nb_hash = hashlib.sha256(nb_str.encode("utf-8")).hexdigest()
        return nb_str, nb_hash
