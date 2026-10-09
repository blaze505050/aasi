# The AASI Cognitive Loop

## 1. 16-Stage Investigation Lifecycle
The Cognitive Engine executes a disciplined 16-stage scientific loop:
1. **INTERPRET:** Parse question and identify physical continuum regime.
2. **MODEL:** Instantiate or update the `AerospaceWorldModel`.
3. **RETRIEVE:** Query persistent cognitive memory for prior investigations, failures, and repairs.
4. **HYPOTHESIZE:** Formulate competing, falsifiable physical hypotheses.
5. **CRITIQUE:** Adversarially audit hypotheses across 9 scientific dimensions.
6. **IDENTIFY UNKNOWNS:** Explicitly flag unmeasured variables.
7. **PLAN EXPERIMENTS:** Design discriminating experiments using information-gain logic.
8. **SELECT ACTION:** Select highest-utility experiment candidate.
9. **SELECT TOOL:** Bind experiment to an available instrument in the `ScientificToolRegistry`.
10. **EXECUTE:** Dispatch computation locally, to Colab, or stage for cluster execution.
11. **VERIFY:** Audit physical conservation, residual convergence ($< 10^{-4}$), and sign conventions.
12. **RECONCILE:** Diagnose multi-fidelity divergences and detect contradictions.
13. **UPDATE WORLD MODEL:** Promote verified results to assertions and refresh provenance hash.
14. **CONSOLIDATE MEMORY:** Store lessons, verified findings, or failure diagnoses in cognitive memory.
15. **DECIDE:** Check stopping criteria and formulate autonomous engineering determination.
16. **STOP OR CONTINUE:** Halt if target resolved, or iterate next cycle.

## 2. Halting Conditions
- `QUESTION_RESOLVED`
- `SUFFICIENT_EVIDENCE`
- `NO_SAFE_ACTION`
- `INSUFFICIENT_RESOURCES`
- `CONTRADICTION_REQUIRES_HUMAN`
- `INVESTIGATION_STALLED`
- `AWAITING_HUMAN_APPROVAL`
- `MAX_CYCLES_REACHED`
