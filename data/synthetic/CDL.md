#Requirement: REQ-CDL
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: CDL
BASELINE: v2.0.1
ABSOLUTE PATH: /AeroSys/Common/CDL

Header: PURPOSE
|| Requirement No:CDL-001 || Requirement: This document specifies the Common Data Link (CDL) requirements for the AeroSys Dynamics common comms core, applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3. The CDL software shall be developed at DO-178C DAL-B on all platforms, and the RF hardware at DO-254 Level B, with cyber-security assurance per DO-326A/DO-356A at DAL-B. ||

Header: SCOPE
|| Requirement No:CDL-002 || Requirement: This module covers the primary line-of-sight (LOS) and beyond-line-of-sight (BLOS) data link used for command-uplink and telemetry/video-downlink between the GCS (##GCS.GCS-001) and the aircraft. It excludes voice communications (##COMM.COMM-001), tactical datalink (##DLNK.DLNK-001), and the GCS ground-side antenna infrastructure beyond the RF interface. ||

|| Requirement No:CDL-003 || Requirement: The CDL shall provide an encrypted, authenticated, integrity-protected bi-directional link, with command-uplink integrity as the safety-critical path and telemetry/video-downlink as the operational path.
Derives From: ARP4761-FHA-COMM-01 ||

Header: REFERENCES
|| Requirement No:CDL-004 || Requirement: The governing references are: STANAG 7085 (Interoperable Data Links), STANAG 4660 (UAS Control Element), STANAG 4586 (UAS Interoperability), RTCA DO-362 (Command and Control Link), RTCA DO-178C, RTCA DO-254, RTCA DO-160G, RTCA DO-326A, RTCA DO-356A, ITU Radio Regulations. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|CDL|Common Data Link|
--------------------------------------------------
|LOS|Line of Sight|
--------------------------------------------------
|BLOS|Beyond Line of Sight|
--------------------------------------------------
|FHSS|Frequency-Hopping Spread Spectrum|
--------------------------------------------------
|DSSS|Direct-Sequence Spread Spectrum|
--------------------------------------------------
|EIRP|Effective Isotropic Radiated Power|
--------------------------------------------------
|BER|Bit Error Rate|
--------------------------------------------------
|HMAC|Hash-based Message Authentication Code|
--------------------------------------------------
|AES|Advanced Encryption Standard|
--------------------------------------------------
|QoS|Quality of Service|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:CDL-005 || Requirement: The CDL shall support the following operational modes:
    a) OFF
    b) ACQUIRE (searching for GCS beacon)
    c) LINKED (forward and return both up)
    d) FORWARD_ONLY (forward link up, return degraded)
    e) RETURN_ONLY (return up, forward degraded)
    f) LOST (no link, entering lost-link timer)
    g) FAULT ||

|| Requirement No:CDL-006 || Requirement: Upon entry into LOST mode, the CDL shall start a platform-configurable lost-link timer (default 10 s). On timer expiry, the Autopilot shall engage RTB per ##AUTO.AUTO-022.
Satisfies: ##AUTO.AUTO-022 ||

|| Requirement No:CDL-007 || Requirement: On recovery from LOST to LINKED before the lost-link timer expires, the CDL shall reset the timer, resynchronise both forward and return links within 2 s, and notify the operator per ##HMI.HMI-100. ||

|| Requirement No:CDL-008 || Requirement: The CDL shall support LOS operations in C-band (4.4 - 5.0 GHz) as the primary LOS configuration and Ku-band (14.0 - 15.35 GHz) as BLOS satellite-relay configuration per STANAG 7085.
References: STANAG 7085 ||

Header: General
|| Requirement No:CDL-009 || Requirement: The CDL forward link (command uplink) shall operate at a baseband data rate of 200 kbps minimum, with BER ≤ 10^-7 at the design-reference link margin of 10 dB.
References: STANAG 7085 ||

|| Requirement No:CDL-010 || Requirement: The CDL return link (telemetry downlink) shall support 2 Mbps minimum for telemetry and 10 Mbps minimum for encrypted video on Stratos-7 and AeroLynx-X2, 5 Mbps combined on Nimbus-C3, and 1 Mbps on Skyrunner-T1, with BER ≤ 10^-6 on telemetry.
References: STANAG 7085 ||

|| Requirement No:CDL-011 || Requirement: The CDL forward link shall impose end-to-end latency (GCS command entry to FCC ingest) not exceeding 100 ms at 90 % confidence, and shall flag stale commands arriving > 250 ms after their transmit timestamp.
References: DO-362 ||

|| Requirement No:CDL-012 || Requirement: The CDL shall use AES-256 encryption in GCM mode for both forward and return links, with session keys rotated every 24 h of flight time or every 10 GB of traffic, whichever comes first, and with key-rotation coordination via the control channel.
Satisfies: ##SEC.SEC-010
References: DO-326A ||

|| Requirement No:CDL-013 || Requirement: The CDL shall authenticate every command frame on the forward link using HMAC-SHA-256 with per-frame sequence number, rejecting any frame whose HMAC fails, whose sequence number has been reused, or whose transmit timestamp is more than 500 ms stale.
Satisfies: ##SEC.SEC-008 ||

|| Requirement No:CDL-014 || Requirement: The CDL shall apply FHSS with ≥ 100 hops/second across ≥ 50 channels on the LOS forward link, to mitigate narrowband jamming. Hop patterns shall be keyed to the session key.
References: DO-326A ||

|| Requirement No:CDL-015 || Requirement: The CDL shall apply forward-error-correction (FEC) on the return link (convolutional code rate 1/2 or LDPC equivalent) tuned to achieve the BER target of CDL-010 at the design link margin. ||

|| Requirement No:CDL-016 || Requirement: The CDL shall automatically reduce return-link data rate in coarse steps (stepping down by factor 2 at a time from nominal to floor) when detected SNR falls below the adaptive-rate threshold for > 3 s, and step back up when SNR recovers. ||

|| Requirement No:CDL-017 || Requirement: The CDL shall detect and report link outage (no frame received for > 500 ms) on either direction within 100 ms of onset, and shall notify the operator per ##HMI.HMI-102. ||

|| Requirement No:CDL-018 || Requirement: The CDL shall support handover between LOS and BLOS configurations without loss of link for more than 2 s, with operator-initiated or automatic handover based on LOS-margin trigger. ||

|| Requirement No:CDL-019 || Requirement: The CDL shall compute and report link-quality statistics (SNR, BER, received signal strength, latency jitter) at 1 Hz to the GCS. ||

|| Requirement No:CDL-020 || Requirement: The CDL shall support at least 3 simultaneous priority queues on the return link (priority 1: safety and flight-critical telemetry; priority 2: routine telemetry; priority 3: video), with priority-1 traffic preempting priority-3 traffic. ||

|| Requirement No:CDL-021 || Requirement: The CDL shall provide cryptographic zeroise capability: on authenticated zeroise command or tamper-detect signal (##SEC.SEC-032), all key material shall be erased within 200 ms and the link transitioned to OFF.
Satisfies: ##SEC.SEC-032 ||

|| Requirement No:CDL-022 || Requirement: The CDL shall support antenna steering/tracking for directional antennas on Stratos-7 and AeroLynx-X2, maintaining pointing within ±1.5° of the true GCS bearing during coordinated manoeuvres. ||

|| Requirement No:CDL-023 || Requirement: The CDL shall operate within the frequency allocation granted by the operational authority (national or ITU), with transmit inhibit on unauthorised frequencies enforced in the RF front-end. ||

|| Requirement No:CDL-024 || Requirement: The CDL shall operate within DO-160G §20 Category Y EMC without degrading or being degraded by the radar altimeter (##RADAR.RADAR-009), GPS (##GPS.GPS-009), or SATCOM comms (##COMM.COMM-005).
References: DO-160G-20 ||

|| Requirement No:CDL-025 || Requirement: The CDL shall sustain the 50 ms primary-power interruption profile per DO-160G §16 Category Z, using hold-up energy from ##PWR.PWR-018.
Satisfies: ##PWR.PWR-018 ||

|| Requirement No:CDL-026 || Requirement: The CDL shall operate across the environmental envelope DO-160G §4 Category A2 (operating temperature -40 °C to +70 °C, altitude up to 55 000 ft). ||

|| Requirement No:CDL-027 || Requirement: The CDL shall support dynamic resource allocation of return-link bandwidth among telemetry, video, and mission-payload data streams, reconfigurable at ≤ 1 Hz via GCS operator command. ||

|| Requirement No:CDL-028 || Requirement: The CDL shall expose the STANAG 4586 Level III (indirect control) or Level IV (direct control) interoperability level per the Platform Certification Matrix (##FCC.FCC-004), with Level IV supported on Stratos-7 and AeroLynx-X2 and Level III on Nimbus-C3.
References: STANAG 4586 ||

|| Requirement No:CDL-029 || Requirement: The CDL shall provide a health-monitoring status word (CDL_HEALTH_WORD) updated at 2 Hz, reporting TX_OK, RX_OK, AUTH_OK, CRYPTO_OK, and per-direction queue occupancy. ||

Header: Interface
|| Requirement No:CDL-030 || Requirement: The CDL shall receive command frames from the GCS at up to 20 Hz and dispatch them to the FCC (##FCC.FCC-031), FMS (##FMS.FMS-022), Autopilot (##AUTO.AUTO-006), and Payload Manager (##PLD.PLD-010) according to the command-routing table (CDL-035).
Satisfies: ##FCC.FCC-031, ##FMS.FMS-022 ||

|| Requirement No:CDL-031 || Requirement: The CDL shall accept telemetry contributions from all avionics buses, aggregating NAV (##NAV.NAV-029), FCC (##FCC.FCC-051), engine (##ENG.ENG-050), fuel (##FUEL.FUEL-025), and payload (##PLD.PLD-020) at their native rates, and transmit them at 20 Hz on the return link.
Satisfies: ##NAV.NAV-029 ||

|| Requirement No:CDL-032 || Requirement: On Stratos-7 and AeroLynx-X2, the CDL shall interface with the primary 1553B avionics bus as Bus Controller for the comms sub-bus, or as Remote Terminal 12 on the main avionics bus. On Skyrunner-T1 and Nimbus-C3, the CDL shall interface via ARINC 429 and 100BASE-TX Ethernet.
References: MIL-STD-1553B, ARINC 429 ||

|| Requirement No:CDL-033 || Requirement: The CDL shall format the CDL_COMMAND_FRAME per the table below.
Table Type: MESSAGE
Table Name or Description: CDL_Command_Frame
Table: CDL_Command_Frame
|Field|Type|Range|Notes|
--------------------------------------------------
|frame_id|uint32|0 to 2^32-1|sequence, monotonic|
--------------------------------------------------
|timestamp|uint64|UTC nanoseconds|GCS TX time|
--------------------------------------------------
|target_module|uint8|enum {FCC,FMS,AUTO,PLD,EMS,SEC}|dispatch target|
--------------------------------------------------
|command_id|uint16|0 to 65535|per-module command code|
--------------------------------------------------
|payload_len|uint16|0 to 1024|bytes|
--------------------------------------------------
|payload|bytes|0 to 1024 B|command-specific|
--------------------------------------------------
|hmac|bytes(32)|HMAC-SHA-256|per CDL-013|
-------------------------------------------------- ||

|| Requirement No:CDL-034 || Requirement: The CDL shall format the CDL_TELEMETRY_FRAME per the following table with compressed TLV-encoded payloads.
Table Type: MESSAGE
Table Name or Description: CDL_Telemetry_Frame
Table: CDL_Telemetry_Frame
|Field|Type|Range|Notes|
--------------------------------------------------
|frame_id|uint32|0 to 2^32-1|sequence|
--------------------------------------------------
|timestamp|uint64|UTC nanoseconds|aircraft TX time|
--------------------------------------------------
|priority|uint8|1 to 3|per CDL-020|
--------------------------------------------------
|num_tlvs|uint16|0 to 255|TLV count|
--------------------------------------------------
|tlv_block|bytes|variable, up to 60 kB|TLV type-length-value|
--------------------------------------------------
|fec_bytes|bytes|per CDL-015|FEC overhead|
--------------------------------------------------
|auth_tag|bytes(16)|HMAC-SHA-256 trunc|frame auth|
-------------------------------------------------- ||

|| Requirement No:CDL-035 || Requirement: The CDL shall dispatch commands per the following routing table; commands with unknown target_module shall be rejected with error E_TARGET_INVALID returned to the operator.
Table Type: MESSAGE
Table Name or Description: Command_Routing
Table: Command_Routing
|target_module|Valid Command Range|Dispatch Bus|Max Frequency|
--------------------------------------------------
|FCC|0x0100 - 0x01FF|1553B RT 5 / ARINC 429|20 Hz|
--------------------------------------------------
|FMS|0x0200 - 0x02FF|same|5 Hz|
--------------------------------------------------
|AUTO|0x0300 - 0x03FF|same|20 Hz|
--------------------------------------------------
|PLD|0x0400 - 0x04FF|payload bus|10 Hz|
--------------------------------------------------
|EMS|0x0500 - 0x05FF|direct|5 Hz|
--------------------------------------------------
|SEC|0x0600 - 0x06FF|secure partition|2 Hz|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:CDL-036 || Requirement: The CDL shall enforce the link-budget design points per the Link_Budget table. Any operation with margin below the "Fail" column shall transition to LOST mode.
Table Type: MESSAGE
Table Name or Description: Link_Budget
Table: Link_Budget
|Config|Design Range|Design Margin|Fail Margin|Hand-over Trigger|
--------------------------------------------------
|C-band LOS, omni|200 nmi|10 dB|2 dB|3 dB|
--------------------------------------------------
|C-band LOS, directional|400 nmi|10 dB|2 dB|3 dB|
--------------------------------------------------
|Ku-band BLOS|SATCOM coverage|8 dB|1 dB|2 dB|
-------------------------------------------------- ||

|| Requirement No:CDL-037 || Requirement: The CDL shall provide QoS service classes per the QoS_Classes table.
Table Type: MESSAGE
Table Name or Description: QoS_Classes
Table: QoS_Classes
|Class|Target Latency|Max Loss|Example Traffic|
--------------------------------------------------
|1 (safety)|100 ms|1e-4|FCC emergency, flight-termination|
--------------------------------------------------
|2 (control)|250 ms|1e-3|routine commands, navigation|
--------------------------------------------------
|3 (payload)|1 s|1e-2|video, imagery, bulk telemetry|
-------------------------------------------------- ||

Header: Test
|| Requirement No:CDL-038 || Requirement: Forward-link latency (CDL-011) shall be verified by end-to-end test on the ground-test range with GCS and aircraft hardware, measuring 1 000 commands with timestamped ingress and egress, demonstrating 90 % within 100 ms.
Verifies: CDL-011
References: STANAG 7085 ||

|| Requirement No:CDL-039 || Requirement: Authentication rejection (CDL-013) shall be verified by fault-injection of malformed HMAC, replayed sequence numbers, and stale timestamps; the CDL shall reject 100 % of injected malformed frames without propagation.
Verifies: CDL-013
References: DO-326A ||

|| Requirement No:CDL-040 || Requirement: Zeroise (CDL-021) shall be verified by commanded zeroise on the flight-configuration hardware, demonstrating key-material erasure within 200 ms and link transition to OFF.
Verifies: CDL-021 ||

|| Requirement No:CDL-041 || Requirement: Jamming resilience (CDL-014) shall be verified by DO-160G §20 Category Y test with a calibrated narrow-band jammer at -50 dBm/Hz, demonstrating link maintenance with BER within spec.
Verifies: CDL-014
References: DO-160G-20 ||

|| Requirement No:STR7-CDL-001 || Requirement: On Stratos-7, the CDL shall support Ku-band SATCOM BLOS via onboard steerable antenna, providing 2 Mbps return link at up to 80° latitude coverage. ||

|| Requirement No:STR7-CDL-002 || Requirement: On Stratos-7, the CDL shall support dual-redundant transceivers in separate chassis fed by different power buses per ##PWR.PWR-025.
Derives From: CDL-003 ||

|| Requirement No:ALX2-CDL-001 || Requirement: On AeroLynx-X2, the CDL shall interoperate with coalition STANAG 4586 Level IV ground stations for multi-nation operations, with configurable ground-station switching every ≤ 30 s.
References: STANAG 4586 ||

|| Requirement No:SKT1-CDL-001 || Requirement: On Skyrunner-T1, the CDL shall be a single-transceiver LOS-only configuration in C-band, with a simplified link budget supporting 200 kbps forward and 1 Mbps return at up to 60 nmi range.
Refines: CDL-010 ||

|| Requirement No:NBC3-CDL-001 || Requirement: On Nimbus-C3, the CDL shall support civil-band allocations (approved C-band and Ku-band civil plans) and shall comply with DO-362 command-and-control link civil certification requirements.
References: DO-362 ||
