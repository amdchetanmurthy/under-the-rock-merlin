# Validation: IFoE Telemetry Check

**Group membership**: post-test, full

Verify that the IFoE telemetry subsystem is active and returning data.
The telemetry manager runs at a 1-second period, so data should always
be available after the firmware has been running for a few seconds.

```bash
ssh $HOST "timeout 5 xncmdclient -c 'ifoe_telemetry_info; quit;'"
```

**PASS**: ifoe_telemetry_info returns telemetry status with non-zero data.
**FAIL**: Telemetry returns empty or zero data after firmware has been
running for more than 5 seconds.
**CRITICAL FAIL**: Timeout or error (telemetry subsystem may be broken).

If telemetry check fails, try enabling collection:
```bash
ssh $HOST "xncmdclient -c 'ifoe_telemetry_ctrl enable; quit;'"
sleep 2
ssh $HOST "xncmdclient -c 'ifoe_telemetry_info; quit;'"
```
