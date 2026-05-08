---
topology: single-node
timeout: 180
pass_criteria: "RSMU register access control works correctly and register operations complete without error"
priority: P1
stability: stable
validation_groups: [post-test]
---

# RSMU Register Access Control Test

## Purpose

Validates the IFoE RSMU driver (ifoe_rsmu.c, 2 files) which provides access to the RSMU (Register Status/Management Unit) registers within the IFoE subsystem. Tests register read/write operations, access control enforcement, and interaction with the IFoE subsystem configuration.

## Category

positive, driver

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- xncmdclient available

## Setup

1. **[host]** Configure IFoE subsystems:
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Read RSMU registers via IFoE I/O read:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_read 0 0; quit;' tlp=0
   ```
   Expected: Register value returned without error

2. **[host]** Write to RSMU register:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_write 0 0 0x1; quit;' tlp=0
   ```
   Expected: Write accepted

3. **[host]** Read back and verify:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_read 0 0; quit;' tlp=0
   ```
   Expected: Value matches what was written

4. **[host]** Test RSMU access on multiple subsystems:
   ```bash
   for ss in 0 1 2 3; do
     xncmdclient --force-enable-mmap -c "eftest ifoe_io_read $ss 0; quit;" tlp=0
   done
   ```
   Expected: Each subsystem RSMU accessible independently

5. **[host]** Verify firmware stability after RSMU operations:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Firmware responsive, config unchanged

## Expected Result

- RSMU registers readable and writable via eftest I/O commands
- Read-after-write returns correct value
- Each subsystem has independent RSMU register set
- RSMU operations do not affect IFoE configuration state

## Failure Indicators

- RSMU register read returns error
- Read-after-write mismatch (data corruption)
- RSMU access on one subsystem affects another
- Firmware crash during RSMU operations

## Cleanup

- None required
