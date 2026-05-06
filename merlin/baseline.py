"""Golden baseline: collect, store, and compare SimNow observations."""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime


@dataclass
class RegisterObservation:
    address: str
    space: str
    value: str
    observation_count: int = 1
    first_seen: str = ""
    stable: bool = False  # promoted to grounded after 5+ consistent observations

    def observe(self, new_value: str) -> bool:
        if self.value == new_value:
            self.observation_count += 1
            if self.observation_count >= 5:
                self.stable = True
            return True
        self.value = new_value
        self.observation_count = 1
        self.stable = False
        return False


@dataclass
class GoldenBaseline:
    component: str
    lkg_date: str = ""
    lkg_commit: str = ""
    registers: dict[str, RegisterObservation] = field(default_factory=dict)
    log_markers: list[str] = field(default_factory=list)
    postcodes: list[str] = field(default_factory=list)
    boot_time_ms: int = 0
    error_log_empty: bool = True

    def save(self, baselines_dir: Path):
        path = baselines_dir / f"{self.component}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        data["registers"] = {k: asdict(v) for k, v in self.registers.items()}
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, baselines_dir: Path, component: str) -> "GoldenBaseline | None":
        path = baselines_dir / f"{component}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        regs = {}
        for k, v in data.pop("registers", {}).items():
            regs[k] = RegisterObservation(**v)
        baseline = cls(**data)
        baseline.registers = regs
        return baseline


# Regex patterns for SimNow log parsing
RE_MONITOR = re.compile(
    r"Monitor\s+(\w+)\s+.*?=\s*(0x[0-9a-fA-F]+)", re.IGNORECASE
)
RE_FW_STATUS = re.compile(
    r"(M(?:PART|PASP)_FW_STATUS)\s*=\s*(0x[0-9a-fA-F]+)", re.IGNORECASE
)
RE_POSTCODE = re.compile(r"postcode\s*[:=]\s*(0x[0-9a-fA-F]+)", re.IGNORECASE)

KNOWN_MARKERS = [
    "PSP firmware initialized",
    "L2 PSP Directory loaded",
    "all ESIDs completed",
    "TOS steady state",
    "MPASP FMC initialized",
    "secure boot: signature verified",
    "MPIO: all PCIe links trained",
    "IP discovery: all blocks found",
    "amdgpu: initialization complete",
]


def collect_from_log(component: str, log_text: str, err_text: str = "") -> GoldenBaseline:
    """Extract a golden baseline from SimNow log output."""
    baseline = GoldenBaseline(
        component=component,
        lkg_date=datetime.now(tz=None).strftime("%Y-%m-%d"),
    )

    for match in RE_MONITOR.finditer(log_text):
        name, value = match.group(1), match.group(2)
        baseline.registers[name] = RegisterObservation(
            address="", space="", value=value,
            first_seen=baseline.lkg_date,
        )

    for match in RE_FW_STATUS.finditer(log_text):
        name, value = match.group(1), match.group(2)
        if name not in baseline.registers:
            baseline.registers[name] = RegisterObservation(
                address="", space="", value=value,
                first_seen=baseline.lkg_date,
            )

    for match in RE_POSTCODE.finditer(log_text):
        baseline.postcodes.append(match.group(1).upper())

    for marker in KNOWN_MARKERS:
        if marker.lower() in log_text.lower():
            baseline.log_markers.append(marker)

    baseline.error_log_empty = len(err_text.strip()) == 0
    return baseline


def update_baseline(existing: GoldenBaseline, new_run: GoldenBaseline) -> GoldenBaseline:
    """Merge a new successful run into the existing golden baseline."""
    for name, obs in new_run.registers.items():
        if name in existing.registers:
            existing.registers[name].observe(obs.value)
        else:
            existing.registers[name] = obs

    for marker in new_run.log_markers:
        if marker not in existing.log_markers:
            existing.log_markers.append(marker)

    if new_run.postcodes:
        existing.postcodes = new_run.postcodes

    existing.lkg_date = new_run.lkg_date
    existing.lkg_commit = new_run.lkg_commit
    existing.error_log_empty = new_run.error_log_empty
    return existing
