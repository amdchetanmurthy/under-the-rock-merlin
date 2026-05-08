# Workflow: MPIFoE PR Gate

## Dispatch Mode: Solo

## Trigger
- Pull request submitted to mpifoe-fw repository
- Pre-merge validation requested by developer
- Code review gate check

## Inputs
- PR branch or commit SHA
- Base branch (default: main)

## Phase 1: Build

**Agent: testbed-ops**

1. Checkout the PR branch:
   ```bash
   cd /scratch/${USER}/mpifoe-fw
   git fetch origin
   git checkout <pr_branch>
   git submodule update --init --recursive
   ```

2. Build MPIFoE firmware with eftest support:
   ```bash
   rm -rf build/*
   ./scripts/build.py -p simnow --eftest
   ```

3. Verify build artifact exists:
   ```bash
   ls -la build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.hbin
   ```

**Gate check:** Build succeeds. If build fails, report error and abort.

## Phase 2: SimNow Boot Check

**Agent: testbed-ops**

1. Copy firmware binary to SimNow workspace:
   ```bash
   cp build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.hbin /scratch/${USER}/simnow/
   ```

2. Launch SimNow:
   ```bash
   cd /scratch/${USER}/simnow/
   /proj/smartnic/xcb/ifoe/simnow/sim111.sh \
     --ifwi MI450X_GENERIC_MI450_Baseline_BRP011_176291_PEMU_MTAG_UMC_APCB.sbin
   ```

3. Launch QEMU:
   ```bash
   /scratch/${USER}/simnow/launch-qemu.sh
   ```

4. Configure IFoE:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```

**Gate check:** Firmware boots and responds to version query. If boot fails, report and abort.

## Phase 3: Pre-Test Validation

**Agent: testbed-ops**

Run validation group: `pre-test`
- fw-heartbeat-check
- ifoe-link-check

**Gate check:** Both validations PASS.

## Phase 4: Sanity Tests

**Agent: testbed-ops**

Run test suite: `sanity`
- fw-version
- fw-uptime
- config-phase
- port-enum

All 4 sanity tests must PASS for the PR gate to pass.

## Phase 5: Report

**Agent: analyst**

Generate PR gate report with:
- Build status (success/failure)
- Boot status (SimNow boot result)
- Validation results (pre-test group)
- Sanity test results (all 4 tests)
- Overall PR gate verdict: PASS or FAIL
- If FAIL, specific failure details for developer action

Post result as comment on PR if GitHub integration is configured.
