#!/usr/bin/env python3
"""Repository smoke tests for dental-ai-skills.

These tests intentionally use only the Python standard library so they can run
in Claude Code, Codex, CI, or a minimal local checkout.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "2026.05.16"
REQUIRED_SKILLS = {
    "clinical-evidence-reviewer",
    "dental-content-creator",
    "dental-evidence-report-artifact",
    "dental-evidence-retriever",
    "dental-image-generator",
    "dental-statistical-forensics",
    "research-critic",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)


def skill_dirs() -> list[pathlib.Path]:
    return sorted(path.parent for path in ROOT.glob("*/SKILL.md"))


def test_required_skills_present() -> None:
    found = {path.name for path in skill_dirs()}
    missing = REQUIRED_SKILLS - found
    if missing:
        fail(f"missing skill dirs: {sorted(missing)}")


def test_skill_frontmatter_validator() -> None:
    run([sys.executable, "scripts/validate_skills.py"])


def test_protocol_versions() -> None:
    for path in skill_dirs():
        text = (path / "SKILL.md").read_text(encoding="utf-8")
        if f"**Skill protocol version:** {PROTOCOL_VERSION}" not in text:
            fail(f"missing protocol version in {path}")


def test_openai_metadata() -> None:
    for path in skill_dirs():
        meta = path / "agents" / "openai.yaml"
        if not meta.exists():
            fail(f"missing agents/openai.yaml for {path.name}")
        text = meta.read_text(encoding="utf-8")
        for required in ("display_name:", "short_description:", "default_prompt:", "allow_implicit_invocation: true"):
            if required not in text:
                fail(f"{meta} missing {required}")
        if f"${path.name}" not in text:
            fail(f"{meta} default_prompt must mention ${path.name}")


def test_statistical_forensics_references_exist() -> None:
    skill = ROOT / "dental-statistical-forensics" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    expected = [
        "references/core-numerical-audit.md",
        "references/effect-measure-guide.md",
        "references/dental-domain-modules.md",
        "references/clinical-thresholds-and-mcid.md",
    ]
    for rel in expected:
        if rel not in text:
            fail(f"{skill} does not mention {rel}")
        if not (ROOT / "dental-statistical-forensics" / rel).exists():
            fail(f"missing referenced file {rel}")


def test_examples_and_artifact_renderer() -> None:
    data_path = ROOT / "examples" / "iasella-statistical-forensics-report-data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for key in ("title", "verdict", "metrics", "flags", "sections", "citations"):
        if key not in data:
            fail(f"example JSON missing {key}")
    html_path = ROOT / "examples" / "iasella-statistical-forensics-report.html"
    html = html_path.read_text(encoding="utf-8")
    if "Iasella 2003 Ridge Preservation" not in html or "Major Flags" not in html:
        fail("generated HTML example missing expected content")
    with tempfile.TemporaryDirectory() as tmp:
        output = pathlib.Path(tmp) / "report.html"
        run([
            sys.executable,
            "dental-evidence-report-artifact/scripts/render_evidence_report.py",
            "--input",
            str(data_path),
            "--output",
            str(output),
        ])
        if "Iasella 2003 Ridge Preservation" not in output.read_text(encoding="utf-8"):
            fail("renderer output missing expected text")


def test_helper_scripts() -> None:
    continuous = run([
        sys.executable,
        "dental-statistical-forensics/scripts/stats_forensics_calculator.py",
        "continuous",
        "--mean-a",
        "-1.2",
        "--sd-a",
        "0.9",
        "--n-a",
        "12",
        "--mean-b",
        "-2.6",
        "--sd-b",
        "2.3",
        "--n-b",
        "12",
    ])
    result = json.loads(continuous.stdout)
    if round(result["mean_difference"], 1) != 1.4:
        fail("continuous helper returned unexpected mean difference")
    if not result["flags"]:
        fail("continuous helper should flag imprecision/dispersion concerns for Iasella-like data")

    diagnostic = run([
        sys.executable,
        "dental-statistical-forensics/scripts/stats_forensics_calculator.py",
        "diagnostic",
        "--sensitivity",
        "0.91",
        "--specificity",
        "0.84",
    ])
    diag = json.loads(diagnostic.stdout)
    if diag["positive_likelihood_ratio"] is None:
        fail("diagnostic helper did not compute LR+")

    citation = run([
        sys.executable,
        "dental-evidence-retriever/scripts/citation_validator.py",
        "PMID:123456",
        "10.1000/example-doi",
    ])
    cited = json.loads(citation.stdout)
    if len(cited["results"]) != 2:
        fail("citation validator did not return two results")
    if not all(item["syntax_valid"] for item in cited["results"]):
        fail("citation validator rejected syntactically valid examples")


def test_fixtures() -> None:
    fixtures = sorted((ROOT / "fixtures").glob("*.md"))
    if len(fixtures) < 7:
        fail("expected expanded fixture set")
    for path in fixtures:
        text = path.read_text(encoding="utf-8")
        has_companion_expected = path.name == "iasella2003-ridge-preservation.md" and (ROOT / "fixtures" / "iasella2003-expected-flags.md").exists()
        if path.name != "fixture-index.md" and not has_companion_expected and "Expected Flags" not in text:
            fail(f"{path} missing Expected Flags section")


TESTS = [
    test_required_skills_present,
    test_skill_frontmatter_validator,
    test_protocol_versions,
    test_openai_metadata,
    test_statistical_forensics_references_exist,
    test_examples_and_artifact_renderer,
    test_helper_scripts,
    test_fixtures,
]


def main() -> int:
    failed = False
    for test in TESTS:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:  # noqa: BLE001 - smoke test should report all failures clearly
            failed = True
            print(f"FAIL: {test.__name__}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
