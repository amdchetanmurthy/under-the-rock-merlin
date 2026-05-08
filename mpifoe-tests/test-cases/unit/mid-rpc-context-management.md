---
topology: single-node
timeout: 90
pass_criteria: "RPC context allocation, tag matching, and cleanup work correctly for all NUM_MID_RPC_CTXS slots"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MID RPC Context Management Unit Test

## Purpose

Validates the dual-MID RPC subsystem's context management (rpc.c): tx_ctx/rx_ctx allocation via mid_rpc_allocate_tx/rx, tag-based response matching via mid_rpc_tag_find_response, and cleanup via mid_rpc_free_tx/rx. This is the foundation of all inter-MID communication.

## Category

positive, unit

## Prerequisites

- Zephyr Twister environment configured
- mpifoe-fw build system available
- native_sim platform target

## Steps

1. **[host]** Build and run Twister test for mid_rpc context management:
   ```bash
   cd /home/cmurthy/utr/under-the-rock-main/firmware/mpifoe-fw
   west twister -T src/subsystems/mid_rpc/tests -p native_sim --test test_mid_rpc_ctx_alloc_free
   ```
   Expected: Test binary compiles and runs

2. **[twister]** Test tx context allocation fills all NUM_MID_RPC_CTXS slots:
   - Allocate NUM_MID_RPC_CTXS tx contexts with unique callbacks
   - Verify each gets a unique non-zero tag
   - Attempt one more allocation, verify it returns NULL

3. **[twister]** Test tag-based response matching:
   - Allocate a tx context for MID_REMOTE_0 with tag T
   - Call mid_rpc_tag_find_response(MID_REMOTE_0, T)
   - Verify it returns the correct context
   - Call mid_rpc_tag_find_response(MID_REMOTE_1, T)
   - Verify it returns NULL (wrong remote)

4. **[twister]** Test context cleanup:
   - Free a tx context with mid_rpc_free_tx
   - Verify the slot is reusable (allocate again succeeds)
   - Verify mid_rpc_tag_find_response no longer finds the freed context

## Expected Result

- All context slots allocatable with unique tags
- Exhaustion returns NULL
- Tag matching is exact on both tag value and remote ID
- Freed slots become reusable
- Mutex properly serializes concurrent access

## Failure Indicators

- Duplicate tags assigned
- NULL returned before all slots consumed
- Wrong context returned for tag lookup
- Freed context still findable
- Deadlock in mid_rpc_ctx_lock mutex

## Cleanup

- Twister cleans up test binary
