---
topology: single-node
timeout: 120
pass_criteria: "Invalid MCDI command IDs dispatch to default_handler which returns ENOTSUP, and oversized payloads are rejected"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MCDI Invalid Command and Payload Error Handling Test

## Purpose

Validates error handling in the MCDI dispatch path (mcdi_manager.c). Tests: (1) command IDs beyond cmd_table size fall through to id=0 default handler, (2) send_cmd_reply rejects payloads exceeding BITFIELD_MASK(MC_CMD_V2_EXTN_IN_ACTUAL_LEN) by returning MC_CMD_ERR_EIO, (3) send_cmd_err properly sets error header fields.

## Category

negative, error-handling

## Prerequisites

- MPIFoE firmware booted
- Raw MCDI interface available (or xncmdclient with raw cmd mode)

## Steps

1. **[host]** Send a valid command to verify baseline:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Version returned successfully

2. **[host]** Send an invalid command ID (e.g., 0xFFFF):
   ```bash
   xncmdclient -c 'raw_cmd 0xFFFF 0; quit;'
   ```
   Expected: Error response with ENOTSUP or handled by default_handler

3. **[host]** Verify error response has ERROR flag set:
   ```bash
   # MCDI_V1_HEADER_SET(cmd, ERROR, 1) should be set
   # ERR_CODE should be populated
   ```

4. **[host]** Send a command with truncated payload (below minimum length):
   ```bash
   xncmdclient -c 'raw_cmd IFOE_SET_IDENTITY 0; quit;'
   ```
   Expected: Error (payload too short for required fields)

5. **[host]** Verify firmware remains responsive after error handling:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Version returned (no crash from error path)

## Expected Result

- Invalid command IDs handled without crash
- Error responses have ERROR flag set in MCDI header
- ERR_CODE field contains appropriate error code
- ERR_ARG contains rc_location_id for debugging (send_cmd_err_rc path)
- Firmware remains responsive after all error conditions

## Failure Indicators

- Firmware crash on invalid command ID
- Missing ERROR flag in response
- Wrong error code
- Firmware becomes unresponsive after error
- send_cmd_reply recurses infinitely (payload overflow in error path)

## Cleanup

- None required
