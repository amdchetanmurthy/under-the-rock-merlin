"""Test generator: produce acceptance tests from ground truth, not imagination."""

from pathlib import Path
import yaml

from merlin.baseline import GoldenBaseline
from merlin.grounding import Assertion, load_ifwi_layout, get_psp_max_size


def generate_acceptance_test(
    component: str,
    baseline: GoldenBaseline | None,
    layout: dict | None = None,
    binary_paths: list[Path] | None = None,
) -> list[Assertion]:
    """Generate grounded acceptance test assertions for a component.

    Only produces assertions that can be verified against real data.
    AI-suggested (ungrounded) assertions are clearly marked.
    """
    if layout is None:
        layout = load_ifwi_layout()

    assertions: list[Assertion] = []

    # 1. Binary size checks — always grounded from IFWI layout
    psp_entries = get_psp_max_size(layout, component)
    for psp_type, name, max_size in psp_entries:
        assertions.append(Assertion(
            name=f"binary_size_{name}",
            type="static",
            check=f"binary_size <= {max_size}",
            expected=str(max_size),
            grounded=True,
            source=f"configs/ifwi_layout.yaml PSP entry {psp_type:#x}",
        ))

    # 2. Boot postcode — always grounded from IFWI layout
    pass_postcode = layout.get("boot_pass_postcode", "0X800F0000")
    assertions.append(Assertion(
        name="boot_postcode",
        type="simnow_postcode",
        expected=pass_postcode,
        grounded=True,
        source="configs/ifwi_layout.yaml",
    ))

    # 3. FW status monitors — always grounded from IFWI layout
    for monitor_name, monitor_info in layout.get("fw_status_monitors", {}).items():
        expected = ""
        if baseline and monitor_name in baseline.registers:
            expected = baseline.registers[monitor_name].value
        elif "MPASP" in monitor_name:
            expected = "0x800f0000"

        if expected:
            assertions.append(Assertion(
                name=f"fw_status_{monitor_name}",
                type="simnow_register",
                address=monitor_info["address"],
                space=monitor_info["space"],
                expected=expected,
                grounded=True,
                source="configs/ifwi_layout.yaml + golden baseline",
            ))

    # 4. Error log empty — always grounded
    assertions.append(Assertion(
        name="error_log_empty",
        type="simnow_error_log",
        expected="empty",
        grounded=True,
        source="standard acceptance criteria",
    ))

    # 5. Log markers from golden baseline — grounded if baseline exists
    if baseline:
        for marker in baseline.log_markers:
            assertions.append(Assertion(
                name=f"log_marker_{marker.replace(' ', '_')[:40]}",
                type="simnow_log_marker",
                marker=marker,
                grounded=True,
                source=f"golden baseline {baseline.lkg_date}",
            ))

        # 6. Stable registers from golden baseline
        for reg_name, obs in baseline.registers.items():
            if obs.stable and reg_name not in layout.get("fw_status_monitors", {}):
                assertions.append(Assertion(
                    name=f"stable_reg_{reg_name}",
                    type="simnow_register",
                    address=obs.address,
                    space=obs.space,
                    expected=obs.value,
                    grounded=True,
                    source=f"golden baseline (stable, {obs.observation_count} observations)",
                ))

    return assertions


def write_acceptance_yaml(
    component: str,
    assertions: list[Assertion],
    output_dir: Path = Path("acceptance_tests"),
):
    """Write acceptance test to YAML file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    grounded = [a for a in assertions if a.grounded]
    advisory = [a for a in assertions if not a.grounded]

    data = {
        "component": component,
        "generated_by": "merlin",
        "pr_gate": {
            "assertions": [
                {
                    "name": a.name,
                    "type": a.type,
                    "expected": a.expected or a.check or a.marker,
                    "grounded": a.grounded,
                    "source": a.source,
                }
                for a in grounded
            ],
        },
    }

    if advisory:
        data["advisory"] = [
            {
                "name": a.name,
                "type": a.type,
                "expected": a.expected or a.check or a.marker,
                "note": a.verdict,
            }
            for a in advisory
        ]

    path = output_dir / f"{component}.yaml"
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    return path
