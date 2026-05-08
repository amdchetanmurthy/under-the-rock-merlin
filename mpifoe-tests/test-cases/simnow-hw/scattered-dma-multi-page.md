---
topology: single-node
timeout: 240
pass_criteria: "Scattered DMA correctly transfers data across multi-page host buffers with proper page boundary handling"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Scattered DMA with Multi-Page Host Buffers Test

## Purpose

Validates the scattered_dma library (scattered_dma.c, 2 files) which performs DMA operations that span multiple non-contiguous host memory pages. Tests scatter-gather list construction, page boundary handling, multi-page DMA transfer completion, and error handling for invalid page addresses. Scattered DMA is used by telemetry distribution and host memory operations.

## Category

positive, boundary, data-integrity

## Prerequisites

- Requires MI450 hardware (not SimNow)
- IFoE kernel driver loaded (provides host memory pages)
- MPIFoE firmware booted
- PCIe DMA path functional
- xncmdclient available

## Steps

1. **[host]** Verify DMA engine initialized (boot self-test):
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Firmware running (DMA self-test passed during boot)

2. **[host]** Configure telemetry DMA with host buffer (exercises scattered DMA):
   ```bash
   xncmdclient -c 'ifoe_telemetry_dma_cfg 0; quit;'
   ```
   Expected: DMA config accepted (page address validated)

3. **[host]** Enable telemetry to trigger DMA transfers:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 5
   ```
   Expected: Multiple DMA transfers to host buffer (1 per second)

4. **[host]** Verify DMA completions via telemetry info:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: DMA transfer count > 0, no DMA errors

5. **[host]** Check for DMA errors in kernel log:
   ```bash
   dmesg | grep -i 'dma.*error\|iommu.*fault\|pcie.*error'
   ```
   Expected: No DMA-related errors

6. **[host]** Verify data integrity in host buffer:
   ```bash
   # Read host buffer via driver interface
   # Verify telemetry data structure is intact across page boundaries
   dmesg | grep -i 'telemetry\|dma.*complete'
   ```
   Expected: No corruption warnings, data readable

7. **[host]** Disable and re-enable to test repeated DMA setup:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
   sleep 1
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 3
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: DMA transfers resume without error

## Expected Result

- Scattered DMA correctly handles multi-page host buffers
- Page boundary crossings do not corrupt data
- DMA completions reported without timeout
- Multiple DMA setup/teardown cycles work correctly
- No IOMMU faults or PCIe errors during DMA

## Failure Indicators

- DMA config rejected (invalid page address)
- DMA transfer timeout
- IOMMU fault in dmesg (address translation failure)
- Data corruption across page boundary
- Firmware crash during DMA operation

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
