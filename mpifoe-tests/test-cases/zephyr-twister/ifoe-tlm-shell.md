---
topology: single-node
timeout: 300
pass_criteria: "All pytest cases pass: help returns 'Available commands:', kernel version returns 'Zephyr version', print_word returns 'done: HELLO', and tlm_process returns SUCCESS (1)"
priority: P1
stability: stable
retries: 0
validation_groups: []
---

# IFoE Telemetry Shell Tests (Zephyr Twister)

## Purpose

Validates the IFoE telemetry subsystem shell interface on native_sim via the Zephyr Twister test harness, covering basic shell commands (help, kernel version, print_word) and the telemetry processing API (tlm_process).

## Category

positive, integration

## Prerequisites

- Zephyr SDK installed and ZEPHYR_BASE set (via `tests/twister_env.sh`)
- `dependencies/zephyr` checkout present in the mpifoe-fw workspace
- Python environment with `pytest`, `twister_harness`, and `test_helpers.utils` available
- native_sim platform support (no hardware required)

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| platform | native_sim | native_sim | Zephyr target platform |

## Setup

1. **[host]** Source the twister environment:
   ```bash
   source tests/twister_env.sh
   ```
   Expected: ZEPHYR_BASE, PYTHONPATH, and PATH configured for twister execution

## Steps

1. **[host]** Run the Zephyr Twister test suite for ifoe_tlm:
   ```bash
   ./tests/twister_env.sh twister --platform native_sim -T tests/ifoe_tlm --make --disable-warnings-as-errors --clobber-output -vv
   ```
   Expected: Twister builds the ifoe_tlm test application for native_sim, launches it, and runs the pytest harness

2. **[host]** Twister executes `test_shell_print_help` (from test_shell.py):
   - Shell command: `help`
   - Expected: Output contains `Available commands:`

3. **[host]** Twister executes `test_shell_print_version` (from test_shell.py):
   - Shell command: `kernel version`
   - Expected: Output contains `Zephyr version`

4. **[host]** Twister executes `test_shell_print_hello` (from test_shell.py):
   - Shell command: `print_word HELLO`
   - Expected: Output contains `done: HELLO`

5. **[host]** Twister executes `test_dut_print_help` (from test_dut.py):
   - DUT command: `help`
   - Expected: Output contains `Available commands:` (via DeviceAdapter readlines_until)

6. **[host]** Twister executes `test_dut_get_stations` (from test_dut.py):
   - DUT command: `tlm_process`
   - Expected: Returns SUCCESS (1) via wait_for_result parser

7. **[host]** Check twister JUnit results:
   ```bash
   cat twister-out/twister.xml
   ```
   Expected: All test cases report `<testcase>` with no failures

## Expected Result

- Twister reports all tests passed for `ifoe_tlm.test.shell`
- Shell `help` command lists available commands
- Shell `kernel version` returns a Zephyr version string
- Shell `print_word HELLO` returns `done: HELLO`
- DUT `tlm_process` call returns SUCCESS (1) confirming telemetry processing works
- JUnit XML at `twister-out/twister.xml` shows zero failures

## Failure Indicators

- Twister build failure for native_sim platform
- `help` command does not return `Available commands:`
- `kernel version` does not contain `Zephyr version` string
- `print_word` output missing expected `done: HELLO`
- `tlm_process` returns value other than 1 (SUCCESS)
- Timeout waiting for DUT response (MAX_WAIT_IN_SEC = 60s)
- Twister XML reports test failures or errors

## Cleanup

- Twister cleans up native_sim processes automatically
- Remove twister-out directory if needed: `rm -rf twister-out`
