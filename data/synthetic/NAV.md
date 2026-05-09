#Requirement: REQ-NAV
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: NAV
BASELINE: v1.7.0
ABSOLUTE PATH: /AeroSys/Common/NAV

Header: PURPOSE
|| Requirement No:NAV-001 || Requirement: This document specifies the Navigation Integration and Fusion requirements for the AeroSys Dynamics common navigation core, applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3. The NAV Fusion software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and at DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:NAV-002 || Requirement: This module covers the fusion and arbitration of navigation inputs from the INS (##INS.INS-020), GPS (##GPS.GPS-030), Air Data System (##ADS.ADS-020), and Radar Altimeter (##RADAR.RADAR-005), producing the unified aircraft-state output used by FCC, FMS, AUTO, and GCS consumers. It excludes the primary sensor LRUs and the Navigation Database (##FMS.FMS-006). ||

|| Requirement No:NAV-003 || Requirement: The NAV Fusion function is hosted on the FCC hardware as an independent software partition with ARINC 653 time/space separation from the control-law partitions on Stratos-7 and AeroLynx-X2.
References: ARINC 653, DO-297 ||

Header: REFERENCES
|| Requirement No:NAV-004 || Requirement: The governing references are: RTCA DO-178C, SAE ARP4754A, SAE ARP4761, RTCA DO-283B (RNP), RTCA DO-236C, RTCA DO-229F, MIL-STD-1553B, ARINC 429. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|NAV|Navigation Integration & Fusion|
--------------------------------------------------
|FDI|Fault Detection and Isolation|
--------------------------------------------------
|AHRS|Attitude and Heading Reference System|
--------------------------------------------------
|TSE|Total System Error|
--------------------------------------------------
|NSE|Navigation System Error|
--------------------------------------------------
|PVT|Position, Velocity, Time|
--------------------------------------------------
|DOP|Dilution of Precision|
--------------------------------------------------
|RAIM|Receiver Autonomous Integrity Monitoring|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:NAV-005 || Requirement: The NAV Fusion function shall support the following modes:
    a) INIT
    b) HYBRID (INS + GPS + baro all valid)
    c) INS_ONLY (GPS invalid)
    d) AHRS (INS position invalid, GPS used for velocity only)
    e) BARO_ONLY (only baro altitude available for vertical reference)
    f) FAULT ||

|| Requirement No:NAV-006 || Requirement: While in HYBRID, the NAV Fusion function shall publish position, velocity, and attitude consistent with the RNP containment targets of ##FMS.FMS-012, and maintain NSE ≤ 0.1 nmi horizontal (95 %) enroute.
Satisfies: ##FMS.FMS-012 ||

|| Requirement No:NAV-007 || Requirement: On loss of GPS aiding lasting more than 60 s, the NAV Fusion function shall transition from HYBRID to INS_ONLY within 200 ms, and shall annunciate NAV_DEGRADED to the operator per ##HMI.HMI-075.
Refines: ##INS.INS-013 ||

|| Requirement No:NAV-008 || Requirement: When the INS reports POS_VALID=0 for more than 500 ms but the GPS fix remains valid, the NAV Fusion function shall transition to AHRS mode, using GPS for position and an attitude-only Kalman filter on the IMU raw rates for attitude. ||

|| Requirement No:NAV-009 || Requirement: While in BARO_ONLY mode, the NAV Fusion function shall publish only vertical state (pressure altitude, vertical velocity from baro rate) with lateral state invalidated, and shall command AUTO to RTB per ##AUTO.AUTO-022.
Satisfies: ##AUTO.AUTO-022 ||

|| Requirement No:NAV-010 || Requirement: The NAV Fusion function shall publish the aircraft-state bundle (position, velocity, attitude, quality indicators) at 50 Hz with transport latency not exceeding 15 ms from the underlying sensor measurement.
References: DO-178C-6.3.4 ||

Header: General
|| Requirement No:NAV-011 || Requirement: The NAV Fusion function shall operate a federated 21-state Kalman filter receiving INS error states, GPS position/velocity residuals, and baro residuals at 10 Hz.
Derives From: ##INS.INS-019 ||

|| Requirement No:NAV-012 || Requirement: The NAV Fusion function shall maintain a running Total System Error (TSE) estimate at 10 Hz composed of Navigation System Error (NSE) and Flight Technical Error (FTE from ##FCC.FCC-024), and shall publish TSE to the FMS for RNP compliance monitoring.
Satisfies: ##FMS.FMS-012 ||

|| Requirement No:NAV-013 || Requirement: The NAV Fusion function shall arbitrate between dual INS LRUs (platforms with dual configuration) using a cross-check with residual threshold 2× the published INS 1-sigma per ##INS.INS-021; on disagreement sustained > 200 ms, it shall declare the minority LRU FAULTED and route output from the majority. ||

|| Requirement No:NAV-014 || Requirement: The NAV Fusion function shall fuse radar-altimeter measurements (##RADAR.RADAR-005) below 2 500 ft AGL into the vertical channel as supplementary input, with weighting reduced above 2 500 ft AGL and zeroed above 5 000 ft AGL.
Satisfies: ##RADAR.RADAR-005 ||

|| Requirement No:NAV-015 || Requirement: The NAV Fusion function shall provide a reversionary AHRS output derived from GPS-aided low-cost IMU integration, available when the primary INS fails, for use by the FCC per ##FCC.FCC-017.
Satisfies: ##FCC.FCC-017 ||

|| Requirement No:NAV-016 || Requirement: The NAV Fusion function shall detect inconsistent altimetry (baro altitude and GPS altitude disagreement > 400 ft for > 10 s after lapse-rate correction), flag ALT_SUSPECT, and preserve baro as the primary vertical reference in the control loop. ||

|| Requirement No:NAV-017 || Requirement: The NAV Fusion function shall detect inconsistent airspeed (TAS from ADS and groundspeed-minus-wind from GPS disagreement > 15 kt sustained for > 5 s), flag VEL_SUSPECT, and notify the operator per ##HMI.HMI-082. ||

|| Requirement No:NAV-018 || Requirement: The NAV Fusion function shall compute wind-vector estimate (speed and direction) from the difference of inertial groundspeed vector and true-airspeed vector, updating at 1 Hz with 1-sigma accuracy ≤ 3 kt magnitude and ≤ 5° direction in steady flight. ||

|| Requirement No:NAV-019 || Requirement: The NAV Fusion function shall compute and publish ground track, ground speed, and drift angle at 10 Hz using fused position and velocity outputs. ||

|| Requirement No:NAV-020 || Requirement: The NAV Fusion function shall publish position in WGS-84 geodetic coordinates at 50 Hz and shall maintain an MGRS-grid position representation synchronised at 1 Hz for ground-operator display per ##HMI.HMI-085. ||

|| Requirement No:NAV-021 || Requirement: The NAV Fusion function shall provide a quality-of-service (QoS) score in the range 0 to 100 at 2 Hz, combining INS QoS (##INS.INS-038), GPS DOP (##GPS.GPS-020), and baro validity, for operator display per ##HMI.HMI-087. ||

|| Requirement No:NAV-022 || Requirement: The NAV Fusion function shall handle GPS-week rollover and leap-second insertions without loss of NAV output, interpolating UTC time across the event. ||

|| Requirement No:NAV-023 || Requirement: The NAV Fusion function shall compute magnetic variation using the World Magnetic Model (WMM-2025 or later) and apply it to all heading outputs where magnetic heading is required by consumer modules. ||

|| Requirement No:NAV-024 || Requirement: The NAV Fusion function shall detect EKF filter divergence (normalised innovation sum-of-squares exceeding 9 sigma over 10 s) within 1 s of onset, reset the filter with current best estimates, and log the divergence event to ##FDR.FDR-024.
Satisfies: ##FDR.FDR-024 ||

|| Requirement No:NAV-025 || Requirement: The NAV Fusion function shall store and reload the last-known-position and last-known-state at graceful shutdown, to accelerate warm-start on next power-up per ##GPS.GPS-005. ||

|| Requirement No:NAV-026 || Requirement: The NAV Fusion function shall sustain uninterrupted output through the 50 ms primary-power interruption profile per DO-160G §16 Category Z, using hold-up energy from ##PWR.PWR-018.
References: DO-160G-16, MIL-STD-704F ||

|| Requirement No:NAV-027 || Requirement: The NAV Fusion function shall expose a time-synchronisation service at 1 Hz with ≤ 10 µs accuracy to all consumer modules via the avionics bus, derived from GPS time when valid (##GPS.GPS-010) and from the on-board OCXO otherwise. ||

|| Requirement No:NAV-028 || Requirement: The NAV Fusion function shall reject any security-relevant input (GPS spoof indicator per ##GPS.GPS-022, INS spoof indicator per ##INS.INS-028) by deweighting the corresponding measurement in the Kalman filter and notifying the security monitor per ##SEC.SEC-028. ||

Header: Interface
|| Requirement No:NAV-029 || Requirement: The NAV Fusion function shall publish NAV_STATE_MSG at 50 Hz on the primary avionics bus (MIL-STD-1553B on STR7/ALX2, ARINC 429 at 100 kbps on SKT1/NBC3), per the NAV_State_Msg table (NAV-031).
References: MIL-STD-1553B, ARINC 429 ||

|| Requirement No:NAV-030 || Requirement: The NAV Fusion function shall consume INS_STATE_MSG at 200 Hz (##INS.INS-020), GPS_PVT_MSG at 10 Hz (##GPS.GPS-030), ADS_MSG at 20 Hz (##ADS.ADS-020), and RADAR_ALT_MSG at 20 Hz (##RADAR.RADAR-008) where available.
Satisfies: ##INS.INS-020, ##GPS.GPS-030, ##ADS.ADS-020 ||

|| Requirement No:NAV-031 || Requirement: The NAV Fusion function shall format the NAV_STATE_MSG per the following table.
Table Type: MESSAGE
Table Name or Description: NAV_State_Msg
Table: NAV_State_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|lat,lon|float64 ×2|-90 to +90, -180 to +180|1e-9 deg|
--------------------------------------------------
|alt_pressure|float32|-1000 to +55000 ft|0.01 ft|
--------------------------------------------------
|alt_geodetic|float32|-1000 to +55000 ft|0.01 ft|
--------------------------------------------------
|alt_agl|float32|0 to 5000 ft|0.1 ft|
--------------------------------------------------
|vel_ned|float32 ×3|-1500 to +1500 kt|0.001 kt|
--------------------------------------------------
|track,gs|float32 ×2|0-360 deg, 0-1500 kt|0.01 deg, 0.01 kt|
--------------------------------------------------
|wind_speed_dir|float32 ×2|0-300 kt, 0-360 deg|0.1 kt, 0.1 deg|
--------------------------------------------------
|quat_wxyz|float32 ×4|-1 to +1|1e-6|
--------------------------------------------------
|tse_horiz,tse_vert|float32 ×2|0 to 10 nmi|0.001 nmi|
--------------------------------------------------
|qos|uint8|0 to 100|integer|
--------------------------------------------------
|mode|uint8|enum {INIT,HYBRID,INS_ONLY,AHRS,BARO_ONLY,FAULT}|integer|
--------------------------------------------------
|valid_flags|uint16|bitmask|bit|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:NAV-032 || Requirement: The NAV Fusion function shall enforce the measurement-arbitration rules in the Sensor_Arbitration table.
Table Type: MESSAGE
Table Name or Description: Sensor_Arbitration
Table: Sensor_Arbitration
|Sensor|Valid Criterion|Fallback|
--------------------------------------------------
|INS primary|VALID=1, attitude residual < 2 sigma|INS secondary (dual configs) or AHRS|
--------------------------------------------------
|GPS|fix_type≥3D, RAIM_OK=1, HDOP<6|INS position propagation|
--------------------------------------------------
|Baro|ADS VALID=1, rate<6000 ft/min|GPS altitude with WMM geoid|
--------------------------------------------------
|Radar altimeter|VALID=1, AGL<5000 ft|disable radar-alt fusion|
-------------------------------------------------- ||

|| Requirement No:NAV-033 || Requirement: The NAV Fusion function shall apply the Innovation_Thresholds table to each incoming measurement and reject measurements exceeding the hard threshold.
Table Type: MESSAGE
Table Name or Description: Innovation_Thresholds
Table: Innovation_Thresholds
|Measurement|Soft (deweight)|Hard (reject)|Persistent (fault)|
--------------------------------------------------
|GPS position|3 sigma|6 sigma|6 sigma > 3 samples|
--------------------------------------------------
|GPS velocity|3 sigma|6 sigma|6 sigma > 3 samples|
--------------------------------------------------
|Baro altitude|2 sigma|4 sigma|4 sigma > 10 samples|
--------------------------------------------------
|Radar AGL|2 sigma|5 sigma|5 sigma > 5 samples|
-------------------------------------------------- ||

Header: Test
|| Requirement No:NAV-034 || Requirement: The NSE performance target (NAV-006) shall be verified by flight-test of 20 missions per platform with GPS/SBAS available, demonstrating horizontal NSE ≤ 0.1 nmi at the 95 % level over each mission.
Verifies: NAV-006
References: DO-283B ||

|| Requirement No:NAV-035 || Requirement: Mode transition HYBRID→INS_ONLY (NAV-007) shall be verified by HIL injection of GPS unavailability starting at random phase and persisting 30, 60, 120, and 300 s, demonstrating transition within 200 ms of the 60 s threshold.
Verifies: NAV-007 ||

|| Requirement No:NAV-036 || Requirement: Filter-divergence detection (NAV-024) shall be verified by fault-injection of large-magnitude pseudo-measurements (50 sigma offset) persisting for 5 s, demonstrating filter reset within 1 s of divergence criterion.
Verifies: NAV-024 ||

|| Requirement No:STR7-NAV-001 || Requirement: On Stratos-7, the NAV Fusion function shall fuse dual-antenna GPS heading (##STR7-GPS-001) to improve static-ground heading determination to ≤ 0.2° 1-sigma.
Satisfies: ##STR7-GPS-001 ||

|| Requirement No:ALX2-NAV-001 || Requirement: On AeroLynx-X2, the NAV Fusion function shall apply enhanced multipath mitigation by weighting GPS vertical-channel updates by 0.3× nominal when radar altimeter is valid, to compensate for sea-surface multipath in littoral operations. ||

|| Requirement No:SKT1-NAV-001 || Requirement: On Skyrunner-T1, the NAV Fusion function shall operate with the simplified commercial-grade MEMS INS (##SKT1-INS-001) and shall maintain HYBRID mode position accuracy ≤ 25 m CEP.
Refines: NAV-006 ||

|| Requirement No:NBC3-NAV-001 || Requirement: On Nimbus-C3, the NAV Fusion function shall monitor conformance to the filed 4D trajectory per ##FMS.FMS-020, publishing deviations to the FCC for conformance alerting per ##NBC3-FCC-004.
Satisfies: ##NBC3-FCC-004 ||
