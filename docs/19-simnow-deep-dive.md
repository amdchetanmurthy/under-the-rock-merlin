# SimNow — Deep Dive: Architecture, Operations & CI Integration

**Sources:** 15+ Confluence pages across SIMNOW, PFO, VBIOS, CNS, ADVTECH, FWAQBV spaces
**Date:** May 5, 2026

---

## 1. What SimNow IS

SimNow is AMD's **pre-silicon platform simulation environment**. It simulates SoC hardware — CPUs, GPUs, memory controllers, PCIe, I/O — without physical silicon. Firmware teams use it to boot IFWI images, validate firmware flows, debug register interactions, and run test scripts before (or instead of) real hardware.

**Key properties:**
- Runs on **Windows** (primary) and **Linux**
- Distributed as self-extracting executables from Artifactory
- Uses **BSD files** (Board Simulation Descriptors) to define SoC models
- Controlled via **script files** (`.script`) that load models, set fuses, load firmware, and execute simulation
- Has a **command console** for interactive debugging
- Supports **Python scripting** for automated testing
- Updated via **nightly builds** from the SimNow team

**Source:** Confluence SIMNOW space (pages 568755984, 568777341, 568754702)

---

## 2. SimNow Architecture

### 2.1 Core Components

```
┌─────────────────────────────────────────────────────────┐
│ SIMNOW EXECUTABLE (simnow.exe / ./simnow)               │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ SoC Model     │  │ Device       │  │ Command      │   │
│  │ Engine        │  │ Models       │  │ Console      │   │
│  │               │  │              │  │              │   │
│  │ - CPU cores   │  │ - NVMe       │  │ - shell.*    │   │
│  │ - MPs (ASP,   │  │ - SATA       │  │ - regsmgr.*  │   │
│  │   ART, MPIO)  │  │ - PCIe       │  │ - ad.*       │   │
│  │ - Memory      │  │ - UART       │  │ - monitor.*  │   │
│  │ - DF          │  │ - ARM Debug  │  │              │   │
│  │ - Fuses       │  │ - GDB Server │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ APIs                                               │    │
│  │ - CmdApi (COM, Windows) — BIOS Test Suite, BV     │    │
│  │ - COSIM (C/C++) — Hybrid models, VBU team         │    │
│  │ - Device SDK (C/C++) — Custom device models       │    │
│  │ - Python Extension — Thin layer over console      │    │
│  │ - Python Embedding — Embedded Python in SimNow    │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         │                    │                   │
         ▼                    ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│ BSD Files     │  │ Firmware Images   │  │ OS Images    │
│ (SoC Models)  │  │ (IFWI .sbin,     │  │ (BusyBox,    │
│               │  │  SBIOS .FD)      │  │  RHEL, Win)  │
└──────────────┘  └──────────────────┘  └──────────────┘
```

*Source: SIMNOW pages 568754702, 568777341*

### 2.2 BSD Files (Board Simulation Descriptors)

BSDs define the SoC model configuration. For MI450:

| BSD File | Model | Configuration |
|----------|-------|---------------|
| `aransas_mi450_1mid1aid2xcd.bsd` | M112 | 1 MID, 1 AID, 2 XCD |
| `aransas_mi450_2g_m112_ifoe.bsd` | 2G_M112_IFoE | 2-GPU with IFoE fabric |
| `aransas_1P1G_W21_M112.bsd` | A+A (CPU+GPU) | Venice CPU + MI450 GPU, full system |
| `feas_mpifoe_mi450_mid.bsd` | FEAS (MPs only) | MPs only, no SoC side memory/NBIO/DF |

BSDs are **packaged inside the SimNow installer** under `bsds/mi4/mi450/`. New models are added with each SimNow release.

*Source: SIMNOW page 568776480 (MI4 SimNow Scripts)*

### 2.3 SimNow APIs

| API | Platform | Users | Language | Description |
|-----|----------|-------|----------|-------------|
| CmdApi | Windows | BIOS Test Suite, BIOSDbg, BV teams | COM (C++, Python, Perl, etc.) | Thin layer over SimNow command console. Loose/unstructured automation |
| COSIM | Windows + Linux | VBU Team | C/C++ | Hybrid modeling (real RTL + SimNow models) |
| Device SDK | Windows + Linux | Microsoft, HPE, Xilinx | C/C++ | Custom SimNow device model development |
| Python Extension | Windows + Linux | SimNow team (regression) | Python | Python scripts at `AMD-SW-Simnow/simnow/scripts/lib_shared/simnow` on GitHub |
| Python Embedding | Windows + Linux | FEAS environment | Python | Full Python embedded inside SimNow process |

*Source: SIMNOW page 568754702*

---

## 3. How to Run SimNow (MI450)

### 3.1 Artifacts Needed

| Artifact | Source | Example |
|----------|--------|---------|
| SimNow executable | Artifactory nightly | `atlartifactory.amd.com/artifactory/sw-simnowbuilds-rel-local/internal/nightly/simnow-win64-internal-20251209-43f4aaf542.exe` |
| IFWI image (.sbin) | Artifactory or build output | `MI450X_GENERIC_MI450_Baseline_EMU027_165974.sbin` |
| SBIOS image (.FD) | BVM (BIOS Vending Machine) | `VWH1380281N.FD` (Venice SBIOS) |
| OS image (BusyBox/RHEL/Win) | Network share or Artifactory | `busybox.img`, `RHEL83.img`, `Ubuntu20.img` |
| SimNow script (.script) | `github.amd.com/PFO/simnow-scripts/tree/main/mi450` | A+A script, M112 script |
| Log files (pre-created) | Local directory | `mi450_EMU027_W21_M112.log`, `*_err.log` |

*Sources: PFO pages 987613634, 1631902861, 1347025400*

### 3.2 Script Anatomy (Real MI450 A+A Non-Secure Script)

```bash
# 1. Load SoC model (BSD)
shell.open $BSDPATH/aransas_1P1G_W21_M112.bsd

# 2. Add debug devices
shell.AddDevice "Simulation Util"
shell.AddDevice "Debugger"
shell.AddDevice "Monitor Analyzer Extension"

# 3. Enable logging
cf:*.log 0xff
axiclient:*.loglevel 0xffffffff

# 4. Setup firmware status monitors
monitor.AddMonitor --address 0x034000d8 --size 4 --space 0.0.mpart --label IOD0_MPART_FW_STATUS
monitor.AddMonitor --address 0x034000d8 --size 4 --space 0.0.mpasp --label IOD0_MPASP_FW_STATUS
monitor.AddMonitor --address 0x03010d80 --size 4 --space 4.0.mpart --label MID_MPART_FW_STATUS
monitor.AddMonitor --address 0x03010d80 --size 4 --space 4.0.mpasp --label MID_MPASP_FW_STATUS

# 5. Load OS image
NVMEdrive.SetImage "<path>/busybox.img"

# 6. Load SBIOS
sbios_rom:0.initfile <path>/MAA5822A.FD

# 7. Load IFWI (this is the firmware image we're testing)
spirom:0.initfile <path>/MI450X_GENERIC_MI450_Baseline_EMU022_161397.sbin

# 8. Set Venice CPU register overrides
regsmgr.AddForce 1Ah_WH_A0/MP_MPASPCRU/MPASP_C2PMSG_97/CONTENT 0x00C20E01
regsmgr.AddForce 1Ah_WH_A0/MP_MPASPCRU/MPASP_C2PMSG_96/CONTENT 0x04F00000
regsmgr.AddForce 1Ah_WH_A0/MP_MPASPCRU/MPASP_C2PMSG_98/CONTENT 0x00000E3F

# 9. Set MI450 GPU register overrides
regsmgr.AddForce MI450_A0_MID/MP_MPASPCRU/MPASP_C2PMSG_97/CONTENT 0x00000204
regsmgr.AddForce MI450_A0_MID/MP_MPASPCRU/MPASP_C2PMSG_98/CONTENT 0x00000800

# 10. Set fuse overrides (non-secure / test mode)
mpart_fuse:*.set ART_LC_STATE_MFG0 7
mpart_fuse:*.set ART_LC_STATE_MFG1 0     # 0 = test mode, 7 = prod mode
aid_fuse0:*.set CHIPLET_LC_STATE_MFG0 7
aid_fuse0:*.set CHIPLET_LC_STATE_MFG1 0
xcd_fuse:*.set CHIPLET_LC_STATE_MFG0 7
xcd_fuse:*.set CHIPLET_LC_STATE_MFG1 0

# 11. Set IKEK for non-secure mode
mpart_fuse:*.Set ART_RKEK F42584C4E7AC4D83FACE35C9AA52B192C0FF53A978842CE01758F49FF37A39FC

# 12. UMC memory config
aid_fuse0:*.set UMC0_UMC_PARTNUM_DENSITY 4
aid_fuse0:*.set UMC0_UMC_PARTNUM_MANUFACTURER_ID 1

# 13. Reset and configure topology
shell.reset
mid_cf:0.write 0x5a08c 0x80010
mpasp_fuse:0.set ENABLE_MCM 0x0

# 14. Enable logging
shell.SetLogFileEnabled 1
shell.SetLogFile "mi450_EMU022_W21_M112.log"
shell.SetErrorLogFileEnabled 1
shell.SetErrorLogFile "mi450_EMU022_W21_M112_err.log"

# 15. Start simulation
dfblock:*.Flags DisTgtRsp 1
shell.go
```

*Source: SIMNOW page 568776480 (MI4 SimNow Scripts — A+A section)*

### 3.3 Boot Success Indicators

From the MI450 SimNow Testing page (524950171), a successful boot shows:

```
MPASP_FW_STATUS = 0x800f0000
All ESIDs completed
TOS steady state reached
```

These are the **pass markers** for the Merlin gate's L0 boot assertion.

### 3.4 Launch Command

```bash
# Windows
simnow.exe -e <path_to_script>.script

# Linux  
./simnow -e <path_to_script>.script
```

*Source: SIMNOW page 568777341, PFO page 1631902861*

---

## 4. SimNow Distribution & Versioning

### 4.1 Artifactory Locations

| Type | URL |
|------|-----|
| Nightly builds | `atlartifactory.amd.com/artifactory/sw-simnowbuilds-rel-local/internal/nightly/` |
| MI450 test builds | `atlartifactory.amd.com/artifactory/sw-simnowbuilds-rel-local/internal/test/mi450/` |
| External releases | `atlartifactory.amd.com/artifactory/sw-simnowbuilds-rel-local/external/` |
| Network share (legacy) | `\\atlcorpnetfs\BiosOnly\SimNow Builds\` |

### 4.2 Naming Convention

```
simnow-win64-internal-YYYYMMDD-<git-hash>.exe     # Nightly
simnow-win64-internal-MI450_LSC_DF_FIX-<hash>.exe  # Test/milestone build
simnow-win64-internal-mi450-lsb-test-YYYY-MM-DD-<hash>.exe  # LSB test
```

### 4.3 SimNow Update Cadence

- **Nightly builds** from the SimNow team, published to Artifactory
- **Milestone builds** at SoC milestones: LSC → LSDm → LSD.1 → LSF → BTO → MTO
- **Test builds** for specific issues (e.g., DF fix, RSMU patch)
- **BSD updates** when new SoC model configurations are needed
- **Fuse recipe updates** when hardware fuse definitions change

*Source: SIMNOW page 568778910 (MI4XX SimNow Releases), PFO page 987613634*

### 4.4 SimNow + IFWI Compatibility Matrix

From the PFO weekly configuration tracking page:

| Date | SimNow Build | IFWI Baseline | Script Model |
|------|-------------|---------------|--------------|
| 12/10/2025 | 20251209 | BRP-M112 EMU035 | M112, M222 |
| 10/15/2025 | 20251007 | EMU027 | A+A M112 Full |
| 10/03/2025 | 20251003 | EMU026 (First BTO) | A+A M112 Full |
| 09/24/2025 | 20250924 | EMU025 | A+A M112 Full |
| 08/24/2025 | 20250823 | EMU022 | A+A M112 Full |
| 07/24/2025 | 20250724 | EMU019/EMUE342 | A+A M111 Cutdown |

**Key observation:** SimNow and IFWI versions must be compatible. Not every SimNow nightly works with every IFWI. The configuration is tracked manually on Confluence.

*Source: PFO page 987613634*

---

## 5. SimNow CI/CD Integration (What Exists Today)

### 5.1 Existing CI Workflow

The `patch-simnow.yml` workflow at `er.github.amd.com/PFO/dcgpu-esid/actions/workflows/` is the most mature SimNow CI integration:

**Inputs:**
1. Branch selection for eSID
2. SimNow version (default: latest nightly, or specify `YYYYMMDD`)
3. IFWI image (default: latest from `mkmartifactory/artifactory/dgpu-spirom-fw/mi450/pre_release/ifwi/`)
4. Optional FW patches (paths to individual binary overrides)

**What it does:**
1. Downloads SimNow from Artifactory
2. Downloads IFWI image (or uses test IFWI)
3. Patches FW components if specified
4. Runs SimNow with MI450 scripts from `github.amd.com/PFO/simnow-scripts/tree/main/mi450`
5. Generates test report

*Source: VBIOS page 1347025400*

### 5.2 SimNow Scripts Repository

`github.amd.com/PFO/simnow-scripts` contains:
- `mi450/` — MI450-specific launch scripts
- Scripts for different model configurations (M112, M222, A+A, etc.)
- Both secure and non-secure variants

### 5.3 IVV Nightly SimNow Usage

From CMakeLists.txt comments, the IVV nightly orchestrator (`ivv-mi450-nightly/patch-run-simnow.yml`) runs SimNow after building firmware. The SimNow step validates that the assembled IFWI boots correctly.

---

## 6. PPR-to-SimNow Pipeline (AI Opportunities Report)

From the comprehensive AI research report (page 1424888583):

### 6.1 Process Stages

```
PPR (Register Specs)
    │
    ├── Fuses (soc_fusedoc headers)
    ├── Regspec headers (hal_regs_addr.h)
    ├── FSDL (FW Simulation Driver Layer)
    ├── RIB (Register Interface Block)
    ├── S3 Image (register save/restore)
    ├── BSD (Board Simulation Descriptor)
    └── Bc (Board Controller config)
         │
         ▼
SimNow Model Build + Refresh (~5 days after collateral delivery)
         │
         ▼
Firmware Validation (boot flow, feature testing, regression)
```

### 6.2 Identified Bottlenecks

| Bottleneck | Impact | Current State |
|-----------|--------|---------------|
| Collateral delivery delays | Cascading delays to SimNow model refresh | Each FW team delivers independently, no unified dashboard |
| Register header churn | Manual integration per milestone | regspec/fuse headers updated per component, per milestone |
| Register mismatches | Force signals hide real issues | SimNow, emulation, and real HW can diverge |
| Manual script maintenance | Days per feature to write test scripts | Each PMFW feature has dedicated Python scripts |
| Debug/log analysis | ~1 week per boot failure | Manual postcode walkthrough |
| Cross-program knowledge transfer | Repeated mistakes | Lessons learned not systematically applied |

### 6.3 AI Opportunities Identified

1. **Intelligent Log Analysis** — LLM analyzes SimNow boot logs, cross-references Jira issues
2. **Script Generation** — LLM generates SimNow Python test scripts from feature specs
3. **Register Delta Analysis** — LLM diffs PPR/regspec between steppings
4. **Collateral Readiness Tracking** — LLM-powered dashboard from Jira/Confluence
5. **IFWI Changelog Review** — LLM flags SimNow-relevant changes
6. **Cross-Program Lessons Learned** — LLM synthesizes checklists from historical pages

*Source: page 1424888583 (AI Opportunities for PPR-to-SimNow)*

---

## 7. SimNow Resource Locations

### 7.1 Confluence Pages

| Page | Space | Content |
|------|-------|---------|
| [SimNow User Guide & FAQ](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568755853) | SIMNOW | Canonical user documentation |
| [SimNow Quick Start Guide](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568777341) | SIMNOW | How to launch and debug |
| [SimNow APIs and Automation](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568754702) | SIMNOW | CmdApi, COSIM, Python, Device SDK |
| [MI4 SimNow Scripts](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568776480) | SIMNOW | MI450 launch scripts (FEAS, SoC, A+A) |
| [MI4XX SimNow Releases](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568778910) | SIMNOW | Release history, BC versions |
| [SimNow Developer Training](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568781228) | SIMNOW | Training materials, videos |
| [SimNow Program Management](https://amd.atlassian.net/wiki/spaces/SIMNOW/pages/568757144) | SIMNOW | Jira workflow, roles |
| [MI450 SimNow Testing](https://amd.atlassian.net/wiki/spaces/VBIOS/pages/524950171) | VBIOS | MI450 test matrix, pass/fail results |
| [SimNow for MI450](https://amd.atlassian.net/wiki/spaces/CNS/pages/556129049) | CNS | Tutorials, XCB examples |
| [Current SimNow/IFWI/SBIOS Config](https://amd.atlassian.net/wiki/spaces/PFO/pages/987613634) | PFO | Weekly config tracking |
| [MI450 IFWI Build & SimNow Boot Test](https://amd.atlassian.net/wiki/spaces/VBIOS/pages/1347025400) | VBIOS | CI workflow description |
| [Onboarding Exercise: SimNow](https://amd.atlassian.net/wiki/spaces/PFO/pages/1631902861) | PFO | Step-by-step new hire guide |
| [SimNow E2E Automation Tool](https://amd.atlassian.net/wiki/spaces/ADVTECH/pages/1624021654) | ADVTECH | End-to-end automation |
| [SIMNOW CI Extension](https://amd.atlassian.net/wiki/spaces/~rongli12/pages/1633475957) | Personal | CI extension plans |
| [SimNow Setup (FWAQBV)](https://amd.atlassian.net/wiki/spaces/FWAQBV/pages/1375572171) | FWAQBV | Generic setup guide |
| [Window SimNow Setup](https://amd.atlassian.net/wiki/spaces/PFO/pages/1170008251) | PFO | Windows setup with file transfer |

### 7.2 Repos

| Repo | Content |
|------|---------|
| `github.amd.com/PFO/simnow-scripts` | MI450 SimNow launch scripts |
| `github.com/AMD-SW-Simnow/simnow` | SimNow Python extension (`scripts/lib_shared/simnow/`) |

### 7.3 Distribution Lists

| DL | Purpose |
|----|---------|
| dl.mds1.simnow.announce@amd.com | User announcements (Medusa1 example) |
| Per-program DLs | Program-specific SimNow announcements |
