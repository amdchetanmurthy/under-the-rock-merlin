---
topology: single-node
timeout: 240
pass_criteria: "PM listener receives and handles PM commands correctly with proper response"
priority: P1
stability: stable
validation_groups: [post-test]
---

# PM Firmware Interaction via Listener Test

## Purpose

Validates the PM (Platform Management) listener (mp1_pm_listener.c, mp1_pm_cmd_handler.c) which handles commands from the PM processor. Tests command registration, dispatch, and handling for PM-initiated operations such as FLR notification, power management, and reset coordination. PM listener is part of the mp_listener framework.

## Category

positive, interaction

## Prerequisites

- Requires SimNow A+A model (needs PM firmware)
- MPIFoE firmware booted
- PM firmware running and communication channel established
- mp_listener framework initialized

## Steps

1. **[host]** Verify firmware is booted and PM channel active:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   ```
   Expected: Firmware running (PM listener initialized during boot)

2. **[host]** Verify IFoE configuration (PM provides topology info):
   ```bash
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: Config reflects PM-provided topology

3. **[host]** Check PM status register:
   ```bash
   xncmdclient --force-enable-mmap -c 'read32 0x034000d8; quit;' tlp=0
   ```
   Expected: PM status bits indicate active communication

4. **[host]** Test entity reset path (PM-related reset hooks):
   ```bash
   xncmdclient --force-enable-mmap -c 'entity_reset; quit;' tlp=0
   ```
   Expected: Reset completes (PM listener's reset hook runs)

5. **[host]** Verify PM listener recovery after reset:
   ```bash
   xncmdclient --force-enable-mmap -c 'version; quit;' tlp=0
   xncmdclient --force-enable-mmap -c 'ifoe_get_config; quit;' tlp=0
   ```
   Expected: PM listener functional after entity reset

6. **[host]** Verify firmware stability:
   ```bash
   xncmdclient --force-enable-mmap -c 'get_uptime; quit;' tlp=0
   ```
   Expected: Firmware responsive, uptime advancing

## Expected Result

- PM listener initializes during boot and registers command handlers
- PM commands dispatched to correct handler functions
- PM-provided topology information reflected in IFoE config
- Entity reset includes PM listener's reset hook
- PM listener recovers after reset

## Failure Indicators

- PM listener not initialized (PM commands not handled)
- PM topology not reflected in IFoE config
- Entity reset crashes PM listener
- PM communication channel drops
- Firmware panic from PM command handler error

## Cleanup

- None required
