---
topology: single-node
timeout: 120
pass_criteria: "CPER record generated in dmesg after RAS error injection with valid error section data"
priority: P1
stability: stable
validation_groups: [post-test]
---

# CPER Record Validation Test

## Purpose

Validates that RAS error injection produces a properly formatted CPER (Common Platform Error Record) in the host dmesg. CPER records are the standard mechanism for reporting hardware errors to the OS and are required for enterprise RAS compliance. This test focuses on the error record content and format rather than the injection itself.

## Category

fault-injection, data-integrity

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Firmware built with --eftest flag
- xncmdclient available on host
- Root access on host for dmesg inspection
- ras-error-inject test should be run first (or injection performed as part of this test)

## Steps

1. **[host]** Clear dmesg buffer:
   ```bash
   dmesg -C
   ```
   Expected: Buffer cleared

2. **[host]** Inject RAS error to trigger CPER generation:
   ```bash
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 <error_type>; quit;'
   ```
   Expected: Error injected without crash

3. **[host]** Wait for CPER record to be generated and logged:
   ```bash
   sleep 5
   ```

4. **[host]** Search dmesg for CPER records:
   ```bash
   dmesg | grep -i 'cper'
   ```
   Expected: CPER-related messages present in dmesg

5. **[host]** Capture full error record context:
   ```bash
   dmesg | grep -i 'mca\|cper\|hardware error\|ifoe' | tail -30
   ```
   Expected: Error record with section type, severity, and error-specific data

6. **[host]** Verify firmware is still operational:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Firmware responsive

## Expected Result

- CPER record appears in dmesg within 5 seconds of error injection
- CPER record contains valid error section data (section type, severity level)
- Error record correctly identifies the source as IFoE/MPIFoE
- Firmware remains operational after CPER generation
- No duplicate or corrupted CPER records

## Failure Indicators

- No CPER record in dmesg after error injection
- CPER record with invalid or missing section data
- Corrupted or truncated CPER record
- Multiple unexpected CPER records (error storm)
- Firmware crash during CPER generation
- CPER source does not identify IFoE subsystem

## Cleanup

- None required (dmesg records are informational)
