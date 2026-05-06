#!/usr/bin/env python3
"""Merlin CLI — AI-native test acceptance for UnderTheRock firmware.

Usage:
  merlin generate <component>              Generate acceptance tests from golden baseline
  merlin collect <component> <log> [err]   Collect golden baseline from SimNow log
  merlin check <component> <log> [err]     Run acceptance tests against SimNow log
  merlin report <component> <log> [err]    Check + produce JUnit XML and markdown
  merlin status                            Show all components and their baseline status
"""

import sys
from pathlib import Path

from merlin.baseline import GoldenBaseline, collect_from_log, update_baseline
from merlin.generator import generate_acceptance_test, write_acceptance_yaml
from merlin.grounding import load_ifwi_layout, validate_assertions
from merlin.runner import check_assertions, to_junit_xml, to_markdown

BASELINES_DIR = Path("golden_baselines")
ACCEPTANCE_DIR = Path("acceptance_tests")
CONFIG_DIR = Path("configs")


def cmd_generate(component: str):
    layout = load_ifwi_layout(CONFIG_DIR / "ifwi_layout.yaml")
    baseline = GoldenBaseline.load(BASELINES_DIR, component)

    assertions = generate_acceptance_test(component, baseline, layout)
    assertions = validate_assertions(assertions, baseline, layout)

    grounded = sum(1 for a in assertions if a.grounded)
    total = len(assertions)

    path = write_acceptance_yaml(component, assertions, ACCEPTANCE_DIR)
    print(f"Generated {path}: {grounded}/{total} grounded assertions")

    if not baseline:
        print(f"  No golden baseline for {component} — run 'merlin collect' first for richer tests")

    for a in assertions:
        tag = "GROUNDED" if a.grounded else "advisory"
        print(f"  [{tag}] {a.name}: {a.type} → {a.expected or a.check or a.marker}")


def cmd_collect(component: str, log_path: str, err_path: str = ""):
    log_text = Path(log_path).read_text()
    err_text = Path(err_path).read_text() if err_path else ""

    new_baseline = collect_from_log(component, log_text, err_text)

    existing = GoldenBaseline.load(BASELINES_DIR, component)
    if existing:
        baseline = update_baseline(existing, new_baseline)
        print(f"Updated golden baseline for {component}")
    else:
        baseline = new_baseline
        print(f"Created new golden baseline for {component}")

    baseline.save(BASELINES_DIR)
    print(f"  Registers: {len(baseline.registers)}")
    print(f"  Log markers: {len(baseline.log_markers)}")
    print(f"  Postcodes: {baseline.postcodes}")
    print(f"  Error log empty: {baseline.error_log_empty}")

    stable = sum(1 for r in baseline.registers.values() if r.stable)
    print(f"  Stable registers (grounded): {stable}/{len(baseline.registers)}")


def cmd_check(component: str, log_path: str, err_path: str = ""):
    layout = load_ifwi_layout(CONFIG_DIR / "ifwi_layout.yaml")
    baseline = GoldenBaseline.load(BASELINES_DIR, component)

    assertions = generate_acceptance_test(component, baseline, layout)
    assertions = validate_assertions(assertions, baseline, layout)

    log_text = Path(log_path).read_text()
    err_text = Path(err_path).read_text() if err_path else ""

    result = check_assertions(assertions, log_text, err_text)
    result.component = component

    print(to_markdown(result))
    return result.verdict == "PASS"


def cmd_report(component: str, log_path: str, err_path: str = ""):
    layout = load_ifwi_layout(CONFIG_DIR / "ifwi_layout.yaml")
    baseline = GoldenBaseline.load(BASELINES_DIR, component)

    assertions = generate_acceptance_test(component, baseline, layout)
    assertions = validate_assertions(assertions, baseline, layout)

    log_text = Path(log_path).read_text()
    err_text = Path(err_path).read_text() if err_path else ""

    result = check_assertions(assertions, log_text, err_text)
    result.component = component

    # Write JUnit XML
    junit_path = Path(f"merlin-{component}-results.xml")
    junit_path.write_text(to_junit_xml(result))

    # Write markdown
    md_path = Path(f"merlin-{component}-results.md")
    md_path.write_text(to_markdown(result))

    print(to_markdown(result))
    print(f"\nJUnit XML: {junit_path}")
    print(f"Markdown:  {md_path}")

    # Update baseline if passed
    if result.verdict == "PASS" and baseline:
        new_obs = collect_from_log(component, log_text, err_text)
        update_baseline(baseline, new_obs)
        baseline.save(BASELINES_DIR)
        print(f"Golden baseline updated for {component}")

    sys.exit(0 if result.verdict == "PASS" else 1)


def cmd_status():
    layout = load_ifwi_layout(CONFIG_DIR / "ifwi_layout.yaml")
    components = list(layout.get("psp_entries", {}).keys())

    print("Component               | Baseline | Grounded | Stable Regs | Markers")
    print("------------------------|----------|----------|-------------|--------")
    for comp in sorted(components):
        baseline = GoldenBaseline.load(BASELINES_DIR, comp)
        if baseline:
            stable = sum(1 for r in baseline.registers.values() if r.stable)
            total_regs = len(baseline.registers)
            markers = len(baseline.log_markers)
            assertions = generate_acceptance_test(comp, baseline, layout)
            grounded = sum(1 for a in assertions if a.grounded)
            print(f"{comp:24s}| YES      | {grounded:8d} | {stable}/{total_regs:10s} | {markers}")
        else:
            assertions = generate_acceptance_test(comp, None, layout)
            grounded = sum(1 for a in assertions if a.grounded)
            print(f"{comp:24s}| NO       | {grounded:8d} | -           | -")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "generate" and len(sys.argv) >= 3:
        cmd_generate(sys.argv[2])
    elif cmd == "collect" and len(sys.argv) >= 4:
        cmd_collect(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "check" and len(sys.argv) >= 4:
        passed = cmd_check(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        sys.exit(0 if passed else 1)
    elif cmd == "report" and len(sys.argv) >= 4:
        cmd_report(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
