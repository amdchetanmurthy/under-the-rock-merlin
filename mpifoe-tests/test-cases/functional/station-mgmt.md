---
topology: single-node
timeout: 120
pass_criteria: "Stations can be enumerated and station state can be queried for each active station"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Station Management Test

## Purpose

Validates the IFoE station management subsystem by enumerating stations and querying individual station states. Stations represent IFoE endpoints and their management is critical for multi-node IFoE fabric operation.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- IFoE configuration applied with active subsystems
- xncmdclient available on host

## Steps

1. **[host]** Enumerate all IFoE stations:
   ```bash
   xncmdclient -c 'ifoe_enum_stations; quit;'
   ```
   Expected: Returns list of station IDs with count

2. **[host]** Query state of station 0:
   ```bash
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: Returns station state information (connected/disconnected, health)

3. **[host]** Query station control capabilities:
   ```bash
   xncmdclient -c 'ifoe_station_ctrl 0; quit;'
   ```
   Expected: Returns station control response without error

4. **[host]** Re-enumerate stations to verify consistency:
   ```bash
   xncmdclient -c 'ifoe_enum_stations; quit;'
   ```
   Expected: Station count and IDs match the first enumeration

## Expected Result

- ifoe_enum_stations returns a valid list of stations
- Station count is consistent across multiple enumerations
- ifoe_station_get_state returns valid state for each enumerated station
- Station control operations complete without error

## Failure Indicators

- ifoe_enum_stations returns error or zero stations when stations are expected
- Station state query fails for an enumerated station ID
- Station count changes between enumerations (instability)
- Station control returns unexpected error
- Timeout during station operations

## Cleanup

- None required (read-only inspection and control queries)
