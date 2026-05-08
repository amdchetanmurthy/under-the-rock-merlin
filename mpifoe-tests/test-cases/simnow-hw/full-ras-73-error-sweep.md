---
topology: single-node
timeout: 900
pass_criteria: "All 73 RAS error types from conversion table injected and cleaned without firmware crash"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Full 73 RAS Error Type Sweep Test

## Purpose

Validates all 73 RAS error types defined in the ras_conv_table across all 5 components (XRMAC, XRPFC, XRSEC, EX, IFOE). The conversion table maps each component+element to an external error ID, error type (SEC/DED), and MCA priority. This test exercises the full sweep: inject each error, verify MCA report, clean the error, and confirm firmware continues. Tests the binary search in ras_ss_get_external_error_id for all entries.

## Category

fault-injection, stress, data-integrity

## Prerequisites

- Requires MI450 hardware (not SimNow -- all 5 components needed)
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- MCA target address configured
- xncmdclient available
- Host dmesg accessible

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| components | 0,1,2,3,4 | 0-4 | Component IDs: XRMAC=0, XRPFC=1, XRSEC=2, EX=3, IFOE=4 |

## Steps

1. **[host]** Configure IFoE and record baseline:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   xncmdclient -c 'version; quit;'
   ```
   Expected: PROVIDER phase reached

2. **[host]** Sweep XRMAC errors (component 0):
   ```bash
   for elem in $(seq 0 14); do
     dmesg -C
     xncmdclient -c "eftest ifoe_ras_inject_error 0 0 $elem; quit;"
     sleep 1
     dmesg | grep -c 'mca\|cper'
     xncmdclient -c "eftest ifoe_ras_inject_error 0 0 $elem clean; quit;"
   done
   xncmdclient -c 'version; quit;'
   ```
   Expected: Each XRMAC error injected, MCA reported, cleaned; firmware responsive

3. **[host]** Sweep XRPFC errors (component 1):
   ```bash
   for elem in $(seq 0 12); do
     dmesg -C
     xncmdclient -c "eftest ifoe_ras_inject_error 0 1 $elem; quit;"
     sleep 1
     dmesg | grep -c 'mca\|cper'
     xncmdclient -c "eftest ifoe_ras_inject_error 0 1 $elem clean; quit;"
   done
   xncmdclient -c 'version; quit;'
   ```
   Expected: Each XRPFC error handled correctly

4. **[host]** Sweep XRSEC errors (component 2):
   ```bash
   for elem in $(seq 0 18); do
     dmesg -C
     xncmdclient -c "eftest ifoe_ras_inject_error 0 2 $elem; quit;"
     sleep 1
     dmesg | grep -c 'mca\|cper'
     xncmdclient -c "eftest ifoe_ras_inject_error 0 2 $elem clean; quit;"
   done
   xncmdclient -c 'version; quit;'
   ```
   Expected: Each XRSEC error handled correctly

5. **[host]** Sweep EX errors (component 3):
   ```bash
   for elem in $(seq 0 10); do
     dmesg -C
     xncmdclient -c "eftest ifoe_ras_inject_error 0 3 $elem; quit;"
     sleep 1
     dmesg | grep -c 'mca\|cper'
     xncmdclient -c "eftest ifoe_ras_inject_error 0 3 $elem clean; quit;"
   done
   xncmdclient -c 'version; quit;'
   ```
   Expected: Each EX error handled correctly

6. **[host]** Sweep IFOE errors (component 4):
   ```bash
   for elem in $(seq 0 15); do
     dmesg -C
     xncmdclient -c "eftest ifoe_ras_inject_error 0 4 $elem; quit;"
     sleep 1
     dmesg | grep -c 'mca\|cper'
     xncmdclient -c "eftest ifoe_ras_inject_error 0 4 $elem clean; quit;"
   done
   xncmdclient -c 'version; quit;'
   ```
   Expected: Each IFOE error handled correctly

7. **[host]** Final firmware health check:
   ```bash
   xncmdclient -c 'version; quit;'
   xncmdclient -c 'get_uptime; quit;'
   xncmdclient -c 'ifoe_get_config; quit;'
   ```
   Expected: Firmware responsive, config intact after all 73 injections

## Expected Result

- All 73 error types from ras_conv_table inject and clean successfully
- Each injection produces correct MCA report with matching module ID
- Binary search in ras_ss_get_external_error_id finds all entries
- SEC/DED toggle via error_flags works for all error types
- Firmware continues running after complete sweep
- No assertion failures from external_error_id lookup

## Failure Indicators

- Any error injection crashes firmware
- MCA report missing for any error type
- Wrong module ID in MCA report
- Error clean fails for any type
- __ASSERT_NO_MSG fires during sweep (lookup failure)
- Firmware crash after partial sweep

## Cleanup

- Verify firmware health:
  ```bash
  xncmdclient -c 'version; quit;'
  ```
- Clean any remaining errors
