---
name: google-antigravity-skills
description: Google Antigravity agentic skill patterns: Model Context Protocol (MCP) tool server integration, sidecar execution harnesses, autonomous agent coordination, and tool contracts.
---

# Google Antigravity Agentic Patterns

## 1. Model Context Protocol (MCP) Integration
- Expose engineering tools through JSON-RPC 2.0 compliant tool schemas.
- Declare explicit input validation types, boundaries, and descriptions for every parameter.
- Return structured outputs with `content` blocks (text/json/media) and metadata containing execution timestamps and provenance hashes.

## 2. Agentic Tool Contracts & Sandboxing
- Every tool call must be pre-validated against safety policies (CPU/RAM/disk budgets).
- Implement rate limiting, timeouts, and process sandboxing to protect host resources.
- Support deterministic execution with repeatable seeds and environment isolation.

## 3. Multi-Agent Task Delegation
- Decompose complex engineering workflows into specialized autonomous subagents.
- Pass state across agents using typed schemas and immutable event logs.
- Provide human-in-the-loop checkpoints for irreversible actions or safety-critical decisions.

