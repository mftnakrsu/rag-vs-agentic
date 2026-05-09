#Requirement: REQ-FCC
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: FCC
BASELINE: v2.3.0
ABSOLUTE PATH: /AeroSys/Common/FCC

Header: PURPOSE
|| Requirement No:FCC-001 || Requirement: This document specifies the functional, performance, interface, and safety requirements of the Flight Control Computer (FCC) software and hardware interfaces for the AeroSys Dynamics common flight-control core, applicable to the Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3 platforms. The FCC software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and at DAL-B on Skyrunner-T1 and Nimbus-C3. The associated programmable logic shall be developed at DO-254 Level A or Level B per the same platform mapping. ||

Header: SCOPE
|| Requirement No:FCC-002 || Requirement: This module covers the normal, degraded, and emergency operation of the FCC including control-law scheduling, actuator command arbitration, cross-channel monitoring, mode management, and fail-safe behaviour. It excludes the mechanical design of servo actuators (##STR.STR-012), the engine control laws (##ENG.ENG-010), and the ground segment (##GCS.GCS-001).
References: ARP4754A ||

|| Requirement No:FCC-003 || Requirement: The FCC shall be implemented as two or three independent lanes (channels) depending on platform, where each lane executes an identical Operational Flight Program (OFP) and exchanges state through a cross-channel data link (CCDL).
Derives From: ARP4761-FHA-FCC-01 ||

Header: REFERENCES
|| Requirement No:FCC-004 || Requirement: The governing references for this module are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, MIL-STD-1553B, ARINC 429, RTCA DO-160G, RTCA DO-326A, RTCA DO-297 for IMA partitioning where applicable. Compliance shall be demonstrated per the Platform Certification Matrix (AeroSys-PCM-001). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|FCC|Flight Control Computer|
--------------------------------------------------
|OFP|Operational Flight Program|
--------------------------------------------------
|CCDL|Cross-Channel Data Link|
--------------------------------------------------
|DAL|Design Assurance Level|
--------------------------------------------------
|LRU|Line-Replaceable Unit|
--------------------------------------------------
|MC/DC|Modified Condition / Decision Coverage|
--------------------------------------------------
|BIT|Built-In Test|
--------------------------------------------------
|MVS|Mid-Value Select|
--------------------------------------------------
|FBW|Fly-By-Wire|
--------------------------------------------------
|HIL|Hardware-In-the-Loop|
--------------------------------------------------
|RTB|Return-To-Base|
--------------------------------------------------
|IMA|Integrated Modular Avionics|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:FCC-005 || Requirement: The FCC shall support the following top-level operational modes:
    a) OFF
    b) INIT
    c) GROUND
    d) TAKEOFF
    e) CLIMB
    f) CRUISE
    g) DESCENT
    h) APPROACH
    i) LANDING
    j) EMERGENCY
Transitions between these modes shall be governed by the Mode_Transition table (FCC-037).
References: ARP4754A-5.3 ||

|| Requirement No:FCC-006 || Requirement: When transitioning from INIT to GROUND, the FCC shall complete the power-on BIT (PBIT) sequence within 15 s, and shall inhibit any actuator command with amplitude greater than 0.5° or 1 %/s until PBIT reports PASS.
Verifies: BIT-005
Satisfies: ##EMS.EMS-004
References: DO-178C-6.3.1 ||

|| Requirement No:FCC-007 || Requirement: While in GROUND mode, the FCC shall accept control-surface deflection commands only via the ground-maintenance command path (##GCS.GCS-022), and shall reject any surface command originating from the autopilot or guidance laws (##AUTO.AUTO-001).
Derives From: FCC-005 ||

|| Requirement No:FCC-008 || Requirement: When transitioning from TAKEOFF to CLIMB, the FCC shall detect positive climb rate (≥ 200 ft/min sustained for 3 s) and weight-off-wheels asserted on both main gear (##LDG.LDG-015), and shall then enable the inner-loop climb schedule within 100 ms of both conditions being met. ||

|| Requirement No:FCC-009 || Requirement: If any of the following conditions occur, the FCC shall autonomously transition to EMERGENCY mode within 50 ms and notify the GCS per ##EMS.EMS-010: (a) loss of valid INS data for ≥ 500 ms with no GPS/barometric fallback valid, (b) dual-channel CCDL disagreement on critical parameters persisting for ≥ 200 ms, (c) loss of FCC primary power for ≥ 50 ms.
Satisfies: ##EMS.EMS-001
References: ARP4761-FHA-FCC-02 ||

|| Requirement No:FCC-010 || Requirement: Upon entering EMERGENCY mode, the FCC shall command wings-level attitude (bank angle ≤ 5°, pitch ≤ 3°) and hold current altitude ±100 ft until GCS issues a valid command or until the Emergency Management function asserts a flight-termination sequence per ##EMS.EMS-020.
Derives From: FCC-009 ||

|| Requirement No:FCC-011 || Requirement: While in any mode other than OFF, the FCC shall accept external mode-change requests only if they are cryptographically authenticated per ##SEC.SEC-010 and received with a valid sequence number not reused within the current flight.
Satisfies: ##SEC.SEC-003
References: DO-326A ||

|| Requirement No:FCC-012 || Requirement: The FCC shall record every mode transition with UTC timestamp (resolution ≤ 1 ms), origin channel, predecessor mode, successor mode, and triggering condition into the non-volatile mode-transition log (##FDR.FDR-008), retained for at least the most recent 50 flight hours.
Verifies: FDR-008 ||

Header: General
|| Requirement No:FCC-013 || Requirement: The FCC shall execute the inner-loop control law at 200 Hz with a cycle-to-cycle jitter not exceeding 1 ms on 95 % of cycles measured over any 10-second window, and not exceeding 2 ms on any cycle.
Note: Timing determinism supports DO-178C DAL-A low-level testing and worst-case execution-time (WCET) analysis objectives.
Derives From: ARP4754A-SYS-004
References: DO-178C-6.3.4 ||

|| Requirement No:FCC-014 || Requirement: The FCC shall execute the outer-loop guidance-tracking law at 50 Hz with cycle-to-cycle jitter not exceeding 2 ms on 95 % of cycles measured over any 10-second window. ||

|| Requirement No:FCC-015 || Requirement: The FCC shall execute background health-monitoring and BIT tasks at a scheduled rate of 10 Hz, and shall guarantee that no background task delays the inner or outer loop beyond the jitter bounds specified in FCC-013 and FCC-014.
Refines: FCC-013, FCC-014
References: DO-178C-6.3.4, ARINC 653 ||

|| Requirement No:FCC-016 || Requirement: The FCC shall receive attitude (pitch, roll, yaw), body rates (p, q, r), and body accelerations from the INS via ##INS.INS-020 at a minimum 200 Hz rate with a transport latency not exceeding 5 ms end-to-end.
Satisfies: INS-020 ||

|| Requirement No:FCC-017 || Requirement: When the measured INS attitude update rate drops below 180 Hz for more than 50 ms, or when the INS VALID bit deasserts, the FCC shall set the INS_DEGRADED flag, switch to the secondary attitude source (GPS-aided AHRS per ##NAV.NAV-015) within 100 ms, and notify the operator per ##HMI.HMI-010.
Refines: FCC-016 ||

|| Requirement No:FCC-018 || Requirement: The FCC shall arbitrate primary control-surface commands across channels using a mid-value select (MVS) scheme when three channels are available, and using a damage-tolerant cross-check with fault isolation when two channels are available.
Derives From: ARP4761-FHA-FCC-03 ||

|| Requirement No:FCC-019 || Requirement: When an inter-channel disagreement on any primary control command exceeds 5 % of full-scale for more than 100 ms, the FCC shall declare the disagreeing channel FAULTED, isolate its outputs from the actuator bus within 50 ms, and continue operation on the remaining channels.
Refines: FCC-018
Verifies: BIT-012 ||

|| Requirement No:FCC-020 || Requirement: The FCC shall command roll, pitch, and yaw axes using gain-scheduled control laws parameterised by calibrated airspeed and pressure altitude, with schedule breakpoints at intervals not exceeding 20 kt and 5 000 ft respectively. Interpolation between breakpoints shall be linear. ||

|| Requirement No:FCC-021 || Requirement: The FCC shall limit commanded normal load factor to the Flight_Load_Limits table (FCC-038), including a 5 % margin below the structural design limit load.
Satisfies: ##STR.STR-008 ||

|| Requirement No:FCC-022 || Requirement: The FCC shall limit commanded angle of attack to 0.9 × α_stall with a recovery margin of 3°, where α_stall is derived from the current aircraft configuration (flaps, gear, weight) per ##ADS.ADS-012. ||

|| Requirement No:FCC-023 || Requirement: The FCC shall detect actuator runaway (commanded-versus-measured surface error > 10 % of full deflection for > 200 ms) on any primary surface, disengage the offending actuator channel within 50 ms, and command the remaining channels to null the disturbance torque.
Satisfies: ##EMS.EMS-006 ||

|| Requirement No:FCC-024 || Requirement: The FCC shall maintain closed-loop attitude tracking performance of ±0.5° (roll, pitch) and ±1.0° (yaw) under steady trim conditions at cruise (calibrated airspeed within ±20 kt of recommended cruise speed, altitude within ±500 ft of commanded altitude), in still-air conditions defined by DO-160G §7. ||

|| Requirement No:FCC-025 || Requirement: The FCC shall maintain body-rate command tracking with a first-order equivalent time constant not exceeding 150 ms and overshoot not exceeding 15 % for step inputs within the linear envelope of FCC-038. ||

|| Requirement No:FCC-026 || Requirement: The FCC shall provide a trim-integrator function on each axis with integrator reset on mode change and integrator freeze on surface saturation (commanded deflection within 2 % of any limit in FCC-038). ||

|| Requirement No:FCC-027 || Requirement: The FCC shall apply structural-mode notch filters on all inertial measurements before inner-loop processing, with notch centre frequencies and widths specified in the Structural_Notch_Filters table (FCC-039).
Satisfies: ##STR.STR-020 ||

|| Requirement No:FCC-028 || Requirement: The FCC shall apply anti-windup protection on every integrator that feeds an actuator command, ensuring that the integrator state cannot increase when the corresponding actuator command is saturated against a limit in FCC-038. ||

|| Requirement No:FCC-029 || Requirement: The FCC shall compute and publish a control-law authority margin (percentage of remaining command authority on each axis) at 50 Hz for operator display via ##HMI.HMI-015 and for recording per ##FDR.FDR-004. ||

|| Requirement No:FCC-030 || Requirement: If the FCC detects dual-axis command saturation on roll and pitch simultaneously for more than 500 ms, the FCC shall escalate a CONTROL_SATURATED condition to the Emergency Management function per ##EMS.EMS-007 and reduce commanded manoeuvre rates to 50 % of nominal until the condition clears. ||

|| Requirement No:FCC-031 || Requirement: The FCC shall validate every incoming command from the GCS (##CDL.CDL-030) for range, rate, and sequence number, and shall reject any command that violates the Command_Validation table (FCC-040) without propagating it to the control laws.
Satisfies: ##SEC.SEC-008 ||

|| Requirement No:FCC-032 || Requirement: The FCC shall accept guidance targets (commanded heading, altitude, airspeed) only from the Autopilot function (##AUTO.AUTO-010) while in CRUISE, CLIMB, or DESCENT modes; in APPROACH mode, guidance targets shall originate exclusively from the FMS approach procedure (##FMS.FMS-030).
Derives From: FCC-005 ||

|| Requirement No:FCC-033 || Requirement: The FCC shall detect and isolate a stuck-at-one or stuck-at-zero fault in any inertial measurement input within 200 ms by cross-comparison with the CCDL peer channel, and shall flag the input INVALID in the output bus messages. ||

|| Requirement No:FCC-034 || Requirement: The FCC shall provide a time-reference service aligned to UTC with accuracy ≤ 1 ms when GPS time is valid (##GPS.GPS-010), and with free-wheel drift ≤ 100 ppm when GPS time is unavailable. ||

|| Requirement No:FCC-035 || Requirement: The FCC shall operate continuously over the environmental envelope defined in DO-160G §4 Category A2 (operating temperature -40 °C to +70 °C, humidity 95 %, altitude up to 55 000 ft). ||

|| Requirement No:FCC-036 || Requirement: The FCC shall sustain uninterrupted inner-loop execution through a primary power interruption of up to 50 ms per MIL-STD-704F and DO-160G §16 Category Z, drawing from the hold-up energy storage specified in ##PWR.PWR-018.
Satisfies: ##PWR.PWR-018 ||

|| Requirement No:FCC-037 || Requirement: The FCC shall enforce mode-transition preconditions according to the following Mode_Transition table. Any transition request whose precondition is not satisfied shall be rejected and logged per FCC-012.
Table Type: MESSAGE
Table Name or Description: Mode_Transition
Table: Mode_Transition
|From|To|Precondition|Max Latency|
--------------------------------------------------
|INIT|GROUND|PBIT=PASS, WoW=TRUE, airspeed<10 kt|200 ms|
--------------------------------------------------
|GROUND|TAKEOFF|throttle>85 %, brakes_released, WoW=TRUE|100 ms|
--------------------------------------------------
|TAKEOFF|CLIMB|WoW=FALSE both main, climb_rate>200 ft/min for 3 s|100 ms|
--------------------------------------------------
|CLIMB|CRUISE||Δalt| < 200 ft for 10 s at commanded altitude|500 ms|
--------------------------------------------------
|CRUISE|DESCENT|descent_target_active, Δalt_cmd < -100 ft|500 ms|
--------------------------------------------------
|DESCENT|APPROACH|approach_armed, FMS approach procedure active|500 ms|
--------------------------------------------------
|APPROACH|LANDING|altitude_agl<100 ft, airspeed<Vapp+10 kt|100 ms|
--------------------------------------------------
|LANDING|GROUND|WoW=TRUE both main for 2 s, groundspeed<40 kt|200 ms|
--------------------------------------------------
|any|EMERGENCY|FCC-009 condition|50 ms|
--------------------------------------------------
References: ARP4754A-5.3 ||

Header: Interface
|| Requirement No:FCC-038 || Requirement: The FCC shall command the primary flight-control surfaces within the ranges and rates specified in the Flight_Control_Limits table. Commands outside these ranges shall be clamped to the nearest limit and the EXCEEDANCE flag shall be set per FCC-029.
Table Type: MESSAGE
Table Name or Description: Flight_Control_Limits
Table: Flight_Control_Limits
|Signal|Unit|Range|Default|Max Rate|
--------------------------------------------------
|pitch_cmd|deg|-25 to +25|0.0|60 deg/s|
--------------------------------------------------
|roll_cmd|deg|-60 to +60|0.0|120 deg/s|
--------------------------------------------------
|yaw_rate_cmd|deg/s|-15 to +15|0.0|30 deg/s/s|
--------------------------------------------------
|throttle_cmd|%|0 to 100|0.0|20 %/s|
--------------------------------------------------
|flap_cmd|deg|0 to 40|0.0|5 deg/s|
--------------------------------------------------
|speedbrake_cmd|%|0 to 100|0.0|25 %/s|
--------------------------------------------------
References: DO-178C-6.3.1 ||

|| Requirement No:FCC-039 || Requirement: The FCC shall apply structural-mode notch filters on inertial rate inputs using the centre frequencies and 3 dB bandwidths defined in the Structural_Notch_Filters table, where filter coefficients are derived per platform.
Table Type: MESSAGE
Table Name or Description: Structural_Notch_Filters
Table: Structural_Notch_Filters
|Platform|Axis|Centre Freq (Hz)|Bandwidth (Hz)|Attenuation (dB)|
--------------------------------------------------
|Stratos-7|pitch|9.2|1.5|-18|
--------------------------------------------------
|Stratos-7|roll|14.1|2.0|-18|
--------------------------------------------------
|AeroLynx-X2|pitch|11.8|1.8|-15|
--------------------------------------------------
|AeroLynx-X2|roll|17.4|2.2|-15|
--------------------------------------------------
|Skyrunner-T1|pitch|22.5|3.0|-12|
--------------------------------------------------
|Nimbus-C3|pitch|8.7|1.4|-15|
--------------------------------------------------
References: ARP4761 ||

|| Requirement No:FCC-040 || Requirement: The FCC shall validate GCS-originated commands against the Command_Validation table and reject any non-conforming command with an error code returned per ##CDL.CDL-035.
Table Type: MESSAGE
Table Name or Description: Command_Validation
Table: Command_Validation
|Field|Type|Valid Range|Rate Limit|Sequence Check|
--------------------------------------------------
|cmd_altitude|int32|0 to 55000 ft|1000 ft/s|monotonic seq #|
--------------------------------------------------
|cmd_heading|uint16|0 to 3599 (0.1 deg)|30 deg/s|monotonic seq #|
--------------------------------------------------
|cmd_airspeed|uint16|40 to 350 kt|10 kt/s|monotonic seq #|
--------------------------------------------------
|cmd_mode|uint8|enum {0..9}|n/a|auth token valid|
--------------------------------------------------
Satisfies: ##SEC.SEC-008 ||

|| Requirement No:FCC-041 || Requirement: On Stratos-7 and AeroLynx-X2, the FCC shall publish the FCC_ATTITUDE_MSG on MIL-STD-1553B Bus A every 20 ms (50 Hz) with the FCC channel as Remote Terminal 5 and the Bus Controller located in the Vehicle Management Computer. On loss of Bus A (3 consecutive missed cycles), the FCC shall fail over to Bus B within 20 ms.
References: MIL-STD-1553B ||

|| Requirement No:FCC-042 || Requirement: On Skyrunner-T1 and Nimbus-C3, the FCC shall publish the FCC_ATTITUDE_WORD on ARINC 429 low-speed (12.5 kbps) with label 325 (attitude) at 50 Hz and label 326 (body rates) at 50 Hz, using SDI bits 9-10 to identify the source channel.
References: ARINC 429 ||

|| Requirement No:FCC-043 || Requirement: The FCC shall accept the INS_STATE_MSG from the INS LRU on MIL-STD-1553B (STR7/ALX2) or ARINC 429 labels 324/325/361 (SKT1/NBC3) at 200 Hz, with data freshness validated by a 2-bit counter that increments each cycle and wraps at 3.
Satisfies: ##INS.INS-022 ||

|| Requirement No:FCC-044 || Requirement: The FCC shall expose a dedicated maintenance Ethernet port (100BASE-TX, RJ-45, shielded) active only when WoW is asserted on both main gear and groundcrew-inhibit is released per ##LDG.LDG-020. All maintenance traffic shall be authenticated per ##SEC.SEC-015. ||

|| Requirement No:FCC-045 || Requirement: The FCC shall consume nominal 28 V DC from the primary essential bus per MIL-STD-704F, with operating range 22 V to 32 V DC, transient tolerance to 80 V for 100 ms, and under-voltage shutdown below 18 V DC after 200 ms of sustained under-voltage.
Satisfies: ##PWR.PWR-008 ||

|| Requirement No:FCC-046 || Requirement: The FCC shall exchange channel state (mode vote, command vote, fault state, health counters) over CCDL every 5 ms using deterministic TDMA slotting, with CRC-32 integrity on every frame and rejection of frames whose CRC fails. ||

|| Requirement No:FCC-047 || Requirement: The FCC shall report BIT-detected failures via the FCC_BIT_STATUS_MSG at 1 Hz to the Vehicle Management Computer and at the nominal FDR recording rate per ##FDR.FDR-005.
Satisfies: ##BIT.BIT-008 ||

|| Requirement No:FCC-048 || Requirement: The FCC shall consume a discrete WoW input from each main landing-gear strut per ##LDG.LDG-015 at a debounce period of 100 ms, using 2-out-of-3 voting across redundant sensors where provided. ||

Header: Tables
|| Requirement No:FCC-049 || Requirement: The FCC shall limit commanded normal load factor (Nz), roll rate (p), and pitch rate (q) per the Flight_Load_Limits table as a function of configuration. Exceeding any limit shall trigger rate reduction per FCC-030.
Table Type: MESSAGE
Table Name or Description: Flight_Load_Limits
Table: Flight_Load_Limits
|Configuration|Nz_max (g)|Nz_min (g)|p_max (deg/s)|q_max (deg/s)|
--------------------------------------------------
|Clean, gear up|+3.5|-1.0|120|60|
--------------------------------------------------
|Flaps intermediate|+2.5|-0.5|90|45|
--------------------------------------------------
|Flaps full, gear down|+2.0|-0.0|60|30|
--------------------------------------------------
|Payload > 80 % MTOW|+2.8|-0.5|90|45|
--------------------------------------------------
Satisfies: ##STR.STR-008 ||

|| Requirement No:FCC-050 || Requirement: The FCC shall map each defined fault condition to the recovery action specified in the Fault_Recovery_Map table.
Table Type: MESSAGE
Table Name or Description: Fault_Recovery_Map
Table: Fault_Recovery_Map
|Fault Code|Description|Recovery Action|Max Latency|Escalation|
--------------------------------------------------
|F_INS_LOSS|INS invalid ≥ 500 ms|switch to AHRS, notify GCS|100 ms|EMS after 2 s|
--------------------------------------------------
|F_CCDL_DIS|CCDL disagreement ≥ 200 ms|isolate minority channel|50 ms|EMS if majority<2|
--------------------------------------------------
|F_ACT_RUN|actuator runaway|disengage channel|50 ms|EMS after 1 s|
--------------------------------------------------
|F_PWR_DIP|power < 22 V > 50 ms|switch to essential bus|50 ms|EMS at 200 ms|
--------------------------------------------------
|F_SAT_DUAL|roll+pitch saturation 500 ms|reduce cmd rate 50 %|100 ms|EMS at 5 s|
--------------------------------------------------
Satisfies: ##EMS.EMS-008 ||

|| Requirement No:FCC-051 || Requirement: The FCC shall publish the FCC_HEALTH_WORD containing the bit-packed status summary defined in the FCC_Health_Word table at 10 Hz on the primary avionics bus.
Table Type: MESSAGE
Table Name or Description: FCC_Health_Word
Table: FCC_Health_Word
|Bit|Name|Meaning (1=asserted)|
--------------------------------------------------
|0|CH_A_OK|Channel A healthy|
--------------------------------------------------
|1|CH_B_OK|Channel B healthy|
--------------------------------------------------
|2|CH_C_OK|Channel C healthy (triplex platforms only)|
--------------------------------------------------
|3|CCDL_OK|CCDL integrity nominal|
--------------------------------------------------
|4|INS_OK|INS input valid|
--------------------------------------------------
|5|ADS_OK|Air-data input valid|
--------------------------------------------------
|6|GPS_OK|GPS input valid|
--------------------------------------------------
|7|PWR_OK|Primary power nominal|
--------------------------------------------------
|8-11|MODE|Current mode enum|
--------------------------------------------------
|12-15|LAST_FAULT|Most recent fault code|
--------------------------------------------------
|| ||

Header: Test
|| Requirement No:FCC-052 || Requirement: Requirements FCC-013, FCC-014, and FCC-015 shall be verified by analysis of loop timing measurements collected over a 60-minute HIL session under nominal and full-payload cases, and by test case TP-FCC-013 on the iron-bird rig.
Verifies: FCC-013, FCC-014, FCC-015
References: DO-178C-6.4.4.2 ||

|| Requirement No:FCC-053 || Requirement: The CCDL disagreement detection of FCC-019 shall be verified by fault-injection test on the HIL rig with injected offsets of 5 %, 10 %, and 20 % of full-scale persisting 50 ms, 200 ms, and 1 s, demonstrating correct isolation of the minority channel within 50 ms of the 200 ms threshold.
Verifies: FCC-019
References: DO-178C-6.4.4.3 ||

|| Requirement No:FCC-054 || Requirement: Control-law stability margins shall be verified by analysis to demonstrate gain margin ≥ 6 dB and phase margin ≥ 45° on all axes at each breakpoint defined in FCC-020, across ±25 % mass-property perturbation and ±15 % aerodynamic-coefficient perturbation.
Verifies: FCC-020, FCC-024, FCC-025
References: ARP4754A-V&V ||

|| Requirement No:FCC-055 || Requirement: The 50 ms power-interruption ride-through requirement FCC-036 shall be verified by DO-160G §16 Category Z test (interruption durations 10, 25, 50, and 75 ms) on the flight-configuration hardware.
Verifies: FCC-036
References: DO-160G-16, MIL-STD-704F ||

|| Requirement No:FCC-056 || Requirement: The structural-mode notch filters of FCC-027 and FCC-039 shall be verified by frequency-response analysis against the platform ground-vibration test data and confirmed by in-flight flutter-clearance tests per ##STR.STR-025.
Verifies: FCC-027
References: DO-160G-8 ||

|| Requirement No:STR7-FCC-001 || Requirement: On Stratos-7, the FCC shall be implemented as a triplex-redundant architecture with three independent lanes, dissimilar compilation toolchains on at least two of the three lanes per ARP4754A development independence guidance, and lane-to-lane physical isolation in separate chassis with distinct power feeds per ##PWR.PWR-025.
Derives From: FCC-003
References: ARP4754A-4.2, DO-178C-6.3 ||

|| Requirement No:STR7-FCC-002 || Requirement: On Stratos-7, the FCC shall command trim via an electric pitch-trim actuator at 0 to 5 deg/s with absolute trim authority of -8° to +4°, and shall disable trim commands automatically if airspeed exceeds 320 kt CAS or Mach 0.72, whichever is lower.
References: DO-178C ||

|| Requirement No:STR7-FCC-003 || Requirement: On Stratos-7, the FCC shall coordinate with the FADEC (##ENG.ENG-020) to limit pitch-up manoeuvres such that commanded pitch rate is reduced to 70 % of nominal whenever N1 exceeds 95 % to prevent compressor stall.
Satisfies: ##ENG.ENG-030 ||

|| Requirement No:STR7-FCC-004 || Requirement: On Stratos-7, the FCC shall support autonomous carrier-free launch (roll-on-roll-off operation) and shall not require any external alignment input beyond INS_READY and GPS_FIX_3D during takeoff roll. ||

|| Requirement No:STR7-FCC-005 || Requirement: On Stratos-7, the FCC shall operate at altitudes up to 44 000 ft with controlled flight envelope margins of 10 kt below V_MO and 0.02 Mach below M_MO at all times. ||

|| Requirement No:STR7-FCC-006 || Requirement: On Stratos-7, the FCC shall respond to a flight-termination input (##EMS.EMS-030) by commanding full nose-down pitch (-25°) with throttle cut within 200 ms of the authenticated termination signal. ||

|| Requirement No:ALX2-FCC-001 || Requirement: On AeroLynx-X2, the FCC shall be implemented as a duplex-redundant architecture with two independent lanes in separate chassis, powered by the essential and secondary buses per ##PWR.PWR-012.
Derives From: FCC-003 ||

|| Requirement No:ALX2-FCC-002 || Requirement: On AeroLynx-X2, the FCC shall coordinate differential thrust between the two turboprops (##ENG.ENG-040) for yaw augmentation when indicated airspeed is below 90 kt and rudder authority is saturated, up to a maximum thrust differential of 15 % between engines. ||

|| Requirement No:ALX2-FCC-003 || Requirement: On AeroLynx-X2, the FCC shall detect single-engine-out within 500 ms of N1 falling below 40 % on either engine, command automatic rudder trim within 1 s to counter asymmetric thrust, and notify the operator per ##HMI.HMI-020. ||

|| Requirement No:ALX2-FCC-004 || Requirement: On AeroLynx-X2, the FCC shall limit bank angle to ±30° (instead of the nominal ±60° per FCC-038) when operating below 2 000 ft AGL with either engine in degraded mode. ||

|| Requirement No:SKT1-FCC-001 || Requirement: On Skyrunner-T1, the FCC shall be implemented as a duplex-redundant architecture at DO-178C DAL-B with two lanes in a single LRU and common power feed via the essential bus per ##PWR.PWR-020.
Derives From: FCC-003 ||

|| Requirement No:SKT1-FCC-002 || Requirement: On Skyrunner-T1, the FCC shall operate in a reduced envelope (ceiling 20 000 ft, airspeed 40 to 120 kt CAS) and shall inhibit CRUISE mode gain schedule points outside this envelope. ||

|| Requirement No:SKT1-FCC-003 || Requirement: On Skyrunner-T1, the FCC shall accept manual control inputs from the GCS operator joystick (##HMI.HMI-025) with a deadband of 2 % of full-scale and a rate limit of 60 deg/s on roll and 30 deg/s on pitch. ||

|| Requirement No:SKT1-FCC-004 || Requirement: On Skyrunner-T1, the FCC shall support field-expedient launch from a pneumatic catapult with peak acceleration tolerance of 8 g for 150 ms per DO-160G §7 Category D. ||

|| Requirement No:NBC3-FCC-001 || Requirement: On Nimbus-C3, the FCC shall account for payload centre-of-gravity variation from 20 % to 40 % MAC, recomputing gain schedules and trim offsets within 2 s of a loadmaster-declared CG change submitted via ##GCS.GCS-030.
References: SORA ||

|| Requirement No:NBC3-FCC-002 || Requirement: On Nimbus-C3, the FCC shall detect in-flight cargo shift (Δcg > 2 % MAC within 10 s) via comparison of trim-integrator output to predicted CG, and shall notify the operator within 500 ms per ##HMI.HMI-022. ||

|| Requirement No:NBC3-FCC-003 || Requirement: On Nimbus-C3, the FCC shall support external-payload pod jettison (##PLD.PLD-030) and shall apply a pre-configured transient attitude compensation (≤ 3° pitch, ≤ 2° roll for 2 s) within 100 ms of jettison command execution. ||

|| Requirement No:NBC3-FCC-004 || Requirement: On Nimbus-C3 civil operations, the FCC shall provide continuous conformance monitoring against the filed 4D trajectory (##FMS.FMS-020) with deviation alerts at ±200 ft vertical or ±0.5 nmi lateral, per SORA operational risk class OC-3.
References: EASA SORA 2.0 ||
