---
topology: single-node
timeout: 300
pass_criteria: "XRPFC priority flow control configures correctly, queue mapping works, and RAS errors handled"
priority: P1
stability: stable
validation_groups: [post-test]
---

# XRPFC Priority Flow Control, Queue Config, and RAS Test

## Purpose

Validates the XRPFC driver (xrpfc_drv.c, 7 files) which manages Priority Flow Control for IFoE network ports. Tests PFC queue configuration, priority-to-queue mapping, flow control enable/disable, and XRPFC-specific RAS error injection. PFC is critical for lossless IFoE traffic -- incorrect PFC configuration causes packet drops under congestion.

## Category

positive, driver, integration

## Prerequisites

- Requires MI450 hardware (not SimNow)
- MPIFoE firmware booted with --eftest flag
- Firmware in PROVIDER phase or later
- xncmdclient available on host
- Network port active (link up preferred)

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| port_id | 0 | 0-3 | Network port to configure |
| ifoe_ss_idx | 0 | 0-17 | IFoE subsystem index |

## Setup

1. **[host]** Configure IFoE subsystems:
   ```bash
   xncmdclient -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; quit;'
   xncmdclient -c 'ifoe_next_phase PROVIDER; quit;'
   ```
   Expected: PROVIDER phase reached

## Steps

1. **[host]** Query current PFC configuration:
   ```bash
   xncmdclient -c 'ifoe_get_config; quit;'
   ```
   Expected: PFC-related fields visible in IFoE config output

2. **[host]** Verify port has expected PFC channel mapping:
   ```bash
   xncmdclient -c 'mac_state 0; quit;'
   ```
   Expected: MAC state includes PFC channel information (IFOE_REQ, IFOE_RESP, NON_IFOE)

3. **[host]** Run L2Ping to validate all three PFC channels:
   ```bash
   xncmdclient -c 'ifoe_ping_config 0 0 10; quit;'
   xncmdclient -c 'ifoe_ping_start 0 0; quit;'
   sleep 5
   xncmdclient -c 'ifoe_ping_poll 0; quit;'
   xncmdclient -c 'ifoe_ping_stop 0; quit;'
   ```
   Expected: req_failures=0, resp_failures=0, non_ifoe_failures=0

4. **[host]** Enable telemetry and check XRPFC counters:
   ```bash
   xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'
   sleep 2
   xncmdclient -c 'ifoe_telemetry_info; quit;'
   ```
   Expected: PFC-related telemetry counters present and non-zero on active port

5. **[host]** Inject XRPFC RAS error (component XRPFC=1):
   ```bash
   dmesg -C
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 1; quit;'
   sleep 3
   ```
   Expected: Error injection accepted

6. **[host]** Verify MCA report for XRPFC error:
   ```bash
   dmesg | grep -i 'mca\|cper\|xrpfc'
   xncmdclient -c 'version; quit;'
   ```
   Expected: MCA record with XRPFC module ID, firmware responsive

7. **[host]** Clean XRPFC RAS error:
   ```bash
   xncmdclient -c 'eftest ifoe_ras_inject_error 0 1 clean; quit;'
   ```
   Expected: Error cleaned

## Expected Result

- PFC channels correctly mapped (IFoE Request, IFoE Response, Non-IFoE)
- L2Ping passes on all three PFC channels
- XRPFC telemetry counters report flow control activity
- RAS error injection produces correct MCA report
- Firmware continues operating after PFC-related error

## Failure Indicators

- L2Ping failures on any PFC channel (req_failures > 0)
- PFC telemetry counters remain zero
- XRPFC RAS error injection crashes firmware
- No MCA record for XRPFC error
- PFC channel misconfiguration causes traffic drops

## Cleanup

- Disable telemetry:
  ```bash
  xncmdclient -c 'ifoe_telemetry_ctrl disable; quit;'
  ```
- Stop any active L2Ping:
  ```bash
  xncmdclient -c 'ifoe_ping_stop 0; quit;'
  ```
