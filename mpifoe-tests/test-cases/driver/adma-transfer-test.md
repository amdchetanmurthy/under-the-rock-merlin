---
topology: single-node
timeout: 60
pass_criteria: "ADMA DMA transfers complete without error for both reliable and unreliable queues"
priority: P1
stability: stable
validation_groups: [post-test]
---

# ADMA DMA Transfer Driver Test

## Purpose

Validates the ADMA DMA driver (amd_smu_adma.c) and DMA library (dma.c). Tests boot-time DMA self-tests (test_dma and test_dma_lib) which validate DMA_QUEUE_ID_RELIABLE and DMA_QUEUE_ID_UNRELIABLE transfer paths. The DMA subsystem is critical for MCDI command sync, telemetry distribution, and inter-MID data transfer.

## Category

positive, driver

## Prerequisites

- MPIFoE firmware booted
- Tracelog access for self-test results

## Steps

1. **[host]** Verify DMA self-test passed at boot:
   ```bash
   # Check tracelog for POSTCODE_SELF_TEST_PASS instance 2 and 3
   # Should see: "DMA Test PASS" and "DMA Lib Test PASS"
   ```
   Expected: Both DMA tests PASS

2. **[host]** Exercise DMA via MCDI command (requires host DMA):
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Success (MCDI sync uses DMA)

3. **[host]** Verify DMA blocking transfer works for telemetry:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info 0; quit;'
   ```
   Expected: Telemetry info returned (uses dma_transfer_blocking)

## Expected Result

- test_dma returns 0 (DMA hardware test passes)
- test_dma_lib returns 0 (DMA library wrapper test passes)
- Blocking transfers complete without timeout
- Both reliable and unreliable queues functional

## Failure Indicators

- POSTCODE_SELF_TEST_FAIL instance 2 or 3
- DMA transfer timeout
- Data corruption in DMA'd data
- dma_transfer_blocking returns non-zero

## Cleanup

- None required
