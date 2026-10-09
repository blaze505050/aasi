# AASI Go-to-Market Plan — Phase 31

> **Audit Date:** 2026-09-25

---

## GTM Strategy: Bottom-Up Technical Adoption

AASI should acquire customers through **technical credibility**, not marketing spend.

---

## Channel Strategy

### Phase 1: First 10 Customers (0-6 months)

| Channel | Tactic | Expected Yield |
|---|---|---|
| **Direct outreach** | Identify UAV/eVTOL startups doing active aerodynamic development | 3-5 customers |
| **University labs** | Offer free tier to aerospace research groups; convert PIs to paid | 2-3 customers |
| **Technical content** | Publish "How AASI conducted a real CFD investigation" with full provenance | Awareness + trust |
| **Open-source ecosystem** | Release panel solver + airfoil tools as open-source | Developer adoption |
| **Aerospace communities** | Post on CFD-Online, Reddit r/aerospace, r/CFD, LinkedIn aerospace groups | Pipeline |

### Phase 2: First 50 Customers (6-12 months)

| Channel | Tactic |
|---|---|
| **Conference presence** | AIAA SciTech, AIAA Aviation, SAE AeroTech (demo booth / talk) |
| **Research collaborations** | Partner with 2-3 university groups on published investigations |
| **Customer case studies** | Publish verified investigation results with customer permission |
| **Referral program** | Existing customers refer peers (engineering community is tight) |
| **Python ecosystem** | Publish `aasi-tools` Python package on PyPI |

### Phase 3: First 100 Customers (12-24 months)

| Channel | Tactic |
|---|---|
| **Product-led growth** | Self-serve signup with free tier → conversion |
| **Integration partnerships** | HPC providers, cloud compute platforms |
| **Enterprise pilot programs** | 30-day trials with R&D teams at mid-size companies |
| **Technical blog / newsletter** | Weekly aerospace investigation insights |
| **API documentation** | Enable developers to embed AASI into workflows |

---

## Customer Acquisition Approach

### Beachhead: UAV/eVTOL Startups

**Why they buy first:**
- Active aerodynamic development cycle
- Small team, can't hire dedicated CFD specialist
- SaaS-comfortable, fast procurement
- Need reproducible investigations for investors/certification
- Value speed over polish

**How to find them:**
- AngelList / Crunchbase: search for UAV, eVTOL, drone startups
- AIAA conference attendee lists
- LinkedIn: "aerodynamicist" OR "CFD engineer" at companies < 50 people
- Y Combinator / Techstars aerospace cohorts
- Defense innovation accelerators (DIU, AFWERX, SBIR)

**Sales motion:**
1. Identify company doing aerodynamic development
2. Reach out to CTO or head of aerodynamics
3. Offer 30-minute demo showing real investigation on their airfoil type
4. 14-day free trial on Professional tier
5. Convert to paid or Team tier

---

## Key Demo Scenarios (Phase 22/32)

1. **"Live Investigation"** — Enter "NACA 0012 drag at Re=500K, 8° AoA" → watch AASI build world model, generate hypotheses, run panel solver, verify, recommend CFD
2. **"Failed CFD Recovery"** — Show a diverged OpenFOAM case → AASI diagnoses root cause → generates repair plan
3. **"Contradicting Evidence"** — Compare panel method vs. CFD vs. experimental data → AASI explains discrepancy with physics
4. **"Engineering Memory"** — Ask about NACA 0012 after a previous investigation → AASI retrieves from memory with provenance
5. **"Investigation Report"** — Show generated report with assumptions, evidence chain, limitations

---

## Positioning for Different Channels

| Channel | Positioning |
|---|---|
| Technical blog | "How to run a reproducible aerodynamic investigation" |
| Conference talk | "Beyond simulation: autonomous scientific investigation for aerospace R&D" |
| University pitch | "Give your students a scientific brain for their CFD projects" |
| Startup pitch | "Your first aerodynamicist that never forgets and always shows its work" |
| Enterprise pitch | "The scientific operating system for your engineering toolchain" |

---

## Metrics to Track

| Metric | Target (6 months) |
|---|---|
| Free tier signups | 200+ |
| Free → Paid conversion | 5-10% |
| Paid customers | 10+ |
| Monthly revenue | $2,000+ |
| Customer retention (monthly) | >90% |
| Investigations per customer/month | 5+ |
| Time-to-first-value (new user) | <10 min |
