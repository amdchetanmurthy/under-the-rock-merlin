---
topology: single-node
timeout: 240
pass_criteria: "Datapath state transitions (DOWN -> ETHERNET -> ETHERNET_SDP) fire correct before/after hooks in proper sequence"
priority: P0
stability: stable
validation_groups: [post-test]
---

# IFoE Datapath State Machine Test

## Purpose

Validates the datapath state machine that derives from config phase and run state. Per the truth table in ifoe_manager.c:
- SYSTEM/READY -> DOWN
- PROVIDER,TENANT/READY -> ETHERNET
- SHOWTIME/READY -> ETHERNET_SDP
- SHOWTIME/ISOLATED -> ETHERNET
Tests that datapath hooks fire in correct order (hardware_datapath_hook before logical_link before non_ifoe_traffic before telemetry) during transitions.

## Category

positive, state-machine, integration

## Prerequisites

- MPIFoE firmware freshly booted
- xncmdclient available
- Tracelog access for hook ordering verification

## Steps

1. **[host]** Start in SYSTEM (datapath = DOWN). Transition to PROVIDER (datapath = ETHERNET):
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: DOWN -> ETHERNET transition fires hooks

2. **[host]** Verify hooks fired in order via tracelog:
   ```bash
   # Check tracelog for:
   # 1. hardware_datapath_hook (hardware out of reset)
   # 2. netport_manager_datapath_hook
   # 3. logical_link_datapath_hook (station init)
   # 4. non_ifoe_traffic_datapath_hook (traffic thread starts)
   # 5. telemetry_datapath_hook (telemetry collection starts)
   ```
   Expected: All hooks present in correct order

3. **[host]** Transition PROVIDER -> TENANT (datapath stays ETHERNET):
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```
   Expected: No datapath hooks fire (state unchanged)

4. **[host]** Transition TENANT -> SHOWTIME (datapath = ETHERNET_SDP):
   ```bash
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: ETHERNET -> ETHERNET_SDP transition fires hooks

5. **[host]** Transition SHOWTIME -> TENANT (backward, datapath = ETHERNET):
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```
   Expected: ETHERNET_SDP -> ETHERNET backward transition fires hooks in reverse order

## Expected Result

- DOWN -> ETHERNET fires 5+ ordered hooks
- ETHERNET -> ETHERNET_SDP fires datapath hooks
- ETHERNET_SDP -> ETHERNET fires reverse-order hooks
- ETHERNET -> ETHERNET stays silent (no hook invocation)
- Ordering constraints enforced (verified by hooks_dump.py at build time)

## Failure Indicators

- Missing hooks in tracelog
- Hooks fire out of order
- Datapath state incorrect after transition
- non_ifoe_traffic starts before hardware is out of reset
- Telemetry starts before logical links initialized

## Cleanup

- Firmware reboot
