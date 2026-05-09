#Requirement: REQ-ENG
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: ENG
BASELINE: v2.0.0
ABSOLUTE PATH: /AeroSys/Common/ENG

Header: PURPOSE
|| Requirement No:ENG-001 || Requirement: This document specifies the Engine Control interface requirements for the AeroSys Dynamics platforms, addressing the aircraft-side interface with the engine-supplied FADEC (turbofan, turboprop) or ECU (piston). Platforms: Stratos-7 (single turbofan), AeroLynx-X2 (twin turboprop), Skyrunner-T1 (single piston), Nimbus-C3 (single turboprop). The aircraft-side engine interface software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2 and DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:ENG-002 || Requirement: This module covers the aircraft-side thrust/torque command generation, FADEC/ECU interface protocol, engine-parameter monitoring (N1, N2, EGT, ITT, Np, torque, oil pressure, oil temperature, fuel flow), start/shutdown sequencing from the FCC, protection-logic coordination, and engine-health reporting. It excludes FADEC/ECU internal control laws (supplier-provided) and mechanical engine design. ||

Header: REFERENCES
|| Requirement No:ENG-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, ARINC 429 (for propulsion), MIL-STD-1553B (military variants), SAE AS6171 (counterfeit electronic parts), engine-supplier ICDs (e.g. Honeywell, Safran, Rolls-Royce, GE, Pratt & Whitney, Rotax per platform).
References: ARP4754A ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|FADEC|Full Authority Digital Engine Control (turbine)|
--------------------------------------------------
|ECU|Engine Control Unit (piston)|
--------------------------------------------------
|N1|Low-pressure spool speed (turbofan) / gas generator speed (turboprop)|
--------------------------------------------------
|N2|High-pressure spool speed|
--------------------------------------------------
|Np|Propeller speed|
--------------------------------------------------
|EGT|Exhaust Gas Temperature|
--------------------------------------------------
|ITT|Interstage Turbine Temperature|
--------------------------------------------------
|PLA|Power Lever Angle|
--------------------------------------------------
|TQ|Torque|
--------------------------------------------------
|FF|Fuel Flow|
--------------------------------------------------
|SFC|Specific Fuel Consumption|
--------------------------------------------------
|OAT|Outside Air Temperature|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:ENG-004 || Requirement: The engine interface shall support the following modes:
    a) OFF
    b) START (cranking and light-off)
    c) IDLE
    d) NORMAL (flight operation)
    e) MAX_CONT (maximum continuous)
    f) TAKEOFF (time-limited max thrust/power)
    g) EMERGENCY_POWER (above normal limits, time-limited)
    h) SHUTDOWN
    i) FAULT
Mode transitions shall be governed by the FCC in conjunction with FADEC/ECU protection logic. ||

|| Requirement No:ENG-005 || Requirement: While in START mode, the FCC shall not command thrust or torque beyond the start-idle schedule supplied by the FADEC/ECU, and shall monitor EGT/ITT for hung-start or hot-start conditions per the start envelope of the supplier ICD. ||

|| Requirement No:ENG-006 || Requirement: Transition from START to IDLE shall be declared when N1 ≥ 55 % (turbofan), N1 ≥ 65 % gas generator (turboprop), or engine RPM ≥ 1 800 rpm (piston), sustained for 30 s within supplier EGT/ITT bounds. ||

|| Requirement No:ENG-007 || Requirement: The FCC shall command MAX_CONT thrust/power for durations up to 5 min and TAKEOFF power for durations up to 2 min per the engine supplier's operating limitations, tracking elapsed time and notifying the operator at 75 % of the limit. ||

|| Requirement No:ENG-008 || Requirement: EMERGENCY_POWER (typically 2 min authorization) shall be authorised only by a specific operator command acknowledged per ##HMI.HMI-120, with automatic timer and post-event engine-inspection maintenance flag.
Satisfies: ##HMI.HMI-120 ||

|| Requirement No:ENG-009 || Requirement: The FCC shall command SHUTDOWN whenever WoW is asserted for > 5 s with groundspeed < 2 kt and operator shutdown command received, or whenever an engine-protection trip condition per the ENG_Protection_Limits (ENG-040) is asserted.
Derives From: ARP4761-FHA-ENG-01 ||

Header: General
|| Requirement No:ENG-010 || Requirement: The FCC shall compute commanded thrust/torque at 50 Hz and transmit it to the FADEC/ECU with transport latency ≤ 20 ms.
References: DO-178C-6.3.4 ||

|| Requirement No:ENG-011 || Requirement: The FCC shall bound commanded thrust/torque such that at no time does the command exceed the supplier's N1/N2/EGT/ITT/TQ redlines by any margin; any such excess commanded value shall be clamped at the FCC before transmission to FADEC. ||

|| Requirement No:ENG-012 || Requirement: The FCC shall monitor N1, N2, EGT (or ITT), oil pressure, oil temperature, torque, and fuel flow at a minimum 20 Hz rate, comparing each parameter against the ENG_Protection_Limits table (ENG-040). ||

|| Requirement No:ENG-013 || Requirement: On any protection-limit exceedance persisting beyond the action time specified in ENG-040, the FCC shall command the appropriate action (warn, retard, shutdown) and log the event to ##FDR.FDR-032.
Satisfies: ##FDR.FDR-032 ||

|| Requirement No:ENG-014 || Requirement: The FCC shall apply engine-interface fuel-flow schedule consistent with the ##FUEL.FUEL-010 fuel-management function, ensuring commanded thrust does not exceed what current fuel availability supports. ||

|| Requirement No:ENG-015 || Requirement: The FCC shall compute and publish thrust-authority-margin (percentage of remaining thrust command authority) at 20 Hz for operator display per ##HMI.HMI-122. ||

|| Requirement No:ENG-016 || Requirement: The FCC shall command flight-idle (configured per platform) whenever the aircraft is in APPROACH mode and descending below 1 000 ft AGL, to provide quick response to go-around command. ||

|| Requirement No:ENG-017 || Requirement: The FCC shall coordinate thrust-to-surface-command compatibility per ##STR7-FCC-003 on Stratos-7 (reduce pitch rate when N1 > 95 %) and per ##ALX2-FCC-002 on AeroLynx-X2 (differential thrust for yaw augmentation).
Satisfies: ##STR7-FCC-003, ##ALX2-FCC-002 ||

|| Requirement No:ENG-018 || Requirement: The FCC shall detect single-engine-out on AeroLynx-X2 (N1 < 40 % on either engine, or torque < 20 % rated torque, for > 500 ms) and trigger the asymmetric-thrust compensation per ##ALX2-FCC-003.
Satisfies: ##ALX2-FCC-003 ||

|| Requirement No:ENG-019 || Requirement: The FCC shall monitor engine-vibration levels from the FADEC/ECU (when supplied) and degrade commanded power by 5 % and notify the operator when vibration exceeds 75 % of the supplier limit. ||

|| Requirement No:ENG-020 || Requirement: The FCC shall publish ENG_STATUS_MSG at 20 Hz with all engine parameters to the NAV, FMS, GCS, and FDR, per the ENG_Status_Msg table (ENG-038).
Satisfies: ##FMS.FMS-017 ||

|| Requirement No:ENG-021 || Requirement: The FCC shall accept throttle position input from the GCS (##CDL.CDL-030) at up to 20 Hz and translate it to commanded thrust/torque, with rate-limiting per ##FCC.FCC-038 throttle max rate (20 %/s).
Satisfies: ##CDL.CDL-030 ||

|| Requirement No:ENG-022 || Requirement: The FCC shall coordinate with the Autopilot (##AUTO.AUTO-025) for autothrottle operation, with Autopilot-commanded thrust superseding GCS-operator throttle when autothrottle is engaged. ||

|| Requirement No:ENG-023 || Requirement: The FCC shall support engine-start sequencing on operator command while WoW is asserted, monitoring starter duty cycle and issuing START_ABORT if starter-on time exceeds supplier limit (typically 60 s on, 5 min off between attempts). ||

|| Requirement No:ENG-024 || Requirement: The FCC shall support in-flight restart attempts within the supplier's relight envelope (typically airspeed 150 to 250 kt, altitude below 25 000 ft for turbofan; airspeed 80 to 160 kt for turboprop; windmilling N1 threshold). ||

|| Requirement No:ENG-025 || Requirement: The FCC shall compute and publish SFC and total fuel consumption for mission tracking and fuel-prediction per ##FMS.FMS-017 and ##FUEL.FUEL-015.
Satisfies: ##FMS.FMS-017 ||

|| Requirement No:ENG-026 || Requirement: The FCC shall detect engine surge or compressor stall (by monitoring N1/N2 rapid drop and EGT/ITT rapid rise signals from the FADEC) and reduce commanded thrust by 20 % for 10 s to allow recovery, escalating to shutdown if recovery fails. ||

|| Requirement No:ENG-027 || Requirement: The FCC shall monitor engine-propeller synchronisation on twin-engine AeroLynx-X2, maintaining Np match within ±10 rpm between engines during cruise to reduce cabin noise and vibration. ||

|| Requirement No:ENG-028 || Requirement: The FCC shall support propeller feathering (twin-engine platforms) on engine-out per ##ALX2-FCC-003 and for single-engine propeller platforms upon severe engine failure to reduce drag. ||

|| Requirement No:ENG-029 || Requirement: The FCC shall operate across DO-160G §4 Category A2 environmental envelope and shall coordinate with TCS (##TCS.TCS-015) to ensure engine-bay thermal management supports continuous operation.
Satisfies: ##TCS.TCS-015 ||

|| Requirement No:ENG-030 || Requirement: The FCC shall apply N1 reserve limit: during TAKEOFF power and EMERGENCY_POWER, commanded N1 shall not exceed 98 % of the supplier-specified maximum to preserve surge margin under transient disturbances.
Satisfies: ##STR7-FCC-003 ||

Header: Interface
|| Requirement No:ENG-031 || Requirement: On Stratos-7 and AeroLynx-X2, the FCC shall interface with the FADEC via MIL-STD-1553B Bus A with FADEC as Remote Terminal 8 (Stratos-7) or RT 8/9 (AeroLynx-X2 port/starboard), at 20 Hz command and 50 Hz monitor rate.
References: MIL-STD-1553B ||

|| Requirement No:ENG-032 || Requirement: On Skyrunner-T1, the FCC shall interface with the ECU via CAN bus at 500 kbps with periodic 20 Hz status frames and on-demand command frames. ||

|| Requirement No:ENG-033 || Requirement: On Nimbus-C3, the FCC shall interface with the FADEC via ARINC 429 high-speed (100 kbps) with labels 150 (N1), 151 (N2), 152 (EGT), 153 (TQ), 154 (FF), 155 (oil P), 156 (oil T), 157 (Np) at 20 Hz.
References: ARINC 429 ||

|| Requirement No:ENG-034 || Requirement: The FCC shall transmit ENG_COMMAND_MSG containing cmd_thrust or cmd_torque, PLA equivalent, mode, and authorisation flags to the FADEC/ECU at 20 Hz. ||

|| Requirement No:ENG-035 || Requirement: The FCC shall consume ENG_STATUS from the FADEC/ECU at 20 Hz, including N1/N2/Np/EGT/ITT/TQ/oil P/oil T/FF/vibration/PLA-echo/mode. ||

|| Requirement No:ENG-036 || Requirement: The FCC shall detect loss of FADEC/ECU message (3 consecutive missed cycles, > 150 ms gap) within 200 ms, command a safe fail-fixed thrust setting (platform-specific, typically flight-idle), and notify the operator per ##HMI.HMI-125. ||

|| Requirement No:ENG-037 || Requirement: The FCC shall verify the FADEC/ECU software CRC or part number reported in every status frame against the expected value for the loaded configuration, flagging CONFIG_MISMATCH if they differ.
Satisfies: ##SEC.SEC-035 ||

|| Requirement No:ENG-038 || Requirement: The FCC shall format ENG_STATUS_MSG per the following table.
Table Type: MESSAGE
Table Name or Description: ENG_Status_Msg
Table: ENG_Status_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|engine_id|uint8|1 or 2 (ALX2 port/starboard); 1 otherwise|integer|
--------------------------------------------------
|n1|float32|0-110 %|0.1 %|
--------------------------------------------------
|n2|float32|0-110 % (turbofan only)|0.1 %|
--------------------------------------------------
|np|float32|0-110 % (turboprop only)|0.1 %|
--------------------------------------------------
|egt_itt|float32|0-1000 °C|1 °C|
--------------------------------------------------
|torque|float32|0-120 % rated|0.1 %|
--------------------------------------------------
|oil_press|float32|0-200 psig|0.1 psig|
--------------------------------------------------
|oil_temp|float32|-40 to +200 °C|0.1 °C|
--------------------------------------------------
|fuel_flow|float32|0-2000 pph|0.1 pph|
--------------------------------------------------
|vibration|float32|0-10 g RMS|0.01 g|
--------------------------------------------------
|pla_echo|float32|0-120 deg (piston) or 0-100 %|0.1|
--------------------------------------------------
|mode|uint8|enum|integer|
--------------------------------------------------
|fault_word|uint32|bitmask|bit|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:ENG-039 || Requirement: The FCC shall enforce the Redline_Limits table and immediately reduce commanded thrust or shut down the engine on redline exceedance per the specified action.
Table Type: MESSAGE
Table Name or Description: Redline_Limits
Table: Redline_Limits
|Parameter|Warning|Redline|Action if > Redline|Action Time|
--------------------------------------------------
|N1|98 % (STR7/NBC3)|103 %|reduce thrust|≤ 200 ms|
--------------------------------------------------
|N2|100 %|105 %|reduce thrust|≤ 200 ms|
--------------------------------------------------
|Np (turboprop)|101 %|105 %|reduce torque|≤ 200 ms|
--------------------------------------------------
|EGT TOGA|peak 920 °C|950 °C|reduce thrust|≤ 500 ms|
--------------------------------------------------
|ITT cruise|800 °C|850 °C|reduce thrust|≤ 500 ms|
--------------------------------------------------
|Torque|110 % rated|120 % rated|reduce torque|≤ 200 ms|
--------------------------------------------------
|Oil pressure (low)|25 psig|15 psig|shutdown|≤ 5 s|
--------------------------------------------------
|Oil temperature|135 °C|150 °C|reduce power|≤ 5 s|
--------------------------------------------------
|Vibration|6 g RMS|8 g RMS|reduce power|≤ 1 s|
-------------------------------------------------- ||

|| Requirement No:ENG-040 || Requirement: The FCC shall enforce the ENG_Protection_Limits table mapping conditions to escalated actions.
Table Type: MESSAGE
Table Name or Description: ENG_Protection_Limits
Table: ENG_Protection_Limits
|Condition|Duration|Action|Escalation|
--------------------------------------------------
|EGT > warn|30 s|notify|redline if persists|
--------------------------------------------------
|N1 > warn|30 s|notify|redline if persists|
--------------------------------------------------
|Oil press < warn|10 s|notify|redline if persists|
--------------------------------------------------
|Vibration > warn|5 s|reduce 5 %|redline if persists|
--------------------------------------------------
|Surge/stall detected|200 ms|reduce 20 %|shutdown if repeated|
--------------------------------------------------
|Loss of FADEC comm|150 ms|fail-fixed thrust|operator notification|
-------------------------------------------------- ||

Header: Test
|| Requirement No:ENG-041 || Requirement: Command latency (ENG-010) shall be verified by end-to-end time-stamp measurement from FCC thrust-command output to FADEC command-receipt on the iron-bird, 5 000 samples, demonstrating ≤ 20 ms at 99.9 % confidence.
Verifies: ENG-010 ||

|| Requirement No:ENG-042 || Requirement: Redline enforcement (ENG-039) shall be verified by injecting FADEC-simulated parameter exceedances and confirming the FCC issues the specified action within the ENG-039 Action Time.
Verifies: ENG-039 ||

|| Requirement No:ENG-043 || Requirement: Loss-of-FADEC detection (ENG-036) shall be verified by suspending FADEC status traffic on the iron-bird, confirming fail-fixed thrust within 200 ms and operator notification within 500 ms.
Verifies: ENG-036 ||

|| Requirement No:ENG-044 || Requirement: Single-engine-out detection on AeroLynx-X2 (ENG-018) shall be verified by HIL injection of N1 drop on one engine, demonstrating detection within 500 ms and asymmetric-thrust compensation commencement per ##ALX2-FCC-003.
Verifies: ENG-018 ||

|| Requirement No:ENG-045 || Requirement: Surge/stall recovery (ENG-026) shall be verified by injecting a simulated surge event (rapid N1 drop + EGT rise) on the iron-bird, confirming 20 % thrust reduction, 10 s recovery window, and correct escalation if recovery fails.
Verifies: ENG-026 ||
