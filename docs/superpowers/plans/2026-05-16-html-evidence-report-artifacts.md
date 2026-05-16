# HTML Evidence Report Artifacts Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional HTML artifact/report layer that turns structured outputs from the dental literature skills into readable, shareable, visually rich clinical/research reports without replacing Markdown as the canonical reasoning format.

**Architecture:** Keep `research-critic`, `clinical-evidence-reviewer`, `dental-evidence-retriever`, and planned `dental-statistical-forensics` as the analysis engines. Add a separate `dental-html-report` skill that consumes their structured Markdown/output sections and produces a self-contained static HTML file or an HTML code block, depending on runtime. Use progressive disclosure: a concise `SKILL.md`, focused reference files for report schema/design/chart patterns, and an optional deterministic renderer script only if the implementation needs repeatable HTML generation.

**Tech Stack:** Markdown Agent Skills (`SKILL.md`), YAML frontmatter, static self-contained HTML/CSS/SVG, optional vanilla JS for copy/tabs/toggles, optional pure-Python renderer script, repo docs (`README.md`, `CLAUDE.md`, `TESTING.md`). No broad tool permissions and no external CDN dependencies by default.

---

## Design Position

HTML should be an optional presentation layer, not the primary audit format.

- Markdown remains the canonical, reviewable, low-token, Git-friendly reasoning output.
- HTML is generated only when the user asks for a report, artifact, printable summary, shareable review, visual dashboard, or teaching handout.
- HTML must render the analysis and extracted data already produced by the core skills. It must not add new clinical claims, invent citations, invent effect sizes, or silently reinterpret evidence.
- If the runtime can write files (Codex / Claude Code), generate a local `.html` file. If not, output a fenced HTML block and clear instructions that it is an artifact the user can save/render in their environment.

---

## Primary Use Cases

1. **Single-paper critique report**
   - Input: `research-critic` output.
   - Output: HTML peer-review report with PICO, study classification, bias tool, severity-coded findings, claim-to-evidence map, study credibility score, and hand-off note.

2. **Body-of-evidence clinical report**
   - Input: `clinical-evidence-reviewer` output plus retrieval log if available.
   - Output: HTML evidence synthesis with retrieval mode, PICO, GRADE-by-outcome table, guideline status, treatment comparison panels, unknowns, and conservative bottom line.

3. **Statistical forensics report**
   - Input: planned `dental-statistical-forensics` output.
   - Output: HTML numerical audit with outcome map, dispersion/predictability warnings, CI/MCID panels, unit-of-analysis/model issues, missing-data/multiplicity flags, and claim-to-number mismatches.

4. **Teaching/Journal club artifact**
   - Input: any of the above.
   - Output: visually digestible report suitable for students, residents, journal club, or clinical team discussion.

5. **Shareable PDF-ready report**
   - Input: completed analysis.
   - Output: print-optimized HTML that can be opened in a browser and exported to PDF.

---

## Non-Goals

- Do not convert every skill output to HTML by default.
- Do not build a full web app.
- Do not add analytics, tracking, external fonts, external JS, or external CSS by default.
- Do not require a dev server.
- Do not make HTML generation a substitute for source/citation verification.
- Do not make charts from missing or inferred data unless the approximation is explicitly labeled and the assumptions are visible.
- Do not add broad `allowed-tools` permissions.

---

## File Structure

Create:

- `dental-html-report/SKILL.md`
  - Thin spine: when to use, runtime behavior, input contract, artifact safety, output modes, report types, and reference-loading rules.
- `dental-html-report/references/report-schema.md`
  - Structured input and output schema for each report type.
- `dental-html-report/references/design-system.md`
  - Visual language, CSS tokens, layout rules, severity colors, GRADE colors, typography, print behavior, accessibility.
- `dental-html-report/references/chart-patterns.md`
  - Safe SVG/CSS chart patterns: evidence heatmaps, GRADE table, risk cards, simple forest plot, SD-vs-effect visualization, dispersion/range plot, citation/provenance table.
- `dental-html-report/references/security-and-portability.md`
  - Self-contained HTML, escaping, no external resources by default, no secret leakage, no hidden tracking, print/export, runtime behavior.
- Optional later: `dental-html-report/scripts/render_report.py`
  - Deterministic renderer that accepts a structured JSON report object and writes a self-contained HTML file.
- `docs/examples/html-reports/`
  - Demo HTML files used only for README/gallery screenshots. Every demo must be clearly labeled as synthetic/example or generated from a documented source analysis.
- `docs/assets/screenshots/`
  - Optimized screenshots used in the README visual gallery.

Modify:

- `research-critic/SKILL.md`
  - Add optional hand-off to `dental-html-report` when the user asks for a shareable/visual report.
- `clinical-evidence-reviewer/SKILL.md`
  - Add optional hand-off to `dental-html-report`.
- `dental-evidence-retriever/SKILL.md`
  - Add optional hand-off to render retrieval logs as HTML.
- Planned `dental-statistical-forensics/SKILL.md`
  - Include an optional hand-off to `dental-html-report` in that implementation.
- `README.md`
  - Add the new skill, install lines, workflow diagram, visual gallery, and explanation of Markdown canonical output vs optional HTML artifact.
- `CLAUDE.md`
  - Add report artifact skill and contributing rules around visual/citation integrity.
- `TESTING.md`
  - Add manual tests for HTML artifact generation, no fabricated charts, accessibility, printability, and runtime behavior.

No changes:

- `dental-content-creator/SKILL.md` unless later deciding to support patient-facing HTML handouts.
- `dental-image-generator/SKILL.md`.

---

## Chunk 1: Branch And Baseline

### Task 1: Start From Current Main

**Files:**
- Inspect: `git log`
- Inspect: `README.md`

- [ ] **Step 1: Fetch and update main**

Run:

```bash
git fetch origin
git checkout main
git pull --ff-only
```

Expected: main includes:

- `6f90162 docs: plan dental statistical forensics skill (#2)`
- `13a3a37 docs: align project-install snippet with all five skills (Codex review)`

- [ ] **Step 2: Create implementation branch**

Run:

```bash
git checkout -b feat/dental-html-report
```

Expected: new branch from current main.

---

## Chunk 2: New Skill Skeleton

### Task 2: Create `dental-html-report/SKILL.md`

**Files:**
- Create: `dental-html-report/SKILL.md`
- Create directory: `dental-html-report/references/`

- [ ] **Step 1: Add frontmatter**

Use this pattern:

```markdown
---
name: dental-html-report
description: Use when the user asks to turn a dental research critique, clinical evidence review, retrieval log, statistical-forensics audit, journal-club analysis, or clinical protocol review into a visual HTML report, artifact, dashboard, printable summary, or shareable file. Generates self-contained HTML from already-available analysis without inventing citations, effect sizes, charts, or clinical claims.
when_to_use: User asks for HTML, artifact, visual report, printable report, shareable evidence summary, dashboard, charts, heatmap, forest plot, journal-club handout, PDF-ready report, or visual rendering of research-critic, clinical-evidence-reviewer, dental-evidence-retriever, or dental-statistical-forensics output.
effort: high
---
```

Keep combined `description` + `when_to_use` under 1,536 characters.

- [ ] **Step 2: Add identity and contract**

Add:

```markdown
# Dental HTML Report

You are a scientific report designer for dental and oral-health evidence. Your job is to turn completed analysis into a readable, self-contained HTML artifact.

Core contract:
- Preserve the source analysis.
- Add visual structure, not new evidence.
- Never invent citations, PMIDs, DOIs, effect sizes, sample sizes, CIs, GRADE ratings, or charts.
- Show provenance and limitations.
- Prefer static HTML/CSS/SVG. Use vanilla JS only for local interactions such as tabs, collapsible sections, copy buttons, and filters.
```

- [ ] **Step 3: Add runtime output modes**

Add:

| Runtime | Behavior |
|---|---|
| Codex / Claude Code with filesystem access | Write a self-contained `.html` file under `reports/` unless user specifies another path. |
| ChatGPT / claude.ai / no filesystem | Output a fenced `html` code block plus a concise note that it is intended to be rendered as an artifact/file. |
| Unknown runtime | Ask whether to write a file or output HTML inline. |

- [ ] **Step 4: Add reference-loading rules**

Add:

```markdown
Load references only as needed:
- Always use `references/report-schema.md`.
- Use `references/design-system.md` for visual style and accessibility.
- Use `references/chart-patterns.md` when rendering numeric or categorical visualizations.
- Use `references/security-and-portability.md` before writing any HTML file or adding JavaScript.
```

- [ ] **Step 5: Add required output sections**

Add:

```markdown
Every HTML report must contain:
- Title and report type.
- Source analysis provenance.
- Evidence/retrieval status when applicable.
- Educational/clinical disclaimer.
- Executive summary.
- Key findings with severity or certainty.
- Main tables from source analysis.
- Visualizations only where source data are present.
- Citations/provenance table.
- Limitations and "what this report does not prove."
- Generated date and artifact version.
```

- [ ] **Step 6: Add methodology review date**

Use:

```markdown
## Methodology Review Date

**Last methodology review:** 2026-05-16

Re-review this skill when artifact rendering behavior, Codex/Claude Code file handling, browser security expectations, or the report schemas of companion skills change.
```

- [ ] **Step 7: Validate frontmatter**

Run:

```bash
ruby -ryaml -e 'ARGV.each { |p| t=File.read(p); fm=t.split(/^---\s*$/,3)[1]; y=YAML.safe_load(fm); puts [p, y["name"], ((y["description"]||"")+(y["when_to_use"]||"")).length, t.lines.count].join(" | ") }' dental-html-report/SKILL.md
```

Expected: valid YAML, name `dental-html-report`, combined trigger text under 1,536 characters.

---

## Chunk 3: Report Schema Reference

### Task 3: Create `references/report-schema.md`

**Files:**
- Create: `dental-html-report/references/report-schema.md`

- [ ] **Step 1: Define common metadata schema**

Add:

```markdown
## Common Report Metadata

- report_title
- report_type: single-paper-critique / evidence-review / retrieval-log / statistical-forensics / combined
- generated_at
- generated_by_skill
- source_skills_used
- source_input_type: pasted paper / abstract / retrieval log / existing analysis / mixed
- retrieval_status: live search performed / no live search / user-provided sources / not applicable
- clinical_disclaimer
- limitations
```

- [ ] **Step 2: Define single-paper critique schema**

Required blocks:

- Quick verdict.
- PICO.
- Study classification.
- Bias assessment tool and domain judgments.
- Severity-coded findings.
- Claim-to-evidence map.
- Study credibility scores.
- Hand-off recommendation.

- [ ] **Step 3: Define evidence-review schema**

Required blocks:

- Evidence Retrieval Mode.
- PICO.
- Quick answer.
- GRADE by critical outcome.
- Evidence summary table.
- Treatment options compared.
- What's unknown.
- Patient selection.
- Guideline status.
- Clinical bottom line.

- [ ] **Step 4: Define statistical-forensics schema**

Required blocks:

- Statistical verdict.
- Data extracted.
- Outcome/effect-measure map.
- Dispersion and individual predictability.
- Precision and clinical thresholds.
- Unit-of-analysis/model audit.
- Missing data and multiplicity.
- Measurement reliability.
- Dental-domain findings.
- Claims unsupported by numbers.

- [ ] **Step 5: Define retrieval-log schema**

Required blocks:

- Retrieval mode.
- PICO.
- Search strategies.
- Live retrieval results, if any.
- Retrieval log.
- Coverage statement.
- Hand-off recommendation.

- [ ] **Step 6: Define combined report schema**

For reports that combine multiple skills:

- Start with one executive summary.
- Use tabs/sections for each source skill.
- Keep a consolidated limitations/provenance section.
- Preserve each source skill's original bottom line.
- Do not collapse study credibility into GRADE certainty.

---

## Chunk 4: Design System Reference

### Task 4: Create `references/design-system.md`

**Files:**
- Create: `dental-html-report/references/design-system.md`

- [ ] **Step 1: Define visual principles**

Add:

- Quiet, clinical, professional, not marketing-heavy.
- Dense but readable.
- Avoid decorative gradients/orbs.
- Use tables for exact data and cards only for repeated findings.
- Use color as secondary encoding, never sole encoding.
- Strong print/PDF behavior.

- [ ] **Step 2: Define CSS tokens**

Include:

```css
:root {
  --bg: #f7f8fa;
  --panel: #ffffff;
  --text: #17202a;
  --muted: #5d6b78;
  --line: #d9e0e7;
  --critical: #b42318;
  --critical-bg: #fff1f0;
  --moderate: #b76e00;
  --moderate-bg: #fff7e6;
  --minor: #2f6f4e;
  --minor-bg: #edf7f1;
  --high: #1f7a4d;
  --moderate-grade: #7a5a00;
  --low: #9a3412;
  --very-low: #991b1b;
}
```

Allow implementer to refine colors, but preserve contrast.

- [ ] **Step 3: Define layout**

Required:

- Max-width content container.
- Sticky/local table of contents for long reports.
- Responsive behavior for mobile.
- Print CSS using `@media print`.
- Tables scroll horizontally on narrow screens.
- Appendices collapsible in screen view but expanded/usable for print.

- [ ] **Step 4: Define accessibility**

Required:

- Semantic headings.
- Table captions.
- `aria-label` for interactive controls.
- Keyboard-accessible tabs/toggles.
- Contrast sufficient for clinical reports.
- Do not use color alone for severity/GRADE.

---

## Chunk 5: Chart Patterns Reference

### Task 5: Create `references/chart-patterns.md`

**Files:**
- Create: `dental-html-report/references/chart-patterns.md`

- [ ] **Step 1: Add chart safety rule**

Add:

```markdown
Only render a chart when source data are explicitly present. If data are missing, render a "Data not reported" callout instead of inventing values.
```

- [ ] **Step 2: Add severity heatmap pattern**

Use for:

- Critical/moderate/minor findings by domain.
- Risk-of-bias domains.
- Claim-support status.

Implementation: HTML table with CSS classes, not canvas.

- [ ] **Step 3: Add GRADE by outcome pattern**

Use:

- Rows for outcomes.
- Certainty badge.
- Downgrade reasons.
- Critical/important tag.

No averaging across outcomes.

- [ ] **Step 4: Add simple forest/effect plot pattern**

Use only when effect estimate and CI are available.

Required labels:

- Effect estimate.
- 95% CI.
- Null line.
- Clinical threshold line if available.
- Direction of benefit/harm.

Use inline SVG.

- [ ] **Step 5: Add SD/range/predictability pattern**

Use for statistical-forensics reports:

- Mean marker.
- SD band if SD is available.
- Range whisker if range is available.
- Clinical threshold marker if available.
- Warning when SD exceeds mean effect or contextual threshold.

Use inline SVG or CSS bars.

- [ ] **Step 6: Add retrieval coverage pattern**

Use for retrieval reports:

- Per-source searched/not searched/failed badges.
- Date searched.
- Result counts only when actually searched.

- [ ] **Step 7: Add no-chart fallback**

When data are insufficient:

```html
<div class="callout missing-data">
  Chart not rendered: confidence interval or source numeric data were not reported.
</div>
```

---

## Chunk 6: Security And Portability Reference

### Task 6: Create `references/security-and-portability.md`

**Files:**
- Create: `dental-html-report/references/security-and-portability.md`

- [ ] **Step 1: Add self-contained artifact rules**

Required:

- No external CSS, JS, fonts, images, or CDN by default.
- Inline CSS in `<style>`.
- Inline SVG for simple charts.
- Vanilla JS only if needed.
- No network requests.
- No analytics or tracking.

- [ ] **Step 2: Add escaping rules**

Required:

- Escape user-provided text before inserting into HTML.
- Do not render arbitrary pasted HTML from papers/users as trusted HTML.
- Treat article titles, author names, citations, and extracted claims as text content.

- [ ] **Step 3: Add privacy rules**

Required:

- Do not include API keys, local paths, hidden prompts, environment variables, or private notes unless explicitly requested.
- If report includes patient/case data, warn about de-identification.
- Add a visible provenance section explaining what sources were used.

- [ ] **Step 4: Add runtime behavior**

Required:

- In filesystem runtimes, write to `reports/<slug>-<YYYYMMDD-HHMM>.html`.
- If `reports/` does not exist, create it.
- If a filename exists, append a suffix rather than overwriting.
- After writing, provide the absolute path.
- Do not start a dev server; static HTML opens directly in a browser.

- [ ] **Step 5: Add print/export behavior**

Required:

- Include `@media print`.
- Avoid dark backgrounds.
- Expand critical content for print.
- Hide interactive-only controls in print.

---

## Chunk 7: Optional Renderer Script Decision

### Task 7: Decide Whether To Add `scripts/render_report.py`

**Files:**
- Optional create: `dental-html-report/scripts/render_report.py`
- Optional create: `dental-html-report/scripts/example_report.json`

- [ ] **Step 1: Default decision**

Default for v1: do **not** require a renderer script. Let the skill generate HTML directly from structured analysis.

Reason: the current repo is instruction-first and the input format from companion skills is not yet strict JSON.

- [ ] **Step 2: Add script only if implementing deterministic rendering**

If added, script requirements:

- Input: JSON object following `references/report-schema.md`.
- Output: self-contained HTML file.
- No network access.
- Escapes all string content.
- Supports only safe built-in chart patterns.
- Has deterministic output given the same input.

- [ ] **Step 3: If script exists, add smoke test**

Run:

```bash
python3 dental-html-report/scripts/render_report.py dental-html-report/scripts/example_report.json --output /tmp/dental-report-test.html
test -s /tmp/dental-report-test.html
```

Expected: non-empty HTML file with no network links.

---

## Chunk 8: Skill Integrations

### Task 8: Add Optional HTML Handoff To `research-critic`

**Files:**
- Modify: `research-critic/SKILL.md`

- [ ] **Step 1: Add hand-off rule**

Add:

```markdown
If the user asks for a visual, printable, shareable, HTML, artifact, dashboard, or journal-club report, hand off to `dental-html-report` after completing the critique. Pass the completed PICO, study classification, bias assessment, severity-coded findings, claim-to-evidence map, and study credibility scores.
```

- [ ] **Step 2: Preserve canonical output**

Do not replace the standard research critique output with HTML unless the user explicitly asks for HTML.

### Task 9: Add Optional HTML Handoff To `clinical-evidence-reviewer`

**Files:**
- Modify: `clinical-evidence-reviewer/SKILL.md`

- [ ] **Step 1: Add hand-off rule**

Add:

```markdown
If the user asks for a visual, printable, shareable, HTML, artifact, dashboard, or clinical-team report, hand off to `dental-html-report` after completing the evidence review. Pass the Evidence Retrieval Mode, PICO, GRADE-by-outcome table, evidence summary, treatment comparison, guideline status, and bottom line.
```

- [ ] **Step 2: Preserve citation policy**

State that HTML rendering must preserve all DOI/PMID/guideline citations and uncertainty labels.

### Task 10: Add Optional HTML Handoff To `dental-evidence-retriever`

**Files:**
- Modify: `dental-evidence-retriever/SKILL.md`

- [ ] **Step 1: Add hand-off rule**

Add:

```markdown
If the user asks for a visual search report, hand off to `dental-html-report` with the retrieval mode, PICO, search strategies, live retrieval results if any, retrieval log, and coverage statement.
```

### Task 11: Integrate With Planned `dental-statistical-forensics`

**Files:**
- Modify later when implementing: `dental-statistical-forensics/SKILL.md`
- Modify optional: `docs/superpowers/plans/2026-05-16-dental-statistical-forensics.md`

- [ ] **Step 1: Add to future implementation**

When implementing `dental-statistical-forensics`, include:

```markdown
If the user asks for a visual numerical audit, HTML artifact, shareable report, or charted output, hand off to `dental-html-report` with the statistical verdict, extracted data, outcome/effect map, dispersion/predictability findings, precision/MCID findings, unit/model audit, missing-data/multiplicity findings, and bottom line.
```

- [ ] **Step 2: Decide whether to update existing plan**

If this plan is implemented before statistical-forensics, update the statistical-forensics plan with the hand-off requirement. If statistical-forensics is implemented first, add this hand-off directly in the implementation PR.

---

## Chunk 9: README And Project Docs

### Task 12: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add new skill row**

Add:

```markdown
| [**Dental HTML Report**](dental-html-report/) | Researchers, clinicians, educators | Optional HTML artifact layer: renders critiques, evidence reviews, retrieval logs, and statistical-forensics audits as self-contained visual reports with tables, SVG charts, severity/GRADE badges, provenance, and print/PDF-ready layout |
```

- [ ] **Step 2: Update workflow diagram**

Add:

```markdown
Any completed analysis -> dental-html-report -> self-contained HTML/PDF-ready artifact
```

Make clear that HTML is optional and downstream of analysis.

- [ ] **Step 3: Update install snippets**

Add `cp -r dental-html-report ...` to personal and project Claude Code install snippets.

- [ ] **Step 4: Add "HTML artifacts" detail section**

Include:

- Markdown remains canonical.
- HTML is optional for presentation/shareability.
- Reports are self-contained by default.
- Charts only from reported data.
- No hidden tracking/external dependencies.
- Opens directly in browser; no dev server required.

### Task 13: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add skill row**

Add `Dental HTML Report`.

- [ ] **Step 2: Add contributing rules**

Add:

```markdown
- HTML artifacts are presentation layers. They must preserve source analysis and must not introduce new clinical claims.
- Charts must only visualize explicitly reported or clearly labeled approximate data.
- Self-contained HTML should avoid external network dependencies, tracking, and hidden metadata.
```

---

## Chunk 10: Visual Gallery And README Screenshots

### Task 14: Add Demo HTML Fixtures And Screenshot Assets

**Files:**
- Create: `docs/examples/html-reports/evidence-review-demo.html`
- Create: `docs/examples/html-reports/statistical-forensics-demo.html`
- Create: `docs/examples/html-reports/research-critic-demo.html`
- Create: `docs/assets/screenshots/html-report-overview.png`
- Create: `docs/assets/screenshots/statistical-forensics-preview.png`
- Create: `docs/assets/screenshots/research-critic-preview.png`
- Optional create: `docs/assets/screenshots/grade-dashboard-preview.png`
- Modify: `README.md`

- [ ] **Step 1: Create demo HTML fixtures**

Create static demo HTML files that represent the intended report output.

Rules:

- Demo files must be clearly labeled: `Demo artifact - synthetic/example data`.
- If using values inspired by a real paper, state: `Values shown for layout demonstration; verify against source before educational or clinical use`.
- Do not include fabricated DOIs, PMIDs, author/year pairs, guideline claims, or patient identifiers.
- Keep demo HTML self-contained: inline CSS, inline SVG, no external assets.
- Prefer the same design tokens defined in `dental-html-report/references/design-system.md`.

- [ ] **Step 2: Create the evidence review demo**

`docs/examples/html-reports/evidence-review-demo.html` should show:

- Evidence Retrieval Mode panel.
- PICO card.
- GRADE-by-critical-outcome table.
- Treatment comparison panels.
- Guideline status table.
- Limitations/provenance section.

All data should be clearly demo/synthetic unless generated from a completed verified review.

- [ ] **Step 3: Create the statistical forensics demo**

`docs/examples/html-reports/statistical-forensics-demo.html` should show:

- Statistical Forensics Verdict.
- Mean/SD/range visualization.
- CI/MCID placeholder panel with `Not reported` state when CI is unavailable.
- Unit-of-analysis/model audit.
- Missing-data/multiplicity warning cards.
- Claims-the-numbers-do-not-support section.

Use an SD/range example that demonstrates the key concept:

```text
Mean effect favorable, but SD/range indicates limited individual predictability.
```

- [ ] **Step 4: Create the research critic demo**

`docs/examples/html-reports/research-critic-demo.html` should show:

- Study credibility score card.
- Phase 0 extraction summary.
- Bias-tool panel.
- Severity heatmap.
- Claim-to-evidence table.
- Hand-off note to clinical evidence review.

- [ ] **Step 5: Generate screenshots from the demo HTML**

Use a deterministic browser screenshot workflow. Prefer Playwright if available:

```bash
mkdir -p docs/assets/screenshots
npx playwright screenshot --viewport-size=1440,1100 "file://$(pwd)/docs/examples/html-reports/evidence-review-demo.html" docs/assets/screenshots/html-report-overview.png
npx playwright screenshot --viewport-size=1440,1100 "file://$(pwd)/docs/examples/html-reports/statistical-forensics-demo.html" docs/assets/screenshots/statistical-forensics-preview.png
npx playwright screenshot --viewport-size=1440,1100 "file://$(pwd)/docs/examples/html-reports/research-critic-demo.html" docs/assets/screenshots/research-critic-preview.png
```

If Playwright is unavailable, use the Codex/Claude browser screenshot workflow or another reproducible local browser capture. Record the command used in the PR body.

- [ ] **Step 6: Optimize screenshots**

Target:

- Each screenshot ideally < 750 KB.
- Use PNG for crisp text; WebP is acceptable if GitHub renders it reliably and alt text is present.
- Avoid huge full-page screenshots that make the README slow.
- Crop to first-screen/high-signal areas if needed.

Validation:

```bash
du -h docs/assets/screenshots/*
file docs/assets/screenshots/*
```

- [ ] **Step 7: Add README visual gallery**

Near the top of `README.md`, after the introductory paragraph and before/after "What's Inside", add:

```markdown
## Preview

<p align="center">
  <img src="docs/assets/screenshots/html-report-overview.png" alt="Preview of a dental HTML evidence report with retrieval status, PICO, GRADE-by-outcome table, and treatment comparison panels" width="100%">
</p>

| Statistical Forensics | Research Critic |
|---|---|
| <img src="docs/assets/screenshots/statistical-forensics-preview.png" alt="Preview of a statistical forensics report showing mean, SD, range, and individual predictability warnings"> | <img src="docs/assets/screenshots/research-critic-preview.png" alt="Preview of a research critic report showing study credibility, severity heatmap, and claim-to-evidence mapping"> |
```

Keep alt text specific and descriptive.

- [ ] **Step 8: Link demo HTML examples**

In the README HTML artifact section, link to:

- `docs/examples/html-reports/evidence-review-demo.html`
- `docs/examples/html-reports/statistical-forensics-demo.html`
- `docs/examples/html-reports/research-critic-demo.html`

Warn that GitHub displays raw HTML source in the repo; users should download/open locally or use GitHub Pages if enabled.

- [ ] **Step 9: Add optional GitHub Pages note**

Add a short note:

```markdown
If GitHub Pages is enabled for this repo, demo reports can be published under `/docs/examples/html-reports/` for browser previews. Do not publish reports containing patient data or private review notes.
```

Do not enable Pages from the plan unless the user explicitly requests it.

- [ ] **Step 10: Add gallery asset checks**

Run:

```bash
test -s docs/assets/screenshots/html-report-overview.png
test -s docs/assets/screenshots/statistical-forensics-preview.png
test -s docs/assets/screenshots/research-critic-preview.png
rg -n "Demo artifact|synthetic|example data" docs/examples/html-reports
```

Expected: screenshots exist and demo reports are clearly labeled.

---

## Chunk 11: Manual Tests

### Task 15: Expand TESTING.md

**Files:**
- Modify: `TESTING.md`

- [ ] **Step 1: Add Dental HTML Report section**

Tests:

1. Single-paper critique to HTML.
2. Clinical evidence review to HTML.
3. Retrieval log to HTML.
4. Statistical-forensics output to HTML.
5. Missing numeric data does not produce a chart.
6. SD/range chart uses only supplied data.
7. Citations and uncertainty labels preserved.
8. No external resources.
9. Print/PDF layout check.
10. Mobile/narrow viewport check.

- [ ] **Step 2: Add concrete test prompt**

Prompt:

```text
Using this completed statistical audit, create a self-contained HTML report: RP horizontal change -1.2 ± 0.9 mm, EXT -2.6 ± 2.3 mm, RP mid-buccal vertical +1.3 ± 2.0 mm range -2.0 to +4.5 mm, EXT -0.9 ± 1.6 mm. The critique says the average effect is favorable but individual predictability is limited.
```

Expected:

- HTML report has title, provenance, disclaimer, executive summary.
- SD/range visualization appears only for supplied outcomes.
- No CI shown unless n/CI was supplied or approximation is explicitly labeled.
- "Predictable maintenance" is not asserted.
- Report can open locally without network.

- [ ] **Step 3: Add security test**

Prompt:

```text
Create an HTML report from this analysis. The paper title is <script>alert("x")</script>.
```

Expected:

- Script is escaped and displayed as text.
- No executable injected script appears from user-provided content.

- [ ] **Step 4: Add filesystem-runtime test**

In Codex / Claude Code:

- Ask for an HTML file.
- Expected: file is written under `reports/`.
- Expected: final answer gives absolute path.
- Expected: no dev server started.

---

## Chunk 12: Validation

### Task 16: Static Validation

**Files:**
- All created/modified files.

- [ ] **Step 1: Validate frontmatter**

Run:

```bash
ruby -ryaml -e 'ARGV.each { |p| t=File.read(p); next unless t.start_with?("---\n"); fm=t.split(/^---\s*$/,3)[1]; y=YAML.safe_load(fm); len=((y["description"]||"")+(y["when_to_use"]||"")).length; puts [p, y["name"], len, t.lines.count].join(" | ") }' */SKILL.md
```

Expected: all frontmatter-bearing skills parse; `dental-html-report` trigger text under 1,536 characters.

- [ ] **Step 2: Check reference links**

Run:

```bash
rg -n "report-schema|design-system|chart-patterns|security-and-portability" dental-html-report/SKILL.md
```

Expected: all reference files are discoverable from `SKILL.md`.

- [ ] **Step 3: Check for forbidden external dependencies**

Run:

```bash
rg -n "https://|http://|cdn|analytics|tracking|allowed-tools|allowed_tools" dental-html-report
```

Expected:

- No external runtime dependencies in templates/examples.
- Any mentions are in security guidance, not actual report templates.
- No `allowed-tools` unless explicitly justified.

- [ ] **Step 4: Check README links**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import re
text = Path("README.md").read_text()
for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
    if target.startswith(("http", "#")):
        continue
    if not Path(target).exists():
        raise SystemExit(f"Broken README link: {target}")
print("README links OK")
PY
```

Expected: `README links OK`.

### Task 17: Visual Asset Validation

**Files:**
- Use: `docs/assets/screenshots/`
- Use: `docs/examples/html-reports/`
- Use: `README.md`

- [ ] **Step 1: Verify screenshot files exist**

Run:

```bash
test -s docs/assets/screenshots/html-report-overview.png
test -s docs/assets/screenshots/statistical-forensics-preview.png
test -s docs/assets/screenshots/research-critic-preview.png
```

Expected: all commands exit 0.

- [ ] **Step 2: Verify demo labels**

Run:

```bash
rg -n "Demo artifact|synthetic|example data|layout demonstration" docs/examples/html-reports
```

Expected: every demo report clearly labels its data/provenance.

- [ ] **Step 3: Verify README image links**

Run:

```bash
rg -n "docs/assets/screenshots/.+\\.png" README.md
python3 - <<'PY'
from pathlib import Path
import re
text = Path("README.md").read_text()
for target in re.findall(r'src="([^"]+)"', text):
    if target.startswith("docs/assets/") and not Path(target).exists():
        raise SystemExit(f"Missing README image: {target}")
print("README images OK")
PY
```

Expected: `README images OK`.

- [ ] **Step 4: Verify image size budget**

Run:

```bash
du -h docs/assets/screenshots/*
```

Expected: screenshots are reasonably sized for README use; optimize any very large image before merging.

### Task 18: Manual Render Validation

**Files:**
- Use: `TESTING.md`

- [ ] **Step 1: Generate a single-paper HTML report**

Expected:

- Valid self-contained HTML.
- PICO and credibility data preserved.
- Severity-coded findings visible.
- Claims/citations preserved.

- [ ] **Step 2: Generate an evidence-review HTML report**

Expected:

- Evidence Retrieval Mode visible.
- GRADE per outcome preserved.
- Guideline-vs-consensus distinction preserved.
- No new citations added.

- [ ] **Step 3: Generate an SD/range HTML report**

Expected:

- Mean/SD/range chart only uses supplied values.
- Report highlights individual predictability limitation.
- No CI if required n/SE/CI absent.

- [ ] **Step 4: Open locally**

Run:

```bash
open reports/<generated-file>.html
```

Expected: browser opens the report directly; no server needed.

---

## Chunk 13: Commit And PR

### Task 19: Commit Implementation

**Files:**
- All created/modified files.

- [ ] **Step 1: Review diff**

Run:

```bash
git diff --stat
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 2: Commit**

Run:

```bash
git add dental-html-report docs/examples/html-reports docs/assets/screenshots research-critic/SKILL.md clinical-evidence-reviewer/SKILL.md dental-evidence-retriever/SKILL.md README.md CLAUDE.md TESTING.md
git commit -m "feat: add dental html report artifact skill"
```

Expected: commit created.

- [ ] **Step 3: Push**

Run:

```bash
git push -u origin feat/dental-html-report
```

Expected: branch pushed.

- [ ] **Step 4: Open PR**

Run:

```bash
gh pr create \
  --title "Add dental HTML report artifact skill" \
  --body-file /tmp/dental-html-report-pr.md
```

PR body should include:

- Summary of new skill.
- Why HTML is optional and downstream of analysis.
- Security/portability guarantees.
- Integration points.
- README visual gallery and screenshot generation command.
- Validation commands.
- Manual render tests.
- Whether renderer script was included or deferred.

---

## Suggested PR Review Checklist

- [ ] HTML is optional, not default.
- [ ] Markdown remains canonical analysis format.
- [ ] New skill has valid frontmatter and concise trigger text.
- [ ] HTML report skill preserves citations, uncertainty labels, GRADE, and study-credibility distinctions.
- [ ] No invented charts or numeric values.
- [ ] No external CDN/network dependencies by default.
- [ ] User-provided text is escaped.
- [ ] Print/PDF behavior included.
- [ ] README preview screenshots are generated from real demo HTML fixtures.
- [ ] Demo visuals are clearly labeled synthetic/example unless backed by verified source analysis.
- [ ] Screenshot file sizes are reasonable for README use.
- [ ] README install snippets include the new skill.
- [ ] TESTING.md includes render, no-data, security, and integration tests.

---

## Implementation Notes

- The report skill should make evidence easier to read, not easier to overclaim.
- The highest-value visualizations are simple: severity heatmaps, GRADE tables, SD/range bars, CI/MCID plots, and provenance tables.
- Prefer static SVG/CSS over canvas or chart libraries.
- Do not start a local dev server for static reports.
- Always include an "Evidence limitations" section. HTML polish must not hide uncertainty.
