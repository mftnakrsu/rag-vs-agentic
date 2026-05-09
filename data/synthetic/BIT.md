#Requirement: REQ-BIT
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: BIT
BASELINE: v1.6.0
ABSOLUTE PATH: /AeroSys/Common/BIT

Header: PURPOSE
|| Requirement No:BIT-001 || Requirement: This document specifies the Built-In Test and Health Management requirements for the AeroSys Dynamics platforms. The BIT software shall be developed at DO-178C DAL-B on all platforms, with DAL-A portions on Stratos-7 and AeroLynx-X2 where BIT feeds DAL-A safety functions. ||

Header: SCOPE
|| Requirement No:BIT-002 || Requirement: This module covers Power-On BIT (PBIT), Continuous BIT (CBIT), Initiated Maintenance BIT (IBIT/MBIT), fault reporting/aggregation, and health-management trending. It excludes the FDR storage (##FDR.FDR-001) and the EMS response logic (##EMS.EMS-001). ||

Header: REFERENCES
|| Requirement No:BIT-003 || Requirement: The governing references are: RTCA DO-178C, RTCA DO-254, SAE ARP4754A, SAE ARP4761, MIL-STD-882E, SAE GEIA-STD-0009 (reliability programme), ARINC 604 (Guidance for Design and Use of Built-In Test Equipment). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|PBIT|Power-On Built-In Test|
--------------------------------------------------
|CBIT|Continuous Built-In Test|
--------------------------------------------------
|IBIT|Initiated Built-In Test|
--------------------------------------------------
|MBIT|Maintenance Built-In Test|
--------------------------------------------------
|FDI|Fault Detection and Isolation|
--------------------------------------------------
|FAR|False Alarm Rate|
--------------------------------------------------
|MTBF|Mean Time Between Failures|
--------------------------------------------------
|LRU|Line-Replaceable Unit|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:BIT-004 || Requirement: The BIT subsystem shall support the following modes:
    a) OFF
    b) PBIT (executing on power-up)
    c) CBIT (normal monitoring during operation)
    d) IBIT/MBIT (operator-initiated, ground-only)
    e) FAULT ||

|| Requirement No:BIT-005 || Requirement: PBIT shall complete on power-up within the time budget allocated to each LRU: FCC ≤ 3 s, INS ≤ 60 s (including coarse-align), GPS warm-start ≤ 30 s, others ≤ 15 s, with aggregate PBIT completion reported to the FCC per ##FCC.FCC-006.
Satisfies: ##FCC.FCC-006 ||

Header: General
|| Requirement No:BIT-006 || Requirement: PBIT shall test processor, memory, non-volatile-memory integrity (CRC), bus transceivers, and critical discrete I/O of each LRU, with each test detecting single-bit errors with ≥ 99.9 % coverage. ||

|| Requirement No:BIT-007 || Requirement: CBIT shall run continuously during operation at an aggregate rate not exceeding 10 % of available CPU, checking bus-cycle integrity, watchdog timers, CRC on critical messages, and cross-channel agreement per ##FCC.FCC-019.
Satisfies: ##FCC.FCC-019 ||

|| Requirement No:BIT-008 || Requirement: The BIT subsystem shall aggregate FCC BIT reports per ##FCC.FCC-047 at 1 Hz and publish consolidated health status to the GCS and FDR.
Satisfies: ##FCC.FCC-047 ||

|| Requirement No:BIT-009 || Requirement: The BIT subsystem shall report every detected fault with a structured fault record containing LRU-ID, fault-code, severity, UTC timestamp, and optional sensor-snapshot. ||

|| Requirement No:BIT-010 || Requirement: The BIT subsystem shall receive IMU BIT failure reports from ##INS.INS-015 and propagate them to the FCC and EMS within 100 ms of receipt.
Satisfies: ##INS.INS-015 ||

|| Requirement No:BIT-011 || Requirement: The BIT subsystem shall maintain a false-alarm rate (FAR) ≤ 0.1 % of detected events over the MTBF-predicted fault rate, tuned via field calibration in successive software releases. ||

|| Requirement No:BIT-012 || Requirement: The BIT subsystem shall enable detection of CCDL channel disagreement per ##FCC.FCC-019 with coverage verified by fault-injection tests.
Verifies: ##FCC.FCC-019 ||

|| Requirement No:BIT-013 || Requirement: The BIT subsystem shall isolate faults to the LRU level with ≥ 95 % first-attempt success on LRU replacement for flight-critical LRUs (FCC, INS, GPS, ADS, CDL).
References: ARINC 604 ||

|| Requirement No:BIT-014 || Requirement: The BIT subsystem shall support trending of fault occurrences per LRU, counting recurring faults in a sliding 100-hour window and flagging LRUs with > 3 recurrences for maintenance. ||

|| Requirement No:BIT-015 || Requirement: The PWR subsystem fault-isolation test per ##PWR.PWR-021 shall be triggerable via MBIT on ground, exercising each SSPC through a controlled over-current event.
Satisfies: ##PWR.PWR-021 ||

|| Requirement No:BIT-016 || Requirement: CBIT shall monitor bus-traffic integrity on MIL-STD-1553B (RT response times, error counts) and ARINC 429 (label validity, parity errors), raising a fault if error rate exceeds 10^-6 per frame over a 30 s window. ||

|| Requirement No:BIT-017 || Requirement: CBIT shall monitor temperature sensors in every LRU at 1 Hz and raise a fault if any internal temperature exceeds the LRU's commercial/industrial-grade rating. ||

|| Requirement No:BIT-018 || Requirement: CBIT shall verify CRC on every non-volatile-memory region (code, configuration, calibration) at 0.1 Hz or less, detecting and reporting any mismatch. ||

|| Requirement No:BIT-019 || Requirement: CBIT shall watchdog each task in the FCC partition with a deadline equal to 1.5× the task's period; watchdog timeout shall trigger task restart and log an OS_WATCHDOG event. ||

|| Requirement No:BIT-020 || Requirement: The BIT subsystem shall expose a MBIT interface for ground maintenance, authenticated per ##SEC.SEC-015, supporting per-LRU and per-function tests triggered by operator.
Satisfies: ##SEC.SEC-015, ##PWR.PWR-027 ||

|| Requirement No:BIT-021 || Requirement: The BIT subsystem shall log every MBIT invocation with operator-ID, test name, result, and artefacts for post-maintenance audit, retained for at least 90 days. ||

|| Requirement No:BIT-022 || Requirement: The BIT subsystem shall support an on-demand full system test (MBIT FULL) completing within 15 min of invocation, exercising all flight-critical functions without aircraft motion. ||

|| Requirement No:BIT-023 || Requirement: The BIT subsystem shall detect stuck-at or timing violations in the CCDL per ##FCC.FCC-046 with the cross-channel consistency checks verified as part of CBIT. ||

|| Requirement No:BIT-024 || Requirement: The BIT subsystem shall track actuator-response health per ##FCC.FCC-023 (runaway detection) and report actuator condition (wear, drift, back-EMF anomalies) to maintenance. ||

|| Requirement No:BIT-025 || Requirement: The BIT subsystem shall receive BMS fault reports from ##APM.APM-008 and propagate them per BIT-009.
Satisfies: ##APM.APM-008 ||

|| Requirement No:BIT-026 || Requirement: The BIT subsystem shall consume health inputs from payload sensors (##EOIR.EOIR-024, ##SAR.SAR-019) and aggregate them into the overall health report. ||

|| Requirement No:BIT-027 || Requirement: The BIT subsystem shall consume GCS health reports (##GCS.GCS-005 mode, connectivity) to provide an overall system-health view covering air and ground segments. ||

|| Requirement No:BIT-028 || Requirement: The BIT subsystem shall consume APM BIT reports per ##APM.APM-026 at 0.1 Hz and include them in the overall health aggregation.
Satisfies: ##APM.APM-026 ||

|| Requirement No:BIT-029 || Requirement: The BIT subsystem shall detect electrical-bus faults per ##PWR.PWR-031 and propagate them to EMS per ##EMS.EMS-019.
Satisfies: ##PWR.PWR-031, ##EMS.EMS-019 ||

|| Requirement No:BIT-030 || Requirement: The BIT subsystem shall consume EOIR sensor PBIT/CBIT per ##EOIR.EOIR-024 and flag sensor health to PMC per ##PLD.PLD-016.
Satisfies: ##EOIR.EOIR-024 ||

|| Requirement No:BIT-031 || Requirement: The BIT subsystem shall export a fault history in a machine-readable format (JSON or equivalent) accessible via the maintenance Ethernet port per ##FCC.FCC-044, authenticated per ##SEC.SEC-015.
Satisfies: ##SEC.SEC-015 ||

|| Requirement No:BIT-032 || Requirement: The BIT subsystem shall provide health-trend analytics (weekly fault-rate trends, LRU-specific MTBF estimates) via the MBIT interface for scheduled maintenance optimisation. ||

|| Requirement No:BIT-033 || Requirement: The BIT subsystem shall support in-field firmware update for individual LRUs via the MBIT interface, with digital-signature verification per ##SEC.SEC-020 and rollback capability on failed update.
Satisfies: ##SEC.SEC-020 ||

|| Requirement No:BIT-034 || Requirement: The BIT subsystem shall allocate a BIT-dedicated watchdog that, on firmware-hang detection, reports the hang via an independent low-power channel before resetting the LRU. ||

|| Requirement No:BIT-035 || Requirement: The BIT subsystem shall operate across DO-160G §4 Category A2 environmental envelope.
References: DO-160G-4 ||

Header: Interface
|| Requirement No:BIT-036 || Requirement: The BIT subsystem shall publish BIT_STATUS_MSG at 1 Hz on the primary avionics bus with per-LRU health score (0-100), fault count, most recent fault code, and overall-system health. ||

|| Requirement No:BIT-037 || Requirement: The BIT subsystem shall format BIT_STATUS_MSG per the following table.
Table Type: MESSAGE
Table Name or Description: BIT_Status_Msg
Table: BIT_Status_Msg
|Field|Type|Range|
--------------------------------------------------
|system_health|uint8|0-100|
--------------------------------------------------
|per_lru_health|uint8 ×N|0-100|
--------------------------------------------------
|active_faults_count|uint16|0-65535|
--------------------------------------------------
|most_recent_fault|uint32|fault code|
--------------------------------------------------
|most_recent_timestamp|uint64|UTC ns|
--------------------------------------------------
|mbit_in_progress|uint8|0 or 1|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:BIT-038 || Requirement: The BIT subsystem shall map severity levels per the Severity_Map table.
Table Type: MESSAGE
Table Name or Description: Severity_Map
Table: Severity_Map
|Severity|Meaning|Action|
--------------------------------------------------
|CRITICAL|flight-safety impact|notify EMS P1|
--------------------------------------------------
|MAJOR|mission-impact, manageable|notify operator, degrade|
--------------------------------------------------
|MINOR|advisory|log only|
--------------------------------------------------
|INFO|informational|log at 0.1 Hz|
-------------------------------------------------- ||

|| Requirement No:BIT-039 || Requirement: The BIT subsystem shall enforce the LRU test-coverage requirements per the Coverage_Requirements table.
Table Type: MESSAGE
Table Name or Description: Coverage_Requirements
Table: Coverage_Requirements
|LRU Class|PBIT Coverage|CBIT Coverage|
--------------------------------------------------
|FCC (DAL-A)|≥ 99.9 %|≥ 99 %|
--------------------------------------------------
|INS/GPS/ADS (DAL-A)|≥ 99.5 %|≥ 95 %|
--------------------------------------------------
|CDL/COMM/DLNK (DAL-B)|≥ 99 %|≥ 90 %|
--------------------------------------------------
|Payload (DAL-B)|≥ 98 %|≥ 85 %|
-------------------------------------------------- ||

Header: Test
|| Requirement No:BIT-040 || Requirement: PBIT coverage (BIT-006, BIT-039) shall be verified by fault-injection of each class of fault (stuck-at memory, bus fault, sensor stuck, CRC corruption) on the flight-configuration hardware, demonstrating coverage per class ≥ 99 %.
Verifies: BIT-006, BIT-039
References: ARINC 604 ||
