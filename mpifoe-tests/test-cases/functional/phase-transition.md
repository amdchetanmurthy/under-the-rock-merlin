---
topology: single-node
timeout: 180
pass_criteria: "Firmware transitions through all phases: SYSTEM -> PROVIDER -> TENANT -> MISSION successfully"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Phase Transition Test

## Purpose

Validates the MPIFoE firmware's ability to transition through all configuration phases using ifoe_next_phase. The phase progression (System -> Provider -> Tenant -> Mission) is the core lifecycle model that gates which operations are available at each stage.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware freshly booted (in SYSTEM phase) or in PROVIDER phase
- IFoE BIOS configuration applied
- xncmdclient available on host

## Steps

1. **[host]** Check current phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Returns current phase (starting point)

2. **[host]** If in SYSTEM phase, apply BIOS config and transition to PROVIDER:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Phase transitions to PROVIDER

3. **[host]** Verify PROVIDER phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Returns PROVIDER

4. **[host]** Transition to TENANT phase:
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```
   Expected: Phase transitions to TENANT

5. **[host]** Verify TENANT phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Returns TENANT

6. **[host]** Transition to MISSION phase:
   ```bash
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: Phase transitions to MISSION

7. **[host]** Verify MISSION phase and firmware health:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   xncmdclient -c 'version; quit;'
   ```
   Expected: Returns MISSION, firmware still responsive

## Expected Result

- Each phase transition completes without error
- ifoe_get_current_phase reflects the new phase after each transition
- Firmware remains responsive throughout all transitions
- No error logs or crashes during transitions

## Failure Indicators

- ifoe_next_phase returns error for any transition
- Phase does not change after transition command
- Firmware becomes unresponsive during or after a transition
- Invalid phase reported after transition
- Phase skips or goes backward

## Cleanup

- Note: Phase transitions are one-way in normal operation. The firmware must be rebooted to return to SYSTEM phase. This test leaves the firmware in MISSION phase.
