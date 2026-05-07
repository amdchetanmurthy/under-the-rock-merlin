# Under The Rock — Merlin

**AI-Native CI/CD for AMD GPU Firmware**

Merlin is the intelligence layer for [UnderTheRock](https://amd.atlassian.net/wiki/spaces/SHARK/pages/1600726439/Project+UnderTheRock) — AMD's initiative to align firmware (IFWI) and kernel driver development with theRock's direction for ROCm 7.0+.

## Quick Start

```bash
pip install pyyaml

# See all components and their baseline status
python3 -m merlin.cli status

# Generate acceptance tests for a component
python3 -m merlin.cli generate fw-asp-fmc

# Collect golden baseline from a SimNow log
python3 -m merlin.cli collect fw-asp-fmc simnow-boot.log simnow-err.log

# Run acceptance check against a SimNow log (exit 0=pass, 1=fail)
python3 -m merlin.cli check fw-asp-fmc simnow-boot.log

# Full report with JUnit XML + markdown
python3 -m merlin.cli report fw-asp-fmc simnow-boot.log simnow-err.log
```

## Documentation

### UnderTheRock Knowledge Base

| # | Document | Description |
|---|----------|-------------|
| 01 | [Project Overview](docs/01-project-overview.md) | Executive briefing: problem, 3 principles, benefits, roles, phases |
| 02 | [Installer](docs/02-installer.md) | Installer architecture, dev setup, reference docs |
| 03 | [Dev Machine Setup](docs/03-dev-machine-setup.md) | AWS EC2 provisioning guide |
| 04 | [PLDM Update HOWTO](docs/04-pldm-update-howto.md) | Complete PLDM firmware update procedure |
| 05 | [Build Leads Asks](docs/05-build-leads-asks.md) | Requirements for component build leads |
| 06 | [FAQ](docs/06-faq.md) | Common questions |
| 07 | [BKC Modules](docs/07-bkc-modules-mi450.md) | 174 MI450 firmware modules with owners |
| 08 | [IFWI Layout](docs/08-ifwi-layout-mi450.md) | SPIROM structure, 74 PSP directory entries |
| 09 | [CRD Ingredients](docs/09-crd-ingredients-mi455.md) | MI455 system validation components |
| 10 | [Submodule Inventory](docs/10-submodule-inventory.md) | 40 git submodules — access status |
| 11 | [Super-Repo Architecture](docs/11-super-repo-architecture.md) | CMake meta-build, fw-* targets, build systems |
| 12 | [CI/CD Gating Design](docs/12-cicd-gating-design.md) | Gate design grounded in real codebase data |
| — | [SimNow](docs/simnow.md) | SimNow architecture, APIs, operations, service design |

### Merlin Plans

| # | Document | Description |
|---|----------|-------------|
| 01 | [Vision](docs/plans/01-vision.md) | Architecture layers, execution sequence |
| 02 | [Phase 0: PoC](docs/plans/02-phase0-poc.md) | End-to-end proof: build → SimNow → PR result |
| 03 | [Phase 1: Foundation](docs/plans/03-phase1-foundation.md) | Change detection, targets gated, LKG manifest |
| 04 | [Phase 2: Nightly + LKG](docs/plans/04-phase2-nightly-lkg.md) | 18 nightly builds, quorum promotion, gardening |
| 05 | [IFWI Assembly](docs/plans/05-ifwi-assembly.md) | SPIROM image assembly from fw-* outputs |
| 06 | [Test Schema](docs/plans/06-test-schema.md) | Unified uttr-tests.yaml specification |
| 07 | [AI-Native Layer](docs/plans/07-ai-native.md) | Triage, gardener, PR review, BKC reasoner agents |
| 08 | [Component Onboarding](docs/plans/08-component-onboarding.md) | Per-component status and checklist |
| 09 | [Test Inventory](docs/plans/09-test-inventory.md) | Existing tests across all firmware repos |
| 10 | [AI Test Acceptance](docs/plans/10-ai-test-acceptance.md) | AI-powered test generation + release strategy |

### PFO Repo Analysis

| Document | Repos |
|----------|-------|
| [PFO Overview](docs/PFO/README.md) | Cross-repo maturity matrix |
| [Core Firmware](docs/PFO/batch1-core-firmware.md) | asp-fmc, amd-tee3_0, pmfw-firmware, mpio, mpifoe-fw |
| [Security & RAS](docs/PFO/batch2-security-ras.md) | art-security, dcgpu-esid, MPRAS-Kernel, MPRAS-Applets, nht-firmware |
| [Drivers & Tools](docs/PFO/batch3-drivers-tools.md) | VBL-TEE-Drv, sriov-dr, sw-security-tools, cp-mi400, pcie-cld-fw, ucie-fw |

## Implementation

| Module | Purpose |
|--------|---------|
| `merlin/baseline.py` | Golden baseline: parse SimNow logs, track register stability |
| `merlin/grounding.py` | Validate assertions against IFWI layout and baselines |
| `merlin/generator.py` | Generate grounded acceptance tests (no hallucination) |
| `merlin/runner.py` | Execute assertions, produce JUnit XML + markdown |
| `merlin/cli.py` | CLI interface: generate, collect, check, report, status |
| `configs/ifwi_layout.yaml` | MI450 PSP directory ground truth (15 components) |
| `acceptance_tests/` | Auto-generated acceptance YAMLs per component |
| `golden_baselines/` | Collected baselines from SimNow runs |
| `tests/test_merlin.py` | 31 tests covering the full pipeline |
