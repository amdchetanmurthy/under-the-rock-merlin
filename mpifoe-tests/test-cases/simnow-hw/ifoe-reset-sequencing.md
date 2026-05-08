---
topology: single-node
timeout: 180
pass_criteria: "IFoE hardware reset sequence completes with correct timing and subsystem re-initialization"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Hardware Reset Timing Sequence Test

## Purpose

Validates the IFoE reset driver (ifoe_reset.c, 1 file) which manages the hardware reset timing sequence for IFoE subsystems. Tests that the reset sequence follows correct ordering, timing constraints are met, and all subsystems properly re-initialize after reset. The reset driver coordinates with entity_reset hooks.

## Category

positive, error-recovery, driver

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- xncmdclient available

## Setup

1. **[host]** Configure IFoE subsystems:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Record pre-reset state:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_get_current_phase; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_enum_stations; quit;' tlp=0
   ```
   Expected: Config, phase, and stations recorded

2. **[host]** Execute entity reset:
   ```bash
   xncmdclient --force-enable-mmap -c 'entity_reset; quit;' tlp=0
   ```
   Expected: Reset completes (IFoE reset hook fires)

3. **[host]** Verify firmware is responsive after reset:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware responds (survived reset)

4. **[host]** Check phase rewound correctly:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_current_phase; quit;' tlp=0
   ```
   Expected: Phase rewound to PROVIDER (PF entity reset behavior)

5. **[host]** Verify subsystems re-initialized:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: IFoE config in clean state (post-reset initialization)

6. **[host]** Re-advance through phases after reset:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase PROVIDER; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase TENANT; quit;' tlp=0
   ```
   Expected: Phase transitions succeed (subsystems properly re-initialized)

7. **[host]** Execute multiple reset cycles:
   ```bash
   for i in $(seq 1 5); do
     xncmdclient --force-enable-mmap -c 'entity_reset; quit;' tlp=0
     xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   done
   ```
   Expected: All reset cycles complete without crash

## Expected Result

- IFoE reset sequence follows correct ordering (FINI hooks before INIT hooks)
- All IFoE subsystems properly re-initialize after reset
- Phase correctly rewinds based on reset context (PF -> PROVIDER)
- Re-advancing through phases works after reset
- Multiple consecutive resets are stable
- No timing violations during reset sequence

## Failure Indicators

- Firmware crash during reset sequence
- Phase not rewound correctly after reset
- Subsystem re-initialization fails (phase transition error after reset)
- Multiple resets cause resource leak
- Reset timing violation (subsystem accessed before re-init)

## Cleanup

- None required (firmware in stable state after reset)
