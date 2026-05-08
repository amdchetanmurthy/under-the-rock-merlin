---
topology: single-node
timeout: 120
pass_criteria: "IFoE+MAC loopback enabled, test packet traverses full datapath including MAC and returns successfully"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE + MAC Loopback Test

## Purpose

Validates the full IFoE datapath including the MAC layer by enabling IFoE+MAC loopback on instance 0 and verifying end-to-end packet flow. This is a more comprehensive test than IFoE-only loopback because it exercises the complete TX/RX path through the MAC.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Firmware built with --eftest flag (EFTEST commands available)
- Port 0 link is up
- xncmdclient available on host

## Setup

1. **[host]** Enable IFoE+MAC loopback on instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe_and_mac; quit;'
   ```
   Expected: IFoE+MAC loopback mode enabled without error

## Steps

1. **[host]** Transmit a test packet on instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_tx_pkt 0; quit;'
   ```
   Expected: Packet transmitted through IFoE encap and MAC TX

2. **[host]** Wait for packet to traverse the MAC loopback path:
   ```bash
   sleep 1
   ```

3. **[host]** Check for received packet on instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_rx_pkt 0; quit;'
   ```
   Expected: Packet received after traversing MAC RX and IFoE decap

## Expected Result

- IFoE+MAC loopback mode is successfully enabled on instance 0
- Test packet traverses the full datapath: IFoE encap -> MAC TX -> MAC loopback -> MAC RX -> IFoE decap
- Received packet data matches transmitted packet data
- No errors reported by MAC or IFoE subsystems

## Failure Indicators

- Loopback enable returns error
- TX packet fails at MAC layer
- No RX packet received (packet lost in MAC loopback)
- RX packet data corruption
- MAC error counters increment
- Firmware crash or hang during loopback

## Config Cleanup

1. **[host]** Disable loopback:
   ```bash
   xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_off; quit;'
   ```

## Cleanup

- Verify firmware is still responsive:
  ```bash
  xncmdclient -c 'version; quit;'
  ```
