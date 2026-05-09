#Requirement: REQ-STR
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: STR
BASELINE: v1.4.0
ABSOLUTE PATH: /AeroSys/Common/STR

Header: PURPOSE
|| Requirement No:STR-001 || Requirement: This document specifies the Structural and Airframe Loads requirements allocating structural performance, loads, and installation provisions for the AeroSys Dynamics platforms. Structures analysis and certification follow FAR Part 25 and FAR Part 23 (adapted for UAS), MIL-HDBK-516F, ARP4754A. ||

Header: SCOPE
|| Requirement No:STR-002 || Requirement: This module covers load envelopes relevant to avionics and subsystems (structural margins for commanded manoeuvres), mounting allocations for LRUs, pitot/antenna placement, and structural feedback for control-law gain scheduling. It excludes primary airframe stress analysis. ||

Header: REFERENCES
|| Requirement No:STR-003 || Requirement: The governing references are: FAR Part 25 / Part 23, MIL-HDBK-516F, MIL-STD-1530 (Aircraft Structural Integrity Programme), SAE ARP4754A, MIL-STD-810H, SAE AS50881. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|MTOW|Maximum Take-Off Weight|
--------------------------------------------------
|MAC|Mean Aerodynamic Chord|
--------------------------------------------------
|CG|Centre of Gravity|
--------------------------------------------------
|Nz|Normal Load Factor|
--------------------------------------------------
|LRU|Line-Replaceable Unit|
--------------------------------------------------
|GVT|Ground Vibration Test|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:STR-008 || Requirement: The airframe structural design limit load shall support the commanded Nz envelope per ##FCC.FCC-049 plus 50 % ultimate margin, specifically Nz +3.5 g / -1.0 g clean and down to +2.0 g / 0.0 g with flaps.
Satisfies: ##FCC.FCC-049
References: FAR Part 25 ||

|| Requirement No:STR-012 || Requirement: The structural design shall provide servo-actuator mounting with stiffness ≥ 10^6 N/m at each mount point per platform, supporting control-surface dynamic response assumptions in ##FCC.FCC-002.
Satisfies: ##FCC.FCC-002 ||

|| Requirement No:STR-020 || Requirement: The airframe ground-vibration test (GVT) shall produce a validated modal model with natural frequencies and mode shapes feeding the Structural_Notch_Filter coefficients per ##FCC.FCC-039.
Satisfies: ##FCC.FCC-027, ##FCC.FCC-039 ||

|| Requirement No:STR-022 || Requirement: The pitot and static ports shall be installed in locations with position-error characteristics validated in flight-test, with position-error correction (PEC) curves stored in ##ADS.ADS-016.
Satisfies: ##ADS.ADS-016 ||

|| Requirement No:STR-025 || Requirement: The airframe flutter-clearance envelope shall be validated via GVT plus in-flight flutter tests per MIL-HDBK-516F, demonstrating adequate damping and no aeroelastic instability up to Vmo / Mmo + 15 % margin.
Satisfies: ##FCC.FCC-056
References: MIL-HDBK-516F ||

|| Requirement No:STR-028 || Requirement: The GNSS antenna placement shall provide clear sky view for elevation angles ≥ 5° around the upper hemisphere, with no installation-induced multipath degrading ##GPS.GPS-011 accuracy.
Satisfies: ##GPS.GPS-011 ||

|| Requirement No:STR-030 || Requirement: The battery mounting bracket shall be qualified to 6 g shock per DO-160G §7 Category B and sustain the peak acceleration loads per ##APM.APM-031.
Satisfies: ##APM.APM-031
References: DO-160G-7 ||

|| Requirement No:STR-032 || Requirement: The fuel-tank structural design and piping installation shall contain fuel under all certified-envelope manoeuvres with fluid susceptibility testing per DO-160G §11, supporting ##FUEL.FUEL-002 scope.
Satisfies: ##FUEL.FUEL-002
References: DO-160G-11 ||

|| Requirement No:STR-035 || Requirement: The landing gear tire and wheel mechanical design shall conform to SAE AS81714 load-rated for platform MTOW with safety factor 1.5, supporting the LDG subsystem operation per ##LDG.LDG-002.
Satisfies: ##LDG.LDG-002
References: SAE AS81714 ||

|| Requirement No:STR-038 || Requirement: The payload bay mounting rails and bus routing shall provide the dedicated payload-bus path per ##PLD.PLD-003 with EMC shielding adequate to meet ##DLNK.DLNK-017 and ##CDL.CDL-024 coexistence requirements.
Satisfies: ##PLD.PLD-003 ||

|| Requirement No:STR-040 || Requirement: The landing gear strut and mount structure shall sustain the platform design sink rate specified in ##LDG.LDG-022 without permanent deformation at design limit load and without functional loss at ultimate load (1.5 ×).
Satisfies: ##LDG.LDG-022 ||

|| Requirement No:STR-042 || Requirement: The SAR antenna mounting location shall provide the required look angle per ##SAR.SAR-004 spotlight and stripmap modes with minimal structural occlusion of the radar beam.
Satisfies: ##SAR.SAR-004 ||

|| Requirement No:STR-004 || Requirement: The structural design shall permit avionics-bay LRU removal and installation (LRU swap) without disassembly of adjacent structure, with MTTR (mean time to replace) ≤ 30 min for flight-critical LRUs. ||

|| Requirement No:STR-005 || Requirement: The structural design shall accommodate LRU mass growth up to 15 % over the current baseline without requiring structural redesign, with CG budget allocations maintained. ||

|| Requirement No:STR-006 || Requirement: The pitot probe location shall be selected to avoid upwash and downwash effects at AOA within the certified flight envelope, with position-error correction curves ≤ 3 kt at cruise verified per ##ADS.ADS-016. ||

|| Requirement No:STR-007 || Requirement: The airframe shall provide lightning protection per DO-160G §22/§23 with bond paths to carry lightning currents without damaging enclosed electronics, in cooperation with ##PWR.PWR-022.
References: DO-160G-22, DO-160G-23 ||

|| Requirement No:STR-009 || Requirement: The airframe shall support HIRF (High-Intensity Radiated Fields) environments per DO-160G §20 Category Y (or Category X on Stratos-7 for military-threat spectrum).
References: DO-160G-20 ||

|| Requirement No:STR-010 || Requirement: The airframe shall be qualified against DO-160G §24 icing conditions where ICE subsystem (##ICE.ICE-001) is installed, with protected surfaces identified in the airframe configuration drawings.
Satisfies: ##ICE.ICE-001
References: DO-160G-24 ||

|| Requirement No:STR-011 || Requirement: The airframe shall provide cooling-air inlet scoops (Stratos-7, AeroLynx-X2, Nimbus-C3) sized to support the TCS airflow budget per ##TCS.TCS-009.
Satisfies: ##TCS.TCS-009 ||

|| Requirement No:STR-013 || Requirement: The airframe shall provide a designated crash-survivable memory mounting volume and orientation (Nimbus-C3) for the FDR CSMU per ##FDR.FDR-060.
Satisfies: ##FDR.FDR-060 ||

|| Requirement No:STR-014 || Requirement: The airframe shall support an upper-hemisphere SATCOM antenna radome (Stratos-7, Nimbus-C3) with size and location consistent with ##COMM.COMM-011 operation.
Satisfies: ##COMM.COMM-011 ||

|| Requirement No:STR-015 || Requirement: The airframe shall provide dedicated cavities for the radar altimeter antenna (downward-looking) with the beam profile meeting ##RADAR.RADAR-005 coverage.
Satisfies: ##RADAR.RADAR-005 ||

|| Requirement No:STR-016 || Requirement: The airframe shall ensure gear-door and gear-strut clearance from adjacent airframe and systems with actuation margin ≥ 25 mm under max deflection, supporting ##LDG.LDG-011 operation.
Satisfies: ##LDG.LDG-011 ||

|| Requirement No:STR-017 || Requirement: The airframe design shall accommodate ±3 % CG variability envelope verified by weighing after manufacture and after each LRU configuration change. ||

|| Requirement No:STR-018 || Requirement: Structural health monitoring (SHM) sensors (optional on Stratos-7) shall feed strain and vibration data to BIT per ##BIT.BIT-024 for airframe fatigue-life tracking. ||

|| Requirement No:STR-019 || Requirement: The airframe shall meet the vibration environment of DO-160G §8 Category U (UAV severe) with margin, and the individual LRU installations shall not violate the acceleration levels assumed in their respective LRU qualifications.
References: DO-160G-8 ||

|| Requirement No:STR-021 || Requirement: The airframe shall provide dissimilar-redundant routing paths for power (##PWR.PWR-012), data bus A/B (##FCC.FCC-041), and CCDL (##FCC.FCC-046) with minimum 150 mm physical separation per AS50881.
Satisfies: ##PWR.PWR-012
References: SAE AS50881 ||

Header: Tables
|| Requirement No:STR-023 || Requirement: The structural load factors per platform are summarised in the Platform_Loads table.
Table Type: MESSAGE
Table Name or Description: Platform_Loads
Table: Platform_Loads
|Platform|Nz limit (g)|Nz ultimate (g)|CG range (% MAC)|MTOW (kg)|
--------------------------------------------------
|Stratos-7|+3.5 / -1.0|+5.25 / -1.5|18-38|~6 000|
--------------------------------------------------
|AeroLynx-X2|+3.0 / -1.0|+4.5 / -1.5|20-35|~3 000|
--------------------------------------------------
|Skyrunner-T1|+4.0 / -1.5|+6.0 / -2.25|22-32|~600|
--------------------------------------------------
|Nimbus-C3|+2.5 / -1.0|+3.75 / -1.5|20-40|~4 500|
-------------------------------------------------- ||

Header: Test
|| Requirement No:STR-024 || Requirement: Limit-load proof test (STR-008) shall be conducted on a representative airframe at design limit load on each axis, demonstrating no permanent deformation and restoration of shape after unloading.
Verifies: STR-008
References: MIL-STD-1530 ||

|| Requirement No:STR-026 || Requirement: Ground-vibration test (STR-020) shall produce a modal model with ≥ 10 bending and torsion modes identified, feeding structural-notch filter design per ##FCC.FCC-039.
Verifies: STR-020
References: MIL-HDBK-516F ||

|| Requirement No:STR-027 || Requirement: Lightning-strike protection (STR-007) shall be verified by DO-160G §22 Category A3 zoning and Category B current injection tests, confirming no damage to protected LRUs.
Verifies: STR-007
References: DO-160G-22 ||
