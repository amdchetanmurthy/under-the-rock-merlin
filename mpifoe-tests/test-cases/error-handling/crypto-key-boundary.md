---
topology: single-node
timeout: 120
pass_criteria: "Crypto key operations reject invalid key IDs, wrong phases, uninitialized encryption, and sideband client types"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Crypto Key Provisioning Boundary and Error Test

## Purpose

Validates error handling in crypto key MCDI commands (ifoe_cfg_cmds.c): set_tx_crypto_key, set_rx_crypto_key, disable_rx_crypto_key. Tests boundary conditions: invalid key IDs (must be KEY_0 or KEY_1), wrong config phase (must be TENANT or SHOWTIME), encryption not enabled (returns ENODEV), and invalid client types for SDP function mapping.

## Category

negative, error-handling, security

## Prerequisites

- MPIFoE firmware in TENANT phase
- xncmdclient available

## Steps

1. **[host]** Ensure TENANT phase without encryption enabled:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: TENANT

2. **[host]** Attempt set_tx_crypto_key without enabling encryption:
   ```bash
   xncmdclient -c 'ifoe_set_tx_crypto_key 0 <32-byte-key>; quit;'
   ```
   Expected: Returns ENODEV (encrypt_enable is false)

3. **[host]** Enable encryption:
   ```bash
   xncmdclient -c 'ifoe_config_crypto AES_GCM_256; quit;'
   ```
   Expected: Success

4. **[host]** Set TX key with valid key ID 0:
   ```bash
   xncmdclient -c 'ifoe_set_tx_crypto_key 0 <32-byte-key>; quit;'
   ```
   Expected: Success

5. **[host]** Set TX key with invalid key ID 99:
   ```bash
   xncmdclient -c 'ifoe_set_tx_crypto_key 99 <32-byte-key>; quit;'
   ```
   Expected: Returns EINVAL (ifoe_crypto_key_for_mcdi_enum fails)

6. **[host]** Attempt config_crypto with invalid mode:
   ```bash
   xncmdclient -c 'ifoe_config_crypto 99; quit;'
   ```
   Expected: Returns EINVAL

7. **[host]** Transition to PROVIDER and attempt crypto key operations:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase PROVIDER; quit;' tlp=0
   xncmdclient -c 'ifoe_set_tx_crypto_key 0 <32-byte-key>; quit;'
   ```
   Expected: Returns EBUSY (wrong phase)

## Expected Result

- Invalid key IDs rejected with EINVAL
- Operations in wrong phase return EBUSY
- Operations without encryption enabled return ENODEV
- Invalid crypto mode returns EINVAL
- Valid operations succeed in correct phase with encryption enabled

## Failure Indicators

- Invalid key ID accepted
- Wrong phase not rejected
- Key provisioned without encryption enabled
- Invalid crypto mode accepted
- Key data corruption

## Cleanup

- Firmware reboot
