---
topology: single-node
timeout: 240
pass_criteria: "MMHUB driver maps GPU HBM memory regions and mmhub_helper provides valid local addresses"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MMHUB/HBM GPU Memory Operations Test

## Purpose

Validates the MMHUB driver (mmhub_drv.c, 2 files) and mmhub_helper library (5 files) which manage GPU HBM (High Bandwidth Memory) access from MPIFoE firmware. Tests memory mapping, address translation between local and remote HBM regions, and the blocking allocation path (hbm_helper_get_local_address_blocking). MMHUB is critical for IFoE telemetry buffer allocation and DMA operations.

## Category

positive, driver, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted
- GPU with HBM visible and initialized
- xncmdclient available on host

## Steps

1. **[host]** Verify firmware boot completed (MMHUB init occurs during boot):
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Firmware running (MMHUB initialized during boot sequence)

2. **[host]** Verify telemetry subsystem initialized (uses HBM buffers):
   ```bash
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Telemetry info reports buffer addresses (allocated from HBM)

3. **[host]** Enable telemetry to exercise HBM DMA path:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 2
   ```
   Expected: Telemetry collection starts (DMA from HBM to collection buffers)

4. **[host]** Read telemetry to verify HBM data is accessible:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Non-zero telemetry data (read from HBM)

5. **[host]** Verify firmware stability after HBM operations:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Firmware responsive, uptime advancing

6. **[host]** Check for any HBM-related errors:
   ```bash
   dmesg | grep -i 'hbm\|mmhub\|memory.*error'
   ```
   Expected: No HBM or MMHUB error messages

## Expected Result

- MMHUB driver initializes during boot without errors
- HBM memory regions mapped for firmware use
- mmhub_helper provides valid local addresses for telemetry buffers
- DMA operations to/from HBM complete successfully
- No memory access violations or mapping errors

## Failure Indicators

- Firmware fails to boot (MMHUB init failure)
- Telemetry reports null buffer addresses
- Telemetry data is all zeros (HBM read failure)
- dmesg shows HBM or MMHUB errors
- Firmware crash during HBM access (mapping fault)

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
