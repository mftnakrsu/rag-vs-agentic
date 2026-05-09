#Requirement: REQ-FDR
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: FDR
BASELINE: v1.3.0
ABSOLUTE PATH: /AeroSys/Common/FDR

Header: PURPOSE
|| Requirement No:FDR-001 || Requirement: This document specifies the Flight Data Recorder (FDR) requirements for the AeroSys Dynamics platforms. The FDR software shall be developed at DO-178C DAL-B on all platforms; crash-survivable recorder hardware shall be qualified per ED-112A / EUROCAE MOPS where applicable. ||

Header: SCOPE
|| Requirement No:FDR-002 || Requirement: This module covers the aircraft-side flight-data recording function including data selection, storage, crash-survivability, post-flight retrieval, and synchronisation with GCS recording per ##GCS.GCS-018. It excludes the GCS recording (mission-level) itself. ||

Header: REFERENCES
|| Requirement No:FDR-003 || Requirement: The governing references are: EUROCAE ED-112A / RTCA DO-160G, RTCA DO-178C, SAE ARP4754A, MIL-STD-810H (crash/impact testing), ICAO Annex 6 (where commercial applicability, Nimbus-C3). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|FDR|Flight Data Recorder|
--------------------------------------------------
|CSMU|Crash-Survivable Memory Unit|
--------------------------------------------------
|ULB|Underwater Locator Beacon|
--------------------------------------------------
|ARINC 573|Flight data acquisition format (legacy)|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:FDR-004 || Requirement: The FDR shall record at minimum the parameters listed in the FDR_Mandatory_Params table (FDR-016), at each parameter's native rate, with timestamp synchronised to UTC via ##NAV.NAV-027.
Satisfies: ##NAV.NAV-027 ||

|| Requirement No:FDR-005 || Requirement: The FDR shall receive the FCC_BIT_STATUS_MSG per ##FCC.FCC-047 at its nominal recording rate (1 Hz) and store it as part of the aircraft health record.
Satisfies: ##FCC.FCC-047 ||

|| Requirement No:FDR-008 || Requirement: The FDR shall record every FCC mode transition per ##FCC.FCC-012 with predecessor mode, successor mode, UTC timestamp, and triggering condition, retained for at least the most recent 50 flight hours.
Satisfies: ##FCC.FCC-012 ||

|| Requirement No:FDR-012 || Requirement: The FDR shall record every FMS uplink-clearance per ##FMS.FMS-022 with timestamp and operator ID.
Satisfies: ##FMS.FMS-022 ||

|| Requirement No:FDR-015 || Requirement: The FDR shall record every autopilot engage/disengage event per ##AUTO.AUTO-010 with predecessor mode, successor mode, and operator confirmation (where applicable).
Satisfies: ##AUTO.AUTO-010 ||

|| Requirement No:FDR-018 || Requirement: The FDR shall record every INS fault transition per ##INS.INS-015 with sensor snapshot and UTC timestamp.
Satisfies: ##INS.INS-015 ||

|| Requirement No:FDR-020 || Requirement: The FDR shall accept INS sensor-snapshots per ##INS.INS-039 at 10 Hz and retain them for at least 8 h of flight time.
Satisfies: ##INS.INS-039 ||

|| Requirement No:FDR-022 || Requirement: The FDR shall record GPS raw-measurement datastream per ##GPS.NBC3-GPS-002 on Nimbus-C3 at 1 Hz for post-flight analysis.
Satisfies: ##NBC3-GPS-002 ||

|| Requirement No:FDR-024 || Requirement: The FDR shall record NAV EKF divergence events per ##NAV.NAV-024 with the filter state snapshot at divergence and the reset state.
Satisfies: ##NAV.NAV-024 ||

|| Requirement No:FDR-028 || Requirement: The FDR shall record PWR_STATUS_MSG per ##PWR.PWR-015 and EPS_STATUS_MSG per ##EPS.EPS-016 at 10 Hz each.
Satisfies: ##PWR.PWR-015, ##EPS.EPS-016 ||

|| Requirement No:FDR-030 || Requirement: The FDR shall record APM battery and APU data per ##APM.APM-023 at 1 Hz nominal and 10 Hz for 60 s before and after any APM fault transition.
Satisfies: ##APM.APM-023 ||

|| Requirement No:FDR-032 || Requirement: The FDR shall record engine protection-limit events per ##ENG.ENG-013 with full parameter snapshot 30 s before and 30 s after the event.
Satisfies: ##ENG.ENG-013 ||

|| Requirement No:FDR-035 || Requirement: The FDR shall record touchdown events per ##LDG.LDG-026 with time, vertical rate, longitudinal and lateral g.
Satisfies: ##LDG.LDG-026 ||

|| Requirement No:FDR-040 || Requirement: The FDR shall record PLD sensor and external-store events per ##PLD.PLD-020 with timestamp, command, operator-ID, and outcome.
Satisfies: ##PLD.PLD-020, ##STR7-PLD-001 ||

|| Requirement No:FDR-045 || Requirement: The FDR shall record EMS fault-code mappings per ##EMS.EMS-008 and operator actions per ##GCS.GCS-010.
Satisfies: ##EMS.EMS-008, ##GCS.GCS-010 ||

|| Requirement No:FDR-050 || Requirement: The FDR shall record EMS rally-point changes per ##EMS.EMS-015 with UTC timestamp and operator-ID.
Satisfies: ##EMS.EMS-015 ||

Header: Interface
|| Requirement No:FDR-055 || Requirement: The FDR shall provide a post-flight data-retrieval interface over the maintenance Ethernet port per ##FCC.FCC-044, with authenticated access per ##SEC.SEC-015, and export in ARINC 573 extended format or vendor-specific format. ||

|| Requirement No:FDR-060 || Requirement: The FDR shall be housed in a crash-survivable memory unit (CSMU) per ED-112A for Nimbus-C3 civil operations, and a non-survivable solid-state recorder for Stratos-7, AeroLynx-X2, and Skyrunner-T1 (where ED-112A is not mandated by certification basis).
References: ED-112A ||

Header: Tables
|| Requirement No:FDR-016 || Requirement: The FDR shall record at minimum the parameters in the FDR_Mandatory_Params table.
Table Type: MESSAGE
Table Name or Description: FDR_Mandatory_Params
Table: FDR_Mandatory_Params
|Parameter|Native Rate|Source|
--------------------------------------------------
|Position (lat, lon, alt)|5 Hz|##NAV.NAV-029|
--------------------------------------------------
|Velocity (NED)|5 Hz|##NAV.NAV-029|
--------------------------------------------------
|Attitude (pitch, roll, yaw)|10 Hz|##INS.INS-020|
--------------------------------------------------
|Airspeed, Mach|5 Hz|##ADS.ADS-020|
--------------------------------------------------
|AOA, sideslip|5 Hz|##ADS.ADS-020|
--------------------------------------------------
|Control surface positions|10 Hz|##FCC.FCC-038|
--------------------------------------------------
|Engine parameters|1 Hz|##ENG.ENG-020|
--------------------------------------------------
|Fuel state|0.5 Hz|##FUEL.FUEL-010|
--------------------------------------------------
|Autopilot mode|2 Hz|##AUTO.AUTO-031|
--------------------------------------------------
|FMS active leg|1 Hz|##FMS.FMS-021|
--------------------------------------------------
|CDL state|1 Hz|##CDL.CDL-029|
--------------------------------------------------
|Electrical state|1 Hz|##PWR.PWR-026|
--------------------------------------------------
|EMS events|event-driven|##EMS.EMS-031|
--------------------------------------------------
|BIT faults|event-driven|##BIT.BIT-036|
--------------------------------------------------
References: ED-112A ||

Header: Test
|| Requirement No:FDR-070 || Requirement: Mandatory parameter coverage (FDR-004, FDR-016) shall be verified by running a HIL mission of 60 min and extracting the recorded data, confirming every parameter in FDR-016 is present at or above its specified rate with valid timestamps.
Verifies: FDR-004, FDR-016
References: ED-112A ||
