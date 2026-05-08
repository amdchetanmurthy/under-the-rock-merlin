---
topology: single-node
timeout: 300
pass_criteria: "Port 0 link cycles up/down 10 times without failure, link re-establishes each iteration"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Link Up/Down Cycling Stress Test

## Purpose

Validates firmware stability under repeated link up/down cycling on port 0. Link cycling stresses the PHY, MAC, and link state machine, and can expose race conditions, resource leaks, or state corruption in the link management subsystem.

## Category

stress

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Port 0 link is currently up
- xncmdclient available on host

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| iterations | 10 | 1-100 | Number of link up/down cycles |
| port | 0 | 0-3 | Port to cycle |
| settle_time | 5 | 2-30 | Seconds to wait after link_ctrl for link to settle |

## Steps

1. **[host]** Verify initial link state is up:
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=1

2. **[host]** For each iteration (1 through 10), bring link down:
   ```bash
   xncmdclient -c 'link_ctrl 0 down; quit;'
   ```
   Expected: Command accepted without error

3. **[host]** Verify link is down:
   ```bash
   sleep 2
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=0

4. **[host]** Bring link back up:
   ```bash
   xncmdclient -c 'link_ctrl 0 up; quit;'
   ```
   Expected: Command accepted without error

5. **[host]** Wait for link to re-establish and verify:
   ```bash
   sleep 5
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=1, speed matches configured mode

6. **[host]** Repeat steps 2-5 for all 10 iterations

7. **[host]** After all iterations, verify firmware health:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Firmware responsive, uptime reflects continuous operation

## Expected Result

- All 10 link down/up cycles complete successfully
- Link re-establishes at the correct speed after each up command
- No link failures or timeouts during re-establishment
- Firmware remains responsive throughout all iterations
- No resource leaks (uptime continues advancing normally)

## Failure Indicators

- Link fails to come back up after link_ctrl up
- Link speed changes between iterations
- Firmware becomes unresponsive during cycling
- Increasing latency in link_state responses (resource leak)
- FEC errors or MAC errors accumulate across iterations

## Cleanup

- Ensure link is up at the end:
  ```bash
  xncmdclient -c 'link_ctrl 0 up; quit;'
  sleep 5
  xncmdclient -c 'link_state 0; quit;'
  ```
