---
topology: single-node
timeout: 240
pass_criteria: "Netport DVD telemetry driver collects port-level telemetry counters correctly"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Netport DVD Telemetry Driver Test

## Purpose

Validates the netport DVD telemetry driver (netport_dvd_telem_drv.c, 4 files) which collects port-level telemetry from the network manager. Tests driver initialization, counter collection per-port, and integration with the telemetry manager. Netport DVD telemetry covers port statistics (link events, error counts, MAC stats) distinct from IFoE DVD telemetry.

## Category

positive, driver, integration

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- Network ports enumerated
- xncmdclient available

## Setup

1. **[host]** Configure IFoE subsystems:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached with ports enumerated

## Steps

1. **[host]** Verify ports enumerated:
   ```bash
   xncmdclient --force-enable-mmap -c 'enum_ports; quit;' tlp=0
   ```
   Expected: Ports listed with correct count for port mode

2. **[host]** Enable telemetry (includes netport DVD):
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_select 0xff; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl enable; quit;' tlp=0
   sleep 3
   ```
   Expected: Telemetry enabled with netport counters

3. **[host]** Query telemetry info for netport counters:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Netport telemetry section present with per-port counters

4. **[host]** Generate port activity to increment counters:
   ```bash
   xncmdclient --force-enable-mmap -c 'link_state 0; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'mac_state 0; quit;' tlp=0
   ```
   Expected: Port queries generate some counter activity

5. **[host]** Read telemetry again and verify counters changed:
   ```bash
   sleep 2
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Netport telemetry counters updated

6. **[host]** Verify per-port counter isolation:
   ```bash
   # Port 0 activity should not affect port 1 counters
   xncmdclient --force-enable-mmap -c 'link_state 1; quit;' tlp=0
   ```
   Expected: Port counters are independent

## Expected Result

- Netport DVD telemetry driver initialized during boot
- Per-port telemetry counters collected at telemetry intervals
- Port activity reflected in counter values
- Counters are per-port isolated
- Netport telemetry integrated into overall telemetry pipeline

## Failure Indicators

- Netport telemetry section missing from telemetry info
- Per-port counters remain zero despite activity
- Counter cross-contamination between ports
- Firmware crash during netport counter access

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl disable; quit;' tlp=0
  ```
