# EUROCAE ED-324 / SAE ARP6983 Artificial Intelligence Assurance

**Standards**:
- EUROCAE WG-114 / SAE G-34: *Artificial Intelligence in Aviation* (ED-324 / ARP6983)
- EASA AI Roadmap 2.0 (Level 2B Human-AI Teaming & Level 3 SPO/eMCO)
- FAA Roadmap for Artificial Intelligence Safety Assurance

---

## 1. Assurance Levels & Scope

AASI establishes verification artifacts across three distinct regulatory tiers:
1. **System Level** (SAE ARP4754A / EUROCAE ED-79A): System safety assessment, hazard classification (Catastrophic to Minor), and allocation to software items.
2. **AI/ML Constituent Level** (EUROCAE ED-324 / SAE ARP6983): Requirements traceability, data quality requirements (DQR), model learning assurance, and operational design domain (ODD) specification.
3. **Item Level** (RTCA DO-178C / DO-254): Traditional deterministic wrapper verification, MC/DC structural coverage, and memory safety.

---

## 2. Operational Design Domain (ODD) Specifications

### A. System-Level ODD
- **Flight Regimes**: Subsonic cruise ($M = 0.15 - 0.78$), transonic boundary ($M = 0.78 - 0.85$), and low-speed approach/landing.
- **Atmospheric Boundaries**: Altitudes from 0 to 45,000 ft; temperatures conforming to US Standard Atmosphere 1976 $\pm 30^\circ$C.
- **Orbital Regimes**: Low Earth Orbit (LEO, 400 - 500 km, SpaDeX / BAS-01), Low Lunar Orbit (LLO, 100 km, Chandrayaan-4).

### B. Machine Learning Constituent ODD (MLCODD)
For vision-based landing (VBL), optical docking, and neural aerodynamic surrogates:
- **Spatial Resolution**: Normalized chord grid $128 \times 128$ to $512 \times 512$.
- **Reynolds Number Range**: $Re = 5 \times 10^5$ to $1 \times 10^7$.
- **Angle of Attack Envelope**: $-4.0^\circ \le \alpha \le +16.0^\circ$ (linear to pre-stall detachment).
- **Illumination Limits**: Minimum solar elevation angle $\ge 5^\circ$; thermal infrared optical range $8 - 12\ \mu\text{m}$.

---

## 3. Data Quality Requirements (DQR) Verification

| DQR Attribute | ED-324 Objective | AASI Verification Mechanism | Pass Metric |
| :--- | :--- | :--- | :--- |
| **Source Suitability** | Data must originate from calibrated wind-tunnels or validated DNS/RANS solvers. | AirfRANS OpenFOAM RANS dataset + NASA Langley LTPT / AGARD experimental wind-tunnel database. | Certified CFD/wind-tunnel pedigree. |
| **Completeness** | Full coverage of operational flight envelope without uncharacterized holes. | Latin Hypercube Sampling (LHS) across Mach, Reynolds, and AoA grid. | $100\%$ envelope grid coverage. |
| **Representativeness** | Training distribution must match the target airframe geometry and Reynolds scaling. | Geometry-Aware deformation (Geo-FNO) preserving physical surface camber and thickness. | Geometric error $< 0.5\%$. |
| **Accuracy & Precision** | Ground truth measurements must possess quantified uncertainty bounds. | ASME V&V 20 Richardson extrapolation GCI calculated for every mesh level. | Fine $GCI < 1.25\%$. |
| **Data Integrity** | Training pipelines and datasets must be protected against tampering. | SHA-256 Merkle root hashing of all raw training datasets and model weights. | Zero bit-rot / checksum match. |
