---
topology: single-node
timeout: 60
pass_criteria: "ifoe_telemetry_info reports telemetry collection is active with non-zero data"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Telemetry Running Check

## Purpose

Validates that the IFoE telemetry subsystem is active and collecting data via ifoe_telemetry_info. The telemetry manager thread runs at a 1-second period, so after boot the telemetry system should be operational.

## Category

positive

## Prerequisites

- MPIFoE firmware booted and in PROVIDER phase or later
- Telemetry manager thread running (built into firmware)
- xncmdclient available on host

## Steps

1. **[host]** Query telemetry info:
   ```bash
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Returns telemetry status information indicating the collection system is active

2. **[host]** Enable telemetry collection if not already active:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   ```
   Expected: Telemetry collection enabled without error

3. **[host]** Wait for at least one collection cycle and re-check:
   ```bash
   sleep 2
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Telemetry info shows updated data (collection count incremented)

## Expected Result

- ifoe_telemetry_info returns valid telemetry status
- Telemetry collection is active (enabled state)
- After waiting 2+ seconds, telemetry data shows activity (non-zero collection counts)

## Failure Indicators

- ifoe_telemetry_info returns error or empty response
- Telemetry collection stuck in disabled state
- Zero telemetry data after multiple collection periods
- Timeout from xncmdclient during telemetry queries

## Cleanup

- None required (telemetry state is left as-is)
