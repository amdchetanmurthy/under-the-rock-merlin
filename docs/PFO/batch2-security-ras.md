# PFO Firmware Inventory -- Batch 2: Security and RAS Components

Generated: 2026-05-05

---

## 1. firmware/art-security -- ART Security (AMD Root of Trust FMC + Runtime)

### Purpose

ART Security implements the AMD Root of Trust firmware, consisting of two stages: First Mutable Code (FMC) and Runtime. FMC is loaded first after the immutable boot code (ART BC) and is responsible for hardware initialization, firmware validation, watchdog timer setup, Register Access Policy (RAP) enforcement, and chain-of-trust establishment. After FMC completes, it hands control to the Runtime, which handles ongoing security services including command interface processing, SPDM measurement reporting, Caliptra error monitoring, DPE (DICE Protection Environment) support, and SEC-EMC initialization.

The firmware runs on a RISC-V core within the AMD Root of Trust (MPART) security processor embedded in AMD GPUs and server processors. It supports multiple ASIC targets: Weisshorn (SP7, SP8, LP), MI450, MI430, Medusa1, AlphaTrion2, Rosenhorn, OlympicRidge, MustangPeak, and Arcadia. ART Security enforces security policies (RAP), anti-rollback SPL checks, DICE attestation, firmware validation chains, and security-critical fuse management.

### PSP Entry

- **TypeId 0xAB** -- FMC binary (e.g., `TypeId0xAB_FMC_weisshorn_0x00XXXXXX.bin`)
- **TypeId 0xAC** -- Runtime binary (e.g., `TypeId0xAC_runtime_weisshorn_0x00XXXXXX.bin`)
- **TypeId 0x00** -- Stage 2 bundle (`TypeId0x00_stage2-bundle_<asic>_<version>.bin`) -- only for ASICs with stage2_bundles configured (MI450, AT2)

Binaries are signed with DEV/PRE-SI/PROD signing using the fw-sign tool via KDS.

### Build System

**GNU Make** with RISC-V cross-compilation. Two top-level Makefiles at `common/fmc/Makefile` and `common/runtime/Makefile`. ASIC-specific configuration is in `asic/<asic>/lms.mk` and `asic/<asic>/rap.mk`. Dependencies are managed via Conan (RISC-V toolchain packages from `swsec-conan-psp-internal` and `swsec-markham-conan-local`). Optional Rust toolchain for DPE local server. Supports both GCC and Clang-18 (LLVM) toolchains. ARTY (ART Test/Yield) has its own Makefile at `common/arty/Makefile`.

Key commands:
- `make -C common/fmc ASIC=weisshorn` -- build FMC
- `make -C common/runtime ASIC=weisshorn` -- build Runtime
- `make ASIC=weisshorn SIGN=DEV` -- build and sign
- `make ASIC=weisshorn CONFIG_TEST=<TEST>` -- build with test firmware

### CI/CD Workflows

| Workflow File | Trigger | What It Does | Blocks Merge? |
|---|---|---|---|
| `artsec-pr.yml` | PR opened/sync to `amd-staging` | Incremental Coverity (matrix across all ASICs, GCC+LLVM), C++ lint, AI code review, keyword scan (KWS), build+sign for MI450/MI430/WH/WH-SP8/WH-LP/MDS/AT2/OLR/MTP/RH/Arcadia, IFWI merge + SimNow boot tests for MI450/MI430/WH/WH-SP8/WH-LP/MDS/AT2, Fuse test builds, Jenkins PR validation for WH, Agesa docs check | Yes |
| `artsec-jira.yml` | PR opened/edited/sync to `amd-staging` | Validates JIRA ticket in PR title | Yes |
| `artsec-nightly.yml` | Cron daily 6:30PM CST + manual | SCC code counter, full Coverity commit (per-ASIC per-code-path), CERT-C commit, BlackDuck SCA, CodeQL, nightly lint, nightly KWS, nightly build+sign for all 8 ASICs, submodule updates to nightly repos, dummy release dry-run for all ASICs, full SimNow matrix across WH/WH-SP8/MI450/MI430/MDS/AT2 (up to 5 parallel), MI450 Racer test, email+Confluence reporting | No |
| `artsec-closed.yml` | Push to `amd-staging` (post-merge) | WH and WH-SP8 incremental build+sign, BVM merge, trigger Jenkins server CI for both variants | No |
| `artsec-release.yml` | Tag push (`*_mi450_*`, `*_wh_*`, etc.) or workflow_call | Parse release tag from `artsec-release.json`, release build+sign, Verix submission, SimNow pre-release validation, release notes generation (Confluence), dry-run support | No |
| `artsec-build-sign.yml` | Reusable (workflow_call) | Checkout, build FMC + Runtime, stage2 bundle generation, fw-sign signing, artifact upload to Artifactory (mkmartifactory) | N/A |
| `artsec-manual.yml` | Manual dispatch | Manual build trigger | No |
| `artsec-manual-wh.yml` | Manual dispatch | Manual WH-specific build | No |
| `artsec-manual-mi450.yml` | Manual dispatch | Manual MI450-specific build | No |
| `artsec-pr-auto-rebase.yml` | PR event | Auto-rebase for PRs | No |
| `artsec-pr-dcauto.yml` | PR event | DC automation pre-submission | No |

### SimNow Configurations

**7 config files**: `wh.yaml`, `whsp8.yaml`, `whlp.yaml`, `mi450.yaml`, `mi430.yaml`, `mds.yaml`, `at2.yaml`

| Config | Incremental (PR) Variants | Nightly-Only Variants | Postcode | Timeout Range |
|---|---|---|---|---|
| **WH** (`wh.yaml`) | 9 variants: A0/B0 Monarch model2/5, B0 Powderhorn model2/5, Morocco, Congo, AB Monarch model2 | 8 variants: model3-2 secure, AB model5, Congo/Morocco B0/B0C Dense/Classic, AB Dense | `0xAA55AA55` | 600-2500s |
| **WH SP8** (`whsp8.yaml`) | Present (parsed from YAML) | Present | `0xAA55AA55` | -- |
| **WH LP** (`whlp.yaml`) | Present (parsed from YAML, uses simoxide-boot-test) | -- | Variant-specific | -- |
| **MI450** (`mi450.yaml`) | 5: 0P1G M112/M228 unsecure+secure, 1P1G SKT7 unsecure+secure | 18: secure variants, force-apply, RAS MBAT, 2-die, SKT4, 1P2G SKT67 | `0x800F0000` | 600-3500s |
| **MI430** (`mi430.yaml`) | 1: 0P1G M112 unsecure | None | `0x800F0000` | 600s |
| **MDS** (`mds.yaml`) | 4: A0/B0 LPDDR5/DDR5 emulation | 4: A0/B0 LPDDR5/DDR5 HW | `0xAA55AA55` | 600-1200s |
| **AT2** (`at2.yaml`) | 2: fp10 unsecure, fp10 SRIOV XTS unsecure | 3: fp10 unsecure (nightly), fp10 secure, SRIOV XTS secure | `0x80BA0000` | 800-1000s |

### Test Infrastructure

| Path | Framework | Description |
|---|---|---|
| `common/test/common_test.c/h` | Custom C | Common test startup functions shared by all unit tests |
| `common/test/test.mk` | Make include | Auto-includes all `.mk` files from subdirs under `common/test/*/` |
| `common/test/*/` | Custom (CONFIG_TEST) | Individual test folders, each with a `.mk` file and `main()` replacement |
| `common/coco/` | Coco (Squish) | Code coverage instrumentation for SimNow execution traces |
| `common/arty/` | ARTY | ART Test/Yield environment with own Makefile |
| Coverity | Synopsys Coverity | Static analysis on PR (incremental) and nightly (full commit) |
| CodeQL | GitHub CodeQL | SAST nightly for all ASICs |

**Unit Tests (CONFIG_TEST):**
- `ART_LOG_TEST` -- FMC/Runtime logging
- `CALIPTRA_TEST` -- Runtime Caliptra iDevID
- `DPE_TEST` -- Runtime DPE functionality
- `RAP_TEST` -- FMC/Runtime Register Access Policy
- `RSMU_TEST` -- Runtime RSMU interface
- `SPDM_TEST` -- Runtime SPDM measurement
- `STARTUP_TEST` -- FMC/Runtime startup sequence
- `WAFL_TEST` -- Runtime WAFL interface
- `FUSE_TEST` -- FMC/Runtime fuse management (built for all 7 ASICs on PR)

### Testing Cadence

| Tier | What Runs |
|---|---|
| **PR Gate** | Incremental Coverity (all ASICs x toolchains), lint, KWS, JIRA check, AI code review, build+sign for 10+ ASICs, fuse test builds for 7 ASICs, IFWI merge + SimNow boot for WH (9 variants), MI450 (5), MI430 (1), AT2 (2), MDS (4), WH-SP8, WH-LP, Jenkins PR validation |
| **Post-Merge** | WH + WH-SP8 build+sign, Jenkins server CI trigger |
| **Nightly** | Full Coverity commit + CERT-C + BlackDuck + CodeQL, all 8 ASIC builds, full SimNow matrix (40+ variants), MI450 Racer, dummy release dry-run, submodule updates, email + Confluence reporting |
| **Release** | Tag-triggered build+sign+Verix, SimNow pre-release, Confluence release notes |

### Gaps

- No host-based unit test framework (no CppUTest/gtest/CMock) -- all tests require SimNow or hardware
- Coco code coverage is manual and not integrated into CI
- No automated test result trending beyond Confluence page append
- WH-LP uses simoxide-boot-test instead of simnow-lnx (different runner), creating platform divergence
- Arcadia IFWI/SimNow jobs are marked TODO
- No conftest.py or pytest-based test harness

---

## 2. firmware/dcgpu-esid -- DCGPU eSID (Embedded Secure ID)

### Purpose

DCGPU eSID (Embedded Secure ID, historically called UBA/VBL) is the DCGPU memory initialization firmware responsible for initializing HBM (High Bandwidth Memory) and LPDDR5 (CBD) memory subsystems on AMD discrete GPUs. It runs early in the GPU boot sequence on a RISC-V core and handles critical tasks including HBM PHY training, memory controller (UMC) configuration, Data Fabric (DF) memory map programming, DF RIB (Resource Interconnect Bus) setup, graphics engine initialization, SMU interaction for power management clocks, and display initialization.

The firmware supports multiple SoC targets (MI450, MI430) and various package configurations ranging from small (1MID+1AID+1XCD) to full configurations (2MID+2AID+4XCD+CBD). It includes an extensive software simulation environment (`Simulate/`) that emulates the hardware register space and allows full firmware execution on a developer workstation without SimNow or silicon.

### PSP Entry

- eSID binary stored under `Build/<SOC>/HBM4/eSID/`
- Signed via fw-sign with DEV/PROD signing
- Produces `.sbin` (signed binary) and `.elf` files

### Build System

**GNU Make** with RISC-V cross-compilation. Top-level `Makefile` and `configure` script for environment setup. SOC-specific build via `dcgpu/Drivers/Soc/<SOC>/Makefile`. Dependencies managed via Conan (`dcgpu/Tools/conan/dependencies_tee3.py`). Lint checking via `dcgpu/Tools/Lint/LintCheckers.mk`. Supports `NOSIGN=1`, `NOLINT=1`, `PRODUCTION=1`, `DUMMY_ESID=1` flags.

Key commands:
- `./configure` -- set up environment
- `make SOC=MI450` -- build for MI450
- `make SOC=MI450 simulation` -- build simulation target
- `make SOC=MI450 UT TARGET=dcgpu/Test/UT/Source/` -- run unit tests

### CI/CD Workflows

| Workflow File | Trigger | What It Does | Blocks Merge? |
|---|---|---|---|
| `dcgpu-esid-pr.yml` | PR opened/sync to `main` | Lint, incremental Coverity (MI450), build+sign MI450+MI430, unit tests (MI450), IFWI merge + SimNow boot for MI450 (5 variants) and MI430 (1 variant) | Yes |
| `dcgpu-esid-jira.yml` | PR event | JIRA ticket validation | Yes |
| `dcgpu-esid-nightly.yml` | Cron daily 4PM CST + manual | Full Coverity commit (MI450+MI430) + CERT-C + BlackDuck, CodeQL, nightly MI450+MI430 build, full SimNow matrix for MI450 (~20 variants) + MI430, email + Confluence reporting | No |
| `dcgpu-esid-build-sign.yml` | Reusable (workflow_call) | Build, sign, upload to Artifactory | N/A |
| `dcgpu-esid-ut.yml` | Reusable (workflow_call) | CppUTest-based unit test execution | N/A |
| `dcgpu-esid-merge.yml` | Push to `main` | Post-merge actions | No |
| `dcgpu-esid-release.yml` | Tag push | MI450 release pipeline | No |
| `dcgpu-esid-mi430-release.yml` | Tag push | MI430 release pipeline | No |
| `dcgpu-esid-mi450-release.yml` | Tag push | MI450-specific release | No |
| `dcgpu-esid-pr-dcauto.yml` | PR event | DC automation | No |
| `patch-simnow.yml` | Workflow | SimNow patching | No |
| `sync-mi450_mc.yml` | Workflow | MI450 memory controller sync | No |

### SimNow Configurations

**2 config files**: `mi450.yaml`, `mi430.yaml`

| Config | Incremental Variants | Nightly-Only Variants | Postcode | Timeout Range |
|---|---|---|---|---|
| **MI450** | 5: 0P1G M112/M228 unsecure+secure, 1P1G SKT7 unsecure+secure | 18: secure, force-apply, RAS MBAT, 2-die, SKT4, 1P2G SKT67 | `0x800F0000` | 600-3500s |
| **MI430** | 1: 0P1G M112 unsecure | None | `0x800F0000` | 600s |

### Test Infrastructure

| Path | Framework | Description |
|---|---|---|
| `dcgpu/Test/UT/` | CppUTest | Host-based unit tests with Makefile |
| `dcgpu/Test/UT/Source/` | CppUTest | Unit test source files |
| `dcgpu/Test/CommonMock/Common/` | Custom C mocks | ~20 mock files (MockSmnLib, MockSocTopology, MockDebugPrint, etc.) |
| `dcgpu/Test/CppUTest/lib/` | CppUTest libs | Pre-built `libCppUTest.a` and `libCppUTestExt.a` |
| `dcgpu/Test/Script/GenerateUnitTestTemplate.py` | Python | Auto-generates unit test boilerplate |
| `dcgpu/Tools/UT_tools/UTLines.py` | Python | UT line counting utility |
| `dcgpu/Tools/UT_tools/cov.sh` | Shell | UT coverage helper |
| `Simulate/` | Custom C simulator | Full software simulation of eSID execution |
| `Simulate/simulate.py` | Python | Test runner for simulation test cases |
| `Simulate/def_testcases.json` | JSON | 15+ platform configs (CEM, M111/M112/M222, BigBoy, cutdown) x 10+ test cases (NPS1/NPS2, HBM harvesting, UMC FW, CBD) |
| `Simulate/Testcase/noinit.json` | JSON | No-init test configuration |
| `.style/check_style.sh` | Shell | Code style enforcement |

### Testing Cadence

| Tier | What Runs |
|---|---|
| **PR Gate** | Lint, Coverity (MI450), build MI450+MI430, CppUTest unit tests (MI450), SimNow MI450 (5 variants) + MI430 (1 variant) |
| **Nightly** | Full Coverity + CERT-C + BlackDuck + CodeQL, build MI450+MI430, full SimNow matrix (~20 MI450 + MI430 variants), email + Confluence |
| **Release** | Tag-triggered build+sign for MI450 and MI430 separately |

### Gaps

- CppUTest unit tests only run for MI450, not MI430
- Simulation (`Simulate/simulate.py`) runs in nightly Coverity build but not as a dedicated PR gate step
- No Coco/gcov code coverage reporting in CI
- Style checking (`.style/`) exists but is not integrated as a CI workflow step
- No AI code review (unlike art-security)

---

## 3. firmware/MPRAS-Kernel -- MPRAS Kernel (RAS Firmware)

### Purpose

MPRAS (Management Processor RAS) Kernel is the RAS (Reliability, Availability, Serviceability) firmware that runs on the MPART RISC-V processor in AMD GPUs. It provides the core operating system services for RAS functionality, built on the Zephyr RTOS. The kernel manages applet lifecycle (loading, scheduling, timer management), inter-processor messaging (ASP, BIOS, HDT, MPIO, PMFW), NMI handling, watchdog timer supervision, DRAM access, scoreboard management, and a Simple File System (SFS) for persistent storage.

The kernel implements a microkernel architecture where the MPRAS Kernel provides core OS services and system calls, while domain-specific RAS logic is implemented in separate applets (PCIe, CXL, PFEH, page retirement) that run as dynamically loaded user-space modules. The kernel exposes an SDK with well-defined syscall interfaces for applets to use hardware services safely.

### PSP Entry

- MPRAS kernel binary (Zephyr ELF, signed)
- Applet DTB JSON metadata: `mpras_kernel_dtb.json`, `mprasfw_combined_dtb.json`
- Release notes: `mprasfw_releasenotes.txt`

### Build System

**CMake + Zephyr RTOS** build system. Application in `app/` with `CMakeLists.txt` and `prj.conf`. Board definition at `app/boards/riscv/amd_mi450_mpras/`. Uses SiFive RISC-V toolchain (`riscv64-unknown-elf-toolsuite`). Dependencies are Zephyr RTOS and MPRAS services as git submodules.

Key commands:
- `mkdir build && cd build`
- `cmake -G"Unix Makefiles" ../app -DBUILD=MI450`
- `make -j32`

### CI/CD Workflows

| Workflow File | Trigger | What It Does | Blocks Merge? |
|---|---|---|---|
| `mpras_kernel-pr.yml` | PR opened/sync to `dev/*` or `rel/*` | Incremental Coverity, lint, MI450 + MI430 build, IFWI merge, SimNow boot tests (MI450: 5 MAT variants, MI430) | Yes |
| `jira.yml` | PR event | JIRA validation | Yes |
| `mpras_kernal-release.yml` | Tag push / release | Release build pipeline | No |

### SimNow Configurations

**2 config files**: `mi450.yaml`, `mi430.yaml`

| Config | MAT Incremental Variants | Nightly Variants | Postcode | Timeout |
|---|---|---|---|---|
| **MI450** | 5: M112/M228 unsecure, 1P1G M112 unsecure, 1P1G M222 SKT4+SKT7 unsecure | 16: secure mirrors, force-apply, 2G, 1P2G SKT67 | `0x800F0000` | 600-2000s |
| **MI430** | From mi430.yaml | -- | `0x800F0000` | -- |

### Test Infrastructure

| Path | Framework | Description |
|---|---|---|
| `app/test/test_main.c/h` | Custom C | Test main entry point |
| `app/test/dram_test.c` | Custom C | DRAM access validation |
| `app/test/messaging_if_test.c` | Custom C | Inter-processor messaging test |
| `app/test/poison_test.c` | Custom C | Memory poison injection test |
| `app/test/remote_die_smn_test.c` | Custom C | Remote die SMN access test |
| `app/src/sdk/test_applet.c` | Custom C | SDK test applet |
| `scripts/dtb_validator.py` | Python | DTB JSON validation |
| `scripts/decoder.py` | Python | Postcode/DTB decoder |

### Testing Cadence

| Tier | What Runs |
|---|---|
| **PR Gate** | Coverity, lint, MI450 + MI430 build, SimNow MI450 (5 MAT variants) + MI430 |
| **Nightly** | Implied by nightly repo but no dedicated nightly workflow in this repo |
| **Release** | Tag-triggered release build |

### Gaps

- No dedicated nightly workflow file -- relies on external nightly repo orchestration
- Test files in `app/test/` appear to be on-target tests (require SimNow), no host-based unit tests
- No CppUTest/gtest framework
- No Coco code coverage
- No CodeQL or BlackDuck SCA workflows
- No AI code review
- No email/Confluence reporting
- Branch structure uses `dev/*` and `rel/*` rather than a single main branch

---

## 4. firmware/MPRAS-Applets -- MPRAS Applets (RAS PCIe/CXL Applets)

### Purpose

MPRAS Applets are dynamically loadable RAS application modules that run on top of the MPRAS Kernel. Each applet implements domain-specific RAS functionality and communicates with the kernel via a well-defined syscall SDK interface. The repository contains production applets for PCIe AER error handling, CXL component error handling, PFEH (Platform First Error Handling), and page retirement/MPIO I2C. It also includes sample applets (sample1, sample2, sample3) for development reference and a unit_test_applet for on-target API sanity testing.

The applets are compiled as standalone position-independent binaries with their own linker scripts, then packaged with DTB JSON metadata for the MPRAS Kernel to load at runtime. Each applet has a `process.c` entry point implementing an applet lifecycle (initialize, process events, shutdown).

### PSP Entry

- Each applet produces a signed `.sbin` binary (e.g., `mpras_pfeh_applet.sbin`, `mpras_pcie_applet.sbin`)
- Applet DTB JSON: `mpras_<applet>_applet_dtb.json`
- Release notes per applet and per platform variant (SP7, SP8, MI450)

### Build System

**CMake + Zephyr RTOS** with applet SDK toolchain (`dependencies/applet_sdk/riscv_toolchain.cmake`). Each applet has its own `CMakeLists.txt` and `prj.conf`. Uses Zephyr SDK (`zephyr-sdk-0.16.8`). Build targets include WH_SP7, WH_SP8, WH_LP, MI450.

Key commands:
- `cd pfehapplet && mkdir build && cd build`
- `cmake -DCMAKE_TOOLCHAIN_FILE="../../dependencies/applet_sdk/riscv_toolchain.cmake" -G"Unix Makefiles" ../ -DBUILD=WH_SP7`
- `make linker_script && make`

### CI/CD Workflows

| Workflow File | Trigger | What It Does | Blocks Merge? |
|---|---|---|---|
| `mpras_applets-pr.yml` | PR opened/edited/sync to `main`, `dev/*`, `rel/*` | Incremental Coverity (WS_SP7, WH_SP8, WH_LP matrix), WH SP7 pcie_applet build, JIRA check, lint | Yes |
| `mpras_applets-smoke.yml` | Push to `main` (post-merge) | WH SP7 + WH SP8 PFEH applet build+sign, upload to Artifactory, trigger Jenkins server CI for SP7 and SP8 | No |
| `mpras_applets-build-sign.yml` | Reusable (workflow_call) | Build + sign individual applet for target ASIC | N/A |
| `mpras_applets-release.yml` | Release trigger | Release pipeline | No |

### SimNow Configurations

**No SimNow configuration files** in this repo. Applet testing relies on the MPRAS-Kernel's SimNow infrastructure (the kernel loads applets during its SimNow boot tests).

### Test Infrastructure

| Path | Framework | Description |
|---|---|---|
| `unit_test_applet/` | Custom C (on-target) | On-target unit test applet loaded by MPRAS Kernel |
| `unit_test_applet/src/common_api_sanity.c` | Custom C | Common API sanity checks |
| `unit_test_applet/src/cxl_api_sanity.c` | Custom C | CXL API sanity checks |
| `unit_test_applet/src/dimm_ppr_api_sanity.c` | Custom C | DIMM PPR API sanity checks |
| `unit_test_applet/src/pcie_api_sanity.c` | Custom C | PCIe API sanity checks |
| `unit_test_applet/src/pcie_scalable_test.c` | Custom C | PCIe scalability test |
| `unit_test_applet/src/pfeh_api_functionality.c` | Custom C | PFEH API functional tests |
| `unit_test_applet/src/pfeh_api_sanity.c` | Custom C | PFEH API sanity checks |
| `sample1/`, `sample2/`, `sample3/` | Example code | Development reference applets |

### Testing Cadence

| Tier | What Runs |
|---|---|
| **PR Gate** | Coverity (3 targets), lint, JIRA check, WH SP7 pcie_applet build |
| **Post-Merge** | WH SP7 + SP8 PFEH smoke build, Jenkins trigger |
| **Release** | Tag-triggered release |

### Gaps

- No SimNow boot testing in this repo's CI (relies entirely on MPRAS-Kernel)
- unit_test_applet is on-target only (requires MPRAS Kernel + SimNow)
- No host-based unit tests (no CppUTest/gtest)
- No nightly workflow file
- No CodeQL, BlackDuck, or code coverage
- No AI code review
- PR gate only builds pcie_applet for WH SP7 -- does not build all applets or all targets
- No MI450/MI430 build or test in applets PR gate (only Weisshorn targets)

---

## 5. firmware/nht-firmware -- NHT Firmware (NHT Controller)

### Purpose

NHT (nHT, Node Hotplug Technology) firmware is the management controller firmware for the nHT engine on AMD GPUs. It handles platform-level messaging and node management functions including inter-node communication, hotplug event handling, and platform messaging between the nHT controller and other on-chip agents. The firmware runs on a Xtensa (Tensilica) processor core and provides an interface layer (PAL - Platform Abstraction Layer) and OS abstraction layer (OSAL) for hardware interaction.

The firmware is built using Zephyr RTOS on a custom Xtensa board definition (`amd_cumberland_nHT`). It includes its own signing flow and header generation. The nHT controller coordinates with the ASP (AMD Security Processor) and other on-chip components through a messaging interface that is documented in the project's Sphinx documentation.

### PSP Entry

- nHT binary with PSP header (generated by `tools/add_psp_header.c`)
- Signed via fw-sign
- Version tracking in `version.txt`

### Build System

**CMake + Zephyr RTOS** with Xtensa toolchain. Top-level build via `nHT/build.sh` or Makefile at `nHT/Makefile`. Board definition at `boards/xtensa/amd_cumberland_nHT/`. Kconfig-based configuration (`nHT/Kconfig`, `nHT/prj.conf`). Custom PSP header tool at `tools/add_psp_header.c` built with its own Makefile (`tools/Makefile`). Sphinx documentation at `nHT/docs/`.

Key commands:
- `cd nHT && ./build.sh -g -d 1` -- generate and configure debug build
- `make -C nHT BUILD_DEBUG=1 -j` -- build

### CI/CD Workflows

| Workflow File | Trigger | What It Does | Blocks Merge? |
|---|---|---|---|
| `mpnht-pr.yml` | PR opened/sync (all branches) | Lint, incremental Coverity (Xtensa), AI code review, MI450 build, MI430 build, IFWI merge + SimNow boot tests for MI450 (5 variants) + MI430 | Yes |
| `mpnht-jira.yml` | PR event | JIRA validation | Yes |
| `mpnht-nightly.yml` | Cron + manual | Nightly builds and SimNow | No |
| `mpnht-build-sign.yml` | Reusable (workflow_call) | Build + sign for target ASIC | N/A |
| `mpnht-release-mi430.yml` | Release trigger | MI430 release | No |
| `mpnht-release-mi450.yml` | Release trigger | MI450 release | No |

### SimNow Configurations

**2 config files**: `mi450.yaml`, `mi430.yaml`

| Config | Incremental Variants | Nightly-Only Variants | Postcode | Timeout |
|---|---|---|---|---|
| **MI450** | 5: 0P1G M112/M228 unsecure+secure, 1P1G SKT7 unsecure+secure | 14: secure mirrors, force-apply, 2G, 1P2G | `0x800F0000` | 600-2000s |
| **MI430** | From mi430.yaml (parsed) | -- | `0x800F0000` | -- |

### Test Infrastructure

| Path | Framework | Description |
|---|---|---|
| `tools/test_sign.py` | Python | Signing verification test |
| `tools/coverity/` | Coverity | Coverity configuration: `amd-checkers.txt`, `cert-c-all.config`, `check_results.py` |
| `tools/coverity/config/` | Coverity | GCC/Xtensa compiler compat headers, test config XML |
| `nHT/docs/` | Sphinx | Documentation including architecture, messaging interface |
| No unit test directory | N/A | No host-based unit tests found |

### Testing Cadence

| Tier | What Runs |
|---|---|
| **PR Gate** | Lint, Coverity (Xtensa), AI code review, MI450 + MI430 build, SimNow MI450 (5 variants) + MI430 |
| **Nightly** | Full SimNow matrix (19 MI450 variants + MI430), nightly build |
| **Release** | Separate MI450 and MI430 release workflows |

### Gaps

- No unit tests at all -- no CppUTest, no gtest, no on-target test applet
- No code coverage reporting
- No CodeQL or BlackDuck SCA
- No email/Confluence nightly reporting
- Coverity uses custom Xtensa compiler configuration which may have limited checker coverage
- `tools/test_sign.py` exists but is not wired into CI as a test step
- Documentation (Sphinx) is not built/validated in CI

---

## Cross-Repo Summary

### Test Maturity Comparison

| Capability | art-security | dcgpu-esid | MPRAS-Kernel | MPRAS-Applets | nht-firmware |
|---|---|---|---|---|---|
| **Host Unit Tests** | None | CppUTest | None | None | None |
| **On-Target Tests** | 9 CONFIG_TEST variants | Simulator | 5 test files | unit_test_applet | None |
| **SimNow Boot (PR)** | 22+ variants (7 ASICs) | 6 variants (2 ASICs) | 5-6 variants (2 ASICs) | None | 5-6 variants (2 ASICs) |
| **SimNow Boot (Nightly)** | 40+ variants | 20+ variants | 16+ variants | None | 19+ variants |
| **Coverity (PR)** | Yes (matrix) | Yes | Yes | Yes (matrix) | Yes |
| **Coverity (Nightly)** | Yes + commit | Yes + commit | No | No | Implied |
| **CodeQL** | Yes | Yes | No | No | No |
| **BlackDuck SCA** | Yes | Yes | No | No | No |
| **AI Code Review** | Yes | No | No | No | Yes |
| **Code Coverage** | Coco (manual) | UT coverage script | No | No | No |
| **JIRA Check** | Yes | Yes | Yes | Yes | Yes |
| **Lint** | Yes | Yes | Yes | Yes | Yes |
| **Jenkins Integration** | Yes (post-merge) | No | No | Yes (post-merge) | No |
| **Email Reporting** | Yes | Yes | No | No | No |
| **Confluence Reporting** | Yes | Yes | No | No | No |

### Top Priority Gaps Across All Repos

1. **Host-based unit testing** -- Only dcgpu-esid has CppUTest. All others lack any host-executable test framework, forcing all validation through SimNow (expensive, slow, limited by runner capacity).

2. **Code coverage** -- No repo has automated CI code coverage. art-security has Coco but it is manual. No gcov/lcov integration exists anywhere.

3. **MPRAS-Applets has no SimNow testing** -- Entirely dependent on MPRAS-Kernel's pipeline for integration validation. A broken applet could merge without any boot test.

4. **nht-firmware has zero unit tests** -- The most test-impoverished repo. Only SimNow boot acts as a functional gate.

5. **MPRAS-Kernel and MPRAS-Applets lack nightly infrastructure** -- No CodeQL, no BlackDuck, no email/Confluence reporting, no nightly workflow. Security and compliance scanning is incomplete.

6. **No cross-repo integration testing** -- Each repo tests its own binary in isolation via IFWI merge. No pipeline validates all 5 components together in a single IFWI.

7. **No regression tracking or test result trending** -- Confluence page append is one-directional. No dashboards, no pass/fail trend analysis, no flake detection.
