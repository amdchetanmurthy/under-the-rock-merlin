# Merlin: SimNow Service Design

**Purpose:** Design how SimNow is deployed, managed, versioned, and used as the gating engine for UnderTheRock PRs and nightly builds.

---

## 1. The Problem

SimNow today is a **desktop tool** — firmware engineers download it, install it on a Windows machine, manually configure scripts, and visually inspect log output. This doesn't scale to CI/CD gating where we need:

- **Automated execution** — no human in the loop
- **Deterministic configuration** — same inputs → same outputs every time
- **Version management** — track which SimNow version works with which IFWI
- **Concurrent execution** — multiple PRs tested simultaneously
- **Result parsing** — structured pass/fail from log analysis

---

## 2. SimNow Execution Model for CI

### 2.1 Headless Mode

SimNow supports headless execution via script mode:
```bash
simnow.exe -e <script_file>
```

The script drives everything — no GUI interaction needed. This is already used by the `patch-simnow.yml` CI workflow at `er.github.amd.com/PFO/dcgpu-esid`.

### 2.2 What the Script Controls

Based on the real MI450 scripts from `github.amd.com/PFO/simnow-scripts/tree/main/mi450`:

| Script Command | What It Does | Merlin Needs to Set |
|----------------|-------------|---------------------|
| `shell.open <bsd>` | Load SoC model | Fixed per product (e.g., `aransas_1P1G_W21_M112.bsd` for mi450 A+A) |
| `spirom:0.initfile <path>` | Load IFWI image | **Variable** — the assembled image from the PR build |
| `sbios_rom:0.initfile <path>` | Load SBIOS | Fixed — use LKG SBIOS from Artifactory |
| `NVMEdrive.SetImage <path>` | Load OS image | Fixed — BusyBox for gate testing |
| `regsmgr.AddForce <reg> <val>` | Set register overrides | Fixed per product (from simnow-scripts repo) |
| `*_fuse:*.set <fuse> <val>` | Set fuse overrides | Non-secure test mode for CI |
| `monitor.AddMonitor ...` | Watch FW status registers | Always enabled for result parsing |
| `shell.SetLogFile <path>` | Output log file | Dynamic — per-run unique path |
| `shell.go` | Start simulation | Always last |

### 2.3 Script Template for Merlin

```bash
# merlin-gate-mi450.script — auto-generated per gate run
# Template parameters substituted by merlin-test-runner.py:
#   {{BSD_PATH}}    — from SimNow install dir
#   {{IFWI_PATH}}   — assembled IFWI from PR build
#   {{SBIOS_PATH}}  — LKG SBIOS from Artifactory
#   {{OS_IMAGE}}    — BusyBox image
#   {{LOG_FILE}}    — unique per-run log path
#   {{ERR_LOG}}     — unique per-run error log path

shell.open {{BSD_PATH}}/aransas_1P1G_W21_M112.bsd

# Debug devices for log capture
shell.AddDevice "Simulation Util"
shell.AddDevice "Monitor Analyzer Extension"

# FW status monitors (critical for result parsing)
monitor.AddMonitor --address 0x034000d8 --size 4 --space 0.0.mpart --label MPART_FW_STATUS
monitor.AddMonitor --address 0x034000d8 --size 4 --space 0.0.mpasp --label MPASP_FW_STATUS
monitor.AddMonitor --address 0x03010d80 --size 4 --space 4.0.mpart --label MID_MPART_FW_STATUS
monitor.AddMonitor --address 0x03010d80 --size 4 --space 4.0.mpasp --label MID_MPASP_FW_STATUS

# Load firmware images
NVMEdrive.SetImage "{{OS_IMAGE}}"
sbios_rom:0.initfile {{SBIOS_PATH}}
spirom:0.initfile {{IFWI_PATH}}

# Venice CPU overrides (for A+A model)
regsmgr.AddForce 1Ah_WH_A0/MP_MPASPCRU/MPASP_C2PMSG_97/CONTENT 0x00C20E01
regsmgr.AddForce 1Ah_WH_A0/MP_MPASPCRU/MPASP_C2PMSG_96/CONTENT 0x04F00000
regsmgr.AddForce 1Ah_WH_A0/MP_MPASPCRU/MPASP_C2PMSG_98/CONTENT 0x00000E3F

# MI450 GPU overrides
regsmgr.AddForce MI450_A0_MID/MP_MPASPCRU/MPASP_C2PMSG_97/CONTENT 0x00000204
regsmgr.AddForce MI450_A0_MID/MP_MPASPCRU/MPASP_C2PMSG_98/CONTENT 0x00000800

# Non-secure test mode fuses
mpart_fuse:*.set ART_LC_STATE_MFG0 7
mpart_fuse:*.set ART_LC_STATE_MFG1 0
aid_fuse0:*.set CHIPLET_LC_STATE_MFG0 7
aid_fuse0:*.set CHIPLET_LC_STATE_MFG1 0
xcd_fuse:*.set CHIPLET_LC_STATE_MFG0 7
xcd_fuse:*.set CHIPLET_LC_STATE_MFG1 0

# IKEK for non-secure mode
mpart_fuse:*.Set ART_RKEK F42584C4E7AC4D83FACE35C9AA52B192C0FF53A978842CE01758F49FF37A39FC

# UMC memory config
aid_fuse0:*.set UMC0_UMC_PARTNUM_DENSITY 4
aid_fuse0:*.set UMC0_UMC_PARTNUM_MANUFACTURER_ID 1

# Reset and configure
shell.reset
mpasp_fuse:0.set ENABLE_MCM 0x0
dfblock:*.Flags DisTgtRsp 1

# Logging
shell.SetLogFileEnabled 1
shell.SetLogFile "{{LOG_FILE}}"
shell.SetErrorLogFileEnabled 1
shell.SetErrorLogFile "{{ERR_LOG}}"

# Execute simulation with timeout
shell.runtimeduration 300
shell.go
```

---

## 3. SimNow Version Management

### 3.1 Version Pinning Strategy

SimNow nightly builds can break compatibility with IFWI. We need a **pinned, validated version**.

```yaml
# merlin-config.yaml — checked into the super-repo
simnow:
  # Pinned SimNow version — only update after validation
  version: "20251209"
  artifact_url: "https://atlartifactory.amd.com/artifactory/sw-simnowbuilds-rel-local/internal/nightly/simnow-win64-internal-20251209-43f4aaf542.exe"
  sha256: "..."  # integrity check
  
  # Validated IFWI baseline for this SimNow version
  compatible_ifwi: "EMU035"
  
  # BSD models included in this version
  models:
    mi450_m112: "bsds/mi4/mi450/aransas_mi450_1mid1aid2xcd.bsd"
    mi450_aa: "bsds/mi4/mi450/aransas_1P1G_W21_M112.bsd"
    mi450_2g_ifoe: "bsds/mi4/mi450/aransas_mi450_2g_m112_ifoe.bsd"

  # Ancillary images
  sbios:
    artifact_url: "https://mkmartifactory.amd.com/artifactory/..."
    sha256: "..."
  busybox:
    path: "images/busybox.img"
```

### 3.2 SimNow Update Process

```
1. SimNow team publishes new nightly
     │
2. Merlin validation job triggered (manual or on-demand):
     ├── Download new SimNow version
     ├── Run against current LKG IFWI
     ├── Run full L0-L5 assertion suite
     ├── Compare results against previous version
     │
3. If all assertions pass with same IFWI:
     ├── Update merlin-config.yaml with new version
     ├── Commit + PR to super-repo
     └── All subsequent gate runs use the new version
     │
4. If assertions fail:
     ├── Log which assertions regressed
     ├── File issue against SimNow team
     └── Keep previous version pinned
```

### 3.3 SimNow Version Cache on Runners

```
/opt/merlin/simnow/
├── 20251209/                    # Pinned version (current)
│   ├── simnow.exe
│   ├── bsds/mi4/mi450/
│   └── ...
├── 20251003/                    # Previous version (fallback)
└── images/
    ├── busybox.img
    └── sbios/
        └── MAA5822A.FD
```

SimNow is pre-installed on IVV runners. The Merlin workflow downloads and caches the pinned version if not present.

---

## 4. SimNow Runner Infrastructure

### 4.1 Runner Requirements

| Requirement | Spec | Notes |
|-------------|------|-------|
| OS | Windows Server 2019+ or Ubuntu 22.04 | Windows primary (SimNow is Win-native); Linux supported |
| RAM | 64 GB minimum | SimNow MI450 A+A model needs ~32GB |
| CPU | Ryzen 7+ or equivalent | High single-thread performance for simulation speed |
| Disk | 20 GB free per SimNow instance | IFWI + SBIOS + OS images + logs |
| Network | Access to Artifactory | Download SimNow, IFWI, SBIOS images |
| Concurrency | 1 SimNow instance per 64GB RAM | A+A model is memory-hungry |

*Source: PFO page 1170008251 (Windows SimNow Setup)*

### 4.2 Runner Pool Design

```
┌─────────────────────────────────────────────────────────┐
│ MERLIN SIMNOW RUNNER POOL                                │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Runner 1      │  │ Runner 2      │  │ Runner 3      │  │
│  │ (pre-submit)  │  │ (pre-submit)  │  │ (nightly)     │  │
│  │               │  │               │  │               │  │
│  │ Label: simnow │  │ Label: simnow │  │ Label: simnow │  │
│  │        mi450  │  │        mi450  │  │        mi450  │  │
│  │  presubmit    │  │  presubmit    │  │  nightly      │  │
│  │               │  │               │  │               │  │
│  │ Win Server    │  │ Win Server    │  │ Win Server    │  │
│  │ 64GB RAM      │  │ 64GB RAM      │  │ 128GB RAM     │  │
│  │ SimNow cached │  │ SimNow cached │  │ SimNow cached │  │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
│  Pre-submit: 2 runners → 2 concurrent PRs                │
│  Nightly: 1 dedicated runner (longer tests)               │
│  Scale: Add runners as PR volume grows                    │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Runner Provisioning

```bash
# Bootstrap a Merlin SimNow runner
# 1. Install SimNow (pinned version)
curl -o simnow-installer.exe "${SIMNOW_ARTIFACT_URL}"
./simnow-installer.exe /S /D=C:\Merlin\SimNow

# 2. Cache ancillary images
mkdir C:\Merlin\images
curl -o C:\Merlin\images\busybox.img "${BUSYBOX_URL}"
curl -o C:\Merlin\images\sbios.FD "${SBIOS_URL}"

# 3. Pre-create log directories
mkdir C:\Merlin\runs

# 4. Register as GHA self-hosted runner
./config.cmd --url https://github.amd.com/PFO/under-the-rock \
  --token "${RUNNER_TOKEN}" \
  --labels "self-hosted,simnow,mi450,presubmit"
```

---

## 5. Result Parsing

### 5.1 Log Analysis for Pass/Fail

SimNow produces two log files per run. The **pass markers** from MI450 testing (page 524950171):

```python
# scripts/parse-simnow-results.py

PASS_MARKERS = {
    "L0_boot": {
        "markers": [
            "MPASP_FW_STATUS = 0x800f0000",
            "all ESIDs completed",
            "TOS steady state",
        ],
        "fail_markers": [
            "MPASP_FW_STATUS = 0x0",        # FMC didn't start
            "PSP boot failed",
            "ESID load error",
            "TOS: assertion failed",
        ],
    },
}

def parse_log(log_file):
    """Parse SimNow log for pass/fail markers."""
    with open(log_file, 'r') as f:
        content = f.read()

    results = {}
    for assertion, config in PASS_MARKERS.items():
        passed = all(m in content for m in config["markers"])
        failed = any(m in content for m in config.get("fail_markers", []))

        if failed:
            results[assertion] = "FAIL"
        elif passed:
            results[assertion] = "PASS"
        else:
            results[assertion] = "INCOMPLETE"

    return results
```

### 5.2 FW Status Register Meanings

The monitor watches `MPASP_FW_STATUS` and `MPART_FW_STATUS` at specific addresses. Values from MI450 testing:

| Register | Value | Meaning |
|----------|-------|---------|
| MPASP_FW_STATUS | 0x800f0000 | PSP boot complete, all stages passed |
| MPASP_FW_STATUS | 0x0 | FMC didn't start (FAIL) |
| MPART_FW_STATUS | various | ART boot progress |

### 5.3 Timeout Handling

```python
# SimNow has no built-in timeout command that works across versions.
# Use shell.runtimeduration for cycle-based timeout, or external process timeout.

# Option A: SimNow script
shell.runtimeduration 300  # sim cycles (not wall-clock seconds)

# Option B: External timeout (more reliable)
# On Windows:
# timeout /t 600 & taskkill /f /im simnow.exe
# On Linux (GHA):
# timeout 600 ./simnow -e script.script
```

---

## 6. SimNow Model Configurations for Merlin

### 6.1 Which Model for Which Test

| Gate Type | SimNow Model | BSD | Why |
|-----------|-------------|-----|-----|
| Pre-submit (default) | MI450 M112 | aransas_mi450_1mid1aid2xcd.bsd | Fastest to boot, covers single-die basics |
| Pre-submit (IFoE changes) | 2G M112 IFoE | aransas_mi450_2g_m112_ifoe.bsd | Tests IFoE fabric between 2 GPUs |
| Nightly (full system) | A+A (Venice + MI450) | aransas_1P1G_W21_M112.bsd | Full system: CPU boots, GPU enumerates on PCIe |
| Nightly (MPIFOE only) | FEAS | feas_mpifoe_mi450_mid.bsd | MPs-only model for MPIFOE side-loading |

### 6.2 Model Selection Logic

```python
def select_model(changed_targets, test_tier):
    """Select SimNow model based on what changed and test tier."""
    if test_tier == "pre_submit":
        if "fw-mpifoe" in changed_targets:
            return "2g_m112_ifoe"    # IFoE model
        return "m112"                 # default single-die

    elif test_tier == "nightly":
        return "aa_m112"              # full A+A system

    elif test_tier == "weekly":
        return "aa_m112"              # full system, longer runs
```

---

## 7. Secure vs Non-Secure Mode

### 7.1 Test Mode (Non-Secure) for CI

For CI gating, we use **non-secure / test mode** fuses:

```bash
# MFG0 = 7, MFG1 = 0  →  test mode (unsigned firmware accepted)
mpart_fuse:*.set ART_LC_STATE_MFG0 7
mpart_fuse:*.set ART_LC_STATE_MFG1 0

# IKEK for non-secure mode (specific key)
mpart_fuse:*.Set ART_RKEK F42584C4E7AC4D83FACE35C9AA52B192C0FF53A978842CE01758F49FF37A39FC
```

### 7.2 Production Mode (Secure) for Nightly/Weekly

```bash
# MFG0 = 7, MFG1 = 7  →  production mode (signed firmware required)
mpart_fuse:*.set ART_LC_STATE_MFG0 7
mpart_fuse:*.set ART_LC_STATE_MFG1 7

# Production IKEK (different key)
mpart_fuse:*.Set ART_RKEK 25ADC6EA41F1369578BB54B880757A961069ED1C2F94CF6220B3999A1550F924
```

**For Merlin pre-submit:** Always use non-secure mode (no signing required, faster).
**For nightly:** Use secure mode when testing signed IFWI images.

*Source: SIMNOW page 568776480 (MI4 SimNow Scripts — secure vs non-secure sections)*

---

## 8. Best Practices (From Confluence)

### 8.1 SimNow Usage

1. **Install to version-specific directories** — don't overwrite when switching versions (`C:\SimNow_Dec25\`, `C:\SimNow_Oct25\`)
2. **Pre-create log files** — SimNow fails silently if log directory/files don't exist
3. **Use BusyBox for gate tests** — faster boot than full OS images (RHEL, Windows)
4. **Don't rely on wall-clock timeouts** — `shell.runtimeduration` is cycle-based; use external process timeout for reliability
5. **Always enable error logging** — `shell.SetErrorLogFileEnabled 1` catches errors that the main log misses

*Source: PFO pages 1631902861, 878940075, 1375572171*

### 8.2 IFWI/SimNow Compatibility

6. **Track the compatibility matrix** — not every SimNow nightly works with every IFWI baseline
7. **Pin SimNow version in CI** — don't auto-update to latest nightly without validation
8. **Test SimNow updates separately** — validate new SimNow version against current LKG IFWI before deploying
9. **Keep BSD files versioned** — BSD changes can break boot even with the same IFWI

*Source: PFO page 987613634, VBIOS page 524950171*

### 8.3 CI-Specific

10. **Caliptra can be disabled** — `mpart_fuse:*.set ART_CALIPTRA_ENABLE 0` for faster CI boots
11. **Use FEAS model for component testing** — faster than full SoC model, sufficient for individual MP validation
12. **Monitor FW status registers** — `MPASP_FW_STATUS = 0x800f0000` is the primary pass marker
13. **Parse both log and error log** — error log contains assertions/crashes the main log may miss

*Source: SIMNOW page 568776480, VBIOS page 524950171*

---

## 9. Merlin SimNow Service Runbook

### 9.1 Adding a New Product

```
1. SimNow team provides new BSD file for the product
2. Add BSD path to merlin-config.yaml
3. Create product-specific script template (fuse overrides, register settings)
4. Validate with LKG IFWI for that product
5. Add product to GHA workflow matrix
```

### 9.2 Updating SimNow Version

```
1. Download candidate SimNow from Artifactory nightly
2. Run merlin-simnow-validate.py against LKG IFWI for all products
3. Compare assertion results against current pinned version
4. If pass: update merlin-config.yaml, PR to super-repo
5. If fail: file issue against SimNow team, keep current version
```

### 9.3 Debugging a Gate Failure

```
1. Download SimNow log and error log from GHA artifacts
2. Search for fail markers (MPASP_FW_STATUS != 0x800f0000, ESID errors, etc.)
3. Compare against last known good log (diff for new errors)
4. If SimNow-specific: check if SimNow version changed
5. If IFWI-specific: check PR's changed component against PSP entry mapping
6. Reproduce locally: download same SimNow version + IFWI + script, run on Windows
```

### 9.4 Runner Health Check

```bash
# Verify SimNow is functional on a runner
simnow.exe -e merlin-health-check.script
# Health check script: loads M112 BSD, boots LKG IFWI, checks MPASP_FW_STATUS
# Expected: completes in < 5 min, MPASP_FW_STATUS = 0x800f0000
```
