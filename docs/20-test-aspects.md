# UnderTheRock Test Aspects — Existing MI455/Helios Tests

**Source:** https://amd.atlassian.net/wiki/spaces/SHARK/pages/1670221018/UnderTheRock+Test+Aspects
**Last Modified:** May 6, 2026

---

## CI-Lite (Pushkin/Tom Robbins's Team) — WIP

### What Is Tested

CI-Lite consumes daily builds of:
- SBIOS (or latest known working)
- HPM_CPLD (or latest known working)
- PLDM components (or latest known working)
- amdgpu driver (daily)
- ROCm (most recent version)

### Where

| Type | Config | MI45X Stepping |
|------|--------|----------------|
| Benchtop | 1P1G | B0 |

### How (via Conductor, plans to move to qTest)

| Test | Duration |
|------|----------|
| Flash FW | ~30 minutes |
| Boot to OS | ~10 minutes |
| Check device enumeration | — |
| Install ROCm & Driver | ~5 minutes |
| Load driver | ~1 minute |
| rocrtst - memory async copy | ~5 minutes |
| rocrtst - memory access | — |
| oblex | ~5 minutes |

**Conductor config:** https://conductor.amd.com/test/component-wizard/config?config_id=932b3288-35c4-4996-b618-d74c2f3a5274

**Total CI-Lite duration: ~56+ minutes**

---

## Pre-Si CI & Quality (ChrisSmith/Ivo's Team)

### Pre-Si CI

**SimOxide:** https://github.amd.com/PFO/simoxide
- Pre-commit tests
- Nightly tests
- Release tests

### Pre-Si Quality

**ATM Tests & MATs:**
- ATM location: http://atm/atm/#/Spaces/195/CoverageMapTestPlan/browse/
- MI450 test cases: http://atm/atm/#/TestCases?tag=%5Epfq_mi450_test%5E&spaceId=195
- Coverage Maps and Test Plans available in ATM Space 195

---

## DCAuto Pre-Commit & CI (Leslie/Balaji's Team)

**DCAuto:** https://amd.atlassian.net/wiki/spaces/FAST/pages/751010079

### Systems

| Type | Config | MI45X Stepping |
|------|--------|----------------|
| Helios R Bench | 1P1G | A0 |

### Test Coverage (Pre-Commit)

Two parts:
1. **Default test list** — runs on every PR
2. **FW developer-selected coverage** — automatically triggers based on FW file changes

**Example:** PMFW CTL Mapping: https://github.amd.com/PFO/dcauto-pre-sub/blob/main/ctl_mapping/pmfw/dev-mi450-main.jsonc

**Test Library:** https://dcauto.amd.com/test/libraries

### DCAuto Test Suite

| Test | Duration |
|------|----------|
| FW Patching | <1 minute |
| PLDM Flash + Boot | ~15 minutes |
| Install Driver + theRock | ~10 minutes |
| Load Driver | <1 minute |
| Boot status check | <1 minute |
| HIPBLAST FP16 Memory Bound | ~2 minutes |
| HIPBLAST FP16 Compute Bound | ~5 minutes |
| AC Cycle | ~10 minutes |
| DC Cycle | ~8 minutes |
| Warm reboot | ~8 minutes |
| Driver Unload | ~2 minutes |

**Total DCAuto duration: ~62+ minutes**

### Automated Debug

- On FW failure, DCAuto automatically invokes **RAT** (https://amd.atlassian.net/wiki/spaces/FAST/pages/751010164) for automated debug triage and failure analysis
- Workload-based performance monitoring planned for upcoming execution flow

---

## Key References

| System | URL | Purpose |
|--------|-----|---------|
| SimOxide | https://github.amd.com/PFO/simoxide | Pre-si CI (SimNow-based) |
| DCAuto | https://dcauto.amd.com/ | Hardware pre-commit + CI |
| DCAuto Pre-Sub | https://github.amd.com/PFO/dcauto-pre-sub | PR trigger workflows |
| DCAuto CTL Mapping | github.amd.com/PFO/dcauto-pre-sub/blob/main/ctl_mapping/ | Per-FW test selection |
| DCAuto Test Library | https://dcauto.amd.com/test/libraries | Available test cases |
| RAT | Confluence FAST/pages/751010164 | Automated failure triage |
| Conductor | https://conductor.amd.com/ | CI-Lite test execution |
| ATM | http://atm/atm/ | Test management (coverage maps) |
