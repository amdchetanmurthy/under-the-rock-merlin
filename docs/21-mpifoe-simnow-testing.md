# MPIFoE SimNow Testing — Setup & Procedures

**Sources:**
- https://amd.atlassian.net/wiki/spaces/CNS/pages/1400513504 (IFoE Component List & Ownership)
- https://amd.atlassian.net/wiki/spaces/CNS/pages/1211370711 (MPIFoE Regression Testing)
- https://amd.atlassian.net/wiki/spaces/EN/pages/1506345840 (MPIFoE Firmware Architecture)

---

## SimNow Setup for MPIFoE

### Workspace
```bash
ssh xcbl-rtl01.xilinx.com  # using NTID
cd /scratch/${USER}/
git clone git@github.com:pensando/mpifoe-fw.git
cd mpifoe-fw
git submodule update --init --recursive  # PFO readonly access needed
git checkout -b user/<ntid>/<jira-id>
```

### Build for SimNow
```bash
rm -rf build/* && ./scripts/build.py -p simnow --eftest
cp build/fw.mi450-a0.simnow_eftest/zephyr/mpifoe_fw.hbin /scratch/${USER}/simnow/
```

### Launch SimNow
```bash
cd /scratch/${USER}/simnow/

# Single MID (M112):
/proj/smartnic/xcb/ifoe/simnow/sim111.sh \
  --ifwi MI450X_GENERIC_MI450_Baseline_BRP011_176291_PEMU_MTAG_UMC_APCB.sbin

# Dual MID (M222):
/proj/smartnic/xcb/ifoe/simnow/222.sh \
  --if /proj/smartnic/xcb/ifoe/simnow/MI450X_GENERIC_MI450_Baseline_BRP015_RSA_180337_standard.sbin
```

### Launch QEMU (in separate window)
```bash
/scratch/${USER}/simnow/launch-qemu.sh
# For dual MID: wait until "simnow" prompt before launching QEMU
# Ubuntu boots: root/l1admin
apt update -y && apt install -y gcc libmnl-dev libnl-3-dev libnl-genl-3-dev pkg-config xterm && resize

# Configure IFoE (4x200G, all subsystems):
/simnow/xncmdclient --force-enable-mmap -c 'ifoe_bios 4x200 0 3ffff 0; ifoe_next_phase PROVIDER; quit;' tlp=0
```

---

## MPIFoE Firmware Architecture Summary

### 11 Threads (Zephyr RTOS, SiFive E6-A RISC-V @ 800MHz)

| Thread | Priority | Purpose |
|--------|----------|---------|
| evq | 2 (highest) | Event queue doorbell processing |
| mid_rpc_chip_link | 2 | Inter-chip RPC for multi-die |
| command | Default | MCDI command dispatcher |
| host_traffic | 3 | Packet RX/TX via MRPIO |
| ifoe_ping | 3 | L2Ping network health checks |
| telemetry_manager | 3 | Stats collection (1s period) |
| dma_lib | DMA | DMA job queue manager |
| chip_ipc | IPC | Intra-chip IPC protocol |
| mp_listener | Default | MP0/MP1 message handler |
| to_mp | Config | Outgoing MP communications |
| cmd_test | 0 | Test only (--with-test-thread) |

### Inter-MP Communication

| Source → MP IFoE | Channel | Purpose |
|------------------|---------|---------|
| ASP (MP0) | SMN Mailbox | Security events, topology, TDISP, key provisioning |
| PM (MP1) | SMN Mailbox | PCIe FLR events, power states, reset coordination |
| MPIO | Hardware | KPX/PHY config at boot (before MP IFoE starts) |
| Host | MCDI (PCIe) | Configuration commands, telemetry requests |

### Configuration Phases
```
System Config (boot) → Provider Config (AIFM) → Tenant Config (VPM) → Mission Mode
```

---

## Current Regression Tests

From Jenkins (`xcb-jenkins-ifoe.amd.com`):

| Test | Method | Duration |
|------|--------|----------|
| Inst 0 Loopback | SimNow + QEMU + xncmdclient | ~8 min |
| RAS error injection | SimNow | TBD |
| MCDI version test | SimNow + QEMU | TBD |

### Regression Test Flow
1. Checkout mpifoe-fw
2. Build with `./scripts/build.py -p simnow --eftest`
3. Create SimNow workspace, link mpifoe binary
4. Create fake stdin pipe for SimNow console input
5. Launch SimNow in background, wait 6 min
6. Launch QEMU in background, wait 2 min
7. Copy MCDI cfg file to QEMU accessible path
8. Run xncmdclient with cfg file via SSH
9. Echo loopback command to fake stdin
10. Wait 1 sec, kill SimNow, grep logs for pass/fail

---

## Git Repos

| Component | URL |
|-----------|-----|
| mpifoe-fw (main) | github.amd.com/PFO/mpifoe-fw |
| mpifoe-fw (mirror) | github.com/pensando/mpifoe-fw |
| ASP | github.amd.com/PFO/asp-fmc |
| ifoe driver | github.com/pensando/ifoe-drv |
| ualoe lib | github.com/pensando/ualoe_access_lib |
| ualoe tests | github.com/pensando/ualoe_config_tests |
| ifcp | github.com/pensando/ifcp |
| ainic-rtos | github.com/pensando/ainic-rtos |
| afmctl/heliforge | github.com/pensando/ifoe-sw |
| aicc | github.com/pensando/aicc-dev |
| bringup scripts | gitenterprise.xilinx.com/SmartNIC/ifoe-bringup-scripts |
