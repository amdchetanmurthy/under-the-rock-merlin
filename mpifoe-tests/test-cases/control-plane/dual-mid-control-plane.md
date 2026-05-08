---
topology: single-node
timeout: 2400
pass_criteria: "ctest reports all ualoe_config_tests pass on a dual-MID (M222) SimNow model with cross-MID IFoE subsystem configuration"
priority: P1
stability: stable
retries: 0
validation_groups: [post-test]
---

# Dual-MID Control Plane Tests (M222)

## Purpose

Validates the IFoE control plane on a dual-MID (M222) SimNow simulation model, ensuring cross-MID IFoE subsystem configuration, driver loading, SR-IOV VF setup, and ualoe_config_tests all function correctly when two MID instances are present. This tests the extended station bitmask configuration across MID boundaries.

## Category

integration, config-matrix

## Prerequisites

- SimNow M222 dual-MID simulation environment available on regr-vm Jenkins agent
- Artifact manager accessible at `/proj/smartnic/xcb/tools/artefact_manager/`
- mpifoe firmware binary (mpifoe_fw.hbin) available as artifact
- ifoe driver package (ifoe_drv.mi450.x86_64) available as artifact
- Control plane tests package (ctrl-path-tests.mi450.x86_64) available as artifact
- QEMU guest image with root access (user: root)

## Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| simnow_script | sim222.IFoE_link_0_to_1.sh | sim222.*.sh | SimNow launch script for dual-MID |
| simnow_release | simnow-latest | version string | SimNow release version |
| port_mode | 4x200 | 1x800, 2x400, 4x200 | Network port mode |
| stations_mask_lower | f80001ff | hex (8 digits) | Lower 32 bits of stations bitmask |
| stations_mask_upper | f | hex (1 digit, 0-f) | Upper 4 bits of stations bitmask |
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
   Expected: Firmware, driver, and test packages downloaded

3. **[host]** Launch SimNow with dual-MID model (longer startup time):
   ```bash
   nohup ${WORKSPACE}/scripts/simnow-launch/sim222.IFoE_link_0_to_1.sh --jenkins --dir ${WORKSPACE}/simnow -r simnow-latest > ${WORKSPACE}/simnow/sn_run.log 2>&1 &
   ```
   Expected: SimNow starts with M222 model (wait ~720 seconds for initialization -- dual-MID takes longer)

4. **[host]** Launch QEMU:
   ```bash
   ${WORKSPACE}/simnow/launch-qemu.sh ${PORT_QEMU} &
   ```
   Expected: QEMU guest starts (wait ~120 seconds for boot)

5. **[host]** Install test prerequisites with dual-MID station masks:
   ```bash
   ssh root@localhost -p ${PORT_QEMU} "/root/prep_gtests.sh -w /root/gtests -ta -da -pm 4x200 -sml f80001ff -smu f"
   ```
   Expected: prep_gtests.sh configures dual-MID station masks via:
   ```
   xncmdclient -c 'ifoe_bios 4x200 0 f80001ff f; ifoe_next_phase PROVIDER; quit;' --force-enable-mmap tlp=0
   ```
   Driver modules loaded, SR-IOV VFs configured. For dual-MID, the second 1747 device (Processing accelerator class 1200) is handled -- one is removed to avoid conflicts.

## Steps

1. **[host]** Run control plane tests via ctest on QEMU guest:
   ```bash
   ssh root@localhost -p ${PORT_QEMU} "ctest --test-dir /root/gtests/ualoe_config_tests/build --output-junit /root/gtests/testRes.xml"
   ```
   Expected: ctest executes basic, config, and station test binaries; all tests pass with cross-MID configuration

2. **[host]** Collect test results:
   ```bash
   scp -P ${PORT_QEMU} root@localhost:/root/gtests/testRes.xml ${WORKSPACE}/testRes.xml
   ```
   Expected: JUnit XML results collected from QEMU guest

## Expected Result

- All ualoe_config_tests pass on dual-MID SimNow model
- Station mask configuration spans both MIDs (lower=f80001ff, upper=f)
- ifoe driver handles dual-MID PCI topology correctly (removes second 1022:1747 Processing accelerator device)
- Port mode configuration applies correctly across MID boundary
- JUnit XML (`testRes.xml`) shows zero failures

## Failure Indicators

- SimNow M222 model fails to start (longer startup vs single-MID)
- QEMU guest unreachable via SSH after extended boot time
- Second MID device removal fails (`echo 1 > /sys/bus/pci/devices/.../remove`)
- ifoe driver module load failure with dual-MID topology
- Cross-MID station configuration rejected by xncmdclient
- ctest reports test failures in basic, config, or station tests
- Invalid port_mode / stations_mask combination errors from prep_gtests.sh

## Cleanup

- Kill SimNow and QEMU processes
- Remove SimNow workspace: `rm -rf ${WORKSPACE}/simnow`
