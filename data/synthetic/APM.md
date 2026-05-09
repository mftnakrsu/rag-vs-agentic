#Requirement: REQ-APM
PROJECT NAME: AeroSys Common Avionics Core
MODULE NAME: APM
BASELINE: v1.6.0
ABSOLUTE PATH: /AeroSys/Common/APM

Header: PURPOSE
|| Requirement No:APM-001 || Requirement: This document specifies the Auxiliary Power Module (APM) and Battery requirements for the AeroSys Dynamics common power architecture, applicable to Stratos-7, AeroLynx-X2, Skyrunner-T1, and Nimbus-C3. The APM control software shall be developed at DO-178C DAL-A on Stratos-7 and AeroLynx-X2, and DAL-B on Skyrunner-T1 and Nimbus-C3. ||

Header: SCOPE
|| Requirement No:APM-002 || Requirement: This module covers the main Li-ion battery (or valve-regulated lead-acid on Skyrunner-T1), battery management system (BMS), optional APU (Stratos-7, AeroLynx-X2, Nimbus-C3), and thermal management of battery cells in cooperation with ##TCS.TCS-012. It excludes primary power distribution (##PWR.PWR-002) and emergency bus switching (##EPS.EPS-001). ||

Header: REFERENCES
|| Requirement No:APM-003 || Requirement: The governing references are: MIL-STD-704F, RTCA DO-311A (Rechargeable Lithium Batteries and Battery Systems), RTCA DO-160G, RTCA DO-178C, RTCA DO-254, UN 38.3 (lithium battery transport), EUROCAE ED-137 (UAS power guidance). ||

Header: GLOSSARY
|Abbreviation|Definition|
--------------------------------------------------
|APM|Auxiliary Power Module|
--------------------------------------------------
|BMS|Battery Management System|
--------------------------------------------------
|APU|Auxiliary Power Unit|
--------------------------------------------------
|SoC|State of Charge|
--------------------------------------------------
|SoH|State of Health|
--------------------------------------------------
|DoD|Depth of Discharge|
--------------------------------------------------
|VRLA|Valve-Regulated Lead-Acid|
--------------------------------------------------
|LTO|Lithium Titanate Oxide (chemistry)|
--------------------------------------------------
|NMC|Nickel Manganese Cobalt (chemistry)|
--------------------------------------------------

Header: REQUIREMENTS

Header: Modes
|| Requirement No:APM-004 || Requirement: The APM shall support the following operational modes:
    a) OFF
    b) CHARGING (connected to primary bus, charging battery)
    c) STANDBY (charged, no discharge)
    d) DISCHARGE (supplying bus load)
    e) APU_START (APU cranking and stabilisation)
    f) APU_RUNNING (APU providing primary bus power)
    g) FAULT ||

|| Requirement No:APM-005 || Requirement: In CHARGING mode, the APM shall charge the main battery at the manufacturer-specified CC/CV profile with charging current limited to 0.5C (where C is rated capacity) for standard cells, completing full charge within 4 h from 20 % SoC.
References: DO-311A ||

|| Requirement No:APM-006 || Requirement: In DISCHARGE mode, the APM shall deliver the rated discharge current to the essential and emergency buses while maintaining battery voltage within 22 V to 29 V until SoC reaches the configured low-voltage cutoff (default 10 %). ||

|| Requirement No:APM-007 || Requirement: On APU_START (Stratos-7, AeroLynx-X2, Nimbus-C3 only), the APM shall command APU ignition, monitor cranking RPM, and transfer load from battery to APU within 30 s of start command, aborting on any failure indication. ||

|| Requirement No:APM-008 || Requirement: The APM shall transition to FAULT within 50 ms on any of: battery over-voltage (> 32 V), battery under-voltage sustained > 18 V cutoff, cell-imbalance > 200 mV, cell-temperature > 65 °C, or BMS self-test failure.
Satisfies: ##BIT.BIT-025 ||

Header: General
|| Requirement No:APM-009 || Requirement: The main battery capacity shall be sized to sustain the essential-bus and emergency-bus load (per PWR_Load_Shed levels 4-6 of ##PWR.PWR-032) for at least 30 min at 70 % DoD, supporting the return-to-base profile per ##AUTO.AUTO-022.
Satisfies: ##AUTO.AUTO-022, ##PWR.PWR-032 ||

|| Requirement No:APM-010 || Requirement: The APM shall supply the emergency bus through a dedicated discharge contactor with transfer time ≤ 50 ms from the trip of the last generator per ##PWR.PWR-007.
Satisfies: ##PWR.PWR-007 ||

|| Requirement No:APM-011 || Requirement: The APM shall operate with Li-ion (NMC or LTO) cells on Stratos-7, AeroLynx-X2, and Nimbus-C3, and VRLA on Skyrunner-T1, with chemistry selection frozen at platform design level. ||

|| Requirement No:APM-012 || Requirement: The BMS shall monitor every cell voltage, cell temperature (one sensor per cell or cell block up to 4 cells), and pack current at a rate ≥ 10 Hz with voltage resolution ≤ 5 mV, temperature resolution ≤ 0.5 °C, and current resolution ≤ 1 A.
References: DO-311A ||

|| Requirement No:APM-013 || Requirement: The BMS shall perform passive or active cell balancing whenever any cell voltage exceeds the pack-average by more than 50 mV during charging, with a target maximum cell-to-cell imbalance of 50 mV at full charge. ||

|| Requirement No:APM-014 || Requirement: The BMS shall protect against cell over-voltage (trip at 4.25 V/cell for NMC, 2.9 V/cell for LTO), cell under-voltage (cutoff at 2.8 V/cell NMC, 1.8 V/cell LTO), over-temperature (trip at 65 °C), and over-current (trip at 3C for > 100 ms).
References: DO-311A ||

|| Requirement No:APM-015 || Requirement: The BMS shall estimate State of Charge (SoC) at 1 Hz with accuracy ±3 % and State of Health (SoH) at power-on and at 1 h intervals thereafter with accuracy ±5 %, publishing both to the PWR subsystem per ##PWR.PWR-028.
Satisfies: ##PWR.PWR-028 ||

|| Requirement No:APM-016 || Requirement: The APM shall log every charge/discharge cycle with start/stop SoC, peak current, peak temperature, and total Ah throughput, retained in non-volatile memory for the entire battery service life. ||

|| Requirement No:APM-017 || Requirement: The APM shall detect thermal-runaway precursors (cell-temperature rise rate > 5 °C/min, or cell-voltage drop > 500 mV in 10 s while charging) and isolate the affected cell block within 200 ms, alert the TCS per ##TCS.TCS-012 and the operator per ##HMI.HMI-110.
Satisfies: ##TCS.TCS-012 ||

|| Requirement No:APM-018 || Requirement: The APM shall support thermal conditioning in cooperation with the TCS, maintaining cell temperatures 0 °C to 45 °C during charging and -20 °C to 60 °C during discharge per DO-311A.
References: DO-311A ||

|| Requirement No:APM-019 || Requirement: On Stratos-7, AeroLynx-X2, and Nimbus-C3, the APU shall be a gas-turbine-driven generator providing ≥ 5 kW output on a secondary ESS-backup bus, started on demand and shut down with operator command. ||

|| Requirement No:APM-020 || Requirement: The APU start sequence shall complete within 30 s from start command to rated-load capability at sea-level ISA conditions, extending to 60 s at 44 000 ft (Stratos-7).
Satisfies: ##PWR.PWR-029 ||

|| Requirement No:APM-021 || Requirement: The APM shall inhibit APU start below battery SoC of 20 % and shall delay APU start 2 s after sensing main-generator failure to allow battery voltage to stabilise. ||

|| Requirement No:APM-022 || Requirement: The APM shall support in-flight restart of the APU up to 40 000 ft (Stratos-7), with restart-success probability ≥ 95 % over 50 attempts under DO-160G §4 Category A2 temperature range. ||

|| Requirement No:APM-023 || Requirement: The APM shall monitor APU health (N1 RPM, EGT, oil pressure) at 5 Hz and shut down APU on any parameter exceedance per the APU_Limits table (APM-036), logging the event to ##FDR.FDR-030. ||

|| Requirement No:APM-024 || Requirement: The APM shall ensure battery isolation during aircraft transit, maintenance, and storage by a ground-selectable disconnect, compliant with UN 38.3 and IATA dangerous-goods handling.
References: UN 38.3 ||

|| Requirement No:APM-025 || Requirement: The APM shall protect battery cells against over-discharge during storage by automatic cell-protection activation if pack voltage falls below the storage-floor threshold (platform-configurable). ||

|| Requirement No:APM-026 || Requirement: The APM shall support an in-flight self-test capability, reporting SoH, cell-balance status, internal-resistance (IR) trend, and BMS health to the BIT function per ##BIT.BIT-028 at 0.1 Hz.
Satisfies: ##BIT.BIT-028 ||

|| Requirement No:APM-027 || Requirement: The APM shall operate across DO-160G §4 Category A2 environmental envelope and shall meet DO-311A mechanical shock, vibration, and thermal-runaway propagation containment requirements.
References: DO-311A, DO-160G-4 ||

|| Requirement No:APM-028 || Requirement: The APM shall contain any single-cell thermal runaway within the battery enclosure for at least 10 minutes without propagation to adjacent cells, per DO-311A propagation-containment test.
References: DO-311A ||

|| Requirement No:APM-029 || Requirement: The APM shall provide a ground-maintenance interface (RS-422 at 115 200 bps) for battery diagnostics, firmware update, and calibration, with access controlled per ##SEC.SEC-015.
Satisfies: ##SEC.SEC-015 ||

|| Requirement No:APM-030 || Requirement: The APM shall report to ##FDR.FDR-030 battery temperatures, SoC, cell-imbalance, and any fault word at 1 Hz, with cell-level detail captured at 0.1 Hz. ||

|| Requirement No:APM-031 || Requirement: The APM shall be mounted consistent with ##STR.STR-030 structural allocations, with mounting-bracket stiffness supporting 6 g shock per DO-160G §7 Category B.
References: DO-160G-7 ||

Header: Interface
|| Requirement No:APM-032 || Requirement: The APM shall publish APM_STATUS_MSG at 1 Hz on the primary avionics bus per the APM_Status_Msg table (APM-034), and cell-level detail at 0.1 Hz on a dedicated telemetry channel.
References: MIL-STD-1553B, ARINC 429 ||

|| Requirement No:APM-033 || Requirement: The APM shall accept commands from ##PWR.PWR-027 (charge enable/disable, APU start/stop, cell-balance override) authenticated per ##SEC.SEC-010. ||

|| Requirement No:APM-034 || Requirement: The APM shall format APM_STATUS_MSG per the table below.
Table Type: MESSAGE
Table Name or Description: APM_Status_Msg
Table: APM_Status_Msg
|Field|Type|Range|Resolution|
--------------------------------------------------
|mode|uint8|enum {OFF,CHG,STBY,DISCHG,APU_START,APU_RUN,FAULT}|integer|
--------------------------------------------------
|soc|uint8|0-100 %|1 %|
--------------------------------------------------
|soh|uint8|0-100 %|1 %|
--------------------------------------------------
|pack_voltage|float32|0-35 V|0.01 V|
--------------------------------------------------
|pack_current|float32|-300 to +300 A|0.1 A|
--------------------------------------------------
|max_cell_v,min_cell_v|float32 ×2|0-5 V|1 mV|
--------------------------------------------------
|max_cell_t,min_cell_t|float32 ×2|-40 to +80 °C|0.1 °C|
--------------------------------------------------
|apu_n1,apu_egt|float32 ×2|0-110 %, 0-900 °C|0.1|
--------------------------------------------------
|cycles_total|uint32|0 to 2^32-1|integer|
--------------------------------------------------
|fault_word|uint32|bitmask|bit|
-------------------------------------------------- ||

Header: Tables
|| Requirement No:APM-035 || Requirement: The APM shall enforce battery cell limits per the Battery_Cell_Limits table.
Table Type: MESSAGE
Table Name or Description: Battery_Cell_Limits
Table: Battery_Cell_Limits
|Chemistry|V_min|V_max|I_max (charge)|I_max (discharge)|T_op|
--------------------------------------------------
|NMC (STR7/ALX2/NBC3)|2.8 V|4.25 V|0.5C|3C|-20 to +60 °C|
--------------------------------------------------
|LTO (alternate STR7)|1.8 V|2.9 V|2C|6C|-30 to +65 °C|
--------------------------------------------------
|VRLA (SKT1)|10.5 V (6-cell)|14.4 V (6-cell)|0.1C|1C|-20 to +50 °C|
-------------------------------------------------- ||

|| Requirement No:APM-036 || Requirement: The APM shall enforce the APU operational limits per the APU_Limits table, shutting down the APU on any exceedance persisting > 5 s (N1) or > 200 ms (EGT redline).
Table Type: MESSAGE
Table Name or Description: APU_Limits
Table: APU_Limits
|Parameter|Nominal|Warning|Redline|Action|
--------------------------------------------------
|N1|98-102 %|< 90 % or > 105 %|> 107 %|auto-shutdown|
--------------------------------------------------
|EGT (operating)|500 °C|650 °C|750 °C|auto-shutdown|
--------------------------------------------------
|EGT (starting)|peak 780 °C|n/a|830 °C|abort start|
--------------------------------------------------
|Oil pressure|> 25 psig|< 20 psig|< 15 psig|auto-shutdown|
--------------------------------------------------
|Oil temp|70-110 °C|> 135 °C|> 150 °C|auto-shutdown|
-------------------------------------------------- ||

Header: Test
|| Requirement No:APM-037 || Requirement: Battery discharge endurance (APM-009) shall be verified by a laboratory discharge test at the RTB-load profile over 30 min, demonstrating terminal voltage remains above cutoff and DoD does not exceed 70 %.
Verifies: APM-009
References: DO-311A ||

|| Requirement No:APM-038 || Requirement: Thermal-runaway containment (APM-028) shall be verified per DO-311A nail-penetration test on a representative cell within the flight-configuration enclosure, confirming no propagation to adjacent cells over 10 min.
Verifies: APM-028
References: DO-311A ||

|| Requirement No:APM-039 || Requirement: APU start-time (APM-020) shall be verified on the iron-bird at sea level and at altitude simulation (44 000 ft for Stratos-7), demonstrating start-to-rated-load ≤ 30 s and ≤ 60 s respectively.
Verifies: APM-020 ||

|| Requirement No:APM-040 || Requirement: Cell-balancing accuracy (APM-013) shall be verified by charging a cell-imbalanced pack (initial 200 mV spread) and demonstrating balancing reduces the spread to ≤ 50 mV at full charge.
Verifies: APM-013 ||
