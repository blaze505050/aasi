# Cognitive Memory & Scientific Skill Architecture

## 1. 11 Memory Categories
The `CognitiveMemoryEngine` stores:
1. `FACT`: Verified aerodynamic constants and properties.
2. `EXPERIMENT`: Executed experimental/numerical studies.
3. `HYPOTHESIS`: Formulated conjectures and their outcomes.
4. `FAILURE`: Solver divergences, negative drag violations, or mesh failures.
5. `REPAIR`: Prescribed strategies to resolve specific numerical failures.
6. `TOOL`: Instrument capability and performance fingerprints.
7. `PHYSICS_RELATIONSHIP`: Invariant physical principles (e.g. D'Alembert's Paradox).
8. `MODEL_LIMITATION`: Identified boundaries of physical validity.
9. `DESIGN_PATTERN`: Proven simulation configuration templates.
10. `INVESTIGATION`: Complete historical investigation session summaries.
11. `SKILL`: Reusable engineering procedures.

## 2. Scientific Skills
A `ScientificSkill` is not a prompt. It is a reusable engineering procedure containing:
- `trigger_conditions`: Conditions activating the skill.
- `required_inputs`: Strict input parameter schema.
- `workflow_steps`: Ordered execution checklist.
- `tools_required`: Registered instruments invoked.
- `verification_checks`: Mandatory validation gates.
- `known_failure_modes`: Historical breakdown mechanisms.
- `repair_strategies`: Prescribed remediations.
