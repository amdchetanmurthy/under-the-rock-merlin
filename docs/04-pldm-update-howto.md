# EAM BKC PLDM Update - Complete HOWTO

## Overview

This documents the complete procedure for performing PLDM Bundle updates on MI450/MI455 EAM hardware via BMC/AMC Redfish interface.

## Pre-Update: Check AMC Readiness

When the PHC loads the IFWI from the PHC Image Flash, the AMC is NOT ready for PLDM Bundle updates because:
- The AST must access the PHC Image Flash for PLDM Bundle Update
- The PHC is accessing the PHC Image Flash for IFWI update
- Both PHC and AST cannot access the PHC Image Flash simultaneously

### Check PHCA::PHC::CFGOWNER Bit

1. SSH into the AMC (pw: `0penBmc`)
2. Run: `ssh 192.168.31.1`
3. Run: `amd-phc-uart phca dump 1`

**If IFWI programming is still in progress:**
```
No response received from PHC.
Check PHC firmware is running and UART is configured.
```
- Single-EAM: wait 3-5 minutes
- Multi-EAM: wait N × (3-5 minutes) where N = number of EAMs

**Successful response — check Bit 8 of SR0 must be '1':**
```
RegId: 3 : SR0 : 0x00000100  # <== Bit 8 set to '1' = SAFE to proceed
```

## PLDM Update Steps

1. **SSH into BMC:**
   ```bash
   ssh root@<bmc-hostname>  # pw: 0penBmc
   ```

2. **SCP the PLDM bundle to BMC:**
   ```bash
   scp <pldm-bundle> root@<bmc-hostname>:/tmp
   ```

3. **Perform the update (from BMC):**

   **BKC_T25.04.XX onwards (MUST use this command — works for ALL BKCs):**
   ```bash
   curl -k -u "root:0penBmc" -H "Content-Type: multipart/form-data" -X POST \
     -F "UpdateParameters={\"ForceUpdate\":true};type=application/json" \
     -F "UpdateFile=@AMD_MI450_06.25.05.69.pldm;type=application/octet-stream" \
     http://192.168.31.1/redfish/v1/UpdateService/update-multipart
   ```

   **Before BKC_T25.04.XX:**
   ```bash
   curl -k -u "root:0penBmc" -H "Content-type:application/octet-stream" \
     -X POST -T <BKC-pldm-filename>.pldm \
     http://192.168.31.1:80/redfish/v1/UpdateService/update
   ```

4. **Check status:**
   ```bash
   curl -u "root:0penBmc" -k http://192.168.31.1:80/redfish/v1/TaskService/Tasks/0
   ```

5. **Workaround if 100% completion with Warning (TaskState: Exception, TaskStatus: Warning):**
   ```bash
   ssh root@192.168.31.1
   cd /tmp/images_pldm
   rm rot_pldm.pldm          # May not be present — that's OK
   systemctl restart pldmd.service
   exit
   # Then re-do the update
   ```

6. **AC cycle to activate the new bundle**

7. **Verify version:**
   ```bash
   curl -u "root:0penBmc" -k -X GET \
     'http://192.168.31.1:80/redfish/v1/UpdateService/FirmwareInventory?$expand=*($levels=1)'
   ```

## Creating Custom/Test Bundles

### Choosing a Test BKC Version Number

Use least significant 2 digits starting with 99 and decrement:

1. Copy `full_build_dir` into local folder
2. Open `build.bat`
3. Update `packageName` variable: e.g., `AMD_MI450_01.26.01.99`
4. Put custom component binaries in `full_build_dir/mi4xx_components`
5. Update `mi450-recipe.json` with new filenames
6. Run `build.bat`
7. After flash + AC cycle, verify:
   ```bash
   curl -u "root:0penBmc" -k -X GET http://192.168.31.1:80/redfish/v1/UpdateService/FirmwareInventory/PLDM_BUNDLE
   ```
   Response should show `"Version": "2.01.26.01.99"`

### Base BKC Build Location
```
\\pharaoh-corp\dcgpuval\sde-validation\projects\MI450\bkc-artifacts\PRE-PRODUCTION
```

### BKC Artifact Streams
- **Rev B** EAM/SLT Stream: `BKC_T25.xx.yy`
- **Rev C** EAM/SLT Stream: `BKC_T26.xx.yy`

## Key Rotation

### Flow
1. Perform PLDM update with **Transition bundle** first (MUST-HAVE)
2. AC Cycle
3. Update to **"Go Forward"/Regular** PLDM bundle to complete transition

### Transition Bundle Location
```
\\pharaoh-corp\dcgpuval\sde-validation\projects\MI450\bkc-artifacts\PRE-PRODUCTION\BKC_T25.04\AMD_MI450_01.25.04.15_Transition\
```

### Go Forward Bundle Location
```
\\pharaoh-corp\dcgpuval\sde-validation\projects\MI450\bkc-artifacts\PRE-PRODUCTION\BKC_T25.04\AMD_MI450_01.25.04.15\
```

### Identifying Key State via ROT FW Version
- `v2.1.x` → Old Keys
- `v2.2.0` → Transition
- `v2.2.1+` → Go Forward/Regular ROT FW with new keys

**Check ROT FW version:**
```bash
curl -u "root:0penBmc" -k -X GET \
  'http://192.168.31.1:80/redfish/v1/UpdateService/FirmwareInventory?$expand=*($levels=1)'
# Search for EROT_FW in output
```

### Key Rotation History
- Rev B - Initial rotation started at: `BKC_T25.04.14`
- Rev C - Initial rotation started at: `BKC_T26.01.01`

**After key rotation:**
- Cannot go back to previous Rev B EAM/SLT BKCs
- Can only use BKCs with new keys
- Need at minimum v1.0.0 of the Bundler tool
- RECOMMENDED: Use Bundler tool included in `full_build_dir` in the BKC release folder

## Rev C Multi-EAM SPI Flash Access Workaround (PLAT-195733)

### Option 1 (Try First)
```bash
# SSH into AMC
echo 4 > /sys/module/xilinx_xdma/parameters/max_bar_writes_before_read
# Then proceed with normal PLDM update
```

### Option 2 (Try Second)
```bash
# SSH into AMC
mctp link set mctpserial0 down
mctp link set mctpserial1 down
mctp link set mctpserial2 down
mctp link set mctpserial3 down
mctp link set mctpserial4 down
systemctl restart pldmd
# Then proceed with normal PLDM update
```

### Option 3 (If Options 1-2 Fail)
**Pre-requisite:** An officially released Rev C single-EAM BKC must be on either inactive or active flash side.

1. SSH into AMC
2. Check active side: `erot_test -t activeget` (returns side 0 or 1)
3. Check component versions: `erot_test -t compinfo`
4. If single-EAM is active side → proceed normally
5. Otherwise: `erot-cli toggle-flash`
6. AC cycle
7. Now running single-EAM bundle → proceed with multi-EAM update
8. AC cycle
9. Done

## Hash Mismatch Workaround

**Symptom:** After PLDM update + AC cycle, AMC did not boot to your BKC (flash corruption).

**Applies to:**
- Rev B: `BKC_T25.04.13` or earlier
- Rev C: `BKC_T26.00.05` or earlier

### Two-Step Procedure

**Step A: Update ROT only**
1. SSH BMC → AMC (`ssh root@192.168.31.1`)
2. Edit `/etc/bundle-update/policy.conf`:
   - `rot_update_enabled=true`
   - `amc_update_enabled=false`
   - `phc_update_enabled=false`
3. Perform bundle update from BMC
4. **DO NOT AC CYCLE**

**Step B: Update AMC + PHC**
1. SSH BMC → AMC
2. Edit `/etc/bundle-update/policy.conf`:
   - `rot_update_enabled=false`
   - `amc_update_enabled=true`
   - `phc_update_enabled=true`
3. Perform bundle update from BMC (check Task/1 instead of Task/0)
4. AC cycle to activate

## Version Checking

### PLDM Bundle Version (from BMC via Redfish)
```bash
curl -u "root:0penBmc" -k -s http://<bmc-ip>/redfish/v1/UpdateService/FirmwareInventory/PLDM_BUNDLE | jq -r .Version
```

### AMC FW Version (from AMC)
```bash
ssh root@192.168.31.1  # pw: 0penBmc
cat /etc/os-release | grep PRETTY_NAME
```

### Full Inventory (via DBus on AMC)
```bash
busctl introspect xyz.openbmc_project.Software.BMC.Updater /xyz/openbmc_project/software/PLDM_BUNDLE | grep -E '\bVersion\b'
busctl introspect xyz.openbmc_project.Software.BMC.Updater /xyz/openbmc_project/software/AMC_FW
busctl introspect xyz.openbmc_project.Software.BMC.Updater /xyz/openbmc_project/software/PHC_FPGA
```

### PHC Console (from AMC)
```bash
amd-phc-uart directio ver              # PHC FPGA Version
amd-phc-uart directio dump 1           # AMC FPGA/Microcode (FIBIR=FPGA, MIBIR=Microcode)
amd-phc-uart directio dump 2           # EAM FPGA/Microcode
```

## AMC/PHC/ROT Compatibility Matrix

### Terminology
| Term | Definition |
|------|-----------|
| Bobcat Classic | PHC design for Rev **B** EAM/SLT |
| Bobcat | PHC design for Rev **C** EAM/SLT |
| Puma | AMC PHC design for N x EAM/SLT support (N <= 4) |
| Eagle Classic | AMC PHC design for N x Rev **B** EAM/SLT support (N <= 4) |
| Eagle | AMC PHC design for N x Rev **C** EAM/SLT support (N <= 4) |

### Matrix
| AMC branch | AMC Version | PHC | ROT | Notes |
|------------|-------------|-----|-----|-------|
| amd_amc_g406_dev_1p1g | v6.a.b.c.d | v0.9.x, v0.10.x | v2.2.1 | Bobcat and Bobcat Classic |
| amd_amc_g406_dev | v7.a.b.c.d | v0.11.x, v0.12.x | v2.2.3 | Puma, Eagle Classic, Eagle |
| mi4xx (OpenBMC 2.18) | v8.a.b.c.d | v0.11.x | v2.2.3 | Puma, Eagle Classic → Eagle |
| mi4xx-dev (OpenBMC 2.18) | v9.a.b.c.d | v0.11.x | v2.2.3 | Puma, Eagle Classic A2 + A1 |

## Default BMC/AMC Credentials
- **Username:** `root`
- **Password:** `0penBmc`
- AMC internal IP: `192.168.31.1`
