---
topology: single-node
timeout: 180
pass_criteria: "L2Ping on all ports simultaneously reports zero failures on all channels"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Multi-Port Simultaneous Traffic Test

## Purpose

Validates that the MPIFoE firmware can handle L2Ping traffic on all configured ports simultaneously. This stresses the firmware's ability to manage concurrent operations across multiple IFoE subsystem instances, testing thread scheduling, buffer management, and resource contention.

## Category

stress, concurrency

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- All configured ports have links up
- Active accelerators discovered on all ports
- xncmdclient available on host

## Steps

1. **[host]** Enumerate ports and verify all links are up:
   ```bash
   xncmdclient -c 'enum_ports; quit;'
   xncmdclient -c 'link_state 0; quit;'
   xncmdclient -c 'link_state 1; quit;'
   xncmdclient -c 'link_state 2; quit;'
   xncmdclient -c 'link_state 3; quit;'
   ```
   Expected: All ports show link_up=1

2. **[host]** Get active accelerators:
   ```bash
   xncmdclient -c 'ifoe_get_active_accelerators; quit;'
   ```
   Expected: Returns accelerator IDs for all active ports

3. **[host]** Configure L2Ping on all ports:
   ```bash
   xncmdclient -c 'ifoe_ping_config <accel_0> 0 4; quit;'
   xncmdclient -c 'ifoe_ping_config <accel_1> 1 4; quit;'
   xncmdclient -c 'ifoe_ping_config <accel_2> 2 4; quit;'
   xncmdclient -c 'ifoe_ping_config <accel_3> 3 4; quit;'
   ```
   Expected: All ping configurations accepted, handles returned

4. **[host]** Start L2Ping on all ports simultaneously:
   ```bash
   xncmdclient -c 'ifoe_ping_start <handle_0> <buf_0>; ifoe_ping_start <handle_1> <buf_1>; ifoe_ping_start <handle_2> <buf_2>; ifoe_ping_start <handle_3> <buf_3>; quit;'
   ```
   Expected: All pings start without error

5. **[host]** Wait for completion and poll all results:
   ```bash
   sleep 15
   xncmdclient -c 'ifoe_ping_poll <handle_0>; quit;'
   xncmdclient -c 'ifoe_ping_poll <handle_1>; quit;'
   xncmdclient -c 'ifoe_ping_poll <handle_2>; quit;'
   xncmdclient -c 'ifoe_ping_poll <handle_3>; quit;'
   ```
   Expected: All ports report zero failures on all three channels

## Expected Result

- L2Ping runs simultaneously on all configured ports
- All ports report zero failures across all three channels (REQ, RESP, NON_IFOE)
- No cross-port interference or resource contention
- Firmware remains responsive during and after concurrent traffic

## Failure Indicators

- Any port reports non-zero failure count
- Ping start fails on some ports due to resource exhaustion
- Firmware becomes unresponsive during concurrent pings
- Results from some ports are missing or incomplete
- Timeout waiting for results on any port

## Cleanup

- Stop all running pings:
  ```bash
  xncmdclient -c 'ifoe_ping_stop <handle_0>; quit;'
  xncmdclient -c 'ifoe_ping_stop <handle_1>; quit;'
  xncmdclient -c 'ifoe_ping_stop <handle_2>; quit;'
  xncmdclient -c 'ifoe_ping_stop <handle_3>; quit;'
  ```
