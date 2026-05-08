---
topology: single-node
timeout: 120
pass_criteria: "N/A - FLR reset is stubbed in firmware"
priority: P1
stability: stable
status: not-applicable
not_applicable_reason: "FLR reset (do_flr_reset) is completely stubbed in reset.c per FWDEV-165197 and FWDEV-165198. The code path is commented out awaiting PM firmware support for key clearing and reset coordination. This test case is a placeholder until those tickets are resolved."
validation_groups: [post-test]
---

# FLR Reset Execution via PM Test

## Purpose

Validates FLR (Function Level Reset) execution triggered from the PM (Platform Management) processor via PCIe. FLR should clear crypto keys, reset IFoE state, and reinitialize subsystems. Currently NOT TESTABLE because do_flr_reset() in reset.c is completely stubbed -- the implementation is gated on FWDEV-165197 (PM reset notification) and FWDEV-165198 (key clearing on FLR).

## Category

positive, interaction, reset

## Prerequisites

- Requires MI450 hardware with PM firmware
- Requires SimNow A+A model (needs host PCIe)
- FWDEV-165197 and FWDEV-165198 must be resolved
- MPIFoE firmware with FLR support enabled

## Steps

1. **[host]** This test is currently not applicable. When FLR is implemented:
   - Trigger PCIe FLR from host
   - Verify PM sends reset notification to MPIFoE
   - Verify crypto keys are cleared
   - Verify IFoE state reinitializes
   - Verify firmware returns to expected phase

## Expected Result

- When implemented: FLR clears all crypto keys, resets IFoE configuration, and firmware resumes in a clean state

## Failure Indicators

- When implemented: Keys not cleared after FLR, firmware crash during FLR, state not reset

## Cleanup

- None (test is not applicable)
