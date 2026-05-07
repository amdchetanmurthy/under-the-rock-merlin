# UnderTheRock Installer - Overview and Architecture

## What Is the Installer?

The Under The Rock Installer delivers the complete compute tray software stack — firmware, kernel driver, and ROCm userspace — in one orchestrated flow for MI455X Helios compute trays.

### How It Relates to the Broader UnderTheRock Program

- **UnderTheRock program** = _building_ firmware from source (super-build, LKG promotion, CI gates)
- **Installer** = _deploying_ validated BKC stacks to hardware

## Architecture Layers

| Layer | Tool | Mechanism |
|-------|------|-----------|
| Firmware (10 OOB components) | `amdfwupd` CLI (Python/Click) | Redfish PLDM bundles, out-of-band via BMC |
| Kernel driver (amdgpu-dkms) | Ansible role `rocm_gpu_driver` | APT package install, in-band via SSH |
| ROCm userspace | Ansible role `rocm_userspace` | APT package install, in-band via SSH |

### Deployment Flow

The Ansible `site.yml` playbook sequences all three:
1. **Firmware first** (OOB — no host OS needed) — happens via BMC Redfish before the host is even booted
2. **Driver** (in-band — requires host OS running)
3. **ROCm** (in-band — requires host OS running)

## Scope and Roadmap

### v0 (Current — POC)
- **EAM/AMC PLDM bundle delivery** — single firmware subsystem (10 sub-components), single compute tray
- `amdfwupd` CLI commands: `show`, `plan`, `update` via Redfish
- Ansible roles for driver and ROCm (scaffolded, APT-based)
- Mock BMC test infrastructure (HTTPS + HTTP, mock SSH server)

### v1 (Planned)
- **Full compute tray** — non-EAM PLDM components (BIOS, CPLDs, PCIe Switch) + BMC firmware

### v2 (Planned)
- **Ansible multi-tray orchestration** — fleet-level update strategies across 8 compute trays per rack
- ACC (AMD Cluster Controller) integration for fleet scale

## Repos

- **Workspace repo:** `git@github.amd.com:PFO/under-the-rock-team.git`
- **Installer repo:** `git@github.amd.com:PFO/under-the-rock-installer.git` (lives inside workspace's `projects/` directory)

### Workspace Submodules (Read-Only References)

| Submodule | Path | Purpose |
|-----------|------|---------|
| Platypi | `refs/technical/conductor/platypi/` | AMD internal BMC automation CLI — study Redfish patterns |
| ACC Workflows | `refs/technical/acc/acc-workflows/` | AMD Cluster Controller Ansible workflows |
| NVIDIA open-nvfwupd | `refs/external/open-nvfwupd/` | Competitor firmware update CLI — direct comparison target |

## Key Technologies

- **Python/Click** for CLI (`amdfwupd`)
- **Ansible** for orchestration (`site.yml` playbook)
- **Redfish** for out-of-band firmware updates via BMC
- **PLDM** (Platform Level Data Model) for firmware bundles
- **Flask** for mock BMC test infrastructure
- **pytest** for testing (~90 tests)
- **ruff** for linting

---

# UnderTheRock Installer - Developer Setup and Workflow

## Prerequisites

- Python 3.10+ (CI runs on 3.12)
- Git with SSH access to `github.amd.com`
- AWS dev VM (see Dev Machine Setup) or any Linux machine with Python

## Setup Steps

### Step 1: Clone Workspace Repo

```bash
git clone git@github.amd.com:PFO/under-the-rock-team.git
cd under-the-rock-team
git submodule update --init
```

Submodule init pulls three reference codebases (read-only, do not modify):
- **Platypi** (`refs/technical/conductor/platypi/`) — Redfish patterns, `utils/redfishtool.py`, `platforms/platform_base.py`
- **ACC Workflows** (`refs/technical/acc/acc-workflows/`) — `workflows/bkc_upgrade/` for BMC firmware update tasks
- **NVIDIA open-nvfwupd** (`refs/external/open-nvfwupd/`) — `nvfwupd/rf_target.py` for Redfish flow, `nvfwupd/pldm.py` for PLDM parsing

### Step 2: Clone Installer Project

```bash
cd projects
git clone git@github.amd.com:PFO/under-the-rock-installer.git
cd under-the-rock-installer
```

### Step 3: Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Runtime deps:** `click`, `requests`, `jsonschema`, `paramiko`
**Dev deps:** `pytest`, `pytest-xdist`, `flask` (mock BMC), `ruff` (linter)

### Step 4: Verify

```bash
pytest -v            # Run all tests (~90 tests, should all pass)
ruff check python/ tests/   # Lint check
amdfwupd version     # Verify CLI is installed
```

All tests run against in-process Flask mock BMCs and a mock SSH server — no real hardware needed.

## Development Workflow

### Running Tests

```bash
pytest                      # Run all tests
pytest -v --tb=long         # Verbose with full tracebacks
pytest -k test_planner      # Run a specific module
pytest -n auto              # Parallel execution (CI mode)
```

### Linting

```bash
ruff check python/ tests/       # Lint check
ruff check --fix python/ tests/  # Auto-fix
```

Ruff config: 100 char line length, Python 3.10 target.

### CI Pipeline

GitHub Actions (`.github/workflows/ci.yml`), runs on push/PR to `main`:

1. **test** job: `ruff check` + `pytest -v --tb=long -n auto` (Ubuntu 24, Python 3.12)
2. **lint** job: `ruff check` + Ansible YAML validation

Dependabot runs weekly for pip dependencies and GitHub Actions versions.

### Credential Management

BMC credentials are always passed via environment variables:

```bash
export AMDFWUPD_BMC_USER=root
export AMDFWUPD_BMC_PASS=<password>
```

Same credentials used for both SSH tunnel (to reach AMC) and Redfish authentication. CLI refuses to run if unset. In Ansible, credentials are injected via Ansible Vault.

## Claude Code Integration (Optional)

The workspace includes extensive AI agent infrastructure:

- `CLAUDE.md` files at workspace and installer levels
- **5 skills** (in `.claude/commands/`):
  - `/pdf-guide` — page-range index for all reference PDFs
  - `/research` — cross-reference search across all workspace sources
  - `/add-source` — workflow for adding new reference material
  - `/summarize-pdf` — structured PDF summary generator
  - `/update-gap` — gap analysis maintenance
- **3 path-scoped rules** (in `.claude/rules/`) — auto-load context for Platypi, ACC, nvfwupd submodules

### Using Claude Code

```bash
cd under-the-rock-team
claude
```

Use `/pdf-guide` before reading any PDF for page ranges.

---

# UnderTheRock Installer - Reference Documents

## Project Documents

| Document | Location | Description |
|----------|----------|-------------|
| Executive Brief | `analysis/executive_brief.md` | Strategic context and project overview |
| v0 Design Proposal | `designs/v0_design_proposal.md` | Technical architecture for v0 |
| Requirements Map | `analysis/requirements/comprehensive_requirements_map.md` | Full PRD-derived requirements |
| Component Gaps | `analysis/gaps/component_and_tooling_gaps.md` | Per-component gap analysis |
| ACC Gap Analysis | `analysis/gaps/acc_gap_analysis.md` | How ACC fits (or doesn't) for v0 |
| Installer README | `projects/under-the-rock-installer/README.md` | CLI usage, recipe format, exit codes |
| Installer CLAUDE.md | `projects/under-the-rock-installer/CLAUDE.md` | Code conventions and architecture decisions |

## PRDs (in `refs/prds/`)

- **Helios Installer PRD** — Primary requirements document
- **AMD Helios Firmware Packaging and Update PRD** — Packaging pipeline requirements
- **Helios-R Installer Requirements Readout** — Requirements review output

## Technical References

| Reference | Location | What to Study |
|-----------|----------|---------------|
| Platypi | `refs/technical/conductor/platypi/` | `utils/redfishtool.py` for Redfish patterns, `platforms/platform_base.py` for update orchestration |
| NVIDIA nvfwupd | `refs/external/open-nvfwupd/` | `nvfwupd/rf_target.py` for Redfish flow, `nvfwupd/pldm.py` for PLDM parsing |
| ACC Workflows | `refs/technical/acc/acc-workflows/` | `workflows/bkc_upgrade/` for BMC firmware update tasks |

## Confluence References

| Page | URL | Description |
|------|-----|-------------|
| Mkm EAM BKC PLDM Update HOWTO | https://amd.atlassian.net/wiki/spaces/DCGPUCEVAL/pages/1351926096 | Official EAM update procedure — ground truth for update flow |
| Helios-R FW Update (EVT2) | https://amd.atlassian.net/wiki/spaces/DPEGFWDOC/pages/1526785233 | Helios-R EVT2 firmware update guide with Redfish commands |
| Helios-R 1P1G Compute Tray | https://amd.atlassian.net/wiki/spaces/DPEGSE/pages/1624422284 | 1P1G tray FW update procedures, board IDs, EAM detection |
| Helios-P META Anacapa | https://amd.atlassian.net/wiki/spaces/DPEGFWSW/pages/1171835676 | Helios-P (Anacapa BMC) reference — different platform, same EAM flow |
| BKC T26.03.03 | https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1599270922 | Current recommended BKC release for Rev C hardware |
| MI4XX Bundle Generation CLI | https://amd.atlassian.net/wiki/spaces/DCGPUCEVAL/pages/1132562746 | How to use the Bundler tool |
| MI455 Planned Releases | https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/601297861 | Latest Rev C single-EAM releases |
