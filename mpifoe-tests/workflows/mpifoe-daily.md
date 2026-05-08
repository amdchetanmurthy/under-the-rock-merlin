# Workflow: MPIFoE Daily Build Health

## Dispatch Mode: Solo

## Trigger
- Daily CI against new MPIFoE firmware build
- After SimNow environment update
- After IFWI refresh
- Manual trigger for ad-hoc build validation

## Inputs
- MPIFoE firmware binary (mpifoe_fw.hbin)
- IFWI image (.sbin)
- SimNow version (default: latest)

## Phase 1: Build & Image Load

**Agent: testbed-ops**

1. Build MPIFoE firmware:
   ```bash
   cd /scratch/${USER}/mpifoe-fw
   git pull origin main
   rm -rf build/*
   ./scripts/build.py -p simnow --eftest
   cp build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.hbin /scratch/${USER}/simnow/
   ```

2. Launch SimNow with IFWI:
   ```bash
   cd /scratch/${USER}/simnow/
   /proj/smartnic/xcb/ifoe/simnow/sim111.sh \
     --ifwi MI450X_GENERIC_MI450_Baseline_BRP011_176291_PEMU_MTAG_UMC_APCB.sbin
   ```

3. Launch QEMU (after SimNow prompt appears):
   ```bash
   /scratch/${USER}/simnow/launch-qemu.sh
   ```
   Wait for Ubuntu boot (root/l1admin), then install dependencies:
   ```bash
   apt update -y && apt install -y gcc libmnl-dev libnl-3-dev libnl-genl-3-dev pkg-config xterm && resize
   ```

4. Configure IFoE:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```

**Gate check:** xncmdclient version responds within 10 seconds. If not, abort and collect SimNow logs.

## Phase 2: Validation Suite

**Agent: testbed-ops**

Run validation group: `full`
- fw-heartbeat-check
- ifoe-link-check
- telemetry-check
- error-log-check

**Gate check:** All validations PASS. If any CRITICAL FAIL, abort workflow.

## Phase 3: Sanity Tests

**Agent: testbed-ops**

Run test suite: `sanity`
- fw-version
- fw-uptime
- config-phase
- port-enum

**Gate check:** All P0 sanity tests PASS. If any P0 fails, skip remaining test phases.

## Phase 4: Bringup Tests

**Agent: testbed-ops**

Run test suite: `bringup`
- link-up
- ifoe-config
- accelerator-discovery
- telemetry-running
- l2ping-connectivity

## Phase 5: Report

**Agent: analyst**

Generate report with:
- Build version (firmware version from xncmdclient)
- SimNow version
- Pass/fail per test with details for any failures
- Comparison against previous daily run
- Any new failures flagged
- Validation group results summary

Post report to JIRA (FWDEV project) if configured.
