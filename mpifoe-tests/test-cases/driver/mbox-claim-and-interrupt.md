---
topology: single-node
timeout: 60
pass_criteria: "Mailbox self-test passes, claim/setup succeeds for all MCDI and chip_ipc mailboxes, and interrupt handlers fire correctly"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Mailbox Claim and Interrupt Handler Driver Test

## Purpose

Validates the mailbox driver (mbox.c). Tests boot-time mailbox self-test (test_mboxes), mailbox claim (mbox_claim), setup with interrupt handlers (mbox_setup), and read/write operations (mbox_read/mbox_write). The mailbox system underpins MCDI doorbells, EVQ read index doorbells, and chip_ipc communication.

## Category

positive, driver

## Prerequisites

- MPIFoE firmware booted
- CONFIG_WA_FWDEV_178242_DISABLE not set
- Tracelog access

## Steps

1. **[host]** Verify MBOX self-test passed at boot:
   ```bash
   # Check tracelog for POSTCODE_SELF_TEST_PASS instance 1
   # Should see: "MBOX Test PASS"
   ```
   Expected: MBOX Test PASS

2. **[host]** Verify MCDI doorbell mailboxes claimed successfully:
   ```bash
   # In command_thread init, mbox_claim for pf_mcdi_mboxes and vf_mcdi_mboxes
   # __ASSERT_NO_MSG(ok) would fire on failure
   ```
   Expected: No assertion failures

3. **[host]** Verify chip_ipc mailboxes claimed:
   ```bash
   # chip_ipc_mb_init claims req_mboxes and resp_mboxes
   # Failure logs POSTCODE_CHIP_IPC_F_MBOX and panics
   ```
   Expected: No POSTCODE_CHIP_IPC_F_MBOX in tracelog

4. **[host]** Exercise mailbox interrupt path via MCDI:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: MCDI doorbell triggers mcdi_mbox_handler interrupt

## Expected Result

- Boot self-test passes (test_mboxes returns 0)
- All required mailboxes claimed without conflict
- Interrupt handlers installed correctly
- mbox_read returns written values
- Double-claim detected via mbox_claim returning false

## Failure Indicators

- POSTCODE_SELF_TEST_FAIL instance 1
- POSTCODE_CHIP_IPC_F_MBOX (mailbox claim failed)
- __ASSERT_NO_MSG fire on mbox_claim failure
- MCDI commands not received (interrupt handler not firing)

## Cleanup

- None required
