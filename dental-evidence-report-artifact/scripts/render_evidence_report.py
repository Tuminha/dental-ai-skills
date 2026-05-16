#!/usr/bin/env python3
"""Render a standalone HTML evidence report from a compact JSON payload."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import sys
from typing import Any


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "evidence-report-template.html"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def block_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return esc(text)


def render_metrics(metrics: list[dict[str, Any]]) -> str:
    chunks = []
    for metric in metrics:
        chunks.append(
            '<article class="card metric">'
            f'<div class="metric-label">{esc(metric.get("label"))}</div>'
            f'<div class="metric-value">{esc(metric.get("value"))}</div>'
            f'<div class="metric-note">{esc(metric.get("note"))}</div>'
            "</article>"
        )
    return "\n".join(chunks)


def render_flags(flags: list[dict[str, Any]]) -> str:
    if not flags:
        return '<div class="flag minor"><div class="flag-title">No major flags supplied</div><div>No major flags were provided in the source analysis.</div></div>'
    chunks = []
    for flag in flags:
        severity = str(flag.get("severity", "moderate")).lower()
        if severity not in {"critical", "moderate", "minor"}:
            severity = "moderate"
        chunks.append(
            f'<div class="flag {severity}">'
            f'<div class="flag-title">{esc(flag.get("title"))}</div>'
            f'<div>{block_text(flag.get("body"))}</div>'
            "</div>"
        )
    return "\n".join(chunks)


def render_sections(sections: list[dict[str, Any]]) -> str:
    chunks = []
    for section in sections:
        width = "wide" if section.get("wide", False) else "section"
        chunks.append(
            f'<article class="card {width}">'
            f'<h2>{esc(section.get("heading"))}</h2>'
            f'<div class="body-text">{block_text(section.get("body"))}</div>'
            "</article>"
        )
    return "\n".join(chunks)


def render_citations(citations: list[dict[str, Any]]) -> str:
    if not citations:
        return "<p>No source list supplied.</p>"
    rows = []
    for citation in citations:
        rows.append(f"<tr><td>{esc(citation.get('label'))}</td><td>{esc(citation.get('detail'))}</td></tr>")
    return "<table><thead><tr><th>Source</th><th>Detail</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def render_meta(data: dict[str, Any]) -> str:
    generated = data.get("generated_date") or dt.date.today().isoformat()
    report_type = data.get("report_type") or "Dental Evidence Report"
    skill = data.get("source_skill") or "not specified"
    meta = [
        f'<span class="pill">{esc(report_type)}</span>',
        f'<span class="pill">Generated: {esc(generated)}</span>',
        f'<span class="pill">Source skill: {esc(skill)}</span>',
    ]
    retrieval = data.get("retrieval_status")
    if retrieval:
        meta.append(f'<span class="pill">Retrieval: {esc(retrieval)}</span>')
    return "\n".join(meta)


def render(data: dict[str, Any], template_path: pathlib.Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    severity = str(data.get("severity", "moderate")).lower()
    if severity not in {"critical", "moderate", "minor"}:
        severity = "moderate"
    replacements = {
        "{{TITLE}}": esc(data.get("title", "Dental Evidence Report")),
        "{{SUBTITLE}}": esc(data.get("subtitle", "")),
        "{{META}}": render_meta(data),
        "{{SEVERITY}}": severity,
        "{{VERDICT}}": block_text(data.get("verdict", "No verdict supplied.")),
        "{{METRICS}}": render_metrics(data.get("metrics", [])),
        "{{FLAGS}}": render_flags(data.get("flags", [])),
        "{{SECTIONS}}": render_sections(data.get("sections", [])),
        "{{CITATIONS}}": render_citations(data.get("citations", [])),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input JSON report payload")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="HTML template path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)
    template_path = pathlib.Path(args.template)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(data, template_path), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
