---
topology: single-node
timeout: 120
pass_criteria: "Network port address get/set operations reject invalid accelerator IDs, invalid netport handles, and correctly handle remote-only configurations"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Network Port Address Mapping Boundary Test

## Purpose

Validates boundary and error handling in ifoe_manager address mapping functions: set/get_src/dst_network_port_address. Tests: invalid accelerator ID (>= IFOE_HW_CFG_MAX_PHYS_ACC_ID returns EINVAL), invalid netport handle (EINVAL), remote-only link configurations, and the acc_id modulo MAX_ACC_ADDR_MAPPINGS_PER_PORT aliasing.

## Category

negative, error-handling

## Prerequisites

- MPIFoE firmware in PROVIDER phase with stations configured
- xncmdclient available

## Steps

1. **[host]** Set src address with valid netport handle:
   ```bash
   xncmdclient -c 'ifoe_set_src_net_addr 0 00:11:22:33:44:55 10.0.0.1; quit;'
   ```
   Expected: Success

2. **[host]** Set dst address with invalid accelerator ID (>= MAX):
   ```bash
   xncmdclient -c 'ifoe_set_dst_net_addr_map 0 9999 00:11:22:33:44:55 10.0.0.2; quit;'
   ```
   Expected: Returns EINVAL

3. **[host]** Set dst address with invalid netport handle:
   ```bash
   xncmdclient -c 'ifoe_set_dst_net_addr_map 9999 0 00:11:22:33:44:55 10.0.0.2; quit;'
   ```
   Expected: Returns EINVAL (netport_handle_from_mcdi validation fails)

4. **[host]** Get src address with invalid stride in payload:
   ```bash
   # Send set_src_net_addr with stride < sizeof(ifoe_cfg_map_addr_t)
   ```
   Expected: Returns EINVAL

5. **[host]** Get src address to verify set value persists:
   ```bash
   xncmdclient -c 'ifoe_get_src_net_addr 0; quit;'
   ```
   Expected: Returns 00:11:22:33:44:55 / 10.0.0.1

## Expected Result

- Valid set/get operations succeed with correct data
- Invalid accelerator ID returns EINVAL
- Invalid netport handle returns EINVAL
- Invalid stride returns EINVAL
- Address aliasing (acc_id % 256) works as documented

## Failure Indicators

- Invalid inputs accepted without error
- Address data corruption
- k_panic on invalid handle (should be error return)
- Remote MID address lookup fails

## Cleanup

- None required
