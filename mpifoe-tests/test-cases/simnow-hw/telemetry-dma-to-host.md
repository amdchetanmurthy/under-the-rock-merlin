---
topology: single-node
timeout: 300
pass_criteria: "Telemetry DMA delivers counter data to host memory buffer with correct format and incrementing values"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Full DMA Telemetry Distribution to Host Memory Test

## Purpose

Validates the telemetry DMA distribution path (telemetry_distributor.c, telemetry_manager.c). Tests the full flow: observer selection, DMA buffer configuration on host, telemetry collection from hardware counters, and DMA transfer of collected data to host memory. Requires host-side memory allocation for the DMA target buffer.

## Category

positive, integration, data-integrity

## Prerequisites

- Requires MI450 hardware (not SimNow)
- IFoE kernel driver loaded (provides host memory allocation)
- MPIFoE firmware in PROVIDER phase or later
- Host PCIe DMA path functional
- xncmdclient available

## Steps

1. **[host]** Verify telemetry subsystem state:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Telemetry info shows observer count and current state

2. **[host]** Select telemetry observer and configure category mask:
   ```bash
   xncmdclient -c 'ifoe_telemetry_select 0xff; quit;'
   ```
   Expected: Telemetry categories selected (mask 0xff = all categories)

3. **[host]** Configure DMA target buffer in host memory:
   ```bash
   xncmdclient -c 'ifoe_telemetry_dma_cfg 0; quit;'
   ```
   Expected: DMA page address configured, size validated

4. **[host]** Enable telemetry collection:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   ```
   Expected: Telemetry collection started (1s period)

5. **[host]** Wait for multiple collection periods:
   ```bash
   sleep 5
   ```

6. **[host]** Query telemetry info for collection status:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Collection count > 0, DMA transfer count > 0

7. **[host]** Verify host buffer has telemetry data:
   ```bash
   # Read host memory buffer via driver debugfs or sysfs
   # Verify counter values are non-zero and incrementing
   dmesg | grep -i 'telemetry\|telem.*dma'
   ```
   Expected: Telemetry data present in host buffer

8. **[host]** Disable telemetry:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
   ```
   Expected: Collection stopped

9. **[host]** Re-enable and verify counter increment:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 3
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Counters continue incrementing from previous values

## Expected Result

- Observer selection and category mask configuration succeeds
- DMA buffer address validated (page alignment, size checks)
- Telemetry counters collected from hardware at 1s intervals
- DMA transfers data to host buffer without corruption
- Counter values are non-zero and increment across collection periods
- Enable/disable/re-enable cycle works correctly

## Failure Indicators

- Telemetry DMA config fails (invalid host address)
- Host buffer remains empty after collection period
- Counter values all zero (collection not working)
- DMA transfer errors in dmesg
- Firmware crash during DMA operation
- Counters do not increment between collection periods

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
