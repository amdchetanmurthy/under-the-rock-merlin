---
topology: single-node
timeout: 60
pass_criteria: "ifoe_get_active_accelerators returns at least one active accelerator"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Accelerator Discovery

## Purpose

Validates that the IFoE subsystem has discovered and activated accelerators via ifoe_get_active_accelerators. Active accelerators are required for L2Ping, traffic, and all IFoE fabric operations.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- IFoE BIOS configuration applied with valid subsystem mask
- xncmdclient available on host

## Steps

1. **[host]** Query active accelerators:
   ```bash
   xncmdclient -c 'ifoe_get_active_accelerators; quit;'
   ```
   Expected: Returns list of active accelerator IDs with status

2. **[host]** Query enabled accelerators for comparison:
   ```bash
   xncmdclient -c 'ifoe_get_enabled_accelerators; quit;'
   ```
   Expected: Returns list of enabled accelerators (active should be a subset of enabled)

3. **[host]** Query local accelerators:
   ```bash
   xncmdclient -c 'ifoe_get_local_accelerators; quit;'
   ```
   Expected: Returns local accelerator information

## Expected Result

- At least one active accelerator is reported
- Active accelerator count is consistent with the configured subsystem mask
- Active accelerators are a subset of enabled accelerators
- Local accelerator information is valid

## Failure Indicators

- Zero active accelerators returned
- Active accelerator count exceeds enabled count
- Error or timeout from ifoe_get_active_accelerators
- Inconsistency between active, enabled, and local accelerator lists

## Cleanup

- None required (read-only inspection)
