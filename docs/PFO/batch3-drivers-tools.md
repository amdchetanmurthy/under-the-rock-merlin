# Batch 3: Drivers, Tools, and NBIOFW Firmware Components

Comprehensive inventory of 6 firmware repositories spanning PFO drivers/tools and NBIOFW pre-silicon firmware.

---

## 1. VBL-TEE-Drv (Video Bootloader TEE Runtime Driver)

**Repo:** `PFO/VBL-TEE-Drv`

### Purpose

VBL-TEE-Drv is the Video Bootloader Runtime Driver that runs in the AMD TEE 3.0 (Trusted Execution Environment) on dGPU ASICs. It is a RISC-V based trusted application that handles GPU initialization tasks during the ESID (Early Silicon Init Driver) boot sequence, including Data Fabric (DF) memory mapping, DF RIB configuration, GFX engine setup, GMC/GMEM initialization, UMC/HBM memory configuration, SMU communication, display initialization, and CBD/LPDDR5 support. The driver operates within the PSP TEE environment and is signed with AMD firmware signing infrastructure for production deployment.

The driver currently targets the MI450 platform (TEE 3.0 architecture). It produces a signed binary `drv_vbl_runtime_MI450.sbin` that is packaged into the IFWI/BIOS SPI ROM image as a PSP directory entry. The firmware supports multiple GPU topology configurations from single-GPU (0P1G) through multi-GPU (1P4G, 18x1P4G) setups with various MID/AID/XCD combinations.

### PSP Entry

- **Binary:** `drv_vbl_runtime_MI450.sbin` (signed), `drv_vbl_runtime_MI450.bin` (unsigned)
- **FW Name (signing):** `esid_vbl_runtime_driver`
- **Entry type:** Referenced via `PFO/ivv-workflows/.github/actions/entrytype-ref` for MI450/MI430
- **Version:** Read from `vbl-dr/config/manifest.txt` (`amd.ta.version` field), 4-byte hex format

### Build System

- **Toolchain:** RISC-V GNU toolchain (`riscv64-unknown-elf-gcc`) via Conan package manager
- **Build tool:** GNU Make, multi-level Makefile hierarchy
- **Top-level Makefile:** Delegates to `vbl-dr/` subdirectory with `SOC=MI450`
- **Conan remotes required:** `swsec-conan-psp-internal`, `fw-interface-conan-local`, `swsec-markham-conan-local`
- **Commands:**
  - `make configure` -- download toolchain/dependencies via Conan
  - `make SOC=MI450` -- build and sign
  - `make SOC=MI450 NOSIGN=1` -- build without signing
  - `make SOC=MI450 simulation` -- build simulation harness
- **Signing:** Uses `fw-sign` Python package from AMD artifactory; supports development and LMS (production) signing
- **Documentation:** Doxygen-based source documentation generation

### CI/CD Workflows

| Workflow | File | Trigger | What It Does | Blocks Merge? |
|----------|------|---------|-------------|---------------|
| VBL-DR - Pull Request | `vbl-dr-pr.yml` | PR opened/sync to `main` | Lint (cpplint), Coverity (incremental), MI450 build+sign, SimNow IFWI merge + SimNow tests, SimNow report | Yes |
| Jira | `vbl-dr-jira.yml` | PR opened/edited/sync to `main` | Checks PR for Jira ticket references | Yes |
| VBL-DR - Build & Sign (Reusable) | `vbl-dr-build-sign.yml` | `workflow_call` / `workflow_dispatch` | Full build+sign pipeline: checkout, build unsigned, build simulation, optionally run unit tests, sign binaries, validate signing, generate META-INF.json, entrytype reference, upload to GHE + Artifactory | N/A (reusable) |
| VBL-DR - MI450 Release | `vbl-dr-mi450-release.yml` | Tag push `*vbl-dr_mi450-*` | Calls build-sign with `cadence=release`, generates Confluence release notes | No (release) |

### SimNow Configurations

**File:** `.github/simnow/mi450.yaml`

**Global settings:**
- `bios_source`: Artifactory
- `bios_extension`: `.sbin`
- `fatal`: true
- `simnow_date`: latest
- `postcode`: `0X800F0000`

**IFWI Merge Configurations (4):**

| Name | Base BIOS | Incremental? | Encrypted | Notes |
|------|-----------|-------------|-----------|-------|
| standard | `dgpu-spirom-fw/mi450/release/*/*_standard.sbin` | Yes | No | Primary config |
| rap_on | `*_RAP_ON.sbin` | No | No | RAP Force Applied |
| ras_on | `*_RAS_ON.sbin` | Yes | No | RAS enabled |
| rap_ras_on | `*_RAP_RAS_ON.sbin` | No | No | RAP + RAS combined |

**SimNow Test Configurations (21 total, 5 incremental/PR-gate):**

**PR-Gate (incremental=true) -- 5 configs:**

| Config Name | BSD | Timeout | Notes |
|-------------|-----|---------|-------|
| MI450 0P1G 1MID 1AID 2XCD Unsecure | `aransas_mi450_1mid1aid2xcd.bsd` | 600s | Basic standalone GPU |
| MI450 0P1G 2MID 2AID 8XCD Unsecure | `aransas_mi450_2mid2aid8xcd.bsd` | 800s | Full-size standalone |
| MI450 0P1G 2MID 2AID 8XCD Secure | `aransas_mi450_2mid2aid8xcd.bsd` | 800s | Secure mode (LC_STATE_MFG1=7) |
| MI450 1P1G 2MID 2AID 2XCD SKT7 Unsecure | `aransas_1P1G_W22_M222_skt7.bsd` | 2000s | Host-attached, socket 7 |
| MI450 1P1G 2MID 2AID 2XCD SKT7 Secure | `aransas_1P1G_W22_M222_skt7.bsd` | 2000s | Host-attached, secure |

**Nightly-Only (incremental=false) -- 16 configs:**
Covers secure variants, force-apply (RAP_ON), RAS MBAT, SKT4 variants, 1P2G multi-GPU topologies (SKT6+7), both unsecure and secure.

### Test Infrastructure

| Location | Framework | Description |
|----------|-----------|-------------|
| `Simulate/` | Custom C simulation + Python runner | Host-based simulation of VBL runtime driver |
| `Simulate/simulate.py` | Python test runner | Executes simulation binary with JSON-defined test cases |
| `Simulate/def_testcases.json` | JSON test definitions | 16+ platform configs (CEM, M111, M112, BigBoy, etc.) x 10+ test cases (NPS1/NPS2 full, HBM harvesting, UMC harvest, CBD LPDDR5, Urutu, SimNow) |
| `Simulate/run_testcases.json` | JSON test matrix | Maps platform configs to test cases to run (BIG_BOY_1G, BIG_BOY_1P1G_S7, CEM, BIG_BOY_2x1P1G_S0, BIG_BOY_18x1P4G_S0) |
| `Simulate/Makefile` | Make | Builds simulation binary (`MI450RunTimeDrv`) |
| `Simulate/src/` | C source | Simulation stubs for PSP services, device context, adapter info |

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | Lint (cpplint, FSDL exclusions), Coverity incremental, Build+Sign MI450, SimNow 5 configs (unsecure/secure, 0P1G/1P1G), Jira check |
| **Nightly** | (via SimNow nightly configs -- 16 additional configs including RAP, RAS, multi-GPU) |
| **Release** | Build+Sign with LMS production signing, Confluence release notes |

### Gaps

- No dedicated unit test framework (GoogleTest/CTest) -- only simulation-based testing
- No CodeQL static analysis workflow
- No BlackDuck SCA/license scanning
- No code coverage measurement
- Simulation tests not explicitly called in PR workflow (only through SimNow)
- No nightly workflow defined (SimNow nightly configs exist but no dedicated nightly.yml trigger)
- Missing CODEOWNERS file

---

## 2. sriov-dr (SR-IOV TEE Driver)

**Repo:** `PFO/sriov-dr`

### Purpose

The SR-IOV (Single Root I/O Virtualization) Driver is a trusted application that runs in the AMD TEE 3.0 environment on dGPU ASICs. It handles SR-IOV virtualization initialization and configuration within the PSP trusted execution environment. The driver enables hardware-level GPU virtualization, allowing a single physical GPU to be partitioned into multiple virtual functions (VFs) for use in virtualized cloud and data center environments.

The driver targets the MI450 platform and produces a signed binary that is loaded by the PSP firmware during the GPU initialization sequence. It uses the same TEE DDK (Driver Development Kit) infrastructure as VBL-TEE-Drv and shares the RISC-V toolchain and Conan-based dependency management.

### PSP Entry

- **Binary:** `drv_sriov_MI450.sbin` (signed), `drv_sriov_MI450.bin` (unsigned)
- **Signing FW name:** `sriov driver`
- **Signing config:** `supportedRelease.json` -- compression=0, encryption=0, LMS=1 (release only), signingfunction=development
- **Version:** Read from binary at offset `0x60` (4 bytes, little-endian)
- **Output variants:** `.sbin` (regular), `.csbin` (compressed), `.esbin` (encrypted), `.ecsbin` (compressed+encrypted)

### Build System

- **Toolchain:** RISC-V GNU toolchain (`riscv64-unknown-elf-gcc`) + armclang via Conan
- **Build tool:** GNU Make
- **DDK:** Uses `amd-tee3.0-ddk` from Conan (`common.mk` included from DDK)
- **Manifest:** `config/manifest.txt` (FW version, SoC FW ID, FW type)
- **Commands:**
  - `make BUILD=MI450 configure` -- download toolchain via Conan
  - `make BUILD=MI450` -- build
- **Signing:** `fw-sign` Python package, driven by `supportedRelease.json`
- **Documentation:** Doxygen support

### CI/CD Workflows

| Workflow | File | Trigger | What It Does | Blocks Merge? |
|----------|------|---------|-------------|---------------|
| SRIOV DR - Pull Request | `sriov-dr-pr.yml` | PR opened/sync to `main` | Coverity incremental (MI450), Lint (cpplint, 200 char line), Build+Sign MI450 incremental | Yes |
| SRIOV DR - Jira | `sriov-dr-jira.yml` | PR opened/edited/sync to `main` | Jira ticket validation | Yes |
| SRIOV DR - Nightly | `sriov-dr-nightly.yml` | Cron `0 0 * * *` / manual | Nightly build+sign MI450, Full Coverity (stream: `psp_tos3.0_sriov_mi450`), CERT-C coding standard, BlackDuck SCA, ELF scan, Nightly lint | No |
| SRIOV DR - Build & Sign (Reusable) | `sriov-dr-build-sign.yml` | `workflow_call` / `workflow_dispatch` | Full build+sign pipeline with restricted package support | N/A (reusable) |
| SRIOV DR - Release MI450 | `sriov-dr-release-mi450.yml` | Tag push `SR-IOV_Driver_Release_*_*` / manual | Release build+sign with LMS production signing | No (release) |

### SimNow Configurations

**None.** The sriov-dr repository has no `.github/simnow/` directory and no SimNow test configurations.

### Test Infrastructure

**None.** The repository contains no test directories, no unit tests, no simulation framework, and no test scripts. The only validation is through CI (Coverity, lint, build verification).

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | Coverity incremental, Lint (200 char line length), Build+Sign MI450 |
| **Nightly** | Full Coverity (with CERT-C coding standards), BlackDuck SCA, ELF binary scan, Full lint, Nightly build+sign |
| **Release** | Build+Sign with LMS production signing |

### Gaps

- **No unit tests whatsoever** -- this is a critical gap
- **No SimNow/emulation testing** -- no functional validation in CI
- **No CodeQL static analysis**
- **No code coverage**
- **No simulation framework** (unlike VBL-TEE-Drv)
- CODEOWNERS file exists but no branch protection rules visible
- No functional testing of SR-IOV VF creation, partition logic, or virtualization features

---

## 3. sw-security-tools (SW Security Tools)

**Repo:** `PFO/sw-security-tools` (or similar path)

### Purpose

sw-security-tools is a repository of pre-built tool binaries used across the PSP firmware ecosystem. It is explicitly described as a binary-only repository: "This repo is meant to only contain tool binaries, it should not contain source." The tools support firmware signing, key management, anti-rollback protection (SPL table generation), binary header manipulation, and various security-related operations for AMD's PSP firmware pipeline.

The repository contains tools organized by provider: `amd/` contains AMD-proprietary tools, `arm/` contains ARM GCC toolchain binaries (gcc-arm-none-eabi 5.4), and `gcc-arm/` contains additional ARM toolchain components. A `conanfile.py` at the root enables the repo to be consumed as a Conan package by other firmware repos.

### PSP Entry

This repo does not produce PSP directory entries directly. It provides the tools that other repos use to generate and sign PSP entries.

### Build System

- **Package manager:** Conan (`conanfile.py` at root)
- **Individual tool Makefiles:** Several tools under `amd/` have their own Makefiles:
  - `amd/fmtc_tool/Makefile` -- FMTC tool build
  - `amd/dgpu_bl_module_sdk/Makefile` -- Bootloader module SDK
  - `amd/key-db/Makefile` -- Key database tool
  - `amd/prom_knoll_keywrap/Makefile` -- Key wrapping tool
  - `amd/spl-table-gen/Makefile` -- SPL table generator
- **Google Test:** `google-test/` directory at root suggests some testing capability

### Tools Inventory (amd/ subdirectory)

| Tool | Purpose |
|------|---------|
| `PspDirectoryTool` | PSP directory manipulation |
| `SPClient` | Service Provider client for signing |
| `allow_list_gen` | Allow list generation |
| `binaryHeaderSpoofer` | Binary header spoofing |
| `chrome` | ChromeOS coreboot image generation |
| `dgpu_bl_module_sdk` | dGPU bootloader module SDK |
| `dgpu_df_rib_fw_sign` | dGPU DF RIB firmware signing |
| `emc_bundle_script` | EMC bundle scripting |
| `error_logging` | Error logging tools |
| `fips` | FIPS compliance tools (Linux/Windows) |
| `fmtc_tool` | FMTC tool |
| `fusefiles_csv2h` | Fuse file CSV to header converter |
| `fw-sign` | Firmware signing modules/schemas |
| `fw_bundle` | Firmware bundling |
| `header_tool` | Binary header tool |
| `json_create_palamida` | Palamida JSON creation |
| `kds_cert` | KDS certificate tools |
| `key-db` | Key database management |
| `permission_tools` | Permission management |
| `platform_fw_sign` | Platform firmware signing |
| `prom_knoll_keywrap` | Key wrapping for PROM/Knoll |
| `reg_access_whitelist_dgpu` | Register access whitelist for dGPU |
| `risc_v` | RISC-V related tools |
| `sfs_pkg` | SFS packaging |
| `sign` | General signing tools |
| `spl-table-gen` | Security Patch Level table generator |
| `stack_size_tool` | Stack size analysis |
| `sub_header_scripts` | Sub-header manipulation scripts |
| `ta_property_tool` | Trusted Application property tool |
| `test_sign` | Test signing utilities |
| `trace_log` | Trace logging tools |
| `ubu_bundle_script` | UBU bundle scripting |
| `whitelist-gen` | Whitelist generation |

### CI/CD Workflows

**None.** No `.github/workflows/` directory exists. No CI/CD pipeline.

### SimNow Configurations

**None.**

### Test Infrastructure

| Location | Type | Description |
|----------|------|-------------|
| `amd/spl-table-gen/tests.py` | Python | SPL table generation tests |
| `amd/test_sign/test_sign.py` | Python | Signing test utilities |
| `amd/key-db/test/t0010/test-me` | Shell | Key DB test case 0010 |
| `amd/key-db/test/t0020/test-me` | Shell | Key DB test case 0020 |
| `google-test/` | C++ (GoogleTest) | GoogleTest framework (dependency, not test files) |

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | None |
| **Nightly** | None |
| **Release** | None |

### Gaps

- **No CI/CD pipeline at all** -- no GitHub Actions workflows
- **No automated test execution** -- tests exist but are not integrated into any pipeline
- **No static analysis** (Coverity, CodeQL)
- **No lint checks**
- **No SCA/license scanning** despite containing third-party binaries (ARM toolchain)
- **No CODEOWNERS file**
- Binary-only repo with no source verification -- security risk for supply chain attacks
- Version management unclear for individual tools

---

## 4. cp-mi400 (Command Processor MI400 Microcode)

**Repo:** `PFO/cp-mi400` (or GFX org)

### Purpose

cp-mi400 contains the Command Processor (CP) microcode for the MI400/MI450 GPU family (GFX12 architecture). The Command Processor is the GPU's front-end hardware that fetches, decodes, and dispatches PM4 command packets from GPU command queues. The microcode implements the instruction-level firmware for four distinct CP engines:

- **PFP (Pre-Fetch Parser):** Fetches and pre-parses PM4 command packets from the ring buffer
- **ME (Micro Engine):** Executes graphics commands (draw/dispatch, state management, context switching)
- **CE (Constant Engine):** Manages constant data loading and prefetching
- **MEC (Micro Engine Compute):** Handles compute dispatch, AQL (Asynchronous Queue Language) for HSA/ROCm, and compute queue management

The microcode is written in a custom assembly language (`.uc` files -- microcode source) and built using AMD's internal GOF (Graphics Output Framework) build system with a custom assembler (`pitgen`). The code supports multiple backward-compatible variants (bc10, bc11) and an rs64 architecture variant. The build produces PM4 IT opcode headers consumed by the GPU driver stack.

### PSP Entry

- **Output:** `pm4_it_opcodes.h` and `pm4_it_opcodes.v` (opcode definitions used by driver)
- **Build artifacts:** Per-engine microcode binaries and opcode text files (`uc_opcodes_F32_*.txt`)
- **Variants:** Standard (mi400), backward-compatible (bc10, bc11), rs64 (production), mec_hwemu (hardware emulation)

### Build System

- **Build system:** AMD GOF (Graphics Output Framework) -- `gof_cmndefs.mk` / `gof_cmnrules.mk`
- **Assembler:** `pitgen` (internal AMD microcode assembler)
- **Preprocessor:** Standard C preprocessor with extensive `CPP_FLAGS`
- **Configuration:** Driven by GC feature flags (`gc_features.mk`, `env_features.mk`, `gfx_cpwd_features.mk`, `gfx_se_features.mk`)
- **Build files:**
  - `Makefile` -- Top-level, invokes GOF to produce PM4 IT opcodes
  - `ucode_common.mk` -- Extensive CPP flag configuration for all CP variants
  - `ce/Makefile`, `me/Makefile`, `mec/Makefile`, `pfp/Makefile` -- Per-engine builds
  - `*.dj` files (album.dj) -- GOF build metadata
- **Source files:** `f32_pfp.uc`, `f32_me.uc`, `f32_ce.uc`, `f32_mec.uc` (top-level) + `*_common.uc` variants

### CI/CD Workflows

**None.** No `.github/workflows/` directory. No GitHub Actions CI/CD pipeline.

### SimNow Configurations

**None.**

### Test Infrastructure

**None.** No test directories, no test files, no test framework.

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | None |
| **Nightly** | None |
| **Release** | None |

### Gaps

- **No CI/CD pipeline** -- builds rely entirely on internal GOF infrastructure
- **No automated testing of any kind** -- no unit tests, no simulation, no emulation
- **No static analysis** -- microcode assembly language may not be compatible with standard tools
- **No lint checks**
- **No README.md** -- no documentation at all
- **No CODEOWNERS file**
- Build depends on internal AMD GOF infrastructure not available in GitHub Actions
- Backward-compatibility variants (bc10, bc11) have no automated regression testing
- rs64 production code path has no validation coverage

---

## 5. pcie-cld-fw (PCIe CLD Firmware)

**Repo:** `NBIOFW/pcie-cld-fw`

### Purpose

pcie-cld-fw is pre-silicon firmware for the PCIe Physical Layer CLD (Core Logic Design) processor. It runs on a RISC-V core within the PCIe subsystem and implements PCIe Firmware Assisted Active Equalization (FAAE) -- a firmware-driven approach to PCIe link equalization using coefficient tuning and preset search algorithms. This firmware is critical for achieving reliable Gen6 PCIe link training at high data rates.

The CLD processor handles the complex equalization sequence that optimizes signal integrity across the PCIe physical layer by searching through transmitter coefficient space and preset combinations to find optimal settings for each lane. The firmware produces a hex binary (`pcie_cld_fw.hex`) and ELF file used in emulation and silicon bring-up.

### PSP Entry

- **Binary:** `pcie_cld_fw.hex` (Verilog hex format), `pcie_cld_fw.elf`, `pcie_cld_fw.bin`
- **Release artifact:** `release_<soc>_<version>.zip` containing hex/elf/bin + `META-INF.json`
- **Artifactory path:** `fw-cld-release-local/<soc>/cld_fw/` (release), `fw-nbiopresifw-rel-local/pcie-cld-fw/devel/` (development)

### Build System

- **Toolchain:** RISC-V GNU toolchain (SiFive FreedomTools-derived)
- **Build tool:** GNU Make (firmware) + CMake/Ninja (unit tests)
- **Source structure:**
  - `src/cld/` -- CLD core logic
  - `src/faae/` -- FAAE equalization algorithms (preset search, coefficient tuning)
  - `src/pcie/` -- PCIe register access
  - `src/regs/` -- Register definitions (PRISM-derived)
  - `src/util/` -- Utilities (logger)
  - `src/riscv/` -- RISC-V startup/linker scripts
  - `src/main/` -- Main entry point
  - `src/fff/` -- Fake Function Framework (test dependency)
- **Build commands:**
  - `./scripts/build_fw.sh` -- Build firmware
  - `make unittest` -- Build and run unit tests (CMake/Ninja/GoogleTest)
  - `make codeql` -- Run CodeQL analysis
  - `make coverity` -- Run Coverity analysis
- **Container:** Docker image `atlhub.amd.com/fw-nbiopresifw-dev/pcie-cld-fw:20260401`
- **Unit test build:** CMake with GoogleTest, C++17/C23 standards

### CI/CD Workflows

| Workflow | File | Trigger | What It Does | Blocks Merge? |
|----------|------|---------|-------------|---------------|
| Build | `pcie-cld-fw-build.yml` | PR, push to `main`/`release/_**`, `workflow_call` | Build firmware in Docker container, upload artifacts | Yes |
| Unit Tests | `pcie-cld-fw-unittest.yml` | PR | Run GoogleTest unit tests via `make unittest` | Yes |
| Lint | `pcie-cld-fw-lint.yml` | PR | cpplint with 180 char line length, excludes FFF | Yes |
| CodeQL | `pcie-cld-fw-codeql.yml` | PR, push to `main`/`release/_**` | CodeQL security+quality analysis, SARIF upload | Yes |
| Coverity | `pcie-cld-fw-coverity.yml` | PR, push to `main`/`release/_**` | Coverity static analysis, HTML report, SARIF upload | Yes |
| Emu Sanity | `pcie-cld-fw-emu-sanity.yml` | PR, manual, `workflow_call` | Build, then run Gen6 PCIe linkup test on Protium emulator via SSH | Yes |
| UT Coverage | `pcie-cld-fw-unittest-coverage.yml` | Manual only | Bullseye code coverage analysis, upload to Artifactory | No |
| Dev Artifacts | `pcie-cld-fw-development-artifacts.yml` | Push to `devel_**` branches | Build + upload to Artifactory devel path | No |
| Release Artifacts | `pcie-cld-fw-release-artifacts.yml` | Tag push `release_**` | Build + generate META-INF.json + upload to Artifactory release path | No (release) |
| AI Code Review | `workflow-ai-review.yml` | PR opened/reopened, `/ai-review` comment, manual | AI-powered PR code review using reusable NBIOFW workflow | No (informational) |

### SimNow Configurations

**None.** pcie-cld-fw uses hardware emulation (Protium) rather than SimNow for functional testing.

### Test Infrastructure

| Location | Framework | Description |
|----------|-----------|-------------|
| `src/faae/test/faae_main_test.cpp` | GoogleTest | FAAE main logic tests |
| `src/faae/test/coefficient_tuning_test.cpp` | GoogleTest | Coefficient tuning algorithm tests |
| `src/faae/test/preset_search_test.cpp` | GoogleTest | Preset search algorithm tests |
| `src/faae/test/logger_test.cpp` | GoogleTest | Logger utility tests |
| `src/pcie/test/pcie_test.cpp` | GoogleTest | PCIe register access tests |
| `src/faae/mock/` | FFF (Fake Function Framework) | Mock implementations for FAAE module |
| `src/pcie/mock/` | FFF | Mock implementations for PCIe module |
| `src/cld/mock/` | FFF | Mock implementations for CLD module |
| `src/util/mock/` | FFF | Mock implementations for utility module |
| `scripts/emu/runptm.sh` | Shell | Protium emulation test runner |
| `scripts/emu/runplato.sh` | Shell | Plato emulation test runner |

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | Build, Unit tests (GoogleTest), Lint (cpplint), CodeQL, Coverity, Emulation sanity (Gen6 linkup on Protium) |
| **Nightly** | Same as PR (triggered by push to main) |
| **Release** | Build + artifact packaging + META-INF.json generation |
| **On-Demand** | Bullseye code coverage (manual trigger) |

### Gaps

- Code coverage workflow is manual-only (not part of PR gate or nightly)
- No BlackDuck SCA/license scanning
- No Jira ticket validation on PRs
- Emulation test only covers Gen6 linkup -- no tests for specific FAAE algorithm edge cases on emulator
- No SimNow testing (uses emulation only)
- CODEOWNERS file exists but contents not reviewed
- AI PR platform configs (`.ai_pr_platform/`) suggest AI-assisted Coverity/CodeQL fix capabilities

---

## 6. ucie-fw (UCIe Firmware)

**Repo:** `NBIOFW/ucie-fw`

### Purpose

ucie-fw is the UCIe (Universal Chiplet Interconnect Express) firmware that runs on a SiFive E2 RISC-V embedded core within the UCIe PHY (Physical Layer). This is bare-metal firmware (no OS) responsible for UCIe link training, sideband messaging, FDI handshake, power management, runtime calibration, and error handling between chiplets connected via the UCIe standard.

The firmware handles the complex multi-stage UCIe link training sequence including analog PHY (APHY) calibration, CLD adapter state machine management, and interrupt-driven event processing. It operates under a critical hardware constraint: all data access must be 32-bit wide (no byte/halfword access) due to missing byte-enable support in the SRAM-to-core memory interface. The firmware supports multiple SoC targets (MI450, Magnus/AlphaTrion2, Arcadia) with per-SoC register headers.

### PSP Entry

- **Binary:** `ucie_fw.hbin` (unsigned with PSP header), plus signed variants
- **Build variants:** release, KGD, SNPS D2D BIST, SNPS training, UCIS short training, UCIS short2 training
- **FW Type ID:** `TypeId0x1EC`
- **Signing:** fw-sign with per-project config (MI450, AlphaTrion2); supports PQC (LMS) post-quantum signing
- **Artifactory paths:**
  - Release: `fw-ucie-release-local/<soc>/`
  - Development: `fw-nbiopresifw-rel-local/ucie-fw/devel/`

### Build System

- **Toolchain:** SiFive RISC-V toolchain (FreedomTools 3.1.2 derived, GCC 13.2.0)
- **Build tools:**
  - Make (firmware) -- `scripts/build_fw.sh` orchestrator
  - CMake + Ninja (unit tests, static analysis)
- **SoC targets:** MI450 (default), Magnus, Arcadia
- **Build commands:**
  - `make ucie_fw_release SOC=mi450` -- build release for MI450
  - `make ucie_fw_all SOC=mi450` -- build all variants for MI450
  - `make ucie_fw_all_soc` -- build all variants for all SoCs
  - `make unittest` -- run unit tests
  - `make unittest_gcov` -- run unit tests with gcov coverage
  - `make codeql` / `make coverity` -- static analysis
- **Container:** Docker image `atlhub.amd.com/fw-nbiopresifw-dev/ucie-fw:20260416-67251aa`
- **Unit test build:** CMake with GoogleTest, C++17/C23, warnings-as-errors, optional gcov coverage

### CI/CD Workflows

| Workflow | File | Trigger | What It Does | Blocks Merge? |
|----------|------|---------|-------------|---------------|
| PR Check | `ucie-fw-pr.yml` | PR opened/sync/reopened/unlabeled | Label check, AI code review, Lint, Build (build + build-all-soc), CodeQL, Coverity, Unit tests (no coverage), Emu sanity (skipped for Arcadia) | Yes |
| Build FW | `ucie-fw-build.yml` | Manual | Build single SoC target (mi450/magnus) | No |
| Nightly Check | `ucie-fw-nightly.yml` | Cron `0 6 * * *` / manual | Lint, Build (both targets), BlackDuck scan, CodeQL, Coverity, Unit tests (with coverage), Emu sanity | No |
| Lint Check | `ucie-fw-lint.yml` | Manual | Copyright check, optional sanitization check | No |
| Unit Test | `ucie-fw-unittest.yml` | Manual | Unit tests with optional gcov coverage | No |
| Emu Sanity Test | `ucie-fw-emu-sanity-test.yml` | Manual | Build + emulation sanity test | No |
| Publish Artifacts | `ucie-fw-publish-artifacts.yml` | Manual, push to `devel_**`, tags `devel_**`/`release_**` | Build + upload to Artifactory (devel/release paths) | No |
| IFWI/BIOS Release | `ucie-fw-ifwi-bios-release.yml` | Manual | Build, sign (fw-sign), optional PQC (LMS) signing, upload to release Artifactory | No (release) |
| BlackDuck Scan | `ucie-fw-blackduck-scan.yml` | Called from nightly | BlackDuck SCA scanning | No |
| CodeQL | `ucie-fw-codeql.yml` | Called from PR/nightly | CodeQL static analysis | Yes (via PR) |
| Coverity | `ucie-fw-coverity.yml` | Called from PR/nightly | Coverity static analysis | Yes (via PR) |
| Branch Merge | `ucie-fw-branch-merge.yml` | (details not read) | Branch merge automation | No |
| Docker Build | `ucie-fw-docker-build.yml` | (details not read) | Build Docker container image | No |
| Docker Cleanup | `ucie-fw-docker-cleanup.yml` | (details not read) | Clean up Docker images | No |
| Emu Cleanup | `ucie-fw-emu-cleanup.yml` | (details not read) | Clean up emulation workspaces | No |
| AI Code Review | `workflow-ai-review.yml` | PR opened/reopened, `/ai-review` comment | AI-powered PR code review | No (informational) |

**Reusable workflows (7):** `reusable-fw-build.yml`, `reusable-fw-unittest.yml`, `reusable-fw-lint.yml`, `reusable-fw-codeql.yml`, `reusable-fw-coverity.yml`, `reusable-fw-emu-test.yml`, `reusable-fw-blackduck-scan.yml`

### SimNow Configurations

**None.** ucie-fw uses hardware emulation (Protium, UCIS CIT platform) rather than SimNow.

### Test Infrastructure

| Location | Framework | Description |
|----------|-----------|-------------|
| `src/ucie_fw/test/ucie_fw_test.cpp` | GoogleTest | Main firmware logic tests |
| `src/ucie_fw/test/modules/ucie_mem_utils_test.cpp` | GoogleTest | Memory utilities tests (critical for 32-bit access constraint) |
| `src/ucie_fw/mock/` | FFF (Fake Function Framework) | Mock implementations for all external module calls |
| `src/fff/` | FFF library | Fake Function Framework dependency |
| `CMakeLists.txt` | CMake | Top-level CMake for unit tests + static analysis |
| `src/ucie_fw/CMakeLists.txt` | CMake | UCIe FW module CMake (test target) |
| `src/ucie_fw/mock/CMakeLists.txt` | CMake | Mock library CMake |
| Emulation tests | Protium + Python | x1 retrain_errinj test, x4 cake_e2e test via SSH to `pldcvemu01` |

**Emulation test details:**
- **x1 retrain_errinj:** Tests link retrain with error injection on x1 UCIe link, with SRAM dump and trace log
- **x4 cake_e2e:** End-to-end CAKE test on x4 UCIe link, verifying data transfer integrity
- Both tests use `scripts/run_ptm.py` with Protium builds from `/proj/nbio_emu_builds/`
- Tests produce trace logs via `btl2exec.py` for post-mortem analysis

### Testing Cadence

| Tier | Tests |
|------|-------|
| **PR Gate** | Label check, AI review, Lint (copyright), Build (2 targets), CodeQL, Coverity, Unit tests (no coverage), Emu sanity (x1 retrain_errinj + x4 cake_e2e) |
| **Nightly** | Lint, Build (2 targets), BlackDuck SCA, CodeQL, Coverity, Unit tests (with gcov coverage), Emu sanity |
| **Release** | Build + fw-sign + optional PQC (LMS) post-quantum signing + Artifactory upload |
| **On-Demand** | Manual unit test with coverage, manual emu test, manual lint with sanitization check |

### Gaps

- Unit test coverage is limited (only 2 test files for a large firmware codebase)
- No Jira ticket validation on PRs
- Emulation test timeout is 30 minutes but does not cover all link training scenarios
- No functional tests for sideband messaging, FDI handshake, or power management
- Arcadia-specific testing gaps (emu sanity is explicitly skipped for Arcadia branches)
- No integration tests between UCIe FW and other NBIO components
- REVIEW.md exists but contents not analyzed
- Coverage report only available in nightly (not PR gate)

---

## Cross-Repo Summary

### Maturity Comparison

| Capability | VBL-TEE-Drv | sriov-dr | sw-security-tools | cp-mi400 | pcie-cld-fw | ucie-fw |
|------------|-------------|----------|--------------------|----------|-------------|---------|
| CI/CD Pipeline | Yes | Yes | **None** | **None** | Yes | Yes |
| Unit Tests | Simulation | **None** | Minimal (manual) | **None** | GoogleTest | GoogleTest |
| Static Analysis (Coverity) | Yes (PR) | Yes (PR+Nightly) | **None** | **None** | Yes (PR) | Yes (PR+Nightly) |
| Static Analysis (CodeQL) | **None** | **None** | **None** | **None** | Yes (PR) | Yes (PR+Nightly) |
| Lint | Yes (PR) | Yes (PR+Nightly) | **None** | **None** | Yes (PR) | Yes (PR+Nightly) |
| SimNow Testing | Yes (21 configs) | **None** | N/A | **None** | **None** | **None** |
| Emulation Testing | **None** | **None** | N/A | **None** | Yes (Gen6 linkup) | Yes (retrain+cake_e2e) |
| Code Coverage | **None** | **None** | **None** | **None** | Manual (Bullseye) | Nightly (gcov) |
| SCA/License Scan | **None** | Nightly (BlackDuck) | **None** | **None** | **None** | Nightly (BlackDuck) |
| Jira Integration | Yes (PR) | Yes (PR) | **None** | **None** | **None** | **None** |
| Signing Pipeline | Yes | Yes | N/A | N/A | No | Yes (incl. PQC) |
| Docker Container | No | No | No | No | Yes | Yes |
| AI Code Review | No | No | No | No | Yes | Yes |

### Org Comparison: PFO vs NBIOFW

The PFO repos (VBL-TEE-Drv, sriov-dr, sw-security-tools, cp-mi400) use shared IVV workflow infrastructure (`PFO/ivv-workflows`) with standardized build/sign/SimNow patterns. The NBIOFW repos (pcie-cld-fw, ucie-fw) use their own reusable workflow library (`NBIOFW/gha-workflows`) with Docker-containerized builds and hardware emulation testing.

NBIOFW repos are generally more mature in CI/CD practices:
- Both have CodeQL + Coverity + Lint + Unit tests + Emulation tests in PR gate
- Both use Docker containers for reproducible builds
- Both have AI-powered code review integration
- ucie-fw additionally has BlackDuck SCA and PQC (post-quantum) signing support

### Critical Gaps Across All Repos

1. **sw-security-tools and cp-mi400 have zero CI/CD** -- these repos are completely untested in automation
2. **sriov-dr has no unit tests or functional tests** -- only static analysis validates the code
3. **No repo has integration testing** between components (e.g., VBL-DR + SRIOV-DR interaction, CLD FW + UCIe FW coordination)
4. **Code coverage is inconsistent** -- only ucie-fw runs it regularly (nightly); pcie-cld-fw has it manual-only; others have none
5. **CodeQL adoption is partial** -- only NBIOFW repos have it; PFO repos lack this second static analysis dimension
6. **No end-to-end boot testing** that validates all components together in a full IFWI image
