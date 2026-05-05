# UnderTheRock - Component Build Leads Requirements

## What Build Leads Must Provide

Each component build lead needs to provide the following to the UnderTheRock build team:

### 1. BKC Module Registration
Add all modules to the BKC module spreadsheet with details:
- BKC it belongs to
- Build Engineer name
- Source Repo location
- Build Recipe
- Dependencies to build

### 2. Source Repo Access
- Provide source repo accesses to UnderTheRock build team
- Provide signing procedures
- If source repo isn't in GitHub, provide a **mirror**

### 3. Build Reproduction
- Build engineer help reproduce the builds in "UnderTheRock" super-repo
- Contact: **Chris Sosa**

### 4. Build Configuration Details
- **Configurable build directory** per component
- **Sub-module checkouts** — double-check correct branch
- **Binary artifact names** must match the IFWI component names
- **NFS / PVC mounts** assumed on CI and local environments
- **Extra symlinks** not in the firmware repo relied on by the build
- **Canonical CI workflow** for the given package

### 5. Infrastructure Requirements
- **Secrets / Artifactory / PyPI extra-index**: names and which steps need them (NOT values)
- **OS/kernel edge cases**: `get_os` / `FAKEOS` / `sitename`, old `.so` sonames, paths CI never hits on vanilla Ubuntu
- **Signing / release policy**: unsigned local OK or must mirror CI; downstream expected artifact layout
- **Operational defaults**: sensible `-j`, timeouts, "minimal" build (skip sign/tests) vs full CI parity

## Firmware Integration Guide

A formal guide for integrating firmware packages is available (PR in progress):
- `under-the-rock/docs/integrate-firmware-package-skill.md`
- Branch: `d46b5aa44e0d9061761571c6f37c9d120b8bfe2e`

## BKC Module Spreadsheet

Location: SharePoint (AIGROCm > NPI > NPI Ops > Firmware > Instinct > BKC Modules.xlsx)
Tracks components for MI450 BKC.
