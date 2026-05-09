#Requirement: REQ-PLD
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: PLD
BASELINE: v1.7.0
ABSOLUTE PATH: /AeroSys/Common/PLD

Header: PURPOSE
|| Requirement No:PLD-001 || Requirement: This document specifies the Payload Management Controller (PMC) requirements for Stratos-7, AeroLynx-X2, and Skyrunner-T1. Nimbus-C3 uses a separate Cargo Management Controller (CMC) specified in a dedicated module (not in this release). The PMC software shall be developed at DO-178C DAL-B on all applicable platforms and cyber-security assurance per DO-326A/DO-356A. ||

Header: SCOPE
|| Requirement No:PLD-002 || Requirement: This module covers the PMC acting as the control point for mission sensors (EOIR per ##EOIR.EOIR-001, SAR per ##SAR.SAR-001), external-pod interfaces, and external-store stations on Stratos-7 where fitted. It excludes the sensor-internal processing and the GCS operator workflow (##GCS.GCS-001). ||

|| Requirement No:PLD-003 || Requirement: The PMC shall be a single LRU on all applicable platforms, located near the payload-bay equipment rack with dedicated payload-bus routing per ##STR.STR-038. ||

Header: REFERENCES
|| Requirement No:PLD-004 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, RTCA DO-160G, STANAG 4586 (UAS interoperability), STANAG 4609 (motion imagery), MIL-STD-1760E (store interface, Stratos-7 only), RTCA DO-326A. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|PMC|Payload Management Controller|
--------------------------------------------------
|EOIR|Electro-Optical / Infrared|
--------------------------------------------------
|SAR|Synthetic Aperture Radar|
--------------------------------------------------
|GMTI|Ground Moving Target Indication|
--------------------------------------------------
|LOI|Level of Interoperability (STANAG 4586)|
--------------------------------------------------
|ROI|Region of Interest|
--------------------------------------------------
|LOS|Line of Sight (sensor)|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:PLD-005 || Requirement: The PMC shall support the following operational modes:
    a) OFF
    b) STANDBY (power applied, sensors warmed)
    c) ACTIVE (at least one sensor in operational state)
    d) SCAN (automated area-scan pattern)
    e) TRACK (sensor tracking a designated target)
    f) TRANSFER (handing over tracks to another platform via ##DLNK.DLNK-009)
    g) FAULT ||

|| Requirement No:PLD-006 || Requirement: The PMC shall require operator authorisation per ##HMI.HMI-150 before transitioning from STANDBY to ACTIVE to prevent inadvertent sensor radiation (SAR on Stratos-7 and AeroLynx-X2). ||

|| Requirement No:PLD-007 || Requirement: The PMC shall transition to FAULT on any of: loss of payload bus for > 500 ms, loss of primary power for > 200 ms without hold-up, or sensor-return safety-interlock disarm (SAR LASER-class illumination safety). ||

Header: General
|| Requirement No:PLD-008 || Requirement: The PMC shall implement STANAG 4586 Level IV control semantics on Stratos-7 and AeroLynx-X2, and Level III on Skyrunner-T1, exposing the corresponding service set to the GCS via ##GCS.GCS-065.
References: STANAG 4586 ||

|| Requirement No:PLD-009 || Requirement: The PMC shall dispatch payload-command frames received from the CDL (##CDL.CDL-030, target_module = PLD) to the appropriate sensor or external store per the command_id routing table (PLD-033), rejecting unknown commands. ||

|| Requirement No:PLD-010 || Requirement: The PMC shall accept EOIR pointing commands (azimuth, elevation, zoom) and SAR imaging parameters (mode, resolution, swath, ROI) at up to 10 Hz and forward them to the respective sensor LRU.
Satisfies: ##CDL.CDL-030 ||

|| Requirement No:PLD-011 || Requirement: The PMC shall aggregate telemetry from EOIR (##EOIR.EOIR-015) and SAR (##SAR.SAR-010) at their native rates, multiplex into the payload-return stream, and forward to the CDL for downlink per ##CDL.CDL-031. ||

|| Requirement No:PLD-012 || Requirement: The PMC shall provide video/imagery encryption for classified operations using AES-256 at the sensor-output stage, with keys managed per ##SEC.SEC-010.
Satisfies: ##SEC.SEC-010
References: DO-326A ||

|| Requirement No:PLD-013 || Requirement: The PMC shall encode EO video to STANAG 4609 motion-imagery format with embedded KLV metadata (platform position, attitude, sensor pointing, time), updating metadata at 25 Hz minimum.
References: STANAG 4609 ||

|| Requirement No:PLD-014 || Requirement: The PMC shall support ROI designation: on receipt of a lat/lon or image-coordinate ROI, the PMC shall compute and command sensor pointing to centre the ROI within ±0.1° of true bearing. ||

|| Requirement No:PLD-015 || Requirement: The PMC shall support sensor handover to/from a coalition partner via the tactical datalink (##DLNK.DLNK-009) on Stratos-7 and AeroLynx-X2, exchanging track state and sensor configuration metadata.
Satisfies: ##DLNK.DLNK-009 ||

|| Requirement No:PLD-016 || Requirement: The PMC shall monitor sensor health at 1 Hz for each attached payload LRU and declare a sensor INOPERATIVE after 3 consecutive heartbeat misses or self-test failures, notifying the operator per ##HMI.HMI-152. ||

|| Requirement No:PLD-017 || Requirement: The PMC shall provide a payload-bus fault-isolation capability: on persistent fault on any sensor node, the PMC shall isolate the sensor from the bus within 200 ms and continue operating the remaining sensors. ||

|| Requirement No:PLD-018 || Requirement: The PMC shall ensure sensor safety interlocks are enforced, including: EOIR laser designator inhibited below configured altitude (nominal 100 ft AGL to prevent specular ground reflections) and SAR transmit inhibited on ground (WoW asserted) and within configured exclusion zones. ||

|| Requirement No:PLD-019 || Requirement: The PMC shall time-stamp all sensor outputs with UTC accuracy ≤ 10 µs derived from ##GPS.GPS-010 via ##NAV.NAV-027, to support georegistration and post-processing.
Satisfies: ##NAV.NAV-027 ||

|| Requirement No:PLD-020 || Requirement: The PMC shall publish PLD_STATUS_MSG at 2 Hz with per-sensor health, mode, pointing, and fault-word to the GCS (##GCS.GCS-070) and FDR (##FDR.FDR-040).
Satisfies: ##GCS.GCS-070 ||

|| Requirement No:PLD-021 || Requirement: The PMC shall maintain internal logging (last 8 h) of all commanded sensor actions, operator-ID (from ##CDL.CDL-033), and results, stored in non-volatile memory for post-mission analysis. ||

|| Requirement No:PLD-022 || Requirement: The PMC shall coordinate with the TCS for payload-bay thermal management (cold-plate temperature, fan control per ##TCS.TCS-022) to keep sensor electronics within operating range.
Satisfies: ##TCS.TCS-022 ||

|| Requirement No:PLD-023 || Requirement: On Stratos-7, the PMC shall manage external-store stations per MIL-STD-1760E, supporting up to 4 hardpoints with umbilical interface for store power, discrete safety signals, and high-speed digital bus.
References: MIL-STD-1760E ||

|| Requirement No:PLD-024 || Requirement: On Stratos-7, the PMC shall verify positive presence of each external-store before enabling its power bus, using the MIL-STD-1760E presence discrete and identification message. ||

|| Requirement No:PLD-025 || Requirement: On Stratos-7, the PMC shall enforce an arm-authorisation chain requiring three independent conditions: operator command, master-arm switch state, and platform-safety interlock (WoW=FALSE AND altitude > configured minimum) before any store-station arm command is executed. ||

|| Requirement No:PLD-026 || Requirement: On Nimbus-C3 (where an under-fuselage cargo pod is fitted), the PMC shall manage the external-pod interface with MIL-STD-1760-compatible umbilical providing pod-power enable, data, and jettison interlock per ##NBC3-FCC-003.
Satisfies: ##NBC3-FCC-003 ||

|| Requirement No:PLD-027 || Requirement: The PMC shall operate across DO-160G §4 Category A2 environmental envelope and shall enforce DO-160G §20 Category Y EMC with the CDL (##CDL.CDL-024) and DLNK (##DLNK.DLNK-017).
References: DO-160G-4, DO-160G-20 ||

|| Requirement No:PLD-028 || Requirement: The PMC shall support a 50 ms power-interruption profile per DO-160G §16 Category Z using hold-up capacitor energy per ##PWR.PWR-018, preserving current sensor state and pointing.
Satisfies: ##PWR.PWR-018 ||

|| Requirement No:PLD-029 || Requirement: The PMC shall implement authenticated command reception per ##SEC.SEC-008 and shall reject commands with invalid HMAC, stale timestamp, or reused sequence number.
Satisfies: ##SEC.SEC-008 ||

|| Requirement No:PLD-030 || Requirement: On Nimbus-C3, the PMC shall support external-pod jettison per the configured emergency-jettison sequence (operator-commanded, authenticated, with 2 s confirmation dialog in ##HMI.HMI-155), with pre-configured attitude compensation per ##NBC3-FCC-003.
Satisfies: ##NBC3-FCC-003, ##HMI.HMI-155 ||

Header: Interface
|| Requirement No:PLD-031 || Requirement: The PMC shall interface to sensors and external stores via a dedicated payload bus: Ethernet 1 Gbps baseline on Stratos-7 and AeroLynx-X2, 100 Mbps on Skyrunner-T1, with FibreChannel in addition on Stratos-7 for high-bandwidth SAR/imagery.
References: STANAG 4586 ||

|| Requirement No:PLD-032 || Requirement: The PMC shall format PLD_STATUS_MSG per the table below.
Table Type: MESSAGE
Table Name or Description: PLD_Status_Msg
Table: PLD_Status_Msg
|Field|Type|Range|
--------------------------------------------------
|mode|uint8|enum {OFF,STBY,ACTIVE,SCAN,TRACK,TRANSFER,FAULT}|
--------------------------------------------------
|eoir_health|uint8|0-100|
--------------------------------------------------
|sar_health (if fitted)|uint8|0-100|
--------------------------------------------------
|eoir_az,eoir_el|float32 ×2|-180 to +180 deg, -90 to +90 deg|
--------------------------------------------------
|sar_mode (if fitted)|uint8|enum|
--------------------------------------------------
|store_present (STR7)|uint8|bitmask 4 stations|
--------------------------------------------------
|master_arm|uint8|0 or 1|
--------------------------------------------------
|fault_word|uint32|bitmask|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:PLD-033 || Requirement: The PMC shall route commands to sensors per the Payload_Command_Routing table.
Table Type: MESSAGE
Table Name or Description: Payload_Command_Routing
Table: Payload_Command_Routing
|command_id range|Target|Purpose|
--------------------------------------------------
|0x0401-0x040F|PMC internal|mode, config|
--------------------------------------------------
|0x0410-0x041F|EOIR|pointing, zoom, mode|
--------------------------------------------------
|0x0420-0x042F|SAR|imaging parameters|
--------------------------------------------------
|0x0430-0x043F|EOIR laser|ranging, designation|
--------------------------------------------------
|0x0440-0x044F|external stores (STR7)|arm, select, release|
--------------------------------------------------
|0x0450-0x045F|external pod (NBC3)|pod power, jettison|
-------------------------------------------------- ||

|| Requirement No:PLD-034 || Requirement: The PMC shall enforce sensor safety inhibits per the Payload_Safety_Inhibits table.
Table Type: MESSAGE
Table Name or Description: Payload_Safety_Inhibits
Table: Payload_Safety_Inhibits
|Sensor/Function|Inhibit Condition|
--------------------------------------------------
|EOIR laser designator|AGL < 100 ft or operator-safe switch off|
--------------------------------------------------
|SAR transmit|WoW asserted, or in exclusion-zone polygon|
--------------------------------------------------
|External store arm (STR7)|WoW asserted OR master-arm off OR altitude < cfg|
--------------------------------------------------
|External pod jettison (NBC3)|altitude < 500 ft AGL|
-------------------------------------------------- ||

Header: Test
|| Requirement No:PLD-035 || Requirement: Command-authentication (PLD-029) shall be verified by fault-injection of malformed, replayed, and stale commands, demonstrating 100 % rejection without propagation to the sensor.
Verifies: PLD-029
References: DO-326A ||

|| Requirement No:PLD-036 || Requirement: Safety-inhibit enforcement (PLD-018) shall be verified by attempting laser-activation on ground and SAR transmit in exclusion zone, demonstrating 100 % inhibit and operator notification.
Verifies: PLD-018 ||

|| Requirement No:PLD-037 || Requirement: Sensor handover (PLD-015) shall be verified on the iron-bird with a simulated coalition partner exchanging track state via DLNK, demonstrating successful handover within 2 s and no loss of track data.
Verifies: PLD-015 ||

|| Requirement No:STR7-PLD-001 || Requirement: On Stratos-7, the PMC shall control 4 MIL-STD-1760E hardpoints with independent per-station arm and release sequencing, and shall log every arm and release event with timestamp to ##FDR.FDR-040.
Satisfies: ##FDR.FDR-040
References: MIL-STD-1760E ||

|| Requirement No:ALX2-PLD-001 || Requirement: On AeroLynx-X2, the PMC shall support a lighter payload bus without MIL-STD-1760 stores, focused on EOIR and SAR (##SAR.SAR-001) operation for tactical ISR. ||

|| Requirement No:SKT1-PLD-001 || Requirement: On Skyrunner-T1, the PMC shall manage a single micro-EOIR sensor (##EOIR.EOIR-001) and an optional laser rangefinder, with simplified STANAG 4586 Level III services. ||

|| Requirement No:SKT1-PLD-002 || Requirement: On Skyrunner-T1, the PMC shall not support SAR, external stores, or tactical-datalink sensor handover. ||
