# Merlin: Component Onboarding Status

**Purpose:** Track which firmware components are ready for the Merlin gate, and what each needs to participate.

---

## Onboarding Checklist (Per Component)

```
□ 1. fw-* target in CMakeLists.txt (built, not stub)
□ 2. Submodule checked out and building on IVV runners
□ 3. PSP entry type(s) mapped in configs/psp-entry-map.yaml
□ 4. Build output collected to ${UTTR_OUTPUT_DIR}/<component>/
□ 5. uttr-tests.yaml created with pre_submit + nightly tests
□ 6. LKG binary published to Artifactory
□ 7. SimNow assertions validated for this component
□ 8. Gardener rotation assigned (component TL in pool)
□ 9. Build engineer contact confirmed (from BKC modules)
```

---

## Component Status Matrix

### Tier 1: Ready to Onboard (Built from source, checked out)

| Component | fw-* Target | PSP Entries | Build System | Checked Out | Build Works | uttr-tests.yaml | LKG Published |
|-----------|-------------|-------------|-------------|-------------|-------------|-----------------|---------------|
| ASP FMC | fw-asp-fmc | 0x0001 (128K) | Make + Conan | Yes | Yes (IVV) | Not yet | Not yet |
| PMFW | fw-pmfw | 0x0008, 0x009b, 0x009c, 0x01ea, 0x1051 | tcsh/CBWA Make | Yes | Yes (IVV) | Not yet | Not yet |
| MPIO | fw-mpio | 0x005d (256K) | Zephyr/Xtensa | Yes | Yes (IVV) | Not yet | Not yet |
| MPIFoE | fw-mpifoe | 0x01f3 (512K) | Zephyr/RISC-V | Yes | Yes (IVV) | Not yet | Not yet |
| AMD TEE3 | fw-amd-tee3 | 14 entries (~3MB) | Make RISC-V | Yes | Yes (IVV) | Not yet | Not yet |
| ART Security | fw-art-security | 0xab, 0xac (140K) | Make + Cargo | Yes | Yes (IVV) | Not yet | Not yet |
| DCGPU eSID | fw-dcgpu-esid | 9 entries (600K) | autoconf + Make | Yes | Yes (IVV) | Not yet | Not yet |
| KeyDB | fw-keydb | 0x50, 0x51, 0xad (52K) | Python | Yes | Yes | Not yet | Not yet |
| MPRAS Kernel | fw-mpras-kernel | 0x6B (128K) | Zephyr/RISC-V | Yes | Yes (IVV) | Not yet | Not yet |
| MPNHT | fw-mpnht | 0x1E0 (25K) | build.sh + Make | Yes | Yes (IVV) | Not yet | Not yet |
| VBL TEE Drv | fw-vbl-tee-drv | 0x01fb | Make | Yes | Yes | Not yet | Not yet |
| Caliptra | fw-caliptra-sw | 0xa8 (128K) | Binary copy | Yes | Yes (trivial) | Not yet | Not yet |
| PCIe CLD | fw-pcie-cld | 0xB5 (16K) | Make | Needs access | — | Not yet | Not yet |
| UCIe | fw-ucie | 0x1ec (81K) | Make | Needs access | — | Not yet | Not yet |
| UniCrypt | fw-unicrypt | 0x9d, 0xae (200K) | Make | Needs access | — | Not yet | Not yet |
| DMU | fw-dmu | DMCUB entry | Xtensa Make | Needs access | — | Not yet | Not yet |

### Tier 2: Stubs (Need Build Wiring)

| Component | fw-* Target | PSP Entries | Blocker |
|-----------|-------------|-------------|---------|
| CP MI400 | fw-cp-mi400 | CP entries | Build not wired, checked out |
| MPRAS Applets | fw-mpras-applets | 0x0135 | Build conditional on submodule |
| SRIOV DR | fw-sriov-dr | 0x01f7 | Build conditional on submodule |
| SW Security Tools | fw-sw-security-tools | 0x0055 | Build not wired |
| RAS TA | fw-ras-ta | 0x0065 | Gerrit access blocked |
| Drivers (10) | fw-drivers-* | Various | github.com access needed |
| IP FW | fw-ip-fw | Various | Gerrit access blocked |
| UDK2018 (GOP) | fw-udk2018 | GOP entry | Gerrit access blocked |
| PMFW EC | fw-pmfw-ec | — | Gerrit access blocked |
| Powerplay Utils | fw-powerplay-utils | — | github.com access needed |

### Tier 3: Not In Git (Perforce / Artifactory / Config)

| Component | FW IDs | Source | Contact |
|-----------|--------|--------|---------|
| Secure Policy RSMU Init | 0x0009 | Perforce | Anas Siraj |
| Security Policy L0 | 0x0024 | Perforce | Anas Siraj |
| Security Policy TOS Late | 0x0045 | Perforce | Anas Siraj |
| Secure Policy L1 | 0x0101 | Perforce | Anas Siraj |
| UMC FW | 0x004f | Perforce | Jin Chung Teng |
| Memory Init Config Table | 0x0147 | Config | Sai Kammila |
| GTA PHY | 0x01f9 | Pending | Ed C. Lee |
| IFOE PHY | 0x01fa | Pending | Ed C. Lee |
| APCB variants | 0x1053-1057 | IFWI Builder | Marco Herdia |
| AINIC bundles | — | Artifactory | Vijay Gopinath |

---

## Priority Order for Onboarding

Based on PSP directory impact (size + criticality):

| Priority | Component | Rationale |
|----------|-----------|-----------|
| P0 | fw-asp-fmc | PSP boot chain entry point; most mature IVV workflow |
| P0 | fw-mpio | Critical path (PCIe/XGMI); frequent changes |
| P0 | fw-pmfw | 5 PSP entries, power management — high-impact |
| P1 | fw-amd-tee3 | 14 entries, security critical |
| P1 | fw-mpifoe | Largest single entry (512K), IFoE is new for MI450 |
| P1 | fw-art-security | Security (MPART), requires Rust/Cargo |
| P2 | fw-dcgpu-esid | 9 entries, autoconf complexity |
| P2 | fw-keydb | Small but security-critical (key databases) |
| P2 | fw-mpras-kernel | RAS — important for datacenter reliability |
| P3 | fw-mpnht, fw-vbl-tee-drv, fw-caliptra-sw | Smaller, less frequent changes |
| P3 | fw-pcie-cld, fw-ucie, fw-unicrypt, fw-dmu | Needs repo access first |

---

## Actions Required

### Immediate (This Sprint)
1. Create `configs/psp-entry-map.yaml` mapping fw-* outputs to PSP entry types
2. Write `uttr-tests.yaml` for fw-asp-fmc (PoC component)
3. Build initial LKG cache from trunk HEAD
4. Create GHA workflow skeleton (merlin-presubmit-poc.yml)

### Short-Term (Phase 1)
5. Write `uttr-tests.yaml` for P0 components (fw-mpio, fw-pmfw)
6. Get repo access for PCIe CLD, UCIe, UniCrypt, DMU (github.amd.com/NBIOFW)
7. Establish Artifactory layout for LKG component binaries
8. Validate IFWI assembly approach (Option A or B)

### Medium-Term (Phase 2)
9. Write `uttr-tests.yaml` for all P1 and P2 components
10. Wire nightly orchestrator workflow
11. Implement LKG promotion logic
12. Onboard gardener rotation for IFWI components
