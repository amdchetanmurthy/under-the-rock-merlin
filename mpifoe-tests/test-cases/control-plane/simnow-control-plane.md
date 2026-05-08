---
topology: single-node
timeout: 1800
pass_criteria: "ctest reports all ualoe_config_tests pass (basic, config, station tests) on SimNow + QEMU with ifoe driver loaded and SR-IOV VFs configured"
priority: P0
stability: stable
retries: 0
validation_groups: [post-test]
---

# SimNow Control Plane Tests

## Purpose

Validates the IFoE control plane end-to-end on a SimNow simulation with QEMU guest, covering driver loading (ifoe, ifoe-cfg, ifoe-cmd), SR-IOV VF configuration, and the full ualoe_config_tests suite (basic, config, station tests) via ctest.

## Category

integration

## Prerequisites

- SimNow simulation environment available on regr-vm Jenkins agent
- Artifact manager accessible at `/proj/smartnic/xcb/tools/artefact_manager/`
- mpifoe firmware binary (mpifoe_fw.hbin) available as artifact or built locally
- ifoe driver package (ifoe_drv.mi450.x86_64) available as artifact
- Control plane tests package (ctrl-path-tests.mi450.x86_64) available as artifact
- QEMU guest image with root access (user: root)

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| simnow_script | sim111.IFoE_link_0_to_1.sh | sim111.*.sh | SimNow launch script |
| simnow_release | simnow-latest | version string | SimNow release version |
| port_mode | 4x200 | 1x800, 2x400, 4x200 | Network port mode |
| run_p0_tests | false | true/false | Run only P0-labeled tests |

## Setup

1. **[host]** Prepare SimNow workspace and symlink firmware binary:
   ```bash
   mkdir -p ${WORKSPACE}/simnow
   ln -s ${WORKSPACE}/fw.mi450-a0.simnow.test/mpifoe_fw.hbin ${WORKSPACE}/simnow/mpifoe_fw.hbin
   ```
   Expected: Firmware binary linked into SimNow workspace

2. **[host]** Fetch artifacts via artifact manager:
   ```bash
   /proj/smartnic/xcb/tools/artefact_manager/ifoe_artefact_manager.sh create_manifest --fw.mi450-a0.simnow.test-version auto --ifoe_drv.mi450.x86_64-version auto --ctrl-path-tests.mi450.x86_64-version auto
   /proj/smartnic/xcb/tools/artefact_manager/ifoe_artefact_manager.sh download manifest.yml
   ```
   Expected: Firmware, driver, and test packages downloaded to workspace

3. **[host]** Launch SimNow:
   ```bash
   nohup ${WORKSPACE}/scripts/simnow-launch/sim111.IFoE_link_0_to_1.sh --jenkins --dir ${WORKSPACE}/simnow -r simnow-latest > ${WORKSPACE}/simnow/sn_run.log 2>&1 &
   ```
   Expected: SimNow starts (wait ~360 seconds for initialization)

4. **[host]** Launch QEMU:
   ```bash
   ${WORKSPACE}/simnow/launch-qemu.sh ${PORT_QEMU} &
   ```
   Expected: QEMU guest starts (wait ~120 seconds for boot)

5. **[host]** Install test prerequisites on QEMU guest:
   ```bash
   scp -P ${PORT_QEMU} scripts/regressions/prep_gtests.sh root@localhost:/root/prep_gtests.sh
   scp -P ${PORT_QEMU} ifoe_drv.mi450.x86_64/*.tar* root@localhost:/root/gtests/ifoe-drv.tar.gz
   scp -P ${PORT_QEMU} ctrl-path-tests.mi450.x86_64/*.tar* root@localhost:/root/gtests/ualoe_config_tests.tar.gz
   ssh root@localhost -p ${PORT_QEMU} "/root/prep_gtests.sh -w /root/gtests -ta -da"
   ```
   Expected: prep_gtests.sh installs dependencies, builds ifoe driver (ifoe.ko, ifoe-cfg.ko, ifoe-cmd.ko), loads modules, configures SR-IOV VFs, and builds ualoe_config_tests

## Steps

1. **[host]** Run control plane tests via ctest on QEMU guest:
   ```bash
   ssh root@localhost -p ${PORT_QEMU} "ctest --test-dir /root/gtests/ualoe_config_tests/build --output-junit /root/gtests/testRes.xml"
   ```
   Expected: ctest executes basic, config, and station test binaries; all tests pass

2. **[host]** For P0-only runs, add label filter:
   ```bash
   ssh root@localhost -p ${PORT_QEMU} "ctest --test-dir /root/gtests/ualoe_config_tests/build --output-junit /root/gtests/testRes.xml -L P0"
   ```
   Expected: Only P0-labeled tests execute

3. **[host]** Collect test results:
   ```bash
   scp -P ${PORT_QEMU} root@localhost:/root/gtests/testRes.xml ${WORKSPACE}/testRes.xml
   ```
   Expected: JUnit XML results collected from QEMU guest

## Expected Result

- All ualoe_config_tests pass (basic, config, station test binaries)
- ifoe driver modules (ifoe.ko, ifoe-cfg.ko, ifoe-cmd.ko) load without errors
- SR-IOV VF creation succeeds (`echo 1 > /sys/bus/pci/devices/0000:${DEV}/sriov_numvfs`)
- JUnit XML (`testRes.xml`) shows zero failures
- prep_gtests.sh configures port mode and runs `xncmdclient -c 'ifoe_bios ${PORT_MODE} ...; ifoe_next_phase PROVIDER; quit;'` successfully

## Failure Indicators

- SimNow fails to start or crashes during initialization
- QEMU guest unreachable via SSH
- ifoe driver module load failure (insmod errors)
- SR-IOV VF creation fails
- ctest reports test failures in basic, config, or station tests
- xncmdclient ifoe_bios or ifoe_next_phase commands fail
- prep_gtests.sh exits with non-zero status

## Cleanup

- Kill SimNow and QEMU processes
- Remove SimNow workspace: `rm -rf ${WORKSPACE}/simnow`
