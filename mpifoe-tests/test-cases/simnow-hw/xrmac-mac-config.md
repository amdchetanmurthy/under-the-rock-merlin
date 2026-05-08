---
topology: single-node
timeout: 300
pass_criteria: "XRMAC driver configures MAC, reads telemetry counters, and handles RAS errors correctly"
priority: P1
stability: stable
validation_groups: [post-test]
---

# XRMAC MAC Configuration, Telemetry, and RAS Test

## Purpose

Validates the XRMAC driver (xrmac_drv.c, 6 files) which manages the MAC layer of IFoE network ports. Tests MAC configuration (speed, FEC mode, lane count), MAC telemetry counter collection, and XRMAC-specific RAS error injection/clean. The XRMAC is one of three IFoE subsystem components (along with XRPFC and XRSEC) that require hardware register access.

## Category

positive, driver, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- xncmdclient available on host
- At least one network port enumerated

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| port_id | 0 | 0-3 | Network port to configure |
| port_mode | 4x200 | 1x800, 2x400, 4x200 | Port mode configuration |

## Setup

1. **[host]** Configure IFoE subsystems and advance to PROVIDER phase:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Enumerate ports and verify MAC is initialized:
   ```bash
   xncmdclient -c 'enum_ports; quit;'
   ```
   Expected: Ports enumerated, port count matches port_mode configuration

2. **[host]** Query MAC state on port 0:
   ```bash
   xncmdclient -c 'mac_state 0; quit;'
   ```
   Expected: MAC state reported with speed, FEC mode, and lane configuration

3. **[host]** Read MAC-level telemetry counters:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 2
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: Telemetry counters incrementing, XRMAC counters non-zero for active port

4. **[host]** Verify fixed port properties include XRMAC attributes:
   ```bash
   xncmdclient -c 'get_fixed_port_properties 0; quit;'
   ```
   Expected: Speed, lane count, and MAC capabilities reported

5. **[host]** Inject XRMAC RAS error (component XRMAC=0):
   ```bash
   dmesg -C
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 0; quit;'
   sleep 3
   ```
   Expected: Error injection accepted, firmware continues running

6. **[host]** Verify MCA report for XRMAC error:
   ```bash
   dmesg | grep -i 'mca\|cper\|xrmac'
   xncmdclient -c 'version; quit;'
   ```
   Expected: MCA record with ErrorCodeExt = MODULE_ID_XRMAC, firmware responsive

7. **[host]** Clean XRMAC RAS error:
   ```bash
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 0 clean; quit;'
   ```
   Expected: Error cleaned, state restored

## Expected Result

- XRMAC MAC initializes with correct speed and FEC for configured port mode
- MAC state query returns consistent configuration
- Telemetry counters for XRMAC subsystem increment correctly
- RAS error injection produces correct MCA report with XRMAC module ID
- RAS error clean restores XRMAC state
- Firmware remains stable throughout all operations

## Failure Indicators

- MAC state returns unexpected speed or lane count
- Telemetry counters remain zero after enabling
- RAS error injection crashes firmware
- No MCA record generated for XRMAC error
- Error clean fails to restore state
- xncmdclient timeouts during any step

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
- Clean any remaining injected errors
