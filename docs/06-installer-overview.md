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
