# MI450 Interconnects: SMN, nHT, nBIF, OpenXGMI, Root Port

**Source:** https://amd.atlassian.net/wiki/spaces/CNS/pages/556183198/MI450+Architectural+Docs

---

## 1. SMN — System Management Network

**MAS:** SharePoint `SIPControlFabric/.../smn15-interconnect-mas.docx`

SMN is the **control network for register programming** across all IP blocks in the SoC. Every firmware component uses SMN to read/write registers.

**Key properties:**
- SMN does NOT go over OpenXGMI (local to each die)
- Uses FLIT-based format internally
- Register accesses from firmware (MPs) go through RSMU → SMN → target IP
- SMN mapping for MI450 is in Perforce: `//sysip/smn/smn-15/branches/smn15_mi450_basedie/src/meta/features/scf_smn_map/variant/cumberland/scf_smn_map.json`

**Impact on testing:**
- Every SimNow register read/write (`regsmgr.AddForce`, `ad.m`) goes through the SMN model
- SMN connectivity is implicitly tested by any SimNow boot — if SMN is broken, nothing works
- The `MPASP_FW_STATUS` register at `0x034000d8` is read via SMN

### SMN-MP (General MP Info)

**MAS:** SharePoint `SECIPHWSWArch/.../secip3_mp_mas.docx`

Documents SMNNB and SMNIF — the SMN interfaces in the general microprocessor architecture. All MPs (MPASP, MPART, MPIFOE, etc.) use the same SMN interface pattern.

---

## 2. RSMU — Remote System Management Unit

**MAS:** SharePoint `SIPControlFabric/.../CF2_Public/IP MAS/RSMU/remote_smu_mas.docx`

RSMU is the **access point** of the control network. It converts from SMN FLIT format to regular AXI interface for IP internal registers.

Every IP block has an RSMU instance. Firmware accesses IP registers through RSMU.

**Impact on testing:**
- RSMU initialization is part of PSP boot chain
- Security policies (PSP entries 0x24, 0x45, 0x101) configure RSMU access permissions
- SimNow models the RSMU as part of each IP block

---

## 3. nHT — Network Hyper Transport

**Spec:** SharePoint `aradu/.../OpenXGMI and nHT NBIO Specification.docx`
**Owner:** Sodke, Rick <Rick.Sodke@amd.com>

nHT is the **data transport layer** over OpenXGMI links. It carries GPU-to-GPU memory transactions.

**Key properties (from OpenXGMI workshop):**
- Separate MP (clone of existing MP, 256KB RAM)
- Firmware loaded from SPI ROM at early boot (PSP entry 0x01e0, `fw-mpnht`)
- Supports Remote Presence Check (RPC) for unpinned memory (required for Linux upstream)
- Uses UTC (Unified Translation Cache) at L2 for address translation
- Pinned memory attribute in GPUVM allows skipping RPC

**nHT Controller FW decisions:**
- nHT Controller is a separate CPU with its own firmware
- Code is in SPI ROM and loaded at early boot
- Non-disruptive FW update is desired but not nHT-specific (tabled for MI400 platform-level solution)
- No need for FW download over XGMI

**Impact on testing:**
- `fw-mpnht` boot is testable in SimNow M228 or A+A models
- nHT link training requires XGMI PHY (PSP entry 0x42)
- IFoE vs nHT are different firmware paths on the same physical links

---

## 4. nBIF / SysHub — NBIF and System Hub

**MI450 Delta:** SharePoint `BIF/.../nBIF_SHUB_MI400_delta.doc`
**IFoE Config:** SharePoint `AINICVulcano/.../MI450A0_nBIF_SYSHUB__IFoE__configuration_v0.1.docx`
**Base MAS:** SharePoint `BIF/.../NBIF_SHUB_MAS.docx`
**Brief Intro:** SharePoint `BIF/.../nBIF_SHUB Brief Introduction from Shuming 2.pptx`
**Reset Spec:** SharePoint `BIF/.../BIF_reset_implementation_spec.docx`
**Owner:** Luo, Sidney <Sidney.Luo@amd.com>

nBIF/SysHub bridges the IFoE subsystem to the rest of the SoC. The MI400 delta document has a section on IFoE at the end.

**Key properties:**
- Handles reset sequences (documented in `BIF_reset_implementation_spec.docx`)
- IFoE configuration requires specific nBIF/SysHub programming
- MI300 delta doc available for reference (different from MI400)

**Impact on testing:**
- nBIF reset handling is critical for warm/cold reset testing
- IFoE link-up depends on correct nBIF configuration
- Reset tests in nightly tier should exercise nBIF reset paths

---

## 5. OpenXGMI

**Workshop Minutes:** https://amd.atlassian.net/wiki/spaces/RTGMI100/pages/639297305

OpenXGMI is the **physical link layer** connecting MI450 GPUs to each other and to AINICs. It extends XGMI to support Ethernet-class traffic.

### 5.1 Data Path Color Coding

| Path | Color | Source → Destination | VC | Use Case |
|------|-------|---------------------|-----|----------|
| PCIe | Red | Host CPU ↔ AINIC (via MI450 Root Port) | VC0/VC1 | Config, interrupts, MMIO |
| GPU cross-domain | Blue (upstream) / Brown (downstream) | GPU → Remote GPU/AINIC → HBM | Separate VC | nHToE, GPUVM-managed memory |
| RDMA | Purple | XRNIC → Remote memory (IOMMU-managed) | Separate VC | RDMA from NIC |
| GPU in-domain | Black | GPU → Same-node GPU → System memory | Separate VC | System Address transactions |

### 5.2 SDP Channel Fields (From Workshop Table)

| Field | PCIe Tx/Rx | Device Mem Tx | Device Mem Rx | Sys Mem Rx | nHT Bypass |
|-------|-----------|---------------|---------------|------------|------------|
| ReqTag | 10 bits | 12 | 12 | 12 | 12 |
| ReqAddr | 57 bits | 56 | 52 | 57 | 56 |
| ReqStreamID | 16 bits | 16 | 16 | 16 | 0 |
| ReqPASID | 20 bits | 0 | 0 | 20 | 0 |
| **Total** | **134 bits** | **109** | **104** | **133** | **91** |

### 5.3 Architectural Decisions Affecting Firmware

| Decision | Impact on Firmware |
|----------|-------------------|
| Root Port in MI450, EP in AINIC | MPIO configures PCIe RP topology |
| SMN does NOT cross OpenXGMI | Each die manages its own registers |
| XGMI up to 128 GHz (was 112.5) | MPIO/nHT PHY training parameters changed |
| 11-bit tags (was 10) | DXS, DMA_BE, GL2 updated |
| Must support unpinned memory | Remote Presence Check in nHT firmware |
| Presence detect via bootstraps/BMC, not XGMI | Boot sequence doesn't depend on link state |

---

## 6. Root Port / AFL-RP

**MAS:** SharePoint `CIPDept/.../OXRP/Projects/MI400/MAS/OXRP_MAS.doc`
**Owner:** Ning, Eric <Eric.Ning@amd.com> / Luo, Sidney <Sidney.Luo@amd.com>

The Root Port on MI450 MID presents the Root Complex of the downstream AINIC device to the host. AINIC appears as a PCIe endpoint device.

**Key properties:**
- Each MID has 96 lanes configurable for AINIC attachment
- Two IOM (IO Manager) targets per MI450 socket
- PCIe MMIO takes the red path

**Impact on testing:**
- MPIO firmware (fw-mpio) handles PCIe link training for the Root Port
- SimNow tests verify PCIe enumeration via the Root Port
- `lspci` in SimNow A+A model should show AINIC endpoints

---

## 7. MCA — Machine Check Architecture

**Spec:** SharePoint `aljackso/.../MCAX_v5.0.0.docx`
**User Guide:** SharePoint `aljackso/.../MCA_IP_User_Guide_and_Specification.pdf`

MCA handles hardware error reporting. Each IP block has MCA banks for logging correctable/uncorrectable errors.

**Impact on testing:**
- MPRAS firmware (fw-mpras-kernel) reads MCA banks
- RAS tests inject errors and verify MCA bank contents
- SimNow supports MCA error injection for testing

---

## 8. Architecture Document Index

| Module | Document | Location |
|--------|----------|----------|
| SMN | smn15-interconnect-mas.docx | SharePoint `SIPControlFabric/` |
| SMN-MP | secip3_mp_mas.docx | SharePoint `SECIPHWSWArch/` |
| SMN-MAP | scf_smn_map.json | Perforce `//sysip/smn/smn-15/branches/smn15_mi450_basedie/` |
| RSMU | remote_smu_mas.docx | SharePoint `SIPControlFabric/.../CF2_Public/IP MAS/RSMU/` |
| nHT | OpenXGMI and nHT NBIO Specification.docx | SharePoint `aradu/` |
| nBIF Base | NBIF_SHUB_MAS.docx | SharePoint `BIF/` |
| nBIF MI400 | nBIF_SHUB_MI400_delta.doc | SharePoint `BIF/.../nBIF_SHUB 7.1 (MI400)/MAS/` |
| nBIF IFoE | MI450A0_nBIF_SYSHUB__IFoE__configuration_v0.1.docx | SharePoint `AINICVulcano/` |
| nBIF Reset | BIF_reset_implementation_spec.docx | SharePoint `BIF/.../baseline_MAS/reset/` |
| Root Port | OXRP_MAS.doc | SharePoint `CIPDept/.../OXRP/Projects/MI400/MAS/` |
| MCA | MCAX_v5.0.0.docx, MCA_IP_User_Guide_and_Specification.pdf | SharePoint `aljackso/` |
| OpenXGMI | Workshop Minutes | Confluence RTGMI100/pages/639297305 |
