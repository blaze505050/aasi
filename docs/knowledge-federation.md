# Aerospace Knowledge Federation & Dynamic Source Separation

## Overview
AASI Phase 5 implements a federated knowledge architecture integrating 15 core aerospace engineering and space science disciplines. The system operates on a dual-track temporal model:
1. **Curated Scientific Reference:** Peer-reviewed technical reports, archival papers (NACA, NASA NTRS, AIAA), and wind-tunnel validation benchmarks.
2. **Dynamic Current Events:** Real-time mission milestones, space weather conditions, orbital fleet statuses, and agency updates strictly separated and labeled with ISO timestamps to prevent hallucinations or temporal pollution.

---

## 15 Federated Scientific Disciplines
The federated source catalog covers:
1. **Fluid Dynamics & Aerodynamics:** Subsonic, transonic, supersonic, and hypersonic flow regimes.
2. **Propulsion Systems:** Chemical liquid/solid rockets, electric Hall thrusters, air-breathing turbofans, and scramjets.
3. **Orbital Mechanics & Astrodynamics:** Keplerian two-body propagation, perturbed orbits ($J_2$, atmospheric drag), and interplanetary trajectory design.
4. **Guidance, Navigation & Control (GNC):** Kalman filtering, reaction wheel momentum dumping, RCS thruster attitude control, and PID loops.
5. **Aerospace Structures & Materials:** High-temperature carbon-carbon composites, titanium/aluminum alloys, aeroelastic flutter, and finite element stress.
6. **Space Environments & Space Weather:** NOAA solar flare flux, geomagnetic storm indices ($Kp$), solar wind speed, and trapped radiation belts.
7. **Planetary Science & Entry, Descent, Landing (EDL):** Atmospheric deceleration, thermal protection systems (PICA-X), and supersonic parachutes.
8. **Avionics & Spacecraft Power:** Rad-hard microprocessors, photovoltaic solar arrays, and lithium-ion batteries.
9. **Systems Engineering & Mission Design:** Delta-V budgets, mass fraction margin, reliability analyses, and staging optimization.
10. **Aeroacoustics & Sonic Boom:** Launch pad acoustic suppression and supersonic overland signature mitigation.
11. **Aerothermodynamics & Hypersonics:** Shock layer chemical dissociation, catalytic surface recombination, and real-gas effects.
12. **Microgravity Sciences:** Fluid slosh dynamics and crystal growth in orbit.
13. **Space Domain Awareness (SDA):** Orbital debris cataloging, close-approach conjunction assessments, and tracking.
14. **Autonomous Flight Systems:** Autonomous terrain relative navigation (TRN) and onboard fault detection.
15. **Space Physiology & Life Support (ECLSS):** Cabin pressurization, oxygen generation, and closed-loop water recovery.

---

## Authentic Source Connectors & Access Protocols

### 1. NASA Technical Reports Server (NTRS) & NACA Archive
- **Scope:** 500,000+ public domain historical and current technical reports dating from 1917 to present.
- **Identifiers:** Validated via regex `r"^NASA-[A-Z]{2,4}(?:-[A-Z0-9]+)*-\d+"` and historical NACA series (`NACA-TR`, `NACA-TN`, `NACA-WR`).
- **Access Protocol:** Direct public REST query; verified cryptographic provenance with SHA-256 content hashes.

### 2. ISRO Public Registry & Archive
- **Honest Integration:** AASI does NOT claim fake real-time internal telemetry or non-existent automated APIs.
- **Registry:** Catalogs published scientific payloads (Chandrayaan-1/2/3, Mars Orbiter Mission, Aditya-L1) and public data releases via ISSDC.
- **Access Protocol:** Curated public scientific bulletins and mission whitepapers.

### 3. ESA Public Registry & Open Access Archive
- **Scope:** European Space Agency technical reports, Rosetta, Gaia, and Copernicus Earth observation publications.
- **Licensing:** Open Access / Creative Commons Attribution (CC-BY).

### 4. SpaceX & Commercial Space Adapter (Strict Guardrail)
- **Epistemic Principle:** AASI strictly refrains from claiming access to internal, confidential, or proprietary engineering design databases of SpaceX or other commercial aerospace firms.
- **Access Scope:** Strictly limited to public regulatory filings (FCC, FAA launch license environmental assessments), official public press kits, and webcast mission timelines.
- **Enforcement:** `CitationGuardrail` automatically intercepts any query claiming proprietary corporate access and issues an authentic provenance refusal notice.

---

## Temporal Separation: Current Events vs Scientific Knowledge
When answering aerospace queries, the system clearly separates foundational physics from transient operational events:

```
[SCIENTIFIC_REFERENCE]
NASA-TN-D-628: NACA 0012 experimental polar demonstrates linear lift slope dCl/da ≈ 0.108 deg⁻¹ up to stall at a ≈ 14°.

[CURRENT_INFORMATION | 2026-09-10T12:00:00Z]
ISRO Aditya-L1 operational update: Solar wind plasma ion spectrometer (SWIS) active at Sun-Earth L1 halo orbit; NOAA geomagnetic Kp index: 2 (Quiet).
```
Every event in the `CurrentInformationService` includes:
- `event_id`: Unique tracking key
- `timestamp`: ISO-8601 UTC timestamp
- `source_url`: Official agency bulletin URL
- `category`: `LAUNCH`, `MISSION_UPDATE`, `SPACE_WEATHER`, or `REGULATORY`
