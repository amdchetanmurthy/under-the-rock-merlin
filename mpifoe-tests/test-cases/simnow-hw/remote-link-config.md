---
topology: single-node
timeout: 300
pass_criteria: "Asymmetric dual-MID link configuration correctly handles remote-only links"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Asymmetric Dual-MID Link Configuration Test

## Purpose

Validates the remote-only link configuration path (ifoe_manager_remote_only_links() in ifoe_manager.c) and cross-MID link configuration RPC (logical_link_rpc.c). In asymmetric dual-MID setups, some links are "remote-only" -- configured on one MID but the physical port is on the other MID. Tests correct handling of this asymmetry.

## Category

positive, integration, config-matrix

## Prerequisites

- Requires SimNow M222 model (dual-MID required)
- MPIFoE firmware booted on both MIDs
- Chip IPC link established
- Asymmetric port assignment configured

## Setup

1. **[host]** Boot dual-MID SimNow with asymmetric config:
   ```bash
   /simnow/xncmdclient --force-enable-mmap \
     -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: PROVIDER phase on dual-MID system

## Steps

1. **[host]** Verify dual-MID topology:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Config shows dual-MID with port assignment

2. **[host]** Query remote-only link status:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_enum_stations; quit;' tlp=0
   ```
   Expected: Stations include remote-only links

3. **[host]** Get destination network address map (includes remote links):
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_dst_net_addr_map; quit;' tlp=0
   ```
   Expected: Address map includes entries for remote-only links

4. **[host]** Get source network port addresses (local vs remote):
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_src_net_addr; quit;' tlp=0
   ```
   Expected: Source addresses correctly reflect local and remote ports

5. **[host]** Advance to TENANT with remote-only config:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_next_phase TENANT; quit;' tlp=0
   ```
   Expected: Phase transition succeeds with remote-only link config propagated

6. **[host]** Verify remote-only links survive phase transition:
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_enum_stations; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_get_dst_net_addr_map; quit;' tlp=0
   ```
   Expected: Remote-only link configuration preserved

7. **[host]** Verify firmware stability:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware responsive

## Expected Result

- ifoe_manager_remote_only_links() correctly identifies remote-only links
- Remote-only link configuration propagated via RPC to owning MID
- Address maps correctly reflect asymmetric port ownership
- Phase transitions preserve remote-only link state
- Cross-MID RPC for link config completes without timeout

## Failure Indicators

- Remote-only links not in station enumeration
- Address map missing remote-only entries
- Phase transition fails with remote-only config
- Cross-MID RPC timeout during link config
- k_panic from phase desync between MIDs

## Cleanup

- None required (SimNow reset handles cleanup)
