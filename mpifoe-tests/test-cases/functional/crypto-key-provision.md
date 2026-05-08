---
topology: single-node
timeout: 120
pass_criteria: "Crypto configuration and TX/RX key provisioning complete without error"
priority: P2
stability: stable
validation_groups: [post-test]
---

# Crypto Key Provisioning Test

## Purpose

Validates the XRSEC crypto subsystem by configuring crypto parameters and provisioning TX/RX encryption keys. Crypto key provisioning is required for encrypted IFoE traffic and is part of the security validation for the IFoE fabric.

## Category

positive, security

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Firmware built with XRSEC crypto support
- xncmdclient available on host

## Steps

1. **[host]** Configure crypto parameters:
   ```bash
   xncmdclient -c 'ifoe_config_crypto <params>; quit;'
   ```
   Expected: Crypto configuration accepted without error

2. **[host]** Set TX crypto key:
   ```bash
   xncmdclient -c 'ifoe_set_tx_crypto_key <key_data>; quit;'
   ```
   Expected: TX key provisioned successfully

3. **[host]** Set RX crypto key:
   ```bash
   xncmdclient -c 'ifoe_set_rx_crypto_key <key_data>; quit;'
   ```
   Expected: RX key provisioned successfully

4. **[host]** Verify firmware is still responsive after key provisioning:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Firmware responds with version (no crash from crypto operations)

## Expected Result

- ifoe_config_crypto accepts the crypto configuration without error
- TX crypto key is provisioned successfully
- RX crypto key is provisioned successfully
- Firmware remains responsive after all crypto operations
- No error codes or exceptions from the XRSEC subsystem

## Failure Indicators

- ifoe_config_crypto returns error (unsupported or invalid config)
- TX or RX key provisioning fails
- Firmware hangs or crashes during crypto operations
- XRSEC error codes in response
- Timeout during key provisioning

## Config Cleanup

1. **[host]** Disable RX crypto key:
   ```bash
   xncmdclient -c 'ifoe_disable_rx_crypto_key; quit;'
   ```

## Cleanup

- Verify firmware is still responsive:
  ```bash
  xncmdclient -c 'version; quit;'
  ```
