# Merlin — AI-Native CI/CD for UnderTheRock

**Codename:** Merlin (the wizard under the stone)
**Tagline:** Every PR is tested. Every regression is caught. Every triage is instant.

---

## What Is Merlin?

Merlin is the CI/CD intelligence layer for UnderTheRock. It takes the 35 firmware submodules, the CMake meta-build, and the SimNow simulation environment — and weaves them into a single automated gate that:

1. **Blocks bad firmware from landing on trunk** — every PR validated before merge
2. **Promotes known-good baselines daily** — nightly LKG via quorum across 18 builds
3. **Triages failures with AI** — automated root-cause analysis, bisection, gardener assist
4. **Enables AI-native firmware development** — agents that understand the IFWI layout, PSP directory, and component dependencies

## Why "Merlin"?

- The UnderTheRock project is named for what's *beneath* theRock (ROCm)
- Merlin is the wizard who lived under/in the stone in Arthurian legend
- Merlin brings intelligence to the rock — just as this layer brings AI-native development to firmware

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  MERLIN LAYER 4: AI-NATIVE DEVELOPMENT                      │
│  - AI triage agent (reads test results, suggests fixes)      │
│  - AI gardener (monitors nightly, auto-files issues)         │
│  - AI reviewer (validates PRs against IFWI layout rules)     │
│  - AI BKC reasoner (answers "what changed" from manifests)   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  MERLIN LAYER 3: ORCHESTRATION                               │
│  - Nightly orchestrator (18 builds, quorum, LKG promotion)   │
│  - Weekly BKC release pipeline                                │
│  - Gardener rotation + alerting                               │
│  - Auto-bisection on failure                                  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  MERLIN LAYER 2: VALIDATION                                  │
│  - SimNow gate (boot, enumeration, IP discovery, driver)     │
│  - FFM error injection (fault code validation)                │
│  - Hardware smoke tests (best-effort, via Conductor/DCAuto)   │
│  - Unified test schema (uttr-tests.yaml per component)       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  MERLIN LAYER 1: BUILD                                       │
│  - Change detection (PR diff → fw-* target mapping)          │
│  - Component build (CMake meta-build on IVV runners)         │
│  - IFWI image assembly (IFWI Builder API or source build)    │
│  - LKG binary cache (Artifactory per-component storage)      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  FOUNDATION: UnderTheRock Super-Repo                         │
│  - 35 fw-* CMake targets (16 built, 19 stubs)               │
│  - patches/<repo>/ overlay system                            │
│  - fetch_sources.py (parallel submodule checkout)            │
│  - IVV runner environment (NFS, Conan, Zephyr, Xtensa)      │
└─────────────────────────────────────────────────────────────┘
```

## Plan Documents

| Document | Contents |
|----------|----------|
| [01-phase0-poc.md](01-phase0-poc.md) | Phase 0: PoC — prove the gate works end-to-end for one component |
| [02-phase1-foundation.md](02-phase1-foundation.md) | Phase 1: GHA pipeline, change detection, SimNow pre-submit |
| [03-phase2-nightly-lkg.md](03-phase2-nightly-lkg.md) | Phase 2: Nightly integration, LKG promotion, CI-Lite |
| [04-ifwi-assembly.md](04-ifwi-assembly.md) | IFWI image assembly pipeline design |
| [05-test-schema.md](05-test-schema.md) | Unified test schema specification (uttr-tests.yaml) |
| [06-ai-native.md](06-ai-native.md) | AI-native development layer design |
| [07-component-onboarding.md](07-component-onboarding.md) | Per-component onboarding checklist and status |

## Execution Sequence

Each phase unlocks the next. No calendar estimates — move as fast as access and infrastructure allow.

| Phase | Deliverable | Unblocks |
|-------|-------------|----------|
| **Phase 0: PoC** | fw-asp-fmc PR → build → SimNow boot → pass/fail on PR | Proves the gate works end-to-end |
| **Phase 1: Foundation** | All 16 built targets gated, LKG manifest, SimNow for mi450 | Pre-submit gates block merges |
| **Phase 2: Nightly + LKG** | 18 builds, LKG promotion, CI-Lite test execution | Daily validated baseline exists |
| **Phase 3: Hardware Gate** | Merge-blocking DCAuto/Conductor hardware tests | Full shift-left for hardware |
| **Phase 4: Gardening** | Oncall rotation, revert automation, all firmware branches | Trunk stays green permanently |
| **Phase 5: Traceability** | Release manifests, compatibility matrix, LTS | Customer BKC reproducibility |
| **Phase 6: AI-Native** | Triage agent, gardener agent, BKC reasoner | AI as first-class participant |
