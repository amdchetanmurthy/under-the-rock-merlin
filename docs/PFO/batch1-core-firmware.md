# Batch 1 -- Core Firmware Inventory

Generated: 2026-05-05

This document provides a comprehensive inventory of five PFO firmware repositories
covering ASP FMC, AMD TEE 3.0, PMFW, MPIO, and MPIFoE.

---

## 1. ASP-FMC (`firmware/asp-fmc`)

### Purpose

ASP-FMC (AMD Security Processor -- First Mutable Code) is the earliest mutable
firmware stage that runs on the AMD Platform Security Processor (PSP). It is
loaded by the immutable boot ROM and is responsible for establishing the initial
security posture of the platform: validating subsequent firmware, performing A/B
recovery, managing DICE attestation, setting up secure mailboxes to the Trusted
OS, and performing crypto-seed key verification. Because it executes before any
other mutable code, its integrity is critical to the entire chain of trust.

The firmware supports a wide matrix of ASICs (Weisshorn SP7/SP8/LP, Rosenhorn,
Medusa1, MI450, MI430, Alphatrion2, Olympicridge, Mustangpeak, Arcadia) and
produces PSP Directory Entry TypeId 0x01 (FMC) as well as a USB BIOS Updater
(UBU) binary.

### PSP Entry

| Entry | Type ID | Description |
|-------|---------|-------------|
| FMC | 0x01 | First Mutable Code -- primary PSP boot stage |
| UBU | varies | USB BIOS Updater utility (BIOSUBU.*) |

Output binary naming: `TypeId0x01_FMC_<asic>_<variant>_<version>.bin`
Signed variants: `.sbin`, `.csbin`, `.esbin`, `.ecsbin`

### Build System

- **Toolchain**: RISC-V GCC cross-compiler (`riscv64-unknown-elf-gcc`), pulled
  via Conan from Artifactory (`riscv64-elf-toolsuite/15.9.0`).
- **Build tool**: GNU Make (top-level `Makefile`).
- **Key commands**:
  - `make ASIC=<asic> configure` -- download toolchain and submodules
  - `make ASIC=<asic> PLATFORM=soc` -- build for silicon
  - `make ASIC=<asic> PLATFORM=simnow` -- build for SimNow simulation
  - `make ASIC=<asic> VARIANT=SP8` -- select SP revision variant
  - `make -C common/ubu ASIC=<asic>` -- build USB BIOS Updater
- **Signing**: `fw-sign` Python package from Artifactory, with KDS token auth.
  Supports DEV, PRE-SI, and PROD signing, plus optional encryption.
- **Dependencies**: Git submodules for `psp-fw-unified-header`, `soc-headers`;
  `librom` from Artifactory; `amd-tee3.0-ddk` headers via Conan.

### CI/CD Workflows

| Workflow | Trigger | What It Does | Blocks Merge? |
|----------|---------|--------------|---------------|
| `aspfmc-pr.yml` | PR opened/synchronize to `amd-staging` | Builds all 11 ASIC variants (SOC + SimNow), runs incremental Coverity, C++ lint, keyword scan, AI code review. Merges BIOS for WH/WHSP8/WHLP/MDS/MI450/MI430/AT2, then runs SimNow boot tests on all incremental configs. Triggers Jenkins `VeniceAspfmcMasterSmoke` for emulation validation. | Yes |
| `aspfmc-pr-presub.yml` | Issue comment containing `[TRIGGER_SMOKE]` | DCAUTO pre-submission pipeline: re-uploads the incremental build to DCAUTO Artifactory and triggers DCAUTO pre-submission testing for MI450 ASP_FMC. | No (manual trigger) |
| `aspfmc-pr-auto-rebase.yml` | PR opened/reopened to `amd-staging` | Automatically rebases the PR branch onto the base branch. | No |
| `aspfmc-jira.yml` | PR opened/edited/synchronize to `amd-staging` | Validates JIRA ticket reference in PR title/body. | Yes |
| `aspfmc-build-sign.yml` | Reusable workflow (called by PR, nightly, release) | Builds a single ASIC variant, signs with fw-sign, uploads to GitHub Artifacts and Artifactory. Supports incremental/nightly/release cadences. | N/A (reusable) |
| `aspfmc-nightly.yml` | Cron daily 4PM CST + manual dispatch | Full Coverity commit + CERT-C for all ASICs on SOC and SimNow. CodeQL analysis. Nightly lint, keyword scan. Builds all 8 ASIC variants as nightly. Runs full SimNow matrix (all configs including nightly-only). Racer test for MI450. Email report + Confluence page update. Dummy release dry-run. Submodule updates to program nightly repos. | N/A |
| `aspfmc-simnow.yml` | Manual dispatch (MDS program) | On-demand SimNow run for a specific program with configurable BSD, script, timeout. | N/A |
| `aspfmc-release.yml` | Tag push matching `*_<program>_*` + reusable | Release pipeline: reads tag to determine ASIC, builds & signs release package, optionally runs SimNow validation, publishes release notes to Confluence, uploads to production Artifactory. Supports dry-run via `_dry-run` suffix. Submits Verix request. | N/A |
| `aspfmc-post-merge.yml` | Push to `amd-staging` | Post-merge build & sign for WH SP7 and SP8, triggers Jenkins CI jobs for server BU validation. | N/A |

### SimNow Configurations

Seven YAML config files under `.github/simnow/`:

**wh.yaml (Weisshorn SP7)** -- 17 configurations:
- 11 incremental (PR gate): A0 Monarch Model 2, B0 Monarch/Powderhorn Model 2/5/3-2, Morocco 2P2C4T, Congo 1C1T, AB Monarch Model 2/5
- 6 nightly-only: Congo/Morocco B0 Dense/Classic, Congo/Morocco AB Dense
- Postcode: `0XAA55AA55`, timeouts: 600-2500s
- BSDs: `bsds/wh/model*_wh*_sp7_family1Ah.bsd`

**whsp8.yaml (Weisshorn SP8)** -- 9 configurations:
- 4 incremental: SP8C/SP8D Monarch Model 2, Eagle 1C1T, Hornbill 2P2C4T
- 5 nightly-only: SP8C Aransas/Model3-2/Model5, SP8D Model3-2/Model5
- Postcode: `0XAA55AA55`, timeouts: 600-1500s

**whlp.yaml (Weisshorn LP / Verano)** -- 2 configurations:
- 2 incremental: Model 2 Secure LSD, Model 3-2 Secure LSD
- Postcode: `0XAA55AA55`, SimNow date: `lkg`, timeout: 600s
- Uses `simoxide-boot-test` workflow instead of `simnow-lnx`

**mi450.yaml (MI450)** -- 25+ configurations:
- 5 incremental (PR gate): 0P1G unsecure/secure (1MID/2MID), 1P1G SKT7 unsecure/secure
- 20+ nightly-only: various topology permutations, RAP/RAS/Force Apply variants, 1P2G configs
- Postcode: `0X800F0000`, timeouts: 600-3500s
- BSDs: `bsds/mi4/mi450/aransas_*.bsd`

**mi430.yaml (MI430)** -- 1 configuration:
- 1 incremental: 0P1G 1MID 1AID 2XCD Unsecure
- Postcode: `0X800F0000`, timeout: 600s

**mds.yaml (Medusa1)** -- 8 configurations:
- 4 incremental: A0/B0 LPDDR5/DDR5 Emulation (64MB)
- 4 nightly-only: A0/B0 DDR5/LPDDR5 HW BIOS
- Postcode: `0XAA55AA55`, timeouts: 1000-1200s, SimNow date: `20260308` or `latest`

**at2.yaml (Alphatrion2)** -- 4 configurations:
- 2 incremental: fp10-unsecure baseline, fp10 SRIOV XTS unsecure
- 2 nightly-only: fp10 secure, fp10 SRIOV XTS secure
- Postcode: `0X80BA0000`, timeouts: 800-1000s

### Test Infrastructure

| Directory/File | Framework | Description |
|----------------|-----------|-------------|
| `conan/dependencies_test.txt` | Conan | Test package dependencies (alternative toolchain config) |
| `.github/coverity/checkers.txt` | Coverity | Extra Coverity checker configuration |
| `.github/coverity/parse_warnings.txt` | Coverity | Warning parse rules for Coverity |
| SimNow boot tests | SimNow + simnow-lnx workflow | End-to-end boot validation via SimNow simulation |
| Jenkins `VeniceAspfmcMasterSmoke` | Jenkins | Server BU emulation validation (PR gate) |
| Jenkins `VeniceAspfmcMasterCi` | Jenkins | Post-merge server BU CI |
| DCAUTO pre-submission | DCAUTO | Manual hardware smoke testing via `[TRIGGER_SMOKE]` comment |
| Racer (nightly) | Racer | MI450 nightly regression test via `run-racer.yml` |

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | Incremental Coverity (9 ASIC configs), C++ lint, keyword scan, AI code review, JIRA checker, all 11 ASIC builds, SimNow boot for incremental configs (~15 WH + 5 MI450 + 4 MDS + 2 AT2 + 1 MI430 + 4 WHSP8 + 2 WHLP), Jenkins emulation smoke |
| **Post-Merge** | WH SP7/SP8 rebuild, Jenkins CI trigger |
| **Nightly** | Full Coverity commit + CERT-C, CodeQL, BlackDuck SCA, ELF scan, full lint + KWS, all nightly SimNow configs (~40+ additional), Racer MI450, email + Confluence reporting, dummy release dry-run |
| **Release** | Release build + sign + SimNow validation + Confluence release notes + Verix submission |

### Gaps

1. **No unit tests**: Zero C-level unit tests or mock-based testing. All
   validation relies on SimNow boot tests and static analysis.
2. **No code coverage measurement**: No coverage tooling configured.
3. **No functional tests beyond boot**: SimNow tests only verify POST code
   reached; no programmatic assertion of FMC behavior (DICE, recovery, crypto).
4. **No integration test with TEE**: FMC's handoff to TOS is validated only
   implicitly by boot success.
5. **Missing Arcadia and Mustangpeak SimNow**: These ASICs have build entries but
   no SimNow test configurations.
6. **No Rosenhorn SimNow in PR gate**: Rosenhorn is built but has no SimNow
   configs at all.

---

## 2. AMD TEE 3.0 (`firmware/amd-tee3_0`)

### Purpose

AMD TEE 3.0 (Trusted Execution Environment) implements the PSP Trusted OS and
its associated drivers, trusted applications, and a DDK (Driver Development Kit).
The Trusted OS provides a secure execution environment on the PSP, hosting
drivers for fTPM, DRTM, SPDM, secure boot, DPE (DICE Protection Environment),
Hardware Attestation, IP Key Management, and confidential computing features. It
is the second major firmware stage after FMC and forms the backbone of AMD's
platform security.

The repo includes: the TOS kernel (`trusted_os/psp_kernel`), the OS layer
(`trusted_os/psp_os`), multiple security drivers (`amd_tee_dr/drv_*`), trusted
applications (`amd_tee_ta/`), the DDK (`amd_tee_ddk/`), an SDK
(`amd_tee_sdk/`), a register access whitelist tool, and a GFX anti-rollback
table. It supports all the same ASIC targets as ASP-FMC plus legacy MI300
variants.

### PSP Entry

The TEE produces multiple PSP directory entries depending on the ASIC. Drivers
are built individually and signed as separate binaries. Key entries include
Trusted OS kernel, system drivers (boot, fTPM, DRTM, SPDM, DPE, HAD, IFST,
etc.), and trusted applications. Version is set via `FW_VERSION_TOS` in
`amd_tee_ddk/inc/asic/<asic>/build_flags.mk`.

### Build System

- **Toolchain**: RISC-V GCC (`riscv64-unknown-elf-gcc`) for Venice-generation
  ASICs; ARM Compiler (`armclang`) for MI300-generation ASICs. Toolchains
  symlinked from `/home/runner/toolchain/`.
- **Build tool**: GNU Make. Top-level Makefile iterates subdirectories. Each
  driver has its own Makefile.
- **Key commands**:
  - `make -C <driverFolder>/<driverName>/ -j16 BUILD=<ASIC> VARIANT=<variant> NOCI=1`
- **Signing**: `fw-sign` Python package with `multiple-fw-sign` action. Produces
  `.sbin`, `.csbin`, `.esbin`, `.ecsbin` variants. Also generates `.h` header
  files from signed binaries for IFWI embedding.
- **Dependencies**: Git submodules; `supportedSocs.json` and
  `supportedRelease.json` define the build matrix dynamically.

### CI/CD Workflows

| Workflow | Trigger | What It Does | Blocks Merge? |
|----------|---------|--------------|---------------|
| `tee-pr.yml` | PR opened/synchronize to `amd-staging` + merge_group | Builds all ASICs via dynamic matrix from `supportedSocs.json`. Incremental Coverity for all project groups. C++ lint, keyword scan. Builds MI450/MI430/AT2/WH/WHSP8/WHLP/RH/OLR/ARCD. SimNow boot tests for MI450/MI430/WH/WHSP8/MDS/AT2. CC tests (SPDM, Sideband SPDM, DOE) on MI450. DDK builds for WH/MDS/OLR. Jenkins VeniceTeeMasterSmoke trigger. Merge queue gatekeeper placeholder. | Yes |
| `tee-nightly.yml` | Cron daily 3PM CST + manual dispatch | Full Coverity commit + CERT-C for all ASICs (multi-branch: staging, MDS1, MI300x/a/c, MI350p, MI308x). CodeQL analysis. Nightly lint + KWS. Builds all 9 ASICs. DDK nightly builds. Full SimNow matrix with combined combiner pipeline. MI450 Racer. Email + Confluence reporting. Dummy release dry-runs. Submodule updates to 6 program nightly repos. | N/A |
| `tee-release.yml` | Tag push `*_<program>_*` + reusable | Release build, sign, optional SimNow validation, Confluence release notes, Verix submission. Dry-run support. | N/A |
| `tee-smoke.yml` | Reusable workflow | Build & sign for a specific ASIC with optional DCAUTO and server test integration. SimNow matrix + Jenkins trigger. | N/A |
| `tee-build-sign.yml` | Reusable | Single ASIC build + sign + upload (incremental/nightly/release). | N/A |
| `tee-ddk-build.yml` | Reusable | DDK build for a specific SOC+MEM_TECH combination. | N/A |
| `tee-ddk-release.yml` | (exists) | DDK release pipeline. | N/A |
| `tee-sdk-release.yml` | (exists) | SDK release pipeline. | N/A |
| `tee-sfs-build.yml` | (exists) | SFS (Secure Feature Set) build. | N/A |
| `tee-pr-presubmit.yml` | (exists) | DCAUTO pre-submission for TEE. | No |
| `tee-pr-closed.yml` | (exists) | PR closed event handler. | N/A |
| `tee-pr-auto-rebase.yml` | PR opened/reopened | Auto-rebase PR branch. | No |
| `tee-jira.yaml` | PR events | JIRA ticket validation. | Yes |
| `run-cc-tests.yml` | Reusable | Confidential Computing tests (SPDM, DOE, Sideband SPDM) running on SimNow with `spdm-emu` library against MI4xx-PFO-Test-Cases repo. | N/A |

### SimNow Configurations

Six YAML config files under `.github/simnow/` -- largely matching ASP-FMC but
scoped to TOS component:

- `wh.yaml`, `whsp8.yaml`, `mds.yaml`, `mi450.yaml`, `mi430.yaml`, `at2.yaml`
- Same BSD models and postcode expectations as ASP-FMC
- TEE uses `tos:` prefix for firmware package lists (vs `fmc:` for ASP-FMC)

### Test Infrastructure

| Directory/File | Framework | Description |
|----------------|-----------|-------------|
| `amd_tee_ddk/amd_tee_test/test_suites/` | Custom | DDK test suites (test applications that run inside TEE) |
| `amd_tee_ta/ta_unit_test/` | VS Project | Trusted Application unit test (Windows-based Visual Studio project) |
| `run-cc-tests.yml` | pytest + spdm-emu | Confidential Computing integration tests: SPDM negotiation, DOE protocol, Sideband SPDM. Runs against SimNow with real IFWI. Checks out `PFO/MI4xx-PFO-Test-Cases`. |
| `.github/coverity/` | Coverity | Checker and warning parse configuration |
| Jenkins `VeniceTeeMasterSmoke` | Jenkins | Server BU emulation validation |
| DCAUTO | DCAUTO | Hardware smoke testing |
| Racer (nightly) | Racer | MI450 regression test |

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | Incremental Coverity (dynamic multi-ASIC matrix), lint, KWS, JIRA check, all ASIC builds, SimNow boot (MI450/MI430/WH/WHSP8/MDS/AT2), CC tests (SPDM/DOE/Sideband SPDM on MI450), DDK builds, Jenkins smoke |
| **Nightly** | Full Coverity + CERT-C (multi-branch), CodeQL, lint, KWS, all nightly SimNow, Racer MI450, email + Confluence, dummy release |
| **Release** | Release build + SimNow + Confluence notes + Verix |

### Gaps

1. **TA unit tests are Windows-only**: `ta_unit_test` uses Visual Studio project;
   not integrated into CI.
2. **DDK test suites not in CI**: `amd_tee_test/test_suites/` exists but no
   workflow runs these tests.
3. **No unit tests for kernel/OS layer**: The core TOS kernel and OS have no
   host-side unit tests.
4. **No code coverage**: No coverage tooling.
5. **CC tests limited to MI450 M112 Unsecure**: Only one SimNow variant tested
   for confidential computing (SPDM/DOE).
6. **No WHLP SimNow config**: TEE has no Verano/LP SimNow configuration.

---

## 3. PMFW (`firmware/pmfw-firmware`)

### Purpose

PMFW (Power Management Firmware) runs on the MP1/MP5/IMU microcontrollers within
MI450 (and MI430) to manage power delivery, clock configuration, thermal
management, and voltage regulation. It is a critical firmware component for DCGPU
power management.

This branch maintains code for five firmware images:
- **XCD.MP5** -- Execution Compute Die MP5 controller
- **MID.MP1** -- Multi-chip Interconnect Die MP1 controller
- **AID.MP5** -- Accelerator Interconnect Die MP5 controller
- **GFX.IMU_I** -- Graphics IMU Instruction firmware
- **GFX.IMU_D** -- Graphics IMU Data firmware

### PSP Entry

| Entry | PSP Entry ID | Description |
|-------|-------------|-------------|
| XCD.MP5 | 0x1051 | XCD MP5 power management (IFWI) |
| MID.MP1 | 0x8 | MID MP1 power management (IFWI) |
| AID.MP5 | 0x01EA | AID MP5 power management (IFWI) |
| GFX.IMU_I | 0x9B | IMU Instruction image (IFWI) |
| GFX.IMU_D | 0x9C | IMU Data image (IFWI) |

### Build System

- **Toolchain**: Custom build environment initialized via `source initdepot mi450.cfg` from the `firmware/` directory.
- **Build tool**: GNU Make with helper Python scripts.
- **Key commands**:
  - `source initdepot mi450.cfg` -- initialize build environment
  - `make` -- build firmware
  - `make fw_sign release` -- sign and package for release
  - `make test_package` -- build test package and upload to Artifactory
  - `make fuses` -- generate fuse headers from soc_fusedoc
  - `make ApcbCheckUid` -- generate APCB-APOB token headers
- **Signing**: `pss.amd.com` signing service, requires MI450 PMFW access.
- **Dependencies**: Git submodules for soc_headers, apcb-apob tokens.
- **Release**: Tagged releases (`dev/mi450_mi450_125.xx.0`) trigger CI pipeline;
  artifacts uploaded to `fw-dgpu-pmfw-release-local/mi450-main/`.

### CI/CD Workflows

| Workflow | Trigger | What It Does | Blocks Merge? |
|----------|---------|--------------|---------------|
| `pmfw-pr.yml` | PR events | PR validation pipeline (details need deeper read). | Yes |
| `pmfw-feas.yml` | (exists) | Feasibility/sanity builds. | Unknown |
| `pmfw-smoke.yml` | (exists) | Smoke test pipeline. | Unknown |
| `pmfw-release-mi450.yml` | Tag push / manual | MI450 release build, sign, upload to Artifactory. | N/A |
| `pmfw-jira.yml` | PR events | JIRA ticket validation. | Yes |
| `pmfw-pr-title-untruncate.yml` | PR events | Fixes truncated PR titles from squash merges. | No |

### SimNow Configurations

Two YAML config files under `.github/simnow/`:

- `mi450.yaml` -- MI450 SimNow configurations for PMFW
- `mi430.yaml` -- MI430 SimNow configurations for PMFW

(Detailed configs would match MI450 DCGPU patterns with PMFW-specific IFWI
merging.)

### Test Infrastructure

| Directory/File | Framework | Description |
|----------------|-----------|-------------|
| `firmware/main/test/` | Python | Test directory with `test_runner.py` |
| `firmware/main/test/test_runner.py` | Python | Test runner script for PMFW validation |
| SimNow boot tests | SimNow | IFWI-level boot validation |
| `python jenkins_run.py regression` | Jenkins/Python | Manual regression test runner |

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | PMFW PR validation, JIRA check |
| **Nightly/Smoke** | PMFW feasibility/sanity, smoke tests |
| **Release** | Tagged release build + sign + Artifactory upload |

### Gaps

1. **Very limited test infrastructure**: Only one test file (`test_runner.py`).
2. **No SimNow boot tests in PR workflow visible**: Need deeper investigation of
   `pmfw-pr.yml` to confirm.
3. **No static analysis (Coverity/CodeQL)**: No Coverity or CodeQL workflows
   visible.
4. **No C++ lint or keyword scan**: Not present in visible workflow list.
5. **MI430 coverage unclear**: SimNow config exists but workflow integration
   unclear.
6. **No unit tests for individual power management features**.

---

## 4. MPIO (`firmware/mpio`)

### Purpose

MPIO (Multi-Purpose I/O) firmware manages PCIe link training, I/O configuration,
hotplug, CXL support, MCTP messaging, and peripheral controller management on
AMD server/DCGPU platforms. It is a Zephyr RTOS-based firmware running on a
dedicated microcontroller within the SoC, responsible for configuring all I/O
lanes (PCIe, SATA, USB, CXL) and managing the PHY/PCS layers.

The firmware includes component handlers for PHY, PCS, KPX, CIT, and various
controllers; drivers for CLD, I3C, MCTP, and mutexes; a GML (Generic Messaging
Layer) automation framework; HAL layers for PCIeSS, SSBDCI, and UCIE; and
hotplug logic.

### PSP Entry

MPIO firmware is loaded as part of the IFWI. The specific PSP entry IDs depend
on the ASIC variant. Built via Zephyr/CMake with firmware signing.

### Build System

- **Toolchain**: Zephyr RTOS build system with `amd-zephyr-common` module.
- **Build tool**: Zephyr (CMake/west) with Make-based wrappers.
- **Dependencies**: Git submodules with LFS support. Requires `git lfs install`
  before cloning.
- **Key commands**:
  - `git clone -b rel/mi450 --recursive git@github.amd.com:PFO/mpio.git`
  - Build commands via Zephyr/west (specific commands in per-ASIC configs)
- **Signing**: `fw-sign` with `test_sign.py` helper.

### CI/CD Workflows

| Workflow | Trigger | What It Does | Blocks Merge? |
|----------|---------|--------------|---------------|
| `pr.yml` | PR events | PR validation: build, likely Coverity, lint, SimNow boot tests. | Yes |
| `jira.yml` | PR events | JIRA ticket validation. | Yes |
| `mpio-release-mi450.yml` | Tag push / manual | MI450 release build, sign, upload. | N/A |
| `mpio-release-mi430.yml` | Tag push / manual | MI430 release build, sign, upload. | N/A |
| `mpio-pr-title-untruncate.yml` | PR events | Fixes truncated PR titles. | No |

### SimNow Configurations

Two YAML config files under `.github/simnow/`:

- `mi450.yaml` -- MI450 SimNow configurations
- `mi430.yaml` -- MI430 SimNow configurations

### Test Infrastructure

MPIO has the most extensive unit test infrastructure of the five repos:

| Directory/File | Framework | Description |
|----------------|-----------|-------------|
| `tests/` | Zephyr test framework | Top-level test directory |
| `tests/unit_tests/` | C++ (gtest/Zephyr) | Core MPIO unit tests |
| `tests/x86/tests/` | x86 native | x86-native test execution |
| `tests/x86/unit_tests.mk` | Make | Build rules for x86 unit tests |
| `comphandlers/tests/` | C++ | Component handler tests (PHY, PCS, KPX, etc.) |
| `drivers/tests/unit_tests/` | C++ | Driver unit tests: CLD, I3C thermal, MCTP, MCTP endpoint, MCTP I2C, MPIO mutex |
| `gml/tests/` | C++ | GML (Generic Messaging Layer) tests |
| `gml/automation/` | Python/scripts | GML automation framework |
| `hasl/tests/unit_tests/` | C++ | HASL (Hardware Abstraction Service Layer) tests |
| `tools/test_sign.py` | Python | Signing validation test |
| `tools/coverity/config/test-cfg.xml` | Coverity | Coverity test configuration |
| `tools/replay/` | Custom | Replay tool for test traces |

Specific driver test files found:
- `cld_drv_tests.cpp` -- CLD driver tests
- `i3c_thm_drv_tests.cpp` -- I3C thermal driver tests
- `mctp_drv_tests.cpp` -- MCTP driver tests
- `mctp_ep_drv_tests.cpp` -- MCTP endpoint driver tests
- `mctp_i2c_tests.cpp` -- MCTP I2C tests
- `mpio_mutex_drv_tests.cpp` -- MPIO mutex driver tests

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | PR validation (build + likely unit tests + SimNow), JIRA check |
| **Release** | Release build + sign for MI450/MI430 |

### Gaps

1. **Unit test CI integration unclear**: Tests exist in source but whether
   `pr.yml` actually runs them needs verification.
2. **No visible nightly workflow**: No `mpio-nightly.yml` for scheduled
   comprehensive testing.
3. **No Coverity workflow visible**: Coverity config exists in `tools/coverity/`
   but no dedicated nightly Coverity workflow.
4. **Limited to MI450/MI430**: No WH/MDS/AT2 SimNow coverage (MPIO may be
   specific to these ASICs).
5. **No code coverage reporting**.
6. **GML automation tests not clearly in CI**.

---

## 5. MPIFoE (`firmware/mpifoe-fw`)

### Purpose

MPIFoE (MP Infinity Fabric over Ethernet) provides the ScaleUp transport
firmware for MI450. It implements the IFoE protocol that enables high-bandwidth,
low-latency GPU-to-GPU communication within a node, replacing traditional
ScaleUp interconnects with an Ethernet-based fabric. The firmware runs on the
Zephyr RTOS and manages network initialization, link training, telemetry, RAS
(Reliability, Availability, Serviceability), and MCDI (Management Controller
Data Interface) messaging.

The firmware integrates with:
- **Zephyr OS** for the RTOS layer
- **amd-zephyr-common** for AMD-specific Zephyr drivers and DTB support
- **ainic-rtos** for networking code shared with the Vulcano ScaleOut codebase
- **IFCP transport** for sideband persona communication

### PSP Entry

MPIFoE firmware is embedded in the MI450 IFWI as a PSP directory entry. The
specific entry ID is configured via `fwsign.ini`. Version is parsed from
`version.txt` and embedded via CMake-configured `version.h`.

### Build System

- **Toolchain**: Zephyr RTOS (CMake + west) with GCC cross-compiler.
- **Build tool**: CMake (`CMakeLists.txt`) with a `build.py` Python wrapper script.
- **Key commands**:
  - `./scripts/build.py -b benchtop -p silicon -s mi450-a0 --eftest` -- silicon benchtop
  - `./scripts/build.py -b minirack -p silicon -s mi450-a0 --eftest` -- silicon minirack
  - `./scripts/build.py -p simnow -s mi450-a0 --eftest` -- SimNow build
- **Build output**: `fw.{soc}.{platform}[.{board}][_eftest][_debug]/` directory
  containing `mpifoe_fw.elf`, `.bin`, `.dis`, `.sections`, `.symbols_size`.
- **Signing**: `fw-sign` tool via CMake custom commands; `fwsign.ini` template
  with version substitution.
- **Kconfig**: Zephyr Kconfig system (`Kconfig`, `Kconfig.build`, `prj.conf`)
  for feature configuration (e.g., `CONFIG_PERSONA_SIDEBAND`).
- **Dependencies**: Zephyr, amd-zephyr-common, ainic-rtos, ifcp (all as
  submodules under `dependencies/`).

### CI/CD Workflows

| Workflow | Trigger | What It Does | Blocks Merge? |
|----------|---------|--------------|---------------|
| `mpifoe-pr.yml` | PR events | PR validation: build, likely SimNow boot tests. | Yes |
| `mpifoe-nightly.yml` | Scheduled / manual | Nightly builds, SimNow, possibly Coverity. | N/A |
| `mpifoe-build-sign.yml` | Reusable | Build + sign for a specific configuration. | N/A |
| `mpifoe-bringup.yml` | (exists) | Bringup/debug builds. | N/A |
| `mpifoe-release-mi450.yml` | Tag push / manual | MI450 release pipeline. | N/A |
| `mpifoe-release-mi430.yml` | Tag push / manual | MI430 release pipeline. | N/A |
| `mpifoe-jira.yml` | PR events | JIRA ticket validation. | Yes |

### SimNow Configurations

Two YAML config files under `.github/simnow/`:

- `mi450.yaml` -- MI450 SimNow configurations for MPIFoE
- `mi430.yaml` -- MI430 SimNow configurations for MPIFoE

### Test Infrastructure

MPIFoE has the richest test infrastructure, spanning multiple frameworks:

| Directory/File | Framework | Description |
|----------------|-----------|-------------|
| `tests/hello_world/test_hello_world.py` | pytest | Basic hello world Zephyr test |
| `tests/ifoe_ras/testcase.yaml` | Zephyr test (twister) | RAS feature test case definition |
| `tests/ifoe_ras/pytest/` | pytest | RAS pytest test suite |
| `tests/ifoe_tlm/testcase.yaml` | Zephyr test (twister) | Telemetry feature test case definition |
| `tests/ifoe_tlm/pytest/` | pytest | Telemetry pytest test suite |
| `tests/common/test_helpers/` | Python | Shared test helper utilities |
| `tests/pffth/` | Custom | PFFTH (Platform Firmware Function Test Harness) tests |
| `src/tests/test_cache.c` | C unit test | Cache subsystem unit test |
| `scripts/tests/` | Python | Script-level tests |
| `scripts/regressions/conftest.py` | pytest | Regression test fixtures and configuration |
| `scripts/regressions/pytest.ini` | pytest | Pytest configuration for regressions |
| `scripts/regressions/test_ifoe_regressions.py` | pytest | IFoE regression test suite |
| `scripts/regressions/prep_gtests.sh` | Shell | GTest preparation script for QEMU host |
| `ci/Jenkinsfile` | Jenkins | Top-level CI Jenkinsfile |
| `ci/unit_tests/Jenkinsfile` | Jenkins | Unit test CI Jenkinsfile |
| `ci/control_plane_tests/Jenkinsfile` | Jenkins | Control plane test Jenkinsfile |
| `ci/regressions/Jenkinsfile` | Jenkins | Regression test Jenkinsfile |
| `ci/control_plane_tests/` | Jenkins | Control plane test pipeline |
| `ci/unit_tests/` | Jenkins | Unit test pipeline |
| `.clang-format` | clang-format | Code formatting rules |
| `.reviewboardrc` | ReviewBoard | Legacy review board configuration |

**GTest Integration**: The repo supports running GTests from within a SimNow
QEMU host environment (`launch-qemu.sh`), with tests for:
- `ualoe_config_tests/build/tests/basic`
- `ualoe_config_tests/build/tests/config`
- `ualoe_config_tests/build/tests/station`

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | PR build validation, JIRA check |
| **Jenkins CI** | Unit tests, control plane tests, regressions (via Jenkinsfiles) |
| **Nightly** | Nightly builds + SimNow |
| **Release** | Release build + sign for MI450/MI430 |

### Gaps

1. **Jenkins/GitHub Actions migration incomplete**: Multiple Jenkinsfiles exist
   alongside GitHub Actions workflows, suggesting a transition is in progress.
2. **Zephyr twister tests not clearly in CI**: `testcase.yaml` files for
   `ifoe_ras` and `ifoe_tlm` exist but may not be run in GitHub Actions.
3. **GTest execution requires SimNow + QEMU**: Complex multi-step manual process
   not automated in CI.
4. **No Coverity visible**: No Coverity workflow files found.
5. **No code coverage**: No coverage tooling configured.
6. **Limited to MI450/MI430**: No other ASIC support (expected for IFoE).
7. **Regression tests (`scripts/regressions/`) unclear in CI**: May only run via
   legacy Jenkins pipeline.

---

## Cross-Repository Summary

### CI Maturity Comparison

| Capability | ASP-FMC | TEE 3.0 | PMFW | MPIO | MPIFoE |
|-----------|---------|---------|------|------|--------|
| GitHub Actions PR gate | Full | Full | Partial | Partial | Partial |
| Coverity (incremental) | Yes | Yes | No | Unclear | No |
| Coverity (nightly commit) | Yes | Yes | No | Unclear | No |
| CodeQL | Yes | Yes | No | No | No |
| C++ Lint | Yes | Yes | No | No | No |
| Keyword Scan | Yes | Yes | No | No | No |
| JIRA Checker | Yes | Yes | Yes | Yes | Yes |
| SimNow Boot (PR) | Yes (40+) | Yes (30+) | Unclear | Yes | Yes |
| SimNow Boot (Nightly) | Yes (60+) | Yes (50+) | Unclear | Yes | Yes |
| Unit Tests | No | No (Windows only) | 1 file | Yes (extensive) | Yes (mixed) |
| CC/Functional Tests | No | Yes (SPDM/DOE) | No | No | GTest (manual) |
| Nightly Email/Confluence | Yes | Yes | No | No | No |
| Release Pipeline | Yes | Yes | Yes | Yes | Yes |
| Auto-Rebase | Yes | Yes | No | No | No |
| Racer Testing | Yes (nightly) | Yes (nightly) | No | No | No |
| DCAUTO Integration | Yes | Yes | No | No | No |
| BlackDuck SCA | Yes | Yes | No | No | No |
| ELF Scan | Yes | Yes | No | No | No |

### Recommended Actions for Complete Test Pipeline

1. **PMFW**: Needs Coverity, lint, keyword scan, and robust SimNow boot testing
   in its PR workflow. Currently the least mature CI.
2. **MPIO**: Should verify unit tests run in PR gate; add Coverity and nightly
   workflows.
3. **MPIFoE**: Migrate Jenkins pipelines to GitHub Actions; integrate Zephyr
   twister tests and GTests into CI; add Coverity.
4. **ASP-FMC**: Add C-level unit tests with mocks for critical paths (DICE,
   recovery, crypto). Add code coverage.
5. **TEE 3.0**: Port TA unit tests from Windows to Linux; integrate DDK test
   suites into CI; expand CC test matrix beyond MI450 M112.
6. **All repos**: Implement code coverage measurement and reporting.
