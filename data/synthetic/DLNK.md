#Requirement: REQ-DLNK
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: DLNK
BASELINE: v1.2.0
ABSOLUTE PATH: /AeroSys/Common/DLNK

Header: PURPOSE
|| Requirement No:DLNK-001 || Requirement: This document specifies the Tactical Datalink (DLNK) requirements applicable to Stratos-7 and AeroLynx-X2 only. The Skyrunner-T1 and Nimbus-C3 platforms do not host tactical datalink capabilities. The DLNK software shall be developed at DO-178C DAL-B and cyber-security assurance per DO-326A/DO-356A. ||

Header: SCOPE
|| Requirement No:DLNK-002 || Requirement: This module covers the Link-16-class tactical datalink terminal per STANAG 5516 (Tactical Data Link Message Standards), supporting time-slotted broadcast network participation, J-series message generation and reception, and integration with the common-avionics mission computer. It excludes the primary CDL (##CDL.CDL-001) and voice comms (##COMM.COMM-001). ||

Header: REFERENCES
|| Requirement No:DLNK-003 || Requirement: The governing references are: STANAG 5516 (Link 16 Tactical Data Exchange), STANAG 4175 (Multifunctional Information Distribution System characteristics), MIL-STD-6016 (Tactical Data Link Standard), RTCA DO-178C, RTCA DO-254, RTCA DO-160G, RTCA DO-326A, NSA Type 1 cryptographic guidance for classified operations. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|DLNK|Tactical Datalink|
--------------------------------------------------
|L16|Link 16 (MIDS-based tactical data link)|
--------------------------------------------------
|MIDS|Multifunctional Information Distribution System|
--------------------------------------------------
|TDMA|Time-Division Multiple Access|
--------------------------------------------------
|PPLI|Precise Participant Location and Identification (J2.0/J2.2)|
--------------------------------------------------
|J-msg|J-series message|
--------------------------------------------------
|NPG|Network Participation Group|
--------------------------------------------------
|TSEC|Transmission Security key|
--------------------------------------------------
|MSEC|Message Security key|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:DLNK-004 || Requirement: The DLNK terminal shall implement the Link 16 protocol per STANAG 5516, operating in the 960 - 1215 MHz L-band on the authorised TDMA time slots assigned by the network controller.
References: STANAG 5516 ||

|| Requirement No:DLNK-005 || Requirement: The DLNK terminal shall support the J-series messages listed in the J_Message_Support table (DLNK-018), including J2.x (PPLI), J3.x (surveillance), J7.x (information management), and J12.x (control) per MIL-STD-6016.
References: MIL-STD-6016 ||

|| Requirement No:DLNK-006 || Requirement: The DLNK terminal shall generate PPLI (J2.0 air) messages at 6 s nominal cadence with position, velocity, identity, and status, consuming aircraft state from ##NAV.NAV-029.
Satisfies: ##NAV.NAV-029
References: MIL-STD-6016 ||

|| Requirement No:DLNK-007 || Requirement: The DLNK terminal shall support network time alignment to the network time reference with accuracy ≤ 1 µs when receiving the time-reference broadcast, synchronised with the onboard GPS time per ##GPS.GPS-010.
Satisfies: ##GPS.GPS-010 ||

|| Requirement No:DLNK-008 || Requirement: The DLNK terminal shall transmit at the authorised power level (typically 200 W or 1 kW per MIDS variant) within the assigned time slots, inhibiting transmit if no valid TSEC or MSEC key is loaded or if time synchronisation has not been achieved. ||

|| Requirement No:DLNK-009 || Requirement: The DLNK terminal shall receive and process incoming J-series messages, routing surveillance tracks (J3.x) to the mission computer, control messages (J12.x) to the Autopilot (##AUTO.AUTO-006), and PPLI (J2.x) to the GCS tactical display per ##GCS.GCS-055. ||

|| Requirement No:DLNK-010 || Requirement: The DLNK terminal shall maintain TDMA time-slot discipline, transmitting only in assigned slots and remaining silent in unassigned slots, with slot-assignment managed via the network initialisation file (NIF) uploaded by operator. ||

|| Requirement No:DLNK-011 || Requirement: The DLNK terminal shall support Network Participation Group (NPG) assignments per the operator-supplied NIF, including NPG 1 (initial entry), NPG 2 (RTT-A), NPG 3 (RTT-B), NPG 5 (surveillance), NPG 6 (mission management), and NPG 7 (air control). ||

|| Requirement No:DLNK-012 || Requirement: The DLNK terminal shall detect and report loss of network synchronisation within 2 time frames (24 s) of onset, and shall attempt automatic re-entry using the initial-entry procedure without operator intervention. ||

|| Requirement No:DLNK-013 || Requirement: The DLNK terminal shall implement Link 16 cryptographic protection using NATO-approved Type 1 crypto module (or equivalent national-approved module) holding TSEC and MSEC key slots for at least 30 days of operation.
Satisfies: ##SEC.SEC-010
References: DO-326A ||

|| Requirement No:DLNK-014 || Requirement: The DLNK terminal shall support cryptographic zeroise within 200 ms of authenticated zeroise command, erasing all TSEC and MSEC key material per ##SEC.SEC-032.
Satisfies: ##SEC.SEC-032 ||

|| Requirement No:DLNK-015 || Requirement: The DLNK terminal shall apply LPI/LPD (low probability of intercept/detection) waveform characteristics as an integral part of the Link 16 waveform (FHSS across >= 51 carriers, TDMA slotting, CCSK spreading). ||

|| Requirement No:DLNK-016 || Requirement: The DLNK terminal shall operate across DO-160G §4 Category A2 environmental envelope and shall sustain DO-160G §16 Category Z 50 ms power-interruption per MIL-STD-704F.
References: DO-160G-4, DO-160G-16 ||

|| Requirement No:DLNK-017 || Requirement: The DLNK terminal shall enforce DO-160G §20 Category Y EMC and coexist with the onboard CDL (##CDL.CDL-024), radar altimeter (##RADAR.RADAR-009), and GPS (##GPS.GPS-009) without mutual interference.
References: DO-160G-20 ||

Header: Interface
|| Requirement No:DLNK-018 || Requirement: The DLNK terminal shall support the J-series messages per the J_Message_Support table.
Table Type: MESSAGE
Table Name or Description: J_Message_Support
Table: J_Message_Support
|J-Msg|Purpose|TX|RX|Platform|
--------------------------------------------------
|J2.0|Indirect PPLI air|yes|yes|STR7, ALX2|
--------------------------------------------------
|J2.2|Indirect PPLI air|yes|yes|STR7, ALX2|
--------------------------------------------------
|J3.2|Air track|optional|yes|STR7, ALX2|
--------------------------------------------------
|J3.5|Land point|no|yes|STR7, ALX2|
--------------------------------------------------
|J7.0|Track management|yes|yes|STR7, ALX2|
--------------------------------------------------
|J12.0|Mission assignment|no|yes|STR7, ALX2|
--------------------------------------------------
|J13.2|Airborne platform status|yes|yes|STR7, ALX2|
--------------------------------------------------
|J28.2|Text message|yes|yes|STR7, ALX2|
-------------------------------------------------- ||

|| Requirement No:DLNK-019 || Requirement: The DLNK terminal shall interface with the primary 1553B avionics bus as Remote Terminal 15, publishing a DLNK_STATUS message at 1 Hz and accepting configuration commands from the GCS (##GCS.GCS-055). ||

|| Requirement No:DLNK-020 || Requirement: The DLNK terminal shall consume nominal 28 V DC per MIL-STD-704F, drawing ≤ 600 W during TX-active slots and ≤ 80 W steady-state, with heat dissipation compatible with ##TCS.TCS-008.
Satisfies: ##TCS.TCS-008 ||

Header: Tables
|| Requirement No:DLNK-021 || Requirement: The DLNK terminal shall use the NPG time-slot allocation per the NPG_Allocation table. Actual allocation is operation-specific and delivered via the NIF.
Table Type: MESSAGE
Table Name or Description: NPG_Allocation
Table: NPG_Allocation
|NPG|Purpose|Typical Usage|Slot Type|
--------------------------------------------------
|1|Initial Entry|1 - 3 % of slots|fixed|
--------------------------------------------------
|5|Surveillance|10 - 30 %|distributed|
--------------------------------------------------
|6|Mission Management|2 - 10 %|distributed|
--------------------------------------------------
|7|Air Control|1 - 5 %|distributed|
--------------------------------------------------
|18|Voice A (if equipped)|up to 25 %|continuous|
--------------------------------------------------
|19|Voice B (if equipped)|up to 25 %|continuous|
-------------------------------------------------- ||

Header: Test
|| Requirement No:DLNK-022 || Requirement: Time-alignment accuracy (DLNK-007) shall be verified by laboratory test with a calibrated network time reference, measuring 1 000 PPLI transmissions and confirming time-alignment error ≤ 1 µs at 99 % confidence.
Verifies: DLNK-007
References: MIL-STD-6016 ||

|| Requirement No:DLNK-023 || Requirement: Transmit inhibit (DLNK-008) shall be verified by attempting transmit with (a) no TSEC key loaded, (b) no MSEC key loaded, and (c) no time sync, confirming 100 % of transmit attempts are inhibited in all three conditions.
Verifies: DLNK-008 ||

|| Requirement No:DLNK-024 || Requirement: Cryptographic zeroise (DLNK-014) shall be verified on the flight-configuration hardware by commanded zeroise, confirming key erasure within 200 ms and network de-entry within the following 2 frames.
Verifies: DLNK-014 ||

|| Requirement No:DLNK-025 || Requirement: Multi-aircraft coordination per ##ALX2-FMS-001 shall be verified by a live-network test with two aircraft (or one aircraft plus a ground surrogate), demonstrating inter-aircraft separation maintenance via PPLI exchange with ≥ 1 nmi lateral and ≥ 500 ft vertical sustained separation.
Verifies: ##ALX2-FMS-001
Satisfies: ##ALX2-FMS-001 ||
