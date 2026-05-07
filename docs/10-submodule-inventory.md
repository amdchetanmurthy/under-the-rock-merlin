# UnderTheRock Submodule Inventory

**Repo:** /home/cmurthy/utr/under-the-rock-main
**Date:** May 5, 2026
**Total Submodules:** 40
**Clone script:** memory-bank/scripts/clone-submodules.sh

## Network Summary (This Machine)

| Host | Ping | SSH | HTTPS | Status |
|------|------|-----|-------|--------|
| github.com | OK | OK (key: `amdchetanmurthy`) | OK | **Working** |
| github.amd.com | OK | Hangs (banner exchange) | OK with PAT `ghp_0Fc...` | **HTTPS only** |
| er.github.amd.com | OK | Hangs | OK with PAT `ghp_pGR...` | **HTTPS only** |
| mkdcgit.amd.com (Gerrit) | OK | Hangs (port 29418 open) | Refused (no HTTPS) | **Blocked** |
| gitlab.sysip.amd.com | OK | N/A | Port 80 open, 443 refused | **HTTP only, no repo access** |

**Root cause:** SSH banner exchange blocked on this AWS EC2 machine for all AMD-internal hosts. ICMP and TCP connect succeed, but the SSH server never sends its version banner.

## Successfully Checked Out (16)

| # | Submodule | Host | Transport | Path | Branch | Files | IFWI Component |
|---|-----------|------|-----------|------|--------|-------|----------------|
| 1 | asp-fmc | github.amd.com | HTTPS+PAT | firmware/asp-fmc | amd-staging | 609 | 0x0001 MPASP_FMC |
| 2 | pmfw-firmware | github.amd.com | HTTPS+PAT | firmware/pmfw-firmware | dev/mi450-main | 1472 | 0x0008 PMFW, IMU, AID/XCD MP5 |
| 3 | mpio | github.amd.com | HTTPS+PAT | firmware/mpio | rel/mi450 | 1103 | 0x005d MPIO FW |
| 4 | MPRAS-Kernel | github.amd.com | HTTPS+PAT | firmware/MPRAS-Kernel | rel/mi450 | 123 | 0x006b MPRAS FW |
| 5 | art-security | github.amd.com | HTTPS+PAT | firmware/art-security | amd-staging | 525 | 0x00ab/ac MPART FMC+Runtime |
| 6 | MPRAS-Applets | github.amd.com | HTTPS+PAT | firmware/MPRAS-Applets | default | 144 | 0x0135 MPRAS Applet 2 |
| 7 | nht-firmware | github.amd.com | HTTPS+PAT | firmware/nht-firmware | dev/mi450_bringup | 114 | 0x01e0 MPNHT FW |
| 8 | mpifoe-fw | github.amd.com | HTTPS+PAT | firmware/mpifoe-fw | main | 672 | 0x01f3 MPIFoE FW (IFoE) |
| 9 | VBL-TEE-Drv | github.amd.com | HTTPS+PAT | firmware/VBL-TEE-Drv | main | 569 | 0x01fb VBL Runtime Driver |
| 10 | cp-mi400 | github.amd.com | HTTPS+PAT | firmware/cp-mi400 | p4-main | 844 | CP: Command Processor |
| 11 | caliptra-sw | github.com | SSH | firmware/caliptra-sw | default | 1162 | 0x00a8 Caliptra Root of Trust |
| 12 | pytorch | github.com | SSH | firmware/pytorch | main | 19383 | ROCm PyTorch |
| 13 | amd-tee3_0 | er.github.amd.com | HTTPS+PAT | firmware/amd-tee3_0 | amd-staging | 3346 | 0x0002 TEE TOS + 13 drivers |
| 14 | dcgpu-esid | er.github.amd.com | HTTPS+PAT | firmware/dcgpu-esid | main | 1781 | 0x0157-015c eSID TOC + eSID 0-4 |
| 15 | sriov-dr | er.github.amd.com | HTTPS+PAT | firmware/sriov-dr | main | 66 | 0x01f7 TEE SRIOV Driver |
| 16 | sw-security-tools | er.github.amd.com | HTTPS+PAT | firmware/sw-security-tools | amd-staging | 14751 | 0x0055 ASP Anti Rollback |

---

## Still Missing (24) — Setup Instructions Per Category

### Category 1: github.com Private Repos — Need Org Access (15)

These repos are on **github.com** (not github.amd.com). Your account `amdchetanmurthy` does not have access.

**How to get access:**
1. Go to https://techprotect.amd.com/access/user_control/
2. Request these tech project groups: `amd_github`, `gfx_doc`, `mi400`, `mi400.4erm`
3. Ask PFO org owners to grant your `amdchetanmurthy` account access: https://github.amd.com/orgs/PFO/people?query=role%3Aowner
4. For AMD-Radeon-Driver specifically, contact the org admin or your manager to add `amdchetanmurthy` to the `AMD-Radeon-Driver` org on github.com

| # | Submodule | URL | Branch | IFWI Component |
|---|-----------|-----|--------|----------------|
| 1 | drivers-ipconfig | github.com:AMD-Radeon-Driver/drivers.git | amd/main/.../ipconfig | 0x0020 IP Discovery, 0x005c SPIROM |
| 2 | drivers-ip_fw | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/ip_fw | Binary FW for SoC15/Brick |
| 3 | drivers-ip_fw_pmfw | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/ip_fw_pmfw | SMU PM FW staging |
| 4 | drivers-lsdma | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/lsdma | LSDMA controller |
| 5 | drivers-mes | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/mes | MES: HW Scheduler |
| 6 | drivers-psp | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/psp | PSP - TOS |
| 7 | drivers-sdma | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/sdma | SDMA engine |
| 8 | drivers-sdma_ip_fw | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/sdma/.../sdma | SDMA FW |
| 9 | drivers-pplib | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/pplib | SMU FW payload |
| 10 | drivers-vcn | github.com:AMD-Radeon-Driver/drivers.git | amd/stg/vcn | VCN FW |
| 11 | KeyDB | github.com:AMD-Firmware/KeyDB.git | amd-staging | 0x0050 ASP BL Key DB |
| 12 | DMU | github.com:AMD-Radeon-Driver/DMU.git | default | DMCUB FW |
| 13 | powerplay-utils | github.com:AMD-Radeon-Driver/powerplay-utils.git | amd/main/.../ip_discovery | PSP IP discovery |
| 14 | mi300x_ubb_soteria_fw | github.com:AMDESE/mi300x_ubb_soteria_fw.git | default | AMC ERoT FW |
| 15 | amd-node-check | github.com:AMD-DCTOOLS/amd-node-check.git | main | Node health checks |

**Note:** All 10 `drivers-*` submodules point to the SAME repo (`AMD-Radeon-Driver/drivers.git`) with different branches. Once you get access, all 10 will work.

**Once you have access, clone with SSH** (already works from this machine):
```bash
git clone --depth 1 --branch amd/stg/ip_fw git@github.com:AMD-Radeon-Driver/drivers.git firmware/drivers-ip_fw
```

### Category 2: er.github.amd.com — No Access to Repo (1)

| # | Submodule | URL | Branch | IFWI Component |
|---|-----------|-----|--------|----------------|
| 1 | unicrypt | er.github.amd.com:PFO/unicrypt.git | amd-staging | 0x009d/00ae LibROM Overlays |

**How to get access:**
1. Log in to https://er.github.amd.com
2. Request access to the `PFO` org — contact PFO org owners
3. Tech project group needed: `pfo.readonly.er` or `mi400.er_aie`

**Once you have access:**
```bash
git clone --depth 1 --branch amd-staging https://er.github.amd.com/PFO/unicrypt.git firmware/unicrypt
```
(PAT for er.github.amd.com is already stored in `~/.git-credentials`)

### Category 3: github.amd.com/NBIOFW — No Access to Org (2)

| # | Submodule | URL | Branch | IFWI Component |
|---|-----------|-----|--------|----------------|
| 1 | pcie-cld-fw | github.amd.com:NBIOFW/pcie-cld-fw.git | default | 0x00b5 CLD Firmware |
| 2 | ucie-fw | github.amd.com:NBIOFW/ucie-fw.git | main | 0x01ec UCIe PHY FW |

**How to get access:**
1. Go to https://techprotect.amd.com/access/user_control/
2. Request tech project group: `nbiofw.read_only`
3. Or contact NBIOFW org admin on github.amd.com

**Once you have access:**
```bash
git clone --depth 1 https://github.amd.com/NBIOFW/pcie-cld-fw.git firmware/pcie-cld-fw
git clone --depth 1 --branch main https://github.amd.com/NBIOFW/ucie-fw.git firmware/ucie-fw
```
(PAT for github.amd.com is already stored in `~/.git-credentials`)

### Category 4: Gerrit — SSH Blocked From This Machine (4)

| # | Submodule | SSH URL | IFWI Component |
|---|-----------|---------|----------------|
| 1 | ras-ta | ssh://gerritgit/sw-security/ec/ras-ta | 0x0065 ASP RAS TA |
| 2 | udk2018 | ssh://gerritgit/amd/ec/uefigop/udk2018 | GOP: UEFI display driver |
| 3 | pmfw-ec-firmware | ssh://gerritgit/pmfw/ec/firmware | PMFW: Power management FW |
| 4 | ip_fw | ssh://gerritgit/amd/ec/p4/vendor/amd/proprietary/drivers/ip_fw | PSP security policy/RLC |

**Hostname resolution** (add to `~/.ssh/config`):
```
Host gerritgit
    HostName mkdcgit.amd.com
    PubkeyAcceptedAlgorithms +ssh-rsa
    User <your-ntid>
    Port 29418
```

**Problem:** SSH port 29418 on mkdcgit.amd.com (172.24.2.203) is reachable at TCP level but hangs at banner exchange — same issue as github.amd.com:22. No HTTPS alternative exists for Gerrit.

**Workaround options:**
1. Clone from a machine where SSH works (corporate desktop, VDI) and rsync to this EC2
2. Ask the Gerrit admin if HTTPS clone is available (gerrit-git.amd.com might have HTTPS)
3. Use the Gerrit web UI to download tarballs: https://gerrit-git.amd.com/plugins/gitiles/

**To verify access** (from a machine where SSH works):
```bash
ssh -p 29418 <ntid>@mkdcgit.amd.com gerrit version
```

### Category 5: gitlab.sysip.amd.com — No Repo Access (1)

| # | Submodule | URL | IFWI Component |
|---|-----------|-----|----------------|
| 1 | rib | gitlab.sysip.amd.com:df-firmware/rib.git | 0x0076 DF RIB |

**Status:** HTTP port 80 is open, HTTPS port 443 refused. Token `kc5jCxxyHjz-QeH6a4CK` is valid but your account doesn't have access to `df-firmware/rib`.

**How to get access:**
1. Log in to http://gitlab.sysip.amd.com
2. Navigate to the `df-firmware` group and request access
3. Contact DF firmware team (Krishna Bernucho per BKC modules sheet)

**Once you have access:**
```bash
git clone --depth 1 http://oauth2:<token>@gitlab.sysip.amd.com/df-firmware/rib.git firmware/rib
```

### Category 6: Large Repo Timeout (1)

| # | Submodule | URL | Branch | Notes |
|---|-----------|-----|--------|-------|
| 1 | onnxruntime | github.com:ROCm/onnxruntime.git | main | Public, SSH works, but clone timed out (120s) |

**Fix:** Clone with longer timeout or shallower depth:
```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --single-branch --branch main git@github.com:ROCm/onnxruntime.git firmware/onnxruntime
```

---

## Non-Git Sources (Not Submodules)

| FW ID | Name | Source | Contact |
|-------|------|--------|---------|
| 0x0009 | Secure Policy RSMU Init | Perforce: `perforce:1677//sysip/smu/doc/security/policy/fsdl_v4/variants/mi400/` | Anas Siraj |
| 0x0024 | Security Policy L0 | Perforce: `atlvp4p01.amd.com:1677` | Anas Siraj |
| 0x0045 | Security Policy TOS Late | Perforce: `perforce.amd.com:1677` | Anas Siraj |
| 0x004f | UMC FW | Perforce: `atlvp4s12.amd.com:1711/depot/umc4/branches/UMC_15_0_MI400_MAIN` | Jin Chung Teng |
| 0x0101 | Secure Policy L1 | Perforce: `perforce.amd.com:1677` | Anas Siraj |
| 0x0147 | Mem Init Config Table | Config (no source) | Sai Kammila |
| 0x01f9 | GTA PHY | Pending permission/url | Ed C. Lee |
| 0x01fa | IFOE PHY | Pending permission/url | Ed C. Lee |
| 0x1053-1057 | APCB variants | IFWI Builder config | Marco Herdia |
| — | AINIC bundles | Artifactory: `repo.radeon.com/amdainic/pensando` | Vijay Gopinath |

---

## Summary

| Status | Count | Action |
|--------|-------|--------|
| Checked out | 16 | Done |
| Need github.com org access | 15 | Request via techprotect + org admin |
| Need er.github.amd.com repo access | 1 | Request PFO/unicrypt access |
| Need github.amd.com/NBIOFW access | 2 | Request `nbiofw.read_only` group |
| Gerrit SSH blocked | 4 | Clone from corp machine or request HTTPS |
| gitlab.sysip.amd.com no repo access | 1 | Request df-firmware group access |
| Large repo timeout | 1 | Retry with longer timeout |
| Non-git (Perforce/Artifactory) | ~10 | Not applicable to git checkout |
| **Total** | **40 + ~10** | |

## Credentials Stored

| Host | File | Type |
|------|------|------|
| github.com | ~/.ssh/id_ed25519 | SSH key (amdchetanmurthy) |
| github.amd.com | ~/.git-credentials | HTTPS PAT |
| er.github.amd.com | ~/.git-credentials | HTTPS PAT |
| gitlab.sysip.amd.com | (manual) | GitLab token `kc5j...` |
