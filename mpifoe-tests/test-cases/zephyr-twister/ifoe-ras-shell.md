---
topology: single-node
timeout: 300
pass_criteria: "All pytest cases pass: print_word returns 'done: <word>' for each input; get_err_loc returns SUCCESS (0) for valid inputs and ERANGE (34) for out-of-range element_id"
priority: P1
stability: stable
retries: 0
validation_groups: []
---

# IFoE RAS Shell Tests (Zephyr Twister)

## Purpose

Validates the IFoE RAS subsystem shell commands on native_sim via the Zephyr Twister test harness, ensuring print_word echoes correctly and get_err_loc returns proper error codes for parametrized RAS error location lookups.

## Category

positive, boundary

## Prerequisites

- Zephyr SDK installed and ZEPHYR_BASE set (via `tests/twister_env.sh`)
- `dependencies/zephyr` checkout present in the mpifoe-fw workspace
- Python environment with `pytest`, `twister_harness`, and `test_helpers.utils` available
- native_sim platform support (no hardware required)

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| platform | native_sim | native_sim | Zephyr target platform |
| word_to_print | HELLO | HELLO, WORLD, TEST | Word passed to print_word shell command |
| ifoe_ss_idx | 0 | 0-N | IFoE subsystem index for get_err_loc |
| ifoe_comp_id | 49 | 0-255 | Component ID for get_err_loc |
| ifoe_element_id | 2 | 0-1000+ | Element ID for get_err_loc (1000 triggers ERANGE) |
| error_flags | 0 | 0-N | Error flags for get_err_loc |
| error_index | 0 | 0-N | Error index for get_err_loc |

## Setup

1. **[host]** Source the twister environment:
   ```bash
   source tests/twister_env.sh
   ```
   Expected: ZEPHYR_BASE, PYTHONPATH, and PATH configured for twister execution

## Steps

1. **[host]** Run the Zephyr Twister test suite for ifoe_ras:
   ```bash
   ./tests/twister_env.sh twister --platform native_sim -T tests/ifoe_ras --make --disable-warnings-as-errors --clobber-output -vv
   ```
   Expected: Twister builds the ifoe_ras test application for native_sim, launches it, and runs the pytest harness

2. **[host]** Twister executes `test_shell_print_hello` with parametrized words (HELLO, WORLD, TEST):
   - Shell command: `print_word <word>`
   - Expected response: `done: <word>` for each word

3. **[host]** Twister executes `test_ras_get_err_loc` with parametrized RAS error data:
   - Input `(0, 49, 2, 0, 0)` via command: `get_err_loc 0 49 2 0 0`
     Expected: returns SUCCESS (0)
   - Input `(0, 49, 4, 0, 0)` via command: `get_err_loc 0 49 4 0 0`
     Expected: returns SUCCESS (0)
   - Input `(2, 49, 1000, 0, 0)` via command: `get_err_loc 2 49 1000 0 0`
     Expected: returns ERANGE (34) -- out-of-range element_id

4. **[host]** Check twister JUnit results:
   ```bash
   cat twister-out/twister.xml
   ```
   Expected: All test cases report `<testcase>` with no failures

## Expected Result

- Twister reports all tests passed for `ifoe_ras.test.shell`
- `print_word` echoes each parametrized word correctly with `done: <word>` format
- `get_err_loc` returns 0 (SUCCESS) for valid subsystem/component/element combinations
- `get_err_loc` returns 34 (ERANGE) for out-of-range element_id value (1000)
- JUnit XML at `twister-out/twister.xml` shows zero failures

## Failure Indicators

- Twister build failure for native_sim platform
- `print_word` output does not contain expected `done: <word>` string
- `get_err_loc` returns unexpected error code (not 0 for valid, not 34 for out-of-range)
- Timeout waiting for DUT response (MAX_WAIT_IN_SEC = 60s)
- Twister XML reports test failures or errors

## Cleanup

- Twister cleans up native_sim processes automatically
- Remove twister-out directory if needed: `rm -rf twister-out`
