# MI450 SoC Architecture Overview

**Source:** https://amd.atlassian.net/wiki/spaces/CNS/pages/556183198/MI450+Architectural+Docs
**Note:** Architecture specs were in flux as of Aug 2024. Always refer to source documents for latest versions.

---

## 1. Chiplet Architecture

MI450 is a multi-chiplet GPU SoC with the following die types:

| Chiplet | Abbreviation | Function | Count (M228 full config) |
|---------|-------------|----------|--------------------------|
| **MID** | Management/IO Die | Platform management, PCIe, IFoE, nHT, SMN | 2 |
| **AID** | Accelerator IO Die | Memory controllers (UMC), HBM interfaces, XGMI | 2 |
| **XCD** | Compute Die | Shader engines, compute units, L2 cache | 8 |

### SimNow Model Configurations (from actual BSDs)

| Model | Config | BSD File |
|-------|--------|---------|
| M112 | 1 MID, 1 AID, 2 XCD | `aransas_mi450_1mid1aid2xcd.bsd` |
| M222 | 2 MID, 2 AID, 2 XCD | `aransas_mi450_2mid2aid2xcd.bsd` |
| M228 | 2 MID, 2 AID, 8 XCD | `aransas_mi450_2mid2aid8xcd.bsd` |
| A+A (CPU+GPU) | Venice CPU + MI450 | `aransas_1P1G_W21_M112.bsd` |
| 2G IFoE | 2 GPUs with IFoE | `aransas_mi450_2g_m112_ifoe.bsd` |
| FEAS (MPs only) | MPs only, no SoC memory | `feas_mpifoe_mi450_mid.bsd` |

*Source: SimNow scripts from `github.amd.com/PFO/simnow-scripts/tree/main/mi450`*

---

## 2. Firmware Components on Each Chiplet

### MID (Management/IO Die)

The MID hosts most of the firmware microprocessors:

| MP | Firmware | PSP Entry | fw-* Target | Function |
|----|----------|-----------|-------------|----------|
| MPASP | ASP FMC | 0x0001 | fw-asp-fmc | First Mutable Code (PSP boot chain entry) |
| MPART | ART Security | 0x00ab, 0x00ac | fw-art-security | AMD Root of Trust (FMC + Runtime) |
| MP1 | PMFW MID | 0x0008 | fw-pmfw | Power management (MID die) |
| MPIFOE | MPIFoE FW | 0x01f3 | fw-mpifoe | IFoE management processor |
| MPNHT | NHT FW | 0x01e0 | fw-mpnht | nHT controller |
| MPRAS | MPRAS Kernel | 0x006b | fw-mpras-kernel | RAS management |
| — | MPIO FW | 0x005d | fw-mpio | Multi-purpose I/O (PCIe, XGMI link training) |
| — | TEE TOS | 0x0002 | fw-amd-tee3 | Trusted Execution Environment |
| — | eSID | 0x0157-015f | fw-dcgpu-esid | Embedded Secure ID |
| — | Caliptra | 0x00a8 | fw-caliptra-sw | Root of Trust |

### AID (Accelerator IO Die)

| MP | Firmware | PSP Entry | fw-* Target | Function |
|----|----------|-----------|-------------|----------|
| MP5 AID | PMFW AID | 0x01ea | fw-pmfw | Power management (AID die) |
| — | UMC FW | 0x004f | (Perforce) | Unified Memory Controller |
| — | IMU Instruction | 0x009b | fw-pmfw | Inertial Measurement Unit code |
| — | IMU Data | 0x009c | fw-pmfw | IMU data |

### XCD (Compute Die)

| MP | Firmware | PSP Entry | fw-* Target | Function |
|----|----------|-----------|-------------|----------|
| MP5 XCD | PMFW XCD | 0x1051 | fw-pmfw | Power management (XCD die) |

---

## 3. Data Paths

From the OpenXGMI Workshop Minutes (https://amd.atlassian.net/wiki/spaces/RTGMI100/pages/639297305):

```
┌─────────────────────────────────────────────────────────────────┐
│ MI450 DATA PATHS (Color-coded from OpenXGMI architecture)       │
│                                                                   │
│ RED PATH — PCIe Traffic                                          │
│   Host CPU ←→ PCIe Root Port ←→ MI450 ←→ AINIC (endpoints)      │
│   Carries: Config, Interrupts, MMIO                              │
│   Uses: VC0/VC1, treats AINIC as PCIe endpoint                   │
│                                                                   │
│ BLUE PATH — GPU Cross-Domain (NPA via GPUVM)                    │
│   GPU ←→ OpenXGMI ←→ Remote GPU/AINIC ←→ HBM                   │
│   Carries: nHToE traffic, GPU memory access                     │
│   Uses: GPUVM address translation, UTC L1/L2                    │
│   NodeID part of address, translated to MAC by AINIC             │
│                                                                   │
│ PURPLE PATH — RDMA via IOMMU                                    │
│   XRNIC ←→ OpenXGMI ←→ Remote memory                            │
│   Carries: RDMA traffic (memory managed by IOMMU)               │
│   Uses: AT=10b bypass or AT=00b untranslated                    │
│                                                                   │
│ BLACK PATH — GPU In-Domain (SPA)                                │
│   GPU ←→ Same-node GPU ←→ System memory                         │
│   Carries: System Address transactions between GPUs              │
│   Uses: Direct SPA addressing                                    │
│                                                                   │
│ BROWN PATH — Device Memory Downstream                           │
│   Return path for blue path requests                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Design Decisions (From OpenXGMI Workshop)

These architectural decisions directly impact firmware testing:

1. **Root Port in MI450, Endpoint in AINIC** — AINIC looks like an external PCIe device to MI450
2. **nHT Controller is a separate MP** — clone of existing MP with 256KB RAM, firmware loaded from SPI ROM at boot
3. **OpenXGMI uses same link training as XGMI and PCIe6** — no special firmware intervention needed
4. **SMN does NOT go over OpenXGMI** — register programming is local only
5. **XGMI must support up to 128 GHz** (increased from 112.5 GHz for AINIC bandwidth)
6. **11-bit tags** in DXS, DMA_BE, and GL2 (due to long nHToE latency with Tomahawk 6)
7. **Unpinned memory required** for Linux upstream — must support Remote Presence Check (RPC)
8. **MI450 connected to Venice SP7 is NOT supported** — only SP8 and later
9. **No FW download over XGMI** — one SPI Flash per 4 AINICs, board area not a concern

*Source: https://amd.atlassian.net/wiki/spaces/RTGMI100/pages/639297305*

---

## 5. High-Level Platform Design Documents

All owned by Mehta, Nisarg <nisarg.mehta@amd.com>:

| Document | SharePoint Path |
|----------|----------------|
| Platform Architecture | `MI400StackTeam/.../MI450 Platform SysHLD.pptx` |
| Platform Design | `MI400StackTeam/.../MI450_SystemHLD-PlatformDesign-30thJuly25.pptx` |
| Platform Power | `MI400StackTeam/.../MI450X SySHLD Power Delivery 2024-July.pptx` |
| Platform Mechanical | `MI400StackTeam/.../MI450 Mechanical HLD.pptx` |
| Platform Thermals | `MI400StackTeam/.../MI450 Thermal HLD.pptx` |
| Platform SI | `MI400StackTeam/.../MI400 System HLD - SI_v04.pptx` |
| SOC Architecture | `MI400StackTeam/.../MI450_SystemHLD_SOC_Arch_update.pptx` |
| Package | `MI400StackTeam/.../MI450 Packaging System HLD document.pptx` |
| Emulation | `MI400StackTeam/.../MI450 Emulation Plan System HLD.pptx` |
| Program Management | `MI400StackTeam/.../MI400 System HLD - PMO.pptx` |

---

## 6. Processor Programming Reference (PPR)

The authoritative register specification for MI450:

**PPR Web:** https://mpdwww.amd.com/pprweb/gpu/MI450/A0/int/pprweb/

The PPR defines every register address, bit field, and default value. It is the source of truth for:
- SimNow register assertions (grounding)
- FW status register addresses (MPASP_FW_STATUS at 0x034000d8)
- Fuse definitions (ART_LC_STATE_MFG0/MFG1, ART_RKEK, etc.)
- IP block enumeration (IP Discovery Binary, PSP entry 0x20)

*Source: https://amd.atlassian.net/wiki/spaces/CNS/pages/556183198*
