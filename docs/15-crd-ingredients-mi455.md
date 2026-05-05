# MI455 CRD Ingredients

**Source:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/861331250/MI455+CRD+Ingredients
**Space:** Datacenter GPU Validation | **Owner:** Montalvo, Javier | **Last Modified:** Apr 07, 2026

## Overview

The MI455 CRD (Customer Reference Design) Ingredients page tracks all hardware/software components needed for a complete MI455 system validation stack. It organizes the BKC into 7 major component areas with owners and links to detailed sub-pages.

## Component Owners & BKC References

| # | Component | Owner | BKC Reference | Notes |
|---|-----------|-------|---------------|-------|
| 1 | CPU (BIOS, BMC) | Kulkarni, Yogesh | [Server Debug BKC](https://amd.atlassian.net/wiki/spaces/SERVERDEBUG/pages/877921104) | BMC/FPGA info at [page 877920428](https://amd.atlassian.net/wiki/spaces/SERVERDEBUG/pages/877920428) |
| 2 | EAM (GPU Module) | Montalvo, Javier | [EAM BKC](https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/601297861), [IFWI](https://amd.atlassian.net/wiki/spaces/PFO/pages/878957687) | Includes IFWI, AMC, EROT, PHC, AMC FPGA, EAM FPGA1, EAM FPGA2, RM |
| 3 | AIFM: Switch FW & Drivers | Mehta, Ambrish (NTSG) | [Platform Validation](https://amd.atlassian.net/wiki/spaces/PLATVAL/pages/743243935) | Network test plan on SharePoint |
| 4 | AI-NIC | Chhotani, Kaushik (Pensando/Broadcom) | — | Derek T / Andy T also involved |
| 5 | Platform Host Software Stack | Huang, Allen / Yanez, Jorge | — | — |
| 6 | Tools | Stavridis, John | MI450 Tools List (SharePoint) | — |
| 7 | Diags | Ciligot, Maurice | — | — |

## Child Pages — Detailed Component Breakdown

### MI450 CRD Ingredients Diagram
- **Page ID:** 1013817664
- **Content:** draw.io diagrams showing component relationships (visual only)
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1013817664

### MI450 CRD Block Diagram
- **Page ID:** 1102941349
- **Content:** Block diagram (visual only)
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1102941349

### MI450 GPU / EAM
- **Page ID:** 1049734527
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1049734527
- Sections: Resources, Components
- **Sub-pages:**
  - **MI450 IFWI** (page 1049543506): Links to SWPMTO build pages, IFWI schedule. Lists firmware components:
    - PSP Firmware (Bootloader, Anti Rollback, WAFL Init, RAS, XGMI DF, Boot Audit, SPIROM Model, RAS MCA, IP Discovery, XGMI Phy)
    - Security Policy
    - Power Management Firmware (PM FW)
    - MPIO Firmware
    - XCD Firmware, UMC Firmware, BAM, DF RIB
    - XGMI Topology Firmware
    - Video Bootloaders (VBL Config Table, APCB Event Log, UBL Firmware, ROM Strap)
    - ASIC Keys (Public Keys for GPU unlock, CSM, Softfuse Override)
    - ASIC Settings (Register programming parameters)
    - SKU Config Settings (CRB/Board Config, Frame Buffer, Memory Tuning, SPI ROM Details)
  - **ROCm, Kernel Driver & Virtualization** (page 1050232995): Links to MLSE ROCm resources at pages 744191990 and 744180108. Sections for AMDGPU & Linux and Virtualization.

### MI450 PHC
- **Page ID:** 1306460706
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1306460706
- Resources link: https://amd.atlassian.net/wiki/spaces/DCGAPHWD/pages/804261614

### MI450 AMC & eROT
- **Page ID:** 1305901038
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1305901038
- Resources link: https://amd.atlassian.net/wiki/x/R3nwLw

### MI450 IFoE (Infinity Fabric over Ethernet)
- **Page ID:** 1076373879
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1076373879
- Key information (as of Dec 15, 2025):
  - IFoE will be a **new component to the ROCm stack build**
  - Not yet decided: either separate (like amdgpu driver and GIM driver, paired with ROCm build) or integrated as part of ROCm build
- Resources:
  - https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/906950252
  - https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1303658384

### MI450 Build & Release Tools, Utilities, Procedures
- **Page ID:** 1062406770
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1062406770
- **Tools & Utilities:**
  - Jenkins Dashboard: http://rocm-ci.amd.com/
  - IFWI Builder: http://rocm-ci.amd.com/
  - Analyze My Instincts: https://analyze-my-instinct.azr.dcgpu-infra.amd.com/
  - MI450 RAP Compliance Tool: https://rapctmi450.amd.com/ (docs at page 1001661961 in SECUREE space)
- **SOPs:**
  - https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/601036537
  - https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1129480232

### MI450 EAM1 & EAM2 FPGA
- **Page ID:** 1306460741
- **URL:** https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1306460741
- Resources: https://amd.atlassian.net/wiki/spaces/DCGAPHWD/pages/1047560839

## Key Takeaways for UnderTheRock

1. **EAM BKC is the primary integration target** — IFWI, AMC, EROT, PHC, FPGAs all part of EAM
2. **IFoE integration is undecided** — may be separate or part of ROCm build
3. **7 component areas** need coordinated BKC versioning
4. **Multiple Confluence spaces** hold BKC info: DCGPUVAL, PFO, SERVERDEBUG, PLATVAL, DCGAPHWD, SWPMTO, MLSE, SECUREE
5. **Build tools** are at rocm-ci.amd.com (Jenkins-based) — UnderTheRock aims to migrate to GitHub Actions
