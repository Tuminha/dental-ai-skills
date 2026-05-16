# Dental AI Skills — Project Instructions

## What This Repo Is

A collection of AI skills (structured markdown protocols) for dental professionals. Each skill is a `SKILL.md` file that gives AI models (Claude, GPT, etc.) specialized dental knowledge and output formats.

## Skills

| Skill | Folder | Purpose |
|-------|--------|---------|
| Research Critic | `research-critic/` | Single-paper appraisal (PICO, bias tools in native formats, dental-specific red flags, claim-to-evidence map, Study Credibility score). Single-paper, internal-credibility focused. |
| Clinical Evidence Reviewer | `clinical-evidence-reviewer/` | Body-of-evidence reviews with runtime-aware retrieval mode, PICO, GRADE certainty **per critical outcome**, guideline vs expert-consensus distinction, citation policy with uncertainty labels. |
| Dental Evidence Retriever | `dental-evidence-retriever/` | Literature-search workflow (PICO → PubMed/Cochrane/guideline-body/registry strategies → retrieval log). Honest about runtime — no fabricated citations. |
| Dental Content Creator | `dental-content-creator/` | Audience-aware dental content with platform adaptations and no-overclaim guardrails. |
| Dental Image Generator | `dental-image-generator/` | AI-generated clinical illustrations and patient visuals via Google Gemini. |

### Literature-skill workflow

```
Clinical question  →  dental-evidence-retriever  →  clinical-evidence-reviewer
                       (search strategy + log)        (GRADE per outcome, guidelines)

Single paper       →  research-critic
                       (Study Credibility — NOT a clinical recommendation by itself)
```

`research-critic` and `clinical-evidence-reviewer` hand off to each other automatically.

## Rules for Contributing

- Do not change the output schema of any skill without updating the README and TESTING.md.
- Every clinical claim in a skill's instructions must be defensible — no unsourced absolutes.
- Keep skills focused: one job per skill. Literature skills can exceed ~150 lines because the protocols are non-trivial, but they must still pass the "one job" test.
- **Citation honesty is non-negotiable.** Skills that demand citations must also branch on whether retrieval is actually possible in the runtime. No fabricated DOIs/PMIDs.
- **Bias-tool fidelity.** Use each tool's native judgment categories — do not force AMSTAR 2, Newcastle-Ottawa, QUADAS, JBI into RoB 2's "Low / Some concerns / High" labels.
- Run the manual tests in TESTING.md before pushing changes.
- Prefer minimal diffs and clear commit messages.
- Methodology updates (case definitions, appraisal tools, guideline-body URLs, GRADE handbook revisions) require updating the "Methodology Review Date" block at the bottom of the affected skill.
