# MPIFoE Firmware Test Gap Analysis

**Date:** 2026-05-05
**Codebase:** `/home/cmurthy/utr/under-the-rock-main/firmware/mpifoe-fw/src/`
**Test Suite:** `/home/cmurthy/utr/under-the-rock-merlin/mpifoe-tests/`

---

## Executive Summary

Analysis of 361 source files (C + headers) across 7 major subsystem categories against 28 existing test cases reveals significant test gaps, particularly in error handling paths, state machine edge cases, inter-MP interactions, and hardware driver coverage. This analysis identifies 17 new test cases created to address the most critical gaps.

---

## Module-by-Module Analysis

### 1. Application Layer (`src/app/`)

| File | Lines | Function |
|------|-------|----------|
| main.c | 124 | Boot sequence, self-tests, heartbeat loop |

**Current Coverage:**
- `test-cases/sanity/fw-version.md` - Checks firmware version response
- `test-cases/sanity/fw-uptime.md` - Checks uptime counter
- `test-cases/unit/cache-flush-invalidate.md` - Tests cache self-tests

**Gaps Identified:**
- Boot self-test sequence (SMN, MBOX, DMA, Cache) results not systematically verified
- Heartbeat interval and interrupt_inspector_check_pics_and_repair() loop untested
- Failure modes of individual self-tests not tested (what happens when test_smn fails?)

**New Tests Created:**
- `test-cases/driver/smn-read-write.md` - SMN self-test verification
- `test-cases/driver/adma-transfer-test.md` - DMA self-test verification
- `test-cases/driver/mbox-claim-and-interrupt.md` - Mailbox self-test verification

**Remaining Gaps (need hardware):**
- interrupt_inspector idle check and repair cycle
- Heartbeat timing accuracy under load

---

### 2. MCDI Manager (`src/managers/mcdi_manager/`)

| File | Lines | Function |
|------|-------|----------|
| mcdi_manager.c | 472 | Command dispatch, doorbell handling, thread |
| ifoe_cfg_cmds.c | 1121 | IFoE config MCDI handlers (20+ commands) |
| ifoe_station_cmds.c | 381 | Station enumeration, control, path mapping |
| ifoe_ping_cmds.c | - | L2 ping MCDI handlers |
| driver_cmds.c | - | Driver-level commands |
| eftest_cmds.c | - | Engineering test commands |
| telemetry_cmds.c | - | Telemetry MCDI handlers |
| reset.c | 29 | Entity reset and FLR handling |
| privileges.c | - | Privilege management |
| rw_cmds.c | - | Read/write commands |
| version.c | - | Version reporting |
| mcdi_events.c | - | MCDI event generation |
| mcdi_send_events.c | - | Event sending to host |
| mcdi_utils.c | - | Error code mapping utilities |
| netport_mcdi.c | - | Netport MCDI handlers |

**Current Coverage:**
- `test-cases/sanity/fw-version.md` - Version command
- `test-cases/sanity/config-phase.md` - Phase query
- `test-cases/functional/phase-transition.md` - Phase transitions
- `test-cases/functional/station-mgmt.md` - Station management
- `test-cases/functional/crypto-key-provision.md` - Crypto key commands
- `test-cases/bringup/accelerator-discovery.md` - Get capabilities/accelerators
- `test-cases/bringup/ifoe-config.md` - IFoE config set/get

**Gaps Identified:**
- **Privilege enforcement not tested** - No test verifies that VF clients are rejected for provider commands
- **Wrong-phase command rejection untested** - Each command checks phase; no systematic test
- **Invalid command ID dispatch untested** - What happens with cmd ID > cmd_table size?
- **send_cmd_reply overflow guard untested** - payload_len > BITFIELD_MASK triggers EIO
- **Sideband MCDI path (CONFIG_TRANSPORT_IFCP) untested** - mcdi_manager_submit_request, buffer semaphore
- **Entity reset hook chain untested** - FINI+INIT sequence, hook ordering
- **FLR reset completely stubbed** - do_flr_reset is commented out (FWDEV-165197/165198)
- **Remote MCDI forwarding untested** - dispatch_cmd_to with mid_rpc_remote inspection
- **MCDI event sending to host untested** - mcdi_send_events flow
- **netport_mcdi handlers untested**

**New Tests Created:**
- `test-cases/unit/mcdi-privilege-check.md` - Privilege enforcement
- `test-cases/error-handling/mcdi-invalid-command.md` - Invalid command dispatch
- `test-cases/error-handling/ifoe-config-wrong-phase.md` - Phase restriction enforcement
- `test-cases/error-handling/crypto-key-boundary.md` - Crypto key error paths
- `test-cases/error-handling/address-mapping-boundary.md` - Address set/get boundaries
- `test-cases/interaction/sideband-mcdi-dispatch.md` - Sideband MCDI path
- `test-cases/interaction/pm-mpifoe-flr-reset.md` - Reset hook chain

**Remaining Gaps:**
- FLR reset (blocked by FWDEV-165197/165198 - code is stubbed)
- MCDI event queue write/read index synchronization stress
- Remote MCDI forwarding (needs dual-MID SimNow)

---

### 3. IFoE Manager (`src/managers/ifoe_manager/`)

| File | Lines | Function |
|------|-------|----------|
| ifoe_manager.c | 1642 | Config state machine, identity, network config, crypto, accelerators |
| logical_link_manager.c | 802 | Station lifecycle, netport handle mapping, link events |
| ifoe_datapath_hw_control.c | - | Hardware datapath control |
| ifoe_hooks.c | - | Hook registration system |
| mp1_pm_cmd_handler.c | - | PM command handling |
| mpasp_ifoe_cmd_handler.c | - | ASP IFoE commands |
| rpc/ifoe_manager_rpc.c | - | RPC handlers for dual-MID |
| rpc/logical_link_rpc.c | - | Logical link RPC |

**Current Coverage:**
- `test-cases/functional/phase-transition.md` - Forward transitions only
- `test-cases/functional/station-mgmt.md` - Basic station operations
- `test-cases/bringup/ifoe-config.md` - Config set/get

**Gaps Identified:**
- **Config phase state machine not exhaustively tested** - Missing: backward transitions, self-resets, DIAGNOSTICS phase, invalid transitions
- **Station lifecycle state machine incomplete** - DISABLED/STOPPED/ACTIVE transitions, power-up/down side effects
- **Datapath state derivation untested** - Truth table (phase x run_state -> datapath_state)
- **Dual-MID phase synchronization untested** - Three sync points with k_panic on desync
- **Config snapshot/restore untested** - Forward snapshot, backward restore, self-reset restore
- **Privilege modification on phase transition untested** - PROVIDER->TENANT grants TENANT privilege to VF
- **Virtualization mode effect on privileges untested** - Baremetal vs virtualized privilege assignment
- **Remote-only link configuration paths untested** - ifoe_manager_remote_only_links() true path
- **Path port map set/get untested** - ifoe_logical_link_set_path_port_map variants
- **Network config broadcast (bcst_*) functions untested** - Cross-MID config propagation
- **Accelerator iterator untested** - get_nth_active_accelerator, get_accelerator_index
- **eftest rx_capture mode untested** - set/get rx_capture_stations
- **Netport listener callbacks untested** - link_post_up/down_handler

**New Tests Created:**
- `test-cases/state-machine/config-phase-state-machine.md` - Exhaustive phase transitions
- `test-cases/state-machine/station-lifecycle.md` - Station state machine
- `test-cases/state-machine/datapath-state-transitions.md` - Datapath state derivation and hooks
- `test-cases/interaction/dual-mid-phase-sync.md` - Cross-MID synchronization

**Remaining Gaps (need SimNow or hardware):**
- Remote-only link configuration (needs asymmetric MID config)
- Netport listener link up/down event propagation
- eftest rx_capture with active stations
- Path port map with failover integration (DEIFOEPM-2093)

---

### 4. Non-IFoE Traffic Manager (`src/managers/non_ifoe_traffic_manager/`)

| File | Lines | Function |
|------|-------|----------|
| non_ifoe_traffic.c | 428 | RX/TX packet handling, VLAN parsing, inter-MID bounce |
| host_traffic.c | - | Host DMA traffic (MR-PIO) |
| ifoe_ping.c | - | L2 ping implementation |
| rx_queue.c | - | RX descriptor queue |
| tx_queue.c | - | TX descriptor queue |
| traffic_queue.c | - | Traffic queue management |
| dbell_queue.c | - | Doorbell queue processing |
| inter_mid.c | - | Inter-MID packet forwarding |

**Current Coverage:**
- `test-cases/bringup/l2ping-connectivity.md` - L2 ping basic test
- `test-cases/stress/multi-port-traffic.md` - Multi-port traffic stress

**Gaps Identified:**
- **RX callback ordering not tested** - Callbacks must fire in non_ifoe_rx_callback_ordering_t order
- **TX callback registration overflow untested** - NUM_TX_CALLBACKS=1, second registration returns EALREADY
- **Inter-MID traffic bounce untested** - bounce_rx_to_mid0, bounce_tx_to_mid1
- **VLAN header parsing edge cases untested** - Tagged vs untagged, wrong TPID
- **RX buffer overflow handling untested** - Packet consumed from HW but no host descriptor
- **Thread wake semaphore behavior untested** - Edge cases in sem wake/sleep
- **Doorbell queue processing untested** - dbell_queue write index handling
- **RX/TX queue descriptor management untested** - Ring buffer wrapping, overflow

**New Tests Created:**
- `test-cases/error-handling/non-ifoe-traffic-overflow.md` - Traffic error paths

**Remaining Gaps:**
- Detailed RX/TX queue ring buffer stress (needs traffic generator)
- Inter-MID traffic bounce under load
- VLAN header edge cases with various TPIDs

---

### 5. Telemetry Manager (`src/managers/telemetry_manager/`)

| File | Lines | Function |
|------|-------|----------|
| telemetry_manager.c | 421 | Observer management, DMA config, collection/distribution |
| telemetry_collector.c | - | Counter collection from hardware |
| telemetry_distributor.c | - | DMA to host buffers |
| telemetry_sync.c | - | Dual-MID telemetry sync |
| telemetry_measure.c | - | Collection timing measurement |

**Current Coverage:**
- `test-cases/bringup/telemetry-running.md` - Basic telemetry check
- `test-cases/zephyr-twister/ifoe-tlm-shell.md` - Telemetry shell commands

**Gaps Identified:**
- **Observer select/deselect lifecycle untested** - Full select -> configure -> enable -> disable cycle
- **Invalid observer ID boundary untested** - observer_id >= TELEMETRY_OBSERVER_ID_COUNT
- **DMA config validation untested** - Page address validation, size calculation
- **Category mask validation untested** - Zero mask, invalid category bits
- **Concurrent observer access untested** - Mutex protection of telemetry_mgr.lock
- **Telemetry sync between MIDs untested** - telemetry_sync_init_completion flow
- **Datapath hook state-dependent collection untested** - telemetry_datapath_hook_state_transition pause/resume
- **HBM allocation blocking path untested** - hbm_helper_get_local_address_blocking

**New Tests Created:**
- `test-cases/unit/telemetry-collector-init.md` - Observer selection and validation

**Remaining Gaps:**
- Full DMA distribution to host buffer (needs host memory allocation)
- Dual-MID telemetry sync (needs SimNow dual-MID)
- Collection timing under various datapath states

---

### 6. Network Manager (`src/managers/network_manager/`)

| File | Lines | Function |
|------|-------|----------|
| netport_manager.c | - | Port management, handle allocation |
| ethport_manager.c | - | Ethernet port lifecycle |
| netport_events.c | - | Port event processing |
| netport_manager_tlm.c | - | Port telemetry |
| network_rpc.c | - | Network RPC for dual-MID |

**Current Coverage:**
- `test-cases/bringup/link-up.md` - Link up verification
- `test-cases/sanity/port-enum.md` - Port enumeration

**Gaps Identified:**
- Netport handle allocation/deallocation lifecycle
- Port listener registration and event dispatching
- Link status query and fault flag interpretation
- Network RPC for cross-MID port management
- ethport_manager state machine

**Remaining Gaps (all need hardware):**
- Physical link up/down event handling
- Port properties (speed, FEC, etc.)
- MAC address change notifications

---

### 7. Sideband Manager (`src/managers/sideband_manager/`)

| File | Lines | Function |
|------|-------|----------|
| sideband_manager.c | - | Sideband transport management |
| sideband_msg_handler.c | - | Sideband message handlers |

**Current Coverage:** NONE

**Gaps Identified:**
- Entire sideband manager is untested
- IFCP transport setup and teardown
- Message handler registration and dispatch
- Transport API registration

**New Tests Created:**
- `test-cases/interaction/sideband-mcdi-dispatch.md` - Covers sideband MCDI path

**Remaining Gaps:**
- Sideband transport lifecycle (needs IFCP infrastructure)
- Message handler stress testing

---

### 8. IFoE Subsystem (`src/subsystems/ifoe_ss/`)

| File | Lines | Function |
|------|-------|----------|
| ifoe_ss.c | - | IFoE subsystem core |
| ifoe_ss_data.c | - | Station data management |
| ifoe_ss_eftest.c | - | Engineering test support |
| non_ifoe_traffic.c | - | Non-IFoE packet RX/TX via IFoE hardware |

**Current Coverage:**
- `test-cases/functional/loopback-ifoe.md` - IFoE loopback test
- `test-cases/functional/loopback-mac.md` - MAC loopback test

**Gaps Identified:**
- Station active/inactive toggle
- Config snapshot/restore at subsystem level
- Network config set/get at subsystem level
- Encrypt enable/disable propagation
- Non-IFoE packet handling through IFoE hardware

**Remaining Gaps (need hardware/SimNow):**
- Actual SDP TX/RX data path
- Failover mode operation
- Multi-station configuration

---

### 9. Chip IPC Subsystem (`src/subsystems/chip_ipc/`)

| File | Lines | Function |
|------|-------|----------|
| chip_ipc.c | 847 | Intra-chip IPC link state machine, command queuing |
| chip_ipc_arbitrator.c | - | Arbitration for concurrent senders |

**Current Coverage:**
- `test-cases/control-plane/dual-mid-control-plane.md` - Basic dual-MID communication

**Gaps Identified:**
- **Link state machine not exhaustively tested** - 7 states (DOWN through WAITING)
- **Stabilization handshake untested** - HELLO -> STAB_1ST -> STAB_REC -> STAB_LAST
- **Link drop and recovery untested** - handle_link_drop, queue draining, re-HELLO
- **Sequence error handling untested** - seq_remote mismatch
- **Completion timeout handling untested** - CONFIG_CHIP_IPC_COMPL_WAIT_INTERVAL_MS
- **Quick path vs regular path untested** - Completion commands vs data commands
- **Missed ISR diagnostics untested** - atomic_inc on re-triggered ISR
- **Arbitrator for concurrent senders untested** - chip_ipc_arbitrator.c

**New Tests Created:**
- `test-cases/state-machine/chip-ipc-link-state-machine.md` - Link state machine

**Remaining Gaps (need dual-MID):**
- Link drop under load with recovery
- Sequence error injection
- Quick path priority over regular path
- Arbitrator fairness testing

---

### 10. MID RPC Subsystem (`src/subsystems/mid_rpc/`)

| File | Lines | Function |
|------|-------|----------|
| rpc.c | 328 | RPC request/response, context management |
| rpc_util.c | - | Blocking RPC helpers |
| transport.c | - | Transport layer (uses chip_ipc) |

**Current Coverage:**
- `test-cases/control-plane/dual-mid-control-plane.md` - Implicit via dual-MID ops

**Gaps Identified:**
- **Context allocation/free lifecycle untested** - tx_ctx/rx_ctx management
- **Tag matching untested** - MID_RPC_REMOTE_TAG_IS_RES, LOCAL_TO_REMOTE conversions
- **Request credit management untested** - remote_req_credits semaphore
- **Handler lookup untested** - mid_rpc_find_handler with module_id/command_id
- **Buffer alignment validation untested** - IS_ALIGNED check in send_request
- **Send failure cleanup untested** - Context freed and credits returned on error
- **Incoming message parsing untested** - Size validation, header parsing

**New Tests Created:**
- `test-cases/unit/mid-rpc-context-management.md` - Context lifecycle

**Remaining Gaps:**
- Full RPC round-trip under load
- Credit exhaustion and recovery
- Transport failure handling

---

### 11. Event Queue Subsystem (`src/subsystems/event_queue/`)

| File | Lines | Function |
|------|-------|----------|
| event_queue.c | 137 | EVQ init/fini, event delivery, doorbell handling |
| event_queue_internal.c | - | Internal EVQ implementation |

**Current Coverage:** NONE (implicitly tested through MCDI event flow)

**Gaps Identified:**
- **EVQ lifecycle untested** - init_evq, fini_evq, double-init guard
- **Event delivery untested** - send_evq_event, send_evq_event_for_client
- **Doorbell processing untested** - ring_evq_rd_idx_dbell
- **Reset hook untested** - evq_reset at order 200
- **PF vs VF EVQ routing untested** - get_evq_index client routing

**New Tests Created:**
- `test-cases/unit/event-queue-lifecycle.md` - EVQ lifecycle and error handling

**Remaining Gaps:**
- Event delivery to host verification (needs host-side EVQ consumer)
- Doorbell synchronization stress

---

### 12. MP Listener Subsystem (`src/subsystems/mp_listener/`)

| File | Lines | Function |
|------|-------|----------|
| mp_listener.c | - | Base listener framework |
| mpasp_listener.c | - | ASP command listener |
| mp1_pm_listener.c | - | PM command listener |
| mpio_listener.c | - | MPIO command listener |

**Current Coverage:** NONE

**Gaps Identified:**
- Entire MP listener framework untested
- ASP command registration and dispatch
- PM command handler registration
- MPIO listener operations

**New Tests Created:**
- `test-cases/interaction/asp-mpifoe-ras-inject.md` - Covers ASP listener path via RAS

**Remaining Gaps:**
- PM listener command handling
- MPIO listener operations
- Listener error handling (invalid command IDs)

---

### 13. RAS Subsystem (`src/subsystems/ras_ss/`)

| File | Lines | Function |
|------|-------|----------|
| ras_ss.c | 548 | Error location mapping, inject/clean, MCA reporting |

**Current Coverage:**
- `test-cases/ras/ras-error-inject.md` - Basic error injection
- `test-cases/ras/cper-validation.md` - CPER record validation

**Gaps Identified:**
- **Conversion table completeness untested** - All 5 components (XRMAC, XRPFC, XRSEC, EX, IFOE) with 73 total errors
- **Binary search in ras_ss_get_external_error_id untested** - Edge cases (first, last, not found)
- **MCA priority mapping untested** - All error types to MCA priorities
- **Invalid component/element rejection untested** - ENODEV, ERANGE paths
- **SEC/DED toggle via error_flags untested** - BIT(ERROR_FLAG_BIT_SECDED) switching
- **Die/socket ID validation in set_mca_target untested** - Cross-socket rejection

**New Tests Created:**
- `test-cases/interaction/asp-mpifoe-ras-inject.md` - Covers error path validation

**Remaining Gaps:**
- Full 73-error injection sweep (needs hardware for all components)
- MCA bank content verification

---

### 14. Hardware Drivers (`src/drivers/`)

| Driver | Files | Current Coverage |
|--------|-------|-----------------|
| boot_info | 2 | Implicit (version, uptime) |
| comms_to_mp | 2 | NONE |
| dma (ADMA) | 2 | Boot self-test only |
| ex_drv | 7 | NONE |
| ifoe_container | 3 | NONE |
| ifoe_drv | 16 | Implicit (via ifoe_ss) |
| ifoe_dvd_telem_drv | 4 | NONE |
| ifoe_irq | 2 | NONE |
| ifoe_pmi | 2 | NONE |
| ifoe_reset | 1 | NONE |
| ifoe_rsmu | 2 | NONE |
| interrupt_inspector | 3 | NONE |
| interrupt_to_host | 2 | NONE |
| mbox | 3 | Boot self-test only |
| mca_drv | 3 | Via RAS test |
| mmhub_drv | 2 | NONE |
| mp_role | 2 | Implicit |
| netport_dvd_telem_drv | 4 | NONE |
| ras_drv | 2 | Via RAS test |
| smn_drv | 2 | Boot self-test only |
| upi2 | 2 | NONE |
| xrmac_drv | 6 | NONE |
| xrpfc_drv | 7 | NONE |
| xrsec_drv | 10 | NONE |

**New Tests Created:**
- `test-cases/driver/smn-read-write.md`
- `test-cases/driver/adma-transfer-test.md`
- `test-cases/driver/mbox-claim-and-interrupt.md`
- `test-cases/driver/ex-drv-init-and-telemetry.md`

**Remaining Gaps (most need hardware):**
- XRMAC driver: MAC configuration, telemetry, RAS
- XRPFC driver: Priority flow control, queue config, RAS
- XRSEC driver: Encryption/decryption, key management, indirect access, RAS
- IFoE driver: TX/RX encap/decap, SDP pack/unpack, TX scheduler, TX buffer
- MMHUB driver: Memory hub mapping
- Interrupt to host: MSI-X delivery
- IFoE reset: Hardware reset sequencing
- UPI2: SD controller mock (SimNow only)

---

### 15. Libraries (`src/lib/`)

| Library | Files | Current Coverage |
|---------|-------|-----------------|
| sg_buffer | 2 | `test-cases/unit/sg-buffer.md` (pffth) |
| dma | 2 | Boot self-test |
| mcdi | 3 | Implicit |
| mcdi_remote_dispatch | 2 | NONE |
| mid_cache | 2 | `test-cases/unit/cache-flush-invalidate.md` |
| mid_rpc_handlers | 1 | NONE |
| reset | 3 | Implicit via entity_reset |
| scattered_dma | 2 | NONE |
| sg_queue | 2 | NONE |
| telemetry | 4 | Implicit |
| map_host_mem | 3 | NONE |
| mmhub_helper | 5 | NONE |
| callback_util | 2 | NONE |
| core (rc, types) | 8 | NONE |
| smn_helper | 2 | NONE |

**Remaining Gaps:**
- sg_queue: Queue management (candidate for pffth unit test)
- scattered_dma: Scatter-gather DMA operations
- mcdi_remote_dispatch: Remote command forwarding
- map_host_mem: Host address mapping/unmapping
- callback_util: Callback registration patterns

---

## Summary Statistics

| Category | Existing Tests | New Tests Created | Remaining Gaps |
|----------|---------------|-------------------|----------------|
| Bringup | 5 | 0 | 0 |
| Sanity | 4 | 0 | 0 |
| Functional | 5 | 0 | 2 |
| Unit | 2 | 4 | 3 |
| State Machine | 0 | 4 | 2 |
| Interaction | 0 | 4 | 3 |
| Error Handling | 0 | 5 | 4 |
| Driver | 0 | 4 | 12 |
| RAS | 2 | 0 | 1 |
| Stress | 3 | 0 | 2 |
| Control Plane | 2 | 0 | 1 |
| Regression | 1 | 0 | 0 |
| Zephyr Twister | 3 | 0 | 1 |
| **Total** | **27** | **17** | **31** |

## New Test Cases Created (17)

### Unit Tests (4)
1. `test-cases/unit/mcdi-privilege-check.md` - MCDI privilege enforcement
2. `test-cases/unit/event-queue-lifecycle.md` - EVQ init/fini/double-init
3. `test-cases/unit/mid-rpc-context-management.md` - RPC context allocation/tag matching
4. `test-cases/unit/telemetry-collector-init.md` - Telemetry observer selection validation

### State Machine Tests (4)
5. `test-cases/state-machine/config-phase-state-machine.md` - Exhaustive phase transition matrix
6. `test-cases/state-machine/station-lifecycle.md` - DISABLED/STOPPED/ACTIVE transitions
7. `test-cases/state-machine/chip-ipc-link-state-machine.md` - 7-state IPC link establishment
8. `test-cases/state-machine/datapath-state-transitions.md` - Datapath state derivation and hook ordering

### Interaction Tests (4)
9. `test-cases/interaction/asp-mpifoe-ras-inject.md` - ASP RAS inject/clean full path
10. `test-cases/interaction/dual-mid-phase-sync.md` - Cross-MID phase synchronization
11. `test-cases/interaction/sideband-mcdi-dispatch.md` - IFCP sideband MCDI path
12. `test-cases/interaction/pm-mpifoe-flr-reset.md` - FLR and entity reset hook chain

### Error Handling Tests (5)
13. `test-cases/error-handling/mcdi-invalid-command.md` - Invalid command ID dispatch
14. `test-cases/error-handling/ifoe-config-wrong-phase.md` - Phase restriction enforcement
15. `test-cases/error-handling/crypto-key-boundary.md` - Crypto key boundary conditions
16. `test-cases/error-handling/non-ifoe-traffic-overflow.md` - Traffic buffer overflow
17. `test-cases/error-handling/address-mapping-boundary.md` - Address mapping boundary

### New Test Suites (4)
- `test-suites/state-machine.yaml`
- `test-suites/interaction.yaml`
- `test-suites/error-handling.yaml`
- `test-suites/driver.yaml`

## Remaining Gaps Requiring Hardware or SimNow (31)

These gaps cannot be addressed with unit tests or xncmdclient alone:

1. **XRMAC/XRPFC/XRSEC driver full testing** - Needs register access to real hardware
2. **IFoE TX/RX datapath testing** - Needs SDP traffic from GPU
3. **Failover mode operation** - Not implemented (DEIFOEPM-2093)
4. **FLR reset execution** - Stubbed in code (FWDEV-165197/165198)
5. **Interrupt to host (MSI-X)** - Needs PCIe interrupt delivery
6. **MMHUB/HBM operations** - Needs GPU memory subsystem
7. **Physical link up/down events** - Needs network cable/transceiver
8. **Chip IPC link drop under load** - Needs controlled dual-MID failure injection
9. **Telemetry DMA to host** - Needs host memory allocation and DMA path
10. **Inter-MID traffic bounce stress** - Needs traffic generator and dual-MID
11. **UPI2 controller operations** - SimNow mock only
12. **IFoE container block offset management** - Hardware register layout
13. **IFoE PMI (Performance Monitor Interface)** - Hardware counters
14. **IFoE RSMU operations** - Hardware specific
15. **Scattered DMA operations** - Needs multi-page host buffers
16. **Map host memory lifecycle** - Needs PCIe BAR mapping
17. **Interrupt inspector repair cycles** - Needs interrupt controller state
18. **Boot info heartbeat timing** - Needs real-time observation
19. **PM listener commands** - Needs PM firmware interaction
20. **MPIO listener operations** - Needs MPIO firmware
21. **Netport link listener event propagation** - Needs physical link changes
22. **Remote-only link configuration** - Needs asymmetric MID config
23. **eftest RX capture mode** - Needs active traffic
24. **DVDtelem drivers (ifoe + netport)** - Need DVD telemetry infrastructure
25. **MCA bank content verification** - Needs MCA register access
26. **Full 73-error RAS injection sweep** - Needs all hardware components
27. **IFoE reset sequencing** - Hardware reset timing
28. **Path port map with failover** - Failover not implemented
29. **Netport DVDtelem driver** - Needs netport telemetry infrastructure
30. **Callback util registration patterns** - Low priority, library utility
31. **SG queue management** - Candidate for pffth test
