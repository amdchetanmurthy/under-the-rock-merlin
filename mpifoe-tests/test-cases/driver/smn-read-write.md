---
topology: single-node
timeout: 60
pass_criteria: "SMN driver reads/writes complete without error and self-test passes at boot"
priority: P1
stability: stable
validation_groups: [post-test]
---

# SMN Driver Read/Write Test

## Purpose

Validates the SMN (System Management Network) driver (smn_drv.c). The SMN bus is used to access registers on other MPs and hardware blocks. Tests that the boot-time SMN self-test (test_smn) passes and that smn_helper provides correct mappings to the other MPIFoE's SRAM and public registers.

## Category

positive, driver

## Prerequisites

- MPIFoE firmware booted
- Tracelog access for self-test results

## Steps

1. **[host]** Verify SMN self-test passed at boot:
   ```bash
   # Check tracelog for POSTCODE_SELF_TEST_PASS instance 0
   # Should see: "SMN Test PASS"
   ```
   Expected: SMN Test PASS in tracelog

2. **[host]** Verify smn_helper initialized correctly:
   ```bash
   # smn_helper_get_other_mpifoe_public() should return valid mapped address
   # SMN_HELPER_OTHER_MPIFOE_SRAM_ADDR should be usable
   ```
   Expected: Valid addresses (verified by chip_ipc using them)

3. **[host]** Exercise SMN path via chip_ipc communication:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Success (dual-MID communication uses SMN)

## Expected Result

- Boot self-test passes (test_smn returns 0)
- SMN mappings to other MP are valid
- Read/write via SMN does not corrupt data
- No POSTCODE_SELF_TEST_FAIL for SMN

## Failure Indicators

- POSTCODE_SELF_TEST_FAIL instance 0 in tracelog
- SMN read returns unexpected data
- chip_ipc communication fails (SMN path broken)
- smn_helper returns NULL mapping

## Cleanup

- None required
