---
topology: single-node
timeout: 180
pass_criteria: "Sideband MCDI requests are received, dispatched, and responded to via IFCP transport without corruption"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Sideband MCDI Dispatch Interaction Test

## Purpose

Validates the sideband (IFCP transport) MCDI path in mcdi_manager.c. When CONFIG_TRANSPORT_IFCP is enabled, MCDI commands can arrive via the sideband channel (mcdi_manager_submit_request) in addition to the TLP doorbell path. Tests submission, buffering (sideband_buffer_sem), dispatch, and response via mcdi_sideband_transport_api->send_response.

## Category

positive, negative, interaction

## Prerequisites

- MPIFoE firmware with CONFIG_TRANSPORT_IFCP enabled
- Sideband transport registered (mcdi_manager_register_sideband_transport_api called)
- Sideband communication channel operational

## Steps

1. **[host]** Verify sideband transport is registered:
   ```bash
   # Sideband manager should have called mcdi_manager_register_sideband_transport_api
   # Verify via tracelog or by sending a sideband MCDI command
   ```

2. **[host]** Send a version query via sideband:
   ```bash
   # Send MC_CMD_GET_VERSION via sideband IFCP channel
   ```
   Expected: Version response received via sideband send_response callback

3. **[host]** Verify buffer semaphore protects against concurrent requests:
   ```bash
   # Send two sideband requests without waiting for first to complete
   ```
   Expected: Second request returns ENOBUFS (sideband_buffer_sem not available)

4. **[host]** Send ifoe_get_current_phase via sideband:
   ```bash
   # Send IFOE_GET_CURRENT_PHASE via sideband
   ```
   Expected: Current phase returned correctly

5. **[host]** Verify sideband privileges match PF privileges:
   ```bash
   # Send PRIVILEGE_MASK query via sideband
   ```
   Expected: Sideband gets same privileges as PF (ifoe_manager_get_sideband_privileges)

## Expected Result

- Sideband commands dispatched correctly through cmd_table
- Responses sent via sideband transport API
- Buffer semaphore prevents concurrent requests (ENOBUFS)
- Sideband client has PF-equivalent privileges
- Command payload correctly copied via memcpy

## Failure Indicators

- Sideband command dispatch fails
- Response not sent via sideband transport
- Buffer overflow from concurrent requests
- Privilege mismatch between sideband and PF
- Payload corruption (memcpy issue)

## Cleanup

- None required
