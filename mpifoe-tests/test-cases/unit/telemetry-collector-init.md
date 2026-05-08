---
topology: single-node
timeout: 120
pass_criteria: "Telemetry collector initializes datasets, observer selection succeeds with valid category mask, and rejects invalid observer IDs"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Telemetry Collector Initialization Unit Test

## Purpose

Validates the telemetry manager's collector initialization and observer selection logic (telemetry_manager.c). Tests telemetry_mgr_select_telemetry for valid/invalid inputs, ensures proper mutex protection, and verifies that the collector_initialised flag gates all operations.

## Category

positive, negative, unit

## Prerequisites

- MPIFoE firmware in PROVIDER phase or later
- Telemetry subsystem has completed HBM allocation
- xncmdclient available

## Steps

1. **[host]** Verify telemetry is running:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info 0; quit;'
   ```
   Expected: Returns telemetry info for category 0

2. **[host]** Select telemetry for a valid observer with valid category mask:
   ```bash
   xncmdclient -c 'ifoe_telemetry_select 0 0x1; quit;'
   ```
   Expected: Returns success with const_data_size and dyn_data_size

3. **[host]** Attempt to select with invalid observer ID (>= TELEMETRY_OBSERVER_ID_COUNT):
   ```bash
   xncmdclient -c 'ifoe_telemetry_select 255 0x1; quit;'
   ```
   Expected: Returns EINVAL

4. **[host]** Attempt to select with zero category mask:
   ```bash
   xncmdclient -c 'ifoe_telemetry_select 0 0x0; quit;'
   ```
   Expected: Returns EINVAL

5. **[host]** Attempt double-select when delivery is already enabled:
   ```bash
   xncmdclient -c 'ifoe_telemetry_control 0 1; quit;'
   xncmdclient -c 'ifoe_telemetry_select 0 0x1; quit;'
   ```
   Expected: Returns EBUSY

## Expected Result

- Valid observer/category returns success with correct size calculations
- Invalid observer ID returns EINVAL
- Zero category mask returns EINVAL
- Already-active observer returns EBUSY
- Mutex protects concurrent access

## Failure Indicators

- Valid selection fails with unexpected error
- Invalid inputs accepted without error
- Size calculation returns 0 for valid categories
- Mutex deadlock causes hang
- collector_initialised not set after init

## Cleanup

- Disable telemetry delivery: `xncmdclient -c 'ifoe_telemetry_control 0 0; quit;'`
