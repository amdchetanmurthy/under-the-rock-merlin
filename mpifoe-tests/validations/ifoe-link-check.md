# Validation: IFoE Link Status Check

**Group membership**: pre-test, full

Verify that at least port 0 has its link up. Link-up is required for
all connectivity, traffic, and L2Ping tests.

```bash
ssh $HOST "timeout 5 xncmdclient -c 'link_state 0; quit;'"
```

**PASS**: link_state returns link_up=1 with valid speed.
**FAIL**: link_up=0 or link_state returns error.
**CRITICAL FAIL**: Timeout (firmware may be hung -- run heartbeat check first).

If link check fails, gather additional diagnostics:
```bash
ssh $HOST "xncmdclient -c 'enum_ports; quit;'"
ssh $HOST "xncmdclient -c 'ifoe_get_current_phase; quit;'"
ssh $HOST "xncmdclient -c 'mac_state 0; quit;'"
ssh $HOST "xncmdclient -c 'get_fixed_port_properties 0; quit;'"
```

Note: Link may take 10-30 seconds to establish after IFoE configuration
is applied. Ensure sufficient settling time before running this check.
