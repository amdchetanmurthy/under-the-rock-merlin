---
topology: single-node
timeout: 120
pass_criteria: "test_cache_flush and test_cache_invalidate both return 0 (success) when executed on-target via the eftest framework"
priority: P1
stability: stable
retries: 0
validation_groups: [post-test]
---

# Cache Flush and Invalidate Tests

## Purpose

Validates the mid_sys_cache_data_flush_range and mid_sys_cache_data_invd_range primitives on-target, ensuring the data cache flush and invalidate operations work correctly on the MI450 ASIC. These are critical low-level operations for DMA coherency in the IFoE datapath.

## Category

positive, boundary

## Prerequisites

- MPIFoE firmware built with `--eftest` flag to include on-target test code
- Firmware binary deployed to SimNow or hardware target
- xncmdclient available on host for invoking eftest commands
- `src/tests/test_cache.c` compiled into the firmware image

## Setup

1. **[host]** Build firmware with eftest support:
   ```bash
   scripts/build.py --eftest -p simnow -s mi450-a0 --clean
   ```
   Expected: Firmware binary at `build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.bin` includes test_cache_flush and test_cache_invalidate

## Steps

1. **[host]** Execute cache flush test via eftest framework:
   ```bash
   xncmdclient -c 'eftest test_cache_flush; quit;'
   ```
   Expected: Returns 0 (success). The test:
   - Allocates a buffer and obtains an uncached alias via `UNCACHED_ADDR(&buf)`
   - XORs cached value with 0xAAAAAAAA to create a dirty cache line
   - Calls `mid_sys_cache_data_flush_range()` to flush the dirty line
   - Verifies the uncached alias now reads the flushed value

2. **[host]** Execute cache invalidate test via eftest framework:
   ```bash
   xncmdclient -c 'eftest test_cache_invalidate; quit;'
   ```
   Expected: Returns 0 (success). The test:
   - Allocates a cache-line-aligned buffer and obtains an uncached alias via `UNCACHED_ADDR(pbuf)`
   - Writes a different value to the cached copy (XOR with 0xAAAAAAAA)
   - Calls `mid_sys_cache_data_invd_range()` to invalidate the cache line
   - Verifies the cached read now matches the uncached (original) value

## Expected Result

- `test_cache_flush` returns 0: cache flush correctly writes dirty cache line to memory
- `test_cache_invalidate` returns 0: cache invalidate correctly discards stale cached data
- No ENOSYS (function not implemented) errors
- No EFAULT (implementation test failed) errors
- On SimNow, negative return values are acceptable (inconclusive -- preparation may fail because SimNow does not fully model cache behavior)

## Failure Indicators

- Return code ENOSYS: `mid_sys_cache_data_flush_range` or `mid_sys_cache_data_invd_range` not implemented
- Return code EFAULT: Cache operation executed but verification failed (data mismatch after flush/invalidate)
- xncmdclient timeout or connection failure
- Build without `--eftest` flag (test functions not linked)

## Cleanup

- None required (tests are read-only operations on stack-allocated buffers)
