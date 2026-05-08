---
topology: single-node
timeout: 30
pass_criteria: "enum_ports returns at least one port with valid port properties"
priority: P0
stability: stable
validation_groups: [pre-test]
---

# Port Enumeration Check

## Purpose

Validates that the MPIFoE firmware can enumerate network ports via MC_CMD_ENUM_PORTS. Port enumeration is a prerequisite for all link, traffic, and connectivity tests.

## Category

positive

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- IFoE BIOS configuration applied (e.g., 4x200G mode)
- xncmdclient available on host

## Steps

1. **[host]** Enumerate all ports:
   ```bash
   xncmdclient -c 'enum_ports; quit;'
   ```
   Expected: Returns a list of ports with port IDs

2. **[host]** For each enumerated port, query fixed port properties:
   ```bash
   xncmdclient -c 'get_fixed_port_properties 0; quit;'
   ```
   Expected: Returns port properties including speed capability and lane count

## Expected Result

- enum_ports returns at least one port entry
- Port count matches the configured port mode (e.g., 4 ports for 4x200G)
- Each port has valid fixed properties (non-zero speed capability, valid lane count)

## Failure Indicators

- enum_ports returns zero ports
- Port count does not match the configured port mode
- get_fixed_port_properties returns error for a valid port ID
- Timeout or error from xncmdclient

## Cleanup

- None required
