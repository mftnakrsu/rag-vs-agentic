#Requirement: REQ-EOIR
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: EOIR
BASELINE: v1.4.0
ABSOLUTE PATH: /AeroSys/Common/EOIR

Header: PURPOSE
|| Requirement No:EOIR-001 || Requirement: This document specifies the Electro-Optical / Infrared (EOIR) sensor requirements for all AeroSys platforms. EOIR is carried on Stratos-7 (30 cm-class gimbal), AeroLynx-X2 (medium gimbal), Skyrunner-T1 (micro EOIR), and Nimbus-C3 (forward-hemisphere sense-and-avoid EOIR). The EOIR software shall be developed at DO-178C DAL-B on all platforms. ||

Header: SCOPE
|| Requirement No:EOIR-002 || Requirement: This module covers EO daylight and low-light imaging, thermal IR imaging, video processing and georegistration, optional laser rangefinder/designator (Stratos-7 and AeroLynx-X2), and video streaming. It excludes the payload-manager command dispatch (##PLD.PLD-001) and the downlink encoding (##PLD.PLD-013). ||

Header: REFERENCES
|| Requirement No:EOIR-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, RTCA DO-160G, STANAG 4609 (motion imagery), STANAG 3733 (infrared thermal-imager performance), MIL-STD-810H (environmental testing), eye-safety IEC 60825-1 for laser products. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|EO|Electro-Optical (visible, daylight)|
--------------------------------------------------
|IR|Infrared (thermal)|
--------------------------------------------------
|FoV|Field of View|
--------------------------------------------------
|FPA|Focal-Plane Array|
--------------------------------------------------
|LRF|Laser Rangefinder|
--------------------------------------------------
|LTD|Laser Target Designator|
--------------------------------------------------
|NUC|Non-Uniformity Correction (IR)|
--------------------------------------------------
|LoS|Line of Sight (sensor)|
--------------------------------------------------
|KLV|Key-Length-Value (metadata)|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:EOIR-004 || Requirement: The EOIR subsystem shall support the following operational modes:
    a) OFF
    b) STANDBY (sensors cooled down, cover open, no video)
    c) LIVE_EO
    d) LIVE_IR
    e) COMBINED (EO+IR fused display)
    f) SCAN (area scan pattern commanded by PMC)
    g) TRACK (target lock and follow)
    h) RANGE (LRF active, STR7/ALX2)
    i) DESIGNATE (LTD active, STR7/ALX2)
    j) FAULT ||

|| Requirement No:EOIR-005 || Requirement: In TRACK mode, the EOIR shall autonomously hold a designated target within the image frame via image-based tracker, maintaining track for targets moving at up to 100 kt relative ground speed. ||

|| Requirement No:EOIR-006 || Requirement: Entry to DESIGNATE mode shall require explicit operator authorisation per ##PLD.PLD-018 laser-safety inhibit and ##HMI.HMI-160, with LTD pulse rate configurable 5 to 20 Hz at NATO-compatible codes.
Satisfies: ##PLD.PLD-018 ||

Header: General
|| Requirement No:EOIR-007 || Requirement: The EOIR EO channel shall provide resolution per platform: Stratos-7 ≥ 1920×1080 at 30 fps daylight, AeroLynx-X2 ≥ 1280×720 at 30 fps, Skyrunner-T1 ≥ 1280×720 at 30 fps, Nimbus-C3 ≥ 720×576 at 30 fps. ||

|| Requirement No:EOIR-008 || Requirement: The EOIR IR channel shall use cooled MWIR (3-5 µm) on Stratos-7 and uncooled LWIR (8-12 µm) on AeroLynx-X2 and Skyrunner-T1, with NETD ≤ 40 mK (cooled) or ≤ 60 mK (uncooled) at 25 °C scene temperature.
References: STANAG 3733 ||

|| Requirement No:EOIR-009 || Requirement: The EOIR gimbal shall provide continuous 360° azimuth and -90° to +30° elevation on Stratos-7 and AeroLynx-X2, and ±90° azimuth and -60° to +10° elevation on Skyrunner-T1. ||

|| Requirement No:EOIR-010 || Requirement: The EOIR gimbal shall stabilise LoS against platform motion with residual LoS jitter ≤ 15 µrad RMS at cruise in normal air, ≤ 30 µrad RMS in moderate turbulence per DO-160G §7. ||

|| Requirement No:EOIR-011 || Requirement: The EOIR shall support minimum and maximum FoV: Stratos-7 0.3° narrow to 30° wide; AeroLynx-X2 0.5° to 35°; Skyrunner-T1 2° to 40°; Nimbus-C3 5° to 50° (fixed or limited-zoom lens). ||

|| Requirement No:EOIR-012 || Requirement: The EOIR shall perform NUC at power-on and at 30-minute intervals or on detected image non-uniformity >5 % peak-to-peak, with interruption to live feed limited to ≤ 2 s. ||

|| Requirement No:EOIR-013 || Requirement: The EOIR LRF (Stratos-7, AeroLynx-X2) shall measure range to target in the 100 m to 20 km range with accuracy ±5 m at ranges up to 10 km, using 1.55 µm eye-safe laser.
References: IEC 60825-1 ||

|| Requirement No:EOIR-014 || Requirement: The EOIR shall compute target geo-coordinates from sensor LoS + platform position (##NAV.NAV-020) + ranging data with horizontal accuracy ≤ 10 m CEP at ranges up to 15 km.
Satisfies: ##NAV.NAV-020 ||

|| Requirement No:EOIR-015 || Requirement: The EOIR shall provide a forward-hemisphere video feed for DAA applications on Nimbus-C3 per ##RADAR.RADAR-017, with 30 Hz frame rate minimum and < 100 ms glass-to-glass latency to the DAA processor.
Satisfies: ##RADAR.RADAR-017
References: DO-365B ||

|| Requirement No:EOIR-016 || Requirement: The EOIR shall apply image stabilisation, edge enhancement, and local contrast enhancement as selectable processing options, commanded via ##PLD.PLD-010. ||

|| Requirement No:EOIR-017 || Requirement: The EOIR shall output video with STANAG 4609 KLV metadata embedded, including platform position, attitude, sensor LoS, FoV, frame timestamp (UTC), and sensor health at 25+ Hz.
References: STANAG 4609 ||

|| Requirement No:EOIR-018 || Requirement: The EOIR shall detect LoS obscuration (image intensity < 10 % dynamic range sustained for > 2 s) and notify operator per ##HMI.HMI-162 with OBSCURATION_SUSPECT flag. ||

|| Requirement No:EOIR-019 || Requirement: The EOIR shall support auto-focus and manual-focus commands with focus convergence time ≤ 2 s across the full focal range. ||

|| Requirement No:EOIR-020 || Requirement: The EOIR gimbal shall accept pointing commands at up to 10 Hz from PMC (##PLD.PLD-010), with slew rates up to 60°/s (azimuth) and 30°/s (elevation), arriving at commanded position within ±0.05° in ≤ 2 s.
Satisfies: ##PLD.PLD-010 ||

|| Requirement No:EOIR-021 || Requirement: The EOIR shall operate across DO-160G §4 Category A2 environmental envelope and DO-160G §8 Category U vibration, with IR-cooler operation sustained from -40 °C to +65 °C.
References: DO-160G-4, DO-160G-8 ||

|| Requirement No:EOIR-022 || Requirement: The EOIR shall consume nominal 28 V DC per MIL-STD-704F with typical steady-state power 90 W (Stratos-7 full gimbal), 60 W (AeroLynx-X2), 25 W (Skyrunner-T1), 20 W (Nimbus-C3 DAA-only). ||

|| Requirement No:EOIR-023 || Requirement: The EOIR shall publish EOIR_STATUS_MSG at 2 Hz with mode, temperature, NUC status, focus state, gimbal position, fault-word. ||

|| Requirement No:EOIR-024 || Requirement: The EOIR shall implement self-test (BIT) reporting to ##BIT.BIT-030, with PBIT sequence ≤ 120 s on power-on including IR cooler stabilisation, and CBIT at 0.1 Hz during operation.
Satisfies: ##BIT.BIT-030 ||

Header: Interface
|| Requirement No:EOIR-025 || Requirement: The EOIR shall interface with the PMC via the payload bus (##PLD.PLD-031) using STANAG 4586 service-oriented messages for control and status, and RTP/RTSP for video streaming.
References: STANAG 4586 ||

|| Requirement No:EOIR-026 || Requirement: The EOIR shall format EOIR_STATUS_MSG per the table below.
Table Type: MESSAGE
Table Name or Description: EOIR_Status_Msg
Table: EOIR_Status_Msg
|Field|Type|Range|
--------------------------------------------------
|mode|uint8|enum|
--------------------------------------------------
|az,el|float32 ×2|-180 to +180 deg, -90 to +90 deg|
--------------------------------------------------
|fov_eo,fov_ir|float32 ×2|narrow-to-wide deg|
--------------------------------------------------
|ir_cooler_temp|float32|60 to 85 K (if cryo)|
--------------------------------------------------
|focus_state|uint8|enum {AUTO, MAN, CONVERGING, FAILED}|
--------------------------------------------------
|nuc_state|uint8|enum {OK, IN_PROGRESS, REQUIRED}|
--------------------------------------------------
|track_active|uint8|0 or 1|
--------------------------------------------------
|lrf_ranging|uint8|0 or 1|
--------------------------------------------------
|ltd_active|uint8|0 or 1|
--------------------------------------------------
|fault_word|uint32|bitmask|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:EOIR-027 || Requirement: The EOIR shall comply with laser-safety eye-exposure constraints per the LRF_LTD_Limits table.
Table Type: MESSAGE
Table Name or Description: LRF_LTD_Limits
Table: LRF_LTD_Limits
|Device|Wavelength|Pulse Energy|PRF|Eye-safety Class|
--------------------------------------------------
|LRF (STR7)|1.55 µm|≤ 10 mJ|max 10 Hz|Class 1 at 1.55 µm|
--------------------------------------------------
|LRF (ALX2)|1.55 µm|≤ 5 mJ|max 10 Hz|Class 1 at 1.55 µm|
--------------------------------------------------
|LTD (STR7)|1.064 µm|≤ 80 mJ|5-20 Hz|Class 4 (hazardous), interlock required|
--------------------------------------------------
|LTD (ALX2, optional)|1.064 µm|≤ 50 mJ|5-20 Hz|Class 4, interlock required|
--------------------------------------------------
References: IEC 60825-1 ||

Header: Test
|| Requirement No:EOIR-028 || Requirement: LoS stabilisation (EOIR-010) shall be verified by shaker-table test per DO-160G §8 Category U with the gimbal installed, measuring residual LoS jitter with a calibrated optical reference and demonstrating ≤ 15 µrad RMS at cruise vibration level.
Verifies: EOIR-010
References: DO-160G-8 ||

|| Requirement No:EOIR-029 || Requirement: Geolocation accuracy (EOIR-014) shall be verified by flight-test with known ground targets at ranges 1 km, 5 km, and 10 km, measuring reported vs truth with CEP ≤ 10 m at ≤ 15 km range.
Verifies: EOIR-014 ||

|| Requirement No:EOIR-030 || Requirement: Laser-safety interlock (EOIR-006, PLD-018) shall be verified by attempting LTD activation on ground and below configured altitude, confirming 100 % inhibit and operator notification.
Verifies: EOIR-006
References: IEC 60825-1 ||
