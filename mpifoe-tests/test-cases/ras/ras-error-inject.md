---
topology: single-node
timeout: 120
pass_criteria: "RAS error injected successfully, firmware continues running, MCA bank updated"
priority: P1
stability: stable
validation_groups: [post-test]
---

# RAS Error Injection Test

## Purpose

Validates the RAS (Reliability, Availability, Serviceability) error injection path using eftest ifoe_ras_inject_error. This test verifies that the firmware can handle injected errors gracefully -- updating the MCA bank, generating appropriate error records, and continuing to operate without crashing.

## Category

fault-injection, error-recovery

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Firmware built with --eftest flag (EFTEST commands available)
- xncmdclient available on host
- Host dmesg accessible for CPER record validation

## Steps

1. **[host]** Record firmware state before injection:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Firmware version and uptime recorded as baseline

2. **[host]** Clear dmesg buffer to isolate new messages:
   ```bash
   dmesg -C
   ```
   Expected: dmesg buffer cleared

3. **[host]** Inject RAS error on IFoE instance 0:
   ```bash
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 <error_type>; quit;'
   ```
   Expected: Error injection command accepted, no firmware crash

4. **[host]** Wait for error processing:
   ```bash
   sleep 5
   ```

5. **[host]** Verify firmware is still running (heartbeat check):
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Firmware responds, uptime has advanced beyond pre-injection value

6. **[host]** Check for MCA/CPER error records in dmesg:
   ```bash
   dmesg | grep -i 'mca\|cper\|ras\|ifoe.*error'
   ```
   Expected: Error records present indicating the injected error was captured

## Expected Result

- RAS error injection completes without firmware crash
- Firmware continues running after error injection (heartbeat check passes)
- MCA bank is updated with error information
- Error records (MCA/CPER) appear in host dmesg
- Uptime continues advancing (firmware not reset or hung)

## Failure Indicators

- Firmware crashes or hangs after error injection
- No MCA/CPER records in dmesg (error not propagated)
- Firmware uptime resets (unexpected reboot)
- xncmdclient timeout after error injection
- RAS inject command returns error

## Cleanup

- Verify firmware health:
  ```bash
  xncmdclient -c 'version; quit;'
  ```
