#Requirement: REQ-SAR
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: SAR
BASELINE: v1.2.0
ABSOLUTE PATH: /AeroSys/Common/SAR

Header: PURPOSE
|| Requirement No:SAR-001 || Requirement: This document specifies the Synthetic Aperture Radar (SAR) requirements for Stratos-7 (X-band, 0.3 m spot resolution) and AeroLynx-X2 (L-band, 1.0 m wide-area resolution). SAR is not carried on Skyrunner-T1 or Nimbus-C3. The SAR software shall be developed at DO-178C DAL-B on both platforms. ||

Header: SCOPE
|| Requirement No:SAR-002 || Requirement: This module covers SAR imaging modes (stripmap, spotlight, GMTI), transmit/receive chain control, image processing (azimuth compression, motion compensation), radiation-safety interlocks, and integration with the PMC (##PLD.PLD-011). It excludes the antenna mechanical installation (##STR.STR-042) and downlink encoding (##PLD.PLD-013). ||

Header: REFERENCES
|| Requirement No:SAR-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, RTCA DO-160G, STANAG 4609 (imagery), STANAG 7023 (Air Reconnaissance Primary Imagery), ITU-R frequency allocations for X-band and L-band radar. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|SAR|Synthetic Aperture Radar|
--------------------------------------------------
|GMTI|Ground Moving Target Indication|
--------------------------------------------------
|PRF|Pulse Repetition Frequency|
--------------------------------------------------
|PRI|Pulse Repetition Interval|
--------------------------------------------------
|RCS|Radar Cross Section|
--------------------------------------------------
|DPCA|Displaced Phase Centre Antenna (for GMTI)|
--------------------------------------------------
|IPP|Inter-Pulse Period|
--------------------------------------------------
|ADC|Analog-to-Digital Converter|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:SAR-004 || Requirement: The SAR shall support the following imaging modes:
    a) OFF
    b) STANDBY (warm, no transmit)
    c) STRIPMAP (wide-area continuous imaging)
    d) SPOTLIGHT (high-resolution limited area, Stratos-7 only)
    e) GMTI (ground-moving-target indication, Stratos-7 only)
    f) BIT (built-in self-test with no transmit)
    g) FAULT ||

|| Requirement No:SAR-005 || Requirement: The SAR shall require operator authorisation per ##PLD.PLD-006 before transitioning from STANDBY to any transmitting mode, and shall enforce ##PLD.PLD-018 transmit inhibits (WoW, exclusion zones).
Satisfies: ##PLD.PLD-006 ||

Header: General
|| Requirement No:SAR-006 || Requirement: On Stratos-7, the SAR shall operate in X-band (9.3 - 9.9 GHz) with peak transmit power ≤ 2 kW, supporting stripmap resolution 1 m (swath 10 km), spotlight resolution 0.3 m (scene 2 × 2 km), and GMTI resolution supporting 1 m/s minimum detectable velocity.
References: ITU-R ||

|| Requirement No:SAR-007 || Requirement: On AeroLynx-X2, the SAR shall operate in L-band (1.25 - 1.35 GHz) with peak transmit power ≤ 1 kW, supporting wide-area stripmap resolution 1 m (swath 20 km) optimised for foliage penetration.
References: ITU-R ||

|| Requirement No:SAR-008 || Requirement: The SAR shall achieve image noise-equivalent sigma-zero ≤ -25 dB for stripmap on Stratos-7 and ≤ -22 dB on AeroLynx-X2 at the centre of the swath. ||

|| Requirement No:SAR-009 || Requirement: The SAR shall produce images with pixel location accuracy (CEP) ≤ 10 m absolute geolocation on Stratos-7 and ≤ 25 m on AeroLynx-X2, using INS (##INS.INS-020) and GPS (##GPS.GPS-011) aiding for motion compensation.
Satisfies: ##INS.INS-020, ##GPS.GPS-011 ||

|| Requirement No:SAR-010 || Requirement: The SAR shall produce imagery at a cadence of ≥ 1 image/10 s in stripmap mode and ≥ 1 image/30 s in spotlight mode (Stratos-7), streaming via the payload bus to ##PLD.PLD-011 for downlink.
Satisfies: ##PLD.PLD-011 ||

|| Requirement No:SAR-011 || Requirement: The SAR image output shall carry STANAG 7023 primary imagery metadata (platform position, velocity, look angle, time, mode, polarisation) and, where applicable, STANAG 4609 motion-imagery metadata.
References: STANAG 7023, STANAG 4609 ||

|| Requirement No:SAR-012 || Requirement: On Stratos-7, the SAR GMTI mode shall detect ground moving targets at velocities ≥ 1 m/s with false-alarm rate ≤ 10^-4 per image cell at signal-to-clutter ratio > 10 dB. ||

|| Requirement No:SAR-013 || Requirement: The SAR shall apply motion compensation to account for platform deviation from nominal straight-line geometry, using INS-derived position and attitude updates at ≥ 100 Hz during aperture formation.
Derives From: ##INS.INS-020 ||

|| Requirement No:SAR-014 || Requirement: The SAR shall enforce PRF selection to avoid range and Doppler ambiguities per the PRF_Selection_Table (SAR-022), with automatic PRF selection based on commanded mode, look-angle, and platform velocity. ||

|| Requirement No:SAR-015 || Requirement: The SAR shall inhibit transmit if any radiation-safety interlock is broken (transmit-safety cover closed, WoW asserted, exclusion-zone geofence per ##PLD.PLD-034), within 100 ms of the interlock signal.
Satisfies: ##PLD.PLD-034 ||

|| Requirement No:SAR-016 || Requirement: The SAR shall monitor transmitter health (high-voltage rail, TWT/solid-state amplifier current, thermal) at 10 Hz and shut down the transmit chain within 200 ms of any parameter redline violation. ||

|| Requirement No:SAR-017 || Requirement: The SAR shall operate across DO-160G §4 Category A2 environmental envelope and DO-160G §20 Category Y EMC with coexistence alongside the radar altimeter (##RADAR.RADAR-009) and CDL (##CDL.CDL-024).
References: DO-160G-4, DO-160G-20 ||

|| Requirement No:SAR-018 || Requirement: The SAR shall consume ≤ 1.2 kW steady-state on Stratos-7 and ≤ 800 W on AeroLynx-X2, with peak transient draw during transmit pulses managed by the TCS (##TCS.TCS-022) for thermal stability.
Satisfies: ##TCS.TCS-022 ||

|| Requirement No:SAR-019 || Requirement: The SAR shall publish SAR_STATUS_MSG at 1 Hz with mode, swath centre coordinates, current PRF, transmitter health, antenna pointing, and fault-word, to the PMC per ##PLD.PLD-011. ||

|| Requirement No:SAR-020 || Requirement: The SAR shall support CUED imaging: on receipt of a geographic point-of-interest via ##PLD.PLD-014, the SAR shall compute required look geometry and collect an image within 30 s if the point is within the sensor's current coverage envelope. ||

Header: Interface
|| Requirement No:SAR-021 || Requirement: The SAR shall interface with the PMC over the high-speed payload bus (##PLD.PLD-031, 1 Gbps Ethernet on Stratos-7 plus FibreChannel for imagery, 1 Gbps on AeroLynx-X2) for control and status, and streaming imagery egress. ||

Header: Tables
|| Requirement No:SAR-022 || Requirement: The SAR shall apply PRF selection per the PRF_Selection_Table to avoid ambiguities at the current platform velocity and look angle.
Table Type: MESSAGE
Table Name or Description: PRF_Selection_Table
Table: PRF_Selection_Table
|Mode|Platform Velocity|Nominal PRF|PRI|
--------------------------------------------------
|Stripmap (STR7 X-band)|~200 kt|1500 Hz|667 µs|
--------------------------------------------------
|Spotlight (STR7 X-band)|~200 kt|2500 Hz|400 µs|
--------------------------------------------------
|GMTI (STR7)|~200 kt|2000 Hz|500 µs|
--------------------------------------------------
|Stripmap (ALX2 L-band)|~160 kt|800 Hz|1250 µs|
-------------------------------------------------- ||

|| Requirement No:SAR-023 || Requirement: The SAR shall enforce transmitter operating limits per the SAR_TX_Limits table.
Table Type: MESSAGE
Table Name or Description: SAR_TX_Limits
Table: SAR_TX_Limits
|Platform|Peak TX Power|Duty Cycle|Avg Power|Thermal Limit|
--------------------------------------------------
|Stratos-7 X-band|2 kW|max 15 %|300 W|cold-plate T_max 55 °C|
--------------------------------------------------
|AeroLynx-X2 L-band|1 kW|max 20 %|200 W|cold-plate T_max 50 °C|
-------------------------------------------------- ||

Header: Test
|| Requirement No:SAR-024 || Requirement: Geolocation accuracy (SAR-009) shall be verified by flight-test imaging known corner-reflectors at ranges 2, 5, and 10 km, measuring reported vs truth with CEP ≤ 10 m (Stratos-7) and ≤ 25 m (AeroLynx-X2).
Verifies: SAR-009 ||

|| Requirement No:SAR-025 || Requirement: Transmit-safety interlock (SAR-015) shall be verified by attempting transmit with each interlock condition violated (WoW asserted, safety cover closed, exclusion-zone active), confirming 100 % inhibit within 100 ms.
Verifies: SAR-015
References: DO-326A ||
