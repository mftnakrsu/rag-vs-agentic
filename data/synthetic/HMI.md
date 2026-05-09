#Requirement: REQ-HMI
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: HMI
BASELINE: v1.8.0
ABSOLUTE PATH: /AeroSys/Common/HMI

Header: PURPOSE
|| Requirement No:HMI-001 || Requirement: This document specifies the Operator HMI & Display requirements for the GCS operator consoles of the AeroSys Dynamics platforms. The HMI software shall be developed at RTCA DO-278A AL-3 on Stratos-7, AeroLynx-X2, and Nimbus-C3, and AL-4 on Skyrunner-T1. Human-factors and usability engineering per SAE ARP5600 and FAA AC 25-11B (display certification, adapted for unmanned). ||

Header: SCOPE
|| Requirement No:HMI-002 || Requirement: This module covers the console displays, input devices (mouse, joystick, touchscreen, voice where fitted), map and video presentation, alerts and annunciations, and the operator workflow. It excludes the GCS core-services layer (##GCS.GCS-001). ||

Header: REFERENCES
|| Requirement No:HMI-003 || Requirement: The governing references are: RTCA DO-278A, SAE ARP5600 (human-factors for cockpits, adapted), FAA AC 25-11B (electronic display certification), ISO 9241 (software ergonomics), MIL-STD-1472H (human engineering). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|HMI|Human-Machine Interface|
--------------------------------------------------
|PFD|Primary Flight Display|
--------------------------------------------------
|ND|Navigation Display|
--------------------------------------------------
|MFD|Multi-Function Display|
--------------------------------------------------
|CAS|Crew Alerting System (adapted to ground ops)|
--------------------------------------------------
|MCDU|Multi-function Control & Display Unit (software equivalent)|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:HMI-004 || Requirement: The HMI shall present a Primary Flight Display (PFD) to the PIC console showing attitude, airspeed, altitude, vertical speed, heading/track, mode annunciation, and key health indicators, updated at ≥ 10 Hz.
References: FAA AC 25-11B ||

|| Requirement No:HMI-005 || Requirement: The HMI shall present a Navigation Display (ND) with a moving-map, flight-plan overlay, aircraft position, weather overlay (where available from ##RADAR.RADAR-013), and DAA traffic (where available from ##AUTO.AUTO-020), updated at ≥ 5 Hz.
Satisfies: ##RADAR.RADAR-013 ||

|| Requirement No:HMI-006 || Requirement: The HMI shall present sensor video feeds (EOIR per ##EOIR.EOIR-017, SAR per ##SAR.SAR-010) at native frame rate on the SMO console, with metadata overlay toggleable.
Satisfies: ##EOIR.EOIR-017 ||

|| Requirement No:HMI-007 || Requirement: The HMI shall provide a Crew Alerting System (CAS) panel listing active alerts grouped by priority (P1 red, P2 amber, P3 cyan), with newest alert highlighted and scrolling older alerts available on operator selection. ||

|| Requirement No:HMI-008 || Requirement: The HMI shall ensure operator-workflow response time (from operator input to visible system response on display) ≤ 150 ms for routine commands and ≤ 50 ms for safety-critical commands (EMS, FLT_TERM, engine SHUTDOWN). ||

|| Requirement No:HMI-009 || Requirement: The HMI shall provide a Flight Management Display (FMD) page analogous to a cockpit MCDU for flight-plan editing, direct-to, performance computation display, and alternate planning. ||

|| Requirement No:HMI-010 || Requirement: The HMI shall annunciate INS_DEGRADED per ##FCC.FCC-017 within 500 ms of detection on the PFD/ND with visual cue and voice alert ("inertial degraded").
Satisfies: ##FCC.FCC-017 ||

|| Requirement No:HMI-015 || Requirement: The HMI shall display control-law authority margin (from ##FCC.FCC-029) as a graphical bar on the PFD, showing remaining authority on each axis.
Satisfies: ##FCC.FCC-029 ||

|| Requirement No:HMI-020 || Requirement: On AeroLynx-X2 engine-out notification (##ALX2-FCC-003), the HMI shall annunciate ENGINE_OUT with voice and visual cue, display the failed engine identifier, and display rudder-trim position.
Satisfies: ##ALX2-FCC-003 ||

|| Requirement No:HMI-022 || Requirement: On Nimbus-C3 cargo-shift notification per ##NBC3-FCC-002, the HMI shall annunciate CARGO_SHIFT with visual alert and current-vs-predicted CG delta.
Satisfies: ##NBC3-FCC-002 ||

|| Requirement No:HMI-025 || Requirement: The HMI shall provide a manual-control joystick input on Skyrunner-T1 for direct-control operation per ##SKT1-FCC-003, with deadband and rate-limiting applied at the GCS side before uplink.
Satisfies: ##SKT1-FCC-003 ||

|| Requirement No:HMI-030 || Requirement: The HMI shall provide an FMS page per ##FMS.FMS-003 supporting flight-plan edit, waypoint insert/delete, VNAV constraint entry, and approach selection.
Satisfies: ##FMS.FMS-003 ||

|| Requirement No:HMI-032 || Requirement: The HMI shall provide FMS SUSPEND/RESUME controls per ##FMS.FMS-009 with clear state indication.
Satisfies: ##FMS.FMS-009 ||

|| Requirement No:HMI-033 || Requirement: The HMI shall provide an operator entry interface for direct-to coordinates when the FMS is in FAULT per ##FMS.FMS-010, accepting lat/lon in DMS or decimal format.
Satisfies: ##FMS.FMS-010 ||

|| Requirement No:HMI-035 || Requirement: The HMI shall provide a wind-profile entry page accepting forecast wind speed and direction at up to 10 altitudes, feeding ##FMS.FMS-015.
Satisfies: ##FMS.FMS-015 ||

|| Requirement No:HMI-037 || Requirement: The HMI shall require explicit operator confirmation (two-step) for uplinked flight-plan modifications per ##FMS.FMS-022, displaying the full diff before confirmation.
Satisfies: ##FMS.FMS-022 ||

|| Requirement No:HMI-040 || Requirement: The HMI shall display FMS approach-deviation indicators (lateral and vertical) per ##FMS.FMS-030 with full-scale deflection matching the RNP containment.
Satisfies: ##FMS.FMS-030 ||

|| Requirement No:HMI-045 || Requirement: The HMI shall raise speed-envelope alerts per ##FMS.FMS-038 on the CAS and visually on the PFD airspeed tape with amber/red colouring at thresholds.
Satisfies: ##FMS.FMS-038 ||

|| Requirement No:HMI-050 || Requirement: The HMI shall detect operator-override stick-force exceeding the configured breakout threshold and forward that signal to ##AUTO.AUTO-010 for autopilot disengage.
Satisfies: ##AUTO.AUTO-010 ||

|| Requirement No:HMI-055 || Requirement: The HMI shall provide LOITER pattern control (centre point, bank angle, radius, direction) per ##AUTO.AUTO-023 with map-drag support.
Satisfies: ##AUTO.AUTO-023 ||

|| Requirement No:HMI-060 || Requirement: The HMI shall display autopilot mode annunciations per ##AUTO.AUTO-031 at 2 Hz, colour-coded (green=active, white=armed).
Satisfies: ##AUTO.AUTO-031 ||

|| Requirement No:HMI-070 || Requirement: The HMI shall display INS-alignment status per ##INS.INS-005, including mode, alignment percent-complete, and time-to-ready estimate. ||

|| Requirement No:HMI-090 || Requirement: The HMI shall annunciate PITOT_SUSPECT per ##ADS.ADS-014 with visual and voice alert, and shall dim or mark the affected airspeed indication to alert the operator.
Satisfies: ##ADS.ADS-014 ||

|| Requirement No:HMI-100 || Requirement: The HMI shall indicate CDL link-state changes (LINKED ↔ LOST ↔ RECOVERED) per ##CDL.CDL-007 with visual and audio cues.
Satisfies: ##CDL.CDL-007 ||

|| Requirement No:HMI-120 || Requirement: The HMI shall require explicit operator acknowledgement (acknowledge dialog + 2 s dwell) for EMERGENCY_POWER authorisation per ##ENG.ENG-008, with elapsed-time countdown visible throughout.
Satisfies: ##ENG.ENG-008 ||

|| Requirement No:HMI-135 || Requirement: The HMI shall require explicit multi-step operator authorisation for Stratos-7 fuel jettison per ##FUEL.FUEL-013, displaying current and post-jettison estimated fuel.
Satisfies: ##FUEL.FUEL-013 ||

|| Requirement No:HMI-155 || Requirement: The HMI shall require explicit 2 s dwell-confirmation for Nimbus-C3 pod jettison per ##PLD.PLD-030, with unambiguous warning of altitude constraint.
Satisfies: ##PLD.PLD-030 ||

|| Requirement No:HMI-160 || Requirement: The HMI shall require explicit operator authorisation for EOIR laser DESIGNATE per ##EOIR.EOIR-006, with eye-safety warning and persistent indicator during laser active.
Satisfies: ##EOIR.EOIR-006 ||

Header: Tables
|| Requirement No:HMI-180 || Requirement: The HMI shall follow the display-colour convention per the Display_Colour_Table.
Table Type: MESSAGE
Table Name or Description: Display_Colour_Table
Table: Display_Colour_Table
|Meaning|Colour|Example|
--------------------------------------------------
|Warning (P1)|Red|engine fire, flight-termination, EMS|
--------------------------------------------------
|Caution (P2)|Amber|LOW_FUEL, degraded INS|
--------------------------------------------------
|Advisory (P3)|Cyan|config mismatch, clock drift|
--------------------------------------------------
|Armed|White|armed AP mode|
--------------------------------------------------
|Active|Green|active AP mode, link active|
--------------------------------------------------
|Inhibited/shed|Grey|shed loads, inhibited modes|
--------------------------------------------------
|Navigation|Magenta|flight-plan leg|
--------------------------------------------------
References: FAA AC 25-11B ||

Header: Test
|| Requirement No:HMI-200 || Requirement: Response-time (HMI-008) shall be verified by automated test harness measuring 500 operator-command round-trips, demonstrating ≤ 150 ms routine and ≤ 50 ms safety-critical at 95 % confidence.
Verifies: HMI-008 ||

|| Requirement No:HMI-210 || Requirement: Confirmation-dialog enforcement (HMI-037, HMI-135, HMI-155, HMI-160) shall be verified by usability test demonstrating that no destructive action can be dispatched without the second-step confirmation, across 20 operator sessions.
Verifies: HMI-037, HMI-135, HMI-155, HMI-160
References: ISO 9241 ||

|| Requirement No:HMI-220 || Requirement: Display-readability (HMI-004, HMI-005) shall be verified under console-ambient illumination from 50 lux to 2 000 lux, demonstrating all primary indications remain legible without operator complaint.
Verifies: HMI-004, HMI-005
References: FAA AC 25-11B ||
