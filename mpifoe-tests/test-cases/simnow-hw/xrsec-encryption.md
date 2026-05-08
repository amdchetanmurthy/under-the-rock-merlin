---
topology: back-to-back
timeout: 600
pass_criteria: "XRSEC encrypts/decrypts traffic with AES-GCM, key provisioning works, and RAS errors handled"
priority: P1
stability: stable
validation_groups: [post-test]
---

# XRSEC AES-GCM Encryption/Decryption and Key Management Test

## Purpose

Validates the XRSEC driver (xrsec_drv.c, 10 files) which manages hardware AES-GCM encryption/decryption for IFoE traffic. Tests crypto key provisioning (TX and RX keys), encryption enable/disable, key rotation (disable RX key + re-provision), and XRSEC-specific RAS error injection. XRSEC is the largest of the three IFoE subsystem drivers by file count, reflecting its complexity.

## Category

positive, security, driver, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted with --eftest flag
- Firmware in MISSION phase (crypto requires full configuration)
- xncmdclient available on both hosts
- Back-to-back link up between two MI450 nodes
- Crypto feature enabled in IFoE config

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| ifoe_ss_idx | 0 | 0-17 | IFoE subsystem index |

## Setup

1. **[server]** Configure IFoE and advance to MISSION phase:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: MISSION phase reached

2. **[client]** Configure matching IFoE and advance to MISSION:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'ifoe_next_phase TENANT; quit;'
   xncmdclient -c 'ifoe_next_phase MISSION; quit;'
   ```
   Expected: MISSION phase reached

## Steps

1. **[server]** Configure crypto parameters:
   ```bash
   xncmdclient -c 'ifoe_config_crypto; quit;'
   ```
   Expected: Crypto configuration accepted

2. **[server]** Provision TX crypto key:
   ```bash
   xncmdclient -c 'ifoe_set_tx_crypto_key <key_data>; quit;'
   ```
   Expected: TX key provisioned successfully

3. **[client]** Provision matching RX crypto key:
   ```bash
   xncmdclient -c 'ifoe_set_rx_crypto_key <key_data>; quit;'
   ```
   Expected: RX key provisioned successfully

4. **[server]** Verify encrypted communication via L2Ping:
   ```bash
   xncmdclient -c 'ifoe_ping_config 0 0 10; quit;'
   xncmdclient -c 'ifoe_ping_start 0 0; quit;'
   sleep 5
   xncmdclient -c 'ifoe_ping_poll 0; quit;'
   xncmdclient -c 'ifoe_ping_stop 0; quit;'
   ```
   Expected: L2Ping passes (req_failures=0, resp_failures=0)

5. **[client]** Disable RX crypto key:
   ```bash
   xncmdclient -c 'ifoe_disable_rx_crypto_key; quit;'
   ```
   Expected: RX key disabled

6. **[client]** Re-provision RX key (key rotation):
   ```bash
   xncmdclient -c 'ifoe_set_rx_crypto_key <new_key_data>; quit;'
   ```
   Expected: New RX key provisioned

7. **[server]** Inject XRSEC RAS error (component XRSEC=2):
   ```bash
   dmesg -C
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 2; quit;'
   sleep 3
   ```
   Expected: Error injection accepted

8. **[server]** Verify MCA report for XRSEC error:
   ```bash
   dmesg | grep -i 'mca\|cper\|xrsec'
   xncmdclient -c 'version; quit;'
   ```
   Expected: MCA record with XRSEC module ID, firmware responsive

9. **[server]** Clean XRSEC RAS error:
   ```bash
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 2 clean; quit;'
   ```
   Expected: Error cleaned

## Expected Result

- TX and RX crypto key provisioning succeeds via MCDI commands
- Encrypted L2Ping communication works end-to-end
- RX key disable clears crypto state on receive side
- Key rotation (disable + re-provision) works cleanly
- XRSEC RAS error injection produces correct MCA report
- Firmware continues operating after XRSEC error

## Failure Indicators

- Crypto key provisioning command returns error
- L2Ping fails after key provisioning (decryption failure)
- RX key disable does not clear state
- XRSEC RAS error crashes firmware
- No MCA record for XRSEC error
- Key rotation leaves stale crypto state

## Cleanup

- Disable RX crypto key on client:
  ```bash
  xncmdclient -c 'ifoe_disable_rx_crypto_key; quit;'
  ```
- Clean any remaining RAS errors
