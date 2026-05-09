#Requirement: REQ-GCS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: GCS
BASELINE: v2.1.0
ABSOLUTE PATH: /AeroSys/Common/GCS

Header: PURPOSE
|| Requirement No:GCS-001 || Requirement: This document specifies the Ground Control Station Core requirements for the AeroSys Dynamics platforms. The GCS software shall be developed at RTCA DO-278A at AL-3 on Stratos-7, AeroLynx-X2, and Nimbus-C3, and AL-4 on Skyrunner-T1. Cyber-security assurance per DO-326A is required on all platforms. ||

Header: SCOPE
|| Requirement No:GCS-002 || Requirement: This module covers the GCS core functions: pilot-in-command control dispatch, telemetry reception and distribution to operator consoles, mission-plan management, recording, audit logging, ground-based safety monitoring, and interfacing with external networks (C4I, ATC coordination). It excludes the ground-based CDL radio equipment covered by ##CDL.CDL-001. ||

|| Requirement No:GCS-003 || Requirement: The GCS shall be a two-operator configuration (Pilot-in-Command and Sensor/Mission Operator) on Stratos-7, AeroLynx-X2, and Nimbus-C3, and single-operator on Skyrunner-T1. ||

Header: REFERENCES
|| Requirement No:GCS-004 || Requirement: The governing references are: RTCA DO-278A (software for non-airborne CNS), RTCA DO-326A/DO-355/DO-356A (airworthiness security), STANAG 4586 (UAS Interop), ARP4754A, ED-137 (EUROCAE voice), MIL-STD-882E (safety programme). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|GCS|Ground Control Station|
--------------------------------------------------
|PIC|Pilot-in-Command|
--------------------------------------------------
|SMO|Sensor/Mission Operator|
--------------------------------------------------
|C4I|Command, Control, Communications, Computers, Intelligence|
--------------------------------------------------
|RBAC|Role-Based Access Control|
--------------------------------------------------
|CUI|Common User Interface|
--------------------------------------------------
|MDM|Mission Data Management|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:GCS-005 || Requirement: The GCS shall support the following operational modes:
    a) OFF
    b) PREFLIGHT (operator check, aircraft not linked)
    c) LINKED (CDL active, normal operations)
    d) DEGRADED (CDL intermittent)
    e) LOST_LINK (awaiting aircraft RTB or reconnect)
    f) MAINTENANCE (ground-test, no flight operations)
    g) FAULT ||

|| Requirement No:GCS-006 || Requirement: While in LINKED mode, the GCS shall dispatch pilot commands to the CDL (##CDL.CDL-030) with GCS-side latency (operator input to CDL ingress) ≤ 50 ms at 95 % confidence. ||

|| Requirement No:GCS-007 || Requirement: On transition to LOST_LINK, the GCS shall display clear operator warning (##HMI.HMI-170), inhibit further command dispatch until reconnection, and await aircraft RTB per ##AUTO.AUTO-022.
Satisfies: ##AUTO.AUTO-022 ||

Header: General
|| Requirement No:GCS-008 || Requirement: The GCS shall authenticate every operator at login using multi-factor authentication (badge + PIN, or smartcard + password), with no operator commands accepted prior to successful authentication.
Satisfies: ##SEC.SEC-015
References: DO-326A ||

|| Requirement No:GCS-009 || Requirement: The GCS shall enforce RBAC such that only authenticated PIC can dispatch flight-control commands (FCC, AUTO, EMS), and only authenticated SMO can dispatch payload commands (PLD) and mission-plan changes within operator authority.
References: DO-326A ||

|| Requirement No:GCS-010 || Requirement: The GCS shall record every operator action with timestamp, operator-ID, command details, and command outcome (ACK/NACK from aircraft), retained for the lifetime of the mission plus 90 days minimum per operator data-retention policy.
Satisfies: ##FDR.FDR-045 ||

|| Requirement No:GCS-011 || Requirement: The GCS shall compute commanded flight-plan uploads and route them to the aircraft FMS (##FMS.FMS-022) via the CDL uplink, requiring PIC confirmation for any plan change of length greater than one waypoint.
Satisfies: ##FMS.FMS-022 ||

|| Requirement No:GCS-012 || Requirement: The GCS shall display real-time aircraft state (position, altitude, airspeed, heading, mode, health) received from ##NAV.NAV-029 at 5 Hz minimum to the operator console.
Satisfies: ##NAV.NAV-029 ||

|| Requirement No:GCS-013 || Requirement: The GCS shall display engine telemetry from ##ENG.ENG-020 at 2 Hz minimum, including N1, EGT, oil pressure, fuel flow, and fault word. ||

|| Requirement No:GCS-014 || Requirement: The GCS shall display fuel state from ##FUEL.FUEL-010 at 1 Hz including total fuel, per-tank quantity, flow rate, and estimated remaining endurance. ||

|| Requirement No:GCS-015 || Requirement: The GCS shall display electrical power status from ##PWR.PWR-015 at 1 Hz including bus voltages, generator/APU status, and battery SoC. ||

|| Requirement No:GCS-016 || Requirement: The GCS shall generate audio alerts on safety-critical conditions (EMS warning per ##EMS.EMS-012, CDL lost, engine-out on AeroLynx-X2, LOW_FUEL, CRITICAL_FUEL) with distinctive audio cues per the Audio_Alert_Table (GCS-035).
Satisfies: ##EMS.EMS-012 ||

|| Requirement No:GCS-017 || Requirement: The GCS shall display DAA resolution advisories received from ##RADAR.RADAR-025 and ##AUTO.AUTO-020 within 500 ms of receipt, with visual and audio cues.
Satisfies: ##AUTO.AUTO-020 ||

|| Requirement No:GCS-018 || Requirement: The GCS shall provide a mission-recording function capturing all telemetry, video, operator actions, and audio with timestamp, at a rate sufficient to enable full post-mission reconstruction (per-telemetry-stream native rate retained). ||

|| Requirement No:GCS-019 || Requirement: The GCS shall record operator-console video (screen capture) at 10 fps minimum during LINKED operation, retained for post-mission review. ||

|| Requirement No:GCS-020 || Requirement: The GCS shall synchronise its internal clock to UTC via GPS-disciplined OCXO with ≤ 10 ms accuracy, and shall align recorded timestamps with aircraft UTC time (##FCC.FCC-034, ##NAV.NAV-027) within ±100 ms. ||

|| Requirement No:GCS-021 || Requirement: The GCS shall support operator handover (transfer of PIC or SMO role from one console to another, or to a relief operator) without interruption of control authority, completing handover within 5 s with explicit confirmation from both outgoing and incoming operator. ||

|| Requirement No:GCS-022 || Requirement: The GCS shall provide ground-maintenance command dispatch per ##FCC.FCC-007 (GROUND mode surface-command path), authenticated and restricted to ground-crew role.
Satisfies: ##FCC.FCC-007 ||

|| Requirement No:GCS-023 || Requirement: The GCS shall detect and flag GCS-to-aircraft clock drift greater than 500 ms, prompting operator to synchronise clocks or troubleshoot. ||

|| Requirement No:GCS-024 || Requirement: The GCS shall isolate operational networks from general IT networks via dedicated firewalls configured per ##SEC.SEC-030, with no operational traffic routed over the general IT network.
Satisfies: ##SEC.SEC-030 ||

|| Requirement No:GCS-025 || Requirement: The GCS shall maintain a backup-GCS cold-standby configuration for Stratos-7 and AeroLynx-X2, supporting switchover within 2 min by trained operator; backup shall receive a live copy of all critical state via redundant network links. ||

|| Requirement No:GCS-026 || Requirement: The GCS shall operate with commercial off-the-shelf displays qualified for continuous 8+ h operator use (brightness ≥ 300 cd/m², resolution ≥ 1920×1080), with redundant display per operator on Stratos-7 and AeroLynx-X2. ||

|| Requirement No:GCS-027 || Requirement: The GCS shall consume ground mains power (230 V AC / 50 Hz or 120 V AC / 60 Hz configurable) with UPS backup supporting uninterrupted operation for at least 30 min during mains outage. ||

|| Requirement No:GCS-028 || Requirement: The GCS shall provide a C4I interface (STANAG 4607 GMTI product, STANAG 7023 imagery, STANAG 5516 PPLI forwarding) for external tactical-network integration on Stratos-7 and AeroLynx-X2.
References: STANAG 4607, STANAG 7023 ||

|| Requirement No:GCS-029 || Requirement: The GCS shall provide an ATC voice-relay capability (operator to aircraft VHF/UHF via ##COMM.COMM-006) with one-way latency ≤ 250 ms.
Satisfies: ##COMM.COMM-006 ||

|| Requirement No:GCS-030 || Requirement: The GCS shall support loadmaster input on Nimbus-C3 for CG declaration per ##NBC3-FCC-001, with entered CG forwarded to the FCC for gain-schedule adaptation.
Satisfies: ##NBC3-FCC-001 ||

Header: Interface
|| Requirement No:GCS-031 || Requirement: The GCS shall interface to the CDL ground terminal (##CDL.CDL-001) via Ethernet 1 Gbps with command and telemetry streams separated by QoS class per ##CDL.CDL-037. ||

|| Requirement No:GCS-032 || Requirement: The GCS shall expose a STANAG 4586 Level III or Level IV service interface per ##CDL.CDL-028 for interoperability with coalition ground stations.
References: STANAG 4586 ||

|| Requirement No:GCS-033 || Requirement: The GCS shall provide an operator-console API for HMI applications (##HMI.HMI-001), published as a documented protocol specification. ||

|| Requirement No:GCS-034 || Requirement: The GCS shall format operator command frames per the CDL_Command_Frame of ##CDL.CDL-033 and shall receive telemetry per ##CDL.CDL-034. ||

Header: Tables
|| Requirement No:GCS-035 || Requirement: The GCS shall generate audio alerts per the Audio_Alert_Table.
Table Type: MESSAGE
Table Name or Description: Audio_Alert_Table
Table: Audio_Alert_Table
|Alert Condition|Priority|Sound Type|Repeat|
--------------------------------------------------
|EMS warning|P1|continuous chime|until ack|
--------------------------------------------------
|CDL lost|P1|double beep + voice|every 5 s|
--------------------------------------------------
|Engine-out (ALX2)|P1|siren + voice|until ack|
--------------------------------------------------
|CRITICAL_FUEL|P1|voice "critical fuel"|every 10 s|
--------------------------------------------------
|LOW_FUEL|P2|single beep + voice|every 30 s|
--------------------------------------------------
|DAA advisory|P1|tone + voice|1×|
--------------------------------------------------
|Config mismatch|P3|chime|1×|
--------------------------------------------------
|Clock drift|P3|chime|1×|
-------------------------------------------------- ||

|| Requirement No:GCS-036 || Requirement: The GCS shall enforce RBAC per the RBAC_Matrix table.
Table Type: MESSAGE
Table Name or Description: RBAC_Matrix
Table: RBAC_Matrix
|Role|Command Classes Allowed|
--------------------------------------------------
|PIC|FCC, AUTO, FMS (mode), EMS, EPS|
--------------------------------------------------
|SMO|PLD (all), EOIR, SAR, CDL config|
--------------------------------------------------
|Ground crew|FCC ground-mode, maintenance Ethernet, BIT|
--------------------------------------------------
|System admin|GCS config, RBAC mgmt, key mgmt|
--------------------------------------------------
|Auditor|read-only to audit log|
-------------------------------------------------- ||

Header: Test
|| Requirement No:GCS-037 || Requirement: Command-dispatch latency (GCS-006) shall be verified by measurement of 1 000 operator inputs with GCS-side timestamps at input and at CDL ingress, demonstrating ≤ 50 ms at 95 % confidence.
Verifies: GCS-006 ||

|| Requirement No:GCS-038 || Requirement: Operator-handover (GCS-021) shall be verified by drill with two console operators swapping PIC role during a simulated mission, demonstrating continuous command authority and completion within 5 s.
Verifies: GCS-021 ||

|| Requirement No:GCS-039 || Requirement: RBAC enforcement (GCS-009) shall be verified by negative test: attempts by each role to issue commands outside the RBAC_Matrix, demonstrating 100 % rejection with audit entry.
Verifies: GCS-009 ||

|| Requirement No:GCS-040 || Requirement: Backup-GCS switchover (GCS-025) shall be verified on the integration rig by simulating primary-GCS failure during a HIL mission, demonstrating switchover in ≤ 2 min and no loss of control authority.
Verifies: GCS-025 ||
