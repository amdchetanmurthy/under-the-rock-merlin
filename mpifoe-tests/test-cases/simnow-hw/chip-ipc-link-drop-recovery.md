---
topology: single-node
timeout: 300
pass_criteria: "Chip IPC link drop is detected, queues drain, and HELLO re-establishment recovers communication"
priority: P1
stability: stable
validation_groups: [post-test]
---

# IPC Link Drop Under Load and Recovery Test

## Purpose

Validates the chip_ipc link drop handling and recovery path (chip_ipc.c, 847 lines). Tests handle_link_drop which drains pending command queues, transitions the link state machine from UP to DOWN, and re-initiates the HELLO handshake for recovery. Also tests the arbitrator (chip_ipc_arbitrator.c) behavior during link drop with concurrent senders.

## Category

error-recovery, stress, interaction

## Prerequisites

- Requires SimNow M222 model (dual-MID required)
- MPIFoE firmware booted on both MIDs
- Chip IPC link established (link state = UP)
- xncmdclient available

## Setup

1. **[host]** Boot dual-MID SimNow and verify IPC link:
   ```bash
   /simnow/xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached (implies IPC link established)

## Steps

1. **[host]** Verify dual-MID communication is working:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Both commands succeed (IPC link active)

2. **[host]** Generate IPC traffic load via rapid MCDI commands:
   ```bash
   for i in $(seq 1 20); do
     xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   done
   ```
   Expected: All commands complete (IPC handling load)

3. **[host]** Trigger IPC link drop by injecting fault:
   ```bash
   # Write to IPC control register to simulate link drop
   # (SimNow-specific: force MID1 MP to stall)
   xncmdclient --force-enable-mmap -c 'write32 0x03400044 1; quit;' tlp=0
   sleep 5
   ```
   Expected: Link drop detected, queues begin draining

4. **[host]** Restore IPC link:
   ```bash
   # Release MID1 MP stall
   xncmdclient --force-enable-mmap -c 'write32 0x03400044 0; quit;' tlp=0
   sleep 10
   ```
   Expected: HELLO handshake re-initiates, link recovers

5. **[host]** Verify IPC communication restored:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Commands succeed (IPC link recovered)

6. **[host]** Verify firmware stability:
   ```bash
   xncmdclient --force-enable-mmap -c 'get_uptime; quit;' tlp=0
   ```
   Expected: Firmware responsive, uptime advancing

## Expected Result

- IPC link drop triggers handle_link_drop state transition (UP -> DOWN)
- Pending command queues are drained without memory leaks
- HELLO handshake re-establishes link (DOWN -> HELLO -> STAB -> UP)
- Cross-MID communication resumes after recovery
- Arbitrator does not deadlock during link drop with concurrent senders
- No firmware crash or panic during drop/recovery cycle

## Failure Indicators

- k_panic during link drop (desync assertion failure)
- Commands fail after recovery (link not re-established)
- Firmware hangs during queue drain
- Arbitrator deadlock (concurrent senders stuck)
- Sequence error after recovery (seq_remote mismatch)

## Cleanup

- Verify firmware is responsive:
  ```bash
  xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
  ```
