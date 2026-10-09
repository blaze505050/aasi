# AASI Customer Segments — Phase 4

> **Audit Date:** 2026-09-25

---

## Customer Segment Analysis

### 1. Aerospace / UAV / eVTOL Startup (5-50 engineers)

| Attribute | Detail |
|---|---|
| **Buyer** | CTO, VP Engineering, Head of Aerodynamics |
| **Daily User** | Aerodynamics engineer, propulsion engineer |
| **Technical Champion** | Senior aerodynamicist who wants faster iteration |
| **Pain** | Cannot hire enough CFD specialists; junior engineers waste time on setup; no institutional memory when people leave; investors want faster design iteration |
| **Workflow** | Conceptual design → preliminary aero analysis → CFD validation → flight test correlation |
| **Current Tools** | XFOIL, OpenFOAM (self-managed), MATLAB, Python scripts, spreadsheets, occasional Ansys license |
| **Budget Behavior** | SaaS-comfortable ($200-$2,000/mo), usage-sensitive, value speed-to-decision |
| **Security** | Standard cloud SaaS acceptable |
| **Procurement** | Credit card or short-cycle PO, <2 weeks |
| **Expected Deployment** | Cloud SaaS |
| **Expected ROI** | 2-3x reduction in investigation time; fewer failed CFD runs; knowledge preservation |
| **Likely Objections** | "How do I know the results are correct?", "Can I use my own compute?", "What if I need 3D?" |

**★ BEACHHEAD CUSTOMER**

---

### 2. University Research Laboratory

| Attribute | Detail |
|---|---|
| **Buyer** | Principal Investigator (PI), Department Head |
| **Daily User** | PhD students, postdocs, research assistants |
| **Technical Champion** | PhD student frustrated with setting up CFD from scratch every project |
| **Pain** | Students reinvent the wheel; no reproducibility between projects; hard to compare results across methods; funding agencies want reproducible, verifiable results |
| **Workflow** | Literature review → hypothesis → simulation setup → run on lab cluster → post-processing → paper |
| **Current Tools** | OpenFOAM, SU2, MATLAB, Python, LaTeX, personal scripts |
| **Budget Behavior** | Grant-funded ($50-$500/mo), annual budget cycles, free tier essential for adoption |
| **Security** | Standard; some export-control sensitivity for defense-funded labs |
| **Procurement** | PO through department admin, 2-4 weeks |
| **Expected Deployment** | Cloud SaaS + Colab compute |
| **Expected ROI** | Faster time-to-publication; reproducibility; institutional memory across student generations |
| **Likely Objections** | "Can I get it for free?", "Does it work with my cluster?", "Can I cite AASI in papers?" |

---

### 3. Space Startup (5-30 engineers)

| Attribute | Detail |
|---|---|
| **Buyer** | CTO, Chief Engineer |
| **Daily User** | Propulsion, aerodynamics, trajectory engineers |
| **Technical Champion** | Systems engineer who needs cross-discipline analysis |
| **Pain** | Small team doing multi-discipline work; no CFD specialist on staff; need quick aerodynamic assessments for launch vehicles/re-entry |
| **Current Tools** | STK, GMAT, Python, occasional Ansys/COMSOL |
| **Budget Behavior** | VC-funded, $500-$3,000/mo acceptable if demonstrable ROI |
| **Procurement** | Fast, credit card |
| **Expected Deployment** | Cloud SaaS |

---

### 4. Aerospace R&D Team (within larger organization)

| Attribute | Detail |
|---|---|
| **Buyer** | R&D Director, Engineering Manager |
| **Daily User** | 5-20 simulation engineers |
| **Technical Champion** | Senior engineer frustrated with tool fragmentation |
| **Pain** | Tools don't talk to each other; tribal knowledge in senior engineers' heads; long simulation queues; no investigation documentation |
| **Current Tools** | Ansys, Siemens, in-house codes, Python, HPC cluster |
| **Budget Behavior** | Departmental budget, $2,000-$10,000/mo, requires business case |
| **Security** | Enterprise requirements (SSO, audit logs, data isolation) |
| **Procurement** | PO through procurement, 4-12 weeks |
| **Expected Deployment** | Cloud with private tenant, potentially on-prem |

---

### 5. Engineering Consultancy

| Attribute | Detail |
|---|---|
| **Buyer** | Managing Director, Technical Director |
| **Daily User** | Project engineers |
| **Technical Champion** | Senior consultant who wants consistent investigation quality |
| **Pain** | Quality depends on individual engineer; reports are inconsistent; knowledge walks out the door; clients want verifiable, auditable analysis |
| **Current Tools** | Mixed — Ansys, OpenFOAM, MATLAB, custom scripts |
| **Budget Behavior** | Per-project, $500-$5,000/mo, expense to client |
| **Expected Deployment** | Cloud SaaS |
| **Expected ROI** | Consistent report quality, faster turnaround, higher client trust |

---

### 6. Large Aerospace OEM / Defense

| Attribute | Detail |
|---|---|
| **Buyer** | VP Engineering, Head of Digital Engineering |
| **Daily User** | Engineering teams across programs |
| **Pain** | Tool fragmentation, knowledge loss, reproducibility for certification |
| **Current Tools** | Full suite — Ansys, Siemens, Dassault, in-house, HPC |
| **Budget Behavior** | Enterprise license, $50K-$500K+/yr |
| **Security** | ITAR, FedRAMP, air-gapped, SSO/SCIM, audit everything |
| **Procurement** | 6-18 months, legal review, security audit |
| **Expected Deployment** | Private cloud or on-prem only |

**★ ENTERPRISE EXPANSION CUSTOMER** (24+ months)

---

## Beachhead → Expansion Path

```
PHASE 1 (0-12 months):  UAV/eVTOL startups + University labs
                         ↓
PHASE 2 (12-24 months): Space startups + Consultancies + R&D teams
                         ↓
PHASE 3 (24+ months):   OEM / Defense via private deployment
```

The beachhead is chosen because:
- **Short sales cycle** (credit card / quick PO)
- **Technical buyers** who understand the value
- **SaaS-comfortable** (no on-prem requirement)
- **Tolerant of evolving product** (startup mindset)
- **Will provide feedback** actively
