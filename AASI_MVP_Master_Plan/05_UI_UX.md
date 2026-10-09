# AASI — MVP Scientific Workspace UX

## Principle

The workspace should feel like a scientific laboratory, not a generic AI chat app.

## Main flow

```text
QUESTION
 ↓
HYPOTHESES
 ↓
PLAN
 ↓
METHOD
 ↓
COMPUTE
 ↓
VERIFY
 ↓
COMPARE
 ↓
CONCLUSION
 ↓
NEXT EXPERIMENT
```

## Question

Large scientific prompt.

Suggested examples:
- aerodynamic analysis
- CFD investigation
- discrepancy analysis
- reproduction request

## Hypotheses

Each card contains:
- hypothesis
- evidence
- prediction
- test
- stage action

## Compute

If local runner exists:

```text
OpenFOAM detected
Version 13
Estimated runtime: ...
[RUN LOCALLY]
```

Otherwise:

```text
OpenFOAM not detected.
Reproducible Colab workflow prepared.
[OPEN IN COLAB]
[DOWNLOAD NOTEBOOK]
```

## Verification

Show individual checks and a final epistemic state.

## Comparison

Display analytical/database/surrogate/CFD/experiment values with explicit source labels.

## Discrepancy

Show:
- magnitude
- candidate causes
- evidence
- next test

## Next experiment

Explain why the experiment is useful, then provide:

`[STAGE EXPERIMENT]`

## Memory

Show validated and failed investigations. Failed cases remain searchable because negative evidence matters.

## Chat

Chat is secondary. It explains the investigation but should not replace the scientific workspace.
