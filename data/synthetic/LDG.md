#Requirement: REQ-LDG
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: LDG
BASELINE: v1.5.0
ABSOLUTE PATH: /AeroSys/Common/LDG

Header: PURPOSE
|| Requirement No:LDG-001 || Requirement: This document specifies the Landing Gear and Braking requirements for the AeroSys Dynamics platforms: Stratos-7 (tricycle retractable), AeroLynx-X2 (tricycle retractable), Skyrunner-T1 (fixed tricycle or skid), Nimbus-C3 (tricycle retractable). LDG control software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:LDG-002 || Requirement: This module covers landing-gear extend/retract (retractable platforms), weight-on-wheels (WoW) sensing, anti-skid braking, nose-wheel steering (where fitted), and gear position monitoring. It excludes tire and wheel mechanical design (##STR.STR-035). ||

Header: REFERENCES
|| Requirement No:LDG-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, RTCA DO-160G, FAR Part 25 §25.729 (gear extension and retraction), SAE AS81714 (tire and wheel). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|LDG|Landing Gear|
--------------------------------------------------
|WoW|Weight-on-Wheels|
--------------------------------------------------
|NLG|Nose Landing Gear|
--------------------------------------------------
|MLG|Main Landing Gear|
--------------------------------------------------
|NWS|Nose Wheel Steering|
--------------------------------------------------
|ABS|Anti-skid Braking System|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:LDG-004 || Requirement: The LDG subsystem shall support the following operational modes:
    a) OFF
    b) GROUND (all struts compressed, WoW asserted)
    c) EXTENDED (airborne, gear down and locked)
    d) TRANSIT (retracting or extending)
    e) RETRACTED (airborne, gear up and locked)
    f) EMERGENCY_EXTEND (gravity extend used, STR7/ALX2/NBC3)
    g) FAULT ||

|| Requirement No:LDG-005 || Requirement: Transition from EXTENDED to TRANSIT (retract) shall be inhibited unless WoW = FALSE on all struts for > 3 s and radar altimeter (##RADAR.RADAR-005) reports AGL ≥ 50 ft. ||

|| Requirement No:LDG-006 || Requirement: Transition from RETRACTED to TRANSIT (extend) shall be inhibited if airspeed exceeds the gear-speed limit (V_LE) specified per platform in the LDG_Speed_Limits table (LDG-028). ||

|| Requirement No:LDG-007 || Requirement: On EMERGENCY_EXTEND command or on hydraulic power loss with airspeed < V_LE, the LDG subsystem shall release gear locks within 2 s and allow gravity + aerodynamic extension, confirming down-and-locked within 30 s. ||

Header: General
|| Requirement No:LDG-008 || Requirement: The LDG subsystem shall extend or retract the gear within 15 s (commanded) at airspeeds below V_LO (gear operating speed), with no single position being held in TRANSIT for more than 20 s.
References: FAR Part 25.729 ||

|| Requirement No:LDG-009 || Requirement: The LDG subsystem shall provide down-and-locked indication from each strut via dual-redundant proximity switches (or single switch on Skyrunner-T1), with agreement required within 200 ms for the DOWN_LOCKED state to be asserted. ||

|| Requirement No:LDG-010 || Requirement: The LDG subsystem shall provide up-and-locked indication from each strut via the same sensor pair; UP_LOCKED shall be asserted only with both proximity switches agreeing. ||

|| Requirement No:LDG-011 || Requirement: On retractable platforms, the LDG subsystem shall command gear doors to close after UP_LOCKED and open before initiating extension, with door position feedback dual-redundant. ||

|| Requirement No:LDG-012 || Requirement: The LDG subsystem shall detect asymmetric gear (one main gear extended and the other not, persisting > 5 s) and notify the operator per ##HMI.HMI-140 with CONFIGURATION_SUSPECT flag. ||

|| Requirement No:LDG-013 || Requirement: The LDG anti-skid braking system shall prevent wheel lockup by modulating brake pressure in response to wheel-speed comparison with reference ground speed, maintaining longitudinal deceleration up to the tire-runway adhesion limit. ||

|| Requirement No:LDG-014 || Requirement: The ABS shall maintain braking authority across runway surface conditions from dry (μ ~0.7) to wet-contaminated (μ ~0.15) while preventing wheel lockup on all wheels. ||

|| Requirement No:LDG-015 || Requirement: The LDG subsystem shall publish WoW discretes for each strut (NLG, MLG-left, MLG-right) with dual-redundant sensors per strut on DAL-A platforms, with 2-out-of-3 voting where feasible per ##FCC.FCC-048.
Satisfies: ##FCC.FCC-048 ||

|| Requirement No:LDG-016 || Requirement: The LDG WoW signals shall be latched with debounce period 100 ms to prevent chattering during touchdown and rollout. ||

|| Requirement No:LDG-017 || Requirement: On Stratos-7, AeroLynx-X2, and Nimbus-C3, the LDG subsystem shall provide nose-wheel steering with authority ±70° (max taxi) and ±7° (max high-speed, rudder-coupled during takeoff/landing roll). ||

|| Requirement No:LDG-018 || Requirement: The NWS authority shall be reduced to ±7° whenever groundspeed exceeds 30 kt, with seamless blending between low- and high-authority modes within 200 ms. ||

|| Requirement No:LDG-019 || Requirement: The LDG subsystem shall provide tire-pressure monitoring (on Stratos-7 and Nimbus-C3) with per-wheel pressure reported to the operator; low-pressure alert triggered at 85 % of nominal. ||

|| Requirement No:LDG-020 || Requirement: The LDG subsystem shall provide a groundcrew-inhibit discrete: when asserted (by maintenance pin or cockpit switch while on-ground), the FCC maintenance Ethernet per ##FCC.FCC-044 and other ground-only functions are unlocked.
Satisfies: ##FCC.FCC-044 ||

|| Requirement No:LDG-021 || Requirement: The LDG subsystem shall detect hydraulic-pressure loss (below 2 000 psig sustained > 2 s on gear actuation system) and transition to FAULT, notifying the operator per ##HMI.HMI-142. ||

|| Requirement No:LDG-022 || Requirement: The LDG subsystem shall survive a hard landing (vertical touchdown rate up to platform design limit per ##STR.STR-040) without permanent deformation of strut, actuator, or mount structure. ||

|| Requirement No:LDG-023 || Requirement: The LDG subsystem shall operate across DO-160G §4 Category A2 environmental envelope with additional qualification for fluid susceptibility per DO-160G §11.
References: DO-160G-11 ||

|| Requirement No:LDG-024 || Requirement: The LDG subsystem shall publish LDG_STATUS_MSG at 10 Hz with per-strut WoW, up/down-lock states, door states, NWS position, per-wheel brake pressure, tire pressure (where fitted), and fault-word. ||

Header: Interface
|| Requirement No:LDG-025 || Requirement: The LDG subsystem shall receive gear-extend/retract and NWS commands from the FCC (##FCC.FCC-031) via the primary avionics bus at up to 10 Hz; brake commands shall be dispatched at up to 100 Hz for anti-skid modulation.
Satisfies: ##FCC.FCC-031 ||

|| Requirement No:LDG-026 || Requirement: The LDG subsystem shall report to ##FDR.FDR-035 all touchdown events with time, vertical rate, longitudinal and lateral g, and runway (when ##FMS.FMS-026 provides runway context). ||

|| Requirement No:LDG-027 || Requirement: The LDG subsystem shall format LDG_STATUS_MSG per the following table.
Table Type: MESSAGE
Table Name or Description: LDG_Status_Msg
Table: LDG_Status_Msg
|Field|Type|Range|
--------------------------------------------------
|mode|uint8|enum|
--------------------------------------------------
|wow_nlg,wow_mlg_l,wow_mlg_r|uint8 ×3|0 or 1|
--------------------------------------------------
|down_locked (per strut)|uint8 ×3|0 or 1|
--------------------------------------------------
|up_locked (per strut)|uint8 ×3|0 or 1|
--------------------------------------------------
|door_open_closed|uint8 ×N|per doors|
--------------------------------------------------
|nws_pos|float32|-70 to +70 deg|
--------------------------------------------------
|brake_press (per wheel)|float32 ×N|0-3000 psig|
--------------------------------------------------
|tire_press (per wheel, optional)|float32 ×N|0-250 psig|
--------------------------------------------------
|fault_word|uint32|bitmask|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:LDG-028 || Requirement: The LDG subsystem shall enforce the LDG_Speed_Limits per the following table; commanded operations outside these limits shall be rejected.
Table Type: MESSAGE
Table Name or Description: LDG_Speed_Limits
Table: LDG_Speed_Limits
|Platform|V_LO (operate)|V_LE (extended)|V_LE Max Roll Brake|
--------------------------------------------------
|Stratos-7|180 kt|220 kt|80 kt max braking|
--------------------------------------------------
|AeroLynx-X2|150 kt|180 kt|70 kt|
--------------------------------------------------
|Skyrunner-T1|fixed gear|n/a|50 kt|
--------------------------------------------------
|Nimbus-C3|160 kt|200 kt|75 kt|
-------------------------------------------------- ||

|| Requirement No:LDG-029 || Requirement: The LDG anti-skid braking system shall apply control parameters per the ABS_Control table.
Table Type: MESSAGE
Table Name or Description: ABS_Control
Table: ABS_Control
|Parameter|Value|Notes|
--------------------------------------------------
|Wheel-speed sample rate|500 Hz|per wheel|
--------------------------------------------------
|Modulation frequency|up to 20 Hz|brake pressure|
--------------------------------------------------
|Slip-ratio target|10-20 %|optimal μ|
--------------------------------------------------
|Lockup detection|wheel < 15 % ref for 100 ms|releases brake|
--------------------------------------------------
|Re-apply rate|≤ 200 ms|stabilise before re-apply|
-------------------------------------------------- ||

Header: Test
|| Requirement No:LDG-030 || Requirement: Gear extension/retraction cycle time (LDG-008) shall be verified by iron-bird cycle tests at simulated airspeeds 50, 100, 150 kt with no external load, demonstrating cycle time ≤ 15 s and no position held > 20 s in TRANSIT.
Verifies: LDG-008
References: FAR Part 25.729 ||

|| Requirement No:LDG-031 || Requirement: WoW dual-sensor agreement (LDG-015) shall be verified by fault injection (single-sensor disagreement) and 2-out-of-3 voting confirmation on DAL-A platforms, demonstrating correct WoW output despite single-sensor fault.
Verifies: LDG-015 ||

|| Requirement No:LDG-032 || Requirement: Anti-skid performance (LDG-014) shall be verified by ground-rolling test on dry and wet-contaminated runway surfaces at maximum brake energy, demonstrating no wheel lockup and stopping distance within platform landing-distance envelope.
Verifies: LDG-014 ||

|| Requirement No:STR7-LDG-001 || Requirement: On Stratos-7, the LDG shall support max-brake-energy landings of ~1.2 MJ per wheel, with carbon-carbon brakes and forced-air cooling per ##TCS.TCS-018.
Satisfies: ##TCS.TCS-018 ||

|| Requirement No:SKT1-LDG-001 || Requirement: On Skyrunner-T1, the LDG shall be a fixed tricycle configuration with no retraction mechanism; gear position is permanently EXTENDED and all retract/EMERGENCY_EXTEND logic is not applicable.
Refines: LDG-004 ||

|| Requirement No:NBC3-LDG-001 || Requirement: On Nimbus-C3, the LDG shall support MTOW-limited landings up to 4 500 kg with main-gear strut stroke 350 mm and sink-rate tolerance up to 12 ft/s per SORA operational class OC-3.
References: EASA SORA 2.0 ||
