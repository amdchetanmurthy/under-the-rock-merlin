---
topology: single-node
timeout: 60
pass_criteria: "lib.foo() returns 0 and test_foo_pass assertion succeeds"
priority: P2
stability: stable
retries: 0
validation_groups: []
---

# Hello World Build Verification (pffth)

## Purpose

Lightweight build verification test using the pffth (Python FFI Test Harness) framework that confirms the basic firmware build toolchain works by compiling and calling a trivial C function (foo) via Python FFI.

## Category

positive

## Prerequisites

- pffth framework available in the Python environment
- Build toolchain configured for mpifoe-fw compilation
- `tests/hello_world/hello_world.c` and `tests/hello_world/test_hello_world.py` present

## Steps

1. **[host]** Run the hello_world pffth test:
   ```bash
   cd tests/hello_world && pytest test_hello_world.py -v
   ```
   Expected: pffth compiles `hello_world.c` into a shared library and runs Python tests against it

2. **[host]** pytest executes `test_foo_pass`:
   - Calls `lib.foo()` via ctypes FFI
   - Expected: `lib.foo()` returns 0

3. **[host]** pytest executes `test_foo_assert` with parametrized args (0, 1):
   - Calls `lib.foo()` and asserts return value equals `test_arg`
   - Expected: Passes for `test_arg=0`, fails for `test_arg=1` (foo always returns 0)

## Expected Result

- `test_foo_pass` passes: `lib.foo()` returns 0 confirming the C function compiled and linked correctly
- `test_foo_assert[0]` passes: return value matches parameter 0
- `test_foo_assert[1]` is expected to fail (foo returns 0, not 1) -- this is a known parametrized negative case in the test file
- The critical assertion is that the pffth toolchain can compile and invoke firmware C code

## Failure Indicators

- pffth import failure (framework not installed)
- Compilation error in `hello_world.c`
- `lib.foo()` returns non-zero value
- Shared library loading failure via ctypes

## Cleanup

- None required (pffth cleans up compiled artifacts)
