# MPIFoE Firmware Architecture

Domain knowledge for the AgentQ domain-expert agent. This file contains
key facts about the MPIFoE firmware architecture needed to understand
test results, diagnose failures, and provide domain-specific guidance.

---

## Overview

MPIFoE (MP IFoE) is the firmware running on the IFoE (Intelligent Fabric
over Ethernet) microprocessor inside AMD MI450 GPUs. It manages the IFoE
network fabric that connects GPUs in a scale-out cluster.

- **RTOS**: Zephyr on SiFive E6-A RISC-V @ 800MHz
- **Target ASIC**: MI450
- **Primary interface**: MCDI (Management Controller Device Interface) over PCIe
- **CLI tool**: xncmdclient (host-side MCDI command-line client)

## 11 Firmware Threads

| Thread | Priority | Purpose |
|--------|----------|---------|
| evq | 2 (highest) | Event queue doorbell processing |
| mid_rpc_chip_link | 2 | Inter-chip RPC for multi-die configurations |
| command | Default | MCDI command dispatcher (handles all xncmdclient commands) |
| host_traffic | 3 | Packet RX/TX via MRPIO |
| ifoe_ping | 3 | L2Ping network health checks |
| telemetry_manager | 3 | Stats collection (1-second period) |
| dma_lib | DMA | DMA job queue manager |
| chip_ipc | IPC | Intra-chip IPC protocol |
| mp_listener | Default | MP0/MP1 message handler |
| to_mp | Config | Outgoing MP communications |
| cmd_test | 0 | Test only (requires --with-test-thread build flag) |

## Configuration Phases

The firmware progresses through four phases in order:

```
System Config (boot) -> Provider Config (AIFM) -> Tenant Config (VPM) -> Mission Mode
```

- **SYSTEM**: Initial boot, hardware initialization
- **PROVIDER**: AIFM (AI Fabric Manager) configures the IFoE fabric
- **TENANT**: VPM (Virtual Partition Manager) configures tenant settings
- **MISSION**: Operational mode, all services active

Phase transitions are one-way. Use `ifoe_next_phase <PHASE>` to advance.
The firmware must be rebooted to return to SYSTEM phase.

## Inter-MP Communication

| Source -> MP IFoE | Channel | Purpose |
|-------------------|---------|---------|
| ASP (MP0) | SMN Mailbox | Security events, topology, TDISP, key provisioning |
| PM (MP1) | SMN Mailbox | PCIe FLR events, power states, reset coordination |
| MPIO | Hardware | KPX/PHY config at boot (before MP IFoE starts) |
| Host | MCDI (PCIe) | Configuration commands, telemetry requests |

## IFoE Subsystems

The IFoE fabric is organized into subsystem instances. The number of
active subsystems depends on the port mode:

| Port Mode | Lanes per Port | Active Subsystems |
|-----------|---------------|-------------------|
| 1x800 | 8 lanes | 1 subsystem |
| 2x400 | 4 lanes each | 2 subsystems |
| 4x200 | 2 lanes each | 4 subsystems |
| 4x100 | 1 lane each | 4 subsystems |

Subsystem mask 0x3ffff enables all 18 possible subsystem blocks.

## Key MCDI Commands

### Basic Health
- `version` -- firmware version (MC_CMD_GET_VERSION)
- `get_uptime` -- firmware uptime (MC_CMD_GET_UPTIME)
- `ifoe_get_current_phase` -- current config phase
- `ifoe_get_capabilities` -- firmware capabilities

### Port Management
- `enum_ports` -- enumerate all ports
- `link_state <port>` -- get link state (up/down, speed, FEC)
- `link_ctrl <port> up|down` -- bring link up or down
- `mac_state <port>` -- MAC layer state
- `get_fixed_port_properties <port>` -- fixed port properties
- `get_transceiver_properties <port>` -- transceiver info

### IFoE Configuration
- `ifoe_get_config` -- current IFoE configuration
- `ifoe_get_active_accelerators` -- active accelerator list
- `ifoe_get_enabled_accelerators` -- enabled accelerator list
- `ifoe_get_local_accelerators` -- local accelerator info
- `ifoe_get_src_net_addr` -- source network port addresses
- `ifoe_get_dst_net_addr_map` -- destination address map
- `ifoe_get_path_port_map` -- path-to-port mapping
- `ifoe_next_phase <PHASE>` -- advance to next phase

### Station Management
- `ifoe_enum_stations` -- enumerate IFoE stations
- `ifoe_station_get_state <id>` -- station state
- `ifoe_station_ctrl <id>` -- station control

### Connectivity
- `ifoe_ping_config <accel> <port> <count>` -- configure L2Ping
- `ifoe_ping_start <handle> <buffer>` -- start L2Ping
- `ifoe_ping_poll <handle>` -- poll L2Ping results
- `ifoe_ping_stop <handle>` -- stop L2Ping

### Telemetry
- `ifoe_telemetry_info` -- telemetry status
- `ifoe_telemetry_ctrl enable|disable` -- enable/disable collection
- `ifoe_telemetry_select <mask>` -- select stats to collect
- `ifoe_telemetry_dma_cfg <buffer>` -- configure DMA for telemetry

### Crypto (XRSEC)
- `ifoe_config_crypto <params>` -- configure crypto
- `ifoe_set_tx_crypto_key <key>` -- provision TX key
- `ifoe_set_rx_crypto_key <key>` -- provision RX key
- `ifoe_disable_rx_crypto_key` -- disable RX key

### EFTEST Commands (requires --eftest build)
- `eftest ifoe_bios_cfg <mode> <flags> <mask> <extra>` -- configure port mode
- `eftest ifoe_loopback_ctrl <inst> <mode>` -- loopback control
- `eftest ifoe_tx_pkt <inst>` -- transmit test packet
- `eftest ifoe_rx_pkt <inst>` -- receive/check test packet
- `eftest ifoe_ras_inject_error <inst> <type>` -- inject RAS error

### Register Access
- `read32 <address>` -- read 32-bit register
- `write32 <address> <value>` -- write 32-bit register

## Key Registers

| Register | Address | Expected Value | Meaning |
|----------|---------|---------------|---------|
| MPASP_FW_STATUS | 0x034000d8 | 0x800F0000 | All boot stages complete |

## SimNow Testing Environment

SimNow is the MI450 simulator used for pre-silicon firmware testing:
- Build: `./scripts/build.py -p simnow --eftest`
- Launch: `/proj/smartnic/xcb/ifoe/simnow/sim111.sh --ifwi <sbin>`
- QEMU: `/scratch/${USER}/simnow/launch-qemu.sh`
- Host: xcbl-rtl01.xilinx.com

## Limitations on Hardware

| Limitation | Why | Workaround |
|------------|-----|------------|
| No internal SRAM read | No debug access to RISC-V | Use MCDI read32 for mapped registers |
| No thread state visibility | No Zephyr debug console | Check heartbeat for liveness |
| No SMN bus tracing | No bus analyzer | Use MCDI for targeted register reads |
| No mailbox inspection | Mailbox consumed by FW | Enable MCDI logging (mcdi_logging_default=1) |
| No breakpoints | No JTAG in production | Use EFTEST for controlled behavior |

## Source Code References

- MCDI Protocol: `firmware/mpifoe-fw/external/smartnic_registry/mcdi/mc_driver_pcol_private.h`
- EFTEST Commands: `firmware/mpifoe-fw/src/managers/mcdi_manager/eftest_cmds.c`
- IFoE Config Commands: `firmware/mpifoe-fw/src/managers/mcdi_manager/ifoe_cfg_cmds.c`
- L2Ping Commands: `firmware/mpifoe-fw/src/managers/mcdi_manager/ifoe_ping_cmds.c`
- Station Commands: `firmware/mpifoe-fw/src/managers/mcdi_manager/ifoe_station_cmds.c`
