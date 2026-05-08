---
topology: single-node
timeout: 180
pass_criteria: "Every IFoE config MCDI command correctly rejects operations performed in the wrong config phase with EBUSY"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE Config Commands Wrong Phase Error Handling Test

## Purpose

Validates that all IFoE configuration MCDI commands enforce phase restrictions. Each command checks ifoe_manager_get_config_phase() and returns MC_CMD_ERR_EBUSY if not in the required phase. Tests every config command in every wrong phase.

## Category

negative, error-handling

## Prerequisites

- MPIFoE firmware booted
- xncmdclient available

## Steps

1. **[host]** In SYSTEM phase, attempt provider-phase commands:
   ```bash
   xncmdclient -c 'ifoe_set_identity 1 0; quit;'
   xncmdclient -c 'ifoe_set_active_accelerators 0x1; quit;'
   xncmdclient -c 'ifoe_set_config 1 0 0; quit;'
   xncmdclient -c 'ifoe_set_active_network_ports 0x1; quit;'
   ```
   Expected: All return EBUSY (require PROVIDER phase)

2. **[host]** Transition to PROVIDER:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```

3. **[host]** In PROVIDER phase, attempt tenant-phase commands:
   ```bash
   xncmdclient -c 'ifoe_set_enabled_accelerators 0x1; quit;'
   xncmdclient -c 'ifoe_config_crypto AES_GCM_256; quit;'
   ```
   Expected: Both return EBUSY (require TENANT phase)

4. **[host]** In PROVIDER phase, attempt showtime-phase commands:
   ```bash
   xncmdclient -c 'ifoe_set_path_port_map 0 0 2 0 1; quit;'
   ```
   Expected: Returns EBUSY (requires SHOWTIME phase)

5. **[host]** Transition to TENANT:
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```

6. **[host]** In TENANT phase, attempt provider-phase commands:
   ```bash
   xncmdclient -c 'ifoe_set_identity 1 0; quit;'
   xncmdclient -c 'ifoe_set_config 1 0 0; quit;'
   ```
   Expected: Both return EBUSY

7. **[host]** In TENANT phase, attempt showtime-phase commands:
   ```bash
   xncmdclient -c 'ifoe_set_path_port_map 0 0 2 0 1; quit;'
   ```
   Expected: Returns EBUSY

## Expected Result

- Every config command returns EBUSY when executed in wrong phase
- No state corruption from rejected commands
- Firmware remains responsive after all rejections

## Failure Indicators

- Config command succeeds in wrong phase
- Wrong error code returned (not EBUSY)
- State corruption after rejected command
- Firmware crash on phase check

## Cleanup

- Firmware reboot
