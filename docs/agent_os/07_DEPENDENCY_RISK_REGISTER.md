# AASI 2.0 — 07. Dependency Risk Register

| Risk ID | Vulnerability / Threat | Probability | Impact | Mitigation Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | LLM Prompt Injection via External Web / Airfoil Docs | Medium | High | Strip prompt instructions; treat all external web text as untrusted string payload; enforce strict Pydantic schemas. | **MITIGATED** |
| **RISK-02** | Path Traversal via Model-Provided File Paths | Medium | Critical | Sandbox all file reads/writes to `workspace_root`; reject `..`, absolute paths outside workspace, and symlinks. | **MITIGATED** |
| **RISK-03** | Destructive Shell Execution by Autonomous Agents | Low | Critical | Strict allowlist of executables (`PERMITTED_EXECUTABLES`); block dangerous patterns (`rm -rf`, `format`, pipe-to-sh). | **MITIGATED** |
| **RISK-04** | Out-of-Memory (OOM) Crash on 8 GB Workstations | High | Medium | Continuous `ResourceMonitor` with minimum free RAM floor (200 MB); reject tasks when safe headroom is exceeded. | **MITIGATED** |
| **RISK-05** | GPL Contamination of Commercial Aerospace IP | Low | High | Subprocess and file contract boundary; no static or dynamic linking of GPL solvers into proprietary code. | **MITIGATED** |
| **RISK-06** | Epistemic Hallucination (Invented CFD/Experimental Results)| High | Critical | Absolute Anti-Fabrication Rule: fail-closed checks; planned != staged != executed != verified; SHA-256 Merkle hashes. | **MITIGATED** |
| **RISK-07** | Stale or Runaway Background Processes | Medium | Medium | Hard task timeouts via `asyncio.wait_for()`, process tracking, and emergency `KillSwitch` singleton. | **MITIGATED** |
| **RISK-08** | Browser Automation Side Effects (Unauthorized Actions) | Medium | High | Restrict browser tools to read-only retrieval; never auto-submit forms, financial transactions, or credential prompts. | **MITIGATED** |
