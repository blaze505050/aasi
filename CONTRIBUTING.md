# Contributing to AASI

Thank you for your interest in contributing to AASI — Autonomous Aerospace Scientific Intelligence.

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### Local Development
```bash
# Clone the repository
git clone https://github.com/blaze505050/aasi.git
cd aasi

# Backend setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# Frontend setup
cd frontend && npm install && cd ..

# Run the unified launcher
python run_aasi.py
```

### Running Tests
```bash
# Full backend test suite (948+ tests)
.venv/bin/python -m pytest tests/ -v

# Frontend type checking
cd frontend && npx tsc --noEmit
```

## Scientific Code Review Standards

All contributions modifying physics, validation, or epistemic classification modules **must** follow the [scientific-code-review](.agents/skills/scientific-code-review/SKILL.md) checklist:

1. **Physical Correctness:** All equations reference specific textbooks/papers. Units are explicit.
2. **Numerical Stability:** No unguarded division-by-zero. Floating-point comparisons use tolerances.
3. **Epistemic Classification:** Every output labeled with classification (`CALCULATED`, `PREDICTED`, etc.).
4. **Reproducibility:** Deterministic behavior verified. Random seeds documented.
5. **Data Integrity:** No geometry leakage between train/test splits.

## Anti-Fabrication Rule

**CRITICAL:** AASI enforces an absolute anti-fabrication doctrine:

- Never fabricate computation results or benchmark numbers
- Never label surrogate predictions as "experimental" or "validated"
- Never claim capabilities that don't exist
- Every displayed data point must come from actual computation
- Panel solver results are `VERIFIED_PANEL_VISCOUS`, not "CFD"

## Pull Request Guidelines

1. **Branch naming:** `feat/description`, `fix/description`, `docs/description`
2. **Tests required:** All PRs must maintain 100% test pass rate
3. **No TODO in critical paths:** Remove or address all TODOs before merging
4. **Type safety:** Frontend changes must pass `npx tsc --noEmit`
5. **Documentation:** Update relevant docs if changing API contracts or physics

## Code of Conduct

Be respectful, constructive, and scientifically honest. Aerospace engineering demands rigor — bring that same standard to code reviews and discussions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
