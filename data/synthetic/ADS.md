#Requirement: REQ-ADS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: ADS
BASELINE: v1.5.0
ABSOLUTE PATH: /AeroSys/Common/ADS

Header: PURPOSE
|| Requirement No:ADS-001 || Requirement: This document specifies the Air Data System (ADS) requirements for the AeroSys Dynamics common air-data LRU (ADM - Air Data Module), applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3. The ADS software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and at DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:ADS-002 || Requirement: This module covers pitot-static sensing, angle-of-attack (AOA) and sideslip sensing, outside-air-temperature (OAT) measurement, and the derived quantities calibrated airspeed (CAS), true airspeed (TAS), Mach, pressure altitude, density altitude, and baro-altitude rate. It excludes the structural mounting and pitot-tube installation (##STR.STR-022) and the downstream navigation fusion (##NAV.NAV-010). ||

|| Requirement No:ADS-003 || Requirement: The ADS shall be dual-redundant on Stratos-7, AeroLynx-X2, and Nimbus-C3, and single-channel on Skyrunner-T1, with independent power feeds per ##PWR.PWR-012.
Derives From: ARP4761-FHA-ADS-01 ||

Header: REFERENCES
|| Requirement No:ADS-004 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, RTCA DO-160G, SAE AS8002A (AOA sensors), MIL-STD-1553B, ARINC 429, ICAO Doc 7488 (Manual of the ICAO Standard Atmosphere). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|ADS|Air Data System|
--------------------------------------------------
|ADM|Air Data Module|
--------------------------------------------------
|AOA|Angle of Attack|
--------------------------------------------------
|CAS|Calibrated Airspeed|
--------------------------------------------------
|TAS|True Airspeed|
--------------------------------------------------
|OAT|Outside Air Temperature|
--------------------------------------------------
|SAT|Static Air Temperature|
--------------------------------------------------
|TAT|Total Air Temperature|
--------------------------------------------------
|Qc|Impact Pressure|
--------------------------------------------------
|Ps|Static Pressure|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:ADS-005 || Requirement: The ADS shall sample pitot (total) pressure Pt, static pressure Ps, total air temperature TAT, AOA, and sideslip angle at no less than 100 Hz, and shall publish derived quantities at 20 Hz with end-to-end latency not exceeding 20 ms.
References: DO-178C-6.3.4 ||

|| Requirement No:ADS-006 || Requirement: The ADS shall compute calibrated airspeed (CAS) using the compressible-flow equation per ICAO Doc 7488, with accuracy ±1 kt or 1 % of reading (whichever is greater) in the range 40 kt to 350 kt at altitudes up to service ceiling.
References: ICAO Doc 7488 ||

|| Requirement No:ADS-007 || Requirement: The ADS shall compute pressure altitude referenced to ISA sea-level (1013.25 hPa) with accuracy ±15 ft at sea level, ±25 ft at 20 000 ft, and ±60 ft at 44 000 ft in steady conditions. ||

|| Requirement No:ADS-008 || Requirement: The ADS shall compute baro-altitude rate (vertical speed) with accuracy ±30 ft/min in steady flight, using a smoothing filter with time constant ≤ 1 s to avoid excessive lag. ||

|| Requirement No:ADS-009 || Requirement: The ADS shall compute Mach number from Pt and Ps with accuracy ±0.005 in the range M 0.2 to M 0.85, per ICAO Doc 7488 subsonic relations. ||

|| Requirement No:ADS-010 || Requirement: The ADS shall compute true airspeed (TAS) from CAS, pressure altitude, and SAT with accuracy ±3 kt or 1 % of reading across the flight envelope. ||

|| Requirement No:ADS-011 || Requirement: The ADS shall compute static air temperature (SAT) from TAT and Mach with recovery-factor correction (nominal 0.95 for typical stagnation probes), with SAT accuracy ±1 °C. ||

|| Requirement No:ADS-012 || Requirement: The ADS shall publish AOA in the range -10° to +25° with accuracy ±0.3° at AOA near α_stall, for use by the FCC envelope-protection function (##FCC.FCC-022).
Satisfies: ##FCC.FCC-022 ||

|| Requirement No:ADS-013 || Requirement: The ADS shall publish sideslip angle β in the range -15° to +15° with accuracy ±0.5° for use by the control laws. ||

|| Requirement No:ADS-014 || Requirement: The ADS shall detect a blocked pitot port within 3 s of onset via consistency cross-check: detected when indicated CAS deviates more than 15 kt from a GPS-groundspeed-minus-wind cross-reference for > 3 s. On detection, the ADS shall flag PITOT_SUSPECT and notify the operator per ##HMI.HMI-090. ||

|| Requirement No:ADS-015 || Requirement: The ADS shall publish BARO_ALT_MSG to the INS for vertical-channel aiding per ##INS.INS-044 at 10 Hz.
Satisfies: ##INS.INS-044 ||

|| Requirement No:ADS-016 || Requirement: The ADS shall apply position-error correction (PEC) calibration curves per platform, stored in on-board non-volatile memory, to remove the aerodynamic installation error of the static source. ||

|| Requirement No:ADS-017 || Requirement: On dual-redundant platforms, the ADS shall arbitrate between the two ADM LRUs using 2-out-of-2 agreement within 2 kt on CAS and 30 ft on pressure altitude; on persistent disagreement (> 200 ms), the ADS shall flag both with SUSPECT and default to a safe conservative output (lower CAS, higher altitude). ||

|| Requirement No:ADS-018 || Requirement: The ADS shall support barometric setting input (QNH) from 950 hPa to 1050 hPa for local altimeter-setting operations, updating altitude output within 500 ms of setting change. ||

|| Requirement No:ADS-019 || Requirement: The ADS shall support heated pitot and heated static ports per DO-160G §24 (icing environmental conditions), with heater-power monitoring and a HEATER_FAIL flag published when heater current falls below 50 % of nominal.
Satisfies: ##ICE.ICE-008 ||

Header: Interface
|| Requirement No:ADS-020 || Requirement: The ADS shall publish ADS_MSG at 20 Hz on the primary avionics bus per the ADS_Msg table (ADS-022).
References: MIL-STD-1553B, ARINC 429 ||

|| Requirement No:ADS-021 || Requirement: On Stratos-7 and AeroLynx-X2, the ADS shall be a 1553B remote terminal (RT 4). On Skyrunner-T1 and Nimbus-C3, the ADS shall publish ARINC 429 labels 205 (Mach), 206 (CAS), 203 (pressure altitude), 212 (altitude rate), 210 (TAS), 213 (SAT), 241 (AOA) at 20 Hz.
References: ARINC 429 ||

|| Requirement No:ADS-022 || Requirement: The ADS shall format the ADS_MSG per the following table.
Table Type: MESSAGE
Table Name or Description: ADS_Msg
Table: ADS_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|cas|float32|0 to 450 kt|0.1 kt|
--------------------------------------------------
|tas|float32|0 to 550 kt|0.1 kt|
--------------------------------------------------
|mach|float32|0 to 0.9|0.001|
--------------------------------------------------
|alt_pressure|float32|-2000 to +55000 ft|0.1 ft|
--------------------------------------------------
|alt_rate|float32|-8000 to +8000 ft/min|1 ft/min|
--------------------------------------------------
|sat|float32|-70 to +55 °C|0.1 °C|
--------------------------------------------------
|tat|float32|-70 to +90 °C|0.1 °C|
--------------------------------------------------
|aoa|float32|-15 to +30 deg|0.05 deg|
--------------------------------------------------
|beta|float32|-20 to +20 deg|0.05 deg|
--------------------------------------------------
|qnh|float32|950 to 1050 hPa|0.1 hPa|
--------------------------------------------------
|valid_flags|uint16|bitmask|bit|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:ADS-023 || Requirement: The ADS shall indicate validity per the ADS_Valid_Flags table.
Table Type: MESSAGE
Table Name or Description: ADS_Valid_Flags
Table: ADS_Valid_Flags
|Bit|Name|Meaning (1=valid)|
--------------------------------------------------
|0|CAS_OK|CAS within spec|
--------------------------------------------------
|1|ALT_OK|pressure altitude within spec|
--------------------------------------------------
|2|MACH_OK|Mach within spec|
--------------------------------------------------
|3|AOA_OK|AOA sensor within spec|
--------------------------------------------------
|4|BETA_OK|sideslip sensor within spec|
--------------------------------------------------
|5|TAT_OK|TAT sensor within spec|
--------------------------------------------------
|6|HEATER_OK|all heaters within current-draw spec|
--------------------------------------------------
|7|PITOT_SUSPECT|blocked-pitot detection triggered|
--------------------------------------------------
|8|STATIC_SUSPECT|blocked-static detection triggered|
--------------------------------------------------
|9|BIT_OK|BIT nominal|
--------------------------------------------------
|10-15|reserved|0|
-------------------------------------------------- ||

|| Requirement No:ADS-024 || Requirement: The ADS shall apply the limit envelope per the ADS_Limits table, and raise warnings to ##HMI.HMI-093 when any limit is approached within 5 % of its threshold.
Table Type: MESSAGE
Table Name or Description: ADS_Limits
Table: ADS_Limits
|Parameter|Lower Limit|Upper Limit|Source|
--------------------------------------------------
|CAS (at sea level)|Vs0|Vmo|platform|
--------------------------------------------------
|Mach (cruise)|n/a|Mmo|platform|
--------------------------------------------------
|Pressure altitude|-1000 ft|service ceiling|platform|
--------------------------------------------------
|AOA|n/a|0.9 × α_stall|##FCC.FCC-022|
--------------------------------------------------
|OAT|-55 °C|+50 °C|DO-160G §4|
-------------------------------------------------- ||

Header: Test
|| Requirement No:ADS-025 || Requirement: CAS accuracy (ADS-006) shall be verified by end-to-end pressure-chamber test injecting calibrated Pt/Ps at speeds 40, 80, 150, 250, and 350 kt at altitudes 0, 10 000, 25 000, 44 000 ft, demonstrating ±1 kt or ±1 % accuracy at each point.
Verifies: ADS-006
References: DO-160G-4, ICAO Doc 7488 ||

|| Requirement No:ADS-026 || Requirement: Blocked-pitot detection (ADS-014) shall be verified by fault injection: port blocked at cruise, climb, and descent phases with the ADS asserting PITOT_SUSPECT within 3 s of onset.
Verifies: ADS-014 ||

|| Requirement No:ADS-027 || Requirement: Pitot heater power monitoring (ADS-019) shall be verified by DO-160G §24 Category X icing exposure test, demonstrating heater current remaining above 50 % nominal throughout the exposure and HEATER_FAIL deasserted.
Verifies: ADS-019
References: DO-160G-24 ||

|| Requirement No:STR7-ADS-001 || Requirement: On Stratos-7, the ADS shall support M 0.72 cruise with compressibility-corrected CAS accuracy within ±1.5 kt, to enable Mach-hold autopilot per ##STR7-AUTO-001.
Satisfies: ##STR7-AUTO-001 ||

|| Requirement No:SKT1-ADS-001 || Requirement: On Skyrunner-T1, the ADS shall be a single ADM LRU with AOA and sideslip vanes rather than dedicated AOA probe, with accuracy relaxed to ±0.5° AOA.
Refines: ADS-012 ||

|| Requirement No:NBC3-ADS-001 || Requirement: On Nimbus-C3, the ADS shall provide TAS and wind-speed outputs with accuracy supporting ±10 s RTA conformance per ##FMS.FMS-020 under wind profiles up to 80 kt at cruise.
Satisfies: ##FMS.FMS-020 ||
