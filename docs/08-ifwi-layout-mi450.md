# MI450 IFWI Layout

**Source:** https://amd.atlassian.net/wiki/spaces/VBIOS/pages/524949427/MI450+IFWI+layout
**Author:** Yan, Xiong | **Last Modified:** Sep 23, 2025

## Overview

MI450 uses an A/B partition layout similar to MI3XX. All IFWI components are signed and authenticated by PSP (Platform Security Processor).

## SPIROM Layout

| Offset | Size | Component |
|--------|------|-----------|
| 0x000000 | 0x54 | Embedded Firmware Structure (EFS) — signature `0x55aa55aa` |
| 0x001000 | 0x04 | RomSignatureTableOffset = 0x1D000 |
| 0x002000 | 0x30 | L1PspDirectoryTable |
| 0x003000 | 0x30 | L1PspDirectoryTable backup |
| 0x010000 | 0x2000 | RomstrapA — cookie `0x24524F4D`, offset defined in EFS |
| 0x012000 | 0x2000 | RomStrapB — cookie `0x24524F4D`, backup/golden (never updated) |
| 0x014000 | 0x20 | ISHA (Image Slot Header A) |
| 0x015000 | 0x20 | ISHB (Image Slot Header B) |
| 0x016000 | 0x200 | ROM_SIGNATURE_EFS |
| 0x017000 | 0x200 | ROM_SIGNATURE_L1_SECTION |
| 0x018000 | 0x200 | ROM_SIGNATURE_ISHA |
| 0x019000 | 0x200 | ROM_SIGNATURE_ISHB |
| 0x01a000 | 0x200 | ROM_SIGNATURE_L2_PARTITION |
| 0x01b000 | 0x200 | ROM_SIGNATURE_ROMSTRAP_A |
| 0x01c000 | 0x200 | ROM_SIGNATURE_ROMSTRAP_B |
| 0x01d000 | 0x80 | ROM_IMAGE_SIGNATURE_TABLE (offset defined at 0x1000) |
| 0x020000 | 0x3E0000 | FW PartitionA: L2PspDirectoryTableA + all FW |
| 0x400000 | 0x3E0000 | FW PartitionB: L2PspDirectoryTableB + all FW |
| 0x7e0000 | 0x10000 | PSP boot configuration settings |

## Embedded Firmware Structure (EFS)

Located at SPIROM offset 0x0 for PCI endpoint devices (GPU). For CPU/APU, EFS is at a different offset (e.g. 0x20000 or 0x1000 for Raphael).

MI450 bootrom reads efuse `MP0_BASE_BOOT_ADDRESS` to determine EFS start offset. For MI450, `MP0_BASE_BOOT_ADDRESS = 0`.

```c
struct IFWI_GENERIC_EFS {
    uint32_t Signature;                    // 0x00 — 0x55aa55aa
    uint32_t Reserved_0x04[4];             // 0x04
    uint32_t PspDirectoryLocation;         // 0x14 — 0x20000 (L1 Primary)
    uint32_t BiosDirectoryLocation[2];     // 0x18 — Not used
    uint32_t Reserved_0x20;                // 0x20
    uint32_t FirstGeneration;              // 0x24 — Not used
    uint32_t Reserved_0x28;                // 0x28
    uint32_t PspDirectoryLocationBackup;   // 0x2c — 0x30000 (L1 Secondary)
    uint32_t Reserved_0x30[6];             // 0x30
    uint32_t PspDirIndLocation;            // 0x48 — Unused on dGPU (0x0)
    uint32_t RomStrapALocation;            // 0x4c — 0x10000
    uint32_t RomStrapBLocation;            // 0x50 — 0x11000 (Golden, never updated)
};
```

EFS is signed with 4K key; signature stored in SignatureTable used by MPASP during IFWI flash.

## L1PspDirectoryTable

Carries pointers to Image Slot Headers (ISH). SEC3.0 MPART bootrom hardcodes PSP entry IDs 0x48 (ISHA) and 0x4a (ISHB) — changed from previous generation (0x13c/0x13d).

Two identical copies at offsets 0x12000 and 0x13000 (2nd is backup for corruption recovery).

```c
struct PSP_DIRECTORY_HEADER {
    uint32_t PspCookie;    // "$PSP" = 0x50535024
    uint32_t Checksum;     // 32-bit CRC of header + entire table
    uint32_t TotalEntries; // Number of PSP Entries
    uint32_t Reserved;
};

struct PSP_DIRECTORY_ENTRY {
    uint32_t u32Type;      // Type of PSP entry
    uint32_t u32Size;      // Size in bytes
    uint32_t Location;     // Address in SPI-ROM space
    uint32_t Location_Hi;
};
```

L1 table has 2 entries:
- PspEntry[0]: Type=0x48 (ISHA), Size=32, Location=0x12000
- PspEntry[1]: Type=0x4a (ISHB), Size=32, Location=0x13000

## Image Slot Header (ISH)

Each partition has an ISH. MPART bootrom uses `BootPriority` to select the partition with higher priority.

| Field | Offset | Size | ISHA Default | ISHB Default | Description |
|-------|--------|------|--------------|--------------|-------------|
| CheckSum | 0x00 | 4 | 0x2f44d47 | 0xed64ec2 | 32-bit Fletcher's CRC |
| BootPriority | 0x04 | 4 | 0x2 | 0x1 | Higher value = preferred boot partition |
| UpdateRetries | 0x08 | 4 | 0 | 0 | Boot attempts before "unbootable" (0 = no retries for A/B) |
| GlitchRetries | 0x0C | 1 | 0 | 0 | Glitch retry counter |
| u16Fw_Id | 0x0D | 2 | 0x14D | 0x14E | FW ID of partition's L2 directory |
| Location | 0x10 | 4 | 0x020000 | 0x400000 | Absolute address of L2 directory in SPIROM |
| PspId | 0x14 | 4 | 0x00 | 0x00 | 32b Chip/PSP ID |
| SlotMaxSize | 0x18 | 4 | 0x3e0000 | 0x3e0000 | Maximum IFWI partition image size |
| LocationCSM | 0x1C | 4 | 0x040000 | 0x420000 | Pointer to L2 partition's VBIOS image (128KB aligned) |

## Signature Table

Used by MPASP during IFWI flash. Before updating each component, MPASP authenticates it with its signature.

Signature table offset found at SPIROM offset 0x1000 (hardcoded), value = 0x1b000.

7 signed components:
1. EFS (0x01)
2. L1_SECTION (0x02)
3. ISHA (0x03)
4. ISHB (0x04)
5. L2_PARTITION (0x05)
6. ROMSTRAP_A (0x06)
7. ROMSTRAP_B (0x07)

## ROMSTRAP

Carries settings for multiple IPs (mostly NBIO) loaded by on-chip PSP boot-rom after HW reset. PSP boot-rom reads romstrap settings from SPI ROM and distributes them to different IPs as part of efuse distribution sequence.

## L2 IFWI Partition — Firmware Directory

L2 carries all off-chip firmware. MI450 uses unified PSP directory IDs across AMD products (CPU, APU, Server, dGPU).

For FW used by CPU/APU/Server (PSP FMC, PMFW, etc.), PSP entry ID differs from FW ID. For GPU-specific FW with FW ID > 0x100, PSP entry ID = FW ID.

New entry ID mappings for MI450:
- 0x101 → Security Policy for SRIOV (FW ID 0x4d)
- 0x102 → PSP Platform TOPOLOGY Table (FW ID 0x4a)

### Complete L2 Directory (74 entries)

| Index | FW Name | Entry Type | FW ID | Size |
|-------|---------|------------|-------|------|
| 0 | AMD_PUBLIC_KEY | 0x0 | 0x0000 | 2K |
| 1 | VBIOS_KEY_TOKEN | 0x13a | 0x013a | 1K |
| 2 | VBIOS_SIGNATURE | 0x141 | 0x0141 | 0.5K |
| 3 | Wrapped_IKEK | 0x21 | 0x0021 | 0.06K |
| 4 | AMD_SOFT_FUSE_CHAIN | 0xb | N/A | 0.01K |
| 5 | DBG_UNLOCK_TOKEN | 0x9 | 0x0132 | 12K |
| 6 | APCB_DEFAULT | 0x1053 | 0x1053 | 8K |
| 7 | APCB_Updatable | 0x1054 | 0x1054 | 16K |
| 8 | APCB_Updatable_backup | 0x1055 | 0x1055 | 1K |
| 9 | APCB_Eventlog | 0x1056 | 0x1056 | 8K |
| 10 | APCB_Eventlog_backup | 0x1057 | 0x1057 | 1K |
| 11 | VGA_VBIOS | 0x137 | 0x0137 | 32K |
| 12 | MemInitCfgTable | 0x147 | 0x0147 | 32K |
| 13 | Caliptra | 0xa8 | 0x00A8 | 128K |
| 14 | AspLibSec | 0xaa | 0x01CB | 132K |
| 15 | MPART_FMC | 0xab | 0x01CC | 64K |
| 16 | MPART_RUNTIME_FW | 0xac | 0x01CD | 76K |
| 17 | ART_LIBROM_OVERLAY | 0x9d | 0x01C5 | 4K |
| 18 | MPASP_FMC | 0x1 | 0x0001 | 128K |
| 19 | MPASP_TRUST_OS | 0x2 | 0x0009 | 256K |
| 20 | TEE_BOOT_Driver | 0x1b | 0x0150 | 256K |
| 21 | TEE_SOC_Driver | 0x1c | 0x014A | 256K |
| 22 | TEE_HAD_Driver | 0x1d | 0x014B | 256K |
| 23 | TOS_PRE_ESID | 0x6a | 0x01D6 | 256K |
| 24 | TOS_POST_ESID | 0x6c | 0x01E0 | 256K |
| 25 | TEE_INTERFACE_Driver | 0x1f | 0x014C | 256K |
| 26 | TEE_RAS_Driver | 0x64 | 0x0152 | 32K |
| 27 | PSP_FW_SYSDRV | 0x28 | 0x000A | 256K |
| 28 | RAS_MCA_TABLE | 0x134 | 0x0134 | 8K |
| 29 | PSPBL_KEY_DATABASE | 0x50 | 0x004E | 24K |
| 30 | PSPOS_KEY_DATABASE | 0x51 | 0x004F | 12K |
| 31 | MPART_KEY_DATA_BASE | 0xad | 0x01E2 | 16K |
| 32 | TOS_ANTI_ROLLBACK | 0x56 | 0x0056 | 4K |
| 33 | PSP_ANTI_ROLLBACK | 0x55 | 0x0055 | 4K |
| 34 | DF_TOPOLOGY | 0x102 | 0x005A | 40K |
| 35 | ESID_TOC | 0x157 | 0x157 | 24K |
| 36-43 | ESID0-ESID7 | 0x158-0x15f | 0x158-0x15f | 64-96K each |
| 44 | UMC_FW | 0x4f | 0x1009 | 192K |
| 45 | MP1_PM_FW | 0x8 | 0x1001 | 260K |
| 46 | MP5_XCD | 0x1051 | 0x1051 | 192K |
| 47 | DF_RIB | 0x76 | 0x0131 | 640K |
| 48 | SEC_POLICY_L0 | 0x24 | 0x004B | 200K |
| 49 | SEC_POLICY_TOS | 0x45 | 0x004C | 64K |
| 50 | SEC_POLICY_L1 | 0x101 | 0x004D | 64K |
| 51 | IP_DISCOVERY_BIN | 0x20 | 0x1007 | 12K |
| 52 | XGMI_PHY_FW | 0x42 | 0x101A | 64K |
| 53 | MPIO_FW | 0x5d | 0x101B | 256K |
| 54 | SPIROM_INFO | 0x5c | 0x0133 | 32K |
| 55 | Whitlist_SN | 0x3a | 0x000C | 4K |
| 56 | SoftFuseOverride | 0x75 | 0x01C4 | 64K |
| 57 | PSP_DIAG_BL | 0x23 | 0x0050 | 32K |
| 58 | UCIE_PHY_FW | 0x1ec | 0x01EC | 81K |
| 59 | IFOE_FW | 0x1f3 | 0x1f9 | 512K |
| 60 | TEE_IPKEYMGR_DRV | 0x15 | 0x01ED | 256K |
| 61 | PSP_BOOT_AUDIT_MODULE | 0x5E | 0x005E | 32K |
| 62 | AID_MP5 | 0x01EA | 0x01EA | 160K |
| 63 | ASP_LIBROM | 0xae | 0xaa | 196K |
| 64 | SPDM_DRV | 0x68 | 0x01C7 | 128K |
| 65 | TEE_DPE_DV | 0x69 | 0x01DB | 128K |
| 66 | MP_NHT_Controller_FW | 0x1E0 | 0x01EF | 25K |
| 67 | IMU_Instruction_FW | 0x9b | 0x203B | 96K |
| 68 | IMU_Data_FW | 0x9c | 0x203C | 96K |
| 69 | PSP_TEE_SRIOV_DRV | 0x1F7 | 0x1FE | 96K |
| 70 | MPRAS_FW | 0x6B | 0x1D7 | 128K |
| 71 | RAS_REG_WHITELIST | 0x9F | 0x0135 | 16K |
| 72 | NBIO_UNIFIED_CLD_FW | 0xB5 | 0x107E | 16K |
| 73 | BOOT_CONFIG | 0x78 | 0x0144 | 4K |

## Key Design Points

- **A/B Partitioning:** PartitionA at 0x020000, PartitionB at 0x400000 — enables safe updates via trusted update feature
- **Boot Selection:** MPART bootrom compares BootPriority in ISHA vs ISHB; higher value wins (default: A=2, B=1, so A boots first)
- **Signature Verification:** All 7 top-level components signed with 4K RSA keys; MPASP verifies before flash
- **L1/L2 Directory Structure:** L1 points to ISH entries; L2 contains all 74 firmware entries
- **Unified PSP Directory:** MI450 uses unified entry IDs across AMD product lines (CPU/APU/dGPU)
- **Total SPIROM Size:** 8MB (0x800000), with 2x ~3.9MB firmware partitions
