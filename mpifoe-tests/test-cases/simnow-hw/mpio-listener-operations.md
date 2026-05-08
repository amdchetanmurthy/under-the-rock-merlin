---
topology: single-node
timeout: 240
pass_criteria: "MPIO listener handles PHY configuration commands and GTA lane assignment correctly"
priority: P1
stability: stable
validation_groups: [post-test]
---

# MPIO Firmware Operations Test

## Purpose

Validates the MPIO (Multi-Purpose I/O) listener (mpio_listener.c) which handles commands from the MPIO processor. MPIO manages PHY lane assignment and GTA (Generic Transceiver Abstraction) configuration. Tests command registration, PHY config dispatch, and lane assignment verification.

## Category

positive, interaction

## Prerequisites

- Requires SimNow M228 model (needs MPIO firmware)
- MPIFoE firmware booted
- MPIO firmware running and communication channel established
- mp_listener framework initialized

## Steps

1. **[host]** Verify firmware booted with MPIO active:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware running (MPIO listener initialized during boot)

2. **[host]** Verify port enumeration reflects MPIO lane assignment:
   ```bash
   xncmdclient --force-enable-mmap -c 'enum_ports; quit;' tlp=0
   ```
   Expected: Ports enumerated with correct lane count per port mode

3. **[host]** Check port properties for PHY/lane info:
   ```bash
   xncmdclient --force-enable-mmap -c 'get_fixed_port_properties 0; quit;' tlp=0
   ```
   Expected: Lane count and GTA assignment visible in port properties

4. **[host]** Verify link state includes PHY-level info:
   ```bash
   xncmdclient --force-enable-mmap -c 'link_state 0; quit;' tlp=0
   ```
   Expected: Link state shows lane configuration from MPIO

5. **[host]** Test PRBS on MPIO-assigned lanes:
   ```bash
   xncmdclient --force-enable-mmap -c 'pma_prbs_tx 0 7; quit;' tlp=0
   sleep 2
   xncmdclient --force-enable-mmap -c 'pma_prbs_rx 0; quit;' tlp=0
   ```
   Expected: PRBS test runs on lanes assigned by MPIO

6. **[host]** Verify firmware stability after MPIO operations:
   ```bash
   xncmdclient --force-enable-mmap -c 'get_uptime; quit;' tlp=0
   ```
   Expected: Firmware responsive

## Expected Result

- MPIO listener initializes and registers PHY command handlers
- GTA lane assignment correctly maps to port configuration
- Port properties reflect MPIO-assigned lane count
- PHY operations (PRBS) work on MPIO-assigned lanes
- MPIO communication channel stable

## Failure Indicators

- Port enumeration shows wrong lane count
- PHY operations fail on assigned lanes
- MPIO listener crash during command dispatch
- Lane assignment mismatch (wrong lanes for port mode)
- Firmware panic from MPIO handler error

## Cleanup

- None required
