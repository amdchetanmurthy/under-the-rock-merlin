---
topology: single-node
timeout: 240
pass_criteria: "IFoE DVD telemetry driver initializes, collects, and distributes DVD counters correctly"
priority: P1
stability: stable
validation_groups: [post-test]
---

# IFoE DVD Telemetry Infrastructure Test

## Purpose

Validates the IFoE DVD (Dynamic Voltage and Device) telemetry driver (ifoe_dvd_telem_drv.c, 4 files) which collects hardware-level telemetry from IFoE subsystem components. Tests driver initialization, counter collection from IFoE hardware, and telemetry distribution to the telemetry manager. DVD telemetry provides the low-level counter data that feeds into the overall telemetry pipeline.

## Category

positive, driver, integration

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- Telemetry subsystem initialized
- xncmdclient available

## Setup

1. **[host]** Configure IFoE subsystems:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Verify telemetry subsystem includes DVD counters:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Telemetry info shows DVD telemetry source active

2. **[host]** Select DVD telemetry categories:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_select 0xff; quit;' tlp=0
   ```
   Expected: All categories including DVD telemetry selected

3. **[host]** Enable telemetry collection:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl enable; quit;' tlp=0
   sleep 3
   ```
   Expected: Collection started, DVD counters being sampled

4. **[host]** Generate traffic to produce DVD telemetry data:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe; quit;' tlp=0
   for i in $(seq 1 10); do
     xncmdclient --force-enable-mmap -c 'eftest ifoe_tx_pkt 0; quit;' tlp=0
   done
   xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;' tlp=0
   ```
   Expected: Traffic generated for DVD counter increment

5. **[host]** Read telemetry after traffic:
   ```bash
   sleep 2
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: DVD telemetry counters incremented from traffic

6. **[host]** Verify telemetry collection count advancing:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Collection count > previous check

## Expected Result

- IFoE DVD telemetry driver initialized during boot
- DVD counters collected from IFoE hardware at telemetry intervals
- Counter values increment with IFoE traffic
- DVD telemetry integrated into overall telemetry pipeline
- Collection/distribution cycle works continuously

## Failure Indicators

- Telemetry info shows no DVD telemetry source
- DVD counters remain zero after traffic
- Telemetry collection count not advancing
- Firmware crash during DVD counter read
- DVD telemetry data corrupted in pipeline

## Cleanup

- Disable loopback:
  ```bash
  xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;' tlp=0
  ```
- Disable telemetry:
  ```bash
  xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl disable; quit;' tlp=0
  ```
