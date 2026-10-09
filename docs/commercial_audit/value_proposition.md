# AASI Value Proposition — Phase 5

> **Audit Date:** 2026-09-25

---

## Core Value Statement

> **AASI reduces the time and expertise required to conduct reproducible, verified aerospace engineering investigations — from engineering question to traceable evidence — while preserving institutional scientific memory.**

---

## Measurable Customer Outcomes

### Primary Value Metrics

| Metric | Description | Current Status |
|---|---|---|
| **Engineering hours saved per investigation** | Time from question to verified answer vs. manual process | TO BE VALIDATED — estimate 40-70% reduction for aerodynamic investigations |
| **Failed simulation rate reduction** | % of CFD runs that diverge before vs. after AASI | TO BE VALIDATED — diagnostic + repair engine should reduce retry cycles |
| **Time-to-first-value** | Minutes from account creation to first useful result | Current: ~5-10 min for panel solver results; CFD depends on compute |
| **Investigation reproducibility** | % of investigations that can be exactly reproduced | Architecture supports 100% — SHA-256 provenance on all evidence |
| **Knowledge reuse rate** | % of new investigations that benefit from prior memory | TO BE VALIDATED — scientific memory search is implemented |
| **Verification coverage** | % of results that undergo automated verification | 100% for CFD results (10-point audit); analytical results verified |

### Secondary Value Metrics

| Metric | Description | Status |
|---|---|---|
| Design variants explored per unit time | Number of parameter variations investigated | TO BE VALIDATED |
| Failure diagnosis time | Time to identify root cause of diverged simulation | TO BE VALIDATED — diagnostic engine is operational |
| Engineering onboarding time | Time for new engineer to produce first investigation | TO BE VALIDATED |
| Report generation time | Time from completed investigation to formatted report | TO BE VALIDATED — report generator exists |
| Simulation infrastructure utilization | % of compute budget used productively (vs. failed runs) | TO BE VALIDATED |

---

## Value Propositions by Customer Segment

### For UAV/eVTOL Startups

> **"Conduct aerodynamic investigations at the speed of your design cycle, not your CFD queue."**

- Reduce multi-step CFD investigation from days of manual interaction to hours of automated/staged operations
- Every result is verified and traceable — ready for design reviews
- Scientific memory preserves knowledge when engineers leave
- BYOC: use your existing compute; AASI adds the brain

### For University Research Labs

> **"From research question to reproducible, publishable investigation with full provenance."**

- Students can run structured investigations without deep CFD expertise
- Every assumption, hypothesis, and evidence item is traceable
- Investigations are reproducible across student generations
- Free/research tier for academic use

### For Engineering Consultancies

> **"Consistent investigation quality across your entire team, with audit-ready provenance."**

- Standardized investigation workflow eliminates quality variation
- Professional reports with clear separation of facts, assumptions, and interpretation
- Clients receive verifiable evidence chains, not just numbers

### For R&D Teams

> **"The scientific memory your engineering team has always needed."**

- Search past investigations by geometry, conditions, solver, quantity
- Reconcile conflicting results from different tools systematically
- Multi-fidelity evidence comparison with physics-aware discrepancy analysis

---

## What AASI Does NOT Promise

| Claim | Status |
|---|---|
| "Replaces engineers" | NO — augments engineering workflow |
| "Guarantees correct results" | NO — provides verified, traceable results with explicit limitations |
| "Faster than all simulation" | NO — fast for panel methods; CFD speed depends on user compute |
| "Certifiable for safety-critical" | NOT YET — informed by ASME V&V 20, but no regulatory certification |
| "Fabricated ROI numbers" | NO — all metrics marked TO BE VALIDATED until measured |
