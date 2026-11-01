---
name: superpowers
description: Software engineering superpowers framework by Jesse Vincent (obra/superpowers). Enforces Test-Driven Development (TDD) red-green-refactor loops, systematic root-cause debugging, architecture brainstorming, and fail-safe incremental refactoring.
---

# Superpowers: Agentic Engineering Protocol

## 1. Test-Driven Development (TDD) Core Loop
1. **Write the Test First**: Before writing any implementation logic, author a failing test that expresses the exact behavioral specification, input contracts, and edge cases.
2. **Verify Failure (Red)**: Run the test suite and confirm it fails for the expected reason (e.g. `AssertionError`, `NotImplementedError`, or missing symbol).
3. **Write Minimal Code (Green)**: Write the simplest implementation that makes the test pass without adding speculative features or premature abstractions.
4. **Refactor & Hardening**: Clean up code quality, ensure strict typing (PEP 484 / TypeScript), eliminate duplication, and verify all regression tests still pass.
5. **Never Weaken Tests**: Never alter test assertions or thresholds to disguise an implementation defect.

## 2. Systematic Root-Cause Debugging
- **Isolate**: Formulate an explicit hypothesis before changing code. Reproduce in a standalone minimal test case.
- **Trace Boundaries**: Log or inspect at system boundaries (inputs, outputs, serialization, numeric precision).
- **Verify Assumptions**: Never assume environment variables, dependencies, or paths exist without programmatic validation.
- **Fail Closed**: In safety-critical software, any unhandled exception or ambiguous state must default to a secure, fail-closed refusal rather than silent corruption.

## 3. Architecture Brainstorming & Trade Studies
- Document decisions using Architectural Decision Records (ADRs).
- Compare candidate architectures against explicit criteria: latency, memory overhead, licensing obligations, determinism, and maintenance complexity.

