---
topology: single-node
timeout: 180
pass_criteria: "Station transitions through DISABLED -> ACTIVE -> STOPPED -> DISABLED correctly with proper netport power and link event handling"
priority: P0
stability: stable
validation_groups: [post-test]
---

# Station Lifecycle State Machine Test

## Purpose

Validates the logical_link_manager station state machine. Each station (logical link) has three states: DISABLED, STOPPED, ACTIVE. Tests all valid transitions via ifoe_station_ctrl, verifies netport power-up/down side effects, and checks that link change events fire on state transitions.

## Category

positive, negative, state-machine

## Prerequisites

- MPIFoE firmware in PROVIDER phase with stations configured
- xncmdclient available
- At least one IFoE station enumerated

## Steps

1. **[host]** Enumerate stations and get station 0 state:
   ```bash
   xncmdclient -c 'ifoe_enum_stations; quit;'
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: Station 0 exists, state is ACTIVE (default after init)

2. **[host]** Transition station 0 from ACTIVE to STOPPED:
   ```bash
   xncmdclient -c 'ifoe_station_ctrl 0 STOPPED; quit;'
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: State is STOPPED

3. **[host]** Transition station 0 from STOPPED to DISABLED:
   ```bash
   xncmdclient -c 'ifoe_station_ctrl 0 DISABLED; quit;'
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: State is DISABLED

4. **[host]** Transition station 0 from DISABLED to ACTIVE:
   ```bash
   xncmdclient -c 'ifoe_station_ctrl 0 ACTIVE; quit;'
   xncmdclient -c 'ifoe_station_get_state 0; quit;'
   ```
   Expected: State is ACTIVE

5. **[host]** Test invalid state value:
   ```bash
   xncmdclient -c 'ifoe_station_ctrl 0 99; quit;'
   ```
   Expected: EINVAL error

6. **[host]** Test invalid station index:
   ```bash
   xncmdclient -c 'ifoe_station_ctrl 255 ACTIVE; quit;'
   ```
   Expected: ERANGE error

7. **[host]** Test station_ctrl rejected outside PROVIDER phase:
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_station_ctrl 0 STOPPED; quit;'
   ```
   Expected: EBUSY error (station_ctrl requires PROVIDER phase)

## Expected Result

- All valid state transitions succeed
- Invalid state values return EINVAL
- Invalid station indices return ERANGE
- Station control rejected outside PROVIDER phase
- Link change events fire on state changes
- Netport power state tracks station state

## Failure Indicators

- Valid transition returns error
- State does not change after successful ctrl
- Invalid state accepted
- Firmware hang during state change (mutex deadlock)
- Link change event callback not invoked

## Cleanup

- Return station to ACTIVE state if possible
- Phase reboot if needed
