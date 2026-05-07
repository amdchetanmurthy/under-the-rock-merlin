# Merlin: Unified Test Schema Specification

**Purpose:** Define a common YAML schema (`uttr-tests.yaml`) that every firmware component uses to declare its tests across all three tiers. This enables the Merlin orchestrator to discover, schedule, and report tests uniformly.

---

## 1. Schema Version 1.0

```yaml
# uttr-tests.yaml — placed in firmware/<component>/ root
schema_version: "1.0"

component:
  name: "fw-asp-fmc"                    # CMake target name
  fw_ids: ["0x0001"]                     # PSP entry type IDs this component produces
  psp_entries:                           # Detailed entry mapping
    - type: 0x0001
      name: "MPASP_FMC"
      max_size: 131072                   # 128K — from L2 PSP directory
      output_glob: "output/asp-fmc/*.bin"

  build:
    system: "make"                       # make | cmake | zephyr | python | copy
    conan_required: true                 # needs Conan venv activated
    nfs_required:                        # NFS mounts needed
      - "/opt/cbar"                      # Xtensa/RISC-V tools
    estimated_build_time_sec: 300        # 5 min

# ── Test Tiers ──

pre_submit:
  # Tests that run on every PR. MUST complete within budget.
  budget_sec: 600  # 10 min max for this component's pre-submit tests

  tests:
    - name: "boot_with_component"
      description: "IFWI boots with this component's binary"
      type: "simnow"
      assertions:
        - "L0_boot"       # references common assertion
        - "L1_enumeration"
        - "L5_fw_version"
      timeout_sec: 300
      products: ["mi450"]
      mandatory: true      # blocks merge if fails

    - name: "component_init"
      description: "Component-specific initialization check"
      type: "simnow"
      assertions:
        - check: "PSP FMC reports version matching build"
          marker: "MPASP FMC initialized"
          fail_marker: "MPASP FMC: init failed"
      timeout_sec: 120
      products: ["mi450"]
      mandatory: true

nightly:
  # Tests that run on nightly builds. Contribute to LKG quorum.
  budget_sec: 3600  # 1 hour max for this component's nightly tests

  tests:
    - name: "extended_boot_cycling"
      description: "10× boot cycles with this component"
      type: "hardware"
      assertions:
        - check: "All 10 boot cycles succeed"
      timeout_sec: 1200
      products: ["mi450"]

    - name: "error_injection"
      description: "FFM error injection for this component"
      type: "simnow"
      assertions:
        - check: "Injected errors correctly detected and logged"
        - check: "CPER output matches expected fault codes"
        - check: "Recovery mechanism triggers"
      timeout_sec: 600
      products: ["mi450"]

weekly:
  # Full regression. Run against LKG-promoted builds.
  budget_sec: 86400  # 24 hours

  tests:
    - name: "full_regression"
      description: "Complete FMC regression suite"
      type: "hardware"
      timeout_sec: 86400
      products: ["mi450", "mi455"]
```

---

## 2. Common Assertions (Shared Across All Components)

These are the **L0-L5 assertions** that every IFWI image must pass. They are NOT defined per-component — they are applied by the Merlin orchestrator to every assembled image.

```yaml
# configs/common-assertions.yaml
schema_version: "1.0"

assertions:
  L0_boot:
    name: "IFWI Boot"
    description: "EFS parsed → L1 Dir → ISH → L2 Dir → PSP FMC init"
    check_type: "simnow_log_markers"
    pass_markers:
      - "EFS signature valid"
      - "L1 PSP Directory loaded"
      - "ISH boot priority resolved"
      - "L2 PSP Directory parsed"
      - "PSP firmware initialized"
    fail_markers:
      - "Invalid EFS signature"
      - "L1 directory corrupt"
      - "ISH checksum mismatch"
      - "L2 directory CRC error"
      - "PSP boot failed"
    timeout_sec: 120
    mandatory: true
    source: "MI450 IFWI Layout — EFS/L1/ISH/L2 boot chain"

  L1_enumeration:
    name: "GPU Enumeration"
    description: "GPU appears on PCIe bus with correct device ID"
    check_type: "command"
    command: "lspci -d 1002: -nn"
    pass_pattern: "1002:"
    timeout_sec: 60
    mandatory: true

  L2_driver_load:
    name: "amdgpu Driver Load"
    description: "amdgpu kernel module loads and attaches to GPU"
    check_type: "command"
    command: "dmesg | grep -E 'amdgpu.*initialization'"
    pass_pattern: "amdgpu.*initialization complete"
    fail_pattern: "amdgpu.*probe failed|amdgpu.*firmware.*failed"
    timeout_sec: 120
    mandatory: true

  L3_ip_discovery:
    name: "IP Discovery"
    description: "All IP blocks found via PSP entry 0x20 (12K IP Discovery Binary)"
    check_type: "simnow_log_markers"
    pass_markers:
      - "IP discovery: all blocks found"
    validation: "IP count matches expected topology for product"
    timeout_sec: 60
    mandatory: true
    source: "PSP entry 0x20, 12K — built by fw-drivers-ipconfig (stub)"

  L4_basic_compute:
    name: "Basic Compute"
    description: "Simple HIP kernel executes (vectorAdd)"
    check_type: "command"
    command: "./vectorAdd"
    pass_pattern: "PASSED"
    timeout_sec: 120
    mandatory: false  # best-effort for pre-submit
    note: "Requires ROCm userspace — may not be available in all SimNow configs"

  L5_fw_version:
    name: "Firmware Version Check"
    description: "All firmware components report expected versions"
    check_type: "script"
    script: "scripts/check-fw-versions.py"
    args: "--manifest build-manifest.json --sysfs /sys/class/drm/card0/device/"
    timeout_sec: 30
    mandatory: true
```

---

## 3. Per-Component Test Templates

Based on the actual fw-* targets and their PSP entries:

### 3.1 fw-asp-fmc (PSP FMC — 0x0001, 128K)

```yaml
pre_submit:
  tests:
    - name: "fmc_boot_chain"
      description: "ASP FMC initializes, hands off to TOS"
      assertions:
        - "L0_boot"
        - check: "FMC version string matches build"
    - name: "key_database_load"
      description: "FMC loads key database (0x0050) successfully"
      assertions:
        - check: "PSPBL key database loaded"

nightly:
  tests:
    - name: "fmc_anti_rollback"
      description: "Anti-rollback table (0x0055) enforced"
    - name: "fmc_error_injection"
      description: "FFM: inject FMC corruption, verify detection"
```

### 3.2 fw-pmfw (Power Management — 5 PSP entries, ~900K total)

```yaml
pre_submit:
  tests:
    - name: "pmfw_init"
      description: "All 5 PMFW components initialize (MP1/AID/XCD/IMU inst/data)"
      assertions:
        - "L0_boot"
        - check: "PMFW MP1 initialized"
        - check: "IMU instruction FW loaded"
        - check: "IMU data FW loaded"

nightly:
  tests:
    - name: "power_state_transitions"
      description: "GPU transitions through power states (D0/D3hot/D3cold)"
    - name: "clock_validation"
      description: "Clock frequencies match expected ranges"
    - name: "thermal_limits"
      description: "Thermal throttling triggers at expected temperatures"
```

### 3.3 fw-mpio (MPIO — 0x005d, 256K)

```yaml
pre_submit:
  tests:
    - name: "mpio_link_training"
      description: "PCIe links train to expected width/speed"
      assertions:
        - "L0_boot"
        - "L1_enumeration"
        - check: "MPIO: all PCIe links trained"
        - check: "PCIe Gen5 x16 active"

nightly:
  tests:
    - name: "xgmi_topology"
      description: "XGMI links enumerate and report correct topology"
    - name: "mpio_reset_resilience"
      description: "Links retrain after warm reset (10× cycles)"
    - name: "pcie_bandwidth"
      description: "PCIe bandwidth meets minimum threshold"
```

### 3.4 fw-amd-tee3 (TEE — 14 PSP entries, ~3MB total)

```yaml
pre_submit:
  tests:
    - name: "tee_boot_sequence"
      description: "TOS boots, all 13 TEE drivers load in order"
      assertions:
        - "L0_boot"
        - check: "TEE TOS initialized"
        - check: "TEE Boot Driver loaded"
        - check: "TEE SoC Driver loaded"
        - check: "TEE HAD Driver loaded"
        - check: "TEE Interface Driver loaded"
        - check: "TEE System Driver loaded"

nightly:
  tests:
    - name: "spdm_handshake"
      description: "SPDM driver (0x0068) performs attestation handshake"
    - name: "ras_driver"
      description: "TEE RAS driver (0x0064) can inject/read MCA errors"
    - name: "sriov_driver"
      description: "TEE SRIOV driver (0x01F7) initializes VF management"
```

---

## 4. Test Result Schema

```yaml
# test-result.yaml — emitted by merlin-test-runner.py
schema_version: "1.0"

run:
  id: "merlin-20260505-143000-abc123"
  tier: "pre_submit"           # pre_submit | nightly | weekly
  trigger:
    type: "pull_request"       # pull_request | nightly | manual
    ref: "PR #142"
    changed_targets: ["fw-mpio"]
  product: "mi450"
  timestamp: "2026-05-05T14:30:00Z"
  duration_sec: 847

build:
  targets_built: ["fw-mpio"]
  lkg_baseline: "2026-05-04"
  ifwi_image: "ifwi-mi450-pr142.bin"
  ifwi_sha256: "a1b2c3d4..."
  build_duration_sec: 420

common_assertions:
  - name: "L0_boot"
    status: "PASS"
    duration_sec: 95
    details: "PSP initialized, L2 directory parsed (74 entries)"

  - name: "L1_enumeration"
    status: "PASS"
    duration_sec: 12
    details: "GPU 1002:7460 on bus 03:00.0"

  - name: "L2_driver_load"
    status: "PASS"
    duration_sec: 45
    details: "amdgpu: initialization complete"

  - name: "L3_ip_discovery"
    status: "PASS"
    duration_sec: 8
    details: "All IP blocks found (matches mi450 topology)"

  - name: "L5_fw_version"
    status: "PASS"
    duration_sec: 3
    details: "MPIO version matches build output"

component_tests:
  - name: "mpio_link_training"
    component: "fw-mpio"
    status: "PASS"
    duration_sec: 180
    details: "8/8 PCIe links trained to Gen5 x16"

  - name: "xgmi_topology"
    component: "fw-mpio"
    status: "SKIP"
    reason: "Not in pre_submit tier"

summary:
  total: 6
  passed: 5
  failed: 0
  skipped: 1
  verdict: "PASS"
```

---

## 5. Test Discovery and Execution

The Merlin test runner discovers and executes tests:

```python
#!/usr/bin/env python3
"""Merlin test runner — discovers and executes tests from uttr-tests.yaml."""
# scripts/merlin-test-runner.py

def discover_tests(changed_targets, tier, product):
    """Find all tests to run for the given targets and tier."""
    tests = []

    # 1. Always run common assertions
    tests.extend(load_common_assertions())

    # 2. Load component-specific tests for changed targets
    for target in changed_targets:
        component_dir = target_to_submodule(target)
        test_file = f"firmware/{component_dir}/uttr-tests.yaml"
        if os.path.exists(test_file):
            spec = yaml.safe_load(open(test_file))
            tier_tests = spec.get(tier, {}).get("tests", [])
            for test in tier_tests:
                if product in test.get("products", [product]):
                    tests.append(test)

    return tests

def run_tests(tests, simnow_session):
    """Execute tests against a running SimNow session."""
    results = []
    for test in tests:
        result = execute_single_test(test, simnow_session)
        results.append(result)

        # Early exit on mandatory failure
        if result.status == "FAIL" and test.get("mandatory", True):
            break

    return results
```

---

## 6. Component Onboarding

To add a component to the unified test schema:

1. **Create `firmware/<component>/uttr-tests.yaml`** using the schema above
2. **Define pre_submit tests** (must fit within 10-min budget per component)
3. **Define nightly tests** (1-hour budget per component)
4. **Define weekly tests** (full regression)
5. **Map PSP entries** in the `component.psp_entries` section
6. **Validate** by running: `python3 scripts/validate-uttr-tests.py firmware/<component>/uttr-tests.yaml`
7. **Register** in `configs/psp-entry-map.yaml` for IFWI assembly

**Current coverage (Phase 1 target: 16 components with uttr-tests.yaml):**

| Component | PSP Entries | Pre-Submit Tests | Status |
|-----------|-------------|------------------|--------|
| fw-asp-fmc | 1 entry (128K) | Boot chain, key DB load | To create |
| fw-pmfw | 5 entries (900K) | All 5 variants init | To create |
| fw-mpio | 1 entry (256K) | Link training, PCIe validation | To create |
| fw-amd-tee3 | 14 entries (3MB) | TOS boot, 13 driver loads | To create |
| fw-mpifoe | 1 entry (512K) | IFoE link up, fabric discovery | To create |
| fw-art-security | 2 entries (140K) | ART boot, secure execution | To create |
| fw-dcgpu-esid | 9 entries (600K) | eSID partition loading | To create |
| fw-keydb | 3 entries (52K) | Key validation | To create |
| fw-mpras-kernel | 1 entry (128K) | RAS init | To create |
| fw-mpnht | 1 entry (25K) | NHT controller init | To create |
| fw-pcie-cld | 1 entry (16K) | CLD load | To create |
| fw-ucie | 1 entry (81K) | UCIe PHY training | To create |
| fw-unicrypt | 2 entries (200K) | LibROM overlay | To create |
| fw-vbl-tee-drv | 1 entry | VBL runtime init | To create |
| fw-caliptra-sw | 1 entry (128K) | Caliptra RoT init | To create |
| fw-dmu | 1 entry | DMCUB init | To create |
