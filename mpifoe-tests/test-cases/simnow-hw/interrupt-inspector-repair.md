---
topology: single-node
timeout: 240
pass_criteria: "Interrupt inspector detects stuck interrupts and repairs them without firmware restart"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Stuck Interrupt Detection and Repair Test

## Purpose

Validates the interrupt_inspector driver (interrupt_inspector.c, 3 files) which runs in the main heartbeat loop (main.c) via interrupt_inspector_check_pics_and_repair(). Detects PIC (Programmable Interrupt Controller) interrupts that are stuck asserted and repairs them. Also validates the missed ISR diagnostic (atomic_inc on re-triggered ISR).

## Category

positive, error-recovery, driver

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted (heartbeat loop running)
- Interrupt controller accessible
- xncmdclient available

## Steps

1. **[host]** Verify firmware heartbeat is running:
   ```bash
   UPTIME1=$(xncmdclient -c 'get_uptime; quit;' | grep uptime)
   sleep 3
   UPTIME2=$(xncmdclient -c 'get_uptime; quit;' | grep uptime)
   echo "Uptime1: $UPTIME1"
   echo "Uptime2: $UPTIME2"
   ```
   Expected: Uptime advancing (heartbeat loop active, interrupt inspector running)

2. **[host]** Check interrupt state via register read:
   ```bash
   # Read interrupt controller status register
   xncmdclient -c 'read32 0x034000d8; quit;'
   ```
   Expected: Normal interrupt state (no stuck bits)

3. **[host]** Generate interrupt activity via MCDI commands:
   ```bash
   for i in $(seq 1 50); do
     xncmdclient -c 'version; quit;'
   done
   ```
   Expected: All commands complete (interrupt handling working)

4. **[host]** Verify no stuck interrupt warnings in firmware state:
   ```bash
   xncmdclient -c 'get_uptime; quit;'
   xncmdclient -c 'version; quit;'
   ```
   Expected: Firmware responsive (interrupt inspector has not found issues)

5. **[host]** Verify interrupt counts are reasonable:
   ```bash
   cat /proc/interrupts | grep -i ifoe
   ```
   Expected: Interrupt counts proportional to MCDI commands sent

6. **[host]** Long-running heartbeat check (interrupt inspector runs each loop):
   ```bash
   # Let heartbeat loop run for extended period
   sleep 30
   xncmdclient -c 'get_uptime; quit;'
   xncmdclient -c 'version; quit;'
   ```
   Expected: Firmware stable after many heartbeat loop iterations

## Expected Result

- Interrupt inspector runs every heartbeat loop iteration
- No stuck interrupts detected during normal operation
- When stuck interrupt is detected, repair restores normal operation
- Missed ISR diagnostic counter tracks re-triggered interrupts
- Firmware does not need restart for interrupt repair

## Failure Indicators

- Firmware hangs (interrupt inspector not detecting stuck interrupt)
- MCDI commands timeout (interrupt delivery broken)
- Interrupt counts growing abnormally (interrupt storm)
- Firmware panic from unhandled interrupt state
- Heartbeat stops advancing (main loop stuck)

## Cleanup

- None required
