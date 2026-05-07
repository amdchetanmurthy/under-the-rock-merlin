# Merlin: IFWI Image Assembly Pipeline

**Purpose:** Combine individual firmware binaries from fw-* build outputs into a complete MI450 SPIROM image (8MB) that SimNow and hardware can boot.

---

## 1. The Assembly Problem

The CMake meta-build produces individual firmware binaries in `build/output/<component>/`. To test them, we need a complete SPIROM image with all 74 entries in the L2 PSP Directory, plus the L1 directory, ISH, EFS, RomStrap, and signatures.

**Today:** IFWI Builder at `http://rocm-ci.amd.com/` does this assembly. It's a web tool used by IVV — unclear if it has a programmable API.

**What we need:** A scriptable assembly path that can be called from GHA workflows.

---

## 2. SPIROM Image Structure (From MI450 IFWI Layout)

Total image: **8,388,608 bytes (0x800000)**

```
Offset       Size        Component
──────────   ──────────  ─────────────────────────────────────
0x000000     0x54        EFS (Embedded Firmware Structure)
0x001000     0x04        Signature Table offset pointer (→ 0x1D000)
0x002000     0x30        L1 PSP Directory (2 entries: ISHA, ISHB)
0x003000     0x30        L1 PSP Directory backup (identical copy)
0x010000     0x2000      RomStrap A (hardware init settings)
0x012000     0x2000      RomStrap B (golden, never updated)
0x014000     0x20        ISH A (Image Slot Header, boot priority=2)
0x015000     0x20        ISH B (Image Slot Header, boot priority=1)
0x016000     0x200       Signature: EFS
0x017000     0x200       Signature: L1 Section
0x018000     0x200       Signature: ISH A
0x019000     0x200       Signature: ISH B
0x01A000     0x200       Signature: L2 Partition
0x01B000     0x200       Signature: RomStrap A
0x01C000     0x200       Signature: RomStrap B
0x01D000     0x80        Signature Table (7 entries)
0x020000     0x3E0000    Partition A: L2 PSP Directory + 74 firmware entries
0x400000     0x3E0000    Partition B: (backup, identical or older)
0x7E0000     0x10000     PSP Boot Configuration
```

### 2.1 L2 PSP Directory Format

```c
// At offset 0x020000 (Partition A)
struct PSP_DIRECTORY_HEADER {
    uint32_t PspCookie;    // 0x324C5024 ("$PL2")
    uint32_t Checksum;     // CRC32 of header + entries
    uint32_t TotalEntries; // 74
    uint32_t Reserved;
};

struct PSP_DIRECTORY_ENTRY {
    uint32_t Type;         // PSP entry type ID (e.g., 0x1 for MPASP_FMC)
    uint32_t Size;         // Binary size in bytes
    uint32_t Location;     // Absolute offset in SPIROM
    uint32_t Location_Hi;  // High 32 bits (0 for MI450)
};
// Total: 16 bytes per entry × 74 entries = 1184 bytes
// Directory header: 16 bytes
// Full L2 directory: 1200 bytes
```

### 2.2 Entry Type → fw-* Target Mapping (74 Entries)

| PSP Type | FW ID | Name | Size | fw-* Target | Output File |
|----------|-------|------|------|-------------|-------------|
| 0x0 | 0x0000 | AMD_PUBLIC_KEY | 2K | (static) | — |
| 0x1 | 0x0001 | MPASP_FMC | 128K | fw-asp-fmc | output/asp-fmc/*.bin |
| 0x2 | 0x0009 | MPASP_TRUST_OS | 256K | fw-amd-tee3 | output/amd-tee3/*/tos.bin |
| 0x8 | 0x1001 | MP1_PM_FW | 260K | fw-pmfw | output/pmfw/*.bin |
| 0x9d | 0x01C5 | ART_LIBROM_OVERLAY | 4K | fw-unicrypt | output/unicrypt/art.bin |
| 0xa8 | 0x00A8 | Caliptra | 128K | fw-caliptra-sw | output/caliptra-sw/*.bin |
| 0xab | 0x01CC | MPART_FMC | 64K | fw-art-security | output/art-security/fmc.bin |
| 0xac | 0x01CD | MPART_RUNTIME_FW | 76K | fw-art-security | output/art-security/runtime.bin |
| 0xae | 0xaa | ASP_LIBROM | 196K | fw-unicrypt | output/unicrypt/asp.bin |
| 0x1b-0x6c | various | TEE Drivers (13) | 32-256K each | fw-amd-tee3 | output/amd-tee3/*/*.bin |
| 0x4f | 0x1009 | UMC_FW | 192K | (Perforce) | LKG cache |
| 0x50 | 0x004E | PSPBL_KEY_DATABASE | 24K | fw-keydb | output/keydb/bl.bin |
| 0x5d | 0x101B | MPIO_FW | 256K | fw-mpio | output/mpio/mpio.pspbin |
| 0x6B | 0x1D7 | MPRAS_FW | 128K | fw-mpras-kernel | output/mpras/*.bin |
| 0x76 | 0x0131 | DF_RIB | 640K | (gitlab, no access) | LKG cache |
| 0x9b | 0x203B | IMU_Instruction_FW | 96K | fw-pmfw | output/pmfw/imu_inst.bin |
| 0x9c | 0x203C | IMU_Data_FW | 96K | fw-pmfw | output/pmfw/imu_data.bin |
| 0xB5 | 0x107E | NBIO_UNIFIED_CLD_FW | 16K | fw-pcie-cld | output/pcie-cld/*.bin |
| 0x157-0x15f | 0x157-15f | eSID TOC + eSID 0-7 | 24-96K | fw-dcgpu-esid | output/dcgpu-esid/*.bin |
| 0x1E0 | 0x01EF | MP_NHT_FW | 25K | fw-mpnht | output/mpnht/*.bin |
| 0x1ec | 0x01EC | UCIE_PHY_FW | 81K | fw-ucie | output/ucie/*.bin |
| 0x1f3 | 0x1f9 | IFOE_FW | 512K | fw-mpifoe | output/mpifoe/*.bin |
| 0x1fb | — | VBL_Runtime | — | fw-vbl-tee-drv | output/vbl-tee-drv/*.bin |
| 0x24/0x45/0x101 | — | Security Policies | 64-200K | (Perforce) | LKG cache |
| ... | ... | (remaining entries) | ... | (static/LKG) | LKG cache |

---

## 3. Assembly Approach: Option A (IFWI Builder API)

### 3.1 Discovery Tasks

Before implementing, determine:

1. **Does IFWI Builder have a REST API?** Ask IFWI team (contact: team at rocm-ci.amd.com)
2. **What inputs does it accept?** Individual binaries, or a "recipe" YAML/JSON?
3. **What outputs does it produce?** Complete SPIROM .bin file?
4. **Does it sign the image?** Or are signatures computed separately?
5. **Can it accept unsigned binaries?** For SimNow testing (no fuse checks)
6. **What's the latency?** Must be < 2 min for pre-submit budget

### 3.2 API Integration (Hypothetical)

```python
# scripts/assemble-ifwi-builder.py
import requests

def assemble_via_builder(components_dir, product, output_path):
    """Call IFWI Builder API to assemble SPIROM image."""
    files = {}
    for entry_type, binary_path in discover_binaries(components_dir):
        files[f"entry_{entry_type}"] = open(binary_path, "rb")

    response = requests.post(
        f"http://rocm-ci.amd.com/api/v1/assemble",
        data={"product": product, "unsigned": "true"},
        files=files,
        timeout=120,
    )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)
```

---

## 4. Assembly Approach: Option B (Source Assembly Script)

If IFWI Builder has no API, we build a Python script that constructs the SPIROM image directly.

### 4.1 Script Design: `scripts/assemble-ifwi.py`

```python
#!/usr/bin/env python3
"""Assemble a complete MI450 SPIROM image from individual firmware binaries.

Uses the L2 PSP Directory format documented in MI450 IFWI Layout
(Confluence: spaces/VBIOS/pages/524949427).

Input: directory of per-component binaries + base image template
Output: 8MB SPIROM .bin file

Two modes:
  --base-image: Start from a complete LKG SPIROM and replace specific entries
  --from-scratch: Build entire image from individual binaries (needs all 74)
"""

import struct
import hashlib
from pathlib import Path

SPIROM_SIZE = 0x800000  # 8MB
EFS_OFFSET = 0x000000
L1_DIR_OFFSET = 0x002000
L1_DIR_BACKUP_OFFSET = 0x003000
ISHA_OFFSET = 0x014000
ISHB_OFFSET = 0x015000
SIG_TABLE_OFFSET = 0x01D000
PARTITION_A_OFFSET = 0x020000
PARTITION_B_OFFSET = 0x400000
PARTITION_SIZE = 0x3E0000
BOOT_CONFIG_OFFSET = 0x7E0000

PSP_COOKIE_L2 = 0x324C5024  # "$PL2"

class PSPDirectoryEntry:
    FORMAT = "<IIII"  # Type, Size, Location, Location_Hi
    SIZE = 16

    def __init__(self, entry_type, size, location, location_hi=0):
        self.entry_type = entry_type
        self.size = size
        self.location = location
        self.location_hi = location_hi

    def pack(self):
        return struct.pack(self.FORMAT, self.entry_type, self.size,
                          self.location, self.location_hi)

class SPIROMAssembler:
    def __init__(self, base_image_path=None):
        if base_image_path:
            with open(base_image_path, "rb") as f:
                self.image = bytearray(f.read())
            assert len(self.image) == SPIROM_SIZE
        else:
            self.image = bytearray(SPIROM_SIZE)

    def parse_l2_directory(self, partition_offset=PARTITION_A_OFFSET):
        """Parse existing L2 PSP directory from image."""
        offset = partition_offset
        cookie, checksum, total_entries, reserved = struct.unpack_from(
            "<IIII", self.image, offset
        )
        assert cookie == PSP_COOKIE_L2, f"Bad L2 cookie: {cookie:#x}"

        entries = []
        for i in range(total_entries):
            entry_offset = offset + 16 + (i * PSPDirectoryEntry.SIZE)
            t, s, loc, loc_hi = struct.unpack_from(
                PSPDirectoryEntry.FORMAT, self.image, entry_offset
            )
            entries.append(PSPDirectoryEntry(t, s, loc, loc_hi))

        return entries

    def replace_entry(self, entry_type, binary_data):
        """Replace a single firmware binary in Partition A."""
        entries = self.parse_l2_directory()

        for entry in entries:
            if entry.entry_type == entry_type:
                if len(binary_data) > entry.size:
                    raise ValueError(
                        f"Binary for type {entry_type:#x} is {len(binary_data)} bytes, "
                        f"max slot size is {entry.size} bytes"
                    )
                # Write binary at the entry's location
                loc = entry.location
                self.image[loc:loc + len(binary_data)] = binary_data
                # Zero-pad remainder of slot
                if len(binary_data) < entry.size:
                    self.image[loc + len(binary_data):loc + entry.size] = (
                        b'\x00' * (entry.size - len(binary_data))
                    )
                # Update size in directory
                entry.size = len(binary_data)
                self._rewrite_directory(entries)
                return

        raise KeyError(f"Entry type {entry_type:#x} not found in L2 directory")

    def _rewrite_directory(self, entries, partition_offset=PARTITION_A_OFFSET):
        """Rewrite L2 PSP directory with updated entries + recalculated checksum."""
        offset = partition_offset
        total = len(entries)

        # Write entries first (after 16-byte header)
        for i, entry in enumerate(entries):
            entry_offset = offset + 16 + (i * PSPDirectoryEntry.SIZE)
            struct.pack_into(PSPDirectoryEntry.FORMAT, self.image, entry_offset,
                           entry.entry_type, entry.size, entry.location, entry.location_hi)

        # Calculate checksum: CRC32 of everything except cookie (first 4 bytes)
        dir_size = 16 + (total * PSPDirectoryEntry.SIZE)
        checksum_data = self.image[offset + 4:offset + dir_size]
        checksum = self._crc32(checksum_data)

        # Write header
        struct.pack_into("<IIII", self.image, offset,
                        PSP_COOKIE_L2, checksum, total, 0)

    def _crc32(self, data):
        """Calculate PSP directory CRC32."""
        # PSP uses standard CRC32 (same as Python's zlib.crc32)
        import zlib
        return zlib.crc32(data) & 0xFFFFFFFF

    def save(self, output_path):
        with open(output_path, "wb") as f:
            f.write(self.image)
```

### 4.2 Usage in Gate Pipeline

```bash
# Mode 1: Replace single entry in LKG base image
python3 scripts/assemble-ifwi.py \
  --base-image lkg-cache/ifwi-mi450.bin \
  --replace 0x0001:build/output/asp-fmc/mpasp_fmc.bin \
  --output build/ifwi-mi450-pr.bin

# Mode 2: Replace multiple entries
python3 scripts/assemble-ifwi.py \
  --base-image lkg-cache/ifwi-mi450.bin \
  --replace 0x0001:build/output/asp-fmc/mpasp_fmc.bin \
  --replace 0x005d:build/output/mpio/mpio.pspbin \
  --output build/ifwi-mi450-pr.bin
```

### 4.3 Entry Type → Output File Mapping

This mapping connects `build/output/<component>/` to PSP entry types:

```yaml
# configs/psp-entry-map.yaml
# Maps fw-* build outputs to L2 PSP Directory entry types
entries:
  fw-asp-fmc:
    - type: 0x0001
      file: "output/asp-fmc/*.bin"  # glob pattern
      max_size: 131072  # 128K

  fw-pmfw:
    - type: 0x0008
      file: "output/pmfw/mid_mp1.bin"
      max_size: 266240  # 260K
    - type: 0x009b
      file: "output/pmfw/imu_instruction.bin"
      max_size: 98304
    - type: 0x009c
      file: "output/pmfw/imu_data.bin"
      max_size: 98304
    - type: 0x01ea
      file: "output/pmfw/aid_mp5.bin"
      max_size: 163840
    - type: 0x1051
      file: "output/pmfw/xcd_mp5.bin"
      max_size: 196608

  fw-mpio:
    - type: 0x005d
      file: "output/mpio/mpio.pspbin"
      max_size: 262144  # 256K

  fw-mpifoe:
    - type: 0x01f3
      file: "output/mpifoe/*.bin"
      max_size: 524288  # 512K (largest single entry)

  fw-amd-tee3:
    - type: 0x0002
      file: "output/amd-tee3/*/tos.bin"
      max_size: 262144
    # ... 13 TEE driver entries ...

  fw-dcgpu-esid:
    - type: 0x0157
      file: "output/dcgpu-esid/esid_toc.bin"
      max_size: 24576
    - type: 0x0158
      file: "output/dcgpu-esid/esid_0.bin"
      max_size: 98304
    # ... eSID 1-7 ...
```

---

## 5. Signing Considerations

### 5.1 SimNow (Pre-Submit)

SimNow does NOT enforce fuse-based signature verification (it's a simulator). Unsigned binaries should work for gate testing.

The meta-build already defaults to skip signing:
- `UTTR_MPIO_SKIP_SIGN=ON` (CMakeLists.txt line 261)
- Most fw-* targets skip the fw-sign step locally

### 5.2 Hardware (Nightly)

For hardware tests, signing may be required depending on the silicon stepping and fuse state. The existing IVV workflows handle signing via:
- `fw-sign` package from Artifactory PyPI (`api/pypi/FW-Sign-DEV-LOCAL/simple`)
- Per-component signing workflows (e.g., `aspfmc-build-sign.yml`)

### 5.3 Production (BKC Release)

Full signing with production keys — out of scope for Merlin gate, handled by release pipeline.

---

## 6. Decision: Option A vs Option B

| Factor | Option A (IFWI Builder API) | Option B (Source Assembly) |
|--------|---------------------------|--------------------------|
| Correctness | Proven (production tool) | Must validate against IFWI Builder output |
| Speed | Network latency + API processing | Local, < 1 sec |
| Availability | Depends on rocm-ci.amd.com uptime | Always available |
| Maintenance | IFWI team maintains | UnderTheRock team maintains |
| Signing | Built-in | Must integrate separately |
| Flexibility | Limited to API capabilities | Full control |

**Recommendation:** Start with **Option B** (source assembly) for the gate — it's faster, always available, and doesn't depend on an external service. Validate by comparing output against IFWI Builder's output for the same inputs. Fall back to Option A if assembly proves too complex.
