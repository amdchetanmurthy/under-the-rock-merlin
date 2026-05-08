---
topology: back-to-back
timeout: 600
pass_criteria: "IFoE SDP TX/RX datapath handles GPU traffic with correct encap/decap and packet integrity"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE TX/RX SDP Datapath with GPU Traffic Test

## Purpose

Validates the IFoE TX/RX SDP (Scalable Data Port) datapath including packet encapsulation/decapsulation, SDP pack/unpack operations, TX scheduling, and TX buffer management. The IFoE driver (ifoe_drv.c, 16 files) handles the core data movement between GPU memory and the network. This test requires actual GPU traffic flowing through the SDP pipeline.

## Category

positive, integration, data-integrity

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted with --eftest flag
- Firmware in MISSION phase with active stations
- Back-to-back link up between two MI450 nodes
- GPU workload driver loaded (ifoe kernel driver)
- xncmdclient available on both hosts

## Setup

1. **[server]** Configure full IFoE datapath:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: MISSION phase with datapath active

2. **[client]** Configure matching IFoE on peer:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: MISSION phase with datapath active

## Steps

1. **[server]** Verify stations are active and datapath is enabled:
   ```bash
   xncmdclient -c 'ifoe_enum_stations; quit;'
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: Stations enumerated, station 0 in ACTIVE state

2. **[server]** Enable IFoE loopback for local datapath validation:
   ```bash
   xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe; quit;'
   ```
   Expected: IFoE loopback enabled

3. **[server]** Transmit test packet through SDP:
   ```bash
   xncmdclient -c 'eftest ifoe_tx_pkt 0; quit;'
   ```
   Expected: TX packet sent through SDP pipeline

4. **[server]** Receive and verify test packet:
   ```bash
   xncmdclient -c 'eftest ifoe_rx_pkt 0; quit;'
   ```
   Expected: RX packet received with correct encap/decap

5. **[server]** Disable loopback and test full MAC loopback:
   ```bash
   xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe_and_mac; quit;'
   xncmdclient -c 'eftest ifoe_tx_pkt 0; quit;'
   xncmdclient -c 'eftest ifoe_rx_pkt 0; quit;'
   ```
   Expected: Packet traverses full datapath including MAC

6. **[server]** Disable loopback:
   ```bash
   xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;'
   ```
   Expected: Normal datapath operation restored

7. **[server]** Check telemetry for TX/RX counters:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 2
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: TX and RX packet counters incremented

8. **[server]** Run L2Ping to verify end-to-end data plane:
   ```bash
   xncmdclient -c 'ifoe_ping_config 0 0 20; quit;'
   xncmdclient -c 'ifoe_ping_start 0 0; quit;'
   sleep 10
   xncmdclient -c 'ifoe_ping_poll 0; quit;'
   xncmdclient -c 'ifoe_ping_stop 0; quit;'
   ```
   Expected: All pings pass with zero failures

## Expected Result

- SDP TX pipeline correctly encapsulates GPU packets into IFoE format
- SDP RX pipeline correctly decapsulates IFoE packets for GPU delivery
- IFoE loopback (without MAC) validates encap/decap in isolation
- IFoE+MAC loopback validates full datapath
- TX/RX telemetry counters correctly reflect traffic volume
- L2Ping end-to-end passes on all channels

## Failure Indicators

- eftest ifoe_tx_pkt returns error (TX pipeline failure)
- eftest ifoe_rx_pkt returns no packet or corrupted data
- Packet count mismatch between TX and RX
- L2Ping failures indicating datapath corruption
- Telemetry counters not incrementing with traffic
- Firmware crash during TX/RX operations

## Cleanup

- Disable loopback:
  ```bash
  xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;'
  ```
- Stop L2Ping:
  ```bash
  xncmdclient -c 'ifoe_ping_stop 0; quit;'
  ```
- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
