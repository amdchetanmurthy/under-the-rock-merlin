# Merlin: AI-Native Development Layer

**Purpose:** Use AI agents to automate triage, assist gardeners, review PRs, reason about BKCs, and ultimately enable firmware developers to work with AI as a peer — not just a code completion tool.

---

## 1. AI Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ MERLIN AI AGENTS                                                 │
│                                                                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ Triage Agent │ │ Gardener    │ │ PR Review   │ │ BKC         │ │
│ │              │ │ Agent       │ │ Agent       │ │ Reasoner    │ │
│ │ Reads:       │ │ Reads:      │ │ Reads:      │ │ Reads:      │ │
│ │ test-result  │ │ nightly     │ │ PR diff     │ │ manifests   │ │
│ │ .yaml        │ │ results     │ │ IFWI layout │ │ changelogs  │ │
│ │ git blame    │ │ git log     │ │ uttr-tests  │ │ ROADMAP.md  │ │
│ │              │ │             │ │ PSP entries  │ │             │ │
│ │ Outputs:     │ │ Outputs:    │ │ Outputs:    │ │ Outputs:    │ │
│ │ suspect      │ │ gardening   │ │ review      │ │ answers to  │ │
│ │ commits      │ │ issues      │ │ comments    │ │ BKC queries │ │
│ │ root cause   │ │ revert PRs  │ │ test gaps   │ │             │ │
│ └──────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ KNOWLEDGE BASE                                               │   │
│ │ • MI450 IFWI Layout (74 PSP entries, offsets, sizes)         │   │
│ │ • Component → PSP entry mapping (psp-entry-map.yaml)        │   │
│ │ • Build system per component (Make/Zephyr/tcsh/Cargo)       │   │
│ │ • BKC Modules spreadsheet (174 modules, owners, contacts)   │   │
│ │ • IVV workflow map (CMakeLists.txt header comments)          │   │
│ │ • Host prerequisites (NFS, Conan, Zephyr SDK)               │   │
│ │ • Historical LKG manifests + test results                   │   │
│ └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent 1: Triage Agent

**Trigger:** SimNow test fails on a PR or nightly build.
**Input:** `test-result.yaml` + `git log` + component knowledge
**Output:** Suspect commits, root cause hypothesis, suggested fix or revert

### 2.1 Triage Logic

```python
# Pseudocode: AI-assisted triage
class TriageAgent:
    def triage(self, test_result, product):
        # 1. Identify which assertion failed
        failed = [a for a in test_result.assertions if a.status == "FAIL"]

        # 2. Map failure to component
        for failure in failed:
            component = self.map_failure_to_component(failure)
            # e.g., "L3_ip_discovery failed" → fw-drivers-ipconfig (PSP entry 0x20)
            # e.g., "mpio_link_training failed" → fw-mpio (PSP entry 0x5d)

        # 3. Find commits since last good LKG
        last_lkg = self.read_lkg_manifest()
        commits = self.git_log(
            component, since=last_lkg.components[component].commit
        )

        # 4. Correlate failure with commit content
        suspects = []
        for commit in commits:
            diff = self.git_diff(commit)
            if self.correlates_with_failure(diff, failure):
                suspects.append(commit)

        # 5. Generate triage report
        return TriageReport(
            failure=failure,
            component=component,
            suspects=suspects,
            hypothesis=self.generate_hypothesis(failure, suspects),
            recommendation=self.recommend_action(suspects),
        )

    def map_failure_to_component(self, failure):
        """Use PSP entry mapping to identify which component failed."""
        # L0_boot failure → could be any PSP component
        # L3_ip_discovery → fw-drivers-ipconfig (PSP 0x20)
        # mpio_link_training → fw-mpio (PSP 0x5d)
        # Component-specific assertion → that component
        PSP_FAILURE_MAP = {
            "MPASP FMC": "fw-asp-fmc",     # PSP 0x1
            "TEE TOS": "fw-amd-tee3",       # PSP 0x2
            "PMFW": "fw-pmfw",               # PSP 0x8
            "MPIO": "fw-mpio",               # PSP 0x5d
            "IP discovery": "fw-drivers-ipconfig",  # PSP 0x20
            "eSID": "fw-dcgpu-esid",         # PSP 0x157-15f
        }
        for keyword, component in PSP_FAILURE_MAP.items():
            if keyword in failure.details:
                return component
        return "unknown"
```

### 2.2 Data Sources for Triage

| Data Source | Location | Agent Uses It For |
|-------------|----------|-------------------|
| test-result.yaml | Build artifacts | Failed assertion details |
| git log | firmware/<component>/ | Commits since LKG |
| git blame | firmware/<component>/src/ | Who changed what |
| IFWI layout | memory-bank/14-ifwi-layout-mi450.md | PSP entry → component mapping |
| BKC modules | memory-bank/13-bkc-modules-mi450.md | Owner/contact for component |
| SimNow logs | simnow-boot.log | Detailed error messages |
| ROADMAP.md | under-the-rock-main/ROADMAP.md | Component build status |

---

## 3. Agent 2: Gardener Agent

**Trigger:** Nightly quorum fails (< 15/18).
**Input:** Nightly results across all 18 builds + git log
**Output:** GitHub issues, revert PRs, Slack notifications

### 3.1 Gardener Workflow

```
Nightly quorum fails
    │
    ▼
Gardener Agent activates:
    │
    ├── 1. Read all 18 nightly test-result.yaml files
    │
    ├── 2. Identify failure pattern:
    │      - Single product failure? → product-specific regression
    │      - All products fail same assertion? → trunk regression
    │      - Branch failure only? → cherry-pick issue
    │
    ├── 3. Cross-reference with git log:
    │      - Commits since last successful LKG
    │      - Filter by changed components
    │
    ├── 4. Create GitHub issue with:
    │      - Failure summary (which builds, which assertions)
    │      - Suspect commits (from git log correlation)
    │      - Owner/contact (from BKC modules sheet)
    │      - Suggested action (revert commit X, or investigate Y)
    │
    ├── 5. If high confidence in suspect:
    │      - Draft revert PR automatically
    │      - Assign to gardener oncall for approval
    │
    └── 6. Notify via Slack:
           - @ifwi-oncall, @kernel-oncall, @rocm-oncall
           - Link to issue + suspect commits
```

### 3.2 Gardener Issue Template

```markdown
## Nightly ${DATE} FAILED — Gardening Required

**Quorum:** ${PASSED}/${TOTAL} (need ${THRESHOLD})
**LKG NOT PROMOTED**

### Failures
| Build | Product | Failed Assertion | Details |
|-------|---------|-----------------|---------|
| A1 | mi450 | L3_ip_discovery | Expected 8 MPIO links, found 6 |

### Suspect Commits (AI-identified)
1. **abc1234** by Bob (MPIO team) — "Refactor link training sequence"
   - Changed: firmware/mpio/mpio/src/link_training.c
   - Correlation: L3_ip_discovery failure maps to MPIO (PSP 0x5d)
   - Confidence: HIGH

### Recommended Action
- [ ] Revert abc1234 (draft PR: #XX)
- [ ] Re-run nightly after revert

### Owner
- MPIO component: ${OWNER} (from BKC modules)
- IFWI Gardener this week: ${GARDENER}
```

---

## 4. Agent 3: PR Review Agent

**Trigger:** PR opened/updated to any firmware/ submodule.
**Input:** PR diff + component's uttr-tests.yaml + PSP entry mapping
**Output:** Review comments on the PR

### 4.1 Review Checks

| Check | What It Verifies | Example |
|-------|-----------------|---------|
| Test coverage | PR has corresponding test updates if behavior changed | "You modified link_training.c but mpio's uttr-tests.yaml has no link-training-specific test" |
| PSP entry size | Binary output won't exceed PSP slot max_size | "MPASP_FMC slot is 128K; this change adds 5K of code — still within budget (estimated ~95K)" |
| Build dependency | New #include or library doesn't break build on IVV runners | "New dependency on libfoo — verify it's available on IVV runners (check host-prerequisites.md)" |
| Patch alignment | If upstream API changed, patches/<repo>/ may need updating | "This changes the Makefile target name — check if patches/mpio/0001-*.patch still applies" |
| Cross-component impact | Change in shared header could affect other fw-* targets | "firmware/amd-tee3_0/amd_tee_ddk/inc/ is included by multiple TEE drivers — all 13 may be affected" |

### 4.2 PR Review Comment Example

```markdown
### Merlin PR Review

**Component:** fw-mpio (PSP entry 0x5d, 256K slot)
**Changed files:** 3 files in firmware/mpio/mpio/src/

#### Checks
- [x] Binary size: estimated ~180K (within 256K slot)
- [x] Build system: no Makefile changes, build should succeed
- [ ] **Test gap:** `link_training.c` modified but `uttr-tests.yaml` has no
      specific link-training test in `pre_submit` tier.
      Consider adding a test assertion for the new retry logic.
- [x] Patch compatibility: no patches/mpio/ conflicts detected
- [x] Cross-component: no shared headers modified

#### Suggestion
Add to `firmware/mpio/uttr-tests.yaml` pre_submit section:
```yaml
- name: "link_training_retry"
  description: "Verify link training retries on initial failure"
  assertions:
    - check: "MPIO: link training retry succeeded"
  timeout_sec: 60
```
```

---

## 5. Agent 4: BKC Reasoner

**Trigger:** Human or agent asks about BKC state.
**Input:** lkg-manifest.yaml, release manifests, changelogs, ROADMAP.md
**Output:** Structured answers to BKC queries

### 5.1 Query Examples

| Query | Data Sources | Answer |
|-------|-------------|--------|
| "What's the current LKG for MPIO?" | lkg-manifest.yaml | "Commit ghi9012, promoted 2026-05-04, binary at artifactory://uttr-lkg/latest/components/mpio/" |
| "What changed in IFWI between BKC X25.05 and X25.06?" | releases/X25.05/manifest.yaml, releases/X25.06/manifest.yaml | Diff of commits per component, changelog summary |
| "Is fix abc1234 in the latest BKC?" | git log + release manifests | "Yes, abc1234 is an ancestor of the mi450 IFWI commit in BKC X25.06" |
| "Which components are still stubs?" | ROADMAP.md, uttr-firmware-all-kinds.txt | "19 targets are stubs: fw-cp-mi400, fw-drivers-*, fw-ip-fw, ..." |
| "Who owns the PMFW firmware?" | BKC modules (13-bkc-modules-mi450.md) | "Build engineer: Matt Mione, Alex Cheung. Owner: Ke Deng" |

---

## 6. Implementation: Claude Code Plugin

Port existing Cursor skills to Claude Code plugin structure:

```
.claude/
├── plugins/
│   └── merlin/
│       ├── plugin.json
│       ├── agents/
│       │   ├── triage-agent.md
│       │   ├── gardener-agent.md
│       │   ├── pr-review-agent.md
│       │   └── bkc-reasoner.md
│       ├── skills/
│       │   ├── triage-failure/SKILL.md
│       │   ├── review-firmware-pr/SKILL.md
│       │   ├── query-bkc/SKILL.md
│       │   ├── onboard-component/SKILL.md
│       │   └── generate-tests/SKILL.md
│       ├── hooks/
│       │   └── hooks.json           # Post-build verification hooks
│       └── CLAUDE.md                # Agent instructions
```

### 6.1 Merlin Plugin CLAUDE.md

```markdown
# Merlin — AI-Native CI/CD for UnderTheRock

You are an AI agent specialized in AMD GPU firmware CI/CD.

## Knowledge Base
- MI450 IFWI layout: 8MB SPIROM, 74 PSP directory entries
- 35 fw-* CMake targets (16 built, 19 stubs)
- Component → PSP entry mapping in configs/psp-entry-map.yaml
- BKC modules: 174 tracked modules with owners
- LKG manifests: daily-promoted baselines

## Key Rules
1. NEVER hallucinate PSP entry IDs or sizes — always read from the IFWI layout
2. NEVER guess component owners — always read from BKC modules
3. Map failures to components via PSP entry types, not by name matching
4. When triaging, always check git log since last LKG, not since arbitrary dates
5. Revert-first culture: recommend reverts over debugging in-place
```

---

## 7. Data Pipeline for AI Agents

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ BUILD OUTPUTS     │     │ TEST RESULTS      │     │ GIT HISTORY      │
│                   │     │                   │     │                   │
│ build/output/     │     │ test-result.yaml  │     │ git log           │
│ uttr-firmware-    │     │ simnow-boot.log   │     │ git blame         │
│   all-kinds.txt   │     │ junit.xml         │     │ git diff          │
│ uttr-firmware-    │     │                   │     │ lkg-manifest.yaml │
│   all-targets.txt │     │                   │     │                   │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                         │
         └────────────┬───────────┴─────────────────────────┘
                      │
              ┌───────▼───────┐
              │ MERLIN AGENTS │
              │               │
              │ Read all data │
              │ Correlate     │
              │ Reason        │
              │ Act           │
              └───────────────┘
```

All data is in **structured, machine-readable formats** (YAML, JSON, plain text with markers). No Confluence pages, no emails, no Slack threads needed for AI agents to reason about the state of the firmware stack.

---

## 8. Rollout Sequence

Each agent builds on the previous. Ship as fast as the data pipeline supports it.

| Step | AI Capability | Depends On |
|------|---------------|------------|
| 1 | **BKC Reasoner** — query manifests, ROADMAP, modules | lkg-manifest.yaml exists |
| 2 | **PR Review Agent** — test gap detection, PSP size checks | uttr-tests.yaml schema defined |
| 3 | **Triage Agent** — failure → suspect commit mapping | test-result.yaml from SimNow gate |
| 4 | **Gardener Agent** — auto-issue creation, draft reverts | Nightly orchestrator running |
| 5 | **Test Generation Agent** — generate uttr-tests.yaml from code | Components onboarded with test schema |
| 6 | **Full AI-native** — agents as first-class participants in gardener rotation | All above operational |
