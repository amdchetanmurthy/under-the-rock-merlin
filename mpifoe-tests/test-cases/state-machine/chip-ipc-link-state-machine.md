---
topology: single-node
timeout: 120
pass_criteria: "Chip IPC transitions through DOWN -> HELLO -> STAB_1ST -> STAB_REC -> STAB_LAST -> IDLE and correctly handles link drops"
priority: P0
stability: stable
validation_groups: [post-test]
---

# Chip IPC Link State Machine Test

## Purpose

Validates the chip_ipc intra-chip communication link state machine (chip_ipc.c). The link goes through: DOWN -> HELLO -> STAB_1ST -> STAB_REC -> STAB_LAST -> IDLE -> WAITING. Tests link establishment, stabilization handshake, command flow, and link drop/recovery. This state machine is critical for dual-MID communication.

## Category

positive, negative, state-machine

## Prerequisites

- Dual-MID firmware loaded (mp_role_is_multi_mp() == true)
- Both MIDs booted and link established
- xncmdclient available or tracelog access for state observation

## Steps

1. **[host]** Verify chip_ipc link is up by checking boot_info mp_link_status:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Firmware responsive, indicating chip_ipc link is up

2. **[host]** Query chip_ipc state via GET_STATE command:
   ```bash
   # The chip_ipc_is_link_up() sends CMD_ID_GET_STATE
   # Observe tracelog for POSTCODE_CHIP_IPC_UP confirming IDLE state
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Phase returned (requires working chip_ipc for dual-MID)

3. **[host]** Verify stabilization was successful by checking tracelog:
   ```bash
   # Look for POSTCODE_CHIP_IPC_UP in tracelog
   # Should see: "Chip-IPC: goes up/idle"
   ```
   Expected: Stabilization completed

4. **[host]** Trigger a command that uses chip_ipc (dual-MID RPC):
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Phase transition succeeds (requires chip_ipc for MID sync)

5. **[host]** Check for missed ISR diagnostics in tracelog:
   ```bash
   # Look for POSTCODE_CHIP_IPC_E_IRQ_MISSED
   ```
   Expected: No missed ISRs during normal operation

## Expected Result

- Link establishes through full handshake (HELLO -> STAB -> IDLE)
- GET_STATE returns >= CHIP_IPC_IDLE on remote
- Commands flow successfully in IDLE/WAITING states
- No missed ISRs or sequence errors
- boot_info reports mp_link_status as true

## Failure Indicators

- POSTCODE_CHIP_IPC_E_LINK_DROP in tracelog
- POSTCODE_CHIP_IPC_E_SEQ sequence error
- POSTCODE_CHIP_IPC_E_MISSED_RESP response timeout
- POSTCODE_CHIP_IPC_E_REQ_CH_DEAD or RESP_CH_DEAD
- boot_info mp_link_status false
- Command timeout during dual-MID operation

## Cleanup

- None (chip_ipc auto-recovers via HELLO retry)
