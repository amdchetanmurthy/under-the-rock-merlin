---
topology: single-node
timeout: 120
pass_criteria: "EX driver initializes hardware, telemetry collection returns valid counter values, and RAS error injection works"
priority: P2
stability: stable
validation_groups: [post-test]
---

# EX Driver Initialization and Telemetry Test

## Purpose

Validates the EX (Exchange) driver (ex_drv.c, ex.c, ex_hal.c, ex_telemetry.c, ex_ras_drv.c). The EX block handles MR-PIO (management read/write PIO) traffic between the host and IFoE. Tests initialization, telemetry counter collection, and RAS error reporting.

## Category

positive, driver

## Prerequisites

- MPIFoE firmware in PROVIDER phase or later
- EX hardware out of reset (datapath hook has run)
- xncmdclient available

## Steps

1. **[host]** Verify EX is out of reset after datapath transition:
   ```bash
   # hardware_datapath_hook takes EX out of reset on DOWN->ETHERNET
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: PROVIDER or later (EX should be initialized)

2. **[host]** Read EX telemetry counters:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info 0; quit;'
   ```
   Expected: Telemetry category includes EX counters

3. **[host]** Verify EX RAS driver is registered:
   ```bash
   # RAS conv table has 7 EX errors (MR_PIO S2R/R2S ECC, parity, TS_LOG, AXI2PRP)
   # ras_drv section should contain EX driver entries
   ```

4. **[host]** Inject an EX ECC error via RAS subsystem:
   ```bash
   # Inject COMP_EX element 0 (MR_PIO_S2R_ECC)
   ```
   Expected: Error injected, MCA report generated

## Expected Result

- EX driver initializes without error
- Telemetry counters readable and valid
- RAS error injection and clean work for all 7 EX error types
- MCA report contains correct EX module ID

## Failure Indicators

- EX initialization failure
- Telemetry counters all zero
- RAS inject returns ENODEV or ENOTSUP
- MCA report missing or wrong module

## Cleanup

- Clean any injected errors
