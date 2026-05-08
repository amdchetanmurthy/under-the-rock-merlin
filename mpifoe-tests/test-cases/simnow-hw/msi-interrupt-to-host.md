---
topology: single-node
timeout: 180
pass_criteria: "MSI-X interrupts delivered from firmware to host and processed by IFoE driver"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MSI-X Interrupt Delivery to Host Test

## Purpose

Validates the interrupt_to_host driver (interrupt_to_host.c, 2 files) which handles MSI-X interrupt delivery from MPIFoE firmware to the host CPU. Tests that the firmware can signal events (MCDI completion, telemetry, error) to the host via PCIe MSI-X interrupts and that the host IFoE driver correctly receives and processes them.

## Category

positive, driver, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- IFoE kernel driver loaded (insmod ifoe.ko)
- PCIe MSI-X interrupts enabled (verify via /proc/interrupts)
- xncmdclient available on host

## Steps

1. **[host]** Verify MSI-X interrupts are registered by IFoE driver:
   ```bash
   cat /proc/interrupts | grep -i ifoe
   ```
   Expected: One or more MSI-X interrupt lines for IFoE device

2. **[host]** Record baseline interrupt count:
   ```bash
   cat /proc/interrupts | grep -i ifoe | awk '{print $1, $2}'
   ```
   Expected: Baseline count recorded

3. **[host]** Trigger MCDI command (generates completion interrupt):
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Command completes, interrupt delivered to host

4. **[host]** Verify interrupt count incremented:
   ```bash
   cat /proc/interrupts | grep -i ifoe | awk '{print $1, $2}'
   ```
   Expected: Interrupt count increased from baseline

5. **[host]** Enable telemetry (generates periodic interrupts):
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 3
   ```
   Expected: Telemetry interrupts delivered periodically

6. **[host]** Check interrupt count after telemetry period:
   ```bash
   cat /proc/interrupts | grep -i ifoe | awk '{print $1, $2}'
   ```
   Expected: Interrupt count has increased further (telemetry period interrupts)

7. **[host]** Verify no interrupt storm (rate check):
   ```bash
   # Check dmesg for interrupt storm warnings
   dmesg | grep -i 'irq.*nobody\|irq.*disabled\|interrupt.*storm'
   ```
   Expected: No interrupt storm warnings

8. **[host]** Check MCDI driver logging for interrupt handling:
   ```bash
   dmesg | grep -i 'ifoe.*mcdi\|ifoe.*irq'
   ```
   Expected: Normal interrupt handling messages, no errors

## Expected Result

- MSI-X interrupts registered for IFoE device in /proc/interrupts
- MCDI command completion triggers interrupt to host
- Telemetry periodic collection generates interrupts
- No interrupt storms or missed interrupts
- Host IFoE driver correctly processes received interrupts

## Failure Indicators

- No IFoE interrupts in /proc/interrupts (MSI-X not enabled)
- Interrupt count does not increment after MCDI command
- Interrupt storm detected in dmesg
- MCDI commands timeout (interrupt delivery broken)
- Host driver error messages related to interrupts

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
