---
topology: single-node
timeout: 180
pass_criteria: "IFoE container block offsets configured correctly and subsystem register access uses correct offsets"
priority: P1
stability: stable
validation_groups: [post-test]
---

# IFoE Container Block Offset Management Test

## Purpose

Validates the ifoe_container driver (ifoe_container.c, 3 files) which manages the mapping of IFoE subsystem register blocks within the container address space. Each IFoE subsystem (up to 18) has a block offset within the container that determines where its registers are mapped. Correct offset management is critical -- wrong offsets cause register access to hit the wrong subsystem.

## Category

positive, driver, boundary

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted with --eftest flag
- xncmdclient available

## Setup

1. **[host]** Configure IFoE subsystems in 4x200 mode (4 subsystems per port):
   ```bash
   xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: All configured subsystems active

## Steps

1. **[host]** Verify subsystem count matches port mode:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Config shows correct subsystem count for 4x200 mode

2. **[host]** Read IFoE container registers for subsystem 0:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_read 0 0; quit;' tlp=0
   ```
   Expected: Register value returned (subsystem 0 block accessible)

3. **[host]** Read IFoE container registers for subsystem 1 (different offset):
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_read 1 0; quit;' tlp=0
   ```
   Expected: Register value returned (subsystem 1 at different offset)

4. **[host]** Verify different subsystems return independent values:
   ```bash
   # Write distinct values to each subsystem
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_write 0 0 0xAA; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_write 1 0 0xBB; quit;' tlp=0
   # Read back and verify isolation
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_read 0 0; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'eftest ifoe_io_read 1 0; quit;' tlp=0
   ```
   Expected: Subsystem 0 reads 0xAA, subsystem 1 reads 0xBB (no cross-contamination)

5. **[host]** Verify all active subsystems are accessible:
   ```bash
   for ss in 0 1 2 3; do
     xncmdclient --force-enable-mmap -c "eftest ifoe_io_read $ss 0; quit;" tlp=0
   done
   ```
   Expected: All active subsystems respond to register reads

6. **[host]** Verify firmware stability:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware responsive

## Expected Result

- Each IFoE subsystem maps to a distinct block offset in the container
- Register reads/writes to different subsystems are independent (no cross-contamination)
- All configured subsystems are accessible via their container offsets
- Container block layout matches port mode configuration

## Failure Indicators

- Register read returns same value for different subsystems (offset collision)
- Write to subsystem N affects subsystem M (offset overlap)
- Access to valid subsystem returns error (offset calculation wrong)
- Firmware crash on subsystem register access

## Cleanup

- None required
