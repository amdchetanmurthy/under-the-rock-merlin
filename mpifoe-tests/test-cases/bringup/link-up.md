---
topology: single-node
timeout: 60
pass_criteria: "All configured ports report link_up=1 with expected speed"
priority: P0
stability: stable
validation_groups: [post-test]
---

# Link State Verification

## Purpose

Validates that all configured network ports have their links up and operating at the expected speed. Link-up is a prerequisite for all connectivity and traffic tests.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- IFoE BIOS configuration applied (e.g., 4x200G)
- Ports enumerated successfully (port-enum test passes)
- xncmdclient available on host

## Steps

1. **[host]** Enumerate ports to get the port count:
   ```bash
   xncmdclient -c 'enum_ports; quit;'
   ```
   Expected: Returns list of port IDs

2. **[host]** Check link state for each port (example for port 0):
   ```bash
   xncmdclient -c 'link_state 0; quit;'
   ```
   Expected: link_up=1, speed matches configured mode (e.g., 200G for 4x200 config)

3. **[host]** Repeat link_state for all remaining ports:
   ```bash
   xncmdclient -c 'link_state 1; quit;'
   xncmdclient -c 'link_state 2; quit;'
   xncmdclient -c 'link_state 3; quit;'
   ```
   Expected: All ports show link_up=1

4. **[host]** Check MAC state for port 0 as additional verification:
   ```bash
   xncmdclient -c 'mac_state 0; quit;'
   ```
   Expected: MAC reports consistent state with link_state

## Expected Result

- All configured ports report link_up=1
- Port speed matches the configured port mode (200G for 4x200, 400G for 2x400, etc.)
- FEC mode is reported and valid
- Lane count matches the port mode configuration

## Failure Indicators

- Any port reports link_up=0
- Speed mismatch with configured port mode
- FEC errors or FEC mode mismatch
- Timeout waiting for link state response
- MAC state inconsistent with link state

## Cleanup

- None required (read-only inspection)
