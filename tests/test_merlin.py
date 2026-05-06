"""Tests for Merlin test acceptance engine."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from merlin.baseline import (
    GoldenBaseline, RegisterObservation, collect_from_log, update_baseline,
)
from merlin.grounding import (
    Assertion, load_ifwi_layout, get_psp_max_size, validate_assertions,
)
from merlin.generator import generate_acceptance_test, write_acceptance_yaml
from merlin.runner import check_assertions, to_junit_xml, to_markdown


SAMPLE_LOG = """
[00:00:01] SimNow MI450 boot starting
[00:00:05] L2 PSP Directory loaded (74 entries)
[00:00:08] PSP firmware initialized
[00:00:12] MPASP FMC initialized version 00.43.3A.00
[00:00:15] Monitor MPASP_FW_STATUS = 0x80010000
[00:00:25] TEE TOS initialized
[00:00:30] all ESIDs completed
[00:00:35] TOS steady state
[00:00:40] Monitor MPASP_FW_STATUS = 0x800f0000
[00:00:42] Monitor MID_MPASP_FW_STATUS = 0x800f0000
[00:00:45] MPIO: all PCIe links trained
[00:00:50] IP discovery: all blocks found
[00:00:55] postcode: 0X800F0000
[00:01:00] Boot complete
"""

SAMPLE_LOG_FAIL = """
[00:00:01] SimNow MI450 boot starting
[00:00:05] L2 PSP Directory loaded (74 entries)
[00:00:08] PSP firmware initialized
[00:00:15] Monitor MPASP_FW_STATUS = 0x80010000
[00:00:30] ERROR: ESID load failed
[00:00:35] Monitor MPASP_FW_STATUS = 0x80030000
"""

CONFIGS_DIR = Path(__file__).parent.parent / "configs"


# ── Baseline Tests ──

class TestBaseline:
    def test_collect_from_log(self):
        baseline = collect_from_log("fw-asp-fmc", SAMPLE_LOG, "")
        assert baseline.component == "fw-asp-fmc"
        assert len(baseline.registers) >= 2
        assert "MPASP_FW_STATUS" in baseline.registers
        assert len(baseline.log_markers) >= 5
        assert "0X800F0000" in baseline.postcodes
        assert baseline.error_log_empty is True

    def test_collect_with_errors(self):
        baseline = collect_from_log("fw-test", SAMPLE_LOG, "ERROR: something broke\n")
        assert baseline.error_log_empty is False

    def test_register_observation_stability(self):
        obs = RegisterObservation(address="0x1234", space="0.0.mpart", value="0xABCD")
        assert obs.stable is False
        for _ in range(4):
            obs.observe("0xABCD")
        assert obs.observation_count == 5
        assert obs.stable is True

    def test_register_observation_reset_on_change(self):
        obs = RegisterObservation(address="0x1234", space="0.0.mpart", value="0xABCD",
                                  observation_count=4)
        obs.observe("0xDEAD")  # different value
        assert obs.observation_count == 1
        assert obs.stable is False
        assert obs.value == "0xDEAD"

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = collect_from_log("fw-test", SAMPLE_LOG, "")
            baseline.save(Path(tmpdir))
            loaded = GoldenBaseline.load(Path(tmpdir), "fw-test")
            assert loaded is not None
            assert loaded.component == "fw-test"
            assert len(loaded.registers) == len(baseline.registers)
            assert loaded.postcodes == baseline.postcodes

    def test_load_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert GoldenBaseline.load(Path(tmpdir), "nope") is None

    def test_update_baseline_merges(self):
        b1 = collect_from_log("fw-test", SAMPLE_LOG, "")
        b2 = collect_from_log("fw-test", SAMPLE_LOG, "")
        merged = update_baseline(b1, b2)
        for reg in merged.registers.values():
            assert reg.observation_count >= 2


# ── IFWI Layout Tests ──

class TestIFWILayout:
    def test_load_layout(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assert layout["spirom_size"] == 0x800000
        assert layout["boot_pass_postcode"] == "0X800F0000"
        assert "fw-asp-fmc" in layout["psp_entries"]

    def test_psp_max_size_single(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        entries = get_psp_max_size(layout, "fw-asp-fmc")
        assert len(entries) == 1
        assert entries[0] == (0x0001, "MPASP_FMC", 131072)

    def test_psp_max_size_multi(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        entries = get_psp_max_size(layout, "fw-pmfw")
        assert len(entries) == 5
        names = [e[1] for e in entries]
        assert "MP1_PM_FW" in names
        assert "IMU_Instruction_FW" in names

    def test_psp_max_size_unknown(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assert get_psp_max_size(layout, "fw-nonexistent") == []

    def test_fw_status_monitors(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        monitors = layout["fw_status_monitors"]
        assert "MPASP_FW_STATUS" in monitors
        assert monitors["MPASP_FW_STATUS"]["address"] == "0x034000d8"


# ── Grounding Tests ──

class TestGrounding:
    def test_postcode_grounded_from_layout(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = [Assertion(name="test", type="simnow_postcode", expected="0X800F0000")]
        validated = validate_assertions(assertions, None, layout)
        assert validated[0].grounded is True

    def test_postcode_ungrounded(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = [Assertion(name="test", type="simnow_postcode", expected="0xDEADBEEF")]
        validated = validate_assertions(assertions, None, layout)
        assert validated[0].grounded is False
        assert "UNGROUNDED" in validated[0].verdict

    def test_register_grounded_from_monitor(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = [Assertion(
            name="test", type="simnow_register",
            address="0x034000d8", expected="0x800f0000",
        )]
        validated = validate_assertions(assertions, None, layout)
        assert validated[0].grounded is True

    def test_register_ungrounded_unknown_address(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = [Assertion(
            name="test", type="simnow_register",
            address="0xBADF00D", expected="0x1234",
        )]
        validated = validate_assertions(assertions, None, layout)
        assert validated[0].grounded is False

    def test_log_marker_grounded_from_baseline(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        baseline = collect_from_log("fw-test", SAMPLE_LOG, "")
        assertions = [Assertion(
            name="test", type="simnow_log_marker",
            marker="PSP firmware initialized",
        )]
        validated = validate_assertions(assertions, baseline, layout)
        assert validated[0].grounded is True

    def test_log_marker_ungrounded_no_baseline(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = [Assertion(
            name="test", type="simnow_log_marker",
            marker="invented marker that never appeared",
        )]
        validated = validate_assertions(assertions, None, layout)
        assert validated[0].grounded is False

    def test_error_log_always_grounded(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = [Assertion(name="test", type="simnow_error_log", expected="empty")]
        validated = validate_assertions(assertions, None, layout)
        assert validated[0].grounded is True


# ── Generator Tests ──

class TestGenerator:
    def test_generate_without_baseline(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = generate_acceptance_test("fw-asp-fmc", None, layout)
        assert len(assertions) >= 4  # size + postcode + 2 monitors + error log
        assert all(a.grounded for a in assertions if a.type == "static")

    def test_generate_with_baseline(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        baseline = collect_from_log("fw-asp-fmc", SAMPLE_LOG, "")
        assertions = generate_acceptance_test("fw-asp-fmc", baseline, layout)
        assert len(assertions) > 5  # baseline adds log markers
        marker_names = [a.name for a in assertions if a.type == "simnow_log_marker"]
        assert len(marker_names) >= 5

    def test_generate_multi_entry_component(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = generate_acceptance_test("fw-pmfw", None, layout)
        size_checks = [a for a in assertions if a.type == "static"]
        assert len(size_checks) == 5  # 5 PSP entries

    def test_write_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
            assertions = generate_acceptance_test("fw-asp-fmc", None, layout)
            path = write_acceptance_yaml("fw-asp-fmc", assertions, Path(tmpdir))
            assert path.exists()
            data = yaml.safe_load(path.read_text())
            assert data["component"] == "fw-asp-fmc"
            assert len(data["pr_gate"]["assertions"]) >= 4


# ── Runner Tests ──

class TestRunner:
    def test_check_pass(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        baseline = collect_from_log("fw-asp-fmc", SAMPLE_LOG, "")
        assertions = generate_acceptance_test("fw-asp-fmc", baseline, layout)
        assertions = validate_assertions(assertions, baseline, layout)
        result = check_assertions(assertions, SAMPLE_LOG, "")
        assert result.verdict == "PASS"
        assert result.failed == 0

    def test_check_fail_bad_postcode(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = generate_acceptance_test("fw-asp-fmc", None, layout)
        assertions = validate_assertions(assertions, None, layout)
        result = check_assertions(assertions, SAMPLE_LOG_FAIL, "")
        assert result.verdict == "FAIL"
        assert result.failed > 0

    def test_check_fail_error_log(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = generate_acceptance_test("fw-asp-fmc", None, layout)
        assertions = validate_assertions(assertions, None, layout)
        result = check_assertions(assertions, SAMPLE_LOG, "ERROR: bad thing\n")
        failed_names = [r.name for r in result.results if r.status == "FAIL"]
        assert "error_log_empty" in failed_names

    def test_ungrounded_skipped(self):
        assertions = [
            Assertion(name="grounded", type="simnow_postcode",
                      expected="0X800F0000", grounded=True),
            Assertion(name="advisory", type="simnow_log_marker",
                      marker="hallucinated", grounded=False),
        ]
        result = check_assertions(assertions, SAMPLE_LOG, "")
        assert result.skipped == 1
        assert result.passed == 1

    def test_junit_xml(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = generate_acceptance_test("fw-asp-fmc", None, layout)
        assertions = validate_assertions(assertions, None, layout)
        result = check_assertions(assertions, SAMPLE_LOG, "")
        result.component = "fw-asp-fmc"
        xml = to_junit_xml(result)
        assert "testsuite" in xml
        assert "fw-asp-fmc" in xml

    def test_markdown_report(self):
        layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")
        assertions = generate_acceptance_test("fw-asp-fmc", None, layout)
        assertions = validate_assertions(assertions, None, layout)
        result = check_assertions(assertions, SAMPLE_LOG, "")
        result.component = "fw-asp-fmc"
        md = to_markdown(result)
        assert "Merlin Gate" in md
        assert "fw-asp-fmc" in md


# ── Integration Test ──

class TestIntegration:
    def test_full_pipeline(self):
        """End-to-end: collect → generate → validate → check → learn."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baselines_dir = Path(tmpdir) / "baselines"
            accept_dir = Path(tmpdir) / "acceptance"
            layout = load_ifwi_layout(CONFIGS_DIR / "ifwi_layout.yaml")

            # 1. Collect baseline
            baseline = collect_from_log("fw-asp-fmc", SAMPLE_LOG, "")
            baseline.save(baselines_dir)

            # 2. Load and generate
            loaded = GoldenBaseline.load(baselines_dir, "fw-asp-fmc")
            assertions = generate_acceptance_test("fw-asp-fmc", loaded, layout)

            # 3. Validate grounding
            validated = validate_assertions(assertions, loaded, layout)
            grounded = [a for a in validated if a.grounded]
            assert len(grounded) >= 10

            # 4. Check against log
            result = check_assertions(validated, SAMPLE_LOG, "")
            result.component = "fw-asp-fmc"
            assert result.verdict == "PASS"

            # 5. Write acceptance YAML
            path = write_acceptance_yaml("fw-asp-fmc", validated, accept_dir)
            assert path.exists()

            # 6. Learn (update baseline)
            new_obs = collect_from_log("fw-asp-fmc", SAMPLE_LOG, "")
            updated = update_baseline(loaded, new_obs)
            updated.save(baselines_dir)

            reloaded = GoldenBaseline.load(baselines_dir, "fw-asp-fmc")
            for reg in reloaded.registers.values():
                assert reg.observation_count >= 2

    def test_baseline_grows_to_stable(self):
        """After 5 consistent runs, registers become stable (grounded)."""
        baseline = collect_from_log("fw-test", SAMPLE_LOG, "")
        for _ in range(5):
            new_run = collect_from_log("fw-test", SAMPLE_LOG, "")
            baseline = update_baseline(baseline, new_run)

        stable_count = sum(1 for r in baseline.registers.values() if r.stable)
        assert stable_count > 0, "At least one register should be stable after 5 runs"
