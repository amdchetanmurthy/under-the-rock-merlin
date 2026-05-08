---
topology: single-node
timeout: 30
pass_criteria: "ifoe_get_current_phase returns a valid phase (SYSTEM, PROVIDER, TENANT, or MISSION)"
priority: P0
stability: stable
validation_groups: [pre-test]
---

# Configuration Phase Check

## Purpose

Validates that the MPIFoE firmware reports a valid configuration phase via MC_CMD_IFOE_GET_CURRENT_PHASE. The phase indicates where the firmware is in its lifecycle (System Config, Provider Config, Tenant Config, or Mission Mode) and determines which operations are available.

## Category

positive

## Prerequisites

- MPIFoE firmware booted
- xncmdclient available on host

## Steps

1. **[host]** Query current configuration phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Returns one of: SYSTEM, PROVIDER, TENANT, or MISSION

2. **[host]** Verify phase is consistent with firmware state:
   Expected: Phase is not an error code and matches a known phase string

## Expected Result

- ifoe_get_current_phase returns one of the four valid phases: SYSTEM, PROVIDER, TENANT, or MISSION
- Response is received within the timeout period
- No error codes in the response

## Failure Indicators

- Unknown or invalid phase string returned
- xncmdclient error or timeout
- Phase returns an error code instead of a phase name
- Empty response from the command

## Cleanup

- None required
