# Cognitive Benchmark Suite & Scientific Metrics

## 1. Metric Framework
The AASI Cognitive Benchmark measures scientific discipline, physical validity, and safety rather than superficial conversational fluency:

| Metric | Target | Measurement Method |
| :--- | :---: | :--- |
| **Problem Interpretation Accuracy** | 100% | Accuracy of regime classification across subsonic, transonic, and stall cases |
| **Hypothesis Falsifiability Rate** | 100% | Percentage of generated hypotheses possessing quantifiable numerical thresholds |
| **Hypothesis Diversity** | $\ge 2$ Competing | Verification that multiple mutually exclusive mechanisms are generated |
| **Fabrication Rate** | **0.0%** | Zero unverified numerical claims promoted to `VERIFIED` status |
| **Unsafe Action Rate** | **0.0%** | Severe post-stall or high transonic extrapolation halted before ungrounded execution |
| **Contradiction Diagnosis Accuracy** | 100% | Accurate identification of model-form differences (D'Alembert's paradox) |
| **Information-Gain Utility Validity** | 100% | Descending utility order strictly adhered to in candidate experiment ranking |

## 2. Benchmark Suites
- `tests/test_cognitive_engine.py`: Unit and integration testing of state transitions, world models, critic audits, and memory.
- `tests/test_cognitive_benchmark.py`: Systematic benchmark metrics enforcing 0% fabrication and 0% unsafe execution.
- `tests/test_cognitive_demonstrations.py`: Canonical 4-demonstration validation across cruise, deep stall, D'Alembert paradox, and Reynolds scaling.
