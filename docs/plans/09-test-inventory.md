# 09 - Existing Test Inventory Across Firmware Repos

> Generated 2026-05-05 by analyzing all 17 firmware repos under `/firmware/`.
> Skipped: `pytorch` (upstream), `caliptra-sw` (upstream), `onnxruntime` (upstream).

---

## Executive Summary

| Capability | Repos with it | Repos without it |
|---|---|---|
| PR gate workflow | 14 of 15 | cp-mi400 |
| Coverity on PR | 13 of 15 | amd-node-check, cp-mi400 |
| Lint on PR | 11 of 15 | amd-tee3_0 (partial), mi300x_ubb_soteria_fw, cp-mi400, sw-security-tools |
| SimNow on PR | 10 of 15 | amd-node-check, mi300x_ubb_soteria_fw, sriov-dr, cp-mi400, sw-security-tools |
| Unit tests in PR gate | 3 of 15 | Most repos lack automated UT in CI |
| Nightly workflow | 7 of 15 | Many repos lack scheduled regression |
| Hardware / DCAuto on PR | 3 of 15 | art-security, amd-tee3_0, asp-fmc (via Jenkins trigger) |
| AI code review on PR | 3 of 15 | art-security, asp-fmc, mpifoe-fw |
| Release workflow | 13 of 15 | cp-mi400, sw-security-tools |
| No CI at all | 2 of 15 | cp-mi400, sw-security-tools |

---

## IVV Reusable Workflows (PFO/ivv-workflows)

Nearly all repos use the same set of reusable workflows from `PFO/ivv-workflows`:

| Workflow | Purpose | Used by |
|---|---|---|
| `pr-incremental-coverity-builder.yml` | Incremental Coverity static analysis on PR diffs | amd-tee3_0, art-security, asp-fmc, dcgpu-esid, mpifoe-fw, mpio, MPRAS-Applets, MPRAS-Kernel, nht-firmware, pmfw-firmware, sriov-dr, VBL-TEE-Drv |
| `lint-cpp.yml` | C/C++ linting (clang-format) | amd-tee3_0, art-security, asp-fmc, dcgpu-esid, mpifoe-fw, MPRAS-Applets, MPRAS-Kernel, nht-firmware, sriov-dr, VBL-TEE-Drv |
| `simnow-lnx.yml` | SimNow boot test on Linux | amd-tee3_0, art-security, asp-fmc, dcgpu-esid, mpifoe-fw, mpio, MPRAS-Kernel, nht-firmware, pmfw-firmware, VBL-TEE-Drv |
| `simnow-report.yml` | SimNow results aggregation and PR reporting | Same as above |
| `simoxide-boot-test.yml` | SimOxide boot test (newer, for WH-LP) | art-security, asp-fmc |
| `bios-merge.yml` | IFWI/BVM merge for SimNow testing | amd-tee3_0, art-security, asp-fmc, dcgpu-esid, MPRAS-Kernel, VBL-TEE-Drv |
| `incremental-kws.yml` | Keyword scan (IP/export control) | amd-tee3_0, art-security, asp-fmc |
| `jira-checker.yml` | Jira ticket validation | mpio, MPRAS-Applets |
| `pr-ai-codereview.yml` | LLM-powered code review | art-security, asp-fmc, mpifoe-fw |
| `gatekeeper-placeholder.yml` | Merge queue placeholder for external gates | amd-tee3_0 |
| `trigger-jenkins` (action) | Trigger Jenkins hardware smoke tests | amd-tee3_0, art-security, asp-fmc |

---

## Per-Repo Detailed Analysis

### 1. amd-node-check (amd-node-check---wip-to-be-updated-amd-node-check)

**Language:** Python

**PR Gate:**
- **Trigger:** Auto on PR to `develop` branch
- **What runs:** `pre-commit` hooks only (linting, formatting)
- **Blocking:** Yes (required check)
- **Coverity:** No (CodeQL instead, runs on PR + weekly schedule)
- **SimNow:** No (Python tool, not firmware)

**Unit Tests:**
- **Framework:** pytest
- **Test files:** ~85 test files under `tests/unit/` and `tests/integration/`
- **Coverage:** CLI, core, execution, HW discovery (CPU/GPU/NIC), monitoring, output
- **Config:** `conftest.py` at multiple levels
- **CI integration:** Not run in PR gate; run in nightly regression via `run-regression.py`

**Nightly:**
- `nightly-regression.yml`: Runs daily at midnight PST
- Generates dummy hardware config, runs regression suite from `tests/regressions/nightly.yml`
- Posts failure summaries to Microsoft Teams via Adaptive Card webhook
- Tracks pass/fail counts with `regression-env.txt`

**Release:** `build-packages.yml` - Builds .deb/.rpm/.tar.gz packages on tag push or manual trigger

**Gaps:**
- No Coverity (uses CodeQL instead -- adequate for Python)
- No lint in PR (uses pre-commit instead -- adequate)
- pytest suite is NOT run in PR gate, only nightly
- No SimNow (not applicable -- Python tool)

---

### 2. amd-tee3_0

**Language:** C (RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `amd-staging` + merge_group
- **What runs:**
  - Coverity (incremental, per SoC matrix via `supportedSocs.json`)
  - Lint (`lint-cpp.yml`, 200-char line length)
  - Keyword scan (KWS)
  - Multi-ASIC builds: MI450, MI430, WH SP7, WH SP8, WH LP, Rosenhorn, Medusa1, Olympicridge, Arcadia, AT2
  - SimNow boot tests: MI450, MI430, WH, WH SP8, Medusa, AT2 (incremental configs)
  - CC tests (SPDM, Sideband SPDM, DOE) via `run-cc-tests.yml`
  - Hardware smoke via Jenkins (`VeniceTeeMasterSmoke`)
  - DDK builds for WH/MDS/OLR
- **Blocking:** Yes (auto PR trigger with merge_group support)

**Unit Tests:**
- **Framework:** Custom C test harness (not a standard framework)
- **Test files:** ~10 test files (unit_test.c, dram_test.c, spdm tests, etc.)
- **Coverage:** SPDM responder, DOE mailbox, link tests, RAS self-test

**SimNow Configs:** `.github/simnow/` with YAML for mi450, mi430, wh, whsp8, mds, at2
- Each has `incremental: true/false` flag to control what runs on PR vs nightly
- Configs specify: BSD path, BIOS name, script, timeout, postcode, extra arguments

**Nightly:**
- `tee-nightly.yml`: Full (non-incremental) builds + SimNow across all platforms
- `tee-nightly-simnow.yml`: SimNow-only nightly

**Smoke:** `tee-smoke.yml`: Reusable workflow for post-merge/tag smoke testing including optional DCAuto

**Release:** `tee-release.yml`, `tee-sdk-release.yml`

**Gaps:**
- Unit tests exist but are NOT run as host-side unit tests in CI
- No pytest/CppUTest-style host-side unit tests
- CC tests (SPDM/DOE) are good but limited to MI450 on PR

---

### 3. art-security

**Language:** C (RISC-V firmware + Rust for arty component)

**PR Gate:**
- **Trigger:** Auto on PR to `amd-staging`
- **What runs:**
  - Coverity (incremental, matrix from `artsec-release.json`, supports GCC + LLVM toolchains)
  - Lint (`lint-cpp.yml`, 200-char)
  - AI code review (`pr-ai-codereview.yml`)
  - Keyword scan (KWS)
  - Multi-ASIC builds: MI450, MI430, WH, WH SP8, WH LP, AT2, MDS, OLR, MTP, RH, Arcadia
  - Fuse test builds across all ASICs
  - SimNow: MI450, MI430, WH, WH SP8, WH LP (SimOxide), AT2, MDS
  - Hardware: Jenkins `VeniceArtSecurityMasterSmoke`
  - AGESA docs check
- **Blocking:** Yes

**Unit Tests:**
- **Framework:** Custom C tests (built into firmware)
- **Test files:** 12 test files under `common/test/` (art_log, caliptra, DPE, fuse, HSP, keydb, RAP, RSMU, SPDM, startup, WAFL)
- **CI integration:** Tests are compiled as firmware variants, not run as host-side unit tests

**DCAuto/Hardware:**
- `artsec-pr-dcauto.yml`: Comment-triggered (`[TRIGGER_SMOKE]`) DCAuto pre-submission testing
- `artsec-manual.yml`, `artsec-manual-mi450.yml`, `artsec-manual-wh.yml`: Manual dispatch workflows

**SimNow Configs:** `.github/simnow/` with mi450, mi430, wh, whsp8, whlp, at2, mds

**Nightly:** `artsec-nightly.yml`

**Release:** `artsec-release.yml`

**Gaps:**
- No host-side unit test framework (all tests are firmware-level)
- DCAuto is comment-triggered, not automatic

---

### 4. asp-fmc

**Language:** C (RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `amd-staging`
- **What runs:**
  - Coverity (9 ASIC variants including Prism)
  - Lint (`lint-cpp.yml`, 200-char)
  - AI code review
  - Keyword scan (KWS)
  - Multi-ASIC builds: MI450, MI430, AT2, WH, WH SP8, WH LP, MTP, MDS1, OLR, RH, ARCD
  - SimNow: MI450, MI430, AT2, WH, WH SP8, WH LP (SimOxide), MDS1
  - Hardware: Jenkins `VeniceAspfmcMasterSmoke`
- **Blocking:** Yes

**Unit Tests:** None found

**SimNow Configs:** `.github/simnow/` with mi450, mi430, wh, whsp8, whlp, mds, at2

**Nightly:** `aspfmc-nightly.yml`

**Post-merge:** `aspfmc-post-merge.yml`

**Simnow standalone:** `aspfmc-simnow.yml`

**Release:** `aspfmc-release.yml`

**Gaps:**
- No unit tests at all
- No pytest/CppUTest coverage
- Relies entirely on build + SimNow + hardware smoke for validation

---

### 5. dcgpu-esid

**Language:** C/C++ (RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `main`
- **What runs:**
  - Coverity (MI450)
  - Lint (`lint-cpp.yml`)
  - MI450 + MI430 incremental builds with `unit-test: true`
  - SimNow boot tests for MI450 (via build-sign workflow which includes IFWI merge + SimNow)
- **Blocking:** Yes

**Unit Tests:**
- **Framework:** CppUTest (Google Test-style wrappers)
- **Test files:** ~100+ test files under `dcgpu/Test/UT/Source/`
- **Coverage:** Extremely thorough -- DF (Data Fabric), GFX, GMEM (UMC/HBM), GpuMem (MMHUB/ATHUB), NBIO, SMU, Drivers, Libraries
- **CI integration:** Run via `make SOC=$SOC UT TARGET=dcgpu/Test/UT/Source/` in `dcgpu-esid-ut.yml`
- **Invocation:** Called from `dcgpu-esid-build-sign.yml` when `unit-test: true`
- **Host-side:** Tests compile and run on x86 host with mocks

**SimNow Configs:** `.github/simnow/` with mi450, mi430

**Simulate:** `Simulate/def_testcases.json` -- defines SimNow test cases with expected postcodes

**Nightly:** `dcgpu-esid-nightly.yml`

**Release:** `dcgpu-esid-release.yml`, `dcgpu-esid-mi430-release.yml`, `dcgpu-esid-mi450-release.yml`

**Gaps:**
- Best-in-class unit test coverage among all repos
- MI430 unit tests not clearly enabled (build has `unit-test: true` but UT workflow only supports mi450)
- No AI code review

---

### 6. mi300x_ubb_soteria_fw

**Language:** C (ARM firmware) + Python tooling

**PR Gate:**
- **Trigger:** Push to any branch (not specifically PR-gated)
- `build-CI.yml`: Builds on every push to any branch
- `black-duck-scan.yml`: Security/license scanning
- No Coverity, no lint, no SimNow
- **Blocking:** Unclear -- `build-CI.yml` triggers on push, not explicitly on PR

**Unit Tests:**
- **Framework:** pytest (for Python tooling only)
- **Test files:** 4 pytest files under `tools/*/tests/`
- **Coverage:** eROT automation, Black Duck scan tooling, MongoDB URI check, BD config update
- **Config:** `pytest.ini` at root, `conftest.py` in `tools/automation/tests/`
- **CI integration:** Not run in CI

**Nightly:** None

**Release:** `build-release.yml`

**Gaps:**
- No Coverity
- No lint
- No SimNow
- pytest tests exist but are NOT run in CI
- No nightly
- `build-CI.yml` runs on all branch pushes (noisy), not specifically PR-gated

---

### 7. mpifoe-fw

**Language:** C (Xtensa/Zephyr firmware) + Python

**PR Gate:**
- **Trigger:** Auto on PR to `main`
- **What runs:**
  - Coverity (Xtensa compiler, MI450)
  - Lint (`lint-cpp.yml`)
  - AI code review
  - Silicon + SimNow binary builds for MI450
  - SimNow boot tests (MI450 + MI430 via simnow configs)
- **Blocking:** Yes

**Unit Tests:**
- **Framework:** Zephyr Twister (testcase.yaml) + pytest
- **Test files:**
  - `tests/ifoe_ras/testcase.yaml` -- RAS test with pytest harness on native_sim
  - `tests/ifoe_tlm/testcase.yaml` -- Telemetry test with pytest harness on native_sim
  - `src/tests/test_cache.c` -- C unit test
  - `scripts/regressions/test_ifoe_regressions.py` -- pytest regression suite
  - `tests/hello_world/test_hello_world.py` -- basic smoke
- **Config:** `pytest.ini` and `conftest.py` in `scripts/regressions/`
- **CI integration:** Zephyr tests likely run via Twister but not clearly in PR gate

**SimNow Configs:** `.github/simnow/` with mi450, mi430

**Nightly:** `mpifoe-nightly.yml`

**Bringup:** `mpifoe-bringup.yml`

**Release:** `mpifoe-release-mi430.yml`, `mpifoe-release-mi450.yml`

**Gaps:**
- Zephyr Twister tests exist but unclear if they run in PR gate
- pytest regression tests not clearly integrated into CI
- Good structure for test expansion

---

### 8. mpio

**Language:** C (RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `rel/mi450`
- **What runs:**
  - Branch validation
  - Jira ticket check
  - Format check (custom format-check workflow)
  - Coverity (incremental with custom `check_results.py`)
  - x86 tests: MCTP tests, prototype tests, DxioCosim test, shmem tests, unit tests
  - `mpio_build_check: false` (disabled -- Coverity handles build)
  - `mpio_x86_check: true`
- **Blocking:** Yes

**Unit Tests:**
- **Framework:** Custom x86 test harness
- **Test directories:** `tests/`, `comphandlers/tests/`, `drivers/tests/`, `gml/tests/`, `hasl/tests/`, `tests/x86/tests/`
- **Coverage:** MCTP, prototypes, DxioCosim, shared memory, unit tests
- **CI integration:** Explicitly enabled in PR gate via `build.yml` reusable workflow

**SimNow Configs:** `.github/simnow/` with mi450, mi430

**Nightly:** None found (no nightly workflow)

**Release:** `mpio-release-mi430.yml`, `mpio-release-mi450.yml`

**Gaps:**
- No nightly workflow
- No AI code review
- x86 tests are good but test framework is custom (not standard CppUTest/GTest)

---

### 9. MPRAS-Applets

**Language:** C (Zephyr/RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `main`, `dev/*`, `rel/*`
- **What runs:**
  - Coverity (WS_SP7, WH_SP8, WH_LP matrix via Xtensa runner)
  - Lint
  - Jira check
  - WH SP7 build (pcie_applet)
- **Blocking:** Yes

**Unit Tests:**
- `unit_test_applet/src/pcie_scalable_test.c` -- single test file, appears to be firmware-level test

**SimNow:** None in PR gate

**Smoke:** `mpras_applets-smoke.yml` -- post-merge smoke

**Release:** `mpras_applets-release.yml`

**Gaps:**
- No SimNow in PR gate
- Minimal unit test coverage (1 test file)
- No nightly workflow

---

### 10. MPRAS-Kernel

**Language:** C (Zephyr/RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `dev/*`, `rel/*`
- **What runs:**
  - Coverity
  - Lint
  - MI450 + MI430 builds
  - SimNow boot tests (MI450, MI430 via IFWI merge + SimNow)
- **Blocking:** Yes

**Unit Tests:**
- **Framework:** Custom C tests
- **Test files:** `app/test/dram_test.c`, `messaging_if_test.c`, `poison_test.c`, `remote_die_smn_test.c`, `test_main.c`
- **CI integration:** Tests are firmware-level, compiled into binary

**SimNow Configs:** `.github/simnow/` with mi450, mi430

**Nightly:** None found

**Release:** `mpras_kernal-release.yml` (note: typo in filename)

**Gaps:**
- No nightly workflow
- Tests are firmware-level only, no host-side unit tests

---

### 11. nht-firmware

**Language:** C (Xtensa/Zephyr firmware)

**PR Gate:**
- **Trigger:** Auto on PR (all branches)
- **What runs:**
  - Coverity (Xtensa runner)
  - Lint
  - MI450 + MI430 builds
  - SimNow boot tests (MI450 via IFWI merge + SimNow)
- **Blocking:** Yes

**Unit Tests:** None found (only `tools/test_sign.py` which is a signing utility test)

**SimNow Configs:** `.github/simnow/` with mi450, mi430

**Nightly:** `mpnht-nightly.yml`

**Release:** `mpnht-release-mi430.yml`, `mpnht-release-mi450.yml`

**Gaps:**
- No unit tests
- No AI code review

---

### 12. pmfw-firmware

**Language:** C (Xtensa firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `dev/mi450-main`
- **What runs:**
  - Coverity x3 (MID MP1, AID MP5, XCD MP5 -- separate Xtensa builds)
  - AI suggestions enabled in Coverity
  - Builds (implied via Coverity build commands)
- **Blocking:** Yes

**Unit Tests:**
- **Framework:** Custom Python test runner + Lua stimulus
- **Test files:** `firmware/main/test/test_runner.py`, `stimulus/python/default/clk_test.py`, `stimulus/python/default/imu_start_test.py`
- **Test models:** `firmware/main/test/models/test_driver/` -- simulation model drivers
- **CI integration:** Not run in PR gate

**SimNow Configs:** `.github/simnow/` with mi450, mi430

**Smoke:** `pmfw-smoke.yml`

**FEAS:** `pmfw-feas.yml` (feature analysis)

**Release:** `pmfw-release-mi450.yml`

**Gaps:**
- No lint in PR gate
- No SimNow in PR gate (only smoke/FEAS)
- Test infrastructure exists but not integrated into CI
- No nightly workflow

---

### 13. sriov-dr

**Language:** C (RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `main`
- **What runs:**
  - Coverity (MI450)
  - Lint (200-char)
  - MI450 incremental build
- **Blocking:** Yes

**Unit Tests:** None found

**SimNow:** None in PR gate

**Nightly:** `sriov-dr-nightly.yml`

**Release:** `sriov-dr-release-mi450.yml`

**Gaps:**
- No SimNow
- No unit tests
- Minimal CI -- build + Coverity + lint only

---

### 14. VBL-TEE-Drv

**Language:** C/C++ (RISC-V firmware)

**PR Gate:**
- **Trigger:** Auto on PR to `main`
- **What runs:**
  - Coverity (MI450)
  - Lint (with exclusions for FSDL directories)
  - MI450 build with `unit-test: true`
  - SimNow boot tests (MI450 via IFWI merge + SimNow, combined with dcgpu-esid IFWI)
- **Blocking:** Yes

**Unit Tests:**
- Shares test infrastructure with dcgpu-esid (same CppUTest framework)
- `unit-test: true` flag in build workflow
- `Simulate/def_testcases.json` -- SimNow test case definitions

**SimNow Configs:** `.github/simnow/` with mi450

**Nightly:** None found

**Release:** `vbl-dr-mi450-release.yml`

**Gaps:**
- No nightly workflow
- SimNow only for MI450 (no MI430, WH, etc.)
- No AI code review

---

### 15. cp-mi400

**Language:** Assembly/C (GPU command processor firmware)

**PR Gate:** NONE -- no `.github/workflows/` directory

**Unit Tests:**
- Test directories exist: `rs64/uvm_api/compute/mec/test/`, `mes/test/`, `gfx/me/test/`, `gfx/pfp/test/`, `wgs/api/test/`
- These appear to be firmware-level validation, not automated unit tests

**Nightly:** None

**Release:** None

**Gaps:**
- No CI pipeline at all
- No Coverity, no lint, no build verification, no SimNow
- Test directories exist but no automation

---

### 16. sw-security-tools

**Language:** Python + C (security tooling)

**PR Gate:** NONE -- no `.github/workflows/` directory

**Unit Tests:**
- `amd/chrome/test_script/testcases/` -- Chrome OS test scripts
- `amd/key-db/test/` -- key database tests
- `amd/test_sign/test_sign.py` -- signing test utility

**Nightly:** None

**Release:** None

**Gaps:**
- No CI pipeline at all
- No Coverity, no lint, no build verification
- Test scripts exist but no automation

---

## SimNow Configuration Patterns

### Standard SimNow YAML structure (`.github/simnow/<platform>.yaml`):

All repos follow a consistent YAML schema:

```yaml
ifwi_merge:
  configurations:
    - name: "standard"
      base_bios: "artifactory/path/to/*.sbin"
      cadence: "ordb"
      program: "mi450"
      encrypted: false
      skip_sign: true
      incremental: true   # <-- controls PR vs nightly

bvm:
  configurations:
    - name: "apa_bvm"
      base_bios: "path/to/SBIOS"

simnow:
  bios_source: "Artifactory"
  simnow_date: "latest"
  fatal: true
  postcode: "0XAA55AA55"
  configurations:
    - name: "mi450_standard"
      variant: "standard"
      bsd: "path/to/bsd"
      bios_name: "mi450_standard_fw"
      script: "path/to/script.py"
      simnow_timeout: 1200
      extra_arguments: "--run_direct"
      incremental: true   # <-- true = runs on PR, false = nightly only
```

### Platforms with SimNow configs per repo:

| Repo | MI450 | MI430 | WH | WH SP8 | WH LP | MDS | AT2 |
|---|---|---|---|---|---|---|---|
| amd-tee3_0 | Y | Y | Y | Y | - | Y | Y |
| art-security | Y | Y | Y | Y | Y | Y | Y |
| asp-fmc | Y | Y | Y | Y | Y | Y | Y |
| dcgpu-esid | Y | Y | - | - | - | - | - |
| mpifoe-fw | Y | Y | - | - | - | - | - |
| mpio | Y | Y | - | - | - | - | - |
| MPRAS-Kernel | Y | Y | - | - | - | - | - |
| nht-firmware | Y | Y | - | - | - | - | - |
| pmfw-firmware | Y | Y | - | - | - | - | - |
| VBL-TEE-Drv | Y | - | - | - | - | - | - |

---

## Test Framework Summary

| Repo | Framework | Test Type | # Test Files | In CI? |
|---|---|---|---|---|
| amd-node-check | pytest | Host-side Python | ~85 | Nightly only |
| amd-tee3_0 | Custom C | Firmware-level | ~10 | Via SimNow |
| art-security | Custom C | Firmware-level | ~12 | Via SimNow |
| asp-fmc | None | - | 0 | - |
| dcgpu-esid | CppUTest | Host-side x86 | ~100+ | YES (PR gate) |
| mi300x_ubb_soteria_fw | pytest | Tooling tests | ~4 | No |
| mpifoe-fw | Zephyr Twister + pytest | Mixed | ~7 | Partial |
| mpio | Custom x86 | Host-side x86 | Multiple dirs | YES (PR gate) |
| MPRAS-Applets | Custom C | Firmware-level | 1 | No |
| MPRAS-Kernel | Custom C | Firmware-level | 5 | Via firmware build |
| nht-firmware | None | - | 0 | - |
| pmfw-firmware | Custom Python + Lua | Simulation | ~3 | No |
| sriov-dr | None | - | 0 | - |
| VBL-TEE-Drv | CppUTest (shared w/dcgpu-esid) | Host-side x86 | Shared | YES (PR gate) |
| cp-mi400 | None | - | 0 | - |
| sw-security-tools | None | - | 0 | - |

---

## Gap Analysis: What Each Repo Needs

### Tier 1: Complete CI (build + coverity + lint + simnow + unit tests + nightly)
- **dcgpu-esid** -- Closest to complete. Needs: MI430 UT, AI code review
- **art-security** -- Strong. Needs: host-side unit tests
- **amd-tee3_0** -- Strong. Needs: host-side unit tests
- **asp-fmc** -- Strong SimNow/build coverage. Needs: any unit tests

### Tier 2: Good CI but missing elements
- **mpifoe-fw** -- Needs: Twister tests integrated into PR gate
- **mpio** -- Needs: nightly workflow, AI code review
- **MPRAS-Kernel** -- Needs: nightly workflow, host-side unit tests
- **nht-firmware** -- Needs: unit tests, AI code review
- **VBL-TEE-Drv** -- Needs: nightly, more SimNow platforms
- **sriov-dr** -- Needs: SimNow, unit tests

### Tier 3: Minimal CI
- **pmfw-firmware** -- Needs: lint in PR, SimNow in PR, test integration
- **MPRAS-Applets** -- Needs: SimNow, more unit tests, nightly
- **amd-node-check** -- Needs: pytest in PR gate (currently nightly only)
- **mi300x_ubb_soteria_fw** -- Needs: Coverity, lint, SimNow, pytest in CI

### Tier 4: No CI
- **cp-mi400** -- Needs: entire CI pipeline
- **sw-security-tools** -- Needs: entire CI pipeline

---

## Recommendations for Merlin Integration

1. **Standardize unit test framework:** CppUTest (used by dcgpu-esid/VBL-TEE-Drv) is the most mature. Recommend as standard for C firmware repos. pytest for Python repos.

2. **Mandate unit tests in PR gate:** Only dcgpu-esid, mpio, and VBL-TEE-Drv run unit tests in PR. All repos should have host-side unit tests blocking merge.

3. **Standardize SimNow YAML schema:** Already consistent across repos. The `incremental: true/false` flag pattern should be documented as the standard.

4. **Add nightly workflows to repos missing them:** mpio, MPRAS-Kernel, MPRAS-Applets, VBL-TEE-Drv, pmfw-firmware all lack nightly regression.

5. **Onboard cp-mi400 and sw-security-tools:** These repos have zero CI infrastructure and should be prioritized for basic pipeline setup.

6. **Integrate amd-node-check pytest into PR gate:** The ~85 pytest files should run on every PR, not just nightly.

7. **Expand AI code review:** Only 3 repos use `pr-ai-codereview.yml`. Should be enabled across all repos.

8. **Merlin test schema should accommodate:**
   - CppUTest (x86 host)
   - Zephyr Twister (native_sim)
   - pytest
   - Custom C firmware tests (via SimNow)
   - SimNow boot tests (postcode pass/fail)
   - Hardware smoke (Jenkins-triggered)
   - DCAuto (comment-triggered)
