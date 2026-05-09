#Requirement: REQ-TCS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: TCS
BASELINE: v1.3.0
ABSOLUTE PATH: /AeroSys/Common/TCS

Header: PURPOSE
|| Requirement No:TCS-001 || Requirement: This document specifies the Thermal Control System (TCS) requirements for Stratos-7, AeroLynx-X2, and Nimbus-C3. Skyrunner-T1 relies on passive cooling only and does not host an active TCS. The TCS software shall be developed at DO-178C DAL-B on all applicable platforms. ||

Header: SCOPE
|| Requirement No:TCS-002 || Requirement: This module covers avionics-bay thermal management, payload-sensor cooling, battery thermal conditioning, and coordination with environmental systems (ICE, ##ICE.ICE-001). It excludes the engine-bay cooling (##ENG.ENG-029) and passive structural thermal behaviour. ||

Header: REFERENCES
|| Requirement No:TCS-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-160G §4 (temperature and altitude), §5 (humidity), SAE ARP4754A, SAE ARP4761. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|TCS|Thermal Control System|
--------------------------------------------------
|ECS|Environmental Control System|
--------------------------------------------------
|VCS|Vapour Compression System|
--------------------------------------------------
|LCU|Liquid Cooling Unit|
--------------------------------------------------
|TIM|Thermal Interface Material|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:TCS-004 || Requirement: The TCS shall maintain avionics-bay air temperature within 5 °C to 55 °C at DO-160G §4 Category A2 operating altitude range, with active cooling engaging when bay temperature exceeds 45 °C.
References: DO-160G-4 ||

|| Requirement No:TCS-005 || Requirement: The TCS shall regulate cold-plate temperatures for high-power electronics (CDL RF, SAR transmitter, EOIR cryo cooler) within ±3 °C of their operating setpoints. ||

|| Requirement No:TCS-006 || Requirement: The TCS shall control variable-speed fans and (on Stratos-7) a vapour-compression cycle with operating feedback to maintain setpoints under varying ambient and load conditions. ||

|| Requirement No:TCS-007 || Requirement: The TCS shall monitor bay and equipment temperatures at 1 Hz with per-sensor accuracy ±1 °C, and shall publish TCS_STATUS_MSG to GCS and FDR at 1 Hz. ||

|| Requirement No:TCS-008 || Requirement: The TCS shall provide heat-dissipation capability for tactical datalink terminals per ##DLNK.DLNK-020 during TX-active slots, without allowing terminal-chassis temperature to exceed the manufacturer limit.
Satisfies: ##DLNK.DLNK-020 ||

|| Requirement No:TCS-009 || Requirement: The TCS shall scale cooling capacity with altitude, increasing fan speed to compensate for reduced air density above 20 000 ft, following a predefined altitude-compensation schedule. ||

|| Requirement No:TCS-010 || Requirement: The TCS shall detect coolant-loop failure (pressure loss > 20 % of nominal, or flow below the minimum threshold for > 5 s) on Stratos-7, and shall start the standby pump within 2 s if fitted. ||

|| Requirement No:TCS-011 || Requirement: The TCS shall publish an over-temperature warning to the operator per ##HMI.HMI-007 when any critical component temperature exceeds 90 % of its max-rated value, and an EMERGENCY alert at max-rated. ||

|| Requirement No:TCS-012 || Requirement: The TCS shall coordinate with the APM for battery thermal management per ##APM.APM-017 and ##APM.APM-018, maintaining cell temperatures 0 °C to 45 °C during charging and -20 °C to 60 °C during discharge.
Satisfies: ##APM.APM-017, ##APM.APM-018 ||

|| Requirement No:TCS-013 || Requirement: The TCS shall maintain cockpit-equivalent avionics-bay humidity within DO-160G §5 Category A/B/C range through airflow management, with no condensation on unprotected electronics.
References: DO-160G-5 ||

|| Requirement No:TCS-014 || Requirement: The TCS shall initiate pre-flight warm-up (battery heaters, equipment heaters) on ground external power at ambient temperatures below 0 °C before permitting engine start. ||

|| Requirement No:TCS-015 || Requirement: The TCS shall coordinate with the engine FADEC (##ENG.ENG-029) to ensure engine-bay cooling airflow supports continuous operation at peak thrust.
Satisfies: ##ENG.ENG-029 ||

|| Requirement No:TCS-016 || Requirement: The TCS shall monitor inlet air-temperature and compensate cold-plate control loops to maintain setpoints across OAT -40 °C to +55 °C per DO-160G §4 Category A2.
References: DO-160G-4 ||

|| Requirement No:TCS-017 || Requirement: The TCS shall log thermal events (over-temperature trips, fan failures, pump failures) to the FDR per ##FDR.FDR-070 with UTC timestamp and sensor snapshot. ||

|| Requirement No:TCS-018 || Requirement: On Stratos-7, the TCS shall support brake-cooling airflow per ##STR7-LDG-001 to permit max-brake-energy landings with carbon-carbon brakes.
Satisfies: ##STR7-LDG-001 ||

|| Requirement No:TCS-019 || Requirement: The TCS shall operate across the DO-160G §4 Category A2 environmental envelope and shall be EMC-qualified per DO-160G §20 Category Y.
References: DO-160G-4, DO-160G-20 ||

|| Requirement No:TCS-020 || Requirement: The TCS shall recover from a 50 ms power interruption per DO-160G §16 Category Z without loss of setpoint tracking for > 5 s.
References: DO-160G-16 ||

|| Requirement No:TCS-021 || Requirement: The TCS shall support graceful-degradation: on single fan or pump failure, the TCS shall redistribute load among remaining cooling resources and may reduce cold-plate setpoint tracking margins without shutdown. ||

|| Requirement No:TCS-022 || Requirement: The TCS shall provide thermal management for the payload bay per ##PLD.PLD-022 and ##SAR.SAR-018, maintaining cold-plate temperatures within the respective platform limits.
Satisfies: ##PLD.PLD-022, ##SAR.SAR-018 ||

Header: Interface
|| Requirement No:TCS-023 || Requirement: The TCS shall publish TCS_STATUS_MSG at 1 Hz per the table below.
Table Type: MESSAGE
Table Name or Description: TCS_Status_Msg
Table: TCS_Status_Msg
|Field|Type|Range|
--------------------------------------------------
|bay_temp (per zone)|float32 ×N|-40 to +80 °C|
--------------------------------------------------
|cold_plate_temp (per cp)|float32 ×N|0 to 80 °C|
--------------------------------------------------
|fan_rpm (per fan)|uint16 ×N|0 to 10000 rpm|
--------------------------------------------------
|coolant_pressure|float32|0 to 60 psig|
--------------------------------------------------
|coolant_flow|float32|0 to 10 L/min|
--------------------------------------------------
|battery_temp|float32|-30 to +70 °C|
--------------------------------------------------
|fault_word|uint32|bitmask|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:TCS-024 || Requirement: The TCS shall apply setpoints per the TCS_Setpoints table.
Table Type: MESSAGE
Table Name or Description: TCS_Setpoints
Table: TCS_Setpoints
|Zone/Component|Setpoint|Warn|Emergency|
--------------------------------------------------
|Avionics bay air|25 °C|55 °C|65 °C|
--------------------------------------------------
|CDL RF cold plate|30 °C|60 °C|75 °C|
--------------------------------------------------
|SAR transmitter cold plate (STR7)|40 °C|55 °C|70 °C|
--------------------------------------------------
|Battery cells|25 °C|50 °C|60 °C|
--------------------------------------------------
|EOIR cryo cooler|-10 °C|+20 °C|+40 °C|
-------------------------------------------------- ||

Header: Test
|| Requirement No:TCS-025 || Requirement: TCS setpoint-tracking accuracy (TCS-005) shall be verified by DO-160G §4 ambient chamber test at the hot-day (55 °C), hot-high (40 °C @ 44 000 ft), and cold-day (-40 °C) conditions, demonstrating ±3 °C cold-plate setpoint hold.
Verifies: TCS-005
References: DO-160G-4 ||
