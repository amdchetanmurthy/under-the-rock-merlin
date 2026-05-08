---
topology: single-node
timeout: 30
pass_criteria: "xncmdclient returns a non-negative uptime value"
priority: P0
stability: stable
validation_groups: [pre-test]
---

# Firmware Uptime Check

## Purpose

Validates that the MPIFoE firmware reports a valid uptime via MC_CMD_GET_UPTIME. A non-zero uptime confirms the firmware has been running since boot. This also serves as a secondary liveness check beyond the version query.

## Category

positive

## Prerequisites

- MPIFoE firmware booted (any phase)
- xncmdclient available on host

## Steps

1. **[host]** Query firmware uptime via MCDI:
   ```bash
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Returns an uptime value (seconds or ticks) that is non-negative

2. **[host]** Wait 2 seconds and query uptime again:
   ```bash
   sleep 2
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Second uptime value is greater than the first, confirming the firmware clock is advancing

## Expected Result

- First uptime query returns a non-negative numeric value
- Second uptime query (after 2s delay) returns a value greater than the first
- Both queries complete without error or timeout

## Failure Indicators

- Uptime returns 0 after firmware has been running for more than a few seconds
- Second uptime is not greater than the first (clock stuck)
- Timeout or error from xncmdclient
- Non-numeric or garbled uptime response

## Cleanup

- None required
