#Requirement: REQ-COMM
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: COMM
BASELINE: v1.4.0
ABSOLUTE PATH: /AeroSys/Common/COMM

Header: PURPOSE
|| Requirement No:COMM-001 || Requirement: This document specifies the Voice and Beyond-Line-of-Sight Communications (COMM) requirements for Stratos-7, AeroLynx-X2, and Nimbus-C3. Skyrunner-T1 is not equipped with voice or independent BLOS comms beyond the primary CDL. The COMM software shall be developed at DO-178C DAL-B and cyber-security assurance per DO-326A. ||

Header: SCOPE
|| Requirement No:COMM-002 || Requirement: This module covers VHF (118 - 137 MHz civil aeronautical band), UHF (225 - 400 MHz military band on STR7/ALX2 only), HF (2 - 30 MHz on STR7 only) voice, and BLOS SATCOM (Iridium L-band, Inmarsat L-band and Ka-band on STR7/NBC3) data and voice. It excludes the primary CDL (##CDL.CDL-001) and tactical datalink (##DLNK.DLNK-001). ||

Header: REFERENCES
|| Requirement No:COMM-003 || Requirement: The governing references are: RTCA DO-186B (VHF transceiver MOPS), RTCA DO-207 (MOPS for 25 kHz/8.33 kHz), ARINC 716 (VHF), ARINC 741 (Inmarsat), ARINC 781 (Iridium), RTCA DO-178C, RTCA DO-254, RTCA DO-160G, RTCA DO-326A, ICAO Annex 10 Volume III. ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|VHF|Very High Frequency|
--------------------------------------------------
|UHF|Ultra High Frequency|
--------------------------------------------------
|HF|High Frequency|
--------------------------------------------------
|ALE|Automatic Link Establishment (HF)|
--------------------------------------------------
|PTT|Push-To-Talk|
--------------------------------------------------
|ATC|Air Traffic Control|
--------------------------------------------------
|CPDLC|Controller-Pilot Data Link Communications|
--------------------------------------------------
|SATCOM|Satellite Communications|
--------------------------------------------------
|SELCAL|Selective Calling|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:COMM-004 || Requirement: The COMM subsystem shall provide dual VHF transceivers per ARINC 716 operating on 25 kHz or 8.33 kHz channels in the 118 - 137 MHz band, remotely tuneable by the GCS operator for ATC voice relay.
References: ARINC 716, DO-186B ||

|| Requirement No:COMM-005 || Requirement: Each VHF transceiver shall operate at transmit power selectable between 5 W and 25 W nominal, with a maximum radiated EIRP compliant with ICAO Annex 10 Volume III.
References: ICAO Annex 10 Vol III ||

|| Requirement No:COMM-006 || Requirement: The COMM subsystem shall support voice-relay through the GCS: audio received on VHF shall be forwarded to the GCS operator headset via the CDL return-link voice channel with one-way latency ≤ 250 ms, and operator PTT audio shall be uplinked via CDL and re-transmitted on VHF within the same latency bound.
Derives From: ##CDL.CDL-011 ||

|| Requirement No:COMM-007 || Requirement: On Stratos-7 and AeroLynx-X2, the COMM subsystem shall include a UHF transceiver operating in 225 - 400 MHz with tunable-channel spacing 25 kHz, supporting HAVE QUICK II frequency-hopping and SINCGARS compatibility where enabled. ||

|| Requirement No:COMM-008 || Requirement: On Stratos-7, the COMM subsystem shall include an HF transceiver operating in the 2 - 30 MHz band with ARQ data mode at 600 bps and ALE (Automatic Link Establishment) per MIL-STD-188-141B. ||

|| Requirement No:COMM-009 || Requirement: The COMM subsystem shall support SELCAL codes for VHF and HF voice channels per ARINC 596, with up to 8 configurable 4-character codes.
References: ARINC 596 ||

|| Requirement No:COMM-010 || Requirement: The COMM subsystem shall include an Iridium L-band SATCOM modem (ARINC 781 classical aero or next-generation) providing BLOS voice and low-rate data (2.4 to 128 kbps) as a fallback to the primary CDL BLOS link.
References: ARINC 781 ||

|| Requirement No:COMM-011 || Requirement: On Stratos-7 and Nimbus-C3, the COMM subsystem shall additionally include an Inmarsat SwiftBroadband or Ka-band terminal providing 432 kbps to 2 Mbps BLOS data per ARINC 741, for civil ATC CPDLC and AOC messaging.
References: ARINC 741, DO-258A ||

|| Requirement No:COMM-012 || Requirement: The COMM subsystem shall support CPDLC per DO-258A (FANS 1/A+) over the SATCOM data link for ATC coordination on civil routes on Stratos-7 and Nimbus-C3.
References: DO-258A ||

|| Requirement No:COMM-013 || Requirement: The COMM subsystem shall support ACARS messaging per ARINC 620 over VHF Data Link (VDL Mode 2) and SATCOM, for routine aircraft-to-airline operational communications on Nimbus-C3 civil operations. ||

|| Requirement No:COMM-014 || Requirement: The COMM subsystem shall maintain BER ≤ 10^-5 on SATCOM data channels at the operational design margin per ARINC 781 (Iridium) and ARINC 741 (Inmarsat).
References: ARINC 741, ARINC 781 ||

|| Requirement No:COMM-015 || Requirement: The COMM subsystem shall support emergency squawk and 121.5 MHz guard monitoring on one VHF receiver continuously when fitted, raising an operator alert upon detected emergency signalling. ||

|| Requirement No:COMM-016 || Requirement: The COMM subsystem shall maintain configured frequency and settings across a 50 ms power-interruption per DO-160G §16 Category Z.
References: DO-160G-16 ||

|| Requirement No:COMM-017 || Requirement: The COMM subsystem shall operate across DO-160G §4 Category A2 environmental envelope (operating temperature -40 °C to +70 °C, altitude up to 55 000 ft).
References: DO-160G-4 ||

|| Requirement No:COMM-018 || Requirement: The COMM subsystem shall enforce DO-160G §20 Category Y EMC requirements and shall coexist with the CDL (##CDL.CDL-024), GPS (##GPS.GPS-009), and radar altimeter (##RADAR.RADAR-009) without mutual interference.
References: DO-160G-20 ||

|| Requirement No:COMM-019 || Requirement: The COMM subsystem shall provide voice-encryption capability on UHF (STR7/ALX2) via embedded cryptographic module with key rotation per ##SEC.SEC-010, inhibiting transmit if no valid key is loaded in secure mode.
Satisfies: ##SEC.SEC-010 ||

|| Requirement No:COMM-020 || Requirement: The COMM subsystem shall expose a health-status word at 1 Hz reporting per-transceiver TX_OK, RX_OK, antenna VSWR, temperature, and HEATER_OK (where fitted). ||

|| Requirement No:COMM-021 || Requirement: On any transceiver fault (failed self-test, excessive VSWR, or loss of local-oscillator lock), the COMM subsystem shall disable transmit on the faulted transceiver within 100 ms and notify the operator per ##HMI.HMI-105. ||

|| Requirement No:COMM-022 || Requirement: The COMM subsystem shall provide a dedicated emergency SATCOM data channel capable of forwarding compact aircraft-state reports (position, altitude, velocity, fuel, basic health) at 1 Hz with ≤ 200 B frame size, useable independent of the primary CDL.
Satisfies: ##EMS.EMS-018 ||

Header: Interface
|| Requirement No:COMM-023 || Requirement: The COMM subsystem shall be remotely controlled from the GCS via the CDL, accepting frequency-set, transceiver-mode, SELCAL-code, and PTT commands per the COMM_Control_Msg table.
Table Type: MESSAGE
Table Name or Description: COMM_Control_Msg
Table: COMM_Control_Msg
|Field|Type|Range|Notes|
--------------------------------------------------
|transceiver_id|uint8|enum {VHF1,VHF2,UHF,HF,IRIDIUM,INMARSAT}|target|
--------------------------------------------------
|freq_khz|uint32|2000 to 400000 kHz|tuned frequency|
--------------------------------------------------
|mode|uint8|enum {RX,TX,VOICE,DATA,OFF}|operating mode|
--------------------------------------------------
|channel_space_hz|uint32|8333 or 25000|VHF only|
--------------------------------------------------
|squelch|uint8|0 to 15|level|
--------------------------------------------------
|ptt|uint8|0 or 1|push-to-talk|
--------------------------------------------------
|selcal_code|bytes(4)|ASCII 4 chars|SELCAL|
--------------------------------------------------
Satisfies: ##CDL.CDL-030 ||

|| Requirement No:COMM-024 || Requirement: The COMM subsystem shall exchange digital data (CPDLC, ACARS, emergency telemetry) with the FMS and GCS via the primary avionics bus at ≤ 1 Hz framing.
References: DO-258A ||

|| Requirement No:COMM-025 || Requirement: The COMM subsystem shall consume nominal 28 V DC per MIL-STD-704F with steady-state power draw ≤ 200 W (STR7 full configuration), ≤ 140 W (ALX2), and ≤ 80 W (NBC3) typical, with transient 50 ms ride-through per DO-160G §16 Category Z.
References: MIL-STD-704F, DO-160G-16 ||

Header: Tables
|| Requirement No:COMM-026 || Requirement: The COMM subsystem shall support the transceiver configurations listed in the Transceiver_Matrix table.
Table Type: MESSAGE
Table Name or Description: Transceiver_Matrix
Table: Transceiver_Matrix
|Transceiver|Band|STR7|ALX2|NBC3|Typical TX Power|
--------------------------------------------------
|VHF1|118-137 MHz|yes|yes|yes|25 W|
--------------------------------------------------
|VHF2|118-137 MHz|yes|yes|yes|25 W|
--------------------------------------------------
|UHF|225-400 MHz|yes|yes|no|30 W|
--------------------------------------------------
|HF|2-30 MHz|yes|no|no|150 W PEP|
--------------------------------------------------
|Iridium|L-band|yes|yes|yes|7 W|
--------------------------------------------------
|Inmarsat|L/Ka-band|yes|no|yes|per terminal class|
-------------------------------------------------- ||

Header: Test
|| Requirement No:COMM-027 || Requirement: VHF voice-relay latency (COMM-006) shall be verified by loop-back test with a calibrated signal generator and GCS operator console, measuring 500 PTT-to-audio and audio-to-headset exchanges, demonstrating ≤ 250 ms one-way latency at the 95 % level.
Verifies: COMM-006 ||

|| Requirement No:COMM-028 || Requirement: SATCOM BER (COMM-014) shall be verified by end-to-end data-mode testing on the operational satellite with 10^8 transmitted bits, confirming measured BER ≤ 10^-5.
Verifies: COMM-014 ||

|| Requirement No:COMM-029 || Requirement: EMC coexistence (COMM-018) shall be verified by DO-160G §20 Category Y testing with all transceivers active simultaneously at maximum duty cycle, demonstrating no spurious emission into the protected GPS, radar-altimeter, and CDL bands beyond the allowable limits.
Verifies: COMM-018
References: DO-160G-20 ||

|| Requirement No:COMM-030 || Requirement: Encrypted-UHF inhibit (COMM-019) shall be verified by negative test: attempt to transmit on UHF with no valid key loaded, confirming transmit is inhibited and an operator alert is raised within 200 ms.
Verifies: COMM-019 ||
