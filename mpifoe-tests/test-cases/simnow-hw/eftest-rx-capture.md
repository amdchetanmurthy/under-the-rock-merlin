---
topology: back-to-back
timeout: 300
pass_criteria: "RX capture mode captures packets from active traffic with correct station filtering"
priority: P2
stability: stable
validation_groups: [post-test]
---

# RX Capture Mode with Active Traffic Test

## Purpose

Validates the eftest RX capture functionality (ifoe_ss_eftest.c, eftest_cmds.c) which allows capturing received packets for inspection. Tests set/get rx_capture_stations, packet capture during active traffic, and capture buffer management. RX capture is a diagnostic tool for debugging datapath issues on hardware.

## Category

positive, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted with --eftest flag
- Firmware in MISSION phase with active stations
- Back-to-back link up between two MI450 nodes
- xncmdclient available on both hosts

## Setup

1. **[server]** Configure IFoE to MISSION phase:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: MISSION phase with active stations

2. **[client]** Configure matching IFoE:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: MISSION phase

## Steps

1. **[server]** Enable RX capture on station 0:
   ```bash
   xncmdclient -c 'eftest ifoe_rx_capture 0 enable; quit;'
   ```
   Expected: RX capture enabled for station 0

2. **[client]** Generate traffic via loopback or L2Ping:
   ```bash
   xncmdclient -c 'ifoe_ping_config 0 0 20; quit;'
   xncmdclient -c 'ifoe_ping_start 0 0; quit;'
   sleep 5
   ```
   Expected: Traffic flowing through station 0

3. **[server]** Check captured packets:
   ```bash
   xncmdclient -c 'eftest ifoe_rx_pkt 0; quit;'
   ```
   Expected: Captured packet data available for inspection

4. **[client]** Stop traffic:
   ```bash
   xncmdclient -c 'ifoe_ping_poll 0; quit;'
   xncmdclient -c 'ifoe_ping_stop 0; quit;'
   ```
   Expected: Traffic stopped

5. **[server]** Disable RX capture:
   ```bash
   xncmdclient -c 'eftest ifoe_rx_capture 0 disable; quit;'
   ```
   Expected: RX capture disabled

6. **[server]** Verify normal datapath restored:
   ```bash
   xncmdclient -c 'ifoe_enum_stations; quit;'
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: Stations in normal state (capture mode fully disabled)

## Expected Result

- RX capture mode enables packet inspection on specified station
- Captured packets contain valid IFoE-encapsulated data
- Capture mode correctly filters by station
- Disabling capture restores normal datapath operation
- Active traffic not disrupted by capture enable/disable

## Failure Indicators

- RX capture enable returns error
- No packets captured despite active traffic
- Captured packet data corrupted
- Normal datapath broken after capture disable
- Firmware crash during capture operations

## Cleanup

- Disable RX capture:
  ```bash
  xncmdclient -c 'eftest ifoe_rx_capture 0 disable; quit;'
  ```
- Stop L2Ping:
  ```bash
  xncmdclient -c 'ifoe_ping_stop 0; quit;'
  ```
