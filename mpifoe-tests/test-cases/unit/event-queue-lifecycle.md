---
topology: single-node
timeout: 120
pass_criteria: "Event queue initializes, sends events, processes doorbells, and finalizes without error"
priority: P1
stability: stable
validation_groups: [post-test]
---

# Event Queue Lifecycle Unit Test

## Purpose

Validates the event queue subsystem (event_queue.c) through its full lifecycle: init, event delivery, doorbell processing, and fini. The event queue is critical for notifying the host of asynchronous firmware events (link changes, station state changes). Tests both PF and VF event queues.

## Category

positive, unit

## Prerequisites

- MPIFoE firmware booted
- xncmdclient available
- Host driver loaded with EVQ allocated

## Steps

1. **[host]** Initialize PF event queue:
   ```bash
   xncmdclient -c 'init_evq 1; quit;'
   ```
   Expected: Returns success, EVQ allocated

2. **[host]** Verify event queue is accepting events by triggering a station link change:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```
   Expected: Phase transition triggers datapath hooks; EVQ thread wakes

3. **[host]** Check that EVQ read index doorbell updates are processed:
   ```bash
   xncmdclient -c 'ifoe_get_current_phase; quit;'
   ```
   Expected: Firmware responsive; EVQ thread not stuck

4. **[host]** Attempt double initialization (should return EALREADY):
   ```bash
   xncmdclient -c 'init_evq 1; quit;'
   ```
   Expected: Returns EALREADY

5. **[host]** Finalize event queue:
   ```bash
   xncmdclient -c 'entity_reset; quit;'
   ```
   Expected: Reset hook calls fini_evq; EVQ cleaned up

## Expected Result

- EVQ initializes once successfully, rejects double-init
- Doorbell processing wakes the evq_thread
- Entity reset properly finalizes the EVQ
- No events lost or EVQ state corruption

## Failure Indicators

- init_evq returns error on first call
- Double init_evq does not return EALREADY
- EVQ thread hangs (firmware becomes unresponsive)
- fini_evq called on uninitialized EVQ (should return ENOENT)

## Cleanup

- entity_reset to return to clean state
