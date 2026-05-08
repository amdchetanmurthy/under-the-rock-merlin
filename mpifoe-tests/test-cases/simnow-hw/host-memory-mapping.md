---
topology: single-node
timeout: 180
pass_criteria: "PCIe BAR mapping lifecycle (map/access/unmap) works correctly with proper cleanup"
priority: P1
stability: stable
validation_groups: [post-test]
---

# PCIe BAR Mapping Lifecycle Test

## Purpose

Validates the map_host_mem library (map_host_mem.c, 3 files) which manages host memory mapping via PCIe BAR (Base Address Register). Tests the full mapping lifecycle: address validation, BAR mapping creation, mapped memory access, and unmapping with cleanup. This library is used by MCDI, telemetry, and DMA subsystems for host memory access.

## Category

positive, boundary, driver

## Prerequisites

- Requires MI450 hardware (not SimNow)
- IFoE kernel driver loaded
- PCIe link up with BAR regions accessible
- xncmdclient available

## Steps

1. **[host]** Verify PCIe device is visible and BARs mapped:
   ```bash
   lspci -d 1002: -vvv | grep -A5 "Memory at"
   ```
   Expected: BAR regions visible with correct sizes

2. **[host]** Verify firmware access to host memory via MCDI:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: MCDI response (uses mapped host memory for command/response buffers)

3. **[host]** Test EVQ init (maps host memory for event queue):
   ```bash
   xncmdclient -c 'init_evq 1; quit;'
   ```
   Expected: EVQ initialized (host memory mapped for event delivery)

4. **[host]** Verify EVQ works (host memory accessible):
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Command completion event delivered through mapped EVQ

5. **[host]** Test EVQ cleanup (unmaps host memory):
   ```bash
   xncmdclient -c 'fini_evq 1; quit;'
   ```
   Expected: EVQ finalized, host memory unmapped

6. **[host]** Verify re-mapping works (map/unmap/re-map cycle):
   ```bash
   xncmdclient -c 'init_evq 1; quit;'
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'fini_evq 1; quit;'
   ```
   Expected: Full cycle completes without error

7. **[host]** Test telemetry DMA buffer mapping:
   ```bash
   xncmdclient -c 'ifoe_telemetry_dma_cfg 0; quit;'
   ```
   Expected: Host memory mapped for telemetry DMA

8. **[host]** Verify no memory leaks after multiple map/unmap cycles:
   ```bash
   for i in $(seq 1 10); do
     xncmdclient -c 'init_evq 1; quit;'
     xncmdclient -c 'fini_evq 1; quit;'
   done
   xncmdclient -c 'version; quit;'
   ```
   Expected: All cycles complete, firmware responsive (no resource exhaustion)

## Expected Result

- PCIe BAR mapping correctly translates host physical addresses
- Mapped memory is accessible for read/write operations
- Unmap properly releases resources
- Multiple map/unmap cycles do not leak resources
- Re-mapping after unmap works correctly

## Failure Indicators

- BAR mapping fails (address validation error)
- Access to mapped memory causes fault
- Unmap does not release resources (subsequent map fails)
- Resource exhaustion after repeated map/unmap cycles
- PCIe errors in dmesg during mapping operations

## Cleanup

- Finalize EVQ if still initialized:
  ```bash
  xncmdclient -c 'fini_evq 1; quit;'
  ```
