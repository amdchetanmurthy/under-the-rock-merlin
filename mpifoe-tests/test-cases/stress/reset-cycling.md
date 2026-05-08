---
topology: single-node
timeout: 600
pass_criteria: "Entity reset completes successfully 10 times, firmware recovers and responds after each reset"
priority: P1
stability: stable
retries: 1
validation_groups: [post-test]
---

# Entity Reset Cycling Stress Test

## Purpose

Validates firmware stability under repeated entity resets. Entity reset exercises the firmware's recovery and re-initialization paths, testing for resource cleanup, state machine correctness, and memory leak resilience across multiple reset cycles.

## Category

stress, error-recovery

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- xncmdclient available on host
- Firmware built with --eftest flag

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| iterations | 10 | 1-50 | Number of reset cycles |
| recovery_wait | 15 | 5-60 | Seconds to wait after reset for firmware recovery |

## Steps

1. **[host]** Record initial firmware state:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Firmware version and phase recorded as baseline

2. **[host]** For each iteration (1 through 10), perform entity reset:
   ```bash
   xncmdclient -c 'entity_reset; quit;'
   ```
   Expected: Reset command accepted

3. **[host]** Wait for firmware to recover:
   ```bash
   sleep 15
   ```

4. **[host]** Verify firmware has recovered:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Firmware responds with same version as baseline

5. **[host]** Re-apply IFoE configuration after reset:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Configuration applied, phase transitions to PROVIDER

6. **[host]** Repeat steps 2-5 for all 10 iterations

7. **[host]** After final iteration, verify full firmware health:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   xncmdclient -c 'enum_ports; quit;'
   ```
   Expected: All checks pass, firmware fully functional

## Expected Result

- All 10 entity resets complete without firmware crash
- Firmware recovers and responds to version query after each reset
- IFoE configuration can be re-applied successfully after each reset
- No degradation in response time across iterations
- Final firmware state is fully functional

## Failure Indicators

- Firmware fails to respond after reset (hung or crashed)
- Firmware version changes unexpectedly after reset
- IFoE configuration fails to apply after reset
- Increasing recovery time across iterations (resource leak)
- Port enumeration fails after reset cycles

## Cleanup

- Ensure firmware is in a usable state:
  ```bash
  xncmdclient -c 'version; quit;'
  xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
  ```
