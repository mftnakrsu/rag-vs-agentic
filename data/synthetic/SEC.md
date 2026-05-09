#Requirement: REQ-SEC
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: SEC
BASELINE: v2.0.0
ABSOLUTE PATH: /AeroSys/Common/SEC

Header: PURPOSE
|| Requirement No:SEC-001 || Requirement: This document specifies the Cyber and Secure Boot requirements for the AeroSys Dynamics platforms. Security lifecycle and assurance per RTCA DO-326A, DO-356A, DO-355 are applied at DAL-B security-partition level on all platforms, with additional DO-326A-only scope on Skyrunner-T1 per the Platform Certification Matrix. ||

Header: SCOPE
|| Requirement No:SEC-002 || Requirement: This module covers security-architecture requirements: secure boot, cryptographic key management, authentication of commands, integrity protection of messages, database-signature verification, continuous airworthiness security, and TVRA-derived mitigations. It excludes physical-security of ground and air equipment. ||

Header: REFERENCES
|| Requirement No:SEC-003 || Requirement: The governing references are: RTCA DO-326A (Airworthiness Security Process), RTCA DO-355A (Information Security Guidance for Continued Airworthiness), RTCA DO-356A (Security Assurance Activities), EUROCAE ED-202A/ED-203A/ED-204A (European equivalents), FIPS 140-3 (cryptographic modules), FIPS 180-4 (SHA-2), FIPS 197 (AES), NIST SP 800-57 (key management). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|TVRA|Threat, Vulnerability, and Risk Assessment|
--------------------------------------------------
|HMAC|Hash-based Message Authentication Code|
--------------------------------------------------
|AES-GCM|Advanced Encryption Standard in Galois/Counter Mode|
--------------------------------------------------
|PKI|Public Key Infrastructure|
--------------------------------------------------
|ROT|Root of Trust|
--------------------------------------------------
|HSM|Hardware Security Module|
--------------------------------------------------
|TPM|Trusted Platform Module|
--------------------------------------------------
|CVE|Common Vulnerabilities and Exposures|
--------------------------------------------------

Header: REQUIREMENTS

Header: General
|| Requirement No:SEC-003 || Requirement: The system shall enforce an authenticated-command discipline on the FCC per ##FCC.FCC-011, using HMAC-SHA-256 with per-command sequence numbers that are monotonically increasing and not reused within a flight.
Satisfies: ##FCC.FCC-011 ||

|| Requirement No:SEC-008 || Requirement: The system shall enforce a command-validation discipline per ##FCC.FCC-031 and ##CDL.CDL-013, rejecting commands with invalid range, rate, sequence, or authentication.
Satisfies: ##FCC.FCC-031, ##CDL.CDL-013, ##FCC.FCC-040, ##PLD.PLD-029 ||

|| Requirement No:SEC-010 || Requirement: The system shall use AES-256 in GCM mode for encryption and HMAC-SHA-256 for authentication on the CDL forward and return links per ##CDL.CDL-012, with session keys rotated per policy.
Satisfies: ##CDL.CDL-012, ##COMM.COMM-019, ##DLNK.DLNK-013, ##AUTO.AUTO-006, ##EMS.EMS-009
References: FIPS 197, FIPS 180-4 ||

|| Requirement No:SEC-015 || Requirement: The system shall require operator authentication (multi-factor per ##GCS.GCS-008) for all maintenance-mode operations, software updates, and configuration changes, across the FCC maintenance port, INS maintenance port, APM maintenance port, and MBIT interface.
Satisfies: ##GCS.GCS-008, ##FCC.FCC-044, ##INS.INS-045, ##APM.APM-029, ##BIT.BIT-020, ##BIT.BIT-031 ||

|| Requirement No:SEC-020 || Requirement: The system shall verify digital signatures on all loadable data and software using an asymmetric public-key scheme (RSA-3072 or ECDSA-P256 minimum), rejecting any load whose signature is invalid, expired, or revoked.
Satisfies: ##FMS.FMS-006, ##FMS.FMS-010, ##BIT.BIT-033
References: NIST SP 800-57 ||

|| Requirement No:SEC-022 || Requirement: The FMS flight-plan upload interface per ##FMS.FMS-035 shall require the same digital-signature scheme as SEC-020, with operator counter-signature from the GCS.
Satisfies: ##FMS.FMS-035 ||

|| Requirement No:SEC-025 || Requirement: The NAV and INS EKF implementations shall include spoofing-detection per ##INS.INS-028, with the security monitor consuming spoof-suspect flags and logging them.
Satisfies: ##INS.INS-028, ##NAV.NAV-028 ||

|| Requirement No:SEC-028 || Requirement: The system shall maintain a dedicated security-monitor function receiving anti-spoof, anti-jam, anti-replay, and anti-tamper indications from INS, GPS, NAV, CDL, COMM, and FCC, and shall coordinate cyber-incident response with ##EMS.EMS-021.
Satisfies: ##EMS.EMS-021, ##INS.INS-029, ##GPS.GPS-022, ##NAV.NAV-028 ||

|| Requirement No:SEC-030 || Requirement: The GCS shall implement network-zone segregation per ##GCS.GCS-024 with dedicated firewalls and no routable paths from general-IT networks to operational networks.
Satisfies: ##GCS.GCS-024
References: DO-326A ||

|| Requirement No:SEC-032 || Requirement: The system shall support cryptographic zeroise per ##CDL.CDL-021 and ##DLNK.DLNK-014 on authenticated command or tamper-detection input, completing within 200 ms.
Satisfies: ##CDL.CDL-021, ##DLNK.DLNK-014 ||

|| Requirement No:SEC-035 || Requirement: The FADEC/ECU configuration verification per ##ENG.ENG-037 shall be extended to all flight-critical LRUs, verifying installed software CRC or hash against an authenticated baseline at power-on.
Satisfies: ##ENG.ENG-037 ||

|| Requirement No:SEC-004 || Requirement: The system shall implement secure boot on all computing LRUs using a hardware root-of-trust (TPM 2.0-equivalent or secure-element), verifying the integrity and authenticity of each boot stage before execution; boot shall halt on verification failure with an audit entry.
References: DO-326A, FIPS 140-3 ||

|| Requirement No:SEC-005 || Requirement: The system shall store cryptographic keys in hardware-protected key stores (HSM or secure-element) with keys not extractable by software, and shall enforce access control on key use based on authenticated role per ##GCS.GCS-009.
Satisfies: ##GCS.GCS-009
References: FIPS 140-3 ||

|| Requirement No:SEC-006 || Requirement: The system shall maintain a Threat, Vulnerability, and Risk Assessment (TVRA) register per DO-326A with mitigation traceability to requirements in this and other modules, reviewed and updated at each major baseline release.
References: DO-326A, DO-356A ||

|| Requirement No:SEC-007 || Requirement: The system shall log all security-relevant events (authentication failures, signature-verification failures, anti-spoof/anti-jam detections, zeroise events, secure-boot failures) to an append-only audit log with cryptographic chaining (hash-linked entries). ||

|| Requirement No:SEC-009 || Requirement: The system shall ensure key-rotation cadence per ##CDL.CDL-012 for CDL (24 h or 10 GB), per ##DLNK.DLNK-013 for DLNK (daily rotation of MSEC within 30-day keyload), and per site-specific policy for GCS operator keys.
Satisfies: ##CDL.CDL-012, ##DLNK.DLNK-013
References: NIST SP 800-57 ||

|| Requirement No:SEC-011 || Requirement: The system shall implement continued-airworthiness security monitoring per RTCA DO-355A on Nimbus-C3 civil operations, with documented procedures for vulnerability assessment, patching cadence, and field-report handling.
References: DO-355A ||

|| Requirement No:SEC-012 || Requirement: The system shall enforce role-separation between security administration and operational roles: an operator cannot self-promote to administrator, and an administrator cannot dispatch operational flight-control commands.
References: DO-326A ||

|| Requirement No:SEC-013 || Requirement: The system shall protect the integrity of time synchronisation per ##NAV.NAV-027 by detecting anomalous jumps in network-time reference (>1 s unexpected step) and rejecting such updates.
Satisfies: ##NAV.NAV-027 ||

|| Requirement No:SEC-014 || Requirement: The system shall apply defence-in-depth between CDL (internet-facing for BLOS) and internal avionics buses, with a dedicated security-partition guard enforcing allowed command types per RBAC and flight phase.
References: DO-356A ||

|| Requirement No:SEC-016 || Requirement: The system shall conduct security-regression testing at each baseline release covering authentication, authorisation, cryptographic primitives, key rotation, zeroise, and vulnerability tests against the current CVE catalogue.
References: DO-356A ||

Header: Tables
|| Requirement No:SEC-017 || Requirement: The cryptographic algorithms and parameters shall be per the Crypto_Selections table.
Table Type: MESSAGE
Table Name or Description: Crypto_Selections
Table: Crypto_Selections
|Function|Algorithm|Key Size|Mode|Notes|
--------------------------------------------------
|Confidentiality (CDL)|AES|256 bit|GCM|per SEC-010|
--------------------------------------------------
|Authentication (commands)|HMAC-SHA-256|256 bit|n/a|per SEC-003|
--------------------------------------------------
|Digital signature (software/DB)|RSA-3072 or ECDSA-P256|3072/256 bit|PKCS#1.5 or DER|per SEC-020|
--------------------------------------------------
|Hash|SHA-256|256 bit|n/a|FIPS 180-4|
--------------------------------------------------
|Tactical DLNK|Type 1 (national)|per approval|TSEC+MSEC|per SEC-009|
--------------------------------------------------
|Key storage|AES-256 wrap in HSM|256 bit|n/a|per SEC-005|
-------------------------------------------------- ||

|| Requirement No:SEC-018 || Requirement: The security-event log shall record events per the Security_Event_Types table, each with UTC timestamp, LRU-ID, role-ID (where applicable), and outcome.
Table Type: MESSAGE
Table Name or Description: Security_Event_Types
Table: Security_Event_Types
|Event|Severity|Log Level|
--------------------------------------------------
|Authentication success|INFO|summary|
--------------------------------------------------
|Authentication failure|MAJOR|detail|
--------------------------------------------------
|Signature verification failure|CRITICAL|full|
--------------------------------------------------
|Secure-boot failure|CRITICAL|full|
--------------------------------------------------
|Anti-spoof trigger|MAJOR|detail|
--------------------------------------------------
|Anti-jam trigger|MAJOR|detail|
--------------------------------------------------
|Zeroise event|CRITICAL|full|
--------------------------------------------------
|Key-rotation success|INFO|summary|
--------------------------------------------------
|Tamper-detect|CRITICAL|full|
-------------------------------------------------- ||

Header: Test
|| Requirement No:SEC-019 || Requirement: Command-authentication end-to-end (SEC-003, SEC-008, CDL-013) shall be verified by fault-injection of malformed HMAC, replayed sequence numbers, stale timestamps, and wrong-key messages, demonstrating 100 % rejection across 1 000 injections.
Verifies: SEC-003, SEC-008, ##CDL.CDL-013
References: DO-356A ||

|| Requirement No:SEC-021 || Requirement: Secure-boot verification (SEC-004) shall be verified by injecting a modified boot image (single bit flip, unsigned image, expired-certificate-signed image) and confirming boot halts with audit entry in each case.
Verifies: SEC-004
References: DO-326A ||

|| Requirement No:SEC-023 || Requirement: Cryptographic zeroise (SEC-032) shall be verified on all key-bearing LRUs (CDL, DLNK, GCS key store) by commanded zeroise and subsequent key-recovery attempt, confirming no residual key material remains retrievable.
Verifies: SEC-032
References: DO-356A, FIPS 140-3 ||
