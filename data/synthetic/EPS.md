#Requirement: REQ-EPS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: EPS
BASELINE: v1.3.0
ABSOLUTE PATH: /AeroSys/Common/EPS

Header: PURPOSE
|| Requirement No:EPS-001 || Requirement: This document specifies the Emergency Power and Bus Switching requirements applicable to Stratos-7, AeroLynx-X2, and Nimbus-C3. Skyrunner-T1 does not host a separate EPS; its single-lane architecture relies on primary-PWR and APM alone. The EPS software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and DAL-B on Nimbus-C3. ||

Header: SCOPE
|| Requirement No:EPS-002 || Requirement: This module covers the emergency-bus definition, automatic switching between primary power, APU, and battery sources, and coordinated load shedding under power-failure conditions. It excludes the primary distribution (##PWR.PWR-001) and the battery/APU hardware (##APM.APM-001). ||

Header: REFERENCES
|| Requirement No:EPS-003 || Requirement: The governing references are: MIL-STD-704F, RTCA DO-160G, RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|EPS|Emergency Power & Bus Switching|
--------------------------------------------------
|DC-TIE|DC Tie contactor|
--------------------------------------------------
|EMRG|Emergency bus|
--------------------------------------------------
|BTB|Bus Tie Breaker|
--------------------------------------------------
|XFER|Transfer contactor|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:EPS-004 || Requirement: The EPS shall support the following operational modes:
    a) NORMAL (primary buses energised from generators)
    b) APU_BACKUP (APU supplying load during generator failure)
    c) BATT_ONLY (battery is the sole source for essential+emergency buses)
    d) LOAD_SHED_1 (non-essential loads shed)
    e) LOAD_SHED_2 (payload loads shed)
    f) LOAD_SHED_3 (deep-shed, only P1+P2 loads remain)
    g) FAULT
Mode transitions shall be automatic per EPS-024. ||

|| Requirement No:EPS-005 || Requirement: On transition to APU_BACKUP, the EPS shall close the APU-to-essential-bus tie contactor within 100 ms of APU ready-signal and open the generator-to-essential-bus tie. ||

|| Requirement No:EPS-006 || Requirement: On transition to BATT_ONLY, the EPS shall open all non-essential bus ties, close the battery-to-emergency-bus tie, and retain only P1+P2 loads per ##PWR.PWR-032.
Satisfies: ##PWR.PWR-032 ||

|| Requirement No:EPS-007 || Requirement: The EPS shall progress load shedding through LOAD_SHED_1 → _2 → _3 whenever the battery SoC falls below 40 %, 20 %, and 10 % respectively during BATT_ONLY operation, each with a 5 s dwell to avoid oscillation. ||

Header: General
|| Requirement No:EPS-008 || Requirement: The EPS shall execute source-selection arbitration at 10 Hz, selecting the highest-priority available source: (1) generators, (2) APU, (3) battery, and commanding contactor state to match.
Derives From: ARP4761-FHA-EPS-01 ||

|| Requirement No:EPS-009 || Requirement: The EPS shall ensure make-before-break transitions between sources whenever possible, with a maximum break time of 50 ms on essential buses.
References: MIL-STD-704F ||

|| Requirement No:EPS-010 || Requirement: The EPS shall prevent paralleling of sources that are not phase-synchronised (not applicable for 28 V DC buses but enforced via mutual-exclusion between generator and APU at the bus tie). ||

|| Requirement No:EPS-011 || Requirement: The EPS shall declare BATT_ONLY if APU start fails within 30 s of command or if APU self-shutdown per ##APM.APM-023 occurs, and shall issue RTB to AUTO per ##AUTO.AUTO-022.
Satisfies: ##AUTO.AUTO-022 ||

|| Requirement No:EPS-012 || Requirement: The EPS shall open the DC-TIE between essential and secondary buses within 50 ms whenever any generator faults and battery SoC < 60 %, isolating the secondary bus to preserve battery for essential loads. ||

|| Requirement No:EPS-013 || Requirement: The EPS shall detect a stuck contactor (commanded position does not match measured position within 200 ms) and log the event, route around the affected contactor if alternate path exists, and notify the operator per ##HMI.HMI-115. ||

|| Requirement No:EPS-014 || Requirement: The EPS shall apply bus-undervoltage protection on the emergency bus (trip at 20 V for > 200 ms) to avoid battery over-discharge below cutoff. ||

|| Requirement No:EPS-015 || Requirement: The EPS shall inhibit load re-connection automatically when returning from BATT_ONLY to APU_BACKUP or NORMAL mode; re-connection of shed P3-P6 loads shall require explicit operator command. ||

|| Requirement No:EPS-016 || Requirement: The EPS shall publish EPS_STATUS_MSG at 5 Hz with mode, contactor states, per-source availability, and active shed level, to the GCS per ##GCS.GCS-060 and FDR per ##FDR.FDR-028. ||

|| Requirement No:EPS-017 || Requirement: The EPS shall operate across DO-160G §4 Category A2 environmental envelope and endure DO-160G §22 lightning transients per Category A3 without loss of function.
References: DO-160G-4, DO-160G-22 ||

|| Requirement No:EPS-018 || Requirement: The EPS shall reject tampering by enforcing command authentication per ##SEC.SEC-010 on any operator-initiated bus-tie command.
Satisfies: ##SEC.SEC-010 ||

|| Requirement No:EPS-019 || Requirement: The EPS shall monitor contactor cycle count and record it in non-volatile memory per contactor, issuing a maintenance flag when cycle count reaches 80 % of the rated life. ||

Header: Interface
|| Requirement No:EPS-020 || Requirement: The EPS shall publish EPS_STATUS_MSG per the table below at 5 Hz on the primary avionics bus.
Table Type: MESSAGE
Table Name or Description: EPS_Status_Msg
Table: EPS_Status_Msg
|Field|Type|Range|
--------------------------------------------------
|mode|uint8|enum {NORMAL,APU_BACKUP,BATT_ONLY,LSHED_1,LSHED_2,LSHED_3,FAULT}|
--------------------------------------------------
|gen1_tie,gen2_tie|uint8 ×2|0 open / 1 closed|
--------------------------------------------------
|apu_tie|uint8|0/1|
--------------------------------------------------
|batt_tie|uint8|0/1|
--------------------------------------------------
|dc_tie|uint8|0/1|
--------------------------------------------------
|shed_level|uint8|0-3|
--------------------------------------------------
|fault_word|uint32|bitmask|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:EPS-021 || Requirement: The EPS shall maintain source priority per the Source_Priority table, selecting the highest-priority available source.
Table Type: MESSAGE
Table Name or Description: Source_Priority
Table: Source_Priority
|Priority|Source|Availability Criterion|
--------------------------------------------------
|1|Primary generator(s)|any GCU reports READY|
--------------------------------------------------
|2|APU generator|APU RUNNING and stable > 10 s|
--------------------------------------------------
|3|Battery|SoC > 5 % AND pack voltage > 20 V|
-------------------------------------------------- ||

|| Requirement No:EPS-022 || Requirement: The EPS shall enforce contactor command-versus-feedback checks per the Contactor_Checks table.
Table Type: MESSAGE
Table Name or Description: Contactor_Checks
Table: Contactor_Checks
|Contactor|Rated Current|Transfer Time|Feedback Delay|
--------------------------------------------------
|Gen1-Ess Tie|150 A|30 ms|≤ 200 ms|
--------------------------------------------------
|Gen2-Ess Tie|150 A|30 ms|≤ 200 ms|
--------------------------------------------------
|APU-Ess Tie|80 A|50 ms|≤ 200 ms|
--------------------------------------------------
|Batt-Emrg Tie|100 A|30 ms|≤ 100 ms|
--------------------------------------------------
|DC-Tie|100 A|50 ms|≤ 200 ms|
-------------------------------------------------- ||

Header: Test
|| Requirement No:EPS-023 || Requirement: Break time (EPS-009) shall be verified by oscilloscope measurement on the iron-bird during commanded source transfers under full load, demonstrating ≤ 50 ms break on essential buses.
Verifies: EPS-009
References: MIL-STD-704F ||

|| Requirement No:EPS-024 || Requirement: Mode-transition logic (EPS-005, EPS-006, EPS-011) shall be verified by fault-injection test on the power rig, simulating generator failure, APU failure, APU start failure, and battery depletion in sequence, demonstrating correct mode and contactor state transitions.
Verifies: EPS-005, EPS-006, EPS-011 ||

|| Requirement No:EPS-025 || Requirement: Lightning immunity (EPS-017) shall be verified per DO-160G §22 Category A3 on the flight-configuration EPS LRU, demonstrating no false mode change or spurious contactor actuation during or after the test pulses.
Verifies: EPS-017
References: DO-160G-22 ||
