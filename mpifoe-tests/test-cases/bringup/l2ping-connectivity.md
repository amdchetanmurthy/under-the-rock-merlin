---
topology: single-node
timeout: 120
pass_criteria: "All L2Ping channels (REQ, RESP, NON_IFOE) report zero failures"
priority: P0
stability: stable
validation_groups: [post-test]
---

# L2Ping Connectivity Test

## Purpose

Validates network connectivity between IFoE subsystems by sending L2Ping packets over all three traffic channels per netport. This is the primary health check for IFoE fabric connectivity. L2Ping tests three channels: IFoE Request, IFoE Response, and Non-IFoE.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER or MISSION phase
- At least one netport link is up
- Active accelerators discovered
- xncmdclient available on host

## Steps

1. **[host]** Discover active accelerators to get accel_id:
   ```bash
   xncmdclient -c 'ifoe_get_active_accelerators; quit;'
   ```
   Expected: Returns at least one active accelerator with its ID

2. **[host]** Configure L2Ping for the first active accelerator:
   ```bash
   xncmdclient -c 'ifoe_ping_config <accel_id> <netport> 4; quit;'
   ```
   Expected: Returns ping handle and results buffer size

3. **[host]** Start L2Ping:
   ```bash
   xncmdclient -c 'ifoe_ping_start <handle> <host_buffer>; quit;'
   ```
   Expected: Ping starts without error

4. **[host]** Wait for completion and poll results:
   ```bash
   sleep 10
   xncmdclient -c 'ifoe_ping_poll <handle>; quit;'
   ```
   Expected: Results available with per-channel failure counts

5. **[host]** Verify results:
   Expected: req_failures=0, resp_failures=0, non_ifoe_failures=0

## Expected Result

All three channels report zero failures:
- IFOE_REQ (channel 0): 0 failures
- IFOE_RESP (channel 1): 0 failures
- NON_IFOE (channel 2): 0 failures

## Failure Indicators

- Any failure count > 0
- Timeout waiting for ping completion
- "ping_config: error" in xncmdclient output
- Missing channels in results (incomplete test)
- Handle allocation failure

## Cleanup

- Stop any running pings:
  ```bash
  xncmdclient -c 'ifoe_ping_stop <handle>; quit;'
  ```
