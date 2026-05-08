---
topology: single-node
timeout: 300
pass_criteria: "MCA bank registers contain correct error information after RAS injection with proper priority and address encoding"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MCA Register Bank Content Verification Test

## Purpose

Validates the MCA (Machine Check Architecture) driver (mca_drv.c, 3 files) register bank content after error injection. Tests that mca_drv_report_error correctly populates MCA bank registers with error information including ErrorCodeExt (module ID), MCA priority mapping (CORRECTED for SEC, SYSTEM_FATAL for DED), and address encoding per component-specific formats (RAS_IFOE_MCA_ADDRESS, etc.).

## Category

positive, fault-injection, data-integrity

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- MCA target address configured (via ASP SET_MCA_TARGET)
- xncmdclient available
- Host dmesg accessible for CPER records

## Steps

1. **[host]** Configure IFoE and ensure RAS subsystem ready:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase, RAS subsystem initialized

2. **[host]** Clear dmesg for clean baseline:
   ```bash
   dmesg -C
   ```

3. **[host]** Inject SEC (correctable) error on IFOE component:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_ras_inject_error 0 4; quit;' tlp=0
   sleep 3
   ```
   Expected: SEC error injected (component IFOE=4)

4. **[host]** Verify MCA bank content for SEC error:
   ```bash
   dmesg | grep -i 'mca\|cper'
   ```
   Expected: MCA record shows:
   - ErrorCodeExt = MODULE_ID_IFOE
   - Priority = CORRECTED (SEC error)
   - Address encoding per RAS_IFOE_MCA_ADDRESS format

5. **[host]** Inject DED (uncorrectable) error:
   ```bash
   dmesg -C
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_ras_inject_error 0 4 ded; quit;' tlp=0
   sleep 3
   ```
   Expected: DED error injected

6. **[host]** Verify MCA bank content for DED error:
   ```bash
   dmesg | grep -i 'mca\|cper'
   ```
   Expected: MCA record shows:
   - ErrorCodeExt = MODULE_ID_IFOE
   - Priority = SYSTEM_FATAL (DED error)

7. **[host]** Inject error on XRMAC component:
   ```bash
   dmesg -C
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_ras_inject_error 0 0; quit;' tlp=0
   sleep 3
   dmesg | grep -i 'mca\|cper'
   ```
   Expected: MCA record with ErrorCodeExt = MODULE_ID_XRMAC

8. **[host]** Inject error on XRPFC component:
   ```bash
   dmesg -C
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_ras_inject_error 0 1; quit;' tlp=0
   sleep 3
   dmesg | grep -i 'mca\|cper'
   ```
   Expected: MCA record with ErrorCodeExt = MODULE_ID_XRPFC

9. **[host]** Verify firmware still running after all injections:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'get_uptime; quit;' tlp=0
   ```
   Expected: Firmware responsive, uptime advancing

## Expected Result

- MCA bank registers populated with correct error information
- ErrorCodeExt correctly maps to source component module ID
- MCA priority correctly maps SEC -> CORRECTED, DED -> SYSTEM_FATAL
- Address encoding follows component-specific format
- Multiple error injections do not corrupt MCA bank state
- CPER records generated for each MCA report

## Failure Indicators

- MCA bank not updated after error injection
- Wrong ErrorCodeExt (module ID mismatch)
- Wrong priority (SEC mapped to FATAL or vice versa)
- Address encoding does not match component format
- No CPER record in dmesg
- Firmware crash from MCA bank access

## Cleanup

- Clean injected errors:
  ```bash
  xncmdclient --force-enable-mmap -c 'eftest ifoe_ras_inject_error 0 0 clean; quit;' tlp=0
  xncmdclient --force-enable-mmap -c 'eftest ifoe_ras_inject_error 0 1 clean; quit;' tlp=0
  xncmdclient --force-enable-mmap -c 'eftest ifoe_ras_inject_error 0 4 clean; quit;' tlp=0
  ```
