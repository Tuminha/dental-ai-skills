# Dental AI Skills

**Structured AI protocols for dentists, researchers, and dental educators.**

Structured appraisal workflows for Claude and Codex, with worked examples and explicit evidence limits. Outputs still require clinical review.

**Start here:** [Journal Club Starter Kit](examples/journal-club-starter-kit.md) · [Paper Numbers Check](examples/paper-numbers-check.md) · [Author relationship review](dental-author-disclosures/)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What's Inside

| Skill | Who It's For | What It Does |
|-------|-------------|--------------|
| [**Dental Author Disclosures**](dental-author-disclosures/) | Researchers & journal clubs | Dated, sourced author relationship register; distinguishes disclosures, external evidence and uncertainty without inferring bias |
| [**Research Critic**](research-critic/) | Researchers & PhD students | Single-paper appraisal: PICO extraction → bias tool selection (RoB 2 incl. cluster and crossover variants; split-mouth via crossover logic plus paired-design checks; ROBINS-I, QUADAS-3, AMSTAR 2, Newcastle-Ottawa, JBI, ARRIVE+SYRCLE, CRIS) → dental red flags → claim-to-evidence map → Study Credibility score |
| [**Clinical Evidence Reviewer**](clinical-evidence-reviewer/) | Clinicians | Body-of-evidence reviews: runtime-aware retrieval mode, PICO, GRADE certainty **per critical outcome**, guideline-vs-consensus distinction, patient selection, "what's unknown" |
| [**Dental Evidence Retriever**](dental-evidence-retriever/) | Researchers, clinicians | Literature search workflow: PICO → PubMed/Cochrane/guideline-body/ClinicalTrials.gov/PROSPERO strategies → retrieval log. Honest about runtime — no fabricated citations |
| [**Dental Paper Fetch**](dental-paper-fetch/) | Researchers, clinicians, journal clubs | Gets the free full-text PDF and the figures of a paper by PMID, DOI, PMCID or title, from legal open-access sources only (PubMed Central, OpenAlex, Europe PMC, CORE, OpenAIRE, Semantic Scholar). Reports a paywalled paper with its link. No way around paywalls or bot checks |
| [**Dental Statistical Forensics**](dental-statistical-forensics/) | Researchers, reviewers | Deep numerical audit: SD/range, CIs, effect sizes, MCID, individual predictability, unit-of-analysis errors, clustering, multiplicity, missing data, model appropriateness, measurement reliability, and claim-to-number discipline |
| [**Dental Evidence Report Artifact**](dental-evidence-report-artifact/) | Educators, researchers | Turns completed critiques, evidence reviews, retrieval logs, and statistical audits into polished HTML/PDF-ready reports without adding new evidence claims |
| [**Dental Content Creator**](dental-content-creator/) | Educators & marketers | Audience-aware content with platform adaptations (LinkedIn/X/Instagram), no-overclaim guardrails, evidence-backed mode |
| [**Dental Image Generator**](dental-image-generator/) | Anyone creating visuals | AI clinical illustrations via OpenAI's Images API (paid, `gpt-image-2.5-sunburst` by default): surgical diagrams, patient infographics, branded content |

**Scientific-literature workflow.** The scientific workflow skills are designed to work together:

```
PMID, DOI or title → Get the full text: dental-paper-fetch → PDF and figures for the skills below
                      (free legal copies only; a paywalled paper is reported with its link)

Question → dental-evidence-retriever  →  body of evidence → clinical-evidence-reviewer
            (search strategy + log)                          (GRADE per outcome, guidelines, recommendations)
                                      ↘ numerical disputes → dental-statistical-forensics
                                        (effect size, SD/range, CI, MCID, model validity)

Single paper to appraise → research-critic → dental-statistical-forensics
                            (single-paper credibility)         (numbers and predictability audit)

Completed analysis → dental-evidence-report-artifact
                     (HTML/PDF-ready report, teaching handout, journal-club artifact)
```

`research-critic`, `clinical-evidence-reviewer`, `dental-evidence-retriever`, `dental-statistical-forensics`, and `dental-evidence-report-artifact` hand off to each other automatically when a question belongs in another layer of the workflow.

`research-critic`, `clinical-evidence-reviewer`, `dental-evidence-retriever`, `dental-statistical-forensics` and `dental-author-disclosures` read the full text, not the abstract. When the runtime can run scripts, they get the PDF with `dental-paper-fetch` first. Otherwise they ask for a PDF you may lawfully share. Their output states whether the full text, part of it or only the abstract was read.

![Iasella statistical forensics report preview](examples/assets/iasella-forensics-preview.svg)

---

## Installation

### Codex (Desktop or CLI)

Clone this repository, then copy the **whole folder** for each skill you want into
`~/.agents/skills/` (personal scope) or `<project>/.agents/skills/` (project scope).
Preserve any customised installation before replacing it. For a first skill:

```bash
git clone https://github.com/Tuminha/dental-ai-skills.git
mkdir -p ~/.agents/skills
cp -R dental-ai-skills/research-critic ~/.agents/skills/
```

Start a new Codex session and invoke `$research-critic`. Use the same folder-copy
pattern for `dental-author-disclosures` and the other skills. No API key is needed
for the instructions or offline number checks; browsing and image generation depend
on your host's tools. [Official Codex installation guidance](https://learn.chatgpt.com/docs/build-skills).

### Option A: Claude Desktop (Non-Technical)

1. **Download:** Click the green "Code" button above → "Download ZIP"
2. **Unzip** the folder anywhere on your computer
3. **Open a Claude conversation or project** and attach the instructions you need
4. Include the skill's supporting reference files for the task
5. Ask Claude to follow the named protocol and identify any unavailable resources
6. Use Claude Code for workflows requiring local scripts or a complete skill folder

> **Tip:** If Claude doesn't follow the protocol, start your prompt with: *"Following the Research Critic protocol, critique this study..."*

### Option B: Claude Code (Terminal)

Claude Code supports two install scopes:

| Scope | Path | Applies to |
|---|---|---|
| **Personal** | `~/.claude/skills/<skill-name>/SKILL.md` | All your projects |
| **Project** | `<project>/.claude/skills/<skill-name>/SKILL.md` | One project only |

```bash
# Clone the repo
git clone https://github.com/Tuminha/dental-ai-skills.git
cd dental-ai-skills

# Option 1 — Personal install (recommended; available everywhere)
mkdir -p ~/.claude/skills
cp -r research-critic ~/.claude/skills/
cp -r clinical-evidence-reviewer ~/.claude/skills/
cp -r dental-evidence-retriever ~/.claude/skills/
cp -r dental-statistical-forensics ~/.claude/skills/
cp -r dental-evidence-report-artifact ~/.claude/skills/
cp -r dental-author-disclosures ~/.claude/skills/
cp -r dental-paper-fetch ~/.claude/skills/
cp -r dental-content-creator ~/.claude/skills/
cp -r dental-image-generator ~/.claude/skills/

# Option 2 — Project install (scoped to one repo)
mkdir -p your-project/.claude/skills
cp -r research-critic your-project/.claude/skills/
cp -r clinical-evidence-reviewer your-project/.claude/skills/
cp -r dental-evidence-retriever your-project/.claude/skills/
cp -r dental-statistical-forensics your-project/.claude/skills/
cp -r dental-evidence-report-artifact your-project/.claude/skills/
cp -r dental-author-disclosures your-project/.claude/skills/
cp -r dental-paper-fetch your-project/.claude/skills/
cp -r dental-content-creator your-project/.claude/skills/
cp -r dental-image-generator your-project/.claude/skills/
```

For the scientific-literature workflow, install the first seven. `dental-paper-fetch`
runs a script: it needs Python 3.10 or newer and internet access.

Claude Code reads the YAML frontmatter and auto-loads each skill when its description matches your prompt. You can also invoke any skill directly: `/research-critic`, `/clinical-evidence-reviewer`, `/dental-evidence-retriever`, `/dental-statistical-forensics`, `/dental-evidence-report-artifact`, `/dental-author-disclosures`, `/dental-paper-fetch`.

### Option C: ChatGPT / claude.ai / Other AI Platforms

1. Open the `SKILL.md` file for the skill you want.
2. Copy the full contents.
3. In ChatGPT: attach the instructions and relevant reference files to a conversation or project; long skills may exceed the custom-instructions field.
4. In claude.ai: Projects → Custom Instructions → paste.
5. In other platforms: use whatever "custom instructions" or "system prompt" mechanism is available.

The skills are plain markdown — they work anywhere that accepts text instructions.

For skills with supporting resources, copy or upload the **full skill folder**, not only `SKILL.md`, whenever the platform allows it. This matters especially for `dental-statistical-forensics`, which depends on `dental-statistical-forensics/references/`, and for `dental-evidence-report-artifact`, which uses its `assets/` template and renderer script. If a platform only accepts one text prompt, paste `SKILL.md` plus the relevant reference files listed in the skill's "Reference Loading" or helper sections.

### Portability note: how the YAML frontmatter behaves across surfaces

| Surface | Frontmatter fields read | Network access | Notes |
|---|---|---|---|
| **Claude Code** | `name`, `description`, `when_to_use`, `effort`, `allowed-tools`, etc. (full Skills spec) | Full (via your machine) | Auto-discovery uses `description` + `when_to_use` to match prompts. `clinical-evidence-reviewer` and `dental-evidence-retriever` can perform real retrieval here. |
| **claude.ai (Projects)** | Skill body is read; frontmatter is generally ignored or absorbed as context | Browsing varies by plan | Skills still work because the body is self-sufficient. Retrieval may or may not be possible — the retrieval-mode block handles this. |
| **Claude API (Agent Skills)** | `name`, `description` (per the Agent Skills spec); other fields ignored | **No network by default** | Skills are pure instructions. `clinical-evidence-reviewer` will branch into "no live retrieval" mode and demand verified or labeled citations. |
| **ChatGPT custom instructions** | Frontmatter ignored — only the body matters | Browsing if enabled | Same as above; the body is self-sufficient. |

The skills are designed so the *body* is the contract. YAML frontmatter improves Claude Code ergonomics but is not required for the skill to work elsewhere.

### Option D: Image Generator (Requires Python and an OpenAI API key)

```bash
cd dental-image-generator
export OPENAI_API_KEY="your-key-from-platform.openai.com/api-keys"
python3 scripts/generate_dental_image.py --prompt "Your description" --style clinical --output image.png
```

The script uses only the Python standard library (Python 3.10 or newer), so there is nothing to install. The API is paid: OpenAI bills each image by output tokens. `--dry-run` prints the request without calling the API, and `--help` works without a key.

---

## Skills in Detail

### Research Critic

The peer reviewer you wish you had. Feed it a single paper and get:

- **Mandatory Phase 0 extraction first** — PICO, study classification (including randomization structure), unit of analysis, design essentials checklist — before any critique.
- **Source text record**: Phase 0 table 0D states whether the full text, part of it or only the abstract was read, where it came from, its license, and whether supplements were read.
- **Correct bias tool, in its native format**: auto-selects RoB 2 (incl. cluster and crossover variants; split-mouth via crossover logic plus paired-design checks), ROBINS-I, QUADAS-3 (preferred; QUADAS-2 only for legacy), AMSTAR 2 (using its native High/Moderate/Low/Critically Low confidence, not a fake score), Newcastle-Ottawa (star system), JBI, ARRIVE 2.0 + SYRCLE for animal, CRIS for in-vitro dental.
- **Unit-of-analysis audit** — patient / implant / tooth / site / surface levels, flags hierarchical-clustering mistakes.
- **Dental-specific red flags** — split-mouth clustering, success vs survival conflation, 2017 World Workshop definitions, short follow-up sold as long-term, implant-level vs patient-level mismatch, examiner calibration, radiographic standardization.
- **Statistical Forensics Triage** — forces SD/range, CI, MCID, individual-predictability, multiplicity, missing-data, and model-appropriateness checks before the paper's numerical claims are accepted.
- **Claim-to-evidence mapping** — checks every Discussion claim against the actual results.
- **Study Credibility score** (renamed from "Overall Evidence Quality"): 0–3 for each of five domains (Design, Methods, Statistics, Bias, Citations), total /15. Funding and relationships are reported, not scored. High credibility ≠ "strong evidence for clinical use"; that's a body-of-evidence question and hands off to `clinical-evidence-reviewer`.
- **Actionable output** — fatal flaws (up to 5, not forced), fixable issues, what would be needed to trust the study.

### Clinical Evidence Reviewer

Evidence-graded decision support, body-of-evidence and outcome-centric:

- **Evidence Retrieval Mode block** — declares runtime (Claude Code / claude.ai / API / unknown), whether live search is possible, what sources were searched. Prevents hallucinated citations in no-network runtimes.
- **Full text line**: the retrieval block states whether the full text of the key studies was obtained, and from which source.
- **PICO before synthesis** — pins population, intervention, comparator, outcomes, setting, time horizon.
- **GRADE certainty per critical outcome** — survival, marginal bone level change, biological complications, aesthetics (PES/WES), patient-reported, retreatment, adverse events. Not a single global rating.
- **Guideline-vs-consensus distinction** — evidence-based guidelines (EFP S3, ADA EBD) are reported with methodology + strength + certainty as stated by the guideline. Pure expert consensus stays at Level V.
- **Strict citation policy** — every clinical claim cites DOI/PMID/guideline document or carries an explicit uncertainty label.
- **Currency check** — ✅ Current / ⚠️ Aging / 🔴 Outdated. Older sources are not automatically outdated.
- **Patient selection, failure modes, what's unknown.**
- **Hand-off to `research-critic`** when the user asks a single-paper question, and to `dental-evidence-retriever` when the literature has not been searched yet.

### Dental Evidence Retriever

Literature-search workflow for dental clinical questions:

- **Runtime-honest** — declares whether live retrieval is possible and never fabricates results.
- **PICO → search strategy** for PubMed (MeSH + free-text), Cochrane CENTRAL, EFP/AAP/EAO/ITI/ADA/NICE/AAOMS guideline repositories, ClinicalTrials.gov, PROSPERO.
- **Retrieval log** — reproducible Boolean queries, date, result counts, per-source status — that `clinical-evidence-reviewer` can consume directly.
- **Full text line**: the Retrieval Mode block states whether the full text of the papers handed off was obtained, and from which source.
- **Citation validation helper** — `citation_validator.py` checks DOI/PMID syntax by default; syntax-valid does **not** mean citation-verified. Use `--check-network` or manual verification before publication or clinical teaching.
- **Hand-off** to `clinical-evidence-reviewer` (for grading), `research-critic` (for single-paper appraisal), and `dental-statistical-forensics` (for numerical audit).

### Dental Paper Fetch

Gets the paper, so the appraisal reads the full text:

- **Input**: a PMID, DOI, PMCID or title. `search` lists PubMed results, with citation counts from OpenAlex.
- **Legal open-access sources only**: the PubMed Central open-access bucket, OpenAlex locations, Europe PMC, CORE (with your own key), OpenAIRE and Semantic Scholar. No Sci-Hub or similar sites. No way around a paywall, CAPTCHA or bot check.
- **Clear result lines**: `SAVED`, `EXISTS`, `OPEN_MANUALLY`, `NO_FREE_COPY`, `NOT_FOUND`, then one count line per run with the saves per source. Exit code 2 means at least one paper was not saved, which is normal.
- **Measured coverage**: between 30 and 48 of every 100 periodontology and implant papers download automatically, in two samples of 100 and 40 papers; a fresh 100-paper run is still to do. Most of the rest are paywalled. The skill lists what to do then: your own library access, author-posted copies, a request to the authors that you write and send.
- **Figures**: each figure is saved with its caption and the paper's license. `reuse_hint` says whether an image model may use a figure as a reference.
- **Script**: `scripts/paper_fetch.py`, Python 3.10 or newer, standard library only. Files go to `PAPERS_DIR`, default `./papers`.

### Dental Statistical Forensics

The numbers reviewer. Use it when the mean looks good but the SD, CI, MCID, missing data, clustering, or model choice may change the interpretation:

- **Core numerical audit** — outcome type, unit of analysis, effect estimate, precision, dispersion, clinical threshold, individual predictability, sample size, missing data, multiplicity, model appropriateness, claim discipline.
- **Dispersion and predictability lens** — explicitly asks whether SD / IQR / range undermine claims like "predictable," "clinically reliable," or "maintains esthetics."
- **Clinical threshold discipline** — compares effect size against MCID, failure thresholds, and measurement error instead of accepting p-values alone.
- **Dental hierarchy checks** — patient / implant / tooth / site / surface / sinus / scan / histologic-field clustering.
- **Domain modules** — ridge preservation and esthetic zone, sinus lift, periodontal treatment, implant outcomes, diagnostic accuracy, digital dentistry, and meta-analysis.
- **Claim-to-number discipline** — separates average treatment effects from individual-patient reliability and flags overinterpretation.
- **Deterministic helper** — `scripts/stats_forensics_calculator.py` can compute screening CIs, SD/effect ratios, binary effect measures, and diagnostic likelihood ratios without third-party packages.

### Dental Evidence Report Artifact

Turns completed analysis into polished HTML/PDF-ready reports:

- **Separation of analysis and presentation** — formats completed outputs from `research-critic`, `clinical-evidence-reviewer`, `dental-evidence-retriever`, or `dental-statistical-forensics`; it does not invent evidence.
- **Standalone HTML template**: restrained clinical styling, metric cards, severity flags, sections, optional per-section tables (used for the author relationship register), and source tables.
- **Renderer script** — `scripts/render_evidence_report.py` converts compact JSON into an HTML report.
- **Example artifact** — see [`examples/iasella-statistical-forensics-report.html`](examples/iasella-statistical-forensics-report.html) and the source JSON in [`examples/iasella-statistical-forensics-report-data.json`](examples/iasella-statistical-forensics-report-data.json).

### Dental Content Creator

Content that sounds professional, not AI-generated:

- **Audience modes** — adjusts tone, depth, and jargon for GPs, specialists, students, patients, or industry
- **Evidence-backed mode** — clinical claims cite sources (default for professional audiences)
- **Full content bundle** — main piece + LinkedIn + X/Twitter + Instagram + 5 hooks + CTA variants
- **No-overclaim guardrails** — no absolute outcome claims, no unsourced brand comparisons, case-selection caveats required

### Dental Image Generator

AI-generated clinical visuals:

- **Three style presets** — clinical (textbook), patient-friendly (calming), infographic (modern)
- **Brand reference**: send your clinic's logo or brochure as an input image and the model matches its colours and style
- **Prompt cookbook** — tested prompts for surgical diagrams, patient handouts, social media graphics
- **OpenAI Images API** (`gpt-image-2.5-sunburst` by default): paid per image, standard-library script, no design skills needed

---

## Troubleshooting

**"The AI isn't following the skill protocol."**
Start your prompt with the skill name: *"Using the Research Critic protocol, analyze..."* If that doesn't help, check that the SKILL.md is loaded in your project (not just mentioned in the chat).

**"Output looks generic, not specialized."**
Make sure you're working inside the project/conversation where the skill is loaded. In Claude Desktop, conversations outside the project don't have access to project knowledge files.

**"It's citing studies that don't exist."**
AI models can hallucinate citations. The Clinical Evidence Reviewer requires an Evidence Retrieval Mode block at the top of every response so you can immediately tell whether the citations come from a live search or from recalled memory. If retrieval was not possible, the skill must label recalled DOIs/PMIDs as `[Recalled citation — verify before use]`. Always verify DOIs before clinical or publication use. Ask: *"Verify this citation — is it real?"*

**"Can I use more than one skill at once?"**
Yes. Add multiple SKILL.md files to the same project. The AI will use whichever is relevant to your prompt. For best results with multiple skills, name the one you want in your prompt.

**"How do I check that Claude Code can parse the skills?"**
Run the included validator from the repo root:

```bash
python3 scripts/validate_skills.py
```

It checks every `*/SKILL.md` for YAML frontmatter and required metadata.

For the full repo smoke test, including `agents/openai.yaml`, examples, fixtures, and helper scripts:

```bash
python3 scripts/smoke_test_repo.py
```

---

## Testing

See [TESTING.md](TESTING.md) for manual test prompts and structural checks for each skill. The `fixtures/` folder includes compact regression fixtures for high-SD / individual-predictability, split-mouth clustering, QUADAS-3 diagnostic accuracy, AMSTAR 2 native judgment, implant survival-vs-success, and periodontal site-level clustering.

---

## About

Created by **[Francisco Teixeira Barbosa](https://periospot.com)** — periodontist, dental tech enthusiast, and founder of [Periospot](https://periospot.com).

These skills are opinionated by design. They enforce structured extraction before judgment, require citations or uncertainty labels, and include dental-specific checks that generic AI prompts miss.

**Newsletter:** [The Periospot Brew](https://periospot.com) — weekly AI + dentistry insights.

## License

MIT — use these however you want. If they help your research or practice, a star is appreciated.

---

*Built by [Periospot](https://periospot.com)*
