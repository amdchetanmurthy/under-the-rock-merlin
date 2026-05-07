# UnderTheRock Super-Repo — Architecture & Implementation Detail

**Source:** `/home/cmurthy/utr/under-the-rock-main/` (all non-firmware files)
**Date:** May 5, 2026

## What the Repo IS

The `under-the-rock` repo is a **CMake meta-build super-repository** that checks out ~40 firmware submodules under `firmware/` and orchestrates building them all from source with a single `cmake --build` command. It is **not** a replacement for CI — it provides a local developer experience that mirrors what IVV (internal verification infrastructure) runners do in production.

The repo name "Under The Rock" = what's **under** "The Rock" (theRock is AMD's ROCm unified build harness). UnderTheRock covers the firmware and kernel layers beneath ROCm.

## Repository Layout

```
under-the-rock-main/
├── CMakeLists.txt          # Meta-build: fw-* targets, UTTR_* options, firmware-all
├── CMakePresets.json        # Presets (e.g. mi450 → UTTR_ASIC=mi450)
├── .gitmodules              # 40 submodule definitions (SSH URLs)
├── README.md                # Build instructions, layout, Conan setup
├── ROADMAP.md               # IFWI component checklist with build/stub status
├── AGENTS.md                # AI agent instructions (Cursor/Claude)
├── requirements-mpio.txt    # Python deps for MPIO/Zephyr build steps
├── firmware/                # Submodule checkouts (~40 repos)
├── patches/                 # Unified diffs applied at build time (never commit inside firmware/)
│   ├── asp-fmc/
│   ├── dcgpu-esid/
│   ├── DMU/
│   ├── mpifoe-fw/
│   ├── mpio/
│   ├── pmfw-firmware/
│   └── ucie-fw/
├── scripts/                 # Build helpers
│   ├── firmware-all-with-report.sh   # Build all + summary report
│   ├── apply-firmware-patches.sh     # Patch application
│   ├── bootstrap-mpio-venv.sh        # MPIO Python venv
│   ├── check-firmware-stub-policy.sh # Stub regression check
│   └── ...
├── build_tools/
│   └── fetch_sources.py     # Smart parallel submodule checkout with caching
├── docs/
│   ├── host-prerequisites.md         # NFS mounts, tools, Conan, SSH (540 lines)
│   ├── artifactory-conan-and-host-layout.md  # Conan remote map
│   ├── current_draft_plan.md         # Full implementation plan (v1.2, very large)
│   ├── glossary.md                   # UTTR, IVV, PMFW, CBWA terms
│   └── integrate-firmware-package-skill.md   # How to add new fw-* targets
├── cmake/
│   └── Rust.cmake            # Rust/Cargo support for art-security lib-dpe
└── .cursor/
    ├── agents/verify-firmware-build.md
    └── skills/
        ├── integrate-firmware-package/SKILL.md
        ├── manage-github-pr/SKILL.md
        ├── under-the-rock-bkc/SKILL.md
        └── under-the-rock-status/SKILL.md
```

## How the Meta-Build Works

### Core Concept

One required variable: **`UTTR_ASIC`** (e.g. `mi450`). No default — you must specify it.

```bash
cmake -S . -B build -DUTTR_ASIC=mi450    # or: cmake --preset mi450
cmake --build build --target firmware-help  # List all targets and options
cmake --build build --target firmware-all -j$(nproc)  # Build everything
cmake --build build --target fw-asp-fmc     # Build one component
```

### Build Targets (fw-*)

Each firmware submodule gets a `fw-*` target. The CMakeLists.txt defines two kinds:

1. **Real targets (built)** — invoke the submodule's actual build system (make, build.py, cmake, etc.)
2. **Stub targets** — echo "populate submodule..." and succeed silently (for sparse checkouts)

Stub vs real is determined at configure time based on whether key files exist in the submodule checkout.

Currently **built** from source (per ROADMAP.md):
- fw-asp-fmc (0x0001 MPASP_FMC)
- fw-art-security (0x00ab/0x00ac MPART FMC + Runtime)
- fw-dcgpu-esid (0x0157-015c eSID TOC + eSID 0-7)
- fw-mpio (0x005d MPIO FW)
- fw-mpifoe (0x01f3 MPIFoE FW)
- fw-mpnht (0x01e0 MPNHT FW)
- fw-mpras-kernel (0x006b MPRAS FW)
- fw-pmfw (0x0008/009b/009c/01ea/1051 — PMFW MID/AID/XCD, IMU)
- fw-amd-tee3 (0x0002 + 13 TEE drivers)
- fw-vbl-tee-drv (0x01fb VBL Runtime Driver)
- fw-keydb (0x0050/00ad Key Databases)
- fw-pcie-cld (0x00b5 CLD Firmware)
- fw-ucie (0x01ec UCIe PHY FW)
- fw-unicrypt (0x009d/00ae LibROM Overlays)

Currently **stubs** (submodule exists but build not wired yet):
- fw-mpras-applets, fw-sriov-dr, fw-ras-ta, fw-sw-security-tools, fw-drivers-ipconfig, fw-caliptra-sw

### Patch System

Patches under `patches/<repo>/` are applied before build via `scripts/apply-firmware-patches.sh`. This avoids committing changes inside read-only firmware submodules. Examples:
- `patches/asp-fmc/` — Conan install extra settings pass-through
- `patches/dcgpu-esid/` — RHEL/yum/dnf package manager support
- `patches/pmfw-firmware/` — multiarch includes, Python3 compatibility
- `patches/mpio/` — build.sh Python venv + Xtensa path fixes

### fetch_sources.py — Smart Submodule Checkout

A sophisticated Python script (1200 lines) that replaces `git submodule update --init --recursive` with:
- **Parallel clones** (thread pool, default 4 workers)
- **Bare-clone cache** deduplication (same remote URL fetched once, reused as `--reference`)
- **Hardlinking** identical checkouts (same URL+SHA → disk savings)
- **Shared Git LFS store** (LFS objects not duplicated across submodules)
- **Incremental registry** (crash-safe progress)
- **`--skip-failed`** — graceful degradation for inaccessible repos
- **`--shallow-firmware-driver`** — depth-1 clone for large driver repos

### Host Prerequisites (NFS + /tool Layout)

The build system expects an **IVV runner-parity** host layout with corporate NFS mounts:

| Mount | Server | Path | Purpose |
|-------|--------|------|---------|
| `/opt/pandora64` | lannister-noec.amd.com | pandora snap | Java, Zephyr SDK, tools |
| `/opt/cbar` | lannister-noec.amd.com | cbar apps | Xtensa tools, RISC-V SiFive |
| `/opt/cbar-old` | lannister-noec.amd.com | older cbar snap | Legacy tool paths |
| `/proj/verif_release_ro` | murphy-02.amd.com | verif release | CBWA init scripts for PMFW |

Symlinks under `/tool/`:
- `/tool/pandora64` → `/opt/pandora64`
- `/tool/cbar/apps/XtensaTools` → from cbar mount
- `/tool/cbar/apps/RISC-V_SiFIVE` → from cbar mount
- `/tools/pandora` → `/tool/pandora64` (mpiFOE)
- `/proj/smartnic/xcb/ifoe/zephyr-sdk-0.16.8` → pandora Zephyr SDK

### Conan 1.x (Package Management)

Several firmware components use Conan 1.x (not 2) to fetch build dependencies from internal Artifactory:

**Conan remotes:**
- `swsec-markham-conan-local` — RISC-V toolsuite, PSP tools
- `swsec-conan-psp-internal` — AMD TEE3.0 DDK
- `fw-interface-conan-local` — optional

**Venv:** `${HOME}/venvs/uttr-conan` with `conan==1.59.0` on Python 3.10/3.11.

**Targets using Conan:** fw-asp-fmc, fw-art-security, fw-dcgpu-esid, fw-amd-tee3

### Zephyr SDK (Cross-compilation)

Multiple firmware targets use Zephyr RTOS. One SDK root is resolved at configure time:
1. `UTTR_ZEPHYR_SDK_INSTALL_DIR` (CMake variable)
2. `ZEPHYR_SDK_INSTALL_DIR` (env var)
3. `~/.cmake/packages/Zephyr-sdk` (from `setup.sh`)

Shared by: fw-mpifoe (RISC-V), fw-mpras-applets, fw-mpras-kernel, fw-mpnht

### PMFW Special Requirements

PMFW (fw-pmfw) is uniquely demanding:
- Requires **tcsh** shell (not bash)
- Sources **CBWA** init scripts from `/proj/verif_release_ro`
- Needs `FAKEOS=lipc24_64` on Linux 6.x (modern kernels)
- Requires compatibility symlinks for old Pandora grep/bc (`libpcre.so.1`, `libreadline.so.6`)
- Has nested submodules (variants/mi450/soc_headers, shared/*)

### Gerrit SSH Configuration

For the 4 Gerrit-hosted submodules, SSH config requires:
```
Host gerritgit
    HostName mkdcgit.amd.com
    PubkeyAcceptedAlgorithms +ssh-rsa
    User <ntid>
    Port 29418
```

### Access Requirements

Access to firmware remotes requires:
- **techprotect.amd.com** registration
- Org membership: PFO, AMD-Radeon-Driver, AMD-Firmware (github.amd.com)
- GitHub EMU (er.github.amd.com) for PFO repos
- Gerrit (gerrit-git.amd.com) for ras-ta, udk2018, pmfw-ec-firmware, ip_fw
- Tech project groups: amd_github, mi400, pfo.readonly, nbiofw.read_only, etc.

## AI Agent Integration (Cursor Skills)

The repo includes 4 Cursor AI skills:

1. **integrate-firmware-package** — Guided workflow for adding new fw-* targets to the meta-build. Includes mandatory build verification.
2. **manage-github-pr** — PR workflow for staging, pushing, and verification hooks.
3. **under-the-rock-bkc** — BKC gap analysis, metrics from xlsx, submodule sync preview.
4. **under-the-rock-status** — Weekly status reports (Milestone 0, RAG, narrative).

Plus 1 agent: **verify-firmware-build** — Automated build verification.

## ROADMAP Status

The ROADMAP.md tracks every IFWI component with `[build][stub]` checkboxes:
- **Built from source:** ~20 firmware components (checked first box)
- **Stub only:** ~6 components (checked second box)
- **Not yet sourced:** ~11 components (both unchecked — sources not identified or in Perforce)
- **Signing:** None done locally yet (all unchecked "Sign" lines)

## Key Design Decisions

1. **Patches over forks** — Changes to upstream firmware repos go through `patches/<repo>/` unified diffs, not forks. This keeps submodules read-only and diffs visible in the super-repo.
2. **Stubs succeed** — Missing submodules produce echo-only stubs, not failures. This lets developers build partial checkouts without errors. Stubs must never use `cmake -E false`.
3. **IVV parity** — The meta-build aims to reproduce exactly what CI runners do: same NFS mounts, same tool paths, same Conan packages. Deviations are documented.
4. **Single Zephyr SDK** — One SDK root shared by all Zephyr-based targets, not per-target installs.
5. **Conan 1.x only** — Despite Conan 2 being current, the project pins to 1.59.0 for IVV compatibility.
6. **UTTR_ASIC required** — No default ASIC. Forces explicit declaration of which GPU program you're building for.

## What Needs to Happen for AI-Native Development

The repo already has Cursor skills and an AI agent. To make this truly AI-native:

1. **Claude Code integration** — Port the 4 Cursor skills to Claude Code skills/plugins
2. **Automated submodule access** — The fetch_sources.py already handles `--skip-failed`; need credential management for HTTPS tokens
3. **Build environment containerization** — NFS mount requirements make cloud/remote builds hard; need Docker images with pre-populated tool paths
4. **BKC manifest automation** — The BKC skill parses xlsx; needs integration with LKG promotion pipeline
5. **Component build knowledge base** — Each fw-* target has unique build quirks (Conan, Zephyr, CBWA, Xtensa); encode these as skills
6. **Status reporting** — Weekly status skill exists; extend to automated triage, gardener alerts, regression detection
7. **Cross-repo PR coordination** — When changes span IFWI + kernel + ROCm, need coordinated PR workflow
