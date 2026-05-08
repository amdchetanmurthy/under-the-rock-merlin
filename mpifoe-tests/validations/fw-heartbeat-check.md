# Validation: MPIFoE Firmware Heartbeat Check

**Group membership**: pre-test, full
**Note**: **run this FIRST** in any validation group. If FW is hung,
all other validations will fail.

Query the firmware version via xncmdclient to verify the firmware is
responsive. This is the most basic liveness check.

```bash
ssh $HOST "timeout 5 xncmdclient -c 'version; quit;'"
```

**PASS**: Returns firmware version string (e.g., `0.14.4.0`) within 5 seconds.
**CRITICAL FAIL**: Hangs, times out, or returns error (firmware likely hung).
**FAIL**: Unexpected version string, empty response, or non-zero exit code.

If heartbeat fails, collect diagnostics:
```bash
ssh $HOST "dmesg | grep -i 'ifoe\|mpifoe' | tail -20"
ssh $HOST "xncmdclient -c 'read32 0x034000d8; quit;'"  # MPASP_FW_STATUS
```

FW takes 30-60s to initialize after image load. Allow settling time
before running this check. Always use `timeout` to prevent SSH hangs
on unresponsive firmware.
