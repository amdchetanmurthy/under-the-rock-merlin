# PFO Firmware Repos — Deep Test Inventory

**16 repos analyzed** (15 checked out + 1 missing: unicrypt on er.github.amd.com)
**1,627 lines** of detailed per-repo analysis across 3 documents.

## Documents

| Document | Repos Covered |
|----------|---------------|
| [batch1-core-firmware.md](batch1-core-firmware.md) | asp-fmc, amd-tee3_0, pmfw-firmware, mpio, mpifoe-fw |
| [batch2-security-ras.md](batch2-security-ras.md) | art-security, dcgpu-esid, MPRAS-Kernel, MPRAS-Applets, nht-firmware |
| [batch3-drivers-tools.md](batch3-drivers-tools.md) | VBL-TEE-Drv, sriov-dr, sw-security-tools, cp-mi400, pcie-cld-fw, ucie-fw |

## Cross-Repo Test Maturity Summary

| Repo | Workflows | SimNow PR | SimNow Nightly | Unit Tests | Coverity | Lint | AI Review | Hardware |
|------|-----------|-----------|----------------|------------|----------|------|-----------|----------|
| asp-fmc | 10 | 4 configs | 60+ configs | None | Yes | Yes | Yes | Jenkins |
| amd-tee3_0 | 18 | 6 ASICs | Yes | TA (Win-only) | Yes | Yes | No | Jenkins |
| pmfw-firmware | 7 | No | No | 1 script | No | No | No | Verix |
| mpio | 5 | No | No | x86 (CppUTest) | Yes | No | No | No |
| mpifoe-fw | 7 | No | Yes | Twister+pytest | Yes | Yes | Yes | Jenkins (legacy) |
| art-security | 11 | 7 ASICs | 60+ configs | CONFIG_TEST | Yes | Yes | Yes | Jenkins |
| dcgpu-esid | 12 | 2 ASICs | Yes | CppUTest (100+) | Yes | Yes | No | DCAuto |
| MPRAS-Kernel | 3 | 5 MAT | 16 configs | 5 on-target | Yes | Yes | No | No |
| MPRAS-Applets | 4 | No | No | 1 test applet | Yes | Yes | No | No |
| nht-firmware | 6 | 2 ASICs | Yes | None | Yes | Yes | Yes | No |
| VBL-TEE-Drv | 4 | 5 configs | 16 configs | Simulator | Yes | Yes | No | No |
| sriov-dr | 5 | No | Yes | None | Yes | Yes | No | No |
| sw-security-tools | 0 | No | No | Manual scripts | No | No | No | No |
| cp-mi400 | 0 | No | No | None | No | No | No | No |
| pcie-cld-fw | 10 | Build+GTest | Yes | GoogleTest (5) | Yes | Yes | Yes | Protium |
| ucie-fw | 17 | Build+GTest | gcov+BlackDuck | GoogleTest (2) | Yes | Yes | No | Protium |

## Top Gaps (Priority Order)

1. **pmfw-firmware** — No Coverity, no lint, no SimNow in CI, minimal tests. Produces 5 PSP entries. Highest risk.
2. **cp-mi400** — Zero CI. Command Processor microcode with no automation at all.
3. **sw-security-tools** — Zero CI. Security-critical signing tools with no automated testing.
4. **mpio** — Has x86 unit tests in source but unclear if they run in CI. No SimNow. No nightly.
5. **MPRAS-Applets** — No SimNow of its own. A broken applet can merge with zero boot validation.
6. **sriov-dr** — Has CI but zero functional tests. Only static analysis.
7. **nht-firmware** — Zero unit tests. Only SimNow boot serves as functional validation.

## Test Framework Distribution

| Framework | Repos Using It |
|-----------|---------------|
| SimNow YAML configs | asp-fmc, amd-tee3_0, art-security, dcgpu-esid, MPRAS-Kernel, nht-firmware, VBL-TEE-Drv |
| GoogleTest | pcie-cld-fw, ucie-fw |
| CppUTest | dcgpu-esid, mpio |
| Zephyr Twister | mpifoe-fw |
| pytest | mpifoe-fw |
| Custom C tests | MPRAS-Kernel, art-security |
| Custom simulator | dcgpu-esid, VBL-TEE-Drv |
| None | pmfw-firmware, sriov-dr, nht-firmware, cp-mi400, sw-security-tools |
