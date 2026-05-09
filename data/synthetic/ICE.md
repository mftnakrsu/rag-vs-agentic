#Requirement: REQ-ICE
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: ICE
BASELINE: v1.2.0
ABSOLUTE PATH: /AeroSys/Common/ICE

Header: PURPOSE
|| Requirement No:ICE-001 || Requirement: This document specifies the De-Ice and Anti-Ice System (ICE) requirements for Stratos-7, AeroLynx-X2, and Nimbus-C3. Skyrunner-T1 is limited to visual-meteorological-conditions (VMC) operation and does not host an ICE subsystem. ICE control software shall be developed at DO-178C DAL-B on all applicable platforms. ||

Header: SCOPE
|| Requirement No:ICE-002 || Requirement: This module covers anti-icing (preventing ice formation) on critical surfaces and sensors, de-icing (removing formed ice) where equipped (leading-edge, propeller), pitot/static-port heating, AOA vane heating, and ice-detection sensors. It excludes fuel heating (##FUEL.FUEL-006). ||

Header: REFERENCES
|| Requirement No:ICE-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, RTCA DO-160G §24 (icing), FAR Part 25 Appendix C (icing envelope), SAE ARP4754A, SAE AIR5315 (ice protection). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|SLD|Supercooled Large Droplet|
--------------------------------------------------
|LWC|Liquid Water Content|
--------------------------------------------------
|MVD|Median Volumetric Diameter|
--------------------------------------------------
|OAT|Outside Air Temperature|
--------------------------------------------------
|ID|Ice Detection|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:ICE-004 || Requirement: The ICE subsystem shall support the following modes:
    a) OFF
    b) ANTI_ICE (continuous heating)
    c) DE_ICE (cyclic operation to shed accumulated ice)
    d) AUTO (automatic activation based on ice-detection sensor)
    e) FAULT ||

|| Requirement No:ICE-005 || Requirement: In AUTO mode, the ICE subsystem shall engage anti-icing automatically when the ice-detector output indicates ice accretion > 0.5 mm or when OAT < 5 °C with visible moisture, and shall disengage 5 min after ice-detector output clears and OAT exceeds 10 °C. ||

Header: General
|| Requirement No:ICE-006 || Requirement: The ICE subsystem shall protect critical wing leading-edge sections on Stratos-7 (electro-thermal), AeroLynx-X2 (electro-mechanical pneumatic boots), and Nimbus-C3 (electro-thermal) per each platform's installation.
References: SAE AIR5315 ||

|| Requirement No:ICE-007 || Requirement: The ICE subsystem shall protect engine inlet lips on Stratos-7 and Nimbus-C3 with electro-thermal heating, preventing ice formation under certified icing envelope per FAR Part 25 Appendix C.
References: FAR Part 25 App C ||

|| Requirement No:ICE-008 || Requirement: The ICE subsystem shall provide heating for pitot and static ports (both sides) per ##ADS.ADS-019 with power monitoring and HEATER_FAIL propagated to operator.
Satisfies: ##ADS.ADS-019 ||

|| Requirement No:ICE-009 || Requirement: The ICE subsystem shall provide AOA vane/probe heating with current monitoring, raising a HEATER_FAIL on current below 50 % of nominal for > 5 s. ||

|| Requirement No:ICE-010 || Requirement: The ICE subsystem shall provide propeller de-ice on AeroLynx-X2 and Nimbus-C3 (turboprop blades), with cyclic activation per blade and slip-ring power delivery. ||

|| Requirement No:ICE-011 || Requirement: The ICE subsystem shall incorporate a primary ice-detector sensor (magnetostrictive or vibrating-probe type) with accumulated-ice indication ≥ 0.5 mm resolution, and shall raise ICE_DETECTED flag when thresholds exceeded. ||

|| Requirement No:ICE-012 || Requirement: The ICE subsystem shall monitor SLD (supercooled large droplet) indication via OAT trending and pilot-observation aid, raising SLD_SUSPECT flag when flight-entry into SLD environment is indicated. ||

|| Requirement No:ICE-013 || Requirement: The ICE subsystem shall operate across DO-160G §24 Category X (Part 25 Appendix C envelope) with LWC up to 2.0 g/m³ and MVD up to 40 µm, maintaining ice-free conditions on protected surfaces.
References: DO-160G-24, FAR Part 25 App C ||

|| Requirement No:ICE-014 || Requirement: The ICE subsystem shall report power-consumption per heated zone at 0.5 Hz, with total ICE power draw not exceeding 40 % of generator capacity per ##PWR.PWR-017.
Satisfies: ##PWR.PWR-017 ||

|| Requirement No:ICE-015 || Requirement: The ICE subsystem shall defer engagement of non-critical heater zones (cabin/comfort heating if fitted) during high-power operations (takeoff, emergency) to preserve electrical budget per ##PWR.PWR-032 (P5 shed level).
Satisfies: ##PWR.PWR-032 ||

|| Requirement No:ICE-016 || Requirement: The ICE subsystem shall publish ICE_STATUS_MSG at 1 Hz to GCS and FDR including mode, per-zone on/off state, ice-detector output, and fault-word. ||

|| Requirement No:ICE-017 || Requirement: The ICE subsystem shall log ICE engagement events (ON/OFF transitions, fault conditions) with UTC timestamp to ##FDR.FDR-017 (via FDR event-record path). ||

|| Requirement No:ICE-018 || Requirement: The ICE subsystem shall sustain the 50 ms power-interruption per DO-160G §16 Category Z, with all heater states restored within 2 s of power recovery.
References: DO-160G-16 ||

Header: Interface
|| Requirement No:ICE-019 || Requirement: The ICE subsystem shall accept operator commands (mode change, manual override) from the GCS per ##CDL.CDL-030 with authentication.
Satisfies: ##CDL.CDL-030 ||

Header: Tables
|| Requirement No:ICE-020 || Requirement: The ICE subsystem shall manage heated zones per the Heated_Zones table.
Table Type: MESSAGE
Table Name or Description: Heated_Zones
Table: Heated_Zones
|Zone|Platform|Power (W)|Activation|
--------------------------------------------------
|Pitot probe (L/R)|all except SKT1|150 × 2|AUTO or manual|
--------------------------------------------------
|AOA vane|STR7/ALX2/NBC3|80|AUTO|
--------------------------------------------------
|Static port|STR7/ALX2/NBC3|50|AUTO|
--------------------------------------------------
|Wing LE (electro-thermal)|STR7, NBC3|2500 each side|AUTO or manual|
--------------------------------------------------
|Wing LE (pneumatic boots)|ALX2|50 (control only)|cyclic|
--------------------------------------------------
|Engine inlet lip|STR7, NBC3|800|AUTO|
--------------------------------------------------
|Propeller|ALX2, NBC3|1200 total|cyclic|
-------------------------------------------------- ||
