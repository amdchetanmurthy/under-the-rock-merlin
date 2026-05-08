---
topology: back-to-back
timeout: 300
pass_criteria: "Physical link change events propagate through netport listeners to IFoE subsystems"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Physical Link Change Event Propagation Test

## Purpose

Validates the netport event propagation path (netport_events.c, netport_manager.c) and the IFoE manager's netport listener callbacks (link_post_up_handler, link_post_down_handler in logical_link_manager.c). Tests that physical link state changes are detected by the network manager and propagated to all registered listeners, triggering appropriate IFoE subsystem state changes.

## Category

positive, integration, error-recovery

## Prerequisites

- Requires MI450 hardware (not SimNow)
- Two MI450 nodes connected back-to-back
- MPIFoE firmware in PROVIDER phase or later on both nodes
- xncmdclient available on both hosts

## Steps

1. **[server]** Verify initial link state and station state:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   xncmdclient -c 'ifoe_enum_stations; quit;'
   ```
   Expected: Link up, stations enumerated

2. **[server]** Register listener state baseline:
   ```bash
   xncmdclient -c 'ifoe_get_config; quit;'
   ```
   Expected: IFoE config shows active link state

3. **[server]** Bring link down:
   ```bash
   xncmdclient -c 'link_ctrl 0 down; quit;'
   sleep 3
   ```
   Expected: Link goes down

4. **[server]** Verify link-down event propagated to IFoE:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   xncmdclient -c 'ifoe_enum_stations; quit;'
   ```
   Expected: Link down, station states reflect link-down event (link_post_down_handler called)

5. **[server]** Bring link back up:
   ```bash
   xncmdclient -c 'link_ctrl 0 up; quit;'
   sleep 5
   ```
   Expected: Link comes up

6. **[server]** Verify link-up event propagated to IFoE:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   xncmdclient -c 'ifoe_enum_stations; quit;'
   ```
   Expected: Link up, station states reflect link-up event (link_post_up_handler called)

7. **[server]** Verify L2Ping works after event propagation:
   ```bash
   xncmdclient -c 'ifoe_ping_config 0 0 10; quit;'
   xncmdclient -c 'ifoe_ping_start 0 0; quit;'
   sleep 5
   xncmdclient -c 'ifoe_ping_poll 0; quit;'
   xncmdclient -c 'ifoe_ping_stop 0; quit;'
   ```
   Expected: L2Ping passes (event propagation correctly restored datapath)

8. **[server]** Verify netport handle allocation stable across events:
   ```bash
   xncmdclient -c 'enum_ports; quit;'
   ```
   Expected: Port handles consistent (no handle leak from events)

## Expected Result

- Link-down event propagates through netport_events to all listeners
- link_post_down_handler in IFoE manager updates station and datapath state
- Link-up event restores state via link_post_up_handler
- Station states correctly reflect link events
- No listener callback errors or missed events
- Port handle allocation stable across link events

## Failure Indicators

- Station states not updated after link event (listener not called)
- L2Ping fails after link recovery (event not propagated)
- Port handle leak after events
- Firmware crash during event callback
- Listener ordering violation

## Cleanup

- Ensure link is up:
  ```bash
  xncmdclient -c 'link_ctrl 0 up; quit;'
  ```
- Stop L2Ping:
  ```bash
  xncmdclient -c 'ifoe_ping_stop 0; quit;'
  ```
