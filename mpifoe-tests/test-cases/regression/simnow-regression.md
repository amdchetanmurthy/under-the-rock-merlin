---
topology: single-node
timeout: 1800
pass_criteria: "All pytest regression tests pass: SimNow setup succeeds, RAS injection tests produce expected log patterns, and loopback test verifies SDP write responses in SimNow logs"
priority: P1
stability: stable
retries: 0
validation_groups: [post-test]
---

# SimNow Regression Tests

## Purpose

Validates IFoE firmware regression scenarios on SimNow using a pytest-based suite that programmatically launches SimNow + QEMU, injects RAS errors via xncmdclient, runs loopback tests, and verifies expected behavior by grepping SimNow simulation logs.

## Category

integration, error-recovery, fault-injection

## Prerequisites

- SimNow simulation environment available on regr-vm Jenkins agent
- mpifoe firmware built with `--eftest` flag: `scripts/build.py --eftest -p simnow -s mi450-a0 --clean`
- Firmware binary at `build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.bin`
- Python virtual environment with pytest at `~/envs/pytest/`
- BIOS and showtime config files in `configs/` directory (jenkins_bios.cfg, jenkins_inst_0_lb.cfg)

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| simnow_script | sim111.IFoE_link_0_to_1.sh | sim*.sh | SimNow launch script |
| simnow_release | simnow-latest | version string | SimNow release version |
| build_debug | false | true/false | Use debug firmware build |

## Setup

1. **[host]** Build firmware with eftest support:
   ```bash
   scripts/build.py --eftest -p simnow -s mi450-a0 --clean
   ```
   Expected: Firmware binary generated at `build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.bin`

## Steps

1. **[host]** Run the pytest regression suite:
   ```bash
   source ~/envs/pytest/bin/activate && cd scripts/regressions/ && pytest --simnow-script=sim111.IFoE_link_0_to_1.sh --simnow-release=simnow-latest --junitxml=ifoe_regression_tests.xml -x
   ```
   Expected: pytest discovers and runs TestIFoERegressions class

2. **[host]** pytest executes `test_setup`:
   - Creates SimNow workspace and symlinks firmware binary
   - Launches SimNow: `nohup scripts/simnow-launch/sim111.IFoE_link_0_to_1.sh --jenkins --dir simnow -r simnow-latest`
   - Waits 360 seconds for SimNow initialization
   - Launches QEMU: `simnow/launch-qemu.sh ${PORT_QEMU}`
   - Waits 120 seconds for QEMU boot
   - Configures BIOS via: `ssh root@localhost -p ${PORT_QEMU} "/simnow/xncmdclient --force-enable-mmap -f /myhome/jenkins_bios.cfg tlp=0"`
   Expected: SimNow + QEMU running, BIOS configured

3. **[host]** pytest executes `test_ras_injections` with parametrized inputs (20 test vectors):
   - IFoE SS component tests: element_ids 32-37 with component_id 49, various error_flags
   - EX component tests: element_ids 0-6 with component_id 48, various error_flags
   - SEC component tests: element_ids 10, 21 with component_id 47
   - Each injection runs:
     ```bash
     ssh root@localhost -p ${PORT_QEMU} "/simnow/xncmdclient --force-enable-mmap -c 'ifoe_ras_inject_error 0x00 0x31 0x25 0x00 0x00;q;' tlp=0"
     ```
   - Validates by searching SimNow log for pattern:
     ```
     0.0.mpifoe: <MPIFOE>INF-{00000500}*** RAS Event Happened(00<ss><comp><elem>)
     ```
   Expected: All 20 RAS injection vectors produce matching log entries

4. **[host]** pytest executes `test_loopback`:
   - Applies showtime config: `xncmdclient --force-enable-mmap -f /myhome/jenkins_inst_0_lb.cfg tlp=0`
   - Injects loopback data: `dfblock:4.MemWrite 0x00010000 0xa5a5a5a5 4 1 0x00 0x0`
   - Validates SimNow log contains:
     - `IFOE-SS_0_0: nothing at wr_resp port: 0`
     - `SDP write response:`
     - `valid: 1, tag: 0x0`
     - `src_phys_acc_id: 3, dst_phys_acc_id: 309`
     - `status: 0`
   Expected: Loopback test confirms IFoE datapath writes and responses work

5. **[host]** Collect JUnit results:
   ```bash
   cat scripts/regressions/ifoe_regression_tests.xml
   ```
   Expected: JUnit XML shows all tests passed

## Expected Result

- `test_setup` successfully launches SimNow + QEMU environment
- All 20 `test_ras_injections` parametrized tests pass with expected RAS event log patterns
- `test_loopback` confirms SDP write response with correct physical accelerator IDs
- JUnit XML at `scripts/regressions/ifoe_regression_tests.xml` shows zero failures
- pytest log at `scripts/regressions/pytest.log` captures full debug output

## Failure Indicators

- SimNow fails to start or crashes during initialization
- QEMU guest unreachable via SSH on allocated port
- xncmdclient BIOS configuration command fails
- RAS injection does not produce expected log pattern in `simnow.mi450.log`
- Loopback test SDP write response missing or shows unexpected accelerator IDs
- pytest reports assertion failures or timeouts
- `run_cmd_and_log` returns non-zero exit code for any system command

## Cleanup

- Kill SimNow and QEMU processes (test_loopback kills SimNow via `kill -9`)
- Remove SimNow workspace directory
