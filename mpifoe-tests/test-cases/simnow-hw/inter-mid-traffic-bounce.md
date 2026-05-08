---
topology: single-node
timeout: 300
pass_criteria: "Inter-MID traffic bounces correctly between MID0 and MID1 with packet integrity"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Inter-MID Traffic Bounce Under Load Test

## Purpose

Validates the inter-MID traffic bounce logic in non_ifoe_traffic.c (bounce_rx_to_mid0, bounce_tx_to_mid1) and inter_mid.c. In dual-MID configurations, certain traffic must be forwarded between MIDs based on port ownership. Tests that packets are correctly bounced without drops or corruption, and that the bounce path handles sustained traffic load.

## Category

positive, stress, integration

## Prerequisites

- Requires SimNow M222 model (dual-MID required)
- MPIFoE firmware booted on both MIDs
- Chip IPC link established between MIDs
- IFoE subsystems configured (both MIDs active)

## Setup

1. **[host]** Boot dual-MID SimNow and configure IFoE:
   ```bash
   /simnow/xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached on dual-MID system

## Steps

1. **[host]** Verify dual-MID is active:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Config shows dual-MID topology

2. **[host]** Enumerate ports on both MIDs:
   ```bash
   xncmdclient --force-enable-mmap -c 'enum_ports; quit;' tlp=0
   ```
   Expected: Ports from both MID0 and MID1 visible

3. **[host]** Run L2Ping that exercises inter-MID path:
   ```bash
   # Ping from MID0 port to MID1 port
   xncmdclient --force-enable-mmap \
     -c 'ifoe_ping_config 0 0 50; quit;' tlp=0
   xncmdclient --force-enable-mmap \
     -c 'ifoe_ping_start 0 0; quit;' tlp=0
   sleep 15
   xncmdclient --force-enable-mmap \
     -c 'ifoe_ping_poll 0; quit;' tlp=0
   xncmdclient --force-enable-mmap \
     -c 'ifoe_ping_stop 0; quit;' tlp=0
   ```
   Expected: L2Ping passes (traffic bounced between MIDs)

4. **[host]** Enable telemetry to check inter-MID counters:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl enable; quit;' tlp=0
   sleep 3
   xncmdclient --force-enable-mmap -c 'ifoe_telemetry_info; quit;' tlp=0
   ```
   Expected: Inter-MID traffic counters show bounce activity

5. **[host]** Send loopback packets on IFoE subsystem owned by MID1:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_loopback_ctrl 2 loopback_ifoe; quit;' tlp=0
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_tx_pkt 2; quit;' tlp=0
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_rx_pkt 2; quit;' tlp=0
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_loopback_ctrl 2 loopback_off; quit;' tlp=0
   ```
   Expected: Packets traverse inter-MID bounce path

6. **[host]** Verify firmware stability after inter-MID traffic:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'get_uptime; quit;' tlp=0
   ```
   Expected: Both MIDs responsive

## Expected Result

- Traffic correctly bounced from MID0 to MID1 and vice versa
- L2Ping passes across inter-MID boundary
- No packet drops during bounce (VLAN header correctly parsed)
- Telemetry shows inter-MID traffic counters incrementing
- Sustained traffic load does not destabilize IPC link

## Failure Indicators

- L2Ping failures (packets dropped during bounce)
- Inter-MID traffic counters remain zero
- IPC link drop during sustained traffic
- Firmware crash on either MID
- VLAN header parsing errors (wrong TPID)

## Cleanup

- Stop L2Ping:
  ```bash
  xncmdclient --force-enable-mmap -c 'ifoe_ping_stop 0; quit;' tlp=0
  ```
- Disable loopback:
  ```bash
  xncmdclient --force-enable-mmap -c 'eftest ifoe_loopback_ctrl 2 loopback_off; quit;' tlp=0
  ```
- Disable telemetry:
  ```bash
  xncmdclient --force-enable-mmap -c 'ifoe_telemetry_ctrl disable; quit;' tlp=0
  ```
