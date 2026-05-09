#Requirement: REQ-FUEL
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: FUEL
BASELINE: v1.5.0
ABSOLUTE PATH: /AeroSys/Common/FUEL

Header: PURPOSE
|| Requirement No:FUEL-001 || Requirement: This document specifies the Fuel System and Fuel Management requirements for the AeroSys Dynamics platforms. The Fuel control software shall be developed at DO-178C DAL-B on all platforms; hardware at DO-254 Level B. Fuel-quantity indication is a safety-related function with single-failure tolerance on Stratos-7, AeroLynx-X2, and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:FUEL-002 || Requirement: This module covers fuel-quantity sensing, fuel-flow measurement, tank-management (including cross-feed on twin-engine AeroLynx-X2), fuel-pump control, fuel-temperature and pressure monitoring, and in-flight fuel-jettison on Stratos-7 only. It excludes the FADEC/ECU fuel-metering function (##ENG.ENG-001) and the fuel piping mechanical design (##STR.STR-032). ||

Header: REFERENCES
|| Requirement No:FUEL-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, RTCA DO-160G, SAE ARP4754A, SAE ARP4761, ASTM D1655 (jet fuel specs), ASTM D910 (avgas specs), MIL-DTL-83133 (JP-8), MIL-STD-704F. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|FQIS|Fuel Quantity Indicating System|
--------------------------------------------------
|BoostP|Boost Pump|
--------------------------------------------------
|XFeed|Cross-Feed|
--------------------------------------------------
|kg/h, pph|kilograms per hour / pounds per hour|
--------------------------------------------------
|EDP|Engine Driven Pump|
--------------------------------------------------
|APU-fuel|Fuel Supply to APU|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:FUEL-004 || Requirement: The FUEL subsystem shall provide fuel-quantity indication for each tank with accuracy ±2 % of full-scale across temperature range -40 °C to +60 °C, using capacitive probes or magnetostrictive sensors per platform.
References: DO-160G-4 ||

|| Requirement No:FUEL-005 || Requirement: The FUEL subsystem shall measure fuel flow (per engine on multi-engine platforms) with accuracy ±1 % of reading in the range 10 to 2 000 pph.
References: ASTM D1655 ||

|| Requirement No:FUEL-006 || Requirement: The FUEL subsystem shall monitor fuel temperature and pressure at each tank outlet and at the engine inlet, raising WARN when temperature falls below -30 °C (fuel icing risk) or pressure drops below 5 psig on any engine supply line. ||

|| Requirement No:FUEL-007 || Requirement: The FUEL subsystem shall control boost pumps (one per tank, redundant pair per tank on Stratos-7) to maintain engine-inlet pressure ≥ 8 psig under all flight attitudes within the certified envelope. ||

|| Requirement No:FUEL-008 || Requirement: On AeroLynx-X2, the FUEL subsystem shall support cross-feed operation to supply either engine from either wing tank, operator-commanded, with max switching time 2 s and inhibit during takeoff and landing. ||

|| Requirement No:FUEL-009 || Requirement: The FUEL subsystem shall detect fuel-leak (unexpected flow > 50 pph without corresponding tank-quantity decrease) within 60 s of onset and notify the operator per ##HMI.HMI-130. ||

|| Requirement No:FUEL-010 || Requirement: The FUEL subsystem shall publish FUEL_STATUS_MSG at 1 Hz with per-tank quantity, total quantity, per-engine fuel flow, fuel temperature, fuel pressure, and tank-valve states, to the FMS (##FMS.FMS-015), FCC, GCS, and FDR.
Satisfies: ##FMS.FMS-015 ||

|| Requirement No:FUEL-011 || Requirement: The FUEL subsystem shall compute total fuel remaining from per-tank quantity sums at 1 Hz and shall provide the total to the FMS for fuel-prediction per ##FMS.FMS-018. ||

|| Requirement No:FUEL-012 || Requirement: The FUEL subsystem shall support fuel-imbalance alerting when inter-tank differential exceeds 100 kg on Stratos-7 or 50 kg on AeroLynx-X2 for > 30 s, notifying the operator per ##HMI.HMI-132. ||

|| Requirement No:FUEL-013 || Requirement: On Stratos-7, the FUEL subsystem shall support in-flight fuel-jettison from the wing tanks at 500 kg/min rate, inhibited below 2 500 ft AGL, requiring explicit operator authorisation per ##HMI.HMI-135.
Satisfies: ##HMI.HMI-135 ||

|| Requirement No:FUEL-014 || Requirement: The FUEL subsystem shall maintain minimum-fuel alert at 30 min of remaining endurance at cruise power, with escalation to LOW_FUEL when fuel reaches 15 min reserve and CRITICAL_FUEL at 5 min per ICAO Annex 6.
References: ICAO Annex 6 ||

|| Requirement No:FUEL-015 || Requirement: The FUEL subsystem shall provide fuel-flow data to the FMS fuel-prediction function (##FMS.FMS-017) with accuracy supporting the ±5 % RSS prediction target.
Satisfies: ##FMS.FMS-017 ||

|| Requirement No:FUEL-016 || Requirement: The FUEL subsystem shall measure fuel density implicitly via compensated capacitive sensing, adjusting quantity calculation for fuel temperature and fuel-type selector (Jet-A, Jet-A1, JP-8, avgas depending on platform). ||

|| Requirement No:FUEL-017 || Requirement: The FUEL subsystem shall control fuel-tank venting to maintain tank pressure within manufacturer limits during climb and descent, with vent-valve position monitored and reported. ||

|| Requirement No:FUEL-018 || Requirement: The FUEL subsystem shall perform tank-quantity compensation for aircraft attitude (pitch ±25°, roll ±60°) using internal tank-geometry tables, with residual attitude-induced quantity error ≤ 2 % of tank volume. ||

|| Requirement No:FUEL-019 || Requirement: The FUEL subsystem shall publish a fuel-exhaustion-time estimate at 1 Hz based on current total fuel and current total fuel flow, updated with a 10 s smoothing filter. ||

|| Requirement No:FUEL-020 || Requirement: The FUEL subsystem shall interface with the APM to provide APU fuel supply (##APM.APM-020) with a dedicated APU-fuel shutoff valve, operator-commanded and automatically closed on APU shutdown.
Satisfies: ##APM.APM-020 ||

|| Requirement No:FUEL-021 || Requirement: On loss of boost-pump output (pressure < 5 psig for > 5 s), the FUEL subsystem shall automatically start the redundant boost pump (where fitted) and notify operator per ##HMI.HMI-138. ||

|| Requirement No:FUEL-022 || Requirement: The FUEL subsystem shall detect engine-inlet-filter blockage via differential-pressure sensor exceeding the manufacturer-specified threshold, flagging FILTER_BYPASS after 30 s and notifying operator. ||

|| Requirement No:FUEL-023 || Requirement: The FUEL subsystem shall operate across DO-160G §4 Category A2 environmental envelope and shall be qualified per DO-160G §5 (humidity), §8 (vibration), and §11 (fluid susceptibility).
References: DO-160G-4, DO-160G-8, DO-160G-11 ||

Header: Interface
|| Requirement No:FUEL-024 || Requirement: The FUEL subsystem shall publish FUEL_STATUS_MSG per the following table at 1 Hz on the primary avionics bus.
Table Type: MESSAGE
Table Name or Description: FUEL_Status_Msg
Table: FUEL_Status_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|tank_qty (array)|float32 × N|0 to max per tank (kg)|0.1 kg|
--------------------------------------------------
|total_qty|float32|0 to MTOW-related|0.1 kg|
--------------------------------------------------
|fuel_flow (per eng)|float32 ×N|0-2000 pph|0.1 pph|
--------------------------------------------------
|fuel_temp (per tank)|float32|-50 to +80 °C|0.1 °C|
--------------------------------------------------
|fuel_press (per line)|float32|0-60 psig|0.1 psig|
--------------------------------------------------
|boost_pump_state|uint16|bitmask|bit|
--------------------------------------------------
|xfeed_state|uint8|0-3 (ALX2 only)|integer|
--------------------------------------------------
|remaining_time|int32|0-36000 s|1 s|
--------------------------------------------------
|fault_word|uint32|bitmask|bit|
-------------------------------------------------- ||

|| Requirement No:FUEL-025 || Requirement: The FUEL subsystem shall accept operator commands from ##CDL.CDL-030 for cross-feed, boost-pump manual override, jettison authorisation (STR7), and APU-fuel valve, authenticated per ##SEC.SEC-010.
Satisfies: ##CDL.CDL-030 ||

|| Requirement No:FUEL-026 || Requirement: The FUEL subsystem shall coordinate with the engine FADEC/ECU (##ENG.ENG-014) such that commanded fuel flow does not exceed what the current boost-pump pressure and tank-level support. ||

Header: Tables
|| Requirement No:FUEL-027 || Requirement: The FUEL subsystem shall apply tank-configuration per the Tank_Matrix table per platform.
Table Type: MESSAGE
Table Name or Description: Tank_Matrix
Table: Tank_Matrix
|Platform|Tank IDs|Total Capacity (kg)|Feed Scheme|
--------------------------------------------------
|Stratos-7|Left Main, Right Main, Centre, Wing Aux (4 tanks)|~3 200|with jettison, cross-feed|
--------------------------------------------------
|AeroLynx-X2|Left Wing, Right Wing (2 tanks)|~1 500|cross-feed supported|
--------------------------------------------------
|Skyrunner-T1|Main (single)|~90|single-source|
--------------------------------------------------
|Nimbus-C3|Main, Auxiliary (2 tanks)|~1 800|series feed, no cross|
-------------------------------------------------- ||

|| Requirement No:FUEL-028 || Requirement: The FUEL subsystem shall monitor fuel-quality parameters per the Fuel_Quality_Params table, with exceedance triggering operator notification.
Table Type: MESSAGE
Table Name or Description: Fuel_Quality_Params
Table: Fuel_Quality_Params
|Parameter|Normal Range|Warning|Action|
--------------------------------------------------
|Fuel temperature|-30 to +50 °C|< -25 °C|notify, engage heater if fitted|
--------------------------------------------------
|Fuel pressure (engine inlet)|10-40 psig|< 8 psig|start backup pump|
--------------------------------------------------
|Tank vent pressure|±0.5 psig|±1.0 psig|check vent|
--------------------------------------------------
|Filter ΔP|< 5 psi|> 7 psi|check filter|
-------------------------------------------------- ||

Header: Test
|| Requirement No:FUEL-029 || Requirement: Fuel-quantity accuracy (FUEL-004) shall be verified by laboratory test on a representative tank shape over the certified attitude envelope, with calibrated reference volumes, demonstrating ±2 % full-scale accuracy at 10 attitude points.
Verifies: FUEL-004
References: DO-160G-4 ||

|| Requirement No:FUEL-030 || Requirement: Leak detection (FUEL-009) shall be verified by injecting a simulated leak (controlled venting) into the fuel system instrumentation, confirming detection within 60 s and operator alert raised.
Verifies: FUEL-009 ||
