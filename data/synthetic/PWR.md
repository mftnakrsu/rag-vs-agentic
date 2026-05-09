#Requirement: REQ-PWR
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: PWR
BASELINE: v1.8.0
ABSOLUTE PATH: /AeroSys/Common/PWR

Header: PURPOSE
|| Requirement No:PWR-001 || Requirement: This document specifies the Primary Electrical Power requirements for the AeroSys Dynamics common power distribution system, applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3. The PWR control software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2 and DAL-B on Skyrunner-T1 and Nimbus-C3; PWR control hardware at DO-254 Level A or Level B per the same platform mapping. ||

Header: SCOPE
|| Requirement No:PWR-002 || Requirement: This module covers primary generator control, bus distribution, load-shedding, hold-up energy delivery, and fault protection for the 28 V DC primary electrical system per MIL-STD-704F. It excludes batteries and APU (##APM.APM-001), emergency bus switching (##EPS.EPS-001), and the engine-driven generator mechanical interface (##ENG.ENG-055). ||

Header: REFERENCES
|| Requirement No:PWR-003 || Requirement: The governing references are: MIL-STD-704F (Aircraft Electric Power Characteristics), MIL-HDBK-704 series (test methods), RTCA DO-160G, RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, AS50881 (Wiring Aerospace Vehicle).
References: MIL-STD-704F ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|GCU|Generator Control Unit|
--------------------------------------------------
|BPCU|Bus Power Control Unit|
--------------------------------------------------
|TRU|Transformer Rectifier Unit|
--------------------------------------------------
|DCU|DC Contactor Unit|
--------------------------------------------------
|ELCU|Electronic Load Control Unit|
--------------------------------------------------
|SSPC|Solid State Power Controller|
--------------------------------------------------
|ESS|Essential|
--------------------------------------------------
|EMRG|Emergency|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:PWR-004 || Requirement: The PWR subsystem shall support the following operational modes:
    a) OFF
    b) GROUND (external power applied, generators offline)
    c) NORMAL (generators online, all buses energised)
    d) SINGLE_GEN (one generator faulted, remaining generator + battery picks up load)
    e) EMERGENCY (all generators offline, essential + emergency buses on battery)
    f) FAULT
Mode transitions shall be automatic based on source-availability state per PWR-033. ||

|| Requirement No:PWR-005 || Requirement: In NORMAL mode, the PWR subsystem shall supply primary 28 V DC to all buses within the MIL-STD-704F steady-state limits (22 V to 29 V DC).
References: MIL-STD-704F ||

|| Requirement No:PWR-006 || Requirement: Upon generator loss in NORMAL, the PWR subsystem shall transition to SINGLE_GEN within 50 ms, maintaining all flight-critical buses energised, and shall shed non-essential loads per the Load_Shed_Priority table (PWR-032). ||

|| Requirement No:PWR-007 || Requirement: Upon loss of all generators, the PWR subsystem shall transition to EMERGENCY within 50 ms, isolate non-essential and secondary buses, and draw from the battery (##APM.APM-010) to sustain essential and emergency buses.
Satisfies: ##APM.APM-010 ||

Header: General
|| Requirement No:PWR-008 || Requirement: The PWR subsystem shall supply nominal 28 V DC per MIL-STD-704F at all essential buses, with steady-state voltage 22 V to 29 V DC, transient limit to 50 V for ≤ 50 ms, and under-voltage limit 18 V (for ≤ 50 ms) before protection-trip.
Satisfies: ##FCC.FCC-045
References: MIL-STD-704F ||

|| Requirement No:PWR-009 || Requirement: The PWR subsystem shall deliver ripple not exceeding 1.5 V peak-to-peak on any essential bus under any load condition permitted by the platform's load analysis.
References: MIL-STD-704F ||

|| Requirement No:PWR-010 || Requirement: The PWR subsystem shall detect short-circuit faults (current > 150 % nominal for > 100 ms, or > 300 % nominal for > 10 ms) on any bus and isolate the faulted bus segment within 50 ms via SSPC or contactor trip. ||

|| Requirement No:PWR-011 || Requirement: The PWR subsystem shall detect over-voltage faults (> 32 V DC for > 100 ms) on any generator output, trip the offending GCU, and route load to the remaining generators and battery. ||

|| Requirement No:PWR-012 || Requirement: The PWR subsystem shall provide independent power feeds for redundant LRUs (FCC lanes per ##FCC.FCC-003, INS LRUs per ##INS.INS-003, ADS LRUs per ##ADS.ADS-003) routed through physically separated wiring bundles per AS50881.
Satisfies: ##FCC.FCC-003, ##INS.INS-003
References: AS50881 ||

|| Requirement No:PWR-013 || Requirement: The PWR subsystem shall provide hold-up capacitor energy at each essential-bus downstream LRU equivalent to sustaining the LRU's nameplate power for 50 ms during a primary-power interruption per ##FCC.FCC-036.
Satisfies: ##FCC.FCC-036 ||

|| Requirement No:PWR-014 || Requirement: The PWR subsystem shall limit turn-on inrush current at any LRU feed to ≤ 150 % of the LRU's steady-state rated current, using inrush-limiters in SSPC devices. ||

|| Requirement No:PWR-015 || Requirement: The PWR subsystem shall publish real-time power-status telemetry at 10 Hz including per-bus voltage, per-feeder current, generator status, GCU health, and mode, routed to the GCS per ##GCS.GCS-060 and to the FDR per ##FDR.FDR-028.
Satisfies: ##GCS.GCS-060 ||

|| Requirement No:PWR-016 || Requirement: The PWR subsystem shall support ground-external-power (GPU) connection via a dedicated receptacle, with automatic changeover to/from generator power on landing/takeoff, inhibiting any GPU load dumping transient > 5 V on essential buses. ||

|| Requirement No:PWR-017 || Requirement: The PWR subsystem shall support load analysis with total continuous essential-bus rated load ≤ 2.5 kW (STR7), 1.5 kW (ALX2), 0.4 kW (SKT1), 1.8 kW (NBC3), matched to the generator rating of ##ENG.ENG-055. ||

|| Requirement No:PWR-018 || Requirement: The PWR subsystem shall deliver hold-up energy at the essential-bus ≥ 50 J continuously available per MIL-STD-704F Category Z 50 ms interruption, for the FCC (##FCC.FCC-036), INS (##INS.INS-035), NAV (##NAV.NAV-026), CDL (##CDL.CDL-025), and GPS (##GPS.GPS-026).
Satisfies: ##FCC.FCC-036, ##INS.INS-035, ##NAV.NAV-026, ##CDL.CDL-025, ##GPS.GPS-026 ||

|| Requirement No:PWR-019 || Requirement: The PWR subsystem shall detect generator under-frequency or under-voltage abnormality (beyond GCU regulation) and trip the affected generator within 200 ms to prevent cascade failure. ||

|| Requirement No:PWR-020 || Requirement: The PWR subsystem shall provide the Skyrunner-T1 single-lane FCC with an essential-bus feed per ##SKT1-FCC-001 routed through a single SSPC with overload protection at 1.2× nominal sustained for > 5 s.
Satisfies: ##SKT1-FCC-001 ||

|| Requirement No:PWR-021 || Requirement: The PWR subsystem shall isolate any feed found faulted within the fault-isolation test of §BIT.BIT-015, by opening the corresponding SSPC and latching-out with operator-only reset. ||

|| Requirement No:PWR-022 || Requirement: The PWR subsystem shall survive without damage and shall resume nominal operation within 2 s after a 100 ms lightning-induced transient per DO-160G §22 Category A3. ||

|| Requirement No:PWR-023 || Requirement: The PWR subsystem shall operate across DO-160G §4 Category A2 (operating temperature -40 °C to +70 °C) and DO-160G §8 Category U vibration envelope.
References: DO-160G-4, DO-160G-8 ||

|| Requirement No:PWR-024 || Requirement: The PWR subsystem shall detect GCU internal fault via GCU self-test at 10 Hz, isolating the GCU on 3 consecutive failures and transferring generator-control to the redundant GCU where installed. ||

|| Requirement No:PWR-025 || Requirement: On Stratos-7, the PWR subsystem shall provide three independent essential-bus feeds to the triplex FCC (##STR7-FCC-001) with generator-to-FCC lane mapping such that no single generator failure disables more than one FCC lane.
Satisfies: ##STR7-FCC-001 ||

Header: Interface
|| Requirement No:PWR-026 || Requirement: The PWR subsystem shall publish PWR_STATUS_MSG at 10 Hz via MIL-STD-1553B (STR7/ALX2) or ARINC 429 (SKT1/NBC3), with format per the PWR_Status_Msg table (PWR-030).
References: MIL-STD-1553B, ARINC 429 ||

|| Requirement No:PWR-027 || Requirement: The PWR subsystem shall accept BPCU commands from the BIT function (##BIT.BIT-020) for non-destructive fault-injection test during ground maintenance, authenticated via ##SEC.SEC-015. ||

|| Requirement No:PWR-028 || Requirement: The PWR subsystem shall monitor battery state-of-charge from ##APM.APM-015 at 1 Hz and shall refuse entry to NORMAL mode if battery SoC < 85 % during ground operations.
Satisfies: ##APM.APM-015 ||

|| Requirement No:PWR-029 || Requirement: The PWR subsystem shall command the APU start (where fitted) via ##APM.APM-020 when SoC or backup-power criteria dictate, receiving APU-ready acknowledgement before transferring load. ||

|| Requirement No:PWR-030 || Requirement: The PWR subsystem shall format PWR_STATUS_MSG per the table below.
Table Type: MESSAGE
Table Name or Description: PWR_Status_Msg
Table: PWR_Status_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|mode|uint8|enum {OFF,GROUND,NORMAL,SINGLE_GEN,EMERGENCY,FAULT}|integer|
--------------------------------------------------
|gen1_voltage,gen2_voltage|float32 ×2|0 to 35 V|0.01 V|
--------------------------------------------------
|ess_bus_v,sec_bus_v,emrg_bus_v|float32 ×3|0 to 35 V|0.01 V|
--------------------------------------------------
|ess_bus_i,sec_bus_i|float32 ×2|0 to 300 A|0.1 A|
--------------------------------------------------
|battery_soc|uint8|0 to 100 %|1 %|
--------------------------------------------------
|shed_level|uint8|0 to 4|integer|
--------------------------------------------------
|fault_word|uint32|bitmask per PWR-031|bit|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:PWR-031 || Requirement: The PWR subsystem shall encode fault conditions per the PWR_Fault_Word table.
Table Type: MESSAGE
Table Name or Description: PWR_Fault_Word
Table: PWR_Fault_Word
|Bit|Name|Meaning (1=fault)|
--------------------------------------------------
|0|GEN1_FAIL|Generator 1 offline or out-of-spec|
--------------------------------------------------
|1|GEN2_FAIL|Generator 2 offline or out-of-spec|
--------------------------------------------------
|2|ESS_BUS_FAIL|Essential bus under-voltage|
--------------------------------------------------
|3|SEC_BUS_FAIL|Secondary bus under-voltage|
--------------------------------------------------
|4|EMRG_BUS_FAIL|Emergency bus under-voltage|
--------------------------------------------------
|5|OVER_VOLTAGE|Any bus > 32 V|
--------------------------------------------------
|6|SHORT_CIRCUIT|SSPC tripped on over-current|
--------------------------------------------------
|7|GCU1_FAIL|GCU1 internal fault|
--------------------------------------------------
|8|GCU2_FAIL|GCU2 internal fault|
--------------------------------------------------
|9|BATTERY_LOW|Battery SoC < 30 %|
--------------------------------------------------
|10|GPU_CONNECTED|External ground power applied|
--------------------------------------------------
|11-31|reserved|0|
-------------------------------------------------- ||

|| Requirement No:PWR-032 || Requirement: The PWR subsystem shall apply the Load_Shed_Priority table on entering SINGLE_GEN or EMERGENCY mode.
Table Type: MESSAGE
Table Name or Description: Load_Shed_Priority
Table: Load_Shed_Priority
|Priority|Loads|Shed Level|
--------------------------------------------------
|P1 (keep)|FCC, INS, CDL, NAV, GPS, ADS|never shed|
--------------------------------------------------
|P2 (keep)|AUTO, FMS, EMS, BIT, FDR, RADAR altimeter|shed only in FAULT|
--------------------------------------------------
|P3 (shed lvl 1)|Weather radar, UHF, HF, Inmarsat|shed on SINGLE_GEN|
--------------------------------------------------
|P4 (shed lvl 2)|Payload (EOIR, SAR)|shed on EMERGENCY|
--------------------------------------------------
|P5 (shed lvl 3)|Comfort heating, ICE (non-critical)|shed on battery-only|
--------------------------------------------------
|P6 (shed lvl 4)|External lighting except NAV lights|shed on low battery|
-------------------------------------------------- ||

|| Requirement No:PWR-033 || Requirement: The PWR subsystem shall enforce the mode-transition rules of PWR_Mode_Transitions.
Table Type: MESSAGE
Table Name or Description: PWR_Mode_Transitions
Table: PWR_Mode_Transitions
|From|To|Trigger|Max Latency|
--------------------------------------------------
|GROUND|NORMAL|WoW=FALSE and ≥ 1 gen online|200 ms|
--------------------------------------------------
|NORMAL|SINGLE_GEN|1 generator failure|50 ms|
--------------------------------------------------
|NORMAL|EMERGENCY|all generators failed|50 ms|
--------------------------------------------------
|SINGLE_GEN|EMERGENCY|remaining generator failed|50 ms|
--------------------------------------------------
|EMERGENCY|SINGLE_GEN|one generator restored|200 ms|
--------------------------------------------------
|any|FAULT|PWR-010, PWR-011, or multiple GCU fault|50 ms|
-------------------------------------------------- ||

Header: Test
|| Requirement No:PWR-034 || Requirement: Generator-loss load transfer (PWR-006) shall be verified by intentionally tripping GCU1 then GCU2 on the iron-bird power rig, demonstrating bus voltages remain within MIL-STD-704F limits during the transition and no essential-bus brownout > 50 ms.
Verifies: PWR-006
References: MIL-STD-704F ||

|| Requirement No:PWR-035 || Requirement: Hold-up delivery (PWR-018) shall be verified by DO-160G §16 Category Z test on each essential-bus LRU with 10, 25, 50, and 75 ms interruptions, confirming all LRUs continue operation through the 50 ms point.
Verifies: PWR-018
References: DO-160G-16 ||
