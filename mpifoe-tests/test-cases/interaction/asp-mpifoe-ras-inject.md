---
topology: single-node
timeout: 180
pass_criteria: "ASP-initiated RAS error injection reaches MPIFoE, triggers MCA report, and error clean restores state"
priority: P1
stability: stable
validation_groups: [post-test]
---

# ASP to MPIFoE RAS Error Inject/Clean Interaction Test

## Purpose

Validates the ASP-to-MPIFoE RAS error injection path. ASP sends MPASP_MPIFOE_CMD_RAS_ERROR_INJECT via the mp_listener/mpasp_listener interface. MPIFoE's ras_ss handles the command, looks up the error location via ras_conv_table, calls the ras_drv inject API, and reports via MCA. Tests the full path: ASP cmd -> mpasp_listener -> ras_ss_inject_error -> ras_drv -> mca_drv_report_error.

## Category

positive, interaction, ras

## Prerequisites

- MPIFoE firmware booted with RAS subsystem initialized
- ASP firmware running and MPASP channel established
- MCA target address configured (via MPASP_MPIFOE_CMD_SET_MCA_TARGET)

## Steps

1. **[host]** Set MCA target address for RAS reports:
   ```bash
   # ASP sends SET_MCA_TARGET command
   # Verify mca_drv_set_target_address() succeeds
   ```
   Expected: MCA target configured

2. **[host]** Inject an IFOE ECC SEC error via ASP command:
   ```bash
   # ASP sends MPASP_MPIFOE_CMD_RAS_ERROR_INJECT with:
   #   ifoe_ss_idx=0, comp_id=IFOE(4), element_id=0 (RXDECAP_ECC)
   #   error_flags=0 (SEC), error_index=0
   ```
   Expected: mp_error_inject_handler returns 0

3. **[host]** Verify MCA report was generated:
   ```bash
   # Check MCA bank for IFoE error with:
   #   ErrorCodeExt = MODULE_ID_IFOE
   #   Address encoding per RAS_IFOE_MCA_ADDRESS
   ```
   Expected: MCA error logged with correct module and address

4. **[host]** Clean the injected error:
   ```bash
   # ASP sends MPASP_MPIFOE_CMD_RAS_ERROR_CLEAN with same parameters
   ```
   Expected: mp_error_clean_handler returns 0, error cleared

5. **[host]** Test invalid component ID:
   ```bash
   # ASP sends inject with invalid comp_id=99
   ```
   Expected: Returns ENODEV (get_conv_table_from_comp_id returns NULL)

6. **[host]** Test invalid element ID beyond table:
   ```bash
   # ASP sends inject with valid comp but element_id=99
   ```
   Expected: Returns ERANGE (set->num_errors <= ifoe_element_id)

## Expected Result

- Valid inject triggers MCA report with correct priority (CORRECTED for SEC, SYSTEM_FATAL for DED)
- Valid clean restores hardware state
- Invalid component returns ENODEV
- Invalid element returns ERANGE
- Error type correctly maps SEC/DED based on error_flags bit

## Failure Indicators

- Inject succeeds but no MCA report generated
- Wrong MCA priority for error type
- Clean fails to restore state
- Valid inject returns non-zero
- __ASSERT_NO_MSG fires on external_error_id lookup failure

## Cleanup

- Clean any injected errors
