#Requirement: REQ-EMS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: EMS
BASELINE: v1.9.0
ABSOLUTE PATH: /AeroSys/Common/EMS

Header: PURPOSE
|| Requirement No:EMS-001 || Requirement: This document specifies the Emergency Management and Flight Termination System (FTS) requirements for the AeroSys Dynamics platforms. EMS software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2 and DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:EMS-002 || Requirement: This module covers autonomous emergency response to critical failures, operator-initiated emergency procedures (RTB, emergency descent, flight termination), and coordination with the FCC, AUTO, and APM/EPS subsystems. It excludes emergency-bus switching logic (##EPS.EPS-001) and structural safety (##STR.STR-001). ||

Header: REFERENCES
|| Requirement No:EMS-003 || Requirement: The governing references are: RTCA DO-178C, SAE ARP4754A, SAE ARP4761, MIL-STD-882E (System Safety), RTCA DO-326A, EASA SORA 2.0, STANAG 4671 (UAS Airworthiness). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|EMS|Emergency Management System|
--------------------------------------------------
|FTS|Flight Termination System|
--------------------------------------------------
|RTB|Return-To-Base|
--------------------------------------------------
|HIRF|High-Intensity Radiated Fields|
--------------------------------------------------
|CRM|Cyclic Redundancy Check / Critical Risk Management|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:EMS-004 || Requirement: The EMS shall support the following operational modes:
    a) NORMAL (no emergency active)
    b) CAUTION (non-critical abnormality detected)
    c) WARNING (single critical subsystem failure, manageable)
    d) EMERGENCY (multiple critical failures or imminent hazard)
    e) TERMINATION (flight-termination sequence active) ||

|| Requirement No:EMS-005 || Requirement: The EMS shall transition to CAUTION upon any P2 fault (##PWR.PWR-032 priority 2 load failure, ##INS.INS-013 DEGRADED, ##COMM.COMM-021 transceiver failure), notifying operator within 500 ms. ||

|| Requirement No:EMS-006 || Requirement: The EMS shall transition to EMERGENCY on any of the conditions listed in ##FCC.FCC-009 and coordinate with the FCC EMERGENCY mode entry per ##FCC.FCC-010.
Satisfies: ##FCC.FCC-009, ##FCC.FCC-010 ||

Header: General
|| Requirement No:EMS-007 || Requirement: The EMS shall coordinate CONTROL_SATURATED response per ##FCC.FCC-030 by issuing reduced-manoeuvre-rate command to AUTO and notifying operator within 500 ms.
Satisfies: ##FCC.FCC-030 ||

|| Requirement No:EMS-008 || Requirement: The EMS shall map fault codes from ##FCC.FCC-050 to recovery actions and log the mapping outcome at 1 Hz to ##FDR.FDR-045.
Satisfies: ##FCC.FCC-050, ##FDR.FDR-045 ||

|| Requirement No:EMS-009 || Requirement: The EMS shall accept operator-initiated emergency procedures (EMERGENCY_DESCENT, RTB, LAND_AT_NEAREST, TERMINATION) authenticated per ##SEC.SEC-010, each requiring explicit operator confirmation per ##HMI.HMI-120 for irreversible actions.
Satisfies: ##SEC.SEC-010 ||

|| Requirement No:EMS-010 || Requirement: The EMS shall notify the GCS of any mode change within 200 ms via the CDL telemetry (##CDL.CDL-031), tagged P1 priority.
Satisfies: ##CDL.CDL-031 ||

|| Requirement No:EMS-011 || Requirement: The EMS shall support autonomous RTB engagement per ##AUTO.AUTO-022 when CDL lost-link timer expires, commanding climb to safe altitude and lateral track to operator-configured rally point.
Satisfies: ##AUTO.AUTO-022 ||

|| Requirement No:EMS-012 || Requirement: The EMS shall issue EMS_WARNING annunciation to the GCS per ##GCS.GCS-016 within 500 ms of any condition that escalates to WARNING or higher.
Satisfies: ##GCS.GCS-016 ||

|| Requirement No:EMS-013 || Requirement: The EMS shall coordinate EMERGENCY_DESCENT on Stratos-7 per ##STR7-AUTO-004 without operator confirmation when commanded, respecting Mmo/Vmo envelope and descending at -5 000 ft/min.
Satisfies: ##STR7-AUTO-004 ||

|| Requirement No:EMS-014 || Requirement: The EMS shall coordinate fuel-jettison decision (Stratos-7) when landing weight prediction exceeds structural landing limit, proposing jettison to operator with automatic calculation of jettison amount per ##FUEL.FUEL-013. ||

|| Requirement No:EMS-015 || Requirement: The EMS shall maintain the operator-configured rally point as the default RTB target, updatable during flight via authenticated GCS command, and shall log rally-point changes to ##FDR.FDR-050.
Satisfies: ##AUTO.AUTO-022 ||

|| Requirement No:EMS-016 || Requirement: The EMS shall detect battery-critical condition (SoC < 15 % from ##APM.APM-015) while in BATT_ONLY mode (##EPS.EPS-006) and command immediate RTB to the nearest suitable landing site.
Satisfies: ##APM.APM-015, ##EPS.EPS-006 ||

|| Requirement No:EMS-017 || Requirement: The EMS shall detect fuel-critical condition (FUEL-018 CRITICAL_FUEL per ##FUEL.FUEL-014) and command immediate divert to the nearest suitable landing site, respecting ##FMS.FMS-018 reserve.
Satisfies: ##FUEL.FUEL-014 ||

|| Requirement No:EMS-018 || Requirement: The EMS shall maintain an emergency SATCOM telemetry channel per ##COMM.COMM-022, broadcasting aircraft state at 1 Hz with 200 B frames independent of CDL availability.
Satisfies: ##COMM.COMM-022 ||

|| Requirement No:EMS-019 || Requirement: The EMS shall monitor BIT (##BIT.BIT-040) health summary and log every new fault with UTC timestamp and severity classification. ||

|| Requirement No:EMS-020 || Requirement: On detection of structural-envelope exceedance (load factor beyond ##STR.STR-008 limit sustained > 500 ms), the EMS shall command reduced-manoeuvre rate and notify operator with STRUCTURAL_EXCEEDANCE flag.
Satisfies: ##STR.STR-008 ||

|| Requirement No:EMS-021 || Requirement: The EMS shall support cyber-incident response per ##SEC.SEC-028 by logging the incident, alerting operator, and optionally transitioning aircraft to a defensive posture (inhibit remote commands, enforce conservative trajectory).
Satisfies: ##SEC.SEC-028 ||

|| Requirement No:EMS-022 || Requirement: The EMS shall coordinate with the TCS for thermal-runaway response per ##TCS.TCS-012, isolating affected battery cells and declaring EMERGENCY if runaway cannot be contained.
Satisfies: ##TCS.TCS-012, ##APM.APM-017 ||

|| Requirement No:EMS-023 || Requirement: The EMS shall support the flight-termination sequence on Stratos-7 and AeroLynx-X2 per ##STR7-FCC-006, requiring dual-authentication from two independent operators within a 30 s window.
Satisfies: ##STR7-FCC-006
References: STANAG 4671 ||

|| Requirement No:EMS-024 || Requirement: The flight-termination sequence shall disarm automatically if the second authentication is not received within 30 s, logging the abort with both operator IDs. ||

|| Requirement No:EMS-025 || Requirement: The flight-termination command, once armed and dual-authenticated, shall be irreversible; any subsequent cancellation attempts shall be rejected and logged. ||

|| Requirement No:EMS-026 || Requirement: On termination, the FCC shall command full nose-down pitch with throttle cut per ##STR7-FCC-006 within 200 ms and shall not accept any subsequent recovery commands.
Satisfies: ##STR7-FCC-006 ||

|| Requirement No:EMS-027 || Requirement: The EMS shall inhibit flight-termination below 1 000 ft AGL and inhibit on ground (WoW asserted) on all platforms.
References: STANAG 4671 ||

|| Requirement No:EMS-028 || Requirement: On Nimbus-C3 civil operations, flight-termination is not a standard capability; the EMS shall instead command CONTROLLED_DITCH or divert-to-safe-area per EASA SORA 2.0 operational risk class OC-3.
References: EASA SORA 2.0 ||

|| Requirement No:EMS-029 || Requirement: The EMS shall operate across DO-160G §4 Category A2 environmental envelope and shall sustain the 50 ms power-interruption per ##PWR.PWR-018 without loss of state.
Satisfies: ##PWR.PWR-018 ||

|| Requirement No:EMS-030 || Requirement: The EMS shall provide the flight-termination discrete output to the FCC per ##FCC.FCC-011 over a dedicated hardwired interface with CRC-verified authentication header, independent of the primary avionics bus.
Satisfies: ##FCC.FCC-011 ||

Header: Interface
|| Requirement No:EMS-031 || Requirement: The EMS shall publish EMS_STATUS_MSG at 2 Hz on the primary avionics bus with current mode, most recent trigger, armed emergency procedures, and fault word. ||

|| Requirement No:EMS-032 || Requirement: The EMS shall accept inputs from BIT (##BIT.BIT-040), CDL (##CDL.CDL-005), PWR (##PWR.PWR-004), APM (##APM.APM-004), FCC (##FCC.FCC-050), and ENG (##ENG.ENG-040) via the primary avionics bus; all aggregated at 5 Hz minimum. ||

Header: Tables
|| Requirement No:EMS-033 || Requirement: The EMS shall enforce emergency-response priorities per the EMS_Priority_Table.
Table Type: MESSAGE
Table Name or Description: EMS_Priority_Table
Table: EMS_Priority_Table
|Priority|Trigger|Autonomous Action|Operator Role|
--------------------------------------------------
|P1|Structural exceedance|rate reduction (EMS-020)|notify|
--------------------------------------------------
|P1|INS loss + no GPS|transition to EMERGENCY (FCC-009)|notify|
--------------------------------------------------
|P1|Engine failure (STR7/NBC3 single eng)|descend, RTB|authorise RTB variant|
--------------------------------------------------
|P2|Single-engine-out (ALX2)|asymmetric compensation|monitor|
--------------------------------------------------
|P2|CDL lost|start lost-link timer|await reconnect|
--------------------------------------------------
|P3|LOW_FUEL|recompute divert options|decide divert|
--------------------------------------------------
|P1|Cyber incident (SEC-028)|defensive posture|decide|
--------------------------------------------------
|P1|Battery critical|RTB nearest|authorise landing|
--------------------------------------------------
|P1|Termination (dual-auth)|irreversible terminate|dual-auth required|
-------------------------------------------------- ||

Header: Test
|| Requirement No:EMS-034 || Requirement: Emergency-mode entry latency (EMS-006) shall be verified by fault-injection of each EMS-triggering condition on the HIL rig, demonstrating mode transition within 50 ms of trigger and operator annunciation within 500 ms.
Verifies: EMS-006 ||

|| Requirement No:EMS-035 || Requirement: Flight-termination dual-authentication (EMS-023) shall be verified by negative tests (single operator, expired window, second operator absent) demonstrating 100 % rejection in all cases.
Verifies: EMS-023
References: STANAG 4671 ||
