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
