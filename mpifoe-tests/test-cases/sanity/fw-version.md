---
topology: single-node
timeout: 30
pass_criteria: "xncmdclient returns a valid firmware version string within 5 seconds"
priority: P0
stability: stable
validation_groups: [pre-test]
---

# Firmware Version Check

## Purpose

Validates that the MPIFoE firmware is responsive and reports a valid version string via MC_CMD_GET_VERSION. This is the most fundamental health check -- if the firmware cannot respond to a version query, all other tests will fail.

## Category

positive

## Prerequisites

- MPIFoE firmware booted (any phase)
- xncmdclient available on host
- PCIe link to MI450 established

## Steps

1. **[host]** Query firmware version via MCDI:
   ```bash
   xncmdclient -c 'version; quit;'
   ```
   Expected: Returns firmware version string (e.g., `0.14.4.0`) within 5 seconds

2. **[host]** Verify version string is non-empty and well-formed:
   Expected: Version string matches pattern `<major>.<minor>.<patch>.<build>` with numeric components

## Expected Result

- xncmdclient returns a firmware version string within 5 seconds
- Version string is non-empty and follows semantic versioning format
- No error or timeout reported by xncmdclient

## Failure Indicators

- xncmdclient hangs or times out (firmware hung)
- Empty or garbled version string
- "connection refused" or "device not found" error
- xncmdclient returns non-zero exit code

## Cleanup

- None required
