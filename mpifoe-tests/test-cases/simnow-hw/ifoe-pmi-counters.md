---
topology: single-node
timeout: 240
pass_criteria: "IFoE PMI counters accessible, incrementing with traffic, and correctly mapped per subsystem"
priority: P1
stability: stable
validation_groups: [post-test]
---

# IFoE Performance Monitor Interface Counters Test

## Purpose

Validates the IFoE PMI driver (ifoe_pmi.c, 2 files) which provides access to hardware performance monitoring counters. PMI counters track TX/RX packets, bytes, errors, and other datapath statistics at the IFoE subsystem level. Tests counter initialization, increment behavior with traffic, and per-subsystem counter isolation.

## Category

positive, driver, performance

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- xncmdclient available

## Setup

1. **[host]** Configure IFoE subsystems:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Enable telemetry to start PMI counter collection:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl enable; quit;' tlp=0
   ```
   Expected: Telemetry enabled (PMI counters being read)

2. **[host]** Read baseline telemetry info:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Counter values reported per subsystem

3. **[host]** Generate traffic via loopback to increment counters:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe; quit;' tlp=0
   for i in $(seq 1 10); do
     xncmdclient --force-enable-mmap -c 'eftest ifoe_tx_pkt 0; quit;' tlp=0
   done
   xncmdclient --force-enable-mmap -c 'eftest ifoe_rx_pkt 0; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;' tlp=0
   ```
   Expected: Traffic generated through subsystem 0

4. **[host]** Wait for PMI collection period:
   ```bash
   sleep 3
   ```

5. **[host]** Read telemetry info after traffic:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: TX/RX counters for subsystem 0 incremented from baseline

6. **[host]** Verify subsystem 1 counters unchanged (isolation):
   ```bash
   # Subsystem 1 should have no traffic-related counter increment
   # unless inter-subsystem traffic occurred
   ```
   Expected: Subsystem 1 counters reflect only its own traffic (isolation verified)

7. **[host]** Disable and re-enable telemetry:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl disable; quit;' tlp=0
   sleep 1
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl enable; quit;' tlp=0
   sleep 2
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Counters continue from previous values (not reset)

## Expected Result

- PMI counters initialized to zero (or baseline) at subsystem init
- Counter values increment with IFoE traffic
- Counters are per-subsystem (traffic on SS0 does not affect SS1 counters)
- Telemetry disable/re-enable does not reset counters
- Counter values accessible via telemetry info command

## Failure Indicators

- Counters remain zero after traffic (PMI not reading hardware)
- Counter values do not increment (stuck counters)
- Subsystem counter cross-contamination (isolation broken)
- Telemetry info returns error after counter operations
- Firmware crash during PMI register access

## Cleanup

- Disable loopback:
  ```bash
  xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;' tlp=0
  ```
- Disable telemetry:
  ```bash
  xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl disable; quit;' tlp=0
  ```
