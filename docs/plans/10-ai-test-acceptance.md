# Merlin: AI-Powered Test Acceptance & Release Strategy

**Problem:** Getting 40+ module owners to write conforming acceptance tests is a nightmare. Each team has different test frameworks, coverage levels, and CI maturity. We can't wait for human coordination.

**Solution:** AI agents that automatically generate, validate, and execute acceptance tests per module — grounded in SimNow behavior, not hallucinated assertions.

---

## 1. The Test Acceptance Problem

Today (from our inventory of 15 repos):
- Only **3 of 15** repos run unit tests in their PR gate
- Only **10 of 15** have SimNow tests
- **2 repos** have zero CI
- Test patterns vary wildly: CppUTest, pytest, Zephyr Twister, custom C, or nothing
- No unified acceptance criteria across modules
- Module owners treat testing as "someone else's problem"

**What we need:** A system where Merlin defines the acceptance bar, AI generates the tests, SimNow validates them, and humans only intervene on failures — not on test creation.

---

## 2. AI Test Acceptance Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  PR SUBMITTED TO ANY firmware/ SUBMODULE                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ STAGE 1: AI TEST GENERATOR                               │     │
│  │                                                           │     │
│  │ Input:                                                    │     │
│  │   - PR diff (what changed)                                │     │
│  │   - Component's PSP entry type + size from IFWI layout    │     │
│  │   - Existing SimNow YAML configs (.github/simnow/*.yaml) │     │
│  │   - Previous test results for this component              │     │
│  │   - FW status register values that indicate success       │     │
│  │                                                           │     │
│  │ Output:                                                   │     │
│  │   - Acceptance test plan (YAML)                           │     │
│  │   - SimNow script modifications (if needed)               │     │
│  │   - Expected postcodes / FW status values                 │     │
│  │   - Register assertions to check after boot               │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          │                                        │
│                          ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ STAGE 2: GROUNDED VALIDATION (Anti-Hallucination)        │     │
│  │                                                           │     │
│  │ Before running any AI-generated test:                     │     │
│  │   1. Verify PSP entry types exist in IFWI layout          │     │
│  │   2. Verify register addresses are in PPR/regspec         │     │
│  │   3. Verify postcode values match known-good from LKG     │     │
│  │   4. Verify SimNow BSD model supports the assertions      │     │
│  │   5. Cross-check against previous successful test runs    │     │
│  │                                                           │     │
│  │ If ANY assertion can't be grounded → mark as UNVERIFIED   │     │
│  │ Only GROUNDED assertions block merge                      │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          │                                        │
│                          ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ STAGE 3: SIMNOW EXECUTION                                │     │
│  │                                                           │     │
│  │ Run acceptance tests on SimNow:                           │     │
│  │   - Build component from PR                               │     │
│  │   - Assemble IFWI (PR binary + LKG for rest)              │     │
│  │   - Boot in SimNow with appropriate model                 │     │
│  │   - Check grounded assertions (postcodes, registers)      │     │
│  │   - Record ALL register values for future baselining      │     │
│  │                                                           │     │
│  │ Pass criteria: ALL grounded assertions pass               │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          │                                        │
│                          ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ STAGE 4: BASELINE LEARNING                                │     │
│  │                                                           │     │
│  │ After each successful test run:                           │     │
│  │   - Record all register values at boot milestones         │     │
│  │   - Record all FW status transitions                      │     │
│  │   - Record timing (how long each boot phase takes)        │     │
│  │   - Store as "golden baseline" for this component version │     │
│  │                                                           │     │
│  │ Next PR: compare against golden baseline                  │     │
│  │   - New register value → investigate (regression?)        │     │
│  │   - Missing FW status transition → flag                   │     │
│  │   - Timing deviation > 20% → warning                     │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Anti-Hallucination: How to Ground AI-Generated Tests

The #1 risk with AI-generated tests is hallucinated assertions — checking register addresses that don't exist, expecting postcodes that are wrong, or asserting behavior the component doesn't have.

### 3.1 Ground Truth Sources

| Source | What It Provides | How AI Uses It |
|--------|-----------------|----------------|
| **IFWI Layout** (memory-bank/14-ifwi-layout-mi450.md) | 74 PSP entry types, sizes, offsets | Verify component's PSP slot exists and size is correct |
| **SimNow mi450.yaml** (firmware/asp-fmc/.github/simnow/mi450.yaml) | BSD models, scripts, postcodes, timeouts | Use exact same configs, don't invent new ones |
| **Previous test results** (golden baselines) | Known-good register values, FW status transitions | Compare against, don't guess |
| **SimNow logs from LKG** | Actual boot sequence, timing, register reads | Extract real assertions from real runs |
| **FW status register map** | MPASP_FW_STATUS addresses and bit meanings | Only assert documented bit fields |
| **Component source code** | What the firmware actually does | Understand intent, but don't trust code comments alone |

### 3.2 The Grounding Rules

```yaml
# merlin-grounding-rules.yaml
# Rules that prevent AI from hallucinating test assertions

rules:
  register_assertions:
    # ONLY assert registers that appear in SimNow logs from a known-good run
    must_exist_in: "golden_baseline.registers"
    # NEVER invent register addresses
    never_guess_addresses: true
    # If a register isn't in the golden baseline, mark as UNVERIFIED
    unknown_handling: "unverified"

  postcode_assertions:
    # ONLY use postcodes from the SimNow YAML config or golden baseline
    allowed_sources:
      - "firmware/<component>/.github/simnow/*.yaml → postcode field"
      - "golden_baselines/<component>/postcodes.yaml"
    # The canonical pass postcode for MI450
    mi450_pass: "0X800F0000"

  fw_status_assertions:
    # Monitor addresses are FIXED per model (from SimNow scripts)
    mi450_monitors:
      MPART_FW_STATUS: { address: "0x034000d8", space: "0.0.mpart" }
      MPASP_FW_STATUS: { address: "0x034000d8", space: "0.0.mpasp" }
      MID_MPART_FW_STATUS: { address: "0x03010d80", space: "4.0.mpart" }
      MID_MPASP_FW_STATUS: { address: "0x03010d80", space: "4.0.mpasp" }

  timing_assertions:
    # Don't assert exact timing — use ranges from golden baseline ±20%
    tolerance_percent: 20
    # Boot phases with expected durations (from golden baselines)
    source: "golden_baselines/<component>/timing.yaml"

  size_assertions:
    # Binary size must fit in PSP slot (from IFWI layout)
    source: "configs/psp-entry-map.yaml"
    # Warn if binary > 90% of slot, fail if > 100%
    warn_threshold_percent: 90
    fail_threshold_percent: 100
```

### 3.3 Golden Baseline Collection

The golden baseline is built from **actual SimNow runs of known-good builds**, not from documentation or guesses:

```python
# scripts/collect-golden-baseline.py
"""
Run after a successful LKG promotion.
Boots LKG IFWI in SimNow and records everything.
"""

class GoldenBaselineCollector:
    def collect(self, component, simnow_log, simnow_err_log):
        baseline = {
            "component": component,
            "lkg_date": current_lkg_date(),
            "lkg_commit": current_lkg_commit(component),

            # All register values observed during boot
            "registers": self.extract_register_values(simnow_log),

            # FW status transitions (ordered sequence)
            "fw_status_sequence": self.extract_fw_status_transitions(simnow_log),

            # Final postcodes
            "postcodes": self.extract_postcodes(simnow_log),

            # Boot phase timing
            "timing": self.extract_timing(simnow_log),

            # Error log (should be empty for golden baseline)
            "errors": self.extract_errors(simnow_err_log),
        }

        # Save as golden baseline
        save_golden_baseline(component, baseline)
        return baseline
```

---

## 4. Per-Module Acceptance Test Template

Every module gets an auto-generated acceptance test file. The AI generates it, grounding validates it, SimNow executes it.

```yaml
# acceptance-tests/<component>.yaml
# AUTO-GENERATED by Merlin AI — grounded against golden baseline
# Last regenerated: 2026-05-06
# Golden baseline: LKG 2026-05-05, commit abc1234

component: fw-asp-fmc
psp_entry: 0x0001
psp_slot_size: 131072  # 128K — from IFWI layout
grounding_source: "golden_baselines/asp-fmc/2026-05-05.yaml"

# ── TIER 1: PR Gate (every PR, < 10 min) ──
pr_gate:
  simnow_model: "mi450_0p1g1mid1aid2xcd_unsecure"  # from mi450.yaml
  simnow_timeout: 600

  assertions:
    # GROUNDED: from golden baseline
    - name: "binary_size_check"
      type: "static"
      check: "binary_size <= 131072"
      grounded: true
      source: "IFWI layout PSP entry 0x0001 max size"

    - name: "boot_postcode"
      type: "simnow_postcode"
      expected: "0X800F0000"
      grounded: true
      source: "mi450.yaml postcode field"

    - name: "mpasp_fw_status"
      type: "simnow_register"
      address: "0x034000d8"
      space: "0.0.mpasp"
      expected: "0x800f0000"
      grounded: true
      source: "golden baseline register dump"

    - name: "esid_completion"
      type: "simnow_log_marker"
      marker: "all ESIDs completed"
      grounded: true
      source: "golden baseline log analysis"

    - name: "tos_steady_state"
      type: "simnow_log_marker"
      marker: "TOS steady state"
      grounded: true
      source: "golden baseline log analysis"

    - name: "no_error_log_entries"
      type: "simnow_error_log"
      expected: "empty"
      grounded: true
      source: "golden baseline error log was empty"

    # UNVERIFIED: AI-suggested based on code analysis (advisory only)
    - name: "fmc_version_string"
      type: "simnow_log_marker"
      marker: "MPASP FMC version"
      grounded: false
      note: "AI-suggested — verify against actual SimNow output"

# ── TIER 2: Daily (nightly build, full model matrix) ──
daily:
  simnow_models:
    - "mi450_0p1g1mid1aid2xcd_unsecure"
    - "mi450_0p1g2mid2aid8xcd_unsecure"
    - "mi450_0p1g2mid2aid8xcd_secure"
    - "mi450_1p1g2mid2aid2xcd_skt7_unsecure"

  assertions:
    # All PR gate assertions PLUS:
    - name: "secure_boot_chain"
      type: "simnow_log_marker"
      marker: "secure boot: signature verified"
      models: ["*_secure"]
      grounded: true

    - name: "boot_timing_regression"
      type: "timing_comparison"
      phase: "fmc_to_tos"
      golden_baseline_ms: 45000
      tolerance_percent: 20
      grounded: true

# ── TIER 3: Release Gate (before promotion to stable) ──
release_gate:
  simnow_models: "ALL"  # every config from mi450.yaml

  assertions:
    # All daily assertions PLUS:
    - name: "full_model_matrix_pass"
      type: "matrix_quorum"
      required_pass_rate: 100  # release requires 100%, not 83%

    - name: "no_regression_vs_previous_release"
      type: "baseline_diff"
      compare_against: "stable"
      max_new_warnings: 0
```

---

## 5. Release Branching Strategy

### 5.1 Three Branches

```
main (integration)
  │
  │  ← PRs land here first
  │  ← Nightly builds from here
  │  ← LKG promoted from here
  │
  ├──→ stable-next (release candidate)
  │      │
  │      │  ← Promoted from main when LKG passes extended validation
  │      │  ← Daily full-matrix SimNow + hardware tests
  │      │  ← Release candidate for next stable
  │      │
  │      └──→ stable (production release)
  │             │
  │             │  ← Promoted from stable-next after release gate passes
  │             │  ← Tagged with BKC version (e.g., BKC-X26.05)
  │             │  ← Only cherry-picks for critical fixes
  │             │  ← What customers/downstream consume
  │             │
  │             └── stable tags: BKC-X26.05, BKC-X26.04, ...
  │
  └── main tags: LKG-2026-05-06, LKG-2026-05-05, ...
```

### 5.2 Branch Rules

| Branch | Who Commits | Testing Required | Promotion Criteria |
|--------|------------|------------------|-------------------|
| **main** | Anyone via PR | PR gate (SimNow boot, grounded assertions) | PR passes all GROUNDED assertions |
| **stable-next** | Automated promotion from main | Full SimNow matrix + hardware smoke | LKG quorum (15/18) + 24h soak on daily tests |
| **stable** | Automated promotion from stable-next + cherry-picks | Release gate (100% matrix, no regressions) | Release gate passes + release manager sign-off |

### 5.3 Promotion Flow

```
Developer opens PR to main
    │
    ▼
PR Gate (Tier 1): Build + SimNow boot + grounded assertions
    │ PASS
    ▼
Merge to main
    │
    ▼
Nightly: Build all from main HEAD, run daily tests (Tier 2)
    │ 15/18 quorum PASS
    ▼
LKG promoted: tag main with LKG-YYYY-MM-DD
    │
    ▼
LKG soak: 24h on daily tests, no regressions
    │ PASS
    ▼
Promote to stable-next: fast-forward or merge from main
    │
    ▼
stable-next daily: Full model matrix + hardware tests
    │ 3 consecutive days green
    ▼
Release gate (Tier 3): 100% matrix pass, baseline diff clean
    │ PASS + release manager approval
    ▼
Promote to stable: fast-forward, tag BKC-X26.XX
    │
    ▼
stable: Only cherry-picks for P0/P1 fixes
    │ Each cherry-pick must pass release gate
```

### 5.4 Branch Configuration

```yaml
# merlin-branches.yaml
branches:
  main:
    purpose: "Integration branch — all PRs land here"
    protection:
      required_checks:
        - "merlin-pr-gate"           # SimNow boot + grounded assertions
        - "coverity-incremental"      # Static analysis
      require_pr: true
      dismiss_stale_reviews: true
    testing:
      on_pr: "tier1"                  # PR gate
      nightly: "tier2"                # Daily full matrix
    promotion:
      target: "stable-next"
      criteria: "lkg_quorum_pass + 24h_soak"

  stable-next:
    purpose: "Release candidate — validated main"
    protection:
      require_pr: false               # Automated promotion only
      restrict_pushes:
        - "merlin-bot"
    testing:
      daily: "tier2_extended"          # Full matrix + hardware
      release_gate: "tier3"            # 100% pass required
    promotion:
      target: "stable"
      criteria: "3_days_green + release_gate_pass + manager_approval"

  stable:
    purpose: "Production release — what customers use"
    protection:
      require_pr: true                 # Cherry-picks only
      required_checks:
        - "merlin-release-gate"        # Full validation
      require_review: 2                # Two approvals for cherry-picks
    testing:
      on_cherry_pick: "tier3"          # Full release gate
    tags:
      format: "BKC-X{yy}.{ww}"        # e.g., BKC-X26.05
```

### 5.5 Cherry-Pick Flow (Hotfix to Stable)

```
P0 bug found in stable
    │
    ▼
Fix developed on main (normal PR flow)
    │ PR gate passes
    ▼
Merged to main
    │
    ▼
Cherry-pick PR to stable (git cherry-pick -x <sha>)
    │
    ▼
Release gate runs on cherry-pick PR
    │ 100% matrix pass
    ▼
Merge to stable, tag BKC-X26.05.1 (patch release)
    │
    ▼
Also cherry-pick to stable-next (keep branches aligned)
```

---

## 6. AI Test Agent Design

### 6.1 Test Generator Agent

```python
class MerlinTestGenerator:
    """Generate acceptance tests for a firmware component.

    CRITICAL: Never hallucinate assertions. Every assertion must be
    grounded in one of:
    1. IFWI layout (PSP entry sizes)
    2. SimNow YAML configs (postcodes, models, timeouts)
    3. Golden baseline (register values from actual runs)
    4. SimNow monitor addresses (from script templates)
    """

    def generate(self, component, pr_diff, golden_baseline):
        assertions = []

        # 1. Static checks (always grounded)
        psp_entry = self.lookup_psp_entry(component)
        if psp_entry:
            assertions.append({
                "name": "binary_size_check",
                "type": "static",
                "check": f"binary_size <= {psp_entry['max_size']}",
                "grounded": True,
                "source": f"IFWI layout PSP entry {psp_entry['type']:#x}",
            })

        # 2. SimNow boot assertions (from existing YAML configs)
        simnow_config = self.load_simnow_yaml(component)
        if simnow_config:
            assertions.append({
                "name": "boot_postcode",
                "type": "simnow_postcode",
                "expected": simnow_config["postcode"],
                "grounded": True,
                "source": f"{component} .github/simnow/*.yaml",
            })

        # 3. Golden baseline assertions (from actual runs)
        if golden_baseline:
            for reg_name, reg_value in golden_baseline["registers"].items():
                assertions.append({
                    "name": f"register_{reg_name}",
                    "type": "simnow_register",
                    "address": reg_value["address"],
                    "expected": reg_value["value"],
                    "grounded": True,
                    "source": f"golden baseline {golden_baseline['lkg_date']}",
                })

            for marker in golden_baseline["fw_status_sequence"]:
                assertions.append({
                    "name": f"log_marker_{marker['name']}",
                    "type": "simnow_log_marker",
                    "marker": marker["text"],
                    "grounded": True,
                    "source": f"golden baseline log",
                })

        # 4. AI-suggested assertions (UNVERIFIED — advisory only)
        ai_suggestions = self.analyze_pr_diff(pr_diff, component)
        for suggestion in ai_suggestions:
            suggestion["grounded"] = False
            suggestion["note"] = "AI-suggested — does not block merge"
            assertions.append(suggestion)

        return assertions
```

### 6.2 Grounding Validator

```python
class GroundingValidator:
    """Validate that every assertion is grounded before execution.

    An assertion is GROUNDED if and only if:
    1. Its register address exists in the golden baseline OR SimNow monitor list
    2. Its expected value was observed in a previous successful run
    3. Its log marker appeared in a previous successful run
    4. Its PSP entry type exists in the IFWI layout

    UNGROUNDED assertions are recorded but do NOT block merge.
    """

    def validate(self, assertions, golden_baseline, ifwi_layout, simnow_config):
        validated = []
        for assertion in assertions:
            if assertion.get("grounded") == False:
                assertion["verdict"] = "ADVISORY"
                validated.append(assertion)
                continue

            if assertion["type"] == "simnow_register":
                if assertion["address"] not in golden_baseline["registers"]:
                    assertion["grounded"] = False
                    assertion["verdict"] = "UNGROUNDED — address not in baseline"
                    validated.append(assertion)
                    continue

            if assertion["type"] == "simnow_log_marker":
                if not any(assertion["marker"] in m["text"]
                          for m in golden_baseline["fw_status_sequence"]):
                    assertion["grounded"] = False
                    assertion["verdict"] = "UNGROUNDED — marker never seen"
                    validated.append(assertion)
                    continue

            assertion["verdict"] = "GROUNDED"
            validated.append(assertion)

        return validated
```

### 6.3 Baseline Learning Agent

```python
class BaselineLearner:
    """After each successful SimNow run, update the golden baseline.

    The baseline grows over time:
    - New registers observed → added to baseline
    - Consistent log markers → promoted to grounded assertions
    - Timing patterns → used for regression detection

    Baseline is NEVER updated from failed runs.
    """

    def learn(self, component, simnow_log, test_result):
        if test_result.verdict != "PASS":
            return  # Never learn from failures

        current = load_golden_baseline(component)
        new_registers = extract_register_values(simnow_log)
        new_markers = extract_log_markers(simnow_log)

        # Add newly observed registers
        for reg, value in new_registers.items():
            if reg not in current["registers"]:
                current["registers"][reg] = {
                    "value": value,
                    "first_seen": today(),
                    "observation_count": 1,
                    "stable": False,  # not yet promoted to grounded
                }
            else:
                existing = current["registers"][reg]
                existing["observation_count"] += 1
                if existing["value"] == value:
                    # Same value seen 5+ times → mark as stable
                    if existing["observation_count"] >= 5:
                        existing["stable"] = True
                else:
                    # Value changed — record but don't promote
                    existing["value"] = value
                    existing["observation_count"] = 1
                    existing["stable"] = False

        save_golden_baseline(component, current)
```

---

## 7. Execution Flow: How It All Works Together

### 7.1 First-Time Onboarding (No Golden Baseline)

```
New component added to super-repo
    │
    ▼
AI generates MINIMAL acceptance test:
    - Binary size check (from IFWI layout)
    - Boot postcode check (0X800F0000 from mi450.yaml)
    - No error log entries
    │
    ▼
Run in SimNow → PASS
    │
    ▼
Baseline Learner records everything observed:
    - All registers values
    - All FW status transitions
    - All log markers
    - Boot timing
    │
    ▼
Next PR: AI generates RICHER acceptance test using the baseline
    - All previously observed registers become grounded assertions
    - Stable markers become grounded assertions
    - Baseline grows with each successful run
```

### 7.2 Steady State (Rich Golden Baseline)

```
PR submitted
    │
    ▼
AI Test Generator:
    - Reads golden baseline (hundreds of grounded assertions)
    - Reads PR diff (what changed)
    - Generates acceptance test with:
      - ALL grounded assertions from baseline
      - NEW AI-suggested assertions for changed code (UNVERIFIED)
    │
    ▼
Grounding Validator:
    - Confirms all "grounded" assertions exist in baseline
    - Marks AI-suggested assertions as ADVISORY
    │
    ▼
SimNow Execution:
    - Builds component from PR
    - Assembles IFWI (PR + LKG rest)
    - Boots in SimNow
    - Checks ALL grounded assertions → must PASS to merge
    - Checks ADVISORY assertions → logged but doesn't block
    │
    ▼
Baseline Learner:
    - If test passed: update baseline with any new observations
    - If test failed: don't update, report which grounded assertion failed
```

---

## 8. Test Acceptance Per Tier

### 8.1 PR Gate (Tier 1)

| Check | Source | Blocking | Grounded |
|-------|--------|----------|----------|
| Binary fits PSP slot | IFWI layout | YES | Always |
| SimNow boot postcode 0X800F0000 | mi450.yaml | YES | Always |
| FW status registers match baseline | Golden baseline | YES | After 5+ observations |
| Log markers present | Golden baseline | YES | After 5+ observations |
| Error log empty | Golden baseline | YES | Always |
| AI-suggested assertions | Code analysis | NO | Never (advisory) |

### 8.2 Daily (Tier 2)

All of Tier 1, plus:

| Check | Source | Blocking |
|-------|--------|----------|
| Full SimNow model matrix (all configs) | mi450.yaml `incremental: false` | YES (quorum) |
| Secure + non-secure boot | mi450.yaml script-modify | YES |
| Boot timing within ±20% of baseline | Golden baseline | WARNING only |
| Register diff vs previous day | Golden baseline | WARNING only |

### 8.3 Release Gate (Tier 3)

All of Tier 2, plus:

| Check | Source | Blocking |
|-------|--------|----------|
| 100% model matrix pass (not quorum) | All configs | YES |
| No regressions vs current stable | stable branch baseline | YES |
| No new error log entries vs stable | stable branch baseline | YES |
| AI-suggested assertions reviewed | Human review | YES (for release) |

---

## 9. Implementation Sequence

| Step | What | Depends On |
|------|------|------------|
| **1** | Build golden baseline collector — run against LKG IFWI on all SimNow models | SimNow access on runners |
| **2** | Define `acceptance-tests/<component>.yaml` schema | Golden baselines for ≥3 components |
| **3** | Build grounding validator | Schema defined |
| **4** | Build AI test generator (minimal: size + postcode + baseline) | Validator working |
| **5** | Integrate into PR gate workflow | Generator + validator + SimNow in CI |
| **6** | Build baseline learner (auto-grow baselines) | PR gate running |
| **7** | Add daily tier (full model matrix) | Nightly orchestrator running |
| **8** | Add release gate + branch promotion | stable/stable-next branches created |
| **9** | Expand AI suggestions (code-aware, not just baseline) | 30+ days of baseline data |

---

## 10. What Makes This Different From "Just Write Tests"

| Traditional Approach | Merlin AI Approach |
|---------------------|-------------------|
| Ask each module owner to write tests | AI generates tests from golden baselines |
| Tests are opinions (what developer thinks matters) | Tests are observations (what actually happens) |
| Tests can be wrong (hallucinated assertions) | Grounding validator prevents false assertions |
| Tests rot as code changes | Baselines auto-update from successful runs |
| Coverage gaps where owners skip tests | Every component gets same baseline treatment |
| Different frameworks per repo | One acceptance schema, one execution engine |
| Manual maintenance | Self-healing (baseline learner) |

The key insight: **we don't need module owners to tell us what to test. We observe what a known-good firmware does in SimNow, and we assert that the next version does the same thing.** If it doesn't, it's a regression — prove it's intentional or fix it.
