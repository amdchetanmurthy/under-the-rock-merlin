# CI/CD Gating & SimNow Pre-Submit Design — Detailed

**Date:** May 5, 2026
**Sources:** CMakeLists.txt (2414 lines), docs/current_draft_plan.md (v1.2), ROADMAP.md, docs/host-prerequisites.md, AGENTS.md

---

## 1. What Actually Exists Today

### 1.1 IVV Nightly Orchestrator (Already Running)

The existing CI reference is `PFO/ivv-mi450-nightly/.github/workflows/patch-run-simnow.yml`. It dispatches reusable workflows per component:

| IVV Job | Reusable Workflow | Component |
|---------|-------------------|-----------|
| mi450-fmc-build | PFO/asp-fmc/.github/workflows/aspfmc-build-sign.yml | fw-asp-fmc |
| mi450-mpio-build | PFO/mpio/.../mpio-build-sign.yml | fw-mpio |
| mi450-mpifoe-build | PFO/mpifoe-fw/.../mpifoe-build-sign.yml | fw-mpifoe |
| mi450-pmfw-build | PFO/pmfw-firmware/.../pmfw-build-sign.yml | fw-pmfw |
| mi450-mpnht-build | PFO/nht-firmware/.../mpnht-build-sign.yml | fw-mpnht |
| mi450-mpras-build | PFO/MPRAS-Kernel/.../mpras-build-sign.yml | fw-mpras-kernel |
| mi450-tos-esid-build | github-remote-trigger (amd-tee3.0, dcgpu-esid) | fw-amd-tee3, fw-dcgpu-esid |
| MPRAS Applets | PFO/MPRAS-Applets/.../mpras_applets-build-sign.yml | fw-mpras-applets |

*Source: CMakeLists.txt lines 1-18*

### 1.2 IVV Runner Environment (IVV Containers)

Self-hosted GitHub runners with NFS mounts. The exact layout from `ivv-containers/ghe/runners/deployment/ghe-prod-pv.yml`:

| NFS Mount | Server | Local Path | Used By |
|-----------|--------|------------|---------|
| pfo-pandora64-nfs | lannister-noec.amd.com | /opt/pandora64 | Zephyr SDK, Java, Python |
| pfo-cbar-nfs | lannister-noec.amd.com | /opt/cbar | Xtensa, RISC-V SiFive |
| pfo-apps.k26.g212.64-nfs | lannister-noec.amd.com | /opt/cbar-old | Legacy tools |
| verif.release | murphy-02.amd.com | /proj/verif_release_ro | CBWA (PMFW) |

*Source: docs/host-prerequisites.md lines 41-50*

### 1.3 The Under-The-Rock Meta-Build (What It Does Now)

The CMake meta-build defines **35 fw-* targets** in the `firmware-all` umbrella. As of today:

**Built from source (16 targets):**
- fw-keydb, fw-asp-fmc, fw-mpio, fw-mpifoe, fw-art-security, fw-dcgpu-esid, fw-pcie-cld, fw-ucie, fw-pmfw*, fw-mpras-kernel*, fw-vbl-tee-drv*, fw-caliptra-sw*, fw-amd-tee3*, fw-mpras-applets*, fw-dmu*, fw-mpnht*, fw-unicrypt*

(*conditional: real build only if submodule is populated, else stub*)

**Stubs only (19 targets):**
fw-cp-mi400, fw-drivers-ip-fw, fw-drivers-ip-fw-pmfw, fw-drivers-ipconfig, fw-drivers-lsdma, fw-drivers-mes, fw-drivers-pplib, fw-drivers-psp, fw-drivers-sdma, fw-drivers-sdma-ip-fw, fw-drivers-vcn, fw-ip-fw, fw-pmfw-ec, fw-powerplay-utils, fw-ras-ta, fw-sriov-dr, fw-sw-security-tools, fw-udk2018

*Source: CMakeLists.txt lines 2229-2345*

### 1.4 Build Output Collection

Each fw-* target copies its artifacts to `${CMAKE_BINARY_DIR}/output/<component>/`:
- asp-fmc → `output/asp-fmc/` (copy_directory from `firmware/asp-fmc/asic/${UTTR_ASIC}/build`)
- dcgpu-esid → `output/dcgpu-esid/` (mirror from `Build/${SOC}/`)
- amd-tee3 → `output/amd-tee3/<VARIANT>/<driver>/`
- mpio → `output/mpio/` (from `firmware/mpio/mpio/mpio.pspbin`)

*Source: CMakeLists.txt lines 148-152, 735-763*

---

## 2. IFWI Image Structure (Real Data)

From the MI450 IFWI Layout (Confluence page 524949427, authored by Yan Xiong):

**Total SPIROM Size: 8MB (0x800000)**

| Region | Offset | Size | Contents |
|--------|--------|------|----------|
| EFS | 0x000000 | 0x54 | Embedded Firmware Structure (signature 0x55aa55aa) |
| L1 PSP Dir | 0x002000 | 0x30 | Points to ISHA/ISHB |
| RomStrap A/B | 0x010000 | 0x4000 | Hardware init settings (NBIO) |
| ISH A/B | 0x014000 | 0x2000 | Image Slot Headers (boot priority) |
| Signature Table | 0x01d000 | 0x80 | 7 signatures (EFS, L1, ISH, L2, RomStrap) |
| **FW Partition A** | **0x020000** | **0x3E0000** | L2 PSP Dir + 74 firmware entries |
| **FW Partition B** | **0x400000** | **0x3E0000** | Backup partition |
| PSP Boot Config | 0x7e0000 | 0x10000 | Boot configuration settings |

**L2 PSP Directory: 74 firmware entries** including all the fw-* target outputs:

| Index | FW Entry | PSP Type | Size | Built By |
|-------|----------|----------|------|----------|
| 13 | Caliptra | 0xa8 | 128K | fw-caliptra-sw |
| 15 | MPART_FMC | 0xab | 64K | fw-art-security |
| 16 | MPART_RUNTIME_FW | 0xac | 76K | fw-art-security |
| 17 | ART_LIBROM_OVERLAY | 0x9d | 4K | fw-unicrypt |
| 18 | MPASP_FMC | 0x1 | 128K | fw-asp-fmc |
| 19 | MPASP_TRUST_OS | 0x2 | 256K | fw-amd-tee3 |
| 20-26 | TEE Drivers | 0x1b-0x6c | 32-256K | fw-amd-tee3 |
| 27 | PSP_FW_SYSDRV | 0x28 | 256K | fw-amd-tee3 |
| 29 | PSPBL_KEY_DATABASE | 0x50 | 24K | fw-keydb |
| 35-43 | eSID TOC + eSID 0-7 | 0x157-15f | 24-96K | fw-dcgpu-esid |
| 44 | UMC_FW | 0x4f | 192K | Perforce (not in git) |
| 45 | MP1_PM_FW | 0x8 | 260K | fw-pmfw |
| 47 | DF_RIB | 0x76 | 640K | fw-rib (gitlab, no access) |
| 48-50 | SEC_POLICY L0/TOS/L1 | 0x24/45/101 | 64-200K | Perforce (not in git) |
| 53 | MPIO_FW | 0x5d | 256K | fw-mpio |
| 58 | UCIE_PHY_FW | 0x1ec | 81K | fw-ucie |
| 59 | IFOE_FW | 0x1f3 | 512K | fw-mpifoe |
| 66 | MP_NHT_Controller_FW | 0x1E0 | 25K | fw-mpnht |
| 70 | MPRAS_FW | 0x6B | 128K | fw-mpras-kernel |
| 72 | NBIO_UNIFIED_CLD_FW | 0xB5 | 16K | fw-pcie-cld |

*Source: memory-bank/14-ifwi-layout-mi450.md, Confluence page 524949427*

---

## 3. IFWI Assembly: How to Build a Complete Image

There are two approaches from the current_draft_plan.md:

### Option A: IFWI Builder API (Binary Assembly)

The existing IFWI Builder at `http://rocm-ci.amd.com/` takes pre-built firmware binaries and assembles them into a complete SPIROM image. This is what IVV currently uses.

**Inputs:** Individual firmware binaries (one per PSP directory entry)
**Output:** Complete 8MB SPIROM image with L1/L2 PSP directory, signatures, A/B partitions

**For the gate:** Build only the changed fw-* target from PR source → take LKG binaries for all other entries → submit to IFWI Builder API → get assembled image.

### Option B: Source Build (Under-The-Rock Super-Build)

Build everything from source using the CMake meta-build. The super-repo already collects outputs to `${UTTR_OUTPUT_DIR}/<component>/`.

**Gap:** No assembly script exists yet in the super-repo to combine `output/*/` into a SPIROM image. This would need to replicate what IFWI Builder does: L1/L2 PSP directory construction, signature table, A/B partitions, ISH headers.

**Current draft plan decision:** Tiger team PoC will determine which approach. Phase 0 evaluates both.

---

## 4. SimNow: What It Actually Tests

From the current_draft_plan.md Tier 1 Pre-Submit specification:

### 4.1 SimNow Tests for IFWI Commits

```yaml
# From current_draft_plan.md lines 841-867
Test_Against: LKG kernel + LKG ROCm
Products: All 6 active Instinct products (MI300X + future products TBD)

Tests:
  - IFWI assembly via IFWI Builder (component integration check)
  - FFM error injection smoke tests (via GHA self-hosted runner + AGFHC):
      - Inject controlled failure into changed component (VbiosMerge.exe)
      - Verify ASP FW detects and logs the error correctly
      - Validate CPER / Redfish / dmesg output matches expected fault codes
      - Verify recovery mechanism triggers where applicable
  - SimNow boot tests (simulated hardware, no physical system needed)
  - Hardware smoke tests (as many products as available):
      - Boot test (cold boot)
      - GPU enumeration
      - Driver load (amdgpu)
      - Basic ROCm (rocm-smi, clinfo)

Pass_Criteria:
  - FFM error injection: all injected errors correctly detected and logged
  - SimNow: boot validation passes
  - Hardware: >80% of available products must pass

Duration: ~30 minutes
```

### 4.2 SimNow Tests for Kernel Commits

```yaml
Test_Against: LKG IFWI + LKG ROCm
Tests:
  - Build verification (all product configs)
  - SimNow boot tests
  - Hardware smoke tests (boot, driver load, GPU enum, basic ROCm)
Pass_Criteria: SimNow boot passes; hardware >80%
Duration: ~30 minutes
```

### 4.3 Nightly Extended Tests (Tier 2, 2-4 Hours)

From current_draft_plan.md lines 1086-1121:

```
Nightly Test Coverage (2-4 hours per build):
├── Build verification
├── Boot tests (cold, warm, AC cycle)
├── GPU enumeration and detection
├── Driver load/unload cycles
├── ROCm Validation Suite (RVS):
│   ├── GPU properties validation
│   ├── PCIe qualification
│   ├── P2P bandwidth tests
│   ├── Memory error detection
│   └── GPU stress tests (GEMM workloads)
├── Reset testing (10× warm, 10× cold, 5× AC cycles)
├── Data Fabric / XGMI (link status, bandwidth, topology)
├── Performance subset (Transferbench, Mini-Hacc, MLPerf subset)
├── Power management (clocks, power limits, thermal)
└── Stability (2-4 hours continuous)
```

### 4.4 LKG Promotion Logic (From Plan)

```python
# From current_draft_plan.md lines 1127-1155
# 18 total nightlies:
#   6 x ifwi/main builds (one per product)
#   6 x firmware branches (one per product)  
#   6 x theRock e2e (one per product)
# Quorum: 15/18 (83%) must pass to promote LKG
```

---

## 5. Real fw-* Build Systems (Per Component)

Each component has a different build system. Here's what the CMakeLists.txt actually invokes:

| Target | Build System | Key Commands | Dependencies | Output |
|--------|-------------|--------------|--------------|--------|
| fw-asp-fmc | GNU Make | `make ASIC=mi450 PLATFORM=soc clean configure <default>` | Conan 1.x (riscv64-elf-toolsuite, amd-tee3.0-ddk) | `asic/mi450/build/` |
| fw-mpio | Zephyr/Xtensa via Make | `make -C mpio` → `build.sh` → Zephyr cmake → xt-objcopy | Xtensa XCC (RI-2019.3), LM_LICENSE_FILE, py_mpio venv | `mpio/mpio.pspbin` |
| fw-mpifoe | Zephyr/RISC-V via build.py | `build.py -s mi450-a0 -p silicon -b benchtop` | Zephyr SDK 0.16.8, /tools/pandora | build artifacts |
| fw-pmfw | tcsh + CBWA Make | tcsh → cbwa_init.csh → initdepot → make fw_compile_github_mi450 | tcsh, /proj/verif_release_ro, FAKEOS=lipc24_64, compat libs | pmfw binaries |
| fw-art-security | GNU Make + Cargo | `make ASIC=mi450 ... dep` → `make ... all` (uses cargo for lib-dpe) | Conan 1.x, Rust/cargo, CURL_TOKEN for RAP headers | FMC + runtime binaries |
| fw-dcgpu-esid | autoconf + Make | `./configure` (submodules, conan) → `make SOC=MI450` | Conan 1.x, git submodules (agesa, GmcFw, dcgpu) | `Build/MI450/` |
| fw-amd-tee3 | GNU Make | `make BUILD=MI450 VARIANT=MI455` via amd_tee_ddk | Conan 1.x (PSP tools), RISC-V SiFive 10.2.0 | per-driver binaries |
| fw-mpras-kernel | Zephyr/RISC-V Make | ZEPHYR_BASE + west build | SiFive toolchain or Zephyr SDK, zephyr submodule | MPRAS binary |
| fw-mpnht | build.sh + Make | `build.sh -d 1 -g` → `make BUILD_DEBUG=1 -j` | Xtensa XCC, LM_LICENSE_FILE, environment-modules | NHT binary |
| fw-keydb | Python | `key-db.py` | fw-sign (PSP signing tool from Artifactory PyPI) | Key database binaries |
| fw-pcie-cld | GNU Make | `make SOC=${UTTR_ASIC} FW_VERSION=...` | Build tools | CLD binary |
| fw-ucie | GNU Make | `make SOC=... FW_VERSION=...` | Build tools | UCIe binary |
| fw-vbl-tee-drv | GNU Make | make-based | PSP tools | VBL binary |
| fw-unicrypt | GNU Make | `make ASIC=mi400 MP=art` or `MP=asp` | romlib-headers, optional PSP_TOOLS_DIR | LibROM overlay |
| fw-caliptra-sw | Binary copy | Production binary, no compiling | None | Caliptra binary |
| fw-dmu | Xtensa Make | `make` with `xt-xcc` | Xtensa XCC (mp1_cpu_lx6), LM_LICENSE_FILE | DMCUB binary |
| fw-mpras-applets | Zephyr Make | west build | Zephyr SDK, fw-sign | Applet binary |

*Source: CMakeLists.txt throughout, AGENTS.md*

---

## 6. Real Change-to-Target Mapping

Based on the actual .gitmodules paths and CMakeLists.txt targets:

```python
# Derived from .gitmodules paths and CMakeLists.txt target definitions
SUBMODULE_TO_TARGET = {
    # Built from source (confirmed working)
    "firmware/asp-fmc":         "fw-asp-fmc",
    "firmware/pmfw-firmware":   "fw-pmfw",
    "firmware/mpio":            "fw-mpio",
    "firmware/mpifoe-fw":       "fw-mpifoe",
    "firmware/amd-tee3_0":      "fw-amd-tee3",
    "firmware/MPRAS-Kernel":    "fw-mpras-kernel",
    "firmware/MPRAS-Applets":   "fw-mpras-applets",
    "firmware/nht-firmware":    "fw-mpnht",
    "firmware/art-security":    "fw-art-security",
    "firmware/dcgpu-esid":      "fw-dcgpu-esid",
    "firmware/VBL-TEE-Drv":     "fw-vbl-tee-drv",
    "firmware/caliptra-sw":     "fw-caliptra-sw",
    "firmware/KeyDB":           "fw-keydb",
    "firmware/pcie-cld-fw":     "fw-pcie-cld",
    "firmware/ucie-fw":         "fw-ucie",
    "firmware/unicrypt":        "fw-unicrypt",
    "firmware/DMU":             "fw-dmu",
    "firmware/cp-mi400":        "fw-cp-mi400",

    # Stubs (submodule paths exist in .gitmodules but build not wired)
    "firmware/drivers-ipconfig":   "fw-drivers-ipconfig",    # stub
    "firmware/drivers-ip_fw":      "fw-drivers-ip-fw",       # stub
    # ... all 10 drivers-* variants → stubs
    "firmware/sw-security-tools":  "fw-sw-security-tools",   # stub
    "firmware/sriov-dr":           "fw-sriov-dr",            # stub
    "firmware/ras-ta":             "fw-ras-ta",              # stub
}

# Patch directories also map to targets
PATCH_TO_TARGET = {
    "patches/asp-fmc":       "fw-asp-fmc",
    "patches/dcgpu-esid":    "fw-dcgpu-esid",
    "patches/DMU":           "fw-dmu",
    "patches/mpifoe-fw":     "fw-mpifoe",
    "patches/mpio":          "fw-mpio",
    "patches/pmfw-firmware": "fw-pmfw",
    "patches/ucie-fw":       "fw-ucie",
}
```

*Source: .gitmodules (40 entries), CMakeLists.txt lines 2229-2264*

---

## 7. What the Gate Pipeline Must Do (Grounded in Real Infrastructure)

### 7.1 Pre-Submit Gate (Per PR)

Based on the existing IVV nightly structure and the plan's Tier 1 spec:

```
PR to firmware/<component>
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Job 1: detect-changes (ubuntu-latest, ~30s)                  │
│   - git diff origin/main..HEAD → map to fw-* target(s)       │
│   - Read lkg-manifest.yaml → get LKG SHAs for other layers   │
│   - Determine product matrix (always mi450 for now)           │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Job 2: build (self-hosted IVV runner with NFS mounts)        │
│   Runner labels: [self-hosted, undertherock-pool, mi450]     │
│   NFS: /opt/pandora64, /opt/cbar, /proj/verif_release_ro     │
│                                                               │
│   1. python3 build_tools/fetch_sources.py --skip-failed       │
│      (parallel submodule checkout with caching)               │
│                                                               │
│   2. source ${HOME}/venvs/uttr-conan/bin/activate             │
│      cmake --preset mi450                                     │
│      cmake --build build --target fw-<changed> -j$(nproc)     │
│                                                               │
│   3. Fetch LKG binaries for unchanged components              │
│      from Artifactory (artifactory://uttr-lkg/...)            │
│                                                               │
│   4. Assemble IFWI image:                                     │
│      Option A: IFWI Builder API (http://rocm-ci.amd.com)      │
│      Option B: scripts/assemble-ifwi.py (TBD)                 │
│                                                               │
│   Build time budget: 5-10 minutes                             │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Job 3: simnow-test (self-hosted runner with SimNow)          │
│                                                               │
│   1. Load assembled IFWI image into SimNow                    │
│   2. Run assertions:                                          │
│      L0: PSP boot (ISH boot priority, L2 dir parse)          │
│      L1: GPU enumeration (PCIe device 1002:7460)              │
│      L2: amdgpu driver load (dmesg check)                     │
│      L3: IP discovery (74 entries match L2 PSP dir)           │
│      L5: FW version strings match build manifest              │
│   3. Run FFM error injection if applicable:                   │
│      - VbiosMerge.exe controlled failure injection            │
│      - CPER / Redfish / dmesg fault code validation           │
│                                                               │
│   SimNow time budget: 5-8 minutes                             │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Job 4: hardware-test (optional, best-effort)                 │
│   Runner: [self-hosted, undertherock-pool, presubmit, mi450] │
│                                                               │
│   1. Reserve system via Conductor                             │
│   2. Flash IFWI via DCAuto                                    │
│   3. Boot test (cold boot)                                    │
│   4. GPU enumeration + driver load                            │
│   5. Basic ROCm (rocm-smi, clinfo)                            │
│   6. Release hardware                                         │
│                                                               │
│   Hardware time budget: 10-15 minutes                         │
│   Pass criteria: >80% of available products                   │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Job 5: aggregate-results                                     │
│   - SimNow MUST pass (mandatory gate)                         │
│   - Hardware is best-effort (advisory, not blocking initially)│
│   - Report via GitHub Checks API with JUnit XML               │
│   - Total: < 30 minutes                                      │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 What Gets Tested per Component (Real PSP Directory Mapping)

When a PR changes a specific component, the SimNow gate validates that the assembled IFWI image boots correctly with that component's binary in its PSP directory slot:

| Changed Component | PSP Entry Types Affected | SimNow Assertion Focus |
|-------------------|--------------------------|------------------------|
| fw-asp-fmc | 0x1 (MPASP_FMC, 128K) | PSP boot chain, FMC initialization |
| fw-amd-tee3 | 0x2, 0x1b-0x6c (TOS + 13 drivers, ~3MB total) | TEE boot sequence, all driver loads |
| fw-pmfw | 0x8, 0x9b, 0x9c, 0x01ea, 0x1051 (MP1/AID/XCD/IMU) | Power management init, clock gating |
| fw-mpio | 0x5d (256K) | PCIe/XGMI link training, topology |
| fw-mpifoe | 0x1f3 (512K, largest single entry) | IFoE link up, fabric discovery |
| fw-dcgpu-esid | 0x157-0x15f (TOC + 8 eSID entries, ~600K total) | eSID partition loading |
| fw-art-security | 0xab, 0xac (FMC 64K + Runtime 76K) | ART boot, secure execution |
| fw-keydb | 0x50, 0x51, 0xad (BL/OS/MPART key DBs, 52K) | Key validation, anti-rollback |
| fw-mpras-kernel | 0x6B (128K) | RAS initialization, MCA readout |
| fw-mpnht | 0x1E0 (25K) | NHT controller init |
| fw-pcie-cld | 0xB5 (16K) | PCIe CLD load |
| fw-ucie | 0x1ec (81K) | UCIe PHY training |
| fw-unicrypt | 0x9d, 0xae (ART/ASP LibROM, ~200K) | LibROM overlay application |
| fw-caliptra-sw | 0xa8 (128K) | Caliptra RoT initialization |

*Source: L2 PSP directory from MI450 IFWI layout (74 entries)*

---

## 8. Nightly LKG Promotion (Real Design from Plan)

### 8.1 Build Matrix: 18 Nightlies

From current_draft_plan.md:

**A) ifwi/main × 6 products = 6 builds**
- Latest IFWI (main) + Latest kernel + Latest ROCm

**B) firmware branches × 6 products = 6 builds**
- Branch IFWI (firmware-{product}.B) + Latest kernel + Latest ROCm
- Currently: firmware-mi300x.B; other products TBD

**C) theRock e2e × 6 products = 6 builds**
- Latest everything + ROCm frameworks (PyTorch, TensorFlow)
- Tests: HIP, ROCr, rocBLAS, rocFFT, MIOpen, RCCL, performance

### 8.2 Quorum: 15/18 (83%)

```python
# From current_draft_plan.md lines 1127-1155
total_nightlies = 18
quorum_threshold = 15  # 83%
# Even if one product completely fails, LKG can still promote
```

### 8.3 LKG Manifest (Real Schema from Plan)

```yaml
# lkg-manifest.yaml — updated nightly on promotion
date: "2026-05-04"
promoted_at: "2026-05-05T00:45:00Z"

nightly_results:
  total: 18
  passed: 17
  threshold: 15
  pass_rate: "94.4%"

ifwi:
  repo: amd/ifwi
  branch: main
  commit: abc1234567890abcdef1234567890abcdef12345
  artifact: artifactory://lkg/2026-05-04/ifwi-abc1234.bin

kernel:
  repo: amd/kernel
  branch: main
  commit: jkl0123456789abcdef1234567890abcdef012345
  artifact: artifactory://lkg/2026-05-04/kernel-jkl0123.deb

rocm:
  repo: ROCm/TheRock
  branch: main
  commit: mno3456789abcdef1234567890abcdef345678ab
  version: "7.2.0"
  artifact: artifactory://lkg/2026-05-04/rocm-mno3456.tar.gz
```

*Source: current_draft_plan.md lines 1296-1328*

### 8.4 Gardening on Failure

When quorum fails (< 15/18 pass), the orchestrator:
1. Creates a GitHub issue with label `gardening`, `nightly-failure`, `P0`
2. Assigns to oncall gardeners: `@ifwi-oncall`, `@kernel-oncall`, `@rocm-oncall`
3. Triggers auto-bisection
4. Gardener SLA: 4-hour revert or fix (business hours)

*Source: current_draft_plan.md lines 1352-1398*

---

## 9. What Does NOT Exist Yet (Gaps to Build)

Based on reading all source files, these are real gaps — not aspirational features:

| Gap | Current State | Needed For Gate | Effort |
|-----|--------------|-----------------|--------|
| **IFWI assembly script** | No script to combine fw-* outputs into SPIROM image | Essential — must either call IFWI Builder API or replicate L1/L2 PSP directory construction | Large |
| **SimNow integration in GHA** | SimNow exists (used by IVV) but no GHA workflow wiring | Pre-submit gate | Medium |
| **LKG binary cache** | No Artifactory structure for per-component LKG binaries | Pre-submit uses LKG for unchanged components | Medium |
| **Change detection script** | No `detect-changed-targets.py` exists | Gate trigger logic | Small |
| **lkg-manifest.yaml** | File format defined in plan, not yet created | Baseline for pre-submit + nightly | Small |
| **Component test definitions** | No `uttr-tests.yaml` per component | Unified test schema | Medium (per component) |
| **Result reporting** | No JUnit XML generation from SimNow results | PR feedback | Small |
| **Gardener rotation tooling** | Described in plan, no implementation | Nightly triage | Medium |
| **firmware-all on IVV runners** | Runs per-component via individual workflows, not unified | Full stack build | Medium |
| **Signing pipeline** | fw-sign exists on Artifactory PyPI; most fw-* skip signing locally (UTTR_MPIO_SKIP_SIGN=ON) | Production images | Large (security) |

---

## 10. Implementation Sequence

Each phase unblocks the next. Execute as fast as access and infrastructure allow.

| Phase | Scope | Unblocks |
|-------|-------|----------|
| **Phase 0: PoC** | Prove gate works: build → assemble → SimNow → PR result | Architecture decision (IFWI Builder API vs source) |
| **Phase 1: Foundation** | GHA pipeline, LKG manifest, SimNow for mi450 | Pre-submit gates on all PRs |
| **Phase 2: Nightly + LKG** | 18 builds, LKG promotion, CI-Lite | Daily validated baseline |
| **Phase 3: Hardware Gate** | Merge-blocking DCAuto/Conductor | Full shift-left |
| **Phase 4: Gardening** | Oncall rotation, revert automation | Trunk stays green |
| **Phase 5: Traceability** | Release manifests, matrix, LTS | Customer BKC reproducibility |

**Key ordering:** Nightly/LKG (Phase 2) comes BEFORE mandatory hardware pre-submit (Phase 3). The sequence is: nightly builds → daily LKG → CI-Lite → then hardware gates.

---

## 11. Tools Referenced in the Codebase

| Tool | URL/Location | Purpose |
|------|-------------|---------|
| IFWI Builder | http://rocm-ci.amd.com/ | Firmware image assembly |
| Jenkins Dashboard | http://rocm-ci.amd.com/ | Current CI (being replaced by GHA) |
| Analyze My Instincts | https://analyze-my-instinct.azr.dcgpu-infra.amd.com/ | IFWI analysis |
| MI450 RAP Compliance | https://rapctmi450.amd.com/ | RAP compliance checking |
| Artifactory | https://mkmartifactory.amd.com/ | Binary artifact storage |
| Conductor | conductor-cli (API TBD) | Hardware reservation |
| DCAuto | dcauto submit (API TBD) | Hardware test execution |
| SimNow | SimNow CLI (internal tool) | Hardware simulation |
| VbiosMerge.exe | Part of IFWI tooling | FFM error injection |
| fw-sign | Artifactory PyPI: api/pypi/FW-Sign-DEV-LOCAL/simple | PSP firmware signing |
| Conan 1.59 | ~/venvs/uttr-conan | Package management |

*Source: docs/host-prerequisites.md, CMakeLists.txt, current_draft_plan.md*

---

## 12. AI-Native Development Hooks (Real Touchpoints)

Based on the actual data structures in the codebase:

1. **uttr-firmware-all-kinds.txt** — CMake generates this at configure time with `built|stub` classification per target. An AI agent can read this to understand what's real vs placeholder.

2. **uttr-firmware-all-targets.txt** — Complete list of fw-* targets. Scripts already use this (firmware-all-with-report.sh).

3. **ROADMAP.md** — Structured `[build][stub]` checkboxes. An AI agent can parse this to track integration progress.

4. **lkg-manifest.yaml** (once created) — Machine-readable baseline. AI agent can answer "what's the known-good version of MPIO?" instantly.

5. **BKC Modules.xlsx** — Already parsed by .cursor/skills/under-the-rock-bkc (openpyxl). Contains build engineer contacts, source locations for all 174 modules.

6. **test-result.yaml** (once created) — Structured test results parseable by AI for triage.

7. **patches/<repo>/*.patch** — AI can generate patches for upstream repos following the existing pattern (unified diffs, never commit inside firmware/).

8. **Existing Cursor skills** — 4 skills already exist (.cursor/skills/). These can be ported to Claude Code skills for AI-native development.
