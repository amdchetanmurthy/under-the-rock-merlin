# Validation: IFoE Error Log Check

**Group membership**: post-test, full

Check host dmesg for IFoE-related error messages. Errors in dmesg after
test execution indicate test-induced damage, firmware issues, or driver
problems that may not be caught by individual test pass/fail criteria.

```bash
ssh $HOST "dmesg | grep -i 'ifoe.*error\|mpifoe.*error\|ifoe.*fault\|ifoe.*fail' | tail -20"
```

**PASS**: No IFoE error messages in dmesg (empty grep output).
**WARN**: IFoE warning messages present but no errors.
**FAIL**: IFoE error or fault messages found in dmesg.

For additional context when errors are found:
```bash
ssh $HOST "dmesg | grep -i 'ifoe\|mpifoe' | tail -40"
ssh $HOST "dmesg | grep -i 'mca\|cper\|hardware error' | tail -10"
```

Note: After intentional RAS error injection tests, CPER/MCA messages
are expected and should not be treated as failures. Only unexpected
error messages indicate a problem.
