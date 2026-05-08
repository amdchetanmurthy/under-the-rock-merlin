---
topology: back-to-back
timeout: 300
pass_criteria: "Link up/down events correctly propagated through firmware and MAC state updates"
priority: P0
stability: stable
validation_groups: [post-test]
---

# Physical Link Up/Down Events with Cable/Transceiver Test

## Purpose

Validates physical link event handling in the network manager (netport_manager.c, netport_events.c, ethport_manager.c). Tests link up/down detection, MAC state transitions, port properties updates, and event propagation to IFoE subsystems when physical link state changes. Requires actual network cable connection between two MI450 nodes.

## Category

positive, error-recovery, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- Two MI450 nodes connected via cable (back-to-back)
- MPIFoE firmware booted on both nodes
- Firmware in PROVIDER phase or later
- xncmdclient available on both hosts

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| port_id | 0 | 0-3 | Network port to test |
| link_cycles | 5 | 1-20 | Number of link up/down cycles |

## Steps

1. **[server]** Verify initial link state:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=1, speed and FEC configured

2. **[server]** Record transceiver properties:
   ```bash
   xncmdclient -c 'get_transceiver_properties 0; quit;'
   ```
   Expected: Transceiver type and capabilities reported

3. **[server]** Bring link down:
   ```bash
   xncmdclient -c 'link_ctrl 0 down; quit;'
   sleep 2
   ```
   Expected: Link control accepted

4. **[server]** Verify link is down:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=0

5. **[server]** Bring link back up:
   ```bash
   xncmdclient -c 'link_ctrl 0 up; quit;'
   sleep 5
   ```
   Expected: Link control accepted

6. **[server]** Verify link restored:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=1, speed and FEC match original

7. **[server]** Cycle link multiple times:
   ```bash
   for i in $(seq 1 5); do
     xncmdclient -c 'link_ctrl 0 down; quit;'
     sleep 2
     xncmdclient -c 'link_ctrl 0 up; quit;'
     sleep 5
   done
   ```
   Expected: All cycles complete without firmware crash

8. **[server]** Verify firmware stability after cycling:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'link_state 0; quit;'
   xncmdclient -c 'mac_state 0; quit;'
   ```
   Expected: Firmware responsive, link up, MAC state consistent

9. **[server]** Run L2Ping after link cycling:
   ```bash
   xncmdclient -c 'ifoe_ping_config 0 0 10; quit;'
   xncmdclient -c 'ifoe_ping_start 0 0; quit;'
   sleep 5
   xncmdclient -c 'ifoe_ping_poll 0; quit;'
   xncmdclient -c 'ifoe_ping_stop 0; quit;'
   ```
   Expected: L2Ping passes (network connectivity restored)

## Expected Result

- Link down correctly detected and MAC state updated
- Link up correctly restores full configuration (speed, FEC, lanes)
- Multiple link cycles do not destabilize firmware
- Link events propagated to IFoE subsystems via netport listeners
- L2Ping passes after link recovery

## Failure Indicators

- Link state does not change after link_ctrl command
- MAC state inconsistent after link up (wrong speed/FEC)
- Firmware crash during link cycling
- L2Ping fails after link recovery
- Link fails to come back up after down

## Cleanup

- Ensure link is up:
  ```bash
  xncmdclient -c 'link_ctrl 0 up; quit;'
  ```
- Stop L2Ping:
  ```bash
  xncmdclient -c 'ifoe_ping_stop 0; quit;'
  ```
