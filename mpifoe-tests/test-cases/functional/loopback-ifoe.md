---
topology: single-node
timeout: 120
pass_criteria: "IFoE loopback enabled, test packet transmitted and received back successfully"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE Loopback Test

## Purpose

Validates the IFoE encapsulation/decapsulation datapath by enabling IFoE-level loopback on instance 0 and verifying that a test packet is transmitted and received back. This tests the IFoE protocol layer without involving the MAC.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Firmware built with --eftest flag (EFTEST commands available)
- xncmdclient available on host

## Setup

1. **[host]** Enable IFoE loopback on instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_loopback_ctrl 0 loopback_ifoe; quit;'
   ```
   Expected: Loopback mode enabled without error

## Steps

1. **[host]** Transmit a test packet on instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_tx_pkt 0; quit;'
   ```
   Expected: Packet transmitted successfully, no error

2. **[host]** Wait briefly for loopback to complete:
   ```bash
   sleep 1
   ```

3. **[host]** Check for received packet on instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_rx_pkt 0; quit;'
   ```
   Expected: Packet received, data integrity verified

## Expected Result

- IFoE loopback mode is successfully enabled on instance 0
- Test packet is transmitted without error
- Looped-back packet is received on the same instance
- Received packet data matches transmitted packet data

## Failure Indicators

- Loopback enable returns error
- TX packet fails to send
- No RX packet received (timeout or empty)
- RX packet data corruption or mismatch
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
