# Under The Rock — Merlin

**AI-Native CI/CD for AMD GPU Firmware**

Merlin is the intelligence layer for [UnderTheRock](https://amd.atlassian.net/wiki/spaces/SHARK/pages/1600726439/Project+UnderTheRock) — AMD's initiative to align firmware (IFWI) and kernel driver development with theRock's direction for ROCm 7.0+.

## What Is This?

This repository contains the design documentation and implementation plans for Merlin — a CI/CD gating system that:

1. **Blocks bad firmware from landing on trunk** — every PR validated via SimNow before merge
2. **Promotes known-good baselines daily** — nightly LKG via quorum across 18 builds
3. **Triages failures with AI** — automated root-cause analysis, bisection, gardener assist
4. **Enables AI-native firmware development** — agents that understand IFWI layout, PSP directory, and component dependencies

## Documentation

### UnderTheRock Project Knowledge Base

| Document | Description |
|----------|-------------|
| [Project Overview](docs/01-project-overview.md) | Mission, three principles, problem statement |
| [Scope & Architecture](docs/02-scope-and-architecture.md) | EAM BKC scope, repos, terminology |
| [Executive Briefing](docs/12-executive-briefing.md) | 19-slide executive presentation summary |
| [BKC Modules (MI450)](docs/13-bkc-modules-mi450.md) | 174 firmware modules with owners |
| [IFWI Layout (MI450)](docs/14-ifwi-layout-mi450.md) | SPIROM structure, 74 PSP directory entries |
| [CRD Ingredients](docs/15-crd-ingredients-mi455.md) | MI455 system validation components |
| [Submodule Inventory](docs/16-submodule-inventory.md) | 40 git submodules — access status |
| [Super-Repo Architecture](docs/17-super-repo-architecture.md) | CMake meta-build, fw-* targets, build systems |
| [CI/CD Gating Design](docs/18-cicd-gating-design.md) | Detailed gate design grounded in real codebase |
| [SimNow Deep Dive](docs/19-simnow-deep-dive.md) | SimNow architecture, APIs, operations |
| [FAQ](docs/11-faq.md) | Common questions |

### Merlin Plans

| Document | Description |
|----------|-------------|
| [Vision](docs/plans/00-vision.md) | Architecture layers, execution sequence |
| [Phase 0: PoC](docs/plans/01-phase0-poc.md) | End-to-end proof: build → SimNow → PR result |
| [Phase 1: Foundation](docs/plans/02-phase1-foundation.md) | Change detection, 16 targets gated, LKG manifest |
| [Phase 2: Nightly + LKG](docs/plans/03-phase2-nightly-lkg.md) | 18 nightly builds, quorum promotion, gardening |
| [IFWI Assembly](docs/plans/04-ifwi-assembly.md) | SPIROM image assembly from fw-* outputs |
| [Test Schema](docs/plans/05-test-schema.md) | Unified uttr-tests.yaml specification |
| [AI-Native Layer](docs/plans/06-ai-native.md) | Triage, gardener, PR review, BKC reasoner agents |
| [Component Onboarding](docs/plans/07-component-onboarding.md) | Per-component status and checklist |
| [SimNow Service Design](docs/plans/08-simnow-service-design.md) | SimNow deployment, versioning, runner infrastructure |

### Other

| Path | Description |
|------|-------------|
| [docs/scripts/](docs/scripts/) | Helper scripts (submodule clone) |
| [docs/assets/](docs/assets/) | Binary documents (BKC spreadsheet, executive briefing) |

## Context

- **UnderTheRock** = firmware + kernel layers beneath theRock (ROCm)
- **Merlin** = the wizard under the stone — AI-native CI/CD intelligence
- **theRock** = AMD's unified build harness for ROCm userspace
- **IFWI** = Integrated Firmware Image (74 firmware components for MI450)
- **SimNow** = AMD's pre-silicon platform simulation environment
- **BKC** = Boot Kit Configuration (validated firmware + kernel + ROCm stack)
- **LKG** = Last Known Good (daily promoted baseline)
