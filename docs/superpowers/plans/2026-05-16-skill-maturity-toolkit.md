# Dental AI Skills Maturity Toolkit Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the dental AI skills repository from strong instruction skills into a more mature, reusable evidence-analysis toolkit with metadata, deterministic helpers, artifacts, examples, regression fixtures, and smoke tests.

**Architecture:** Keep `SKILL.md` files concise and use progressive disclosure. Deterministic work moves into small scripts, reusable report presentation moves into a separate artifact skill, and regression coverage lives in fixtures plus smoke tests. The existing analysis skills remain the source of methodological behavior.

**Tech Stack:** Markdown skills, YAML metadata, Python 3 standard library scripts, static HTML/SVG examples, GitHub Actions-compatible CLI validation.

---

## File Structure

- `*/agents/openai.yaml`: UI-facing metadata for Codex skill chips.
- `dental-statistical-forensics/scripts/stats_forensics_calculator.py`: deterministic statistics helper.
- `dental-evidence-retriever/scripts/citation_validator.py`: DOI/PMID syntax and optional network validator.
- `dental-evidence-report-artifact/`: new skill for turning completed evidence reviews into HTML/PDF-ready reports.
- `examples/`: sample report markdown, report JSON, generated HTML, and SVG preview.
- `fixtures/`: known-answer regression fixtures for common dental research traps.
- `scripts/smoke_test_repo.py`: repository-level validation.
- `README.md`, `CLAUDE.md`, `TESTING.md`: document new skill, scripts, fixtures, and validation workflow.

## Task 1: Branch, Plan, And Metadata

- [ ] Create feature branch from clean `main`.
- [ ] Save this implementation plan.
- [ ] Add `agents/openai.yaml` to every skill.
- [ ] Add `Skill protocol version: 2026.05.16` to every `SKILL.md`.
- [ ] Validate all skill frontmatter still parses.

## Task 2: Deterministic Helpers

- [ ] Add `stats_forensics_calculator.py` with continuous, binary, and diagnostic calculations.
- [ ] Add `citation_validator.py` with DOI/PMID syntax checks and optional network verification.
- [ ] Add usage notes to the relevant `SKILL.md` files without bloating workflow text.
- [ ] Run helper commands against known values.

## Task 3: Artifact Skill And Examples

- [ ] Add `dental-evidence-report-artifact/SKILL.md`.
- [ ] Add `render_evidence_report.py` and static HTML template assets.
- [ ] Add Iasella example JSON, markdown, HTML, and SVG preview.
- [ ] Add README visuals pointing to the example artifact.

## Task 4: Fixtures And Smoke Tests

- [ ] Add regression fixtures for split-mouth clustering, diagnostic accuracy, AMSTAR 2, implant survival/success, and periodontal clustering.
- [ ] Add fixture index.
- [ ] Add `scripts/smoke_test_repo.py` covering skills, metadata, references, fixtures, examples, and helper scripts.
- [ ] Run `validate_skills.py` and `smoke_test_repo.py`.

## Task 5: Documentation And Release

- [ ] Update README install commands and workflow map for the artifact skill.
- [ ] Update CLAUDE.md contributor notes.
- [ ] Update TESTING.md with artifact and helper-script checks.
- [ ] Commit, push, open PR, and merge after checks pass.
