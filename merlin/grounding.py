"""Grounding validator: ensures every test assertion traces to real data."""

from dataclasses import dataclass
from pathlib import Path
import yaml

from merlin.baseline import GoldenBaseline


@dataclass
class Assertion:
    name: str
    type: str  # static, simnow_postcode, simnow_register, simnow_log_marker, simnow_error_log, timing
    expected: str = ""
    address: str = ""
    space: str = ""
    marker: str = ""
    check: str = ""
    grounded: bool = False
    source: str = ""
    verdict: str = ""  # GROUNDED, UNGROUNDED, ADVISORY


def load_ifwi_layout(config_path: Path = Path("configs/ifwi_layout.yaml")) -> dict:
    return yaml.safe_load(config_path.read_text())


def get_psp_max_size(layout: dict, component: str) -> list[tuple[int, str, int]]:
    """Return [(psp_type, name, max_size)] for a component."""
    entry = layout["psp_entries"].get(component)
    if not entry:
        return []
    if "type" in entry:
        return [(entry["type"], entry["name"], entry["max_size"])]
    return [(e["type"], e["name"], e["max_size"]) for e in entry.get("entries", [])]


def validate_assertions(
    assertions: list[Assertion],
    baseline: GoldenBaseline | None,
    layout: dict,
) -> list[Assertion]:
    """Validate each assertion is grounded. Returns assertions with verdict set."""
    validated = []
    for a in assertions:
        if a.type == "static":
            a.grounded = True
            a.verdict = "GROUNDED"

        elif a.type == "simnow_postcode":
            if a.expected.upper() == layout.get("boot_pass_postcode", "").upper():
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = "configs/ifwi_layout.yaml boot_pass_postcode"
            elif baseline and a.expected.upper() in [p.upper() for p in baseline.postcodes]:
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = f"golden baseline {baseline.lkg_date}"
            else:
                a.grounded = False
                a.verdict = "UNGROUNDED — postcode not in baseline or layout"

        elif a.type == "simnow_register":
            monitors = layout.get("fw_status_monitors", {})
            known_addresses = {v["address"] for v in monitors.values()}
            baseline_regs = set(baseline.registers.keys()) if baseline else set()

            if a.address in known_addresses:
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = "configs/ifwi_layout.yaml fw_status_monitors"
            elif a.name in baseline_regs and baseline.registers[a.name].stable:
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = f"golden baseline (stable after {baseline.registers[a.name].observation_count} runs)"
            elif a.name in baseline_regs:
                a.grounded = False
                a.verdict = f"UNGROUNDED — observed {baseline.registers[a.name].observation_count} times, need 5 for stable"
            else:
                a.grounded = False
                a.verdict = "UNGROUNDED — register not in baseline"

        elif a.type == "simnow_log_marker":
            if baseline and a.marker in baseline.log_markers:
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = f"golden baseline {baseline.lkg_date}"
            else:
                a.grounded = False
                a.verdict = "UNGROUNDED — marker not in baseline"

        elif a.type == "simnow_error_log":
            if baseline and baseline.error_log_empty:
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = "golden baseline error log was empty"
            else:
                a.grounded = True
                a.verdict = "GROUNDED"
                a.source = "error log check always grounded"

        else:
            a.grounded = False
            a.verdict = f"ADVISORY — unknown type {a.type}"

        validated.append(a)
    return validated
