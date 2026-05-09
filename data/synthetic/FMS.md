#Requirement: REQ-FMS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: FMS
BASELINE: v2.1.0
ABSOLUTE PATH: /AeroSys/Common/FMS

Header: PURPOSE
|| Requirement No:FMS-001 || Requirement: This document specifies the Flight Management System (FMS) requirements for the Stratos-7, AeroLynx-X2, and Nimbus-C3 platforms. The Skyrunner-T1 does not host an FMS; its navigation is handled directly by the Navigation Integration function (##NAV.NAV-001). The FMS software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and DAL-B on Nimbus-C3. ||

Header: SCOPE
|| Requirement No:FMS-002 || Requirement: This module covers flight-plan management, lateral and vertical navigation (LNAV, VNAV), performance computation, fuel prediction, and procedure execution (SID, STAR, approach). It excludes low-level inertial integration (##INS.INS-001), GNSS receiver processing (##GPS.GPS-001), and the autopilot inner loop (##FCC.FCC-013). ||

|| Requirement No:FMS-003 || Requirement: This module does not address human-crewed cockpit MCDU interactions; all FMS operator interactions are performed through the GCS FMS page (##HMI.HMI-030). ||

Header: REFERENCES
|| Requirement No:FMS-004 || Requirement: The governing references for this module are: RTCA DO-178C, SAE ARP4754A, ARINC 424 (Navigation Database Coding), ARINC 702A (Advanced FMS), ARINC 429, RTCA DO-283B (Required Navigation Performance), RTCA DO-236C (Path Definition), and ICAO Doc 8168 (PANS-OPS). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|FMS|Flight Management System|
--------------------------------------------------
|LNAV|Lateral Navigation|
--------------------------------------------------
|VNAV|Vertical Navigation|
--------------------------------------------------
|SID|Standard Instrument Departure|
--------------------------------------------------
|STAR|Standard Terminal Arrival Route|
--------------------------------------------------
|RNP|Required Navigation Performance|
--------------------------------------------------
|TAS|True Airspeed|
--------------------------------------------------
|ECON|Economy (cost index driven speed)|
--------------------------------------------------
|LRC|Long-Range Cruise|
--------------------------------------------------
|NDB|Navigation Database|
--------------------------------------------------
|TOD|Top of Descent|
--------------------------------------------------
|TOC|Top of Climb|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:FMS-005 || Requirement: The FMS shall support the following operational modes:
    a) INIT
    b) PREFLIGHT
    c) ACTIVE
    d) SUSPENDED
    e) FAULT
Transitions shall be governed by the FMS_Mode_Transitions table (FMS-033). ||

|| Requirement No:FMS-006 || Requirement: While in INIT mode, the FMS shall load the active Navigation Database revision, verify its CRC against the signed manifest (##SEC.SEC-020), and reject any database whose AIRAC cycle has expired more than 56 days ago.
Satisfies: ##SEC.SEC-020 ||

|| Requirement No:FMS-007 || Requirement: While in PREFLIGHT mode, the FMS shall accept a filed flight plan of up to 200 waypoints, validate each waypoint against the Navigation Database (##NAV.NAV-010), and compute a provisional TOC/TOD pair before transitioning to ACTIVE. ||

|| Requirement No:FMS-008 || Requirement: While in ACTIVE mode, the FMS shall publish LNAV and VNAV guidance targets (##AUTO.AUTO-020) at 10 Hz and shall advance the active leg whenever the aircraft crosses the leg-transition boundary per ARINC 424 path terminator semantics. ||

|| Requirement No:FMS-009 || Requirement: While in SUSPENDED mode, the FMS shall hold the current position, disable automatic leg sequencing, and continue to publish the last-valid LNAV/VNAV targets unchanged until the operator issues a RESUME command per ##HMI.HMI-032. ||

|| Requirement No:FMS-010 || Requirement: Upon detection of a database integrity failure (CRC mismatch, signature invalid, or AIRAC expiry during flight), the FMS shall transition to FAULT mode within 100 ms and degrade to direct-to-waypoint operation using only operator-entered coordinates per ##HMI.HMI-033.
Satisfies: ##SEC.SEC-020 ||

Header: General
|| Requirement No:FMS-011 || Requirement: The FMS shall maintain a flight-plan structure supporting departure (SID), enroute, arrival (STAR), approach, and missed-approach segments with a maximum of 5 alternate airports and 3 company routes, per ARINC 702A.
References: ARINC 702A ||

|| Requirement No:FMS-012 || Requirement: The FMS shall compute lateral guidance targets to an accuracy that, when coupled with the Autopilot (##AUTO.AUTO-025), achieves total-system-error (TSE) cross-track ≤ 1.0 nmi 95 % in enroute phase, ≤ 0.5 nmi 95 % in terminal phase, and ≤ 0.3 nmi 95 % in approach phase, consistent with RNP 1.0, RNP 0.5, and RNP 0.3 respectively.
References: DO-283B ||

|| Requirement No:FMS-013 || Requirement: The FMS shall compute vertical guidance targets (commanded altitude, commanded vertical speed) maintaining altitude error ≤ 50 ft 95 % in cruise and ≤ 75 ft 95 % in climb/descent when coupled to the Autopilot. ||

|| Requirement No:FMS-014 || Requirement: The FMS shall support path-terminator types IF, TF, CF, DF, FA, FC, FD, FM, CA, CD, CI, CR, VA, VD, VI, VM, VR, HA, HF, HM as defined in ARINC 424 §5.
References: ARINC 424 ||

|| Requirement No:FMS-015 || Requirement: The FMS shall compute Top of Climb (TOC) and Top of Descent (TOD) points using the current aircraft mass (from ##FUEL.FUEL-010), forecast winds entered via ##HMI.HMI-035, and the performance model per FMS-040. TOD shall be recomputed every 10 s or whenever any input changes by more than 2 %. ||

|| Requirement No:FMS-016 || Requirement: The FMS shall compute cost-index-driven speed schedules (ECON) for climb, cruise, and descent using the Cost_Index_Schedule table (FMS-036), where cost index is a dimensionless ratio of time cost to fuel cost in the range 0 to 999. ||

|| Requirement No:FMS-017 || Requirement: The FMS shall compute fuel-flow prediction at each waypoint with root-sum-square error not exceeding 5 % of total predicted fuel consumption, using the platform performance model and current wind profile.
Satisfies: ##FUEL.FUEL-015 ||

|| Requirement No:FMS-018 || Requirement: The FMS shall continuously compute and publish remaining fuel at destination (FOD), remaining fuel at alternate (FOA), and minimum-fuel-alert condition (reaching destination with less than 30 minutes reserve at 1 500 ft above airport elevation) per ICAO Annex 6.
References: ICAO Annex 6 ||

|| Requirement No:FMS-019 || Requirement: The FMS shall recompute the active flight plan whenever the operator inserts, deletes, or modifies a waypoint, completing the recomputation within 2 s and publishing the new guidance targets within 500 ms of recomputation completion. ||

|| Requirement No:FMS-020 || Requirement: The FMS shall support 4D trajectory definition (lat, lon, altitude, time) with required-time-of-arrival (RTA) waypoints, maintaining RTA accuracy within ±10 s under nominal wind conditions (± 30 kt).
References: DO-236C ||

|| Requirement No:FMS-021 || Requirement: The FMS shall publish the active flight plan to the GCS at 1 Hz and immediately on any plan change, including full waypoint list, active leg index, predicted times, and predicted fuel at each waypoint.
Satisfies: ##GCS.GCS-040 ||

|| Requirement No:FMS-022 || Requirement: The FMS shall accept an uplinked flight plan modification (uplink-clearance) via the CDL (##CDL.CDL-040), require explicit operator confirmation per ##HMI.HMI-037 before activation, and log every uplink with timestamp and operator ID per ##FDR.FDR-012.
Satisfies: ##CDL.CDL-040 ||

|| Requirement No:FMS-023 || Requirement: The FMS shall support direct-to (DIRTO) operations by recomputing a great-circle track from current position to any valid waypoint within 500 ms of operator command and seamlessly activating the new leg without interruption of guidance output. ||

|| Requirement No:FMS-024 || Requirement: The FMS shall detect and flag flight-plan discontinuity (undefined leg termination) within 100 ms of reaching the discontinuity, suspending leg sequencing and publishing a DISCO alert to the operator. ||

|| Requirement No:FMS-025 || Requirement: The FMS shall support holding patterns per ARINC 424 with configurable inbound course, leg length (time or distance), and turn direction, maintaining the pattern until release or fuel-exhaustion alert per FMS-018.
References: ARINC 424 ||

|| Requirement No:FMS-026 || Requirement: The FMS shall compute takeoff performance (V1, Vr, V2 for turbine platforms; Vr only for piston and turboprop) using the platform performance model per FMS-040, departure runway data, wind, temperature, and aircraft mass. ||

|| Requirement No:FMS-027 || Requirement: The FMS shall compute landing performance (Vref, Vapp, required landing distance) using the platform performance model, arrival runway data, wind, temperature, and aircraft mass at predicted landing time. ||

|| Requirement No:FMS-028 || Requirement: The FMS shall support RNP APCH procedures with LPV or LNAV/VNAV minima when the host GNSS provides SBAS augmentation per ##GPS.GPS-015, degrading gracefully to LNAV-only minima if SBAS becomes unavailable.
References: DO-236C, DO-283B ||

|| Requirement No:FMS-029 || Requirement: The FMS shall abandon an active approach and execute the coded missed-approach procedure if any of the following occur: (a) GNSS integrity alert for > 5 s, (b) RNP containment exceeded, (c) operator missed-approach command, (d) autopilot disconnect.
Satisfies: ##AUTO.AUTO-040 ||

|| Requirement No:FMS-030 || Requirement: During an approach, the FMS shall publish lateral and vertical deviation signals to the HMI (##HMI.HMI-040) at 10 Hz with full-scale deflection corresponding to the approach procedure's containment (e.g. ±0.3 nmi lateral, ±75 ft vertical for RNP 0.3 LNAV/VNAV). ||

|| Requirement No:FMS-031 || Requirement: The FMS shall enforce speed constraints (maximum and minimum) at altitude-constrained waypoints, degrading ECON targets as necessary to satisfy the constraint, and flagging infeasible constraints (impossible to meet without violating flight envelope) within 100 ms. ||

|| Requirement No:FMS-032 || Requirement: The FMS shall support polar-region operations by switching to true-heading reference north of 82° N and south of 82° S, using grid-navigation reference frame per ARP4754A. ||

Header: Interface
|| Requirement No:FMS-033 || Requirement: The FMS shall publish LNAV_GUIDANCE_MSG and VNAV_GUIDANCE_MSG every 100 ms on the primary avionics bus (MIL-STD-1553B on STR7/ALX2, ARINC 429 at 100 kbps on NBC3) with the message format defined in the FMS_Guidance_Msg table (FMS-037).
Table Type: MESSAGE
Table Name or Description: FMS_Mode_Transitions
Table: FMS_Mode_Transitions
|From|To|Trigger|
--------------------------------------------------
|INIT|PREFLIGHT|database loaded, CRC valid|
--------------------------------------------------
|PREFLIGHT|ACTIVE|plan validated, operator ACTIVATE|
--------------------------------------------------
|ACTIVE|SUSPENDED|operator SUSPEND or loss of valid INS|
--------------------------------------------------
|SUSPENDED|ACTIVE|operator RESUME, INS valid|
--------------------------------------------------
|any|FAULT|FMS-010 condition|
--------------------------------------------------
|FAULT|INIT|operator RESET after database reload|
-------------------------------------------------- ||

|| Requirement No:FMS-034 || Requirement: The FMS shall consume aircraft state (position, velocity, altitude) from the NAV fusion function (##NAV.NAV-020) at 50 Hz and fuel state from ##FUEL.FUEL-020 at 1 Hz. ||

|| Requirement No:FMS-035 || Requirement: The FMS shall expose a flight-plan upload/download API over the maintenance Ethernet port per ##FCC.FCC-044, supporting ARINC 424 subset XML format with digital signature per ##SEC.SEC-022.
References: ARINC 424 ||

|| Requirement No:FMS-036 || Requirement: The FMS shall compute cost-index-driven speed targets per the Cost_Index_Schedule table.
Table Type: MESSAGE
Table Name or Description: Cost_Index_Schedule
Table: Cost_Index_Schedule
|Cost Index|Climb Speed|Cruise Speed|Descent Speed|Notes|
--------------------------------------------------
|0|Vy|LRC|Vmd|max range|
--------------------------------------------------
|50|Vy+10|M0.70|Vmd+10|ECON low|
--------------------------------------------------
|100|Vy+20|M0.72|Vmd+20|ECON mid|
--------------------------------------------------
|200|Vy+30|M0.74|Vmd+30|ECON high|
--------------------------------------------------
|999|Vmo-10|Mmo-0.01|Vmo-10|max speed|
--------------------------------------------------
Note: Values are representative of Stratos-7; AeroLynx-X2 and Nimbus-C3 schedules are published in platform-specific appendices. ||

Header: Tables
|| Requirement No:FMS-037 || Requirement: The FMS shall format the LNAV and VNAV guidance messages per the FMS_Guidance_Msg table.
Table Type: MESSAGE
Table Name or Description: FMS_Guidance_Msg
Table: FMS_Guidance_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|cmd_track|float32|0 to 360 deg|0.01 deg|
--------------------------------------------------
|cmd_altitude|int32|-1000 to 55000 ft|1 ft|
--------------------------------------------------
|cmd_airspeed|float32|40 to 350 kt|0.1 kt|
--------------------------------------------------
|xtk_error|float32|-10 to +10 nmi|0.001 nmi|
--------------------------------------------------
|vertical_dev|float32|-1000 to +1000 ft|1 ft|
--------------------------------------------------
|active_leg|uint16|0 to 199|integer|
--------------------------------------------------
|rta_seconds|int32|-3600 to +3600|1 s|
--------------------------------------------------
|valid_flag|uint8|0 or 1|bit|
-------------------------------------------------- ||

|| Requirement No:FMS-038 || Requirement: The FMS shall apply the speed constraints from the Speed_Envelope table for each aircraft phase; violations shall trigger operator alerts per ##HMI.HMI-045.
Table Type: MESSAGE
Table Name or Description: Speed_Envelope
Table: Speed_Envelope
|Phase|V_min (kt)|V_max (kt)|Configuration|
--------------------------------------------------
|Climb|Vy-10|Vmo|clean|
--------------------------------------------------
|Cruise|LRC-20|Vmo|clean|
--------------------------------------------------
|Descent|Vmd-10|Vmo|clean|
--------------------------------------------------
|Approach|Vapp-5|Vapp+20|flaps down|
--------------------------------------------------
|Landing|Vref-5|Vref+10|flaps full, gear down|
-------------------------------------------------- ||

|| Requirement No:FMS-039 || Requirement: Flight-plan validation shall reject any plan that fails any check in the Plan_Validation_Checks table.
Table Type: MESSAGE
Table Name or Description: Plan_Validation_Checks
Table: Plan_Validation_Checks
|Check|Criterion|Error Code|
--------------------------------------------------
|Waypoint exists|waypoint found in NDB|E_WPT_NOT_FOUND|
--------------------------------------------------
|Altitude feasible|alt ≤ service ceiling|E_ALT_INFEASIBLE|
--------------------------------------------------
|Leg length|0.1 nmi ≤ length ≤ 500 nmi|E_LEG_INVALID|
--------------------------------------------------
|Turn feasible|turn radius ≤ max per speed|E_TURN_INFEASIBLE|
--------------------------------------------------
|Fuel sufficient|predicted fuel > reserve|E_FUEL_INSUFFICIENT|
--------------------------------------------------
|Airspace auth|no restricted airspace|E_AIRSPACE_RESTRICTED|
-------------------------------------------------- ||

|| Requirement No:FMS-040 || Requirement: The FMS shall use a platform performance model with parameters published in the Performance_Model_Params appendix per platform. The model shall compute specific-range, specific-endurance, and fuel flow as a function of mass, altitude, Mach/CAS, temperature deviation from ISA, and wind. ||

Header: Test
|| Requirement No:FMS-041 || Requirement: LNAV cross-track accuracy (FMS-012) shall be verified by end-to-end simulation of 50 representative flight plans covering enroute, terminal, and approach phases, with recorded TSE statistics demonstrating compliance at the 95 % level.
Verifies: FMS-012
References: DO-283B, DO-178C-6.4 ||

|| Requirement No:FMS-042 || Requirement: Database integrity protection (FMS-006, FMS-010) shall be verified by injecting corrupted database images with known bit flips in the CRC region, the content region, and the signature region; the FMS shall reject all three within 100 ms of load attempt.
Verifies: FMS-006, FMS-010
References: DO-326A ||

|| Requirement No:FMS-043 || Requirement: Fuel prediction accuracy (FMS-017) shall be verified by flight-test on 20 representative missions per platform, comparing predicted versus actual fuel burn at each waypoint and demonstrating RSS error ≤ 5 % of total consumption.
Verifies: FMS-017 ||

|| Requirement No:FMS-044 || Requirement: Missed-approach execution (FMS-029) shall be verified by HIL testing with fault injection on GNSS integrity and operator command, demonstrating correct abandonment and published procedure execution within 2 s of trigger.
Verifies: FMS-029 ||

|| Requirement No:STR7-FMS-001 || Requirement: On Stratos-7, the FMS shall support long-endurance loiter operations with automatic racetrack or figure-8 pattern generation around an operator-defined point, maintaining position within ±200 m of the pattern centreline for durations up to 24 h.
Derives From: FMS-025 ||

|| Requirement No:ALX2-FMS-001 || Requirement: On AeroLynx-X2, the FMS shall support coalition multi-aircraft coordinated flight-plan execution with inter-aircraft separation constraints ≥ 1 nmi lateral and ≥ 500 ft vertical, maintained through the shared tactical datalink (##DLNK.DLNK-025).
Derives From: FMS-012 ||
