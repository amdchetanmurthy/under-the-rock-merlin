---
topology: single-node
timeout: 120
pass_criteria: "All MCDI commands correctly reject unauthorized clients with MC_CMD_ERR_EPERM"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MCDI Privilege Enforcement Unit Test

## Purpose

Validates that every MCDI command handler correctly enforces privilege checks. The firmware uses a per-command privilege category table (cmd_category[]) and mc_client_has_privilege() to gate access. This test sends MCDI commands from VF clients to provider-only endpoints to verify EPERM is returned.

## Category

negative, security

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase
- xncmdclient available on host
- VF driver loaded (or VF MCDI channel available)

## Steps

1. **[host]** Verify firmware is in PROVIDER phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: PROVIDER

2. **[host]** Attempt provider-only commands from VF context:
   ```bash
   xncmdclient --vf 0 -c 'ifoe_set_identity 1 0; quit;'
   ```
   Expected: Returns EPERM error

3. **[host]** Attempt to set active accelerators from VF context:
   ```bash
   xncmdclient --vf 0 -c 'ifoe_set_active_accelerators 0x1; quit;'
   ```
   Expected: Returns EPERM error

4. **[host]** Attempt to set local accelerators from VF context:
   ```bash
   xncmdclient --vf 0 -c 'ifoe_set_local_accelerators 0x1; quit;'
   ```
   Expected: Returns EPERM error

5. **[host]** Verify PF can execute the same commands successfully:
   ```bash
   xncmdclient -c 'ifoe_set_identity 1 0; quit;'
   ```
   Expected: Success (no EPERM)

## Expected Result

- VF client receives EPERM for all provider-privileged commands
- PF client can execute the same commands without EPERM
- Privilege mask correctly reflects PF having PROVIDER privilege and VF having none in PROVIDER phase

## Failure Indicators

- VF client can execute provider-privileged commands
- PF client receives unexpected EPERM
- Firmware crash or hang on privilege check
- Wrong error code returned (not EPERM)

## Cleanup

- None required
