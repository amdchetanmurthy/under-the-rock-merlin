"""SimNow test runner: execute assertions and produce structured results."""

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from merlin.grounding import Assertion


@dataclass
class TestResult:
    name: str
    status: str  # PASS, FAIL, SKIP
    duration_sec: float = 0.0
    message: str = ""
    grounded: bool = True


@dataclass
class RunResult:
    component: str
    tier: str  # pr_gate, daily, release
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    verdict: str = ""
    results: list[TestResult] = field(default_factory=list)
    log_file: str = ""
    err_log_file: str = ""

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total * 100 if self.total else 0


def check_assertions(
    assertions: list[Assertion],
    simnow_log: str,
    simnow_err: str = "",
    binary_sizes: dict[str, int] | None = None,
) -> RunResult:
    """Check assertions against SimNow log output. Returns structured results."""
    result = RunResult(component="", tier="pr_gate")
    result.total = len(assertions)

    for assertion in assertions:
        if not assertion.grounded:
            result.results.append(TestResult(
                name=assertion.name, status="SKIP",
                message="ADVISORY — not grounded, does not block",
                grounded=False,
            ))
            result.skipped += 1
            continue

        t0 = time.monotonic()
        tr = _check_one(assertion, simnow_log, simnow_err, binary_sizes or {})
        tr.duration_sec = time.monotonic() - t0
        result.results.append(tr)

        if tr.status == "PASS":
            result.passed += 1
        else:
            result.failed += 1

    result.verdict = "PASS" if result.failed == 0 else "FAIL"
    return result


def _check_one(
    a: Assertion, log: str, err: str, sizes: dict[str, int]
) -> TestResult:
    if a.type == "static" and a.check.startswith("binary_size"):
        max_size = int(a.expected)
        actual = sizes.get(a.name.replace("binary_size_", ""), 0)
        if actual == 0:
            return TestResult(name=a.name, status="PASS", message="size check skipped (no binary)")
        if actual <= max_size:
            return TestResult(name=a.name, status="PASS", message=f"{actual} <= {max_size}")
        return TestResult(name=a.name, status="FAIL", message=f"{actual} > {max_size} — exceeds PSP slot")

    if a.type == "simnow_postcode":
        if a.expected.upper() in log.upper():
            return TestResult(name=a.name, status="PASS", message=f"postcode {a.expected} found")
        return TestResult(name=a.name, status="FAIL", message=f"postcode {a.expected} NOT found in log")

    if a.type == "simnow_register":
        reg_name = a.name.replace("fw_status_", "").replace("stable_reg_", "")
        pattern = re.compile(
            rf"(?:{re.escape(a.name)}|{re.escape(reg_name)}).*?=\s*(0x[0-9a-fA-F]+)", re.IGNORECASE
        )
        matches = list(pattern.finditer(log))
        match = matches[-1] if matches else None  # use LAST occurrence (final state)
        if match:
            actual = match.group(1).lower()
            expected = a.expected.lower()
            if actual == expected:
                return TestResult(name=a.name, status="PASS", message=f"{a.name} = {actual}")
            return TestResult(name=a.name, status="FAIL", message=f"{a.name} = {actual}, expected {expected}")
        return TestResult(name=a.name, status="FAIL", message=f"{a.name} not found in log")

    if a.type == "simnow_log_marker":
        if a.marker.lower() in log.lower():
            return TestResult(name=a.name, status="PASS", message=f"marker '{a.marker}' found")
        return TestResult(name=a.name, status="FAIL", message=f"marker '{a.marker}' NOT found")

    if a.type == "simnow_error_log":
        if len(err.strip()) == 0:
            return TestResult(name=a.name, status="PASS", message="error log empty")
        lines = len(err.strip().splitlines())
        return TestResult(name=a.name, status="FAIL", message=f"error log has {lines} lines")

    return TestResult(name=a.name, status="SKIP", message=f"unknown assertion type: {a.type}")


def to_junit_xml(run: RunResult) -> str:
    """Convert run results to JUnit XML for GitHub Actions."""
    suite = ET.Element("testsuite", {
        "name": f"merlin-{run.component}",
        "tests": str(run.total),
        "failures": str(run.failed),
        "skipped": str(run.skipped),
        "time": str(sum(r.duration_sec for r in run.results)),
    })

    for r in run.results:
        case = ET.SubElement(suite, "testcase", {
            "name": r.name,
            "classname": f"merlin.{run.component}",
            "time": str(r.duration_sec),
        })
        if r.status == "FAIL":
            ET.SubElement(case, "failure", {"message": r.message})
        elif r.status == "SKIP":
            ET.SubElement(case, "skipped", {"message": r.message})

    return ET.tostring(suite, encoding="unicode", xml_declaration=True)


def to_markdown(run: RunResult) -> str:
    """Human-readable markdown summary."""
    lines = [
        f"## Merlin Gate: {run.component}",
        f"**Verdict: {run.verdict}** ({run.passed}/{run.total} passed, {run.skipped} advisory skipped)",
        "",
        "| Test | Status | Details |",
        "|------|--------|---------|",
    ]
    for r in run.results:
        icon = {"PASS": "pass", "FAIL": "FAIL", "SKIP": "skip"}[r.status]
        lines.append(f"| {r.name} | {icon} | {r.message} |")
    return "\n".join(lines)
