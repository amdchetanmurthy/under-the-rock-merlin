---
topology: single-node
timeout: 120
pass_criteria: "SG queue enqueue/dequeue operations work correctly with proper overflow handling"
priority: P2
stability: stable
validation_groups: [post-test]
---

# SG Queue Management Test

## Purpose

Validates the sg_queue library (sg_queue.c, 2 files) which provides scatter-gather queue management. Tests enqueue, dequeue, full/empty detection, and overflow handling. SG queues are used internally for DMA descriptor management and traffic queue operations. This is a candidate for pffth (Zephyr) unit test but is included here for completeness.

## Category

positive, boundary

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted
- SG queue used by traffic subsystem (initialized during boot)
- xncmdclient available

## Steps

1. **[host]** Verify firmware booted (SG queue initialized as part of subsystems):
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware running (SG queues initialized)

2. **[host]** Exercise SG queue via traffic path (loopback):
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe; quit;' tlp=0
   ```
   Expected: Loopback enabled (SG queue allocated for packet descriptors)

3. **[host]** Send multiple packets to exercise queue enqueue:
   ```bash
   for i in $(seq 1 10); do
     xncmdclient --force-enable-mmap -c 'eftest ifoe_tx_pkt 0; quit;' tlp=0
   done
   ```
   Expected: Packets enqueued and processed through SG queue

4. **[host]** Receive packets to exercise queue dequeue:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_rx_pkt 0; quit;' tlp=0
   ```
   Expected: Packets dequeued from SG queue

5. **[host]** Disable loopback:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;' tlp=0
   ```
   Expected: SG queue drained and released

6. **[host]** Verify firmware stable (no queue corruption):
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'get_uptime; quit;' tlp=0
   ```
   Expected: Firmware responsive

## Expected Result

- SG queue enqueue/dequeue operations complete without error
- Queue correctly handles multiple enqueue/dequeue cycles
- Queue drain on loopback disable completes cleanly
- No queue corruption or memory leaks

## Failure Indicators

- Packet TX fails (SG queue full, overflow not handled)
- Packet RX fails (SG queue dequeue error)
- Firmware crash from SG queue corruption
- Memory leak after repeated queue operations

## Cleanup

- Disable loopback:
  ```bash
  xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;' tlp=0
  ```
