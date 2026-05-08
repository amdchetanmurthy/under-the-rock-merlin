---
topology: single-node
timeout: 240
pass_criteria: "Config phase transitions synchronize across both MIDs without desync panics"
priority: P0
stability: stable
validation_groups: [post-test]
---

# Dual-MID Config Phase Synchronization Test

## Purpose

Validates that config phase transitions (ifoe_manager_set_config_phase) are properly synchronized across both MIDs. The source code shows three sync points:
1. Pre-transition: Primary reads remote phase and panics on mismatch (POSTCODE_IFOE_STATE_DESYNC)
2. During transition: Primary sends set_config_phase_async to remote and waits for completion
3. Post-transition: Primary re-reads remote phase and panics on mismatch
Tests that these sync points work correctly and that both MIDs end in the same phase.

## Category

positive, interaction, synchronization

## Prerequisites

- Dual-MID firmware booted with chip_ipc link established
- Both MIDs in SYSTEM phase
- xncmdclient available

## Steps

1. **[host]** Verify both MIDs start in SYSTEM phase:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: SYSTEM (primary reports for both)

2. **[host]** Transition to PROVIDER (triggers dual-MID sync):
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Success on both MIDs

3. **[host]** Verify no POSTCODE_IFOE_STATE_DESYNC in tracelog:
   ```bash
   # Check tracelog for absence of POSTCODE_IFOE_STATE_DESYNC
   ```
   Expected: No desync postcodes

4. **[host]** Transition to TENANT (triggers privilege update across MIDs):
   ```bash
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   ```
   Expected: Both MIDs transition to TENANT

5. **[host]** Verify config hooks ran on both MIDs:
   ```bash
   # Check tracelog for POSTCODE_IFOE_STATE on both MIDs
   ```
   Expected: Both MIDs show TENANT phase

6. **[host]** Verify backward transition syncs:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Both MIDs revert to PROVIDER, snapshots restored on both

## Expected Result

- All transitions complete on both MIDs
- No POSTCODE_IFOE_STATE_DESYNC postcodes
- No k_panic during phase sync
- Config hooks fire on both MIDs (primary runs hooks locally, remote runs via async RPC)
- Backward transitions restore snapshots on both MIDs

## Failure Indicators

- POSTCODE_IFOE_STATE_DESYNC in tracelog
- k_panic during transition
- Phase mismatch between MIDs
- Blocking semaphore timeout in cb_ctx
- RPC send failure during set_config_phase_async

## Cleanup

- Firmware reboot if panic occurred
