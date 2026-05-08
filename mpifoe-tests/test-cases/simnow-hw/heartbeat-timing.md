---
topology: single-node
timeout: 120
pass_criteria: "Boot heartbeat increments at expected interval with timing accuracy within 10%"
priority: P2
stability: stable
validation_groups: [post-test]
---

# Boot Heartbeat Timing Accuracy Test

## Purpose

Validates the heartbeat timing in the main boot loop (main.c). The heartbeat counter increments at a fixed interval, and interrupt_inspector_check_pics_and_repair() runs each iteration. Tests that the heartbeat rate is consistent and that the uptime counter accurately tracks elapsed time.

## Category

positive, performance

## Prerequisites

- Requires MI450 hardware or SimNow M112/M222 model
- MPIFoE firmware booted
- xncmdclient available

## Steps

1. **[host]** Read initial uptime:
   ```bash
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Uptime value recorded as T0

2. **[host]** Wait a known duration:
   ```bash
   sleep 10
   ```

3. **[host]** Read uptime again:
   ```bash
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Uptime value recorded as T1

4. **[host]** Calculate timing accuracy:
   ```bash
   # T1 - T0 should be approximately 10 seconds
   # Acceptable range: 9-11 seconds (within 10%)
   ```
   Expected: Uptime delta = 10 +/- 1 second

5. **[host]** Repeat with longer interval:
   ```bash
   xncmdclient -c 'get_uptime; quit;'
   sleep 60
   xncmdclient -c 'get_uptime; quit;'
   ```
   Expected: Uptime delta = 60 +/- 6 seconds

6. **[host]** Verify heartbeat under MCDI load:
   ```bash
   T_START=$(date +%s)
   xncmdclient -c 'get_uptime; quit;'
   for i in $(seq 1 100); do
     xncmdclient -c 'version; quit;' > /dev/null 2>&1
   done
   xncmdclient -c 'get_uptime; quit;'
   T_END=$(date +%s)
   echo "Wall clock elapsed: $((T_END - T_START)) seconds"
   ```
   Expected: Firmware uptime delta matches wall clock elapsed time (within 10%)

## Expected Result

- Heartbeat counter increments at consistent rate
- Uptime counter accurately tracks elapsed time (within 10% tolerance)
- Heartbeat timing not significantly affected by MCDI command load
- Uptime monotonically increasing (never goes backward)

## Failure Indicators

- Uptime delta far from expected (timing > 10% off)
- Uptime not incrementing (heartbeat loop stuck)
- Uptime goes backward (counter overflow or reset)
- Large timing drift under load (heartbeat starved)

## Cleanup

- None required
