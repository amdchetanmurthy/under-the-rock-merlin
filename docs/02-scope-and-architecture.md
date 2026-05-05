# UnderTheRock - Scope and Architecture

## Initial Scope: EAM BKC

### In-Scope Components

1. **IFWI Firmware** (PFO IFWI Team)
   - PSP (Platform Security Processor)
   - MPIO (Multi-Port I/O)
   - PMFW (Power Management Firmware)
   - RAS (Reliability, Availability, Serviceability)
   - UMC (Unified Memory Controller)
   - VBL (Video BIOS Loader)

2. **Kernel Driver** (RTG Kernel Team)
   - amdgpu kernel driver

3. **ROCm** (ROCm Teams)
   - Runtime
   - Libraries
   - Frameworks

### Future Integration (Planned)
- CPU BKC
- HPM (Host Platform Management)
- DCSCM (Data Center Secure Control Module)
- NIC (Network Interface Card)
- Storage
- Non-EAM Compute
- AIFM (AI Fabric Manager)
- Tools, Diags
- RMC/Switches
- AI NIC BKC (binary artifact from Pensando)
- SwitchOS (binary artifact, consumed as-is)

## Key Terminology

| Term | Definition |
|------|-----------|
| **IFWI** | Integrated Firmware Image — complete firmware package |
| **BKC** | Boot Kit Configuration — validated IFWI + kernel + ROCm stack |
| **LKG** | Last Known Good — daily promoted validated baseline |
| **theRock** | Existing unified build harness for ROCm (https://github.com/rocm/therock) |
| **EAM BKC** | Enterprise AI Module BKC (IFWI + kernel + ROCm) |
| **I×K×R** | IFWI × Kernel × ROCm combination matrix |

## Architecture Decisions

- Build mechanics, repo structure, and integration approach are **TBD** — determined by tiger team during PoC
- Super-build approach: consolidating ~65 firmware components into a unified build system
- GitHub Actions (GHA) as the single CI platform
- Manifest-driven BKC with `lkg-manifest.yaml`

## Integration with theRock

UnderTheRock and theRock share LKG promotion:
- Joint nightly decision: All 18 nightlies contribute to LKG quorum
- Single `lkg-manifest.yaml` contains IFWI + kernel + ROCm SHAs
- Coordinated gardening: IFWI, kernel, ROCm gardeners collaborate

## Super-Build Components (~65 firmware packages)

Each firmware package needs:
- Source repo access and signing procedures
- Build recipe conversion to super-build compatible format
- Configurable build directory per component
- Sub-module checkouts on the correct branch
- Binary artifact names matching IFWI component names
- NFS/PVC mounts (assumed on CI and local environments)
- Identification of extra symlinks not in firmware repo
- Canonical CI workflow identification
- Secrets / Artifactory / PyPI extra-index names
- OS/kernel edge cases (`get_os` / `FAKEOS` / `sitename`, old `.so` sonames)
- Signing / release policy documentation
- Operational defaults (sensible `-j`, timeouts, minimal vs full CI builds)

## Repos

- **Main repo:** `git@github.amd.com:PFO/under-the-rock.git` (requires TechProtect access to pfo.readonly)
- **TechProtect access:** https://techprotect.amd.com/access/tech_project_family.php?hname=family_UserGroupFamily_handler&fk0=213&master_viewmode=0
- **Implementation plan:** `docs/current_draft_plan.md` in the repo (30K+ words)
- **Firmware integration guide:** `docs/integrate-firmware-package-skill.md`
