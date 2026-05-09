#Requirement: REQ-AUTO
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: AUTO
BASELINE: v2.2.1
ABSOLUTE PATH: /AeroSys/Common/AUTO

Header: PURPOSE
|| Requirement No:AUTO-001 || Requirement: This document specifies the Autopilot and Guidance Laws for the AeroSys Dynamics common flight-control core, applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3. The Autopilot software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:AUTO-002 || Requirement: This module covers outer-loop guidance laws (altitude hold, heading hold, track hold, airspeed hold, vertical speed hold), coupled guidance (LNAV, VNAV, approach, autoland), and automated manoeuvres (loiter, orbit, return-to-base, collision avoidance). It excludes inner-loop attitude/rate control (##FCC.FCC-013), flight-plan management (##FMS.FMS-005), and the collision-avoidance sensor (##RADAR.RADAR-020). ||

|| Requirement No:AUTO-003 || Requirement: The Autopilot is hosted on the FCC hardware as a separate software partition with ARINC 653 time and space partitioning on Stratos-7 and AeroLynx-X2.
References: ARINC 653, DO-297 ||

Header: REFERENCES
|| Requirement No:AUTO-004 || Requirement: The governing references are: RTCA DO-178C, SAE ARP4754A, RTCA DO-236C (Path Definition), RTCA DO-283B (RNP), RTCA DO-365B (DAA for UAS), RTCA DO-297 (IMA), ARINC 653, and MIL-F-9490D (Flight Control Systems) as historical guidance. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|ALT HOLD|Altitude Hold|
--------------------------------------------------
|HDG HOLD|Heading Hold|
--------------------------------------------------
|TRK HOLD|Track Hold|
--------------------------------------------------
|IAS HOLD|Indicated Airspeed Hold|
--------------------------------------------------
|VS HOLD|Vertical Speed Hold|
--------------------------------------------------
|LNAV|Lateral Navigation (FMS-coupled)|
--------------------------------------------------
|VNAV|Vertical Navigation (FMS-coupled)|
--------------------------------------------------
|APP|Approach|
--------------------------------------------------
|RTB|Return-To-Base|
--------------------------------------------------
|DAA|Detect and Avoid|
--------------------------------------------------
|TCAS|Traffic Collision Avoidance System|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:AUTO-005 || Requirement: The Autopilot shall support the following engageable modes:
    a) ALT HOLD
    b) HDG HOLD
    c) TRK HOLD
    d) IAS HOLD
    e) MACH HOLD (Stratos-7 only)
    f) VS HOLD
    g) LNAV
    h) VNAV
    i) APP
    j) AUTOLAND (platforms and airfields certified only)
    k) RTB
    l) LOITER
    m) DAA RESOLUTION
References: DO-236C ||

|| Requirement No:AUTO-006 || Requirement: The Autopilot shall require explicit operator engagement for any mode other than DAA RESOLUTION and RTB (which may be engaged autonomously per AUTO-020 and AUTO-022). Engagement requests shall be authenticated per ##SEC.SEC-010.
Satisfies: ##SEC.SEC-010 ||

|| Requirement No:AUTO-007 || Requirement: When two lateral modes are simultaneously requested (e.g. HDG HOLD and LNAV), the Autopilot shall arbitrate per the priority ladder: APP > AUTOLAND > DAA > LNAV > TRK HOLD > HDG HOLD, with the highest active priority winning and a mode annunciation change published within 100 ms.
Refines: AUTO-005 ||

|| Requirement No:AUTO-008 || Requirement: When two vertical modes are simultaneously requested (e.g. ALT HOLD and VNAV), the Autopilot shall arbitrate per the priority ladder: AUTOLAND > APP > DAA > VNAV > VS HOLD > ALT HOLD.
Refines: AUTO-005 ||

|| Requirement No:AUTO-009 || Requirement: If any inner-loop condition from ##FCC.FCC-009 is asserted (EMERGENCY mode), the Autopilot shall disengage all active modes within 50 ms, revert to published neutral guidance targets, and inhibit re-engagement until EMERGENCY clears.
Satisfies: ##EMS.EMS-006 ||

|| Requirement No:AUTO-010 || Requirement: On pilot-command override (stick force above the breakout threshold per ##HMI.HMI-050 or operator AUTOPILOT DISCONNECT press), the Autopilot shall disengage within 100 ms and publish the AUTO_DISENGAGED event to FDR per ##FDR.FDR-015.
Verifies: FDR-015 ||

Header: General
|| Requirement No:AUTO-011 || Requirement: The Autopilot shall execute outer-loop computations at 50 Hz with transport latency from input measurement to published command not exceeding 25 ms.
Derives From: ##FCC.FCC-014
References: DO-178C-6.3.4 ||

|| Requirement No:AUTO-012 || Requirement: In ALT HOLD, the Autopilot shall maintain pressure altitude within ±30 ft of the captured altitude under turbulence conditions not exceeding DO-160G §7 Category R (moderate turbulence). ||

|| Requirement No:AUTO-013 || Requirement: In HDG HOLD, the Autopilot shall maintain commanded magnetic heading within ±1° under still-air conditions and within ±2° under moderate turbulence. ||

|| Requirement No:AUTO-014 || Requirement: In TRK HOLD, the Autopilot shall maintain commanded ground track within ±0.5° provided GNSS velocity is valid (##GPS.GPS-012). ||

|| Requirement No:AUTO-015 || Requirement: In IAS HOLD, the Autopilot shall maintain commanded calibrated airspeed within ±3 kt in steady flight, with first-order equivalent time constant not exceeding 5 s for step commands within ±20 kt. ||

|| Requirement No:AUTO-016 || Requirement: In VS HOLD, the Autopilot shall maintain commanded vertical speed within ±100 ft/min under still-air conditions, limited by the current climb/descent performance envelope. ||

|| Requirement No:AUTO-017 || Requirement: In LNAV, the Autopilot shall track the active leg published by the FMS (##FMS.FMS-033), achieving cross-track error consistent with the RNP targets of ##FMS.FMS-012. ||

|| Requirement No:AUTO-018 || Requirement: In VNAV, the Autopilot shall track the vertical path defined by the FMS climb/descent schedule, transitioning between path-capture and altitude-capture per the geometry described in the VNAV_Transition table (AUTO-033). ||

|| Requirement No:AUTO-019 || Requirement: In APP, the Autopilot shall couple to the approach procedure published by the FMS, engaging glideslope capture when vertical deviation enters ±2 dots for 2 s and disengaging upon reaching the decision altitude without visual acquisition. ||

|| Requirement No:AUTO-020 || Requirement: On receipt of a validated DAA resolution advisory from ##RADAR.RADAR-025, the Autopilot shall autonomously engage DAA RESOLUTION mode within 200 ms, executing the commanded vertical or lateral manoeuvre at rates specified in the DAA_Resolution_Rates table (AUTO-035) until the conflict is resolved.
Satisfies: ##RADAR.RADAR-025
References: DO-365B ||

|| Requirement No:AUTO-021 || Requirement: On exit from DAA RESOLUTION, the Autopilot shall attempt to return to the lateral and vertical modes active prior to engagement, subject to operator confirmation where pre-engagement mode was not a FMS-coupled mode. ||

|| Requirement No:AUTO-022 || Requirement: On loss of CDL for more than the lost-link timeout per ##CDL.CDL-050, the Autopilot shall autonomously engage RTB mode within 1 s, commanding a climb to the configured safe altitude and lateral track to the operator-defined rally point per ##EMS.EMS-015.
Satisfies: ##EMS.EMS-015 ||

|| Requirement No:AUTO-023 || Requirement: In LOITER mode, the Autopilot shall fly a coordinated turn at commanded bank angle (default 25°, range 10° to 45°) holding commanded altitude, with direction and radius commanded via the FMS or direct operator input per ##HMI.HMI-055. ||

|| Requirement No:AUTO-024 || Requirement: The Autopilot shall support orbit-over-point, racetrack, and figure-8 patterns with pattern geometry configurable in the range 0.3 nmi to 20 nmi radius, 0.6 nmi to 40 nmi length. ||

|| Requirement No:AUTO-025 || Requirement: The Autopilot shall compute guidance commands to the FCC inner loop (##FCC.FCC-013) expressed as roll, pitch, and throttle targets, bounded by the Flight_Control_Limits table (##FCC.FCC-038).
Satisfies: ##FCC.FCC-013 ||

|| Requirement No:AUTO-026 || Requirement: The Autopilot shall gain-schedule lateral and vertical control gains by calibrated airspeed and altitude, with breakpoints not exceeding 20 kt CAS and 5 000 ft intervals. Interpolation between breakpoints shall be linear.
Derives From: ##FCC.FCC-020 ||

|| Requirement No:AUTO-027 || Requirement: The Autopilot shall limit commanded bank angle to 30° above 2 000 ft AGL and 15° below 2 000 ft AGL, unless the active mode is DAA RESOLUTION or AUTOLAND in which case AUTO-020 or AUTO-030 limits apply.
Refines: AUTO-023 ||

|| Requirement No:AUTO-028 || Requirement: The Autopilot shall reject any commanded altitude outside the certified envelope per ##FCC.FCC-038 and shall not initiate climb above the service ceiling or descent below MSA (minimum safe altitude) published by ##FMS.FMS-011.
Satisfies: ##FMS.FMS-011 ||

|| Requirement No:AUTO-029 || Requirement: On AUTOLAND-certified platforms (Stratos-7 at CAT I, subject to airfield certification), the Autopilot shall execute an autoland sequence including glideslope capture, flare initiation at 50 ft AGL radar altitude, and derotation after main-gear touchdown, keeping lateral deviation within ±3 m of runway centreline at touchdown.
References: DO-236C ||

|| Requirement No:AUTO-030 || Requirement: The Autopilot shall smooth mode transitions using blend functions with 0.5 s to 2 s cross-fade, avoiding step discontinuities in commanded roll, pitch, or throttle greater than 2° or 5 % respectively. ||

|| Requirement No:AUTO-031 || Requirement: The Autopilot shall publish an annunciation string (armed modes, active modes, reference values) at 2 Hz for operator display per ##HMI.HMI-060.
Satisfies: ##HMI.HMI-060 ||

Header: Interface
|| Requirement No:AUTO-032 || Requirement: The Autopilot shall consume the FMS_Guidance_Msg from ##FMS.FMS-037 at 10 Hz and the INS state from ##INS.INS-020 at 200 Hz via internal software interface in the common FCC partition.
Satisfies: ##FMS.FMS-037 ||

|| Requirement No:AUTO-033 || Requirement: The Autopilot shall expose mode-engagement and target-set commands over an internal software interface to the GCS command dispatcher (##CDL.CDL-030), accepting fields per the AP_Command_Msg table.
Table Type: MESSAGE
Table Name or Description: VNAV_Transition
Table: VNAV_Transition
|From|To|Trigger|Blend Time|
--------------------------------------------------
|PATH|ALT CAPTURE|altitude error < 200 ft|1.0 s|
--------------------------------------------------
|ALT CAPTURE|ALT HOLD|altitude error < 50 ft for 2 s|0.5 s|
--------------------------------------------------
|ALT HOLD|PATH|VNAV leg sequenced, new target|1.0 s|
--------------------------------------------------
|any|VS HOLD|operator VS preselect|0.5 s|
--------------------------------------------------
References: DO-236C ||

|| Requirement No:AUTO-034 || Requirement: The Autopilot shall format the AP_Command_Msg per the following table.
Table Type: MESSAGE
Table Name or Description: AP_Command_Msg
Table: AP_Command_Msg
|Field|Type|Range|Notes|
--------------------------------------------------
|mode_lat|uint8|enum {OFF,HDG,TRK,LNAV,APP,RTB,LOITER,DAA,AUTOLAND}|active lateral|
--------------------------------------------------
|mode_vert|uint8|enum {OFF,ALT,VS,VNAV,APP,AUTOLAND,DAA}|active vertical|
--------------------------------------------------
|cmd_hdg|uint16|0-3599 (0.1 deg)|HDG HOLD ref|
--------------------------------------------------
|cmd_alt|int32|-1000 to 55000 ft|ALT HOLD ref|
--------------------------------------------------
|cmd_vs|int16|-6000 to +6000 ft/min|VS HOLD ref|
--------------------------------------------------
|cmd_ias|uint16|40 to 350 kt|IAS HOLD ref|
--------------------------------------------------
|cmd_mach|uint16|0 to 999 (0.001)|MACH HOLD ref, STR7 only|
--------------------------------------------------
|cmd_bank|uint8|5 to 45 deg|loiter bank|
--------------------------------------------------
|seq_num|uint32|monotonic|auth|
--------------------------------------------------
|auth_tag|bytes(16)|HMAC-SHA256 trunc|per SEC-010|
--------------------------------------------------
Satisfies: ##SEC.SEC-010 ||

Header: Tables
|| Requirement No:AUTO-035 || Requirement: The Autopilot shall execute DAA resolution manoeuvres at the rates specified in the DAA_Resolution_Rates table.
Table Type: MESSAGE
Table Name or Description: DAA_Resolution_Rates
Table: DAA_Resolution_Rates
|Manoeuvre|Rate|Duration|Max Deviation|
--------------------------------------------------
|Climb|1500 ft/min|until clearance|+2000 ft|
--------------------------------------------------
|Descend|1500 ft/min|until clearance|-2000 ft|
--------------------------------------------------
|Turn left|3 deg/s|until clearance|90 deg|
--------------------------------------------------
|Turn right|3 deg/s|until clearance|90 deg|
--------------------------------------------------
|Speed decrease|5 kt/s|until clearance|-30 kt|
--------------------------------------------------
References: DO-365B ||

|| Requirement No:AUTO-036 || Requirement: The Autopilot shall limit capture-transition rates per the Capture_Rates table to avoid large transient deviations.
Table Type: MESSAGE
Table Name or Description: Capture_Rates
Table: Capture_Rates
|Capture|Max Rate|
--------------------------------------------------
|Altitude capture|vertical speed ≤ 1000 ft/min residual|
--------------------------------------------------
|Heading capture|bank angle ≤ 25 deg|
--------------------------------------------------
|Glideslope capture|pitch rate ≤ 2 deg/s|
--------------------------------------------------
|Track capture|bank angle ≤ 25 deg|
-------------------------------------------------- ||

Header: Test
|| Requirement No:AUTO-037 || Requirement: ALT HOLD accuracy (AUTO-012) shall be verified by HIL simulation of 20 min steady flight in moderate turbulence, demonstrating altitude excursions within ±30 ft for 95 % of the run.
Verifies: AUTO-012 ||

|| Requirement No:AUTO-038 || Requirement: DAA RESOLUTION engagement latency (AUTO-020) shall be verified by simulated intruder injection on the HIL rig with resolution advisory issued at random phase; the Autopilot shall demonstrate mode engagement within 200 ms and correct manoeuvre execution within one full rate-limited response.
Verifies: AUTO-020
References: DO-365B ||

|| Requirement No:AUTO-039 || Requirement: RTB engagement on lost-link (AUTO-022) shall be verified by HIL test suspending CDL for durations of 10 s, 30 s, and 60 s, with engagement at the configured timeout per ##CDL.CDL-050 and correct track to the rally point.
Verifies: AUTO-022 ||

|| Requirement No:AUTO-040 || Requirement: Autoland touchdown dispersion (AUTO-029, Stratos-7 only) shall be verified by 30 simulated approaches with representative wind profiles (headwind, tailwind, crosswind up to 15 kt), demonstrating ≥ 95 % of touchdowns within ±3 m of centreline.
Verifies: AUTO-029 ||

|| Requirement No:STR7-AUTO-001 || Requirement: On Stratos-7, the Autopilot shall support MACH HOLD above FL280 with accuracy ±0.005 Mach in steady cruise.
Derives From: AUTO-005 ||

|| Requirement No:STR7-AUTO-002 || Requirement: On Stratos-7, AUTOLAND shall be certified at CAT I only, requiring decision height ≥ 200 ft and runway visual range ≥ 550 m.
Refines: AUTO-029 ||

|| Requirement No:STR7-AUTO-003 || Requirement: On Stratos-7, the Autopilot shall support a dedicated ISR station-keeping mode maintaining position within ±100 m of a ground target for orbits of up to 18 h at 15 000 to 25 000 ft. ||

|| Requirement No:STR7-AUTO-004 || Requirement: On Stratos-7, the Autopilot shall execute emergency descent profiles (-5 000 ft/min) on commanded EMERGENCY DESCENT without operator confirmation, respecting the Mmo/Vmo envelope. ||

|| Requirement No:ALX2-AUTO-001 || Requirement: On AeroLynx-X2, the Autopilot shall coordinate differential thrust commands (##ALX2-FCC-002) when commanded yaw rate exceeds rudder authority below 90 kt CAS.
Satisfies: ALX2-FCC-002 ||

|| Requirement No:ALX2-AUTO-002 || Requirement: On AeroLynx-X2, the Autopilot shall support maritime search patterns (expanding square, sector search, track crawl) with configurable spacing 0.5 nmi to 5 nmi. ||

|| Requirement No:ALX2-AUTO-003 || Requirement: On AeroLynx-X2, the Autopilot shall execute single-engine-out procedures coordinated with ##ALX2-FCC-003, maintaining altitude ±100 ft with the surviving engine at up to 95 % power. ||

|| Requirement No:SKT1-AUTO-001 || Requirement: On Skyrunner-T1, the Autopilot shall not support MACH HOLD, AUTOLAND, or CAT-II/III approaches. Only ALT HOLD, HDG HOLD, TRK HOLD, IAS HOLD, VS HOLD, LNAV, VNAV, LOITER, RTB, and DAA RESOLUTION shall be supported.
Refines: AUTO-005 ||

|| Requirement No:SKT1-AUTO-002 || Requirement: On Skyrunner-T1, LOITER bank angle shall be limited to 20° due to reduced structural margins and the lower service ceiling. ||

|| Requirement No:NBC3-AUTO-001 || Requirement: On Nimbus-C3, the Autopilot shall respect RTA constraints per ##FMS.FMS-020 to maintain civil ATM conformance, adjusting cruise Mach/CAS within ±10 % of ECON target to preserve ±10 s RTA accuracy. ||

|| Requirement No:NBC3-AUTO-002 || Requirement: On Nimbus-C3, the Autopilot shall engage DAA RESOLUTION at advisory levels consistent with manned-aircraft equipage (TCAS II RA) per DO-365B §4.
References: DO-365B ||
