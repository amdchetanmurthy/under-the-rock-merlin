# MI450 IFoE (Infinity Fabric over Ethernet) Architecture

**Source:** https://amd.atlassian.net/wiki/spaces/CNS/pages/556183198/MI450+Architectural+Docs
**IFoE IP Team Page:** https://amd.atlassian.net/wiki/spaces/IFOE/pages/790200335 (access required)

---

## 1. What IFoE Is

IFoE (Infinity Fabric over Ethernet) is MI450's **GPU-to-GPU fabric networking subsystem**. It enables direct memory access between GPUs over Ethernet links, bypassing the host CPU. This is AMD's answer to NVLink — a high-bandwidth, low-latency fabric for AI training clusters.

IFoE lives on the **MID (Management/IO Die)** and is managed by the **MPIFOE** microprocessor (firmware: `fw-mpifoe`, PSP entry 0x01f3, 512K — the largest single firmware entry in the IFWI).

**Key property for CI/CD:** IFoE is a NEW subsystem for MI450 (not present in MI300X). It has the most complex firmware interactions and the most active development. Testing IFoE correctly is critical.

---

## 2. IFoE Subsystem Blocks

```
┌─────────────────────────────────────────────────────────────┐
│ IFoE SUBSYSTEM (on MID die)                                  │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ XRMAC    │  │ XRPFC    │  │ XRSEC    │  │ EX       │    │
│  │ (8 ports)│  │ Priority │  │ Security │  │ Ethernet │    │
│  │          │  │ Flow     │  │ (encrypt │  │ Switch   │    │
│  │ Ethernet │  │ Control  │  │  /auth)  │  │ (Vulcano)│    │
│  │ MAC      │  │          │  │          │  │          │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │          │
│       └──────────────┴──────┬───────┴──────────────┘          │
│                             │                                 │
│                      ┌──────┴──────┐                          │
│                      │ SDP         │                          │
│                      │ (Scalable   │                          │
│                      │  Data Port) │                          │
│                      └──────┬──────┘                          │
│                             │                                 │
│  ┌──────────┐        ┌──────┴──────┐                          │
│  │ MPIFOE   │←──SMN──│ SMN/RSMU   │                          │
│  │ (RISC-V) │        │ (Register  │                          │
│  │ FW:0x1f3 │        │  Access)   │                          │
│  └──────────┘        └─────────────┘                          │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ nBIF / SysHub — bridges IFoE to rest of SoC          │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Module Details

### 3.1 XRMAC — Ethernet MAC (8 ports)

**MAS:** SharePoint `AINICVulcano/.../XRMAC/MAS/`
**Supporting Docs:** SharePoint `AINICVulcano/.../XRMAC/MAS/Supporting Doc and Information/`

The MAC layer handles Ethernet frame transmission/reception across 8 ports. Each port connects to an XGMI PHY link.

**Key for testing:**
- Per-port PM statistics (tx/rx counters, error counts)
- PM Tick mechanism triggers atomic stat snapshots (see telemetry doc)
- `rx_port_pm_tick[7:0]` and `tx_port_pm_tick[7:0]` ports
- `pm_rdy` asserted within 300 AXI-lite clock cycles of `pm_tick`

### 3.2 XRPFC — Priority Flow Control

**MAS:** SharePoint `AINICVulcano/.../XRPFC/MAS/`
**Supporting Docs:** SharePoint `AINICVulcano/.../XRPFC/MAS/Supporting Doc and Information/`

IEEE 802.1Qbb Priority-based Flow Control. Manages traffic classes and prevents buffer overflow.

**Key for testing:**
- PFC pause frame generation/detection
- Per-priority traffic class counters
- Statistics via PM Tick (uses registers, not SRAMs — faster than XRMAC)

### 3.3 XRSEC — Security Block

**MAS:** SharePoint `AINICVulcano/.../XRSEC/MAS/`

Encryption and authentication for IFoE traffic. Ensures data integrity over Ethernet links.

**Key for testing:**
- Encryption enable/disable
- Authentication handshake
- Key rotation

### 3.4 EX — Ethernet Switch (Vulcano)

**Spec:** SharePoint `AINICVulcano/.../EX Tile/Vulcano EX spec.docx`

The Vulcano Ethernet Switch connects IFoE ports and routes traffic between GPUs.

### 3.5 SDP — Scalable Data Port

**Spec:** Cognidox `XN-202422-PS` (v1.5.0 — use this version)
**Also:** SharePoint `CIPDept/.../SDP spec/Soc15_ScalableDataPort_Specification_latest_1.50.pdf`
**Tile Spec:** SharePoint `AINICVulcano/.../PSDPX Tile/Vulcano PSDPX Tile Spec.docx`
**Owner:** Kisanagar, Surender <surender.kisanagar@amd.com>

SDP is the internal switch/exerciser in the IFoE subsystem. It carries data between GPU clients (CU, SDMA, etc.) and the Ethernet fabric.

**Key SDP design decisions (from OpenXGMI workshop):**
- Uses separate VCs for blue/brown, purple, black, and two VCs for red path
- `ReqStreamID` provides 16-bit requester ID
- Supports PASID/AT/T/XT for confidential compute
- 57-bit inbound VA, 52-bit outbound PA
- 128-bit max overhead for SDP control fields

### 3.6 MPIFOE — IFoE Management Processor

**TRM:** SharePoint `SECIPHWSWArch/.../secip3_mpIFOE_trm.docx`

RISC-V microprocessor that manages the IFoE subsystem. Runs Zephyr RTOS firmware (`fw-mpifoe`).

**Key for testing:**
- Boot sequence: MPIFOE firmware loaded from IFWI SPIROM (PSP entry 0x01f3)
- Link training and fabric topology discovery
- PM statistics collection via PM Tick interrupts
- IFoE RAS error handling

---

## 4. IFoE Architecture Documents Index

| Document | Type | Description | Owner |
|----------|------|-------------|-------|
| [IFoE_arch.docx](https://amdcloud.sharepoint.com/:w:/s/AINICVulcano/EfJHHfYEBRJAqgy3nxeP8QsBiRm_t4-T4AYBleQtc8O89g) | Word | Detailed IFoE architecture spec | David Riddoch |
| [2024-03 IFoE Architecture Overview.pptx](https://amdcloud-my.sharepoint.com/:p:/g/personal/driddoch_amd_com/Ef_a4jbU_4BMmOTCYHc186gBUdeH5esIFXM9nPbBXwNg9A) | PPT | High-level architectural view | David Riddoch |
| [IFoE-Port-For-MID-MI400.pptx](https://amdcloud.sharepoint.com/:p:/r/sites/AINICVulcano/Shared%20Documents/IFoE-Port-SS/IFoE-Port-For-MID-MI400.pptx) | PPT | Block diagram of IFoE port into MI450's MID | David Riddoch, Sridhar Rudraraju |
| [2024-08 IFoE Day in the Life.pptx](https://amdcloud-my.sharepoint.com/:p:/g/personal/driddoch_amd_com/EYdzADYL7IhLkHokNPxGHBkBQ24i6E1w7WDL2S4641QI8w) | PPT | Packet transmission walkthrough | David Riddoch |
| [IFoE_MAS.docx](https://amdcloud.sharepoint.com/:w:/s/AINICVulcano/EWBX5hWj6E9KneFxkv1wx9oB_n3nNWGtYe2RZAAz-argWA) | Word | Micro Architecture Spec | — |
| [AMD E6A Manual](https://cognidox.xilinx.com/cgi-perl/part-details?partnum=XN-202659-PR) | Cognidox | E6A Reference Manual | — |
| [AMD E6A User Guide](https://cognidox.xilinx.com/cgi-perl/part-details?partnum=XN-202658-PS) | Cognidox | E6A User Guide | — |
| [secip3_mpIFOE_trm.docx](https://amdcloud.sharepoint.com/:w:/r/sites/SECIPHWSWArch/_layouts/15/Doc.aspx?sourcedoc=%7B0BAAF070-019E-473F-ABED-A944EAAD60B6%7D) | Word | MP-IFoE Technical Reference Manual | — |

---

## 5. IFoE Integration Status for CI/CD

From the CRD Ingredients page (https://amd.atlassian.net/wiki/spaces/DCGPUVAL/pages/1076373879):

> "The IFoE will be a new component to the ROCm stack build (per Dec 15, 2025 communication). Not yet decided: either separate (like amdgpu driver and GIM driver, paired with ROCm build) or integrated as part of ROCm build."

**Impact on Merlin:**
- IFoE firmware testing requires the **2G IFoE SimNow model** (`aransas_mi450_2g_m112_ifoe.bsd`) — not the default M112 model
- IFoE link-up is a critical test assertion — if IFoE doesn't train, multi-GPU workloads fail
- MPIFOE firmware is Zephyr-based with Twister test framework — can run unit tests in `native_sim`
- The `firmware/mpifoe-fw/tests/` directory has IFoE RAS and TLM testcases

**SimNow test configs for IFoE changes:**
- Use `mi450_0p1g2mid2aid8xcd_unsecure` (M228) or `mi450_2g_m112_ifoe` (2G) model
- NOT the default M112 single-die model
