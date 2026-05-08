# AgentQ Integration for MPIFoE Testing

**Purpose:** How to add MPIFoE firmware tests to the AgentQ infrastructure so AI agents can automatically generate, execute, and triage IFoE tests.

---

## 1. AgentQ Architecture (What It Provides)

AgentQ is a **multi-agent test orchestration framework** with 9 specialized agents:

| Agent | Role | How It Helps MPIFoE |
|-------|------|---------------------|
| **qa-lead** | Orchestrator — dispatches workflows, manages phases | Drives the overall test run (daily build, feature handoff) |
| **test-planner** | Generates test plans from JIRA/specs/code | Auto-generates MPIFoE test cases from architecture spec |
| **test-critic** | Reviews test plans for coverage gaps | Validates MPIFoE test coverage (all 18 subsystems, all phases) |
| **testbed-ops** | Executes tests on hardware via SSH/MCP | Runs xncmdclient commands, collects SimNow logs |
| **analyst** | Interprets results, writes reports | Analyzes pass/fail, compares baselines, identifies regressions |
| **domain-expert** | Provides domain-specific knowledge | Knows MPIFoE architecture (threads, MCDI, IFoE subsystem blocks) |
| **kb-curator** | Manages known issues and baselines | Tracks MPIFoE known issues, flaky tests, golden baselines |
| **testbed-ops** | Provisions hardware/SimNow | Sets up SimNow, flashes IFWI, launches QEMU |

## 2. What We Need to Create

To integrate MPIFoE with AgentQ, we need a **project directory** with:

```
mpifoe-tests/                          # project_dir
├── project.yaml                       # Project identity, CLI tools, NFS paths
├── test-cases/
│   ├── sanity/
│   │   ├── fw-version.md              # MCDI version check
│   │   ├── fw-uptime.md               # Uptime check
│   │   ├── config-phase.md            # Phase check
│   │   └── port-enum.md               # Port enumeration
│   ├── bringup/
│   │   ├── link-up.md                 # Link state verification
│   │   ├── ifoe-config.md             # IFoE configuration check
│   │   ├── accelerator-discovery.md   # Active accelerator enumeration
│   │   ├── telemetry-running.md       # Telemetry collection active
│   │   └── l2ping-connectivity.md     # L2Ping all channels
│   ├── functional/
│   │   ├── loopback-ifoe.md           # IFoE loopback test
│   │   ├── loopback-mac.md            # IFoE+MAC loopback test
│   │   ├── station-mgmt.md            # Station add/remove
│   │   ├── phase-transition.md        # Provider→Tenant→Mission
│   │   └── crypto-key-provision.md    # XRSEC key provisioning
│   ├── stress/
│   │   ├── link-cycling.md            # Link up/down cycling
│   │   ├── reset-cycling.md           # Entity reset cycling
│   │   └── multi-port-traffic.md      # All ports simultaneous
│   ├── ras/
│   │   ├── ras-inject.md              # RAS error injection
│   │   └── cper-validation.md         # CPER record generation
│   └── performance/
│       ├── telemetry-latency.md       # Telemetry collection latency
│       └── prbs-ber.md                # PRBS bit error rate
├── test-suites/
│   ├── sanity.yaml                    # 4 tests, < 5 min
│   ├── bringup.yaml                   # 9 tests, < 15 min
│   ├── full-validation.yaml           # All tests, < 60 min
│   └── nightly.yaml                   # Bringup + functional + RAS
├── validations/
│   ├── fw-heartbeat-check.md          # MPIFoE firmware heartbeat
│   ├── ifoe-link-check.md             # IFoE link status
│   ├── telemetry-check.md             # Telemetry counters non-zero
│   └── error-log-check.md             # No errors in dmesg/logs
├── validation-groups/
│   ├── pre-test.yaml                  # Before any test: heartbeat + link
│   ├── post-test.yaml                 # After each test: error log + counters
│   └── full.yaml                      # All validations
├── workflows/
│   ├── mpifoe-daily.md                # Daily build health for MPIFoE
│   └── mpifoe-pr-gate.md              # PR gate workflow
├── memory/
│   └── known-issues.md                # Known MPIFoE issues/workarounds
└── agent-knowledge/
    └── domain-expert/
        └── mpifoe-architecture.md     # MPIFoE domain knowledge
```

## 3. project.yaml

```yaml
name: mpifoe-tests
description: "MPIFoE firmware test project for MI450"
jira:
  systest_tracker: FWDEV
  component: mpifoe-fw

platform:
  card_cli: xncmdclient
  card_cli_args: ""
  firmware_type: mpifoe
  asic: mi450

nfs:
  bundle_pattern: "/proj/smartnic/xcb/ifoe/simnow/*.sbin"
  fw_binary_pattern: "build/fw.mi450-a0.*/zephyr/mpifoe_fw.hbin"

simnow:
  launch_script: "/proj/smartnic/xcb/ifoe/simnow/sim111.sh"
  launch_script_dual: "/proj/smartnic/xcb/ifoe/simnow/222.sh"
  workspace: "/scratch/${USER}/simnow"

build:
  command: "./scripts/build.py -p simnow --eftest"
  source_dir: "/scratch/${USER}/mpifoe-fw"

test_suites:
  sanity:
    test_cases:
      - sanity/fw-version
      - sanity/fw-uptime
      - sanity/config-phase
      - sanity/port-enum

  bringup:
    test_cases:
      - sanity/*
      - bringup/*

  full-validation:
    test_cases:
      - sanity/*
      - bringup/*
      - functional/*
      - stress/*
      - ras/*

  nightly:
    test_cases:
      - sanity/*
      - bringup/*
      - functional/*
      - ras/*

validation_groups:
  pre-test:
    validations:
      - fw-heartbeat-check
      - ifoe-link-check

  post-test:
    validations:
      - error-log-check
      - telemetry-check

  full:
    validations:
      - fw-heartbeat-check
      - ifoe-link-check
      - telemetry-check
      - error-log-check
```

## 4. Example Test Case: L2Ping Connectivity

```markdown
---
topology: single-node
timeout: 120
pass_criteria: "All L2Ping channels (REQ, RESP, NON_IFOE) report zero failures"
priority: P0
stability: stable
validation_groups: [post-test]
---

# L2Ping Connectivity Test

## Purpose

Validates network connectivity between IFoE subsystems by sending
L2Ping packets over all three traffic channels per netport. This is
the primary health check for IFoE fabric connectivity.

## Category

positive, integration

## Prerequisites

- MPIFoE firmware booted and in PROVIDER or MISSION phase
- At least one netport link is up
- xncmdclient available on host

## Steps

1. **[host]** Configure L2Ping for all available accelerators:
   ```bash
   xncmdclient -c 'ifoe_ping_config <accel_id> <netport> 4; quit;'
   ```
   Expected: Returns ping handle and results size

2. **[host]** Start L2Ping:
   ```bash
   xncmdclient -c 'ifoe_ping_start <handle> <host_buffer>; quit;'
   ```
   Expected: Ping starts, no error

3. **[host]** Wait for completion and poll results:
   ```bash
   sleep 10
   xncmdclient -c 'ifoe_ping_poll <handle>; quit;'
   ```
   Expected: Results available

4. **[host]** Check results:
   Expected: req_failures=0, resp_failures=0, non_ifoe_failures=0

## Expected Result

All three channels report zero failures:
- IFOE_REQ (channel 0): 0 failures
- IFOE_RESP (channel 1): 0 failures  
- NON_IFOE (channel 2): 0 failures

## Failure Indicators

- Any failure count > 0
- Timeout waiting for ping completion
- "ping_config: error" in xncmdclient output
- Missing channels in results (incomplete test)

## Cleanup

- Stop any running pings:
  ```bash
  xncmdclient -c 'ifoe_ping_stop <handle>; quit;'
  ```
```

## 5. Example Validation: FW Heartbeat Check

```markdown
# Validation: MPIFoE Firmware Heartbeat Check

Run this FIRST in any validation group. If FW is hung, all other
validations will fail.

```bash
ssh $HOST "xncmdclient -c 'version; quit;'"
```

**PASS**: Returns firmware version within 5 seconds.
**CRITICAL FAIL**: Hangs, times out, or returns error.
**FAIL**: Unexpected version string or empty response.

If heartbeat fails, collect diagnostics:
```bash
ssh $HOST "dmesg | grep -i 'ifoe\|mpifoe' | tail -20"
ssh $HOST "xncmdclient -c 'read32 0x034000d8; quit;'"  # MPASP_FW_STATUS
```
```

## 6. Example Workflow: MPIFoE Daily Build Health

```markdown
# Workflow: MPIFoE Daily Build Health

## Dispatch Mode: Solo

## Trigger
- Daily CI against new MPIFoE firmware build
- After SimNow environment update
- After IFWI refresh

## Inputs
- MPIFoE firmware binary (mpifoe_fw.hbin)
- IFWI image (.sbin)
- SimNow version (default: latest)

## Phase 1: Build & Image Load

**Agent: testbed-ops**

1. Build MPIFoE firmware:
   ```bash
   cd /scratch/${USER}/mpifoe-fw
   ./scripts/build.py -p simnow --eftest
   cp build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.hbin /scratch/${USER}/simnow/
   ```

2. Launch SimNow with IFWI:
   ```bash
   /proj/smartnic/xcb/ifoe/simnow/sim111.sh --ifwi <ifwi_path>
   ```

3. Launch QEMU (after SimNow prompt appears):
   ```bash
   /scratch/${USER}/simnow/launch-qemu.sh
   ```

4. Configure IFoE:
   ```bash
   xncmdclient --force-enable-mmap -c 'eftest ifoe_bios_cfg 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
   ```

## Phase 2: Validation Suite

**Agent: testbed-ops**

Run validation group: `full`
- fw-heartbeat-check
- ifoe-link-check
- telemetry-check
- error-log-check

## Phase 3: Sanity Tests

**Agent: testbed-ops**

Run test suite: `sanity`
- fw-version, fw-uptime, config-phase, port-enum

## Phase 4: Bringup Tests

**Agent: testbed-ops**

Run test suite: `bringup`
- link-up, ifoe-config, accelerator-discovery, telemetry-running, l2ping

## Phase 5: Report

**Agent: analyst**

Generate report with:
- Build version
- SimNow version
- Pass/fail per test
- Comparison against previous daily run
- Any new failures flagged
```

## 7. How to Add Tests to AgentQ

### Step 1: Create project directory
```bash
mkdir -p mpifoe-tests/{test-cases/{sanity,bringup,functional,stress,ras,performance},test-suites,validations,validation-groups,workflows,memory,agent-knowledge/domain-expert}
```

### Step 2: Write project.yaml
Copy the template from section 3 above, customize paths.

### Step 3: Write test cases
Each test case is a markdown file with YAML frontmatter (section 4 above).
Follow the template at `plugins/agentq/templates/test-cases/test-case-template.md`.

### Step 4: Write validations
Each validation is a markdown file with check commands.
Follow examples at `plugins/agentq/templates/validations/`.

### Step 5: Define test suites
YAML files listing which test cases belong to each suite (sanity, bringup, full, nightly).

### Step 6: Define validation groups
YAML files listing which validations run before/after tests.

### Step 7: Write workflows
Markdown files defining the phased execution plan.

### Step 8: Add domain knowledge
Copy `mpifoe-architecture.md` to `agent-knowledge/domain-expert/` so the domain-expert agent understands MPIFoE.

### Step 9: Configure AgentQ
Add to `agentq-config.yaml`:
```yaml
project_dir: /path/to/mpifoe-tests
logs_dir: ./agentq-logs
plans_dir: ./agentq-plans
scratch_dir: ./agentq-scratch
testbeds:
  - name: simnow-mi450
    topology: single-node
    hosts:
      - ip: xcbl-rtl01.xilinx.com
```

### Step 10: Run
```bash
# Via AgentQ skill:
/agentq daily-build-health --testbed simnow-mi450

# Or via qa-lead agent directly
```

## 8. Key Integration Points

| AgentQ Component | MPIFoE Integration |
|------------------|-------------------|
| `card_cli` | `xncmdclient` (all MCDI commands) |
| `load-image` skill | Build mpifoe_fw.hbin + launch SimNow + QEMU |
| `fw-heartbeat-check` | `xncmdclient -c 'version; quit;'` |
| `test-planner` input | MP IFoE architecture doc + MCDI command list |
| `test-critic` coverage | 18 subsystems × 3 phases × 11 threads |
| `analyst` baselines | SimNow log markers + MCDI response values |
| `kb-curator` | Known MPIFoE issues from FWDEV JIRA |
