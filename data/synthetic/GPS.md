#Requirement: REQ-GPS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: GPS
BASELINE: v1.6.0
ABSOLUTE PATH: /AeroSys/Common/GPS

Header: PURPOSE
|| Requirement No:GPS-001 || Requirement: This document specifies the GPS/GNSS Receiver requirements for the AeroSys Dynamics common GNSS LRU, applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3 platforms. The GNSS receiver software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and DAL-B on Skyrunner-T1 and Nimbus-C3, with hardware per DO-254 Level A or Level B respectively. ||

Header: SCOPE
|| Requirement No:GPS-002 || Requirement: This module covers GNSS signal acquisition, tracking, pseudorange and Doppler measurement, position/velocity/time (PVT) solution, SBAS augmentation processing, receiver-autonomous integrity monitoring (RAIM), and fault detection and exclusion (FDE). It excludes the antenna (##STR.STR-028 allocates physical placement) and the downstream navigation fusion (##NAV.NAV-010). ||

Header: REFERENCES
|| Requirement No:GPS-003 || Requirement: The governing references are: RTCA DO-253D (Minimum Operational Performance Standards for GPS/SBAS airborne equipment), RTCA DO-229F (GPS/WAAS), RTCA DO-283B (RNP), RTCA DO-178C, RTCA DO-254, RTCA DO-160G, ICAO Annex 10 Volume I (GNSS SARPS), and IS-GPS-200N (GPS Interface Specification). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|GNSS|Global Navigation Satellite System|
--------------------------------------------------
|GPS|Global Positioning System|
--------------------------------------------------
|SBAS|Satellite-Based Augmentation System|
--------------------------------------------------
|PVT|Position, Velocity, Time solution|
--------------------------------------------------
|PRN|Pseudo-Random Noise|
--------------------------------------------------
|RAIM|Receiver Autonomous Integrity Monitoring|
--------------------------------------------------
|FDE|Fault Detection and Exclusion|
--------------------------------------------------
|TTFF|Time To First Fix|
--------------------------------------------------
|DOP|Dilution of Precision|
--------------------------------------------------
|HDOP|Horizontal DOP|
--------------------------------------------------
|VDOP|Vertical DOP|
--------------------------------------------------
|CEP|Circular Error Probable|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:GPS-004 || Requirement: The GNSS receiver shall support the following operational states:
    a) OFF
    b) WARMUP (clock and oscillator stabilisation)
    c) ACQUIRE (signal search)
    d) TRACK (2D fix, < 4 SVs)
    e) NAV (3D fix, ≥ 4 SVs, RAIM valid)
    f) NAV_SBAS (3D fix with SBAS augmentation)
    g) DEGRADED (fix but RAIM failed or geometry poor)
    h) FAULT ||

|| Requirement No:GPS-005 || Requirement: The GNSS receiver shall acquire the first 3D fix within the following Time-To-First-Fix bounds under open-sky conditions: cold start ≤ 60 s, warm start ≤ 30 s, hot start ≤ 5 s.
References: DO-253D ||

|| Requirement No:GPS-006 || Requirement: The GNSS receiver shall transition from TRACK to NAV automatically when at least 4 SVs are tracked with elevation ≥ 5°, HDOP ≤ 6, VDOP ≤ 8, and RAIM availability flag asserted.
References: DO-229F ||

|| Requirement No:GPS-007 || Requirement: The GNSS receiver shall transition from NAV to NAV_SBAS automatically when at least one SBAS geostationary satellite is tracked, its messages are valid, and all corrections are applicable to the current position (within the SBAS service volume).
References: DO-229F ||

|| Requirement No:GPS-008 || Requirement: The GNSS receiver shall transition from NAV or NAV_SBAS to DEGRADED if RAIM declares an unresolved satellite fault, if HDOP exceeds 6, or if fewer than 4 SVs remain trackable.
References: DO-229F ||

Header: General
|| Requirement No:GPS-009 || Requirement: The GNSS receiver shall track GPS L1 C/A (1575.42 MHz) as the minimum constellation on all platforms, and shall additionally track GPS L5 (1176.45 MHz) and Galileo E1/E5a on Stratos-7, AeroLynx-X2, and Nimbus-C3 for multi-constellation and multi-frequency operation.
References: IS-GPS-200N ||

|| Requirement No:GPS-010 || Requirement: The GNSS receiver shall output UTC time accurate to ≤ 50 ns 1-sigma when NAV is valid, provided to downstream systems (##INS.INS-037, ##FCC.FCC-034) via a 1 pulse-per-second (1PPS) hardware discrete and a time-of-week message.
Satisfies: ##INS.INS-037 ||

|| Requirement No:GPS-011 || Requirement: The GNSS receiver shall achieve horizontal position accuracy ≤ 5 m CEP in NAV mode (unaugmented) and ≤ 1 m CEP in NAV_SBAS mode under open-sky conditions.
References: DO-229F ||

|| Requirement No:GPS-012 || Requirement: The GNSS receiver shall publish velocity with 3D accuracy ≤ 0.1 m/s 1-sigma in NAV or NAV_SBAS mode under dynamic conditions up to 5 g and 400 m/s velocity.
Satisfies: ##AUTO.AUTO-014 ||

|| Requirement No:GPS-013 || Requirement: The GNSS receiver shall publish PVT updates at 10 Hz for INS aiding (##INS.INS-043) and at 1 Hz for GCS display (##GCS.GCS-045).
Satisfies: ##INS.INS-043 ||

|| Requirement No:GPS-014 || Requirement: The GNSS receiver shall implement Fault Detection and Exclusion (FDE) per DO-229F, detecting an unhealthy satellite within 6 s of fault onset when geometry supports FDE (≥ 6 SVs in view, HDOP ≤ 4), and excluding the unhealthy satellite from the PVT solution.
References: DO-229F ||

|| Requirement No:GPS-015 || Requirement: The GNSS receiver shall process SBAS messages (EGNOS, WAAS, or any ICAO-compliant SBAS within service volume) per DO-229F, applying fast corrections, slow corrections, and ionospheric corrections to the PVT solution.
Satisfies: ##INS.INS-022
References: DO-229F ||

|| Requirement No:GPS-016 || Requirement: The GNSS receiver shall support RNP APCH procedures down to LNAV/VNAV and LPV minima per DO-229F, providing integrity bounds (HPL, VPL) at the 10 Hz PVT rate.
References: DO-283B, DO-229F ||

|| Requirement No:GPS-017 || Requirement: The GNSS receiver shall raise an integrity alert within 6 s (enroute), 4 s (terminal), and 2 s (approach) of an unresolved HPL or VPL exceedance per DO-229F alert-limit timing.
References: DO-229F ||

|| Requirement No:GPS-018 || Requirement: The GNSS receiver shall track minimum 12 SVs simultaneously for GPS L1 C/A (≥ 24 parallel correlator channels when multi-constellation tracking is active on tactical platforms).
References: IS-GPS-200N ||

|| Requirement No:GPS-019 || Requirement: The GNSS receiver shall re-acquire a fix within 30 s after a signal-outage event (loss of all SVs for 60 s followed by return to open-sky conditions). ||

|| Requirement No:GPS-020 || Requirement: The GNSS receiver shall publish HDOP, VDOP, PDOP, and TDOP with every PVT solution, for downstream use by the INS Kalman-gain scheduler per ##INS.INS-030.
Satisfies: ##INS.INS-030 ||

|| Requirement No:GPS-021 || Requirement: On Stratos-7 and AeroLynx-X2, the GNSS receiver shall support anti-spoofing by requiring authenticated GPS Chimera-compatible signals where available and by verifying SBAS message authentication (SBAS Authentication per ICAO draft SARPS) where the service provides it.
References: DO-326A ||

|| Requirement No:GPS-022 || Requirement: The GNSS receiver shall detect jamming via C/N0 degradation monitoring, raising a JAMMING_SUSPECT flag when received carrier-to-noise density falls below 30 dB-Hz across ≥ 75 % of tracked satellites for > 2 s.
Satisfies: ##SEC.SEC-028 ||

|| Requirement No:GPS-023 || Requirement: On JAMMING_SUSPECT, the GNSS receiver shall notify the security monitor (##SEC.SEC-028) and shall continue PVT output if any SVs remain trackable, flagging the reduced-confidence condition in the PVT validity field.
Refines: GPS-022 ||

|| Requirement No:GPS-024 || Requirement: The GNSS receiver shall support cold-boot operation following Chinese-remainder ambiguity resolution and almanac refresh within 12 min of first-ever power-up, without requiring any operator input other than antenna connection. ||

|| Requirement No:GPS-025 || Requirement: The GNSS receiver shall operate continuously across the temperature range -40 °C to +70 °C per DO-160G §4 Category A2, with degradation of TTFF not exceeding 50 % at the temperature extremes.
References: DO-160G-4 ||

|| Requirement No:GPS-026 || Requirement: The GNSS receiver shall accept nominal 28 V DC input per MIL-STD-704F, with steady-state draw ≤ 12 W and 50 ms power-interruption ride-through via hold-up capacitor energy per ##PWR.PWR-018.
Satisfies: ##PWR.PWR-018 ||

Header: Interface
|| Requirement No:GPS-027 || Requirement: On Stratos-7 and AeroLynx-X2, the GNSS receiver shall publish GPS_PVT_MSG on MIL-STD-1553B Bus A every 100 ms with the GNSS as Remote Terminal 7.
References: MIL-STD-1553B ||

|| Requirement No:GPS-028 || Requirement: On Skyrunner-T1 and Nimbus-C3, the GNSS receiver shall publish GPS_PVT_WORD on ARINC 429 high-speed with labels 103 (horizontal velocity), 104 (vertical velocity), 110 (latitude), 111 (longitude), 076 (altitude), 150 (UTC time), 101 (HDOP/VDOP) at 10 Hz. Additionally a 1PPS hardware discrete shall be routed to the INS and FCC per ##INS.INS-037 and ##FCC.FCC-034.
References: ARINC 429 ||

|| Requirement No:GPS-029 || Requirement: The GNSS receiver shall accept external aiding (external PVT hypothesis, coarse position and time) via a maintenance-only command to reduce TTFF after long storage; operator authentication shall be required per ##SEC.SEC-015. ||

|| Requirement No:GPS-030 || Requirement: The GNSS receiver shall format the GPS_PVT_MSG per the table below.
Table Type: MESSAGE
Table Name or Description: GPS_PVT_Msg
Table: GPS_PVT_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|lat|float64|-90 to +90 deg|1e-9 deg|
--------------------------------------------------
|lon|float64|-180 to +180 deg|1e-9 deg|
--------------------------------------------------
|alt_wgs84|float32|-1000 to +60000 ft|0.01 ft|
--------------------------------------------------
|vel_ned|float32 ×3|-1500 to +1500 kt|0.001 kt|
--------------------------------------------------
|utc_time|uint64|UTC nanoseconds|1 ns|
--------------------------------------------------
|hdop,vdop|float32 ×2|0 to 50|0.01|
--------------------------------------------------
|num_sv|uint8|0 to 32|integer|
--------------------------------------------------
|fix_type|uint8|enum {NO_FIX, 2D, 3D, 3D_SBAS}|integer|
--------------------------------------------------
|hpl,vpl|float32 ×2|0 to 10000 m|0.1 m|
--------------------------------------------------
|valid_flags|uint16|bitmask|bit|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:GPS-031 || Requirement: The GNSS receiver shall indicate PVT validity per the GPS_Valid_Flags table.
Table Type: MESSAGE
Table Name or Description: GPS_Valid_Flags
Table: GPS_Valid_Flags
|Bit|Name|Meaning (1=valid)|
--------------------------------------------------
|0|POS_VALID|position within accuracy spec|
--------------------------------------------------
|1|VEL_VALID|velocity within accuracy spec|
--------------------------------------------------
|2|TIME_VALID|UTC time sync ≤ 50 ns|
--------------------------------------------------
|3|SBAS_ACTIVE|SBAS corrections applied|
--------------------------------------------------
|4|RAIM_OK|RAIM availability asserted|
--------------------------------------------------
|5|FDE_ACTIVE|FDE algorithm active|
--------------------------------------------------
|6|JAMMING_SUSPECT|jamming detected per GPS-022|
--------------------------------------------------
|7|SPOOF_SUSPECT|spoof indicators present|
--------------------------------------------------
|8|AUTH_SIGNAL|authenticated signal in use (STR7/ALX2)|
--------------------------------------------------
|9-15|reserved|0|
-------------------------------------------------- ||

|| Requirement No:GPS-032 || Requirement: The GNSS receiver shall enforce the alert-limit thresholds per the DO-229F Alert Limits table.
Table Type: MESSAGE
Table Name or Description: DO229F_Alert_Limits
Table: DO229F_Alert_Limits
|Phase|HAL|VAL|Time-to-Alert|
--------------------------------------------------
|Enroute|2 nmi|n/a|6 s|
--------------------------------------------------
|Terminal|1 nmi|n/a|4 s|
--------------------------------------------------
|LNAV approach|556 m|n/a|2 s|
--------------------------------------------------
|LNAV/VNAV|556 m|50 m|2 s|
--------------------------------------------------
|LPV-200|40 m|35 m|2 s|
--------------------------------------------------
References: DO-229F ||

Header: Test
|| Requirement No:GPS-033 || Requirement: TTFF (GPS-005) shall be verified by laboratory test on an RF simulator with 20 repetitions per start class, demonstrating cold-start ≤ 60 s, warm-start ≤ 30 s, hot-start ≤ 5 s at the 90 % level.
Verifies: GPS-005
References: DO-253D ||

|| Requirement No:GPS-034 || Requirement: RAIM/FDE performance (GPS-014, GPS-017) shall be verified by satellite-fault injection on an RF simulator, introducing pseudorange step errors of 50 m, 100 m, and 500 m; the receiver shall raise the integrity alert within the applicable time-to-alert of GPS-032.
Verifies: GPS-014, GPS-017
References: DO-229F ||

|| Requirement No:STR7-GPS-001 || Requirement: On Stratos-7, the GNSS receiver shall be dual-antenna installed for heading aiding during prolonged static ground operations, with antenna baseline ≥ 1.5 m providing heading accuracy ≤ 0.2° 1-sigma. ||

|| Requirement No:ALX2-GPS-001 || Requirement: On AeroLynx-X2, the GNSS receiver shall support operations in littoral environments where multipath exceeds open-sky conditions, with multipath-mitigation algorithms (narrow correlator, MEDLL or equivalent) enabled by default. ||

|| Requirement No:SKT1-GPS-001 || Requirement: On Skyrunner-T1, the GNSS receiver shall be a single-frequency L1 C/A receiver with optional Galileo E1, omitting SBAS due to the lower certification class (DAL-B, DO-326A only).
Refines: GPS-009 ||

|| Requirement No:NBC3-GPS-001 || Requirement: On Nimbus-C3, the GNSS receiver shall support LPV-200 approaches per DO-229F §2.1.4.2 to enable civil cargo operations into SBAS-equipped airfields.
References: DO-229F ||

|| Requirement No:NBC3-GPS-002 || Requirement: On Nimbus-C3, the GNSS receiver shall publish a raw-measurement datastream (pseudoranges, carrier phase, Doppler) at 1 Hz to support on-ground post-flight analysis per ##FDR.FDR-022 and ADS-B-Out integration where mandated.
Satisfies: ##FDR.FDR-022 ||
