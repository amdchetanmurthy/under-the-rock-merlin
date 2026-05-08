---
topology: single-node
timeout: 180
pass_criteria: "FLR and entity reset correctly run all reset hooks and return firmware to expected state"
priority: P0
stability: stable
validation_groups: [post-test]
---

# PM/Host to MPIFoE FLR and Entity Reset Interaction Test

## Purpose

Validates the reset paths in the MCDI manager (reset.c). Tests entity_reset (full FINI+INIT hook sequence) and FLR reset (currently stubbed per FWDEV-165197/165198). Verifies that reset hooks run in the correct order and that EVQ, IFoE config, and other subsystems properly reinitialize.

## Category

positive, interaction, reset

## Prerequisites

- MPIFoE firmware in PROVIDER or later phase
- EVQ initialized
- xncmdclient available

## Steps

1. **[host]** Set up state that reset should clear (init EVQ, configure stations):
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   xncmdclient -c 'init_evq 1; quit;'
   ```
   Expected: PROVIDER phase, EVQ initialized

2. **[host]** Execute entity_reset:
   ```bash
   xncmdclient -c 'entity_reset; quit;'
   ```
   Expected: Success returned

3. **[host]** Verify reset hooks ran:
   ```bash
   # evq_reset hook (order 200) should have called fini_evq
   # ifoe_config reset hook (order 100) should have rewound config phase
   ```

4. **[host]** Verify EVQ was finalized by attempting re-init:
   ```bash
   xncmdclient -c 'init_evq 1; quit;'
   ```
   Expected: Success (previous EVQ was finalized, can re-init)

5. **[host]** Verify IFoE config state after PF entity reset:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: PROVIDER (PF reset rewinds to PROVIDER per reset hook)

6. **[host]** Test entity_reset from VF context:
   ```bash
   xncmdclient --vf 0 -c 'entity_reset; quit;'
   ```
   Expected: VF reset rewinds to TENANT (if currently past TENANT)

## Expected Result

- Entity reset runs FINI then INIT hooks in order
- EVQ is properly finalized and re-initializable
- Config phase rewinds based on client type (PF->PROVIDER, VF->TENANT, Supervisor->SYSTEM)
- Reset hooks respect ordering (EVQ at 200, ifoe_config at 100)

## Failure Indicators

- entity_reset returns error
- EVQ not finalized after reset (init returns EALREADY)
- Config phase not rewound correctly
- Reset hooks run out of order
- Firmware crash during reset

## Cleanup

- Re-initialize EVQ and phase as needed
