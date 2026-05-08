---
topology: single-node
timeout: 240
pass_criteria: "UPI2 PHY registers accessible and SD controller operations complete without error"
priority: P2
stability: stable
validation_groups: [post-test]
---

# UPI2 PHY Register Operations via SimNow Test

## Purpose

Validates the UPI2 driver (upi2.c, 2 files) which provides access to the PHY layer SD (SerDes) controller. Tests register read/write operations, PHY initialization, and lane configuration. UPI2 is currently only testable via SimNow as it requires the SD controller mock.

## Category

positive, driver

## Prerequisites

- Requires SimNow M112/M222 model
- MPIFoE firmware booted
- SimNow SD controller mock active
- xncmdclient available

## Setup

1. **[host]** Boot SimNow and configure IFoE:
   ```bash
   /simnow/xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Verify PHY is initialized by checking port properties:
   ```bash
   xncmdclient --force-enable-mmap -c 'get_fixed_port_properties 0; quit;' tlp=0
   ```
   Expected: Port properties include PHY/lane information

2. **[host]** Read UPI2-related registers via SMN:
   ```bash
   # Read UPI2 base register
   xncmdclient --force-enable-mmap -c 'read32 0x11000000; quit;' tlp=0
   ```
   Expected: Non-zero value (SD controller present in SimNow model)

3. **[host]** Run PRBS test to exercise PHY lanes:
   ```bash
   xncmdclient --force-enable-mmap -c 'pma_prbs_tx 0 7; quit;' tlp=0
   sleep 2
   xncmdclient --force-enable-mmap -c 'pma_prbs_rx 0; quit;' tlp=0
   ```
   Expected: PRBS pattern transmitted and checked (SimNow may report perfect BER)

4. **[host]** Configure lane parameters:
   ```bash
   xncmdclient --force-enable-mmap -c 'pma_configure_lane 0 0; quit;' tlp=0
   ```
   Expected: Lane configuration accepted

5. **[host]** Verify link state after PHY operations:
   ```bash
   xncmdclient --force-enable-mmap -c 'link_state 0; quit;' tlp=0
   ```
   Expected: Link state consistent (PHY operations did not break link)

6. **[host]** Verify firmware stability:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware responsive

## Expected Result

- UPI2 registers readable via SMN path
- PRBS test exercises PHY lanes (SimNow mock returns clean results)
- Lane configuration accepted without error
- PHY operations do not destabilize link state
- SD controller mock in SimNow provides expected register responses

## Failure Indicators

- UPI2 register read returns 0xDEADDEAD (unmapped address)
- PRBS test times out
- Lane configuration returns error
- Link state corrupted after PHY operations
- Firmware crash during UPI2 access

## Cleanup

- None required (SimNow model reset on test completion)
