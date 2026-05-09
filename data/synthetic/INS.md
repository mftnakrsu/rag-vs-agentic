#Requirement: REQ-INS
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: INS
BASELINE: v1.9.2
ABSOLUTE PATH: /AeroSys/Common/INS

Header: PURPOSE
|| Requirement No:INS-001 || Requirement: This document specifies the Inertial Navigation System (INS) functional, performance, interface, and safety requirements for the AeroSys Dynamics common INS LRU, applicable to the Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3 platforms. The INS software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and at DAL-B on Skyrunner-T1 and Nimbus-C3. The INS IMU hardware shall be developed at DO-254 Level A or Level B per the same platform mapping. ||

Header: SCOPE
|| Requirement No:INS-002 || Requirement: This module covers the INS LRU functions: sensor sampling, strapdown mechanisation, coarse and fine alignment, in-flight alignment, Kalman filter integration with GPS aiding (##GPS.GPS-001) and baro-altitude aiding (##ADS.ADS-001), state output publication, and BIT. It excludes GNSS receiver signal processing (##GPS.GPS-005), air-data pressure transducer hardware (##ADS.ADS-003), and downstream navigation fusion beyond the INS LRU (##NAV.NAV-001). ||

|| Requirement No:INS-003 || Requirement: The INS LRU shall be a single LRU on Skyrunner-T1 and a dual-redundant pair of INS LRUs on Stratos-7, AeroLynx-X2, and Nimbus-C3, with independent power feeds per ##PWR.PWR-012.
Derives From: ARP4761-FHA-NAV-01 ||

Header: REFERENCES
|| Requirement No:INS-004 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, RTCA DO-160G, MIL-STD-1553B, ARINC 429, IEEE Std 952-2020 (gyro test), IEEE Std 1293-2018 (accelerometer test), and STANAG 4572 (inertial sensor classification). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|INS|Inertial Navigation System|
--------------------------------------------------
|IMU|Inertial Measurement Unit|
--------------------------------------------------
|RLG|Ring Laser Gyroscope|
--------------------------------------------------
|FOG|Fibre-Optic Gyroscope|
--------------------------------------------------
|MEMS|Micro-Electro-Mechanical Systems|
--------------------------------------------------
|ECEF|Earth-Centred, Earth-Fixed frame|
--------------------------------------------------
|NED|North-East-Down frame|
--------------------------------------------------
|EKF|Extended Kalman Filter|
--------------------------------------------------
|AHRS|Attitude and Heading Reference System|
--------------------------------------------------
|ZUPT|Zero Velocity Update|
--------------------------------------------------
|TTR|Time To Ready|
--------------------------------------------------
|CEP|Circular Error Probable|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:INS-005 || Requirement: The INS shall support the following operational modes:
    a) OFF
    b) STANDBY
    c) COARSE_ALIGN
    d) FINE_ALIGN
    e) NAV
    f) IN_FLIGHT_ALIGN
    g) DEGRADED (inertial-only, no aiding)
    h) FAULT
Mode transitions shall be governed by the INS_Mode_Transitions table (INS-040).
References: ARP4754A-5.3 ||

|| Requirement No:INS-006 || Requirement: When transitioning from STANDBY to COARSE_ALIGN, the INS shall verify that aircraft attitude rates are below 0.5 °/s on all axes sustained for 10 s (WoW asserted, aircraft static), rejecting the transition otherwise and annunciating MOTION_DETECTED to the operator per ##HMI.HMI-070. ||

|| Requirement No:INS-007 || Requirement: While in COARSE_ALIGN, the INS shall compute an initial attitude estimate using measured gravity and Earth-rate vectors, completing the coarse alignment within 60 s at any latitude between 70° S and 70° N.
References: IEEE Std 952-2020 ||

|| Requirement No:INS-008 || Requirement: While in FINE_ALIGN, the INS shall refine the attitude and heading estimate via gyrocompassing, achieving a heading 1-sigma error not exceeding 0.1° / cos(latitude) for latitudes up to 70°, within 8 min of fine-align commencement.
Derives From: STANAG 4572 ||

|| Requirement No:INS-009 || Requirement: The INS shall automatically transition from FINE_ALIGN to NAV when heading uncertainty falls below 0.3° / cos(latitude) for 30 s, provided GPS fix has been available for at least 60 s during fine-align.
Satisfies: ##GPS.GPS-012 ||

|| Requirement No:INS-010 || Requirement: If the aircraft begins motion (accelerometer magnitude deviation > 0.05 g from 1 g gravity, or gyro magnitude > 2 °/s) before fine-align completes, the INS shall abandon FINE_ALIGN and transition to IN_FLIGHT_ALIGN within 100 ms.
Refines: INS-008 ||

|| Requirement No:INS-011 || Requirement: While in IN_FLIGHT_ALIGN, the INS shall acquire heading and position convergence using GPS velocity aiding (##GPS.GPS-013) and dynamic-manoeuvre observability, achieving the NAV transition criterion within 15 min under nominal aircraft manoeuvre profile (minimum 2 heading changes > 45° within the interval). ||

|| Requirement No:INS-012 || Requirement: While in NAV, the INS shall publish position, velocity, attitude, body rates, and body accelerations at 200 Hz to the FCC (##FCC.FCC-016) and at 50 Hz to the NAV fusion function (##NAV.NAV-010). ||

|| Requirement No:INS-013 || Requirement: On loss of GPS aiding for > 60 s, the INS shall transition to DEGRADED mode, continue to publish inertial-only navigation, and annunciate NAV_DEGRADED to the operator per ##HMI.HMI-075.
Satisfies: ##HMI.HMI-075 ||

|| Requirement No:INS-014 || Requirement: While in DEGRADED, the INS shall accept barometric altitude aiding from ##ADS.ADS-015 to stabilise the vertical channel, clamping the vertical-velocity error growth to below 2 ft/s 1-sigma over 10 min.
Derives From: INS-013 ||

|| Requirement No:INS-015 || Requirement: On any IMU BIT failure (gyro bias drift > 10× spec, accelerometer bias drift > 10× spec, or sensor saturation > 100 ms), the INS shall transition to FAULT mode within 50 ms, deassert the VALID flag on all output messages, and log the fault to ##FDR.FDR-018.
Satisfies: ##BIT.BIT-010 ||

Header: General
|| Requirement No:INS-016 || Requirement: The INS shall sample each IMU axis (3 gyros, 3 accelerometers) at no less than 2 000 Hz with 24-bit ADC resolution, and downsample to the 200 Hz publication rate using a zero-mean anti-aliasing filter.
References: IEEE Std 952-2020 ||

|| Requirement No:INS-017 || Requirement: The INS shall execute the strapdown mechanisation in the ECEF frame with quaternion attitude representation, rotating to NED for publication, at a computation rate no lower than 400 Hz. ||

|| Requirement No:INS-018 || Requirement: The INS shall compute and apply real-time temperature compensation on gyro bias, gyro scale factor, accelerometer bias, and accelerometer scale factor, using factory-calibrated polynomials of up to 3rd order across the operating temperature range -40 °C to +70 °C per DO-160G §4 Category A2.
References: DO-160G ||

|| Requirement No:INS-019 || Requirement: The INS shall execute an 18-state Extended Kalman Filter (3 position, 3 velocity, 3 attitude-error, 3 gyro-bias, 3 accelerometer-bias, 3 clock states) at 10 Hz, integrating GPS position and velocity measurements when GPS is valid and baro-altitude measurements at 5 Hz. ||

|| Requirement No:INS-020 || Requirement: The INS shall publish the INS_STATE_MSG containing attitude (quaternion), body rates, body accelerations, position (lat/lon/alt WGS-84), velocity (NED), and validity flags at 200 Hz with end-to-end latency from sensor sample to bus publication not exceeding 5 ms.
Satisfies: ##FCC.FCC-016
References: DO-178C-6.3.4 ||

|| Requirement No:INS-021 || Requirement: Attitude accuracy in NAV mode with GPS aiding shall be 0.05° 1-sigma (roll, pitch) and 0.1° 1-sigma (heading) under steady cruise, degrading to 0.1° (roll, pitch) and 0.3° (heading) under 0.5 g coordinated turns.
Derives From: STANAG 4572 ||

|| Requirement No:INS-022 || Requirement: Position accuracy in NAV mode with GPS aiding shall be ≤ 10 m CEP horizontal and ≤ 15 m 1-sigma vertical when GPS SBAS augmentation is available (##GPS.GPS-015), and ≤ 25 m CEP horizontal otherwise.
Satisfies: ##GPS.GPS-015 ||

|| Requirement No:INS-023 || Requirement: Position drift in DEGRADED mode (no GPS) shall not exceed 1.5 nmi/hr 1-sigma for tactical-grade configurations (Stratos-7, AeroLynx-X2) and 4 nmi/hr 1-sigma for navigation-grade configurations (Skyrunner-T1, Nimbus-C3).
References: STANAG 4572 ||

|| Requirement No:INS-024 || Requirement: The INS shall use an IMU with gyro in-run bias stability ≤ 0.01 °/hr (tactical grade, Stratos-7 and AeroLynx-X2) or ≤ 1 °/hr (commercial grade, Skyrunner-T1 and Nimbus-C3), and accelerometer in-run bias stability ≤ 50 µg (tactical) or ≤ 500 µg (commercial).
References: IEEE Std 952-2020 ||

|| Requirement No:INS-025 || Requirement: The INS shall apply lever-arm compensation from the IMU reference point to the aircraft reference point, with lever-arm coordinates stored as calibration parameters accurate to ±5 mm, and centripetal/tangential-acceleration compensation applied at the 400 Hz mechanisation rate. ||

|| Requirement No:INS-026 || Requirement: The INS shall apply gravity modelling per WGS-84 with normal gravity formula and altitude correction, supplemented by the EGM2008 geoid model (degree/order 360) for ellipsoid-to-MSL altitude conversion. ||

|| Requirement No:INS-027 || Requirement: The INS shall handle the trans-equator and trans-polar regions without singularity, switching to grid-navigation reference above latitude 82° N and below 82° S consistent with ##FMS.FMS-032.
Satisfies: ##FMS.FMS-032 ||

|| Requirement No:INS-028 || Requirement: The INS shall detect GPS spoofing attempts via innovation-sequence monitoring in the EKF, flagging a SPOOF_SUSPECT condition when the normalised position innovation exceeds 6-sigma for 3 consecutive measurements, and rejecting the offending GPS update without transitioning to DEGRADED.
Satisfies: ##SEC.SEC-025
References: DO-326A ||

|| Requirement No:INS-029 || Requirement: On SPOOF_SUSPECT assertion, the INS shall inhibit GPS updates for 60 s, continue on inertial-only, and notify the security monitor per ##SEC.SEC-028. ||

|| Requirement No:INS-030 || Requirement: The INS shall detect GPS multipath or poor-geometry conditions via DOP monitoring (##GPS.GPS-020) and reduce the Kalman gain on GPS measurements when HDOP > 3 or VDOP > 5.
References: DO-283B ||

|| Requirement No:INS-031 || Requirement: The INS shall detect stuck-at-X faults on any IMU axis within 500 ms (constant output for > 500 ms while aircraft motion indicates non-constant true value) and transition to FAULT mode per INS-015. ||

|| Requirement No:INS-032 || Requirement: The INS shall support ZUPT (Zero Velocity Update) when WoW is asserted on both main gear (##LDG.LDG-015) and groundspeed < 0.5 m/s for > 5 s, using the zero-velocity constraint as a Kalman measurement to refine accelerometer biases. ||

|| Requirement No:INS-033 || Requirement: The INS shall support transfer-alignment from a master reference (e.g. primary INS on the same aircraft for dual-redundant platforms) with convergence to within 0.05° attitude 1-sigma in ≤ 60 s of manoeuvring alignment. ||

|| Requirement No:INS-034 || Requirement: The INS shall operate continuously under vibration profile DO-160G §8 Category U (UAV, severe) and mechanical shock DO-160G §7 Category B, without loss of alignment or NAV mode.
References: DO-160G-7, DO-160G-8 ||

|| Requirement No:INS-035 || Requirement: The INS shall operate under DO-160G §16 Category Z power input profile including 50 ms primary-power interruption, drawing hold-up from ##PWR.PWR-018 during the interruption.
Satisfies: ##PWR.PWR-018 ||

|| Requirement No:INS-036 || Requirement: The INS shall sustain continuous NAV mode operation through electromagnetic compatibility environments per DO-160G §20 Category T (transmitter-equipped aircraft) without attitude or position error excursions beyond INS-021 and INS-022.
References: DO-160G-20 ||

|| Requirement No:INS-037 || Requirement: The INS shall provide a time-reference output synchronised to UTC (via GPS time, ##GPS.GPS-010) with accuracy ≤ 1 µs when GPS time is valid, and free-running with OCXO stability ≤ 100 ppb per day when GPS time is unavailable.
Satisfies: ##FCC.FCC-034 ||

|| Requirement No:INS-038 || Requirement: The INS shall maintain a running quality-of-service indicator (QoS) in the range 0 to 100 computed from Kalman-filter covariance, GPS availability, and IMU health, publishing it at 2 Hz for operator display per ##HMI.HMI-080. ||

|| Requirement No:INS-039 || Requirement: The INS shall log a sensor-snapshot (gyro and accelerometer raw samples, corrected outputs, and EKF state) to non-volatile memory at 10 Hz for the most recent 8 h of flight, for post-flight analysis per ##FDR.FDR-020.
Satisfies: ##FDR.FDR-020 ||

|| Requirement No:INS-040 || Requirement: The INS shall enforce mode-transition preconditions per the INS_Mode_Transitions table.
Table Type: MESSAGE
Table Name or Description: INS_Mode_Transitions
Table: INS_Mode_Transitions
|From|To|Precondition|Max Time|
--------------------------------------------------
|OFF|STANDBY|power applied, PBIT PASS|5 s|
--------------------------------------------------
|STANDBY|COARSE_ALIGN|operator ALIGN cmd, WoW=TRUE, rates<0.5 deg/s for 10 s|1 s|
--------------------------------------------------
|COARSE_ALIGN|FINE_ALIGN|coarse-attitude converged|60 s|
--------------------------------------------------
|FINE_ALIGN|NAV|heading 1-sigma < 0.3 deg/cos(lat), GPS valid 60 s|8 min|
--------------------------------------------------
|FINE_ALIGN|IN_FLIGHT_ALIGN|motion detected|100 ms|
--------------------------------------------------
|IN_FLIGHT_ALIGN|NAV|convergence criteria met|15 min|
--------------------------------------------------
|NAV|DEGRADED|GPS unavailable > 60 s|100 ms|
--------------------------------------------------
|DEGRADED|NAV|GPS valid for 30 s, innovations nominal|30 s|
--------------------------------------------------
|any|FAULT|IMU BIT failure|50 ms|
-------------------------------------------------- ||

Header: Interface
|| Requirement No:INS-041 || Requirement: On Stratos-7 and AeroLynx-X2, the INS shall publish INS_STATE_MSG on MIL-STD-1553B Bus A at 200 Hz with the INS as Remote Terminal 3, and shall fail over to Bus B on loss of Bus A per ##FCC.FCC-041.
References: MIL-STD-1553B ||

|| Requirement No:INS-042 || Requirement: On Skyrunner-T1 and Nimbus-C3, the INS shall publish INS_STATE_MSG on ARINC 429 high-speed (100 kbps) with labels 324 (lat), 325 (lon), 361 (altitude), 326 (pitch), 327 (roll), 314 (heading) at 50 Hz, plus labels 362 (body rates) and 363 (body accelerations) at 200 Hz over a dedicated transmit port.
References: ARINC 429 ||

|| Requirement No:INS-043 || Requirement: The INS shall consume GPS measurement messages from ##GPS.GPS-030 at 5 Hz (position+velocity+time) and use the measurements as EKF observations.
Satisfies: ##GPS.GPS-030 ||

|| Requirement No:INS-044 || Requirement: The INS shall consume barometric altitude from ##ADS.ADS-015 at 10 Hz and use it as an EKF observation for vertical-channel stabilisation, with the ADS validity flag as gate.
Satisfies: ##ADS.ADS-015 ||

|| Requirement No:INS-045 || Requirement: The INS shall expose a maintenance interface (RS-422 at 115 200 bps, or optional USB-C service port) for calibration download, log extraction, and firmware update, active only when WoW is asserted and operator authentication is valid per ##SEC.SEC-015. ||

|| Requirement No:INS-046 || Requirement: The INS shall consume nominal 28 V DC input per MIL-STD-704F, draw ≤ 45 W steady-state (tactical-grade) or ≤ 22 W steady-state (commercial-grade), and support the 50 ms power-interruption ride-through per INS-035. ||

|| Requirement No:INS-047 || Requirement: The INS shall format the INS_STATE_MSG per the following structure.
Table Type: MESSAGE
Table Name or Description: INS_State_Msg
Table: INS_State_Msg
|Field|Type|Range|Resolution|Rate|
--------------------------------------------------
|quat_w,x,y,z|float32 ×4|-1 to +1|1e-6|200 Hz|
--------------------------------------------------
|body_rate_pqr|float32 ×3|-400 to +400 deg/s|0.001 deg/s|200 Hz|
--------------------------------------------------
|body_accel_xyz|float32 ×3|-20 to +20 g|0.0001 g|200 Hz|
--------------------------------------------------
|lat,lon|float64 ×2|-90 to +90, -180 to +180 deg|1e-9 deg|200 Hz|
--------------------------------------------------
|altitude_wgs84|float32|-1000 to +60000 ft|0.1 ft|200 Hz|
--------------------------------------------------
|velocity_ned|float32 ×3|-1500 to +1500 kt|0.01 kt|200 Hz|
--------------------------------------------------
|valid_flags|uint16|bitmask per INS-048|bit|200 Hz|
--------------------------------------------------
|mode|uint8|enum {OFF..FAULT}|integer|200 Hz|
--------------------------------------------------
|seq_count|uint16|0 to 65535|integer|200 Hz|
--------------------------------------------------
|crc32|uint32|per DO-254|integer|200 Hz|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:INS-048 || Requirement: The INS shall set the valid_flags bitmask in INS_STATE_MSG per the following semantic.
Table Type: MESSAGE
Table Name or Description: INS_Valid_Flags
Table: INS_Valid_Flags
|Bit|Name|Meaning (1=valid)|
--------------------------------------------------
|0|ATT_VALID|attitude fused, within spec|
--------------------------------------------------
|1|POS_VALID|position fused, within spec|
--------------------------------------------------
|2|VEL_VALID|velocity fused, within spec|
--------------------------------------------------
|3|GPS_AIDED|GPS fix currently aiding EKF|
--------------------------------------------------
|4|BARO_AIDED|baro altitude currently aiding EKF|
--------------------------------------------------
|5|ZUPT_ACTIVE|ZUPT constraint applied|
--------------------------------------------------
|6|ALIGN_OK|align criterion met|
--------------------------------------------------
|7|TIME_VALID|UTC time sync accurate ≤ 1 µs|
--------------------------------------------------
|8|SPOOF_SUSPECT|GPS spoof detection triggered|
--------------------------------------------------
|9|BIT_OK|IMU BIT nominal|
--------------------------------------------------
|10-15|reserved|0|
-------------------------------------------------- ||

|| Requirement No:INS-049 || Requirement: The INS shall apply temperature-compensation coefficients per the Gyro_Accel_Temp_Coeff table, stored in on-board non-volatile memory and rewritable only through the authenticated maintenance interface.
Table Type: MESSAGE
Table Name or Description: Gyro_Accel_Temp_Coeff
Table: Gyro_Accel_Temp_Coeff
|Sensor|Parameter|Range|Units|Polynomial Order|
--------------------------------------------------
|gyro_x,y,z|bias(T)|-40 to +70 °C|deg/hr|3|
--------------------------------------------------
|gyro_x,y,z|scale_factor(T)|-40 to +70 °C|ppm|2|
--------------------------------------------------
|accel_x,y,z|bias(T)|-40 to +70 °C|µg|3|
--------------------------------------------------
|accel_x,y,z|scale_factor(T)|-40 to +70 °C|ppm|2|
-------------------------------------------------- ||

Header: Test
|| Requirement No:INS-050 || Requirement: Fine-alignment heading accuracy (INS-008) shall be verified by laboratory test on a 2-axis turntable at reference latitudes 0°, 30°, 50°, and 70°, with the INS completing fine-align in ≤ 8 min and demonstrating heading 1-sigma ≤ 0.1°/cos(lat) over 50 repetitions per latitude.
Verifies: INS-008
References: IEEE Std 952-2020 ||

|| Requirement No:INS-051 || Requirement: Position drift in DEGRADED mode (INS-023) shall be verified by flight-test with GPS disabled for 1 h, demonstrating RMS position error ≤ 1.5 nmi/hr (tactical) or ≤ 4 nmi/hr (commercial) over 30 representative flights per platform.
Verifies: INS-023 ||

|| Requirement No:INS-052 || Requirement: GPS-spoof detection (INS-028) shall be verified by controlled laboratory spoofing with a calibrated signal generator injecting false position offsets of 100 m, 500 m, and 2 000 m; INS shall assert SPOOF_SUSPECT within 3 measurement updates for offsets ≥ 500 m.
Verifies: INS-028
References: DO-326A ||

|| Requirement No:INS-053 || Requirement: Transport latency (INS-020) shall be verified by end-to-end time-stamp measurement from the IMU sample trigger to the 1553B bus publication, with 10 000 samples collected on the flight-configuration hardware demonstrating ≤ 5 ms at the 99.9 % confidence level.
Verifies: INS-020
References: DO-178C-6.4.4.2 ||

|| Requirement No:INS-054 || Requirement: Vibration robustness (INS-034) shall be verified by DO-160G §8 Category U test at the LRU level with alignment performed before, during, and after vibration exposure, confirming no loss of NAV mode and attitude excursions bounded per INS-021.
Verifies: INS-034
References: DO-160G-8 ||

|| Requirement No:STR7-INS-001 || Requirement: On Stratos-7, the INS shall be dual-redundant with two LRUs mounted on the primary avionics rack with 200 mm minimum lateral separation, fed from distinct buses per ##PWR.PWR-025.
Derives From: INS-003 ||

|| Requirement No:STR7-INS-002 || Requirement: On Stratos-7, the INS shall support high-altitude operations up to 44 000 ft with no degradation of attitude or position accuracy beyond INS-021 and INS-022. ||

|| Requirement No:STR7-INS-003 || Requirement: On Stratos-7, the INS shall support airborne-start (engine-running on ramp) alignment with ground-handling-induced vibration up to 0.3 g RMS, completing fine-align in ≤ 10 min. ||

|| Requirement No:ALX2-INS-001 || Requirement: On AeroLynx-X2, the INS shall be dual-redundant and support coordinated attitude output for twin-engine differential-thrust control (##ALX2-FCC-002), with lane-to-lane attitude agreement within 0.05° 1-sigma.
Satisfies: ##ALX2-FCC-002 ||

|| Requirement No:ALX2-INS-002 || Requirement: On AeroLynx-X2, the INS shall support maritime operations including extended over-water flights with no GPS outage greater than 10 min producing position drift exceeding 500 m. ||

|| Requirement No:SKT1-INS-001 || Requirement: On Skyrunner-T1, the INS shall be a single commercial-grade MEMS IMU packaged with the FCC in a combined LRU to reduce weight and cost, with bias stability per INS-024 commercial grade.
Refines: INS-003 ||

|| Requirement No:SKT1-INS-002 || Requirement: On Skyrunner-T1, the INS shall support catapult-launch acceleration of up to 8 g for 150 ms per ##SKT1-FCC-004 without loss of alignment or transition to FAULT mode.
Satisfies: ##SKT1-FCC-004 ||

|| Requirement No:NBC3-INS-001 || Requirement: On Nimbus-C3 civil operations, the INS shall meet the navigation performance requirements of EASA SORA 2.0 OC-3 with containment volume defined by INS-022 position accuracy plus 99.9 % confidence bound.
References: EASA SORA 2.0 ||

|| Requirement No:NBC3-INS-002 || Requirement: On Nimbus-C3, the INS shall detect in-flight cargo CG shifts indirectly via EKF residual statistics (acceleration residual > 0.05 g 1-sigma over 60 s) and flag CG_SUSPECT to the FCC per ##NBC3-FCC-002.
Satisfies: ##NBC3-FCC-002 ||

Header: APPENDICES
|| Requirement No:INS-055 || Requirement: The INS Appendix A (AeroSys-INS-APP-A) shall contain the derivation of the EKF state equations, covariance update formulation, and strapdown mechanisation identities. Appendix B shall contain the factory-calibration procedure and acceptance-test criteria. Both appendices are controlled per the Configuration Management Plan AeroSys-CMP-001 and are referenced here for completeness.
References: ARP4754A-5.5 ||
