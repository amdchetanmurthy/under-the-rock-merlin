---
topology: single-node
timeout: 60
pass_criteria: "ifoe_get_config returns a valid configuration matching the applied BIOS config"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE Configuration Verification

## Purpose

Validates that the IFoE subsystem configuration matches what was applied during BIOS configuration. This ensures the port mode, subsystem mask, and other configuration parameters were accepted and applied correctly by the firmware.

## Category

positive

## Prerequisites

- MPIFoE firmware booted
- IFoE BIOS configuration applied (e.g., `eftest ifoe_bios_cfg 4x200 0 3ffff 0`)
- Firmware transitioned to PROVIDER phase or later
- xncmdclient available on host

## Steps

1. **[host]** Query the current IFoE configuration:
   ```bash
   xncmdclient -c 'ifoe_get_config; quit;'
   ```
   Expected: Returns configuration structure with port mode, subsystem mask, and flags

2. **[host]** Verify the port mode matches the applied BIOS config:
   Expected: Port mode field matches the configured mode (e.g., 4x200)

3. **[host]** Check the subsystem enable mask:
   Expected: Subsystem mask matches what was configured (e.g., 0x3ffff for all 18 subsystems)

4. **[host]** Query the current phase to confirm config was applied:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Phase is PROVIDER or later (not stuck in SYSTEM)

## Expected Result

- ifoe_get_config returns a valid configuration structure
- Port mode matches the BIOS configuration that was applied
- Subsystem enable mask reflects the requested subsystems
- Firmware is in PROVIDER phase or later, confirming the config was accepted

## Failure Indicators

- ifoe_get_config returns error or empty response
- Port mode does not match what was configured
- Subsystem mask is 0 or does not match the requested mask
- Firmware stuck in SYSTEM phase (config not applied)
- Unexpected flags or configuration values

## Cleanup

- None required (read-only inspection)
