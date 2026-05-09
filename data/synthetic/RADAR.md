#Requirement: REQ-RADAR
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: RADAR
BASELINE: v1.3.0
ABSOLUTE PATH: /AeroSys/Common/RADAR

Header: PURPOSE
|| Requirement No:RADAR-001 || Requirement: This document specifies the Radar Altimeter and Weather Radar functional, performance, and interface requirements applicable to Stratos-7, AeroLynx-X2, and Nimbus-C3. The Skyrunner-T1 does not host radar altimetry or weather radar due to size, weight, and power constraints. The Radar Altimeter software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and DAL-B on Nimbus-C3. ||

Header: SCOPE
|| Requirement No:RADAR-002 || Requirement: This module covers two independent radar subsystems: (a) Radar Altimeter operating in the 4.2 - 4.4 GHz band per ICAO Annex 10 Volume I, providing AGL altitude measurement for approach and autoland, and (b) Weather Radar (Stratos-7 and Nimbus-C3 only) operating in X-band, providing weather-cell mapping and turbulence indication. It excludes the Detect-and-Avoid sensor suite (covered by ##EOIR.EOIR-015 and ##SAR.SAR-020). ||

Header: REFERENCES
|| Requirement No:RADAR-003 || Requirement: The governing references are: RTCA DO-155 (Radio Altimeter MOPS), ICAO Annex 10 Vol I, RTCA DO-178C, RTCA DO-254, RTCA DO-160G, ARP4754A, RTCA DO-365B (DAA for UAS), ITU-R M.2059 (Radio Altimeter emission masks). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|RA|Radar Altimeter|
--------------------------------------------------
|WXR|Weather Radar|
--------------------------------------------------
|AGL|Above Ground Level|
--------------------------------------------------
|FMCW|Frequency-Modulated Continuous Wave|
--------------------------------------------------
|PRF|Pulse Repetition Frequency|
--------------------------------------------------
|dBZ|Reflectivity (logarithmic)|
--------------------------------------------------
|DAA|Detect and Avoid|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:RADAR-004 || Requirement: The Radar Altimeter shall operate in the 4.2 - 4.4 GHz band using FMCW modulation per DO-155, with transmit power ≤ 500 mW and compliant spectrum mask per ITU-R M.2059.
References: DO-155, ITU-R M.2059 ||

|| Requirement No:RADAR-005 || Requirement: The Radar Altimeter shall measure AGL altitude in the range 0 ft to 5 000 ft with accuracy ±(2 ft + 2 % of measured height) and update rate ≥ 20 Hz over smooth terrain with reflectivity ≥ -20 dB.
Satisfies: ##NAV.NAV-014
References: DO-155 ||

|| Requirement No:RADAR-006 || Requirement: The Radar Altimeter shall declare measurement VALID when signal-to-noise ratio exceeds 10 dB and track has been maintained for at least 3 consecutive update cycles; measurement shall be flagged INVALID within 150 ms of track loss. ||

|| Requirement No:RADAR-007 || Requirement: The Radar Altimeter shall support banked-flight operation up to 30° roll and 15° pitch without loss of track over smooth terrain; beyond these angles, an OUT_OF_COVERAGE flag shall be asserted. ||

|| Requirement No:RADAR-008 || Requirement: The Radar Altimeter shall publish RADAR_ALT_MSG at 20 Hz to the NAV Fusion function per ##NAV.NAV-030 and to the FCC for autoland flare initiation per ##AUTO.AUTO-029.
Satisfies: ##NAV.NAV-030, ##AUTO.AUTO-029 ||

|| Requirement No:RADAR-009 || Requirement: The Radar Altimeter shall support DO-160G §20 Category Y environmental EMC and shall coexist without mutual interference with the CDL at C-band (##CDL.CDL-005) and any onboard GPS receiver (##GPS.GPS-009).
References: DO-160G-20 ||

|| Requirement No:RADAR-010 || Requirement: On Stratos-7 and Nimbus-C3, the Weather Radar shall operate in X-band (9.3 - 9.5 GHz) with transmit peak power ≤ 100 W and tunable PRF 1 - 4 kHz.
References: ARINC 708A ||

|| Requirement No:RADAR-011 || Requirement: The Weather Radar shall scan azimuth ±60° with tilt control ±15°, producing a reflectivity map with 0 to 50 dBZ range and range resolution ≤ 300 m. ||

|| Requirement No:RADAR-012 || Requirement: The Weather Radar shall support turbulence mode using pulse-pair processing or equivalent Doppler-spectrum-width estimator, flagging cells with spectral width > 4 m/s as turbulence-suspect. ||

|| Requirement No:RADAR-013 || Requirement: The Weather Radar shall publish weather-cell summary (bearing, range, reflectivity, turbulence flag) to the GCS at 1 Hz for operator display per ##GCS.GCS-050 and to the FMS for route-advisory computation per ##FMS.FMS-019. ||

|| Requirement No:RADAR-014 || Requirement: On loss of weather radar data (TX failure, scan servo failure, or data path error) for > 2 s, the system shall flag WXR_FAIL to the operator per ##HMI.HMI-095 and continue all other flight operations unaffected. ||

Header: Modes
|| Requirement No:RADAR-015 || Requirement: The Radar Altimeter shall support the following modes:
    a) OFF
    b) STANDBY (warm, no transmit)
    c) TRACK (nominal)
    d) DEGRADED (track with reduced SNR)
    e) FAULT
Automatic transition from STANDBY to TRACK shall occur at aircraft-height transition through 5 000 ft AGL (detected via GPS-baro cross-reference). ||

|| Requirement No:RADAR-016 || Requirement: On Stratos-7 and Nimbus-C3, the Weather Radar shall support modes:
    a) OFF
    b) STANDBY
    c) WXR (weather mapping)
    d) TURB (turbulence detection)
    e) BIT
    f) FAULT ||

|| Requirement No:RADAR-017 || Requirement: The Radar Altimeter shall support DAA resolution advisory integration via coupling with the EOIR/DAA computer (##EOIR.EOIR-018), providing AGL validation for terrain-avoidance resolution manoeuvres per ##AUTO.AUTO-020.
Satisfies: ##AUTO.AUTO-020
References: DO-365B ||

Header: Interface
|| Requirement No:RADAR-018 || Requirement: On Stratos-7 and AeroLynx-X2, the Radar Altimeter shall publish RADAR_ALT_MSG on MIL-STD-1553B at 20 Hz, with the RA as Remote Terminal 9. On Nimbus-C3, the RA shall use ARINC 429 label 164 (radio height) at 20 Hz.
References: MIL-STD-1553B, ARINC 429 ||

|| Requirement No:RADAR-019 || Requirement: The Weather Radar (Stratos-7 and Nimbus-C3) shall publish WXR_MAP via ARINC 708A serial-bus digital weather format at 1 frame/s, with 128 azimuth bins × 256 range bins per frame.
References: ARINC 708A ||

|| Requirement No:RADAR-020 || Requirement: The Radar Altimeter shall consume nominal 28 V DC per MIL-STD-704F, drawing ≤ 30 W steady-state including antenna heating if fitted, with 50 ms power-interruption ride-through per DO-160G §16 Category Z.
References: DO-160G-16 ||

|| Requirement No:RADAR-021 || Requirement: The Radar Altimeter shall format the RADAR_ALT_MSG per the table below.
Table Type: MESSAGE
Table Name or Description: Radar_Alt_Msg
Table: Radar_Alt_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|alt_agl|float32|0 to 5000 ft|0.1 ft|
--------------------------------------------------
|rate_agl|float32|-4000 to +4000 ft/min|1 ft/min|
--------------------------------------------------
|snr|float32|0 to 50 dB|0.1 dB|
--------------------------------------------------
|valid|uint8|0 or 1|bit|
--------------------------------------------------
|out_of_coverage|uint8|0 or 1|bit|
--------------------------------------------------
|mode|uint8|enum {OFF,STBY,TRACK,DEGRADED,FAULT}|integer|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:RADAR-022 || Requirement: The Radar Altimeter shall apply accuracy allocation per the RA_Accuracy table as a function of AGL altitude.
Table Type: MESSAGE
Table Name or Description: RA_Accuracy
Table: RA_Accuracy
|AGL Range|Accuracy (1-sigma)|Used In|
--------------------------------------------------
|0 - 100 ft|±1 ft|autoland flare, touchdown detection|
--------------------------------------------------
|100 - 500 ft|±(2 ft + 1 %)|approach|
--------------------------------------------------
|500 - 2500 ft|±(2 ft + 2 %)|low-level ingress, NAV aiding|
--------------------------------------------------
|2500 - 5000 ft|±(2 ft + 2 %), coverage-limited|supplementary AGL cue|
--------------------------------------------------
References: DO-155 ||

Header: Test
|| Requirement No:RADAR-023 || Requirement: AGL accuracy (RADAR-005) shall be verified by flight-test over smooth-water and over calibrated ground tracks at AGL altitudes 50, 200, 1 000, and 3 000 ft, comparing RA output to laser-altimeter ground truth.
Verifies: RADAR-005
References: DO-155 ||

|| Requirement No:RADAR-024 || Requirement: EMC coexistence (RADAR-009) shall be verified by DO-160G §20 Category Y test with CDL and GPS transmitters active, demonstrating no degradation of RA track or PVT output.
Verifies: RADAR-009
References: DO-160G-20 ||

|| Requirement No:RADAR-025 || Requirement: DAA coupling (RADAR-017) shall be verified by HIL injection of intruder profiles from the EOIR/DAA path, demonstrating timely RA AGL cross-check and appropriate resolution-advisory arming to AUTO per ##AUTO.AUTO-020.
Verifies: RADAR-017
Satisfies: ##AUTO.AUTO-020
References: DO-365B ||
