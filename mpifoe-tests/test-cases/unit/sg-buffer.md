---
topology: single-node
timeout: 60
pass_criteria: "sg_buffer_init returns 0 and all sg_buffer struct fields are initialized correctly (current_mapped_address=0, current_mapped_page=0, num_pages=10, address_space=HOST_ADDR_SPC_PF_MCDI)"
priority: P1
stability: stable
retries: 0
validation_groups: []
---

# Scatter-Gather Buffer Unit Tests (pffth)

## Purpose

Validates the scatter-gather buffer initialization API using the pffth (Python FFI Test Harness) framework, ensuring sg_buffer_init correctly sets up buffer metadata and that DMA mock functions are properly wired for host address mapping.

## Category

positive

## Prerequisites

- pffth framework available in the Python environment
- Build toolchain configured for mpifoe-fw compilation
- `src/lib/sg_buffer/test_sg_buffer.py` and associated C source present

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| NUM_PAGES | 10 | 1-N | Number of scatter-gather pages to allocate |

## Steps

1. **[host]** Run the sg_buffer pffth tests:
   ```bash
   cd src/lib/sg_buffer && pytest test_sg_buffer.py -v
   ```
   Expected: pffth compiles the sg_buffer C code into a shared library with mock support and runs Python tests

2. **[host]** pytest executes `TestSGBuffer::test_sg_buffer_init`:
   - Sets up mock functions via `@mock_set()`:
     - `unmap_host_addr(space_, local_addr_)` returns 0
     - `map_host_addr(space_, local_addr_)` returns 0
     - `dma_transfer_blocking(dmaq_, from_, to_, len_)` returns 0
   - Retrieves C types via `get_type('host_addr_spc_t')` and `get_type('sg_buffer_t')`
   - Calls `lib.sg_buffer_init(HOST_ADDR_SPC_PF_MCDI, 10, page_addresses, sg_buffer)`
   - Expected: Returns 0 (success)

3. **[host]** Verify sg_buffer struct fields after initialization:
   - `sg_buffer.current_mapped_address == 0`
   - `sg_buffer.current_mapped_page == 0`
   - `sg_buffer.num_pages == 10`
   - `sg_buffer.address_space.value == HOST_ADDR_SPC_PF_MCDI`

## Expected Result

- `sg_buffer_init` returns 0 indicating successful initialization
- Buffer tracking fields are zeroed (no page mapped yet)
- `num_pages` matches the requested page count (10)
- `address_space` correctly records the MCDI PF address space
- All three mock functions (unmap_host_addr, map_host_addr, dma_transfer_blocking) are installed without error

## Failure Indicators

- pffth import failure or compilation error
- `sg_buffer_init` returns non-zero (initialization failure)
- `current_mapped_address` or `current_mapped_page` not zero after init
- `num_pages` does not match the NUM_PAGES constant (10)
- `address_space` does not match `HOST_ADDR_SPC_PF_MCDI`
- Mock setup failure (function signature mismatch)

## Cleanup

- None required (pffth cleans up compiled artifacts)
