# UnderTheRock - Executive Briefing (19 Slides)

**Presented by:** Chris Sosa | **Date:** March 2026

## Slide 1: Title
UnderTheRock — Making the Complete GPU Stack as Simple to Develop As ROCm Alone. Aligning firmware and kernel development with theRock's direction for ROCm 7.0+.

## Slide 2: Executive Summary

**What it is:** Aligns firmware (IFWI) and kernel driver development with theRock's direction for ROCm 7.0+.

**The Problem:**
- Fragmented tooling — Different tools, workflows, infrastructure
- Trunk frequently broken — No pre-submit testing; 24-48h regression detection
- No shared baseline — Developers guess which I×K×R combos work
- QA-driven triage — Developers brought in reactively days later

**The Solution — Three Principles:**
1. Trunk is Shippable — Pre-submit gates, revert-first (<4h), nightly LKG
2. Simplified Codebase — GitHub consolidation, one CI platform, one LKG manifest
3. Consistent, Comprehensive, Reproducible Releases — Manifest-driven BKC, 18x coverage

**Key Benefits:**
- For Developers: Trunk always usable, 30-min feedback, zero friction baseline
- For AMD: 96% faster regression detection, 18x test coverage, fewer field failures

## Slide 3: The Problem — Development is Unnecessarily Complex

Developer quotes:
> "Will my IFWI change work with the latest kernel? With ROCm 7.1? I won't know until QA runs tests tomorrow night."

> "I pulled latest ifwi/main this morning. It doesn't boot. I'll check Slack to see if anyone knows which commit broke it."

**What Makes Development Hard:**
- IFWI uses DCAuto + Conductor + IFWI Builder + Perforce
- Kernel uses Jenkins + Gerrit
- ROCm uses theRock + GitHub Actions
- Only 1 I×K×R combination tested per week
- Root cause: Testing and release infrastructure are fragmented, downstream, and QA-centric

## Slide 4: Principle 1 — Trunk is Shippable (Shift-Left)

**Before:** Commit Monday → Wait for nightly (Tuesday) → QA finds regression (Wednesday) → Debug Thursday

**After:** Open PR → Pre-submit runs (<30 min) → Pass = Merge / Fail = Fix → Trunk stays green

**Key elements:**
- Every commit tested before merge (SimNow + hardware smoke)
- Bad commits never land; PRs blocked if they break tests
- Revert-first culture — regressions reverted within 4 hours
- Nightly LKG promotion — 18 builds across 6 products
- Developer-owned triage via "gardener" rotation

## Slide 5: Principle 2 — Simplified Codebase

**Before:** "Which Perforce branch?" "Which Jenkins job?" "Do these versions work together?"

**After:** Clone super repo → Read lkg-manifest.yaml → Open PRs the same way → Same CI, same workflow

**Key elements:**
- GitHub consolidation (Perforce, Gerrit, Cerberus migrate)
- One CI platform: GitHub Actions
- One LKG manifest: `lkg-manifest.yaml`
- One branching model: Chrome OS-style (dev on main, firmware branches at tapeout)
- Three groups of repos: amd/ifwi, amd/kernel, ROCm/TheRock

## Slide 6: Principle 3 — Consistent, Comprehensive, Reproducible Releases

**Before:** Customer failure → Search Confluence → Find kernel in JIRA → Guess ROCm version → Reconstruct (1-2 hours)

**After:** Check manifest → git checkout SHAs → Reproduce exact customer env (5 min)

**Key elements:**
- Nightly LKG promotion (18 builds pass → manifest updated daily)
- Weekly BKC = promoted LKG manifest + git tags
- Matrix testing: nightly bleeding-edge, weekly N-1/N-2 compat validation
- Automated changelogs via git log
- BKC reproducibility: 1-2 hours → 5 min (95% faster)

## Slide 7: Workflow Comparison — Today vs. UnderTheRock

**Today (Fragmented):** Find hardware (Conductor Web, manual reservation) → Figure out DCAuto command → Check kernel compatibility → Flash IFWI → Reboot → Collect logs manually → Compare against... nothing → File bug for QA

**With UnderTheRock (Unified):** Open PR on amd/ifwi → GHA runs pre-submit automatically → Fetches LKG kernel + ROCm SHAs → Builds from PR branch → Runs SimNow on 6 products → Reserves hardware via DCAuto → Pass/fail in <30 min → Merge or fix

## Slide 8: Quantified Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Regression detection | 24-48h | <30 min | 96% faster |
| Trunk usability | Frequently broken | Always usable | 100% uptime |
| Nightly coverage | 1 I×K×R | 18 I×K×R | 18x |
| BKC reproducibility | 1-2h (Confluence) | 5 min (git checkout) | 95% faster |
| CI platforms | 3 systems | 1 (GHA) | 67% reduction |
| Developer onboarding | Weeks (tribal) | Days (documented) | Significant |

Additional:
- "Is trunk safe?" Unknown → Always (LKG guarantee) → Zero friction
- "Which I×K×R works?" 30 min → 5 sec (read manifest) → 99.7% faster
- "Submit HW test" 30 min manual → 0 min automated → 100% automated

## Slide 9: Strategic Alignment with theRock

**Before:**
- ROCm: theRock (unified repos, pre-submits, LKG, gardening)
- Kernel: Jenkins + Gerrit, QA-gated, no LKG, no pre-submits
- IFWI: DCAuto + Perforce, QA-gated, no LKG, no pre-submits

**After:** All three layers use the same platform, same workflow.

## Slide 10: Unified Testing Architecture

**Three tiers:**

1. **PRE-SUBMIT (<30 min)** — GHA Workflows, BLOCKS MERGE
   - EAM: IFWI (SimNow 6 products), Kernel (Kbuild)
   - ROCm (theRock pre-submits)

2. **NIGHTLY CONTINUOUS (2-4 hrs)** — LKG PROMOTION (quorum required)
   - EAM: IFWI (Racer+HW 6 products), Kernel (stress)
   - ROCm (theRock nightlies), MI450 mini-rack
   - Target: Unified LKG | Transition: Independent

3. **WEEKLY RELEASE** — Long-Duration
   - EAM: IFWI regression, Kernel IP+perf, ROCm
   - MI450 full rack (week-long), workloads

**EAM BKC is primary integration target from day 1.** Other components integrate when ready.

## Slide 11: Roles & Responsibilities

### EAM BKC Component Ownership
- **IFWI** (PFO IFWI Team): PSP, MPIO, PMFW, RAS, UMC, VBL
- **Kernel** (RTG Kernel Team): amdgpu driver, Feature impl, Component testing
- **ROCm** (ROCm Teams): Runtime (HIP, ROCr), Libraries (rocBLAS, rocFFT), Frameworks

### UnderTheRock Gardening (New)
- **IFWI Gardener** (Weekly Rotation): Monitor CI, Triage to owners, 4h revert, LKG auth
- **Kernel Gardener** (Weekly Rotation): Same responsibilities
- **ROCm Gardener** (Weekly Rotation, RFC0002): Same responsibilities
- **Platform Integration Gardener**: Rack-level tests (MI450), Cross-layer coord, L2 escalation

## Slide 12: CI/CD Workflow

Flow: Component Source Code → UnderTheRock Super-Repo → Individual BKCs (EAM, CPU, AINIC, Non-EAM, AIFM, Tools, Diags) → Rack Recipe → Component & Basic Rack Tests → Rack CI Tests → LKG Rack Recipe

Goal: Build everything from source code (some exceptions: 3rd party binaries from Sanmina, Meta SW, etc.)

## Slides 13-14: DPEG Rack Recipe Test Flow

UnderTheRock provides **Candidate Rack SW-FW Recipe** to DPEG for extended rack-level validation.

## Slide 15: CI/CD Steps

1. Individual component CI/CD: Pre-checkin for all commits
2. UnderTheRock builds individual BKCs
3. UnderTheRock builds SW-FW Rack Recipe / E2E BKC
4. UnderTheRock runs basic tests with Rack Recipe
5. DPEG runs extended tests with Rack Recipe
6. Declare LKG BKC

## Slide 16: Phased Plan

1. CI-Lite: Build BRP from BKC binaries, Run basic CI tests, Publish LKG
2. Build EAM BKC from sources in UnderTheRock (very few binary exceptions)
3. Nightly/on-demand E2E BKC from component BKCs
4. Rack Recipe tested in CI-Lite infra (short term) → DPEG Rack Level Test Flows
5. Build automatic bisection/resolver workflows for LKG BKCs
6. Parallel track: Generate multiple Rack Recipes for multiple customers and HW configs

## Slide 17: Ask for Component Owners

- Add modules to BKC modules sheet
- Provide source repo accesses and signing procedures
- Build engineer help reproduce builds in super-repo
- Setup CI/CD tests for qualifying individual and E2E BKCs
- Establish programmatic source code update/frequency/guidelines/hooks

## Slide 18: Implementation Timeline

- **Phase 0:** PoC — Tiger Team (IFWI Builder API vs source build, PoC gate)
- **Phase 1:** Foundation (GHA pipeline, LKG manifest, SimNow pre-submit)
- **Phase 2:** Hardware Pre-Submit (DCAuto integration, merge blocking <30 min, >90% pass)
- **Phase 3:** Nightly + LKG (18 nightly builds, 83% quorum promotion)
- **Phase 4:** Gardening (Oncall rotation, revert automation, all 6 firmware branches)
- **Phase 5:** Release Traceability (Release manifests, compatibility matrix)

## Slide 19: Status and Next Steps

**Current Status:**
- Architecture designed around three principles
- Implementation approach flexible (PoC determines mechanics)
- Tiger team bootstrapped (Eric Eaton + others)

**Tiger Team Determines:**
- IFWI build approach: Option A (IFWI Builder API) or Option B (source builds)
- Repository structure: Super repos (like theRock) or individual component repos
- Kernel CI integration: Build process, test harness, hardware pool
- ROCm artifact generation: How theRock produces artifacts
- Signing pipeline: When and where signing happens

**What Happens Next:**
- PoC completion → Architecture decision gate
- Phased implementation based on validated PoC
- Deliverable: One unified platform

**This briefing is an FYI on the direction and design. Resource planning for the tiger team is the immediate next step.**
