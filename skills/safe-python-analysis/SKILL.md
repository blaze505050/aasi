---
name: safe-python-analysis
version: 2.0.0
description: AST-based static safety analysis of Python code before execution.
triggers:
  - "analyze script safety"
  - "inspect python script"
preconditions:
  - Target Python file exists
permitted_tools:
  - inspect_ast
required_inputs:
  file_path: string
output_schema:
  is_safe: boolean
  dangerous_imports: list
  syscall_attempts: list
resource_estimate:
  ram_mb: 32
  wall_time_seconds: 5
---

# Safe Python Analysis Skill

## Purpose
Parses Python source code into an abstract syntax tree (AST) to detect dangerous calls (`eval`, `exec`, `subprocess.Popen` with shell=True, raw socket creation) prior to execution.
