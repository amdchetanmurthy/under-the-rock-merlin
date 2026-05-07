# MI450 Telemetry & RAS Architecture

**Source:** https://amd.atlassian.net/wiki/spaces/ASIC/pages/597643471 (PM Tick)
**Source:** https://amd.atlassian.net/wiki/spaces/CNS/pages/556183198 (MCA)

---

## 1. PM Tick — Telemetry Statistics Collection

**Source:** https://amd.atlassian.net/wiki/spaces/ASIC/pages/597643471/ETH+SS+-+pm_tick+implementation

The PM Tick mechanism provides **atomic snapshots** of per-port statistics across the IFoE subsystem. This is the foundation for hardware telemetry — firmware uses PM Tick to collect traffic counters, error rates, and performance metrics.

### 1.1 How PM Tick Works

```
                    ┌──────────────────┐
                    │ 48-bit System    │
                    │ Timer            │
                    │ (clk_eth 1.3GHz) │
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │ MUX (6-bit sel)  │
                    │ Select bit 16-47 │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ XRMAC    │  │ XRPFC    │  │ IFOE     │
        │ (8 ports)│  │          │  │          │
        │          │  │          │  │          │
        │ pm_tick  │  │ pm_tick  │  │ pm_tick  │
        │    ↓     │  │    ↓     │  │    ↓     │
        │ pm_rdy   │  │ (regs)   │  │          │
        │ (SRAMs)  │  │          │  │          │
        └──────────┘  └──────────┘  └──────────┘
              │
              ▼
        stats_valid window
        (75% of pm_tick period)
              │
              ▼
        FW reads statistics
```

### 1.2 Timer Details

- **48-bit system timer** running at `clk_eth` (1.3 GHz, ~760ps period)
- Timer wraps after ~54 hours
- CSR selects which timer bit (16-47) drives pm_tick
- **Configurable periodicity:** `2^(16 + timer_bit + 1) / f_clk_eth`
  - Minimum useful: ~100 μs (bit 17)
  - Typical: 1 second (bit ~30)
  - Maximum: ~54 hours (bit 47)

### 1.3 Statistics Collection Sequence

1. Configure `PM_TIMER_BIT_SELECT` CSR (6-bit, default 0x0F → ~1.6 sec period)
2. Enable one interrupt bit in `PM_TICK_INTR_INT_ENABLE_SET` (32 bits, one at a time)
3. Clear existing interrupts first to avoid immediate trigger
4. On interrupt:
   - Check `status_valid` bit — asserted from `pm_rdy` until 75% of period
   - Check `pm_rdy` per lane for XRMAC/MXRT
   - Read PFC and IFOE tile statistics
   - Clear interrupt register

### 1.4 Key Timing Constraints

| Parameter | Value | Notes |
|-----------|-------|-------|
| pm_rdy assertion | ≤300 AXI-lite clocks (~750 ns) | After pm_tick, SRAMs need copy time |
| stats_valid window | pm_rdy to 75% of period | FW must read within this window |
| Minimum pm_tick spacing | Several hundred AXI-lite clocks | Closer ticks cause ambiguous results |
| AXI-lite clock | 400 MHz (clk_flash) | Slower than clk_eth (1.3 GHz) |

### 1.5 Registers

| Register | Bits | Type | Description |
|----------|------|------|-------------|
| `PM_TIMER_BIT_SELECT` | 6 | Config | Periodicity: 2^(16+value+1)/f_clk_eth |
| `PM_TICK_TIMER_CNT` | 48 | Status | Current timer count |
| `PM_TICK_INTR_INTRREG` | 32 | Interrupt | Write-one-to-clear per timer bit |
| `PM_TICK_INTR_INT_ENABLE_SET` | 32 | W1S | Enable one interrupt at a time |
| `PM_TICK_INTR_INT_ENABLE_CLEAR` | 32 | W1C | Disable interrupts |
| `PORT_PM_STATUS` | 9 | Status | 8-bit per-lane pm_rdy + 1-bit stats_valid |

### 1.6 Impact on Testing

**For Merlin CI/CD:**
- PM Tick is how MPIFOE firmware collects IFoE statistics
- A broken PM Tick means no telemetry → silent degradation
- SimNow models PM Tick behavior — test assertions should verify:
  - Timer is running (PM_TICK_TIMER_CNT incrementing)
  - pm_rdy asserts after pm_tick
  - stats_valid window is correct duration
- Nightly tests should verify statistics collection end-to-end
- This is relevant for `fw-mpifoe` changes that touch telemetry code

---

## 2. MCA — Machine Check Architecture (RAS)

**Spec:** SharePoint `aljackso/.../MCAX_v5.0.0.docx`
**User Guide:** SharePoint `aljackso/.../MCA_IP_User_Guide_and_Specification.pdf`

### 2.1 What MCA Does

MCA (Machine Check Architecture) is the hardware error reporting framework. Each IP block has one or more **MCA banks** that log:

- **Correctable errors (CE)** — ECC corrections, retries, recovered errors
- **Uncorrectable errors (UCE)** — Fatal hardware errors requiring attention
- **Deferred errors** — Errors detected but not yet consumed

### 2.2 MCA and MPRAS Firmware

The **MPRAS firmware** (`fw-mpras-kernel`, PSP entry 0x006b) reads MCA banks and:
- Aggregates error counts
- Reports errors via CPER (Common Platform Error Record) to the host
- Triggers error injection for testing (RAS validation)
- Manages page retirement for faulty HBM pages

### 2.3 MCA Banks in MI450

Each IP block has dedicated MCA banks. Key ones for firmware testing:

| IP Block | MCA Bank | Error Types |
|----------|----------|-------------|
| UMC (Memory Controller) | HBM ECC | CE, UCE on HBM memory |
| XGMI | Link errors | CRC errors, replay, link degradation |
| PCIe (NBIO) | PCIe AER | Correctable/uncorrectable PCIe errors |
| GC (Graphics Core) | Shader errors | ECC errors in L1/L2/LDS |
| SDMA | DMA errors | Transfer errors |
| VCN | Video errors | Decode/encode errors |
| IFoE | Fabric errors | Link errors, packet drops |

### 2.4 RAS Test Coverage

From the test inventory, RAS-related test coverage:

| Component | RAS Tests Available |
|-----------|-------------------|
| fw-mpras-kernel | 5 on-target tests: dram_test, poison_test, messaging_if_test, remote_die_smn_test |
| fw-art-security | RAS-related test suites (MPRAS applets, rsmu_test) |
| SimNow | MI450 RAS MBAT configs (simnow mi450.yaml: `*_ras_mbat` variants) |

### 2.5 Impact on Testing

**For Merlin CI/CD:**
- RAS testing requires specific SimNow configs with MBAT (MI450 Board Acceptance Test) enabled
- The `mi450_ras_on_fmc` IFWI variant enables RAS features
- Nightly tier should include RAS MBAT SimNow configs
- MPRAS firmware changes should trigger RAS-specific test assertions:
  - MCA bank readability
  - Error injection → detection → CPER generation
  - Page retirement flow
- The `MPASP_C2PMSG_96/97` register overrides control RAS mode in SimNow scripts:
  ```
  # RAS MBAT mode
  script_modify: "MPASP_C2PMSG_96/CONTENT 0x19300000<->MPASP_C2PMSG_96/CONTENT 0x11300000;
                   MPASP_C2PMSG_97/CONTENT 0x00800204<->MPASP_C2PMSG_97/CONTENT 0x00000204"
  ```

---

## 3. Architecture → Test Mapping Summary

| Architecture Module | Firmware | SimNow Model | Key Test Assertion |
|--------------------|-----------|--------------|--------------------|
| IFoE subsystem | fw-mpifoe | 2G IFoE or M228 | IFoE link up, fabric topology |
| PM Tick telemetry | fw-mpifoe | Any (M112+) | Timer running, stats collection |
| XRMAC/XRPFC | fw-mpifoe | 2G IFoE | Per-port counters, PFC |
| SMN/RSMU | All FW | Any | Register access works (implicit) |
| nHT | fw-mpnht | A+A or 2G | nHT link training, RPC |
| OpenXGMI links | fw-mpio, fw-mpnht | 2G or A+A | Link training, VC allocation |
| Root Port / PCIe | fw-mpio | A+A | PCIe enumeration, AINIC discovery |
| MCA / RAS | fw-mpras-kernel | M228 + RAS MBAT | Error injection, MCA bank read |
| nBIF reset | All FW | Any | Warm/cold reset cycling |
| Security (XRSEC) | fw-amd-tee3 | Secure variants | Encryption, key rotation |
