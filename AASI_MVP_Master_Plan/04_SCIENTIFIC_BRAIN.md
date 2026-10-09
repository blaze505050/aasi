# AASI — Scientific Brain Specification

## Objective

Give AASI a real scientific reasoning architecture without pretending that a language model itself is a physics solver.

## 1. Reasoning

Responsible for:
- interpretation
- hypothesis generation
- causal explanations
- planning
- communication

## 2. Physics

Deterministic modules initially cover:
- aerodynamics
- fluid mechanics
- thermodynamics
- propulsion fundamentals
- orbital mechanics

Expand only after the aerodynamic core is reliable.

## 3. Dimensional analysis

Before execution:
- validate units
- check dimensions
- identify missing quantities
- reject impossible or ambiguous inputs

## 4. Physics sanity checks

Check:
- NaN/Inf
- numerical stability
- residual behavior
- physical bounds
- conservation where measurable
- boundary-condition consistency

These checks supplement, not replace, solver verification.

## 5. Hypothesis object

```text
HYPOTHESIS
Boundary-layer separation causes drag rise.

EVIDENCE
Existing trend + validated reference data.

PREDICTION
Wall shear decreases and separated region grows above a threshold.

TEST
Run selected AoA cases and inspect separation indicators.
```

## 6. Evidence states

Keep distinct:

`USER_ASSERTION`
`MODEL_GENERATED`
`ANALYTICAL`
`REFERENCE_DATA`
`SIMULATED`
`EXTERNALLY_EXECUTED`
`VERIFIED`
`EXPERIMENTAL`

Do not merge these categories.

## 7. Uncertainty

Represent uncertainty explicitly.

If it has not been established:

```json
{
  "value": 0.662,
  "uncertainty": null,
  "uncertainty_status": "NOT_ESTABLISHED"
}
```

Never invent error bars.

## 8. Contradiction engine

When evidence disagrees, quantify the difference and investigate:
- geometry
- Re/Mach
- transition
- turbulence model
- mesh
- boundary conditions
- measurement uncertainty
- implementation differences

Then propose discriminating experiments.

## 9. Scientific answer format

Every important answer should conceptually contain:

```text
CURRENT CONCLUSION
KNOWN
ASSUMED
UNKNOWN
CONFLICT
NEXT BEST EXPERIMENT
```

This is the core scientific behavior of AASI.
