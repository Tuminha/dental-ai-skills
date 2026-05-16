# Dental Statistical Forensics Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SOTA numerical-skepticism layer to the Dental AI Skills repo so papers and evidence reviews are audited for dispersion, effect size, uncertainty, unit-of-analysis errors, missing data, multiplicity, model choice, measurement reliability, and dental-domain clinical interpretability.

**Architecture:** Keep `research-critic` and `clinical-evidence-reviewer` as the main user-facing workflows, but add a companion `dental-statistical-forensics` skill for deep numerical review. `research-critic` gets a mandatory lightweight triage checkpoint; `clinical-evidence-reviewer` gets explicit hand-off language for effect-size, imprecision, and GRADE downgrading. The new skill uses progressive disclosure: a concise `SKILL.md` plus focused `references/` modules for deep domain-specific checks.

**Tech Stack:** Markdown Agent Skills (`SKILL.md`), YAML frontmatter, repo docs (`README.md`, `CLAUDE.md`, `TESTING.md`), optional pure-Python helper scripts for future deterministic calculations. No broad tool permissions.

---

## Status Check

Point 1 from the prior recommendation is already complete on `main`.

- Verified commit: `13a3a37 docs: align project-install snippet with all five skills (Codex review)`.
- Verified `README.md` now copies all five skills in both personal and project Claude Code install blocks.
- Keep this item as a no-op verification task in the implementation PR so the history is clear.

---

## Evidence And Standards To Respect

Use these as design anchors, not as long quoted content inside the skill:

- Cochrane Handbook, Chapter 6: effect measures, continuous outcomes, repeated observations, body-part/unit-of-analysis problems.
- Cochrane Handbook, Chapter 14: GRADE certainty of evidence assessed for each outcome.
- Cochrane Handbook, Chapter 15: interpretation and imprecision; continuous-outcome precision depends on variability/SD.
- ASA Statement on p-values: p-values do not measure effect size or clinical importance; conclusions should not rest only on threshold significance.
- CONSORT-Outcomes 2022: outcomes should specify domain, measurement variable, analysis metric, aggregation method, and time point.
- QUADAS-3: diagnostic accuracy appraisals assess risk of bias and applicability at the estimate level.

Do not turn the skill into a bibliography. Mention standards briefly where operationally useful, and keep the working checklist concise.

---

## File Structure

Create:

- `dental-statistical-forensics/SKILL.md`
  - Thin spine: identity, trigger scope, mandatory output blocks, when to load each reference module, output format, and methodology review date.
- `dental-statistical-forensics/references/core-numerical-audit.md`
  - Core checklist: outcome type, unit of analysis, effect estimate, CI/SE/p-value discipline, dispersion, MCID/clinical thresholds, individual predictability, missing data, multiplicity, model appropriateness, measurement error, claim discipline.
- `dental-statistical-forensics/references/effect-measure-guide.md`
  - How to translate common dental outcomes into effect measures: continuous mm outcomes, binary events, time-to-event, diagnostic accuracy, agreement/reliability, digital accuracy, meta-analysis.
- `dental-statistical-forensics/references/dental-domain-modules.md`
  - Dental modules: esthetic zone/ridge preservation, sinus lift/grafting, periodontal site-level outcomes, implant survival/success/marginal bone loss, diagnostic accuracy, digital dentistry, meta-analysis.
- `dental-statistical-forensics/references/clinical-thresholds-and-mcid.md`
  - Practical thresholds and caveats. Must distinguish well-established MCIDs from contextual or approximate thresholds. Do not invent universal thresholds.
- Optional later: `dental-statistical-forensics/scripts/stat_forensics_calculator.py`
  - Deterministic helper for approximate CI, SE, SD/effect ratio, coefficient of variation, risk difference, NNT/NNH, and simple normal-approximation threshold-crossing estimates.

Modify:

- `research-critic/SKILL.md`
  - Add mandatory Statistical Forensics Triage.
  - Add hand-off to `dental-statistical-forensics`.
  - Expand output format with a triage section.
- `clinical-evidence-reviewer/SKILL.md`
  - Add hand-off/use language for `dental-statistical-forensics` when interpreting effect sizes, CIs, MCID, imprecision, heterogeneity/dispersion, and GRADE downgrades.
- `dental-evidence-retriever/SKILL.md`
  - Optional small hand-off note: retrieval logs can feed both `clinical-evidence-reviewer` and `dental-statistical-forensics`.
- `README.md`
  - Add the new skill to the skill table, workflow diagram, installation snippets, portability notes, and skill detail section.
- `CLAUDE.md`
  - Add the new skill and statistical-fidelity contributing rules.
- `TESTING.md`
  - Add manual tests for numerical traps and integration behavior.

No changes needed:

- `dental-content-creator/SKILL.md`
- `dental-image-generator/SKILL.md`
- `LICENSE`

---

## Chunk 1: Planning And Branch Hygiene

### Task 1: Verify The Merged Baseline

**Files:**
- Inspect: `README.md`
- Inspect: `git log`

- [ ] **Step 1: Fetch latest main**

Run:

```bash
git fetch origin
git checkout main
git pull --ff-only
```

Expected: branch is up to date with `origin/main`.

- [ ] **Step 2: Verify install snippet includes all five skills**

Run:

```bash
sed -n '48,92p' README.md
```

Expected: both personal and project install blocks include `research-critic`, `clinical-evidence-reviewer`, `dental-evidence-retriever`, `dental-content-creator`, and `dental-image-generator`.

- [ ] **Step 3: Create implementation branch**

Run:

```bash
git checkout -b feat/dental-statistical-forensics
```

Expected: new branch created from current `main`.

---

## Chunk 2: New Skill Skeleton

### Task 2: Create `dental-statistical-forensics/SKILL.md`

**Files:**
- Create: `dental-statistical-forensics/SKILL.md`
- Create directory: `dental-statistical-forensics/references/`

- [ ] **Step 1: Add frontmatter**

Use this pattern:

```markdown
---
name: dental-statistical-forensics
description: Use when the user asks for a deep statistical or numerical audit of a dental/oral-health study, paper, abstract, systematic review, or evidence table. Use for standard deviations, confidence intervals, effect sizes, MCID, prediction/individual-patient variability, p-values, multiplicity, missing data, unit-of-analysis errors, clustered dental data, model appropriateness, survival analysis, diagnostic accuracy, meta-analysis statistics, and clinical interpretation of numbers.
when_to_use: User asks about SD, CI, dispersion, p-values, statistical tests, effect size, imprecision, MCID, clinical significance, patient-level predictability, multiple comparisons, missing data, clustering, split-mouth analysis, implant/site/tooth-level analysis, survival vs success, diagnostic accuracy statistics, or whether the numbers support the authors' conclusion.
effort: high
---
```

Keep combined `description` + `when_to_use` under the Claude Code 1,536-character cap.

- [ ] **Step 2: Add identity and scope**

State:

```markdown
# Dental Statistical Forensics

You are a skeptical biostatistician and dental research methodologist. Your job is to audit numerical results, not summarize the paper. You test whether the conclusion still holds after inspecting effect size, SD/range/IQR, confidence intervals, MCID, missing data, unit of analysis, clustering, model choice, multiplicity, measurement reliability, and domain-specific clinical thresholds.

Scope: This skill performs deep numerical review. It complements `research-critic` and `clinical-evidence-reviewer`; it does not replace full risk-of-bias appraisal or body-of-evidence grading.
```

- [ ] **Step 3: Add mandatory workflow**

Include mandatory sections:

1. Data extraction status.
2. Outcome classification.
3. Core numerical audit.
4. Dental-domain module selection.
5. Statistical red flags.
6. Clinical interpretability.
7. Claim-to-number discipline.
8. Bottom line.

- [ ] **Step 4: Add reference-loading rules**

Add:

```markdown
Load references only as needed:
- Always use `references/core-numerical-audit.md`.
- Use `references/effect-measure-guide.md` when the outcome type or effect measure is unclear.
- Use `references/dental-domain-modules.md` for domain-specific checks.
- Use `references/clinical-thresholds-and-mcid.md` when judging clinical thresholds or MCID.
```

- [ ] **Step 5: Add output format**

Required output:

```markdown
## Statistical Forensics Verdict
## Data Extracted
## Outcome And Effect-Measure Map
## Dispersion And Individual Predictability
## Precision And Clinical Thresholds
## Unit-of-Analysis / Model Audit
## Missing Data And Multiplicity
## Measurement Reliability
## Dental-Domain Module Findings
## Claims The Numbers Do Not Support
## Bottom Line
```

- [ ] **Step 6: Add Methodology Review Date**

Use:

```markdown
## Methodology Review Date

**Last methodology review:** 2026-05-16

Re-review this skill when Cochrane guidance, GRADE guidance, CONSORT-Outcomes, ASA p-value guidance, diagnostic accuracy guidance, or major dental outcome thresholds change.
```

- [ ] **Step 7: Validate frontmatter and length**

Run:

```bash
ruby -ryaml -e 'ARGV.each { |p| t=File.read(p); fm=t.split(/^---\s*$/,3)[1]; y=YAML.safe_load(fm); puts [p, y["name"], ((y["description"]||"")+(y["when_to_use"]||"")).length, t.lines.count].join(" | ") }' dental-statistical-forensics/SKILL.md
```

Expected: valid YAML, name `dental-statistical-forensics`, combined trigger text under 1,536 characters.

---

## Chunk 3: Core Numerical Audit Reference

### Task 3: Create `references/core-numerical-audit.md`

**Files:**
- Create: `dental-statistical-forensics/references/core-numerical-audit.md`

- [ ] **Step 1: Add the mandatory 12-point triage**

Include exactly these checks:

1. Outcome type: continuous, binary, ordinal, count/rate, time-to-event, diagnostic, agreement/reliability, digital accuracy, meta-analytic.
2. Unit of analysis: patient, implant, tooth, site, surface, sinus, scan, specimen, histologic field.
3. Effect estimate: mean difference, standardized mean difference, risk ratio, odds ratio, risk difference, hazard ratio, sensitivity/specificity, likelihood ratio, ICC, Bland-Altman limits, RMS/angular deviation.
4. Precision: 95% CI, SE, p-value, width of interval, whether CI crosses null and clinical thresholds.
5. Dispersion: SD, IQR, range, coefficient of variation, SD/effect ratio, SD/MCID ratio.
6. Clinical threshold: MCID or domain-specific failure/success threshold; state when threshold is contextual or not established.
7. Individual predictability: whether SD/range suggests many patients/sites may cross an unacceptable clinical threshold despite favorable mean.
8. Sample size and power: planned vs achieved n, assumptions, smallest detectable difference, underpowered secondary outcomes.
9. Missing data: amount, reasons, balance, informative missingness, ITT/per-protocol/as-treated, sensitivity analyses.
10. Multiplicity: number of outcomes, time points, subgroups, interim looks, unadjusted p-values, prespecified primary outcome.
11. Model appropriateness: paired vs unpaired, clustered, repeated measures, regression/ANCOVA, survival model, diagnostic model, meta-analysis model.
12. Claim discipline: whether the authors' conclusions match magnitude, precision, dispersion, missingness, model, and clinical relevance.

- [ ] **Step 2: Add severity rules**

Use:

```markdown
Severity:
- Critical: likely changes the direction/trustworthiness of the conclusion.
- Moderate: materially weakens interpretation but does not fully invalidate.
- Minor: reporting or interpretation issue with limited impact.
```

- [ ] **Step 3: Add SD/dispersion red-flag rules**

Include:

- SD greater than mean effect or greater than domain MCID.
- Wide range including clinically unacceptable failures.
- Mean benefit smaller than plausible measurement error.
- No range/IQR/individual plot despite claims of predictability.
- "Predictable" language based only on mean difference.

- [ ] **Step 4: Add precision rules**

Include:

- CI absent for primary continuous/binary/time-to-event outcomes.
- CI crosses null.
- CI does not cross null but crosses clinically unimportant or clinically harmful threshold.
- Non-significant result interpreted as no effect.
- Significant result interpreted as clinically important without effect size.

- [ ] **Step 5: Add missing-data rules**

Include:

- Missingness related to poor outcome is Critical.
- Excluding failed sites/implants/cores from final analysis is Critical unless handled transparently.
- Per-protocol-only analysis after attrition is at least Moderate.

---

## Chunk 4: Effect-Measure Guide

### Task 4: Create `references/effect-measure-guide.md`

**Files:**
- Create: `dental-statistical-forensics/references/effect-measure-guide.md`

- [ ] **Step 1: Add data-type-to-effect-measure map**

Create a table:

| Outcome type | Dental examples | Preferred effect measures | Common traps |
|---|---|---|---|
| Continuous mm | ridge width, MBL, PD, CAL, KT width | mean difference, CI, SD, range, MCID comparison | p-value without CI; SD ignored |
| Binary | implant failure, membrane perforation, pocket closure yes/no | risk difference, RR, OR, NNT/NNH | OR overinterpreted as RR |
| Time-to-event | implant survival over loading time | Kaplan-Meier, HR, censoring table | survival vs success conflated |
| Diagnostic | CBCT diagnosis, peri-implantitis test | sensitivity, specificity, LR+/LR-, PPV/NPV with prevalence, AUC | no CI; spectrum bias |
| Agreement/reliability | examiner calibration, scan agreement | ICC, kappa, Bland-Altman limits | correlation mistaken for agreement |
| Digital accuracy | scan trueness/precision | RMS, mean/median deviation, angular deviation, precision SD | color-map overinterpretation |
| Meta-analysis | pooled MD/RR/OR | random/fixed effect, heterogeneity, prediction interval | pooling incompatible designs |

- [ ] **Step 2: Add approximation boundaries**

State:

- The skill may estimate approximate CIs from summary statistics when formulas are straightforward and assumptions are stated.
- The skill must label all approximations as approximate.
- Do not compute exact claims when required data are absent.
- Do not invent sample sizes, SDs, event counts, or correlation coefficients.

- [ ] **Step 3: Add Iasella-style example pattern without overfitting**

Add a generic example:

```markdown
If mean vertical change is +1.3 mm with SD 2.0 mm and range -2.0 to +4.5 mm, do not write "predictable maintenance." Write: "Average effect is favorable, but individual-site variability is large; some treated sites still had clinically relevant loss."
```

---

## Chunk 5: Dental Domain Modules

### Task 5: Create `references/dental-domain-modules.md`

**Files:**
- Create: `dental-statistical-forensics/references/dental-domain-modules.md`

- [ ] **Step 1: Add esthetic-zone / ridge-preservation module**

Checks:

- Horizontal ridge-width loss.
- Mid-buccal and interproximal vertical changes.
- Buccal contour / facial wall failure.
- Soft tissue thickness and midfacial recession.
- PES/WES or esthetic acceptability where reported.
- Need for additional GBR/CTG/staged augmentation.
- Proportion crossing failure thresholds.
- Mean benefit with high SD/range.
- Claims of "predictability" unsupported by individual data.

- [ ] **Step 2: Add sinus lift / grafting module**

Checks:

- Residual bone height baseline balance.
- Vertical bone gain and graft shrinkage/remodeling.
- Membrane perforation and complication rates per patient/sinus.
- Implant survival vs implant success.
- Follow-up after loading, not only after placement.
- Bilateral sinus or multiple implant clustering.
- Histology/core missingness and graft-material remnants.

- [ ] **Step 3: Add periodontal treatment module**

Checks:

- Probing-depth reduction, CAL gain, pocket closure, BOP.
- Patient/tooth/site-level clustering.
- Full-mouth vs selected-site reporting.
- Maintenance interval and adherence.
- Smoking/diabetes stratification.
- Mean PD/CAL change vs proportion reaching pocket closure.
- Examiner calibration and probing measurement error.

- [ ] **Step 4: Add implant outcomes module**

Checks:

- Survival vs success.
- Patient-level vs implant-level reporting.
- Marginal bone loss mean/SD/range.
- Biological and technical complications.
- Time under loading.
- Dropouts and censored implants.
- Multiple implants per patient/operator/center.
- Industry-sponsored device outcome claims.

- [ ] **Step 5: Add digital dentistry module**

Checks:

- Trueness vs precision.
- RMS and angular deviation.
- Full-arch vs short-span indirectness.
- Scan body position and scan path.
- Repeated scans clustered by model/patient/operator.
- In-vitro vs in-vivo indirectness.
- Color-map overinterpretation.

- [ ] **Step 6: Add diagnostic accuracy module**

Checks:

- Sensitivity/specificity with CI.
- Threshold predefinition.
- ROC/AUC interpretation.
- Reference-standard quality.
- Prevalence effects on PPV/NPV.
- Indeterminate results.
- Estimate-level QUADAS-3 thinking.
- Patient/site/tooth/surface diagnostic-unit mismatch.

- [ ] **Step 7: Add meta-analysis module**

Checks:

- Pooling compatible designs/outcomes/time points.
- Random-effects vs fixed-effect rationale.
- Heterogeneity and prediction intervals.
- Small-study/publication bias.
- Subgroup/meta-regression overreach.
- Unit-of-analysis overlap across included studies.
- SMD interpretability and back-translation to clinical units.

---

## Chunk 6: Clinical Thresholds And MCID Reference

### Task 6: Create `references/clinical-thresholds-and-mcid.md`

**Files:**
- Create: `dental-statistical-forensics/references/clinical-thresholds-and-mcid.md`

- [ ] **Step 1: Add threshold policy**

State:

- Prefer validated MCIDs or guideline-defined thresholds.
- If no validated MCID exists, use clinically plausible thresholds only as contextual benchmarks.
- Always label contextual thresholds as contextual, not universal.
- Always compare effect magnitude to measurement error when measurement error is reported or inferable.

- [ ] **Step 2: Add domain examples with caveats**

Examples:

- Ridge preservation: 1-2 mm facial/buccal change may be clinically important in esthetic-zone planning, but threshold depends on baseline anatomy and planned augmentation.
- Marginal bone level: small differences may be statistically detectable but clinically uncertain; interpret with follow-up duration and measurement error.
- Periodontal PD/CAL: mean changes should be interpreted alongside pocket closure and BOP, not alone.
- Implant outcomes: survival alone is insufficient for success; biological/technical complications matter.
- Diagnostic accuracy: PPV/NPV depend on prevalence; sensitivity/specificity require CI.
- Digital accuracy: clinical relevance depends on span length, prosthetic tolerance, and in-vivo/in-vitro setting.

- [ ] **Step 3: Add "do not overclaim thresholds" rule**

Add:

```markdown
If the threshold is not established for the exact domain, write "clinical threshold not firmly established" and use the benchmark only for sensitivity-style interpretation.
```

---

## Chunk 7: Research Critic Integration

### Task 7: Add Mandatory Statistical Forensics Triage To `research-critic`

**Files:**
- Modify: `research-critic/SKILL.md`

- [ ] **Step 1: Insert triage after current Statistics section**

Add:

```markdown
## Phase 4B: Statistical Forensics Triage (Mandatory for Quantitative Papers)

For every quantitative paper, extract and assess:
1. Outcome type.
2. Unit of analysis.
3. Effect estimate.
4. Precision (95% CI/SE/p-value; estimate only if data are sufficient).
5. Dispersion (SD/IQR/range; SD/effect and SD/clinical-threshold concern).
6. Clinical threshold or MCID.
7. Individual predictability.
8. Sample size and power assumptions.
9. Missing data and likely direction of bias.
10. Multiplicity.
11. Model appropriateness.
12. Claim discipline.

If any item is complex, unclear, or central to the conclusion, hand off to `dental-statistical-forensics`.
```

- [ ] **Step 2: Add explicit SD/predictability red flag**

In Dental-Specific Red Flags or Statistical Review, add:

```markdown
High dispersion / limited individual predictability: mean benefit is clinically attractive, but SD/IQR/range is large relative to the mean effect or clinical threshold. This supports average treatment effect, not predictable individual-patient outcome.
```

- [ ] **Step 3: Update output format**

Add:

```markdown
## Statistical Forensics Triage
[Outcome map, dispersion/predictability, precision/CI, unit/model issues, missing data, multiplicity, and whether deep hand-off is needed]
```

- [ ] **Step 4: Update hand-off section**

Add:

```markdown
Use `dental-statistical-forensics` when the user asks whether the numbers support the conclusion, when SD/range/CI/MCID are central, or when the statistical model may be wrong.
```

- [ ] **Step 5: Validate no old overclaiming reappears**

Run:

```bash
rg -n "Strong evidence|suitable for informing clinical decisions|Overall Evidence Quality|Top 5 Fatal" research-critic/SKILL.md
```

Expected: no matches except explicit negative/testing references if any.

---

## Chunk 8: Clinical Evidence Reviewer Integration

### Task 8: Add Statistical-Forensics Hand-Off To `clinical-evidence-reviewer`

**Files:**
- Modify: `clinical-evidence-reviewer/SKILL.md`

- [ ] **Step 1: Add numerical audit rule under GRADE**

Add:

```markdown
When judging effect size, imprecision, MCID, heterogeneity, dispersion, or clinical relevance, use `dental-statistical-forensics` if the numerical interpretation is central to the recommendation or unclear from the evidence table.
```

- [ ] **Step 2: Expand GRADE table instructions**

For each outcome, require:

- effect estimate with CI if available;
- clinical threshold/MCID if established;
- whether CI crosses clinical threshold;
- whether dispersion or prediction interval limits patient-level predictability where applicable.

- [ ] **Step 3: Add hand-off trigger**

In Hand-Off Logic, add:

```markdown
Hand off to `dental-statistical-forensics` when the user asks about SD, CI, effect size, MCID, p-values, model choice, missing data, multiplicity, or whether a numerical result is clinically meaningful.
```

- [ ] **Step 4: Preserve retrieval honesty**

Run:

```bash
rg -n "Evidence Retrieval Mode|Recalled citation|GRADE by Critical Outcome|dental-statistical-forensics" clinical-evidence-reviewer/SKILL.md
```

Expected: all relevant concepts present.

---

## Chunk 9: Dental Evidence Retriever Link

### Task 9: Add A Small Retriever Hand-Off Note

**Files:**
- Modify: `dental-evidence-retriever/SKILL.md`

- [ ] **Step 1: Update hand-off section**

Add:

```markdown
If the user wants numerical extraction or statistical interpretation from retrieved papers, hand off to `dental-statistical-forensics` after retrieval.
```

- [ ] **Step 2: Keep scope narrow**

Do not make `dental-evidence-retriever` perform statistical audit. It only retrieves/searches.

---

## Chunk 10: README And Project Docs

### Task 10: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add new skill to "What's Inside"**

Add a row:

```markdown
| [**Dental Statistical Forensics**](dental-statistical-forensics/) | Researchers, clinicians, reviewers | Deep numerical audit: SD/range, CIs, effect sizes, MCID, unit-of-analysis errors, clustering, multiplicity, missing data, model fit, measurement reliability, and clinical interpretation of numbers |
```

- [ ] **Step 2: Update workflow diagram**

Add:

```markdown
Single paper -> research-critic -> dental-statistical-forensics when numbers drive the conclusion
Clinical question -> dental-evidence-retriever -> clinical-evidence-reviewer -> dental-statistical-forensics for effect-size/imprecision/MCID disputes
```

- [ ] **Step 3: Update install snippets**

Add `cp -r dental-statistical-forensics ...` to both personal and project install examples.

- [ ] **Step 4: Add skill detail section**

Include concise bullets:

- SD/range/individual predictability.
- CI and MCID discipline.
- Unit-of-analysis and clustered dental data.
- Missing data and multiplicity.
- Domain modules.
- Works with `research-critic` and `clinical-evidence-reviewer`.

### Task 11: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add skill row**

Add `Dental Statistical Forensics`.

- [ ] **Step 2: Add contributing rule**

Add:

```markdown
- Numerical claims must distinguish statistical significance, effect magnitude, precision, dispersion, and clinical relevance.
- Do not claim predictability from a favorable mean without checking SD/range/individual outcome distribution.
```

---

## Chunk 11: Manual Tests

### Task 12: Expand TESTING.md

**Files:**
- Modify: `TESTING.md`

- [ ] **Step 1: Add Dental Statistical Forensics section**

Add tests:

1. High SD relative to mean in ridge preservation.
2. CI crosses null or clinical threshold.
3. P-value without effect size/CI.
4. Missing histology/core data related to poor outcome.
5. Multiple outcomes/time points without adjustment.
6. Implant-level analysis with multiple implants per patient.
7. Survival vs success overclaim.
8. Diagnostic sensitivity/specificity without CI.
9. Digital trueness vs precision confusion.
10. Meta-analysis pooling incompatible designs/outcomes.

- [ ] **Step 2: Add integration tests**

Add tests:

- `research-critic` triggers Statistical Forensics Triage.
- `research-critic` hands off to `dental-statistical-forensics` when SD/range dominate interpretation.
- `clinical-evidence-reviewer` hands off when GRADE imprecision/MCID/effect-size interpretation is disputed.
- `dental-evidence-retriever` routes numerical extraction to `dental-statistical-forensics`.

- [ ] **Step 3: Add expected checklist details for the Iasella-style SD case**

Prompt:

```text
Audit these ridge-preservation results: RP horizontal change -1.2 ± 0.9 mm, EXT -2.6 ± 2.3 mm, RP mid-buccal vertical +1.3 ± 2.0 mm range -2.0 to +4.5 mm, EXT -0.9 ± 1.6 mm. Authors claim predictable maintenance in the esthetic zone.
```

Expected:

- Mean benefit acknowledged.
- SD/range flagged as limiting individual predictability.
- "Predictable maintenance" weakened.
- CIs requested or approximated only if n is supplied.
- No clinical recommendation from this numerical audit alone.

---

## Chunk 12: Optional Calculator Script

### Task 13: Decide Whether To Add A Calculator In This PR

**Files:**
- Optional create: `dental-statistical-forensics/scripts/stat_forensics_calculator.py`

- [ ] **Step 1: Make the scope decision**

Default for first implementation PR: do **not** add a script unless the skill behavior repeatedly requires exact arithmetic.

Reason: the repo is currently instruction-first, and PR #1 deliberately avoided broad tool/script scope.

- [ ] **Step 2: If adding script, keep it deterministic and narrow**

Allowed calculations:

- SE from SD/n.
- approximate CI for independent mean difference.
- SD/effect ratio.
- coefficient of variation where meaningful.
- absolute risk difference.
- NNT/NNH from risk difference.
- simple normal-approximation proportion crossing threshold, clearly labeled as assumption-dependent.

Must not:

- Infer paired correlation unless provided.
- Claim exact prediction intervals without required data.
- Make clinical decisions.
- Fetch web sources.

- [ ] **Step 3: Add script tests if script exists**

If a script is added, create simple self-tests or documented examples. Otherwise, skip.

---

## Chunk 13: Validation

### Task 14: Static Validation

**Files:**
- All created/modified files.

- [ ] **Step 1: Validate frontmatter for all native skills**

Run:

```bash
ruby -ryaml -e 'ARGV.each { |p| t=File.read(p); next unless t.start_with?("---\n"); fm=t.split(/^---\s*$/,3)[1]; y=YAML.safe_load(fm); len=((y["description"]||"")+(y["when_to_use"]||"")).length; puts [p, y["name"], len, t.lines.count].join(" | ") }' */SKILL.md
```

Expected: all frontmatter-bearing skills parse; `dental-statistical-forensics` trigger text under 1,536 characters.

- [ ] **Step 2: Check references are linked**

Run:

```bash
rg -n "core-numerical-audit|effect-measure-guide|dental-domain-modules|clinical-thresholds-and-mcid" dental-statistical-forensics/SKILL.md
```

Expected: all reference files are discoverable from `SKILL.md`.

- [ ] **Step 3: Check no broad tool permissions**

Run:

```bash
rg -n "allowed-tools|allowed_tools" dental-statistical-forensics research-critic clinical-evidence-reviewer dental-evidence-retriever
```

Expected: no matches unless deliberately justified in PR body.

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

### Task 15: Manual Behavior Tests

**Files:**
- Use: `TESTING.md`

- [ ] **Step 1: Run the high-SD ridge-preservation test**

Expected: the skill flags dispersion and weakens predictability claims.

- [ ] **Step 2: Run the unit-of-analysis test**

Expected: multiple implants/sites per patient flagged as clustering problem.

- [ ] **Step 3: Run the clinical-evidence hand-off test**

Expected: `clinical-evidence-reviewer` uses or hands off to `dental-statistical-forensics` for disputed effect-size/MCID interpretation.

- [ ] **Step 4: Run the research-critic integration test**

Expected: `research-critic` includes Statistical Forensics Triage in quantitative paper critique.

---

## Chunk 14: Commit And PR

### Task 16: Commit The Implementation

**Files:**
- All created/modified files.

- [ ] **Step 1: Review diff**

Run:

```bash
git diff --stat
git diff --check
```

Expected: no whitespace errors; diff matches plan scope.

- [ ] **Step 2: Commit**

Run:

```bash
git add dental-statistical-forensics research-critic/SKILL.md clinical-evidence-reviewer/SKILL.md dental-evidence-retriever/SKILL.md README.md CLAUDE.md TESTING.md
git commit -m "feat: add dental statistical forensics skill"
```

Expected: commit created.

- [ ] **Step 3: Push**

Run:

```bash
git push -u origin feat/dental-statistical-forensics
```

Expected: branch pushed.

- [ ] **Step 4: Open PR**

Run:

```bash
gh pr create \
  --title "Add dental statistical forensics skill" \
  --body-file /tmp/dental-statistical-forensics-pr.md
```

PR body should include:

- Summary of new skill.
- Integration points.
- Why SD/dispersion and individual predictability matter.
- Validation commands run.
- Manual tests still needed.
- Note whether optional calculator script was included or deferred.

---

## Suggested PR Review Checklist

- [ ] New skill has valid YAML frontmatter and concise trigger text.
- [ ] `SKILL.md` stays as a thin spine; deep details live in references.
- [ ] Research Critic triage catches SD/range/CI/MCID/unit-of-analysis/missing-data/multiplicity issues.
- [ ] Clinical Evidence Reviewer uses the skill for GRADE imprecision and clinical relevance disputes.
- [ ] README install snippets include the new skill in both personal and project blocks.
- [ ] TESTING.md includes high-SD, CI, unit-of-analysis, multiplicity, missing-data, diagnostic, survival, digital, and integration tests.
- [ ] No broad `allowed-tools` permissions added.
- [ ] No universal MCID/threshold claims where evidence is contextual.

---

## Implementation Notes

- Do not let this become a generic statistics textbook. It is a forensic dental-review workflow.
- The key behavioral win is not "more statistics"; it is forcing the model to ask whether the mean result survives dispersion, precision, clinical thresholds, and individual-patient variability.
- Treat "predictable" as a claim that requires SD/range/individual-data support.
- Treat "clinically significant" as a claim that requires effect-size plus threshold/MCID plus measurement-error context.
- Treat "statistically significant" as insufficient without effect magnitude and uncertainty.
