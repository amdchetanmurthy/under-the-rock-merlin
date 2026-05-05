# Merlin: Existing Test Inventory Across Firmware Repos

**Source:** Actual `.github/workflows/`, test directories, and test files in 16 checked-out repos
**Date:** May 5, 2026

---

## 1. Summary: What Exists Today

| Component | Workflows | PR Gate | Nightly | SimNow | DCAuto HW | Unit Tests | Lint/Coverity |
|-----------|-----------|---------|---------|--------|-----------|------------|---------------|
| amd-tee3_0 | 15 | tee-pr.yml, tee-pr-presubmit.yml | tee-nightly.yml, tee-nightly-simnow.yml | Yes (nightly) | Yes (DCAuto presubmit `[TRIGGER_SMOKE]`) | ta_unit_test/ | Yes (Coverity) |
| art-security | 11 | artsec-pr.yml | artsec-nightly.yml | Via aspfmc-simnow | Yes (artsec-pr-dcauto.yml) | common/test/ (13 test suites) | Yes (Coverity) |
| asp-fmc | 9 | aspfmc-pr.yml, aspfmc-pr-presub.yml | aspfmc-nightly.yml | aspfmc-simnow.yml (20 MI450 configs!) | Yes (DCAuto `[TRIGGER_SMOKE]`) | No (build-only) | No |
| caliptra-sw | 19 | build-test.yml | nightly-verilator.yml, nightly-fuzzing.yml | No (FPGA/verilator) | No | Extensive Rust tests | Yes (code-coverage.yml) |
| dcgpu-esid | 12 | dcgpu-esid-pr.yml | dcgpu-esid-nightly.yml | patch-simnow.yml | Yes (dcgpu-esid-pr-dcauto.yml) | CppUTest (dcgpu/Test/) | Yes (Coverity, lint) |
| mpifoe-fw | 7 | mpifoe-pr.yml | mpifoe-nightly.yml | No (but bringup.yml) | No | ci/unit_tests/, tests/ifoe_ras | Yes (Coverity, lint) |
| mpio | 5 | pr.yml | No | No | No | tests/ (shmem, mock_shmem, unit_tests, CppUTest) | No |
| MPRAS-Applets | 4 | mpras_applets-pr.yml | No | No | No | unit_test_applet/ | No |
| MPRAS-Kernel | 3 | mpras_kernel-pr.yml | No | No | No | app/test/ (5 test files) | No |
| nht-firmware | 6 | mpnht-pr.yml | mpnht-nightly.yml | No | No | No | No |
| pmfw-firmware | 6 | pmfw-pr.yml | No | No | Yes (Verix via DCAuto) | firmware/main/test/ | No |
| sriov-dr | 5 | sriov-dr-pr.yml | sriov-dr-nightly.yml | No | No | No | No |
| VBL-TEE-Drv | 4 | vbl-dr-pr.yml | No | No | No | Simulate/Testcase/ | No |
| cp-mi400 | 0 | No | No | No | No | gcapi_test, mes_api_test (6 test dirs) | No |
| sw-security-tools | 0 | No | No | No | No | google-test/, test_sign/ | No |
| pytorch | 122 | pull.yml | nightly.yml | No | No | Extensive (test/) | Yes (lint.yml) |

---

## 2. Test Tiers (Actual Workflow Patterns)

### 2.1 PR Gate (Pre-Submit)

**Pattern:** Triggered on `pull_request` to main/staging branches. Most repos use `PFO/ivv-workflows` reusable workflows.

| Repo | Workflow | What It Does | Gate Type |
|------|----------|-------------|-----------|
| asp-fmc | aspfmc-pr-presub.yml | **DCAuto hardware test** triggered by `[TRIGGER_SMOKE]` comment | Comment-triggered, not auto |
| amd-tee3 | tee-pr-presubmit.yml | **DCAuto hardware test** triggered by `[TRIGGER_SMOKE]` comment | Comment-triggered, not auto |
| amd-tee3 | tee-pr.yml | Build verification | Auto on PR open/sync |
| art-security | artsec-pr.yml | Coverity incremental + build | Auto on PR open/sync |
| art-security | artsec-pr-dcauto.yml | **DCAuto hardware test** | Comment-triggered |
| dcgpu-esid | dcgpu-esid-pr.yml | Lint + Coverity incremental + build (SOC=MI450) | Auto on PR open/sync |
| dcgpu-esid | dcgpu-esid-pr-dcauto.yml | **DCAuto hardware test** | Likely comment-triggered |
| mpifoe-fw | mpifoe-pr.yml | Lint + Coverity + **AI Code Review** | Auto on PR open/sync |
| mpio | pr.yml | Build verification | Auto on PR open/sync |
| MPRAS-Applets | mpras_applets-pr.yml | Build verification | Auto on PR open/sync |
| MPRAS-Kernel | mpras_kernel-pr.yml | Build verification | Auto on PR open/sync |
| nht-firmware | mpnht-pr.yml | Build verification | Auto on PR open/sync |
| pmfw-firmware | pmfw-pr.yml | Build verification | Auto on PR open/sync |
| sriov-dr | sriov-dr-pr.yml | Build verification | Auto on PR open/sync |
| VBL-TEE-Drv | vbl-dr-pr.yml | Build verification | Auto on PR open/sync |

**Key finding:** Most PR gates are **build-only**. DCAuto hardware tests exist but are **comment-triggered** (`[TRIGGER_SMOKE]`), not automatic. Only mpifoe has **AI Code Review** integrated.

### 2.2 Smoke (Post-Merge)

**Pattern:** Triggered on push to main branch. Builds + uploads artifacts.

| Repo | Workflow | What It Does |
|------|----------|-------------|
| pmfw-firmware | pmfw-smoke.yml | Build MI450 + MI430, then submit **Verix** via DCAuto |
| MPRAS-Applets | mpras_applets-smoke.yml | Build + sign + upload to Artifactory |
| amd-tee3 | tee-smoke.yml | Reusable: build + sign + optional DCAuto test |

### 2.3 Nightly

**Pattern:** Scheduled via cron, builds all ASIC variants, signs, uploads.

| Repo | Workflow | Schedule | ASICs | What It Does |
|------|----------|----------|-------|-------------|
| amd-tee3 | tee-nightly.yml | Daily 11AM CST | MI350, MI300A/C/X, MI350P | Signed build for all ASICs |
| amd-tee3 | tee-nightly-simnow.yml | ? | MI350 and before | Build + SimNow validation |
| art-security | artsec-nightly.yml | ? | Multiple ASICs | Signed build |
| asp-fmc | aspfmc-nightly.yml | ? | Multiple ASICs | Signed build |
| dcgpu-esid | dcgpu-esid-nightly.yml | ? | MI450 | Build + unit tests |
| mpifoe-fw | mpifoe-nightly.yml | ? | MI450 | Build |
| nht-firmware | mpnht-nightly.yml | ? | MI450 | Build |
| sriov-dr | sriov-dr-nightly.yml | ? | MI450 | Build |

### 2.4 SimNow Testing

**Pattern:** Dedicated SimNow workflows that build IFWI, assemble image, boot in SimNow.

| Repo | Workflow | Configs | Trigger |
|------|----------|---------|---------|
| asp-fmc | aspfmc-simnow.yml | **20 MI450 configurations** (from mi450.yaml) | Manual (workflow_dispatch) |
| dcgpu-esid | patch-simnow.yml | Configurable (branch, SimNow version, IFWI, FW patches) | Manual |
| amd-tee3 | tee-nightly-simnow.yml | MI350 and before | Scheduled |

---

## 3. asp-fmc SimNow Configuration (Most Mature)

The `firmware/asp-fmc/.github/simnow/mi450.yaml` is the **most comprehensive SimNow test configuration** — 20 test configurations split between pre-commit and nightly:

### Pre-Commit SimNow Configs (4 configs, `incremental: true`)

| Config | BSD | Mode | Timeout |
|--------|-----|------|---------|
| MI450 0P1G M112 Unsecure | aransas_mi450_1mid1aid2xcd.bsd | Non-secure | 600s |
| MI450 0P1G M228 Unsecure | aransas_mi450_2mid2aid8xcd.bsd | Non-secure | 800s |
| MI450 0P1G M228 Secure | aransas_mi450_2mid2aid8xcd.bsd | Secure (script-modify) | 800s |
| MI450 1P1G M222 SKT7 Unsecure | aransas_1P1G_W22_M222_skt7.bsd | Non-secure + AGESA | 2000s |

### Nightly SimNow Configs (16 additional configs, `incremental: false`)

Covers: M112 secure, M228 variants, M222 SKT4/SKT7 secure/unsecure, Force Apply, RAS MBAT, 1P2G SKT67 variants.

### Key SimNow Parameters from mi450.yaml

```yaml
simnow:
  bios_source: "Artifactory"
  bios_extension: ".sbin"
  fatal: true
  simnow_date: "latest"
  postcode: "0X800F0000"          # ← This is the PASS marker
  suppress_summary: true
  output_json: true
```

**`postcode: "0X800F0000"`** — this is the `MPASP_FW_STATUS` value that means "PSP boot complete, all stages passed". The SimNow harness checks for this postcode to determine pass/fail.

**`script-modify`** — mechanism to transform a base script between secure/non-secure by replacing fuse values:
```
ART_LC_STATE_MFG1 0<->ART_LC_STATE_MFG1 7
F42584...→25ADC6...  (IKEK swap)
```

---

## 4. Unit Test Frameworks by Component

| Component | Framework | Test Files | What's Tested |
|-----------|-----------|------------|---------------|
| mpio | **CppUTest** (x86) | shmem/*_tests.cpp, mock_shmem/*_tests.cpp | PCIe link training, XGMI, UCIe SSBDCI, IFoE, bootflow |
| art-security | **Custom C** | common/test/*.c (13 suites) | Caliptra, DPE, fuses, HSP, KeyDB, RAP, RSMU, SPDM, startup, WAFL |
| dcgpu-esid | **CppUTest** | dcgpu/Test/CppUTest/ | eSID validation |
| mpifoe-fw | **Zephyr Twister + pytest** | tests/ifoe_ras/testcase.yaml, scripts/regressions/ | RAS, TLM, hello_world, regressions |
| MPRAS-Kernel | **C tests** | app/test/dram_test.c, poison_test.c, etc. | DRAM, messaging, poison, remote die SMN |
| MPRAS-Applets | **C tests** | unit_test_applet/src/pcie_scalable_test.c | PCIe scalable testing |
| caliptra-sw | **Rust (cargo test)** | Extensive across crates | Full Caliptra stack (verilator, FPGA, fuzzing) |
| cp-mi400 | **Custom** | gcapi_test, mes_api_test (6 dirs) | GC API, MES API |
| sw-security-tools | **Google Test + Python** | google-test/, test_sign/test_sign.py | Signing, SPL table gen |
| amd-tee3 | **Custom** | amd_tee_test/test_suites/ | TEE test suites |

---

## 5. Reusable IVV Workflows (Shared Infrastructure)

Most repos delegate to `PFO/ivv-workflows` reusable workflows:

| Reusable Workflow | Used By | Purpose |
|-------------------|---------|---------|
| `lint-cpp.yml` | dcgpu-esid, mpifoe-fw | C/C++ linting |
| `pr-incremental-coverity-builder.yml` | dcgpu-esid, mpifoe-fw, art-security | Coverity static analysis on PR diffs |
| `dcauto-ctl.yml` | amd-tee3 presubmit | Query DCAuto Common Test Library |
| `pr-ai-codereview.yml` | mpifoe-fw | AI-powered code review (uses LLM_GATEWAY_KEY) |
| `git-info.yml` (from dcauto-pre-sub) | asp-fmc presubmit | Extract PR info for DCAuto |

### DCAuto Integration Pattern

DCAuto is the hardware test execution system. The pattern is:
1. PR author comments `[TRIGGER_SMOKE]` on the PR
2. Workflow fires, builds firmware, uploads to Artifactory
3. DCAuto flashes firmware on reserved hardware
4. DCAuto runs smoke tests (boot, enumeration, basic validation)
5. Results posted back to PR

**This is NOT automatic** — it requires a human to comment `[TRIGGER_SMOKE]`.

---

## 6. Runner Labels Used

| Label | Used By | Environment |
|-------|---------|-------------|
| `arc-base` | Most builds | Basic IVV runner with NFS mounts |
| `arc-coverity` | Coverity builds | Runner with Coverity tools + NFS |
| `arc-lite` | Lightweight tasks | Minimal runner |
| `arc-oneclone` | Clone caching | Dedicated clone cache runner |
| `coverity-xtensa` | mpifoe Coverity | Runner with Xtensa + Coverity |
| `[ivv, arc-base]` | Nightly builds | IVV-labeled runners |
| `[ivv, arc-coverity]` | TEE nightly | IVV with Coverity |

---

## 7. What Merlin Can Leverage

### 7.1 Immediately Usable

1. **asp-fmc SimNow configs** — 20 pre-defined MI450 test configurations in YAML with BSD paths, scripts, timeouts, and postcode pass criteria
2. **DCAuto integration** — existing `dcauto-pre-sub` actions for hardware smoke tests
3. **IVV reusable workflows** — lint, Coverity, AI code review already packaged
4. **CppUTest suites** — MPIO and dcgpu-esid have x86-runnable unit tests
5. **Zephyr Twister** — MPIFoE test framework with testcase.yaml definitions
6. **fw-sign** — signing tool from Artifactory PyPI, integrated into smoke/nightly workflows

### 7.2 Gaps to Fill

1. **No automatic SimNow on PR** — SimNow tests are manual dispatch or nightly, not PR-triggered
2. **No unified test result schema** — each repo reports differently
3. **No LKG concept** — nightly builds don't promote to LKG
4. **Comment-triggered hardware tests** — `[TRIGGER_SMOKE]` is manual; need automatic gating
5. **No cross-component testing** — each repo tests in isolation; no assembled IFWI validation
6. **Inconsistent coverage** — mpio has unit tests, pmfw has none; some repos have Coverity, others don't

### 7.3 Pattern for Merlin Integration

The asp-fmc `mi450.yaml` SimNow config is the **blueprint for Merlin's unified test schema**. It already has:
- Multiple BSD/model configurations per product
- Secure vs non-secure mode switching via `script-modify`
- Timeout management per configuration
- Postcode-based pass/fail (`0X800F0000`)
- Artifact source management (Artifactory paths)
- Pre-commit vs nightly config separation (`incremental: true/false`)

Merlin should extend this YAML pattern to all components, adding:
- Unit test definitions (CppUTest, Zephyr Twister, Rust)
- Cross-component IFWI assembly test
- Structured result reporting (JUnit XML)
- Automatic PR triggering (not comment-based)
