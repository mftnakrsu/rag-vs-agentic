#Requirement: REQ-LGT
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: LGT
BASELINE: v1.1.0
ABSOLUTE PATH: /AeroSys/Common/LGT

Header: PURPOSE
|| Requirement No:LGT-001 || Requirement: This document specifies the External Lighting requirements for the AeroSys Dynamics platforms (Stratos-7, AeroLynx-X2, Skyrunner-T1, Nimbus-C3). Lighting control software shall be developed at DO-178C DAL-C on all platforms; lamp-out monitoring shall support maintenance. ||

Header: SCOPE
|| Requirement No:LGT-002 || Requirement: This module covers navigation lights, anti-collision (strobe/beacon) lights, landing/taxi lights, logo lights (where fitted), and IR covert-lighting (Stratos-7/AeroLynx-X2 only). It excludes interior cabin lighting (not applicable to UAS). ||

Header: REFERENCES
|| Requirement No:LGT-003 || Requirement: The governing references are: RTCA DO-178C, FAR §25.1389/§25.1401/§25.1403 (position lights and anti-collision), ICAO Annex 6, SAE AS50881. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|NAV|Navigation (position) lights|
--------------------------------------------------
|ACL|Anti-Collision Light|
--------------------------------------------------
|IR|Infrared (covert) lighting|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:LGT-004 || Requirement: The lighting subsystem shall provide position (navigation) lights: red (port wingtip), green (starboard wingtip), white (tail), each with intensity and beam pattern compliant with FAR §25.1389.
References: FAR 25.1389 ||

|| Requirement No:LGT-005 || Requirement: The lighting subsystem shall provide at least one anti-collision strobe light visible from all angles in the upper hemisphere (and lower hemisphere combined via redundant units), flashing at 40 to 100 cycles per minute per FAR §25.1401.
References: FAR 25.1401 ||

|| Requirement No:LGT-006 || Requirement: The lighting subsystem shall provide landing light(s) with peak intensity meeting ICAO guidance for night operations, selectable from the GCS and automatically engaged when gear is extended during night approach (configurable). ||

|| Requirement No:LGT-007 || Requirement: The lighting subsystem shall provide taxi light(s) operational only on the ground (WoW asserted from ##LDG.LDG-015), with operator override available for maintenance. ||

|| Requirement No:LGT-008 || Requirement: On Stratos-7 and AeroLynx-X2, the lighting subsystem shall provide IR covert-lighting mode, in which NAV and anti-collision are replaced with IR-spectrum emitters; covert mode engagement shall be authenticated per ##SEC.SEC-010.
Satisfies: ##SEC.SEC-010 ||

|| Requirement No:LGT-009 || Requirement: The lighting subsystem shall use LED sources for all lamps with service life ≥ 20 000 h at rated power, and shall monitor lamp health via current sensing. ||

|| Requirement No:LGT-010 || Requirement: The lighting subsystem shall detect lamp-out conditions (current below 50 % of nominal for > 2 s) and report each lamp's state to the GCS at 0.5 Hz. ||

|| Requirement No:LGT-011 || Requirement: The lighting subsystem shall be fed from the secondary bus (shed level P6 per ##PWR.PWR-032 during deep-shed conditions) with the NAV lights alone held on P5 to maintain minimum conspicuity.
Satisfies: ##PWR.PWR-032 ||

|| Requirement No:LGT-012 || Requirement: The lighting subsystem shall operate across DO-160G §4 Category A2 environmental envelope with lamp qualification per DO-160G §8 vibration.
References: DO-160G-4, DO-160G-8 ||

|| Requirement No:LGT-013 || Requirement: The lighting subsystem shall publish LGT_STATUS_MSG at 1 Hz with per-lamp state (ON/OFF), lamp-out flags, and mode (normal/covert). ||

Header: Interface
|| Requirement No:LGT-014 || Requirement: The lighting subsystem shall accept operator mode and individual-lamp commands from the GCS per ##CDL.CDL-030 with authentication; automatic modes (gear-down landing, WoW taxi) shall be configurable.
Satisfies: ##CDL.CDL-030 ||

Header: Tables
|| Requirement No:LGT-015 || Requirement: The lighting subsystem shall manage lamps per the Lamp_Inventory table.
Table Type: MESSAGE
Table Name or Description: Lamp_Inventory
Table: Lamp_Inventory
|Lamp|Platform|Visible Spectrum|IR (covert) Variant|Power (W)|
--------------------------------------------------
|NAV red (port)|all|yes|STR7/ALX2 only|10|
--------------------------------------------------
|NAV green (stbd)|all|yes|STR7/ALX2 only|10|
--------------------------------------------------
|NAV white (tail)|all|yes|STR7/ALX2 only|10|
--------------------------------------------------
|Upper ACL strobe|all|yes|STR7/ALX2 only|35|
--------------------------------------------------
|Lower ACL strobe|all|yes|STR7/ALX2 only|35|
--------------------------------------------------
|Landing light|STR7, ALX2, NBC3|yes|no|80|
--------------------------------------------------
|Taxi light|STR7, ALX2, NBC3|yes|no|40|
--------------------------------------------------
|Logo light|STR7 optional|yes|no|20|
-------------------------------------------------- ||
