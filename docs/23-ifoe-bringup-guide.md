# IFoE Bringup Guide — Real Hardware Procedures

**Source:** https://amd.atlassian.net/wiki/spaces/EN/pages/1400811597/IFoE+bringup

---

## Access Requirements

| System | URL | Groups Needed |
|--------|-----|---------------|
| techprotect | https://techprotect.amd.com/access/user_control/ | mi300_doc.4erminus, mi400_doc, mi400_doc.4er, pfo.readonly, pfo.readonly.er, amd_github, amd_github.er |
| Conductor | https://conductor.amd.com/dashboard | Login with NTID, team member onboards you |
| McnABB pool | https://conductor.amd.com/system/pool?id=ae14a66e-... | Needed for AHDS & MI4xx setup |

**Note:** Permission propagation takes ~24 hours after access grant.

---

## Testbed Types

### SLT System
- Socketed GPU
- Loopback from some ports MID0 → MID1
- Can boot 0P1G (MI450 only) or 1P1G (MI450 + Venice A+A)

### EAM System
- Soldered GPU
- All ports connected back to self on MID1
- Can boot 0P1G or 1P1G

**Testbed details:** [ScaleUP setups.xlsx](https://amdcloud-my.sharepoint.com/:x:/r/personal/visriniva_amd_com/Documents/ScaleUP%20setups.xlsx)

---

## Build MPIFoE Firmware

### Build Server
```bash
ssh -J xcb-labjmp01.xilinx.com xcb-build-ainic-01.xilinx.com -l ${NTID}
bash  # use bash for full build

WS=/scratch/$(whoami)/myws/src/github.amd.com/PFO/
mkdir -p ${WS}
cd ${WS}
git clone https://github.amd.com/PFO/mpifoe-fw.git
git submodule update --init --recursive
export PATH=/tools/pandora/bin/:${PATH}
```

### Build for Silicon
```bash
source /proj/smartnic/xcb/ifoe/zephyr-build-env.sh
rm -rf build/*
./scripts/build.py -b "minirack" -p silicon -s mi450-a0 --eftest
```
Output: `./build/amd_mi450_mpifoe_eftest/zephyr/mpifoe.hbin`

### Build for SimNow
```bash
rm -rf build/*
./scripts/build.py -p simnow --eftest
```
Output: `build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.hbin`

---

## Test Images

### IFWI Image
- Version tracking: https://ontrack-internal.amd.com/browse/FWDEV-171274
- Download: `https://mkmartifactory.amd.com:8443/ui/repos/tree/General/dgpu-spirom-fw/mi450/pre_release/ifwi/`

### PLDM Image Creation
```bash
# On xcbfwbuild03 (Ubuntu only)
git clone https://gitenterprise.xilinx.com/SmartNIC/ifoe-bringup-scripts.git
cd ifoe-bringup-scripts
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/pbalakri/Downloads/share/
./scripts/patch-pldm.sh pldm/AMD_MI450_01.25.04.13 /path/to/mpifoe_fw.hbin
```

---

## Host Tools Installation

### xncmdclient
```bash
# Download from: https://amd.atlassian.net/wiki/spaces/CNS/pages/1407737726
scp xcbl-rtl01:/home/pbalakri/Downloads/share/xncmdclient /tmp/

# Usage
./xncmdclient --force-enable-mmap tlp=0
# MCC> version
# MCC> ifoe_bios 4x100 0 fffc0000 ffffffff
# MCC> ifoe_next_phase PROVIDER
```

### IFoE Driver
```bash
wget --no-check-certificate \
  https://xcbartifactory01.xilinx.com/artifactory/ifoe-dev-local/com.xilinx/ifoe-ifoe_drv.mi450.x86_64/<version>/ifoe-drv-<version>.tar.gz

apt install -y libmnl-dev libnl-3-dev libnl-genl-3-dev pkg-config
tar -xzf ifoe-drv-*.tar.gz
cd ifoe-drv-*/linux/
make -j32
insmod ifoe.ko
insmod ifoe-cfg.ko
```

### ualinkctl
```bash
wget --no-check-certificate \
  https://xcbartifactory01.xilinx.com/artifactory/ifoe-dev-local/com.xilinx/ifoe-ualoe_ctl.mi450.x86_64/<version>/ualink-ctl-<version>.tar.gz

# Quick tests:
sudo ./ualink_ctl 0001:00:01.1 --version
sudo ./ualink_ctl 0001:00:01.1 --ifoe-info
sudo ./ualink_ctl 0001:00:01.1 --get-caps
sudo ./ualink_ctl 0001:00:01.1 --get-config=128
```

---

## Running IFoE Control Plane Tests

```bash
# Clone repos
git clone https://github.com/pensando/ualoe_access_lib
git clone https://github.com/pensando/ifoe-drv
git clone https://github.com/pensando/ualoe_config_tests

# Build and load drivers
cd ifoe-drv && make -C linux
sudo insmod linux/ifoe.ko
sudo insmod linux/ifoe-cfg.ko

# Build ualinkctl
sudo apt install libmnl-dev libnl-genl-3-dev -y
cd ualoe_access_lib/ualink_ctl && make

# Build and run tests
sudo apt install cmake libpci-dev -y
cd ualoe_config_tests
git submodule update --init
make clean -C lib/ualoe_access_lib/ualoe_lib/
make -C lib/ualoe_access_lib/ualoe_lib/
cmake -DCFG_ASAN=y -S . -B build
cmake --build build
sudo ctest --test-dir build --output-on-failure

# Note: first configure IFoE
xncmdclient -c 'ifoe_bios 2x400 0 3ffff; ifoe_next_phase PROVIDER; quit;' --force-enable-mmap tlp=0
```

---

## UPI2 Manual Sequence (Register-Level PHY Access)

Real register addresses from bringup session:
```
# Station address mapping (sta=904 for MID0 station 0)
# PCS registers at offset ${sta}91xxx
# PHY registers at offset ${sta}f0xxx

# PCS Resync: reset port
ifoe_io_write 0 0 ${sta}91010 1    # PCS reset
ifoe_io_write 0 0 ${sta}910f0 1    # FEC reset
ifoe_io_write 0 0 ${sta}900f0 10   # SERDES reset

# PCS Resync: unreset port
ifoe_io_write 0 0 ${sta}91010 0
ifoe_io_write 0 0 ${sta}910f0 0
ifoe_io_write 0 0 ${sta}900f0 0

# TX Sync init
ifoe_io_write 0 0 ${sta}f0018 0    # Clear
ifoe_io_write 0 0 ${sta}f0018 0xff # Pulse
ifoe_io_write 0 0 ${sta}f0018 0    # Clear

# Read PCS counters (per port, 3 words)
ifoe_io_read 0 0 ${sta}91c00 3
# 0x00000000 = clean, 0x0bad0bad = no link

# UPI2 command to station/lane
cmd af d7e '<STATION> '<LANE> <OPCODE> <PARAM>

# Suspend FW operations on port
cmd af c7e '<PORT> 1
```

---

## Known Issues

- FLR reset stubbed (FWDEV-165197/165198)
- MID1 DMA host memory issue (affects ualinkctl)
- ASP fw status 80EB0006 debug unclear
- APCB player v3.1.8.0 location on thick client
