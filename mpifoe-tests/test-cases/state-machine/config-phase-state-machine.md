---
topology: single-node
timeout: 300
pass_criteria: "All valid config phase transitions succeed and all invalid transitions are rejected with ERANGE or EINVAL"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE Config Phase State Machine Exhaustive Test

## Purpose

Exhaustively tests every transition in the ifoe_manager config phase state machine (ifoe_manager_set_next_config_phase). The valid transitions per source code are:
- SYSTEM -> PROVIDER
- PROVIDER -> TENANT, PROVIDER (self-reset), DIAGNOSTICS
- TENANT -> SHOWTIME, TENANT (self-reset), PROVIDER (backward)
- SHOWTIME -> PROVIDER (backward), TENANT (backward)
- DIAGNOSTICS -> PROVIDER (backward)
Invalid transitions (e.g., SYSTEM -> TENANT, TENANT -> DIAGNOSTICS) must return ERANGE.

## Category

positive, negative, state-machine

## Prerequisites

- MPIFoE firmware freshly booted (SYSTEM phase)
- xncmdclient available
- BIOS config applied for station setup

## Steps

1. **[host]** Verify starting in SYSTEM phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: SYSTEM

2. **[host]** Test invalid: SYSTEM -> TENANT (must fail):
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```
   Expected: ERANGE error

3. **[host]** Test invalid: SYSTEM -> SHOWTIME (must fail):
   ```bash
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: ERANGE error

4. **[host]** Test valid: SYSTEM -> PROVIDER:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Success, phase now PROVIDER

5. **[host]** Test self-reset: PROVIDER -> PROVIDER:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Success, snapshot restored, phase still PROVIDER

6. **[host]** Test valid: PROVIDER -> DIAGNOSTICS:
   ```bash
   xncmdclient -c 'ifoe_next_phase DIAGNOSTICS; quit;'
   ```
   Expected: Success

7. **[host]** Test valid: DIAGNOSTICS -> PROVIDER (backward):
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Success

8. **[host]** Test valid: PROVIDER -> TENANT:
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```
   Expected: Success

9. **[host]** Test invalid: TENANT -> DIAGNOSTICS (must fail):
   ```bash
   xncmdclient -c 'ifoe_next_phase DIAGNOSTICS; quit;'
   ```
   Expected: ERANGE error

10. **[host]** Test self-reset: TENANT -> TENANT:
    ```bash
    xncmdclient -c 'ifoe_next_phase TENANT; quit;'
    ```
    Expected: Success

11. **[host]** Test valid: TENANT -> SHOWTIME:
    ```bash
    xncmdclient -c 'ifoe_next_phase MISSION; quit;'
    ```
    Expected: Success

12. **[host]** Test invalid: SHOWTIME -> DIAGNOSTICS (must fail):
    ```bash
    xncmdclient -c 'ifoe_next_phase DIAGNOSTICS; quit;'
    ```
    Expected: ERANGE error

13. **[host]** Test valid: SHOWTIME -> TENANT (backward):
    ```bash
    xncmdclient -c 'ifoe_next_phase TENANT; quit;'
    ```
    Expected: Success

14. **[host]** Test valid: from TENANT -> PROVIDER (backward):
    ```bash
    xncmdclient --force-enable-mmap -c 'ifoe_next_phase PROVIDER; quit;' tlp=0
    ```
    Expected: Success

## Expected Result

- All 8 valid transitions (including self-resets and backward transitions) succeed
- All invalid transitions return ERANGE or EINVAL
- Config snapshot is taken on forward transitions
- Config snapshot is restored on backward transitions and self-resets
- Privilege masks updated correctly on PROVIDER -> TENANT boundary

## Failure Indicators

- Valid transition returns error
- Invalid transition succeeds
- Phase desync between MIDs (k_panic in source)
- Datapath hooks not invoked during state changes
- Config snapshot not restored on backward transition

## Cleanup

- Firmware reboot to return to SYSTEM phase
