# ASTM F3269-21 Run-Time Assurance (RTA) Compliance Matrix

**Standard**: ASTM F3269-21 — *Standard Practice for Methods to Safely Bound Behavior of Aircraft Systems Containing Complex Functions Using Run-Time Assurance*  
**System**: Assured Autonomous Space and Aviation Intelligence (AASI)  
**Applicability**: Civil Transport Aircraft (CS-25 eMCO), Regional SPO (CS-23), Unmanned Aircraft Systems, and Spacecraft Autonomous Rendezvous (SpaDeX, Chandrayaan-4, BAS-01).

---

## 1. Architectural Role Mapping

| ASTM F3269-21 Construct | AASI Architectural Subsystem | Implementation File | Verification Standard |
| :--- | :--- | :--- | :--- |
| **Larger System** | Integrated Aircraft Airframe / Spacecraft Bus (Actuators, Reaction Wheels, RCS, Flight Controls) | [`aasi_orbital_gnc.orbital_dynamics`](file:///c:/Users/ADITYA/Desktop/AASI/aasi-orbital-gnc/aasi_orbital_gnc/orbital_dynamics.py) | SAE ARP4754A / NASA-STD-8719.13 |
| **Complex Function** | Neural Operators (FourNetFlows, Geo-FNO, IUFNO) & 6-DOF Reinforcement Meta-Learning Docking Policy | [`aasi_aero_fno`](file:///c:/Users/ADITYA/Desktop/AASI/aasi-aero-fno/aasi_aero_fno), [`aasi_orbital_gnc.meta_rl_docking`](file:///c:/Users/ADITYA/Desktop/AASI/aasi-orbital-gnc/aasi_orbital_gnc/meta_rl_docking.py) | EUROCAE ED-324 / SAE ARP6983 |
| **Safety Monitor** | 2-of-3 Heterogeneous Evaluator Stack (Physics Kinematics + Envelope Governor + Approach Corridor) | [`aasi_constitution_rta.safety_monitor`](file:///c:/Users/ADITYA/Desktop/AASI/aasi-constitution-rta/aasi_constitution_rta/safety_monitor.py) | RTCA DO-178C DAL-A / DO-254 |
| **RTA Switch** | Deterministic Control Authority Switch & Latch | [`aasi_constitution_rta.safety_monitor.RTASwitch`](file:///c:/Users/ADITYA/Desktop/AASI/aasi-constitution-rta/aasi_constitution_rta/safety_monitor.py) | Hardware / Memory-Isolated Software Flag |
| **Recovery Function** | Deterministic Wings-Level 1g Trim / Retrograde Abort Pulse | [`aasi_constitution_rta.safety_monitor.RecoveryFunction`](file:///c:/Users/ADITYA/Desktop/AASI/aasi-constitution-rta/aasi_constitution_rta/safety_monitor.py) | RTCA DO-178C DAL-A Deterministic Rules |

---

## 2. ASTM F3269-21 Table 1 Data Integrity Enforcement

ASTM F3269-21 Table 1 requires that unassured data produced by the Complex Function must not contaminate the Safety Monitor's estimation of the Larger System's state:

```
[ Complex Function (AI/RL) ]  -->  [ Proposed Action ]
                                              |
                                              v
[ Independent Sensors (NavIC, IMU, LRF) ] -> [ Safety Monitor (2-of-3) ]
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
        [ Acceptable (>=2 votes) ]                            [ Vetoed (>=2 votes) ]
                   |                                                     |
                   v                                                     v
          [ Commanded to Bus ]                               [ RTA Switch Flips ]
                                                                         |
                                                                         v
                                                             [ Recovery Function Engaged ]
```

- **AASI Enforcement**: The `observe` phase of AASI's 5-stage loop enforces cross-sensor corroboration. The Safety Monitor computes its own independent state estimates directly from NavIC, IMU, and ISL sensors without passing through neural latent states.

---

## 3. Coded Failsafes Compliance Matrix (F-1 through F-19)

| Failsafe Code | Title | Trigger Condition | Severity | Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| **F-1** | Prompt Injection & Adversarial Semantics | Regex / semantic detection of prompt escape sequences | `CRITICAL` | Block input; trigger constitutional veto. |
| **F-2** | Command Token Forgery | Ed25519 digital signature mismatch or expired nonce | `FATAL` | Immediate rejection; command dropped. |
| **F-3** | GNSS / NavIC Spoofing | NavIC vs. IMU position divergence $> 50$ m or velocity $> 1.5$ m/s | `CRITICAL` | Discard GNSS; fallback to ISL + dead reckoning. |
| **F-4** | Sensor Cross-Corroboration Anomaly | Uncorroborated single-sensor anomaly (ASTM F3269 Table 1) | `CRITICAL` | Veto action; demand independent corroboration. |
| **F-5** | Resource Ceiling Violation | Power $> P_{\max}$ ($350$ W) or Temp $> 85^\circ$C | `CRITICAL` | Throttle compute; lock high-power payloads. |
| **F-6** | Two-Person Rule Authorization | High-consequence burn without dual-operator signature | `FATAL` | Inhibit actuator bus until second signature sealed. |
| **F-7** | Operator Console Compromise | Session IP alteration or replay attack token | `FATAL` | Invalidate session; lock operator console. |
| **F-8** | Flight Envelope Protection | $\alpha > \alpha_{\text{stall}}$ ($16^\circ$), $V > V_{ne}$ ($240$ m/s), or $n > 3.8$ g | `CRITICAL` | Engage Recovery Function; command trim pitch. |
| **F-9** | Actuator Slew Rate Exceedance | Slew rate $> 45^\circ$/s | `CRITICAL` | Clamp rate to maximum certified servo slew rate. |
| **F-10**| State Estimation Divergence | Kalman error covariance trace $\text{Tr}(P) > 0.25$ | `CRITICAL` | Re-initialize filter; halt aggressive maneuvers. |
| **F-11**| Approach Corridor Violation | Lateral offset exceeds $10^\circ$ cone or speed $> 15$ mm/s at latch | `CRITICAL` | Veto burn; engage V-bar safe-hold abort. |
| **F-12**| Thruster Minimum Impulse Bit | Pulse width $< 15$ ms or duty cycle $> 65\%$ | `WARNING` | Cluster pulses into valid MIB window. |
| **F-13**| Post-Eclipse Thermal Blindness | Optical saturation post-eclipse or thermal gradient $> 15^\circ$C/min | `CRITICAL` | Switch to RF/ISL backup until sensor chills. |
| **F-14**| Communications Heartbeat Loss | Downlink/uplink silence $> 5.0$ seconds | `CRITICAL` | Engage autonomous watchdog safe-hold orbit. |
| **F-15**| Single Event Upset (SEU) | Memory checksum mismatch across TMR banks | `FATAL` | Trigger memory scrub; re-read from sealed boot image. |
| **F-16**| Total Ionizing Dose (TID) Breach | Cumulative radiation dose $> 25$ krad | `CRITICAL` | Log breach; activate protective shield shutter. |
| **F-17**| Orbital Conjunction Warning | Collision probability $P_c > 10^{-6}$ and miss $< 1,000$ m | `CRITICAL` | Compute and execute automated tangential CAM burn. |
| **F-18**| Non-Permitted Tool Invocation | Subsystem tool call not in certified ODD whitelist | `CRITICAL` | Veto invocation; log security breach event. |
| **F-19**| Audit Trail Tamper | Merkle hash pointer discontinuity | `FATAL` | Immediate system freeze; alert sovereign ground station. |
