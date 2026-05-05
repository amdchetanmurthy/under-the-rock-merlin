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
