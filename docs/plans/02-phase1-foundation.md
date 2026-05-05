# Merlin Phase 1: Foundation

**Depends on:** Phase 0 PoC validated
**Goal:** All 16 built fw-* targets gated on PRs, LKG manifest operational, SimNow validation for mi450.

---

## Phase 1 Deliverables

1. **Change detection** — PR diff → fw-* target mapping → selective build
2. **Full component build** — all 16 built targets compile on IVV runners via GHA
3. **IFWI assembly pipeline** — production-quality image assembly (API or source)
4. **SimNow gate** — L0-L3 assertions for mi450
5. **LKG manifest** — daily-updated `lkg-manifest.yaml` (manual promotion initially)
6. **Artifact management** — per-component binary storage in Artifactory

---

## 1. Change Detection System

### 1.1 Script: `scripts/detect-changed-targets.py`

```python
#!/usr/bin/env python3
"""Map git diff paths to fw-* targets for selective building."""

import json
import os
import subprocess
import sys

# Authoritative mapping derived from .gitmodules + CMakeLists.txt
# See: CMakeLists.txt lines 2229-2264 for firmware-all target list
SUBMODULE_TO_TARGET = {
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
}

PATCH_TO_TARGET = {
    "patches/asp-fmc":       "fw-asp-fmc",
    "patches/dcgpu-esid":    "fw-dcgpu-esid",
    "patches/DMU":           "fw-dmu",
    "patches/mpifoe-fw":     "fw-mpifoe",
    "patches/mpio":          "fw-mpio",
    "patches/pmfw-firmware": "fw-pmfw",
    "patches/ucie-fw":       "fw-ucie",
    "patches/nht-firmware":  "fw-mpnht",
}

# Files that affect ALL targets
GLOBAL_PATHS = [
    "CMakeLists.txt",
    "cmake/",
    "scripts/apply-firmware-patches.sh",
    "requirements-mpio.txt",
]

def get_changed_files(base_ref="origin/main"):
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True, text=True
    )
    return result.stdout.strip().splitlines()

def detect_targets(changed_files):
    targets = set()
    rebuild_all = False

    for f in changed_files:
        # Check global paths
        for gp in GLOBAL_PATHS:
            if f == gp or f.startswith(gp):
                rebuild_all = True
                break

        # Check submodule paths
        for submodule, target in SUBMODULE_TO_TARGET.items():
            if f.startswith(submodule + "/"):
                targets.add(target)

        # Check patch paths
        for patch_dir, target in PATCH_TO_TARGET.items():
            if f.startswith(patch_dir + "/"):
                targets.add(target)

    if rebuild_all:
        targets = set(SUBMODULE_TO_TARGET.values())

    return sorted(targets)

def main():
    base_ref = os.environ.get("GITHUB_BASE_REF", "origin/main")
    changed = get_changed_files(base_ref)
    targets = detect_targets(changed)

    # GitHub Actions output
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"targets={json.dumps(targets)}\n")
            f.write(f"target_count={len(targets)}\n")
            f.write(f"products={json.dumps(['mi450'])}\n")

    print(f"Changed files: {len(changed)}")
    print(f"Affected targets: {targets}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 1.2 Products Matrix

Initially fixed to `mi450`. The preset already exists in CMakePresets.json:
```json
{"name": "mi450", "cacheVariables": {"UTTR_ASIC": "mi450"}}
```

Future: add `mi455` and other products as presets are defined.

---

## 2. Build Pipeline on IVV Runners

### 2.1 Runner Requirements

From `docs/host-prerequisites.md`, IVV runners need:

| Requirement | Path | Used By |
|-------------|------|---------|
| Pandora NFS | /opt/pandora64 → /tool/pandora64 | fw-mpifoe, fw-mpio (Java) |
| CBAR NFS | /opt/cbar → /tool/cbar/apps | fw-mpio (Xtensa), fw-mpras-kernel (SiFive) |
| Verif NFS | /proj/verif_release_ro | fw-pmfw (CBWA) |
| Conan 1.59 venv | ~/venvs/uttr-conan | fw-asp-fmc, fw-art-security, fw-dcgpu-esid, fw-amd-tee3 |
| Zephyr SDK 0.16.8 | /proj/smartnic/xcb/ifoe/zephyr-sdk-0.16.8 | fw-mpifoe, fw-mpras-applets, fw-mpras-kernel, fw-mpnht |
| Xtensa license | LM_LICENSE_FILE=2020@licsrv07.amd.com | fw-mpio, fw-dmu, fw-mpnht |
| tcsh | /usr/bin/tcsh | fw-pmfw |
| Rust/cargo | ~/.cargo/bin | fw-art-security (lib-dpe) |
| Ubuntu packages | build-essential, cmake, ninja-build, git, etc. | All |

### 2.2 Build Strategy

**Selective build:** Only build targets affected by the PR.

```yaml
- name: Build changed components
  run: |
    source "${HOME}/venvs/uttr-conan/bin/activate"
    cmake --preset mi450
    
    changed='${{ needs.detect.outputs.targets }}'
    for target in $(echo "$changed" | jq -r '.[]'); do
      echo "=== Building $target ==="
      cmake --build build --target "$target" -j$(nproc)
    done
```

**Full build timing estimates** (from CMakeLists.txt UTTR_PARALLEL=12 default):

| Target | Build System | Estimated Time | Notes |
|--------|-------------|----------------|-------|
| fw-asp-fmc | Make + Conan | 3-5 min | Conan install adds ~1 min first time |
| fw-mpio | Zephyr/Xtensa | 5-8 min | Includes py_mpio venv bootstrap |
| fw-mpifoe | Zephyr/RISC-V | 3-5 min | build.py with --jobs |
| fw-pmfw | tcsh/CBWA Make | 5-10 min | 5 PMFW variants (MID/AID/XCD/IMU) |
| fw-art-security | Make + Cargo | 4-7 min | lib-dpe Rust compile on first build |
| fw-amd-tee3 | Make (RISC-V) | 5-8 min | 13+ TEE drivers |
| fw-dcgpu-esid | autoconf + Make | 3-5 min | ./configure + make SOC=MI450 |
| fw-keydb | Python | < 1 min | key-db.py script |
| fw-mpras-kernel | Zephyr/RISC-V | 3-5 min | west build |
| fw-mpnht | build.sh + Make | 3-5 min | Xtensa |
| fw-pcie-cld | Make | 1-2 min | Simple make |
| fw-ucie | Make | 1-2 min | Simple make |
| fw-vbl-tee-drv | Make | 2-3 min | |
| fw-unicrypt | Make | 2-3 min | |
| fw-caliptra-sw | Copy | < 1 min | No compile, binary copy |
| fw-dmu | Xtensa Make | 3-5 min | xt-xcc compiler |

**Single component PR: 1-10 min build time. firmware-all: ~15-25 min parallel.**

---

## 3. LKG Binary Cache

### 3.1 Artifactory Layout

```
uttr-lkg/
├── latest/                           # Symlink to most recent promoted LKG
│   ├── ifwi-mi450.bin                # Complete assembled SPIROM image
│   └── components/
│       ├── asp-fmc/                  # Per-component binaries
│       │   ├── mpasp_fmc.bin
│       │   └── manifest.json         # {commit, date, build_id}
│       ├── pmfw-firmware/
│       ├── mpio/
│       └── ... (all 16 built components)
│
├── 2026-05-04/                       # Date-stamped LKG snapshots
│   ├── ifwi-mi450.bin
│   ├── components/
│   └── lkg-manifest.yaml
│
├── 2026-05-03/
└── ...
```

### 3.2 LKG Fetch Script

```python
#!/usr/bin/env python3
"""Fetch LKG binaries for unchanged components."""
# scripts/fetch-lkg-binaries.py

import yaml
import subprocess

def fetch_lkg(manifest_path, skip_targets, output_dir):
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    for component, info in manifest["components"].items():
        target = f"fw-{component}"
        if target in skip_targets:
            print(f"  SKIP {target} (building from PR)")
            continue

        artifact_url = info["artifact"]
        dest = f"{output_dir}/{component}/"
        print(f"  FETCH {target} from {artifact_url}")
        subprocess.run([
            "jfrog", "rt", "download",
            artifact_url, dest
        ], check=True)
```

---

## 4. SimNow Gate (L0-L3)

### 4.1 Assertion Definitions

From the MI450 IFWI layout and current_draft_plan.md Tier 1 spec:

| Level | Assertion | What It Checks | Timeout | Mandatory |
|-------|-----------|----------------|---------|-----------|
| L0 | IFWI Boot | EFS parsed, L1 PSP Dir found, ISH read, L2 partition loaded, PSP FMC initialized | 120s | Yes |
| L1 | GPU Enumeration | GPU appears on PCIe bus (device 1002:xxxx for mi450) | 60s | Yes |
| L2 | Driver Load | amdgpu kernel module loads, attaches to GPU | 120s | Yes |
| L3 | IP Discovery | IP discovery table (PSP entry 0x20, 12K) parsed, all expected IPs present | 60s | Yes |

### 4.2 SimNow Configuration

Based on what IVV's `patch-run-simnow.yml` uses:

```yaml
# configs/mi450_simnow.yaml
product: mi450
simnow:
  config_file: "mi450_a0.cfg"  # SimNow product config
  memory: "32G"
  timeout_total: 600  # 10 min max for all assertions
  boot_timeout: 300   # 5 min for boot

assertions:
  L0_boot:
    markers:
      - "PSP firmware initialized"
      - "L2 PSP Directory loaded"
      - "ISH boot priority: A"
    fail_markers:
      - "PSP boot failed"
      - "Invalid EFS signature"
      - "L1 directory corrupt"

  L1_enumeration:
    markers:
      - "GPU enumerated"
      - "PCI device 1002:"
    command: "lspci -d 1002: -nn"

  L2_driver_load:
    markers:
      - "amdgpu: initialization complete"
    command: "dmesg | grep amdgpu"
    fail_markers:
      - "amdgpu: probe failed"
      - "amdgpu: firmware loading failed"

  L3_ip_discovery:
    markers:
      - "IP discovery: all blocks found"
    check: "sysfs IP discovery matches expected topology"
```

---

## 5. Result Reporting

### 5.1 JUnit XML Generation

```python
#!/usr/bin/env python3
"""Convert SimNow test output to JUnit XML for GitHub Actions."""
# scripts/simnow-to-junit.py

import xml.etree.ElementTree as ET
from dataclasses import dataclass

@dataclass
class TestResult:
    name: str
    status: str  # PASS, FAIL, SKIP
    duration_sec: float
    message: str = ""
    log: str = ""

def generate_junit(results: list[TestResult], suite_name: str) -> str:
    suite = ET.Element("testsuite", {
        "name": suite_name,
        "tests": str(len(results)),
        "failures": str(sum(1 for r in results if r.status == "FAIL")),
        "time": str(sum(r.duration_sec for r in results)),
    })

    for r in results:
        case = ET.SubElement(suite, "testcase", {
            "name": r.name,
            "time": str(r.duration_sec),
        })
        if r.status == "FAIL":
            failure = ET.SubElement(case, "failure", {"message": r.message})
            failure.text = r.log

    return ET.tostring(suite, encoding="unicode", xml_declaration=True)
```

### 5.2 PR Check Display

The PR will show:
```
Merlin Gate: SimNow Boot (mi450)
├── L0_boot ✅ (95s)
├── L1_enumeration ✅ (12s)
├── L2_driver_load ✅ (45s)
└── L3_ip_discovery ✅ (8s)
Total: 160s — PASS
```

---

## 6. Phase 1 Milestone Checklist

```
□ detect-changed-targets.py operational
□ GHA workflow triggers on PR to any firmware/ path
□ All 16 built targets compile on IVV runners
□ LKG binary cache populated in Artifactory
□ lkg-manifest.yaml created and maintained
□ IFWI image assembly working (Option A or B)
□ SimNow L0-L3 assertions running for mi450
□ JUnit XML results posted to PRs
□ Total gate time < 30 min for single-component PRs
□ Documentation: onboarding guide for component owners
```
