# Dental AI Skills — Project Instructions

## What This Repo Is

A collection of AI skills (structured markdown protocols) for dental professionals. Each skill is a `SKILL.md` file that gives AI models (Claude, GPT, etc.) specialized dental knowledge and output formats.

## Skills

| Skill | Folder | Purpose |
|-------|--------|---------|
| Research Critic | `research-critic/` | Structured critique of dental research papers (PICO extraction, bias assessment, claim-to-evidence mapping) |
| Clinical Evidence Reviewer | `clinical-evidence-reviewer/` | Evidence-graded treatment recommendations with GRADE certainty, citations, and uncertainty labeling |
| Dental Content Creator | `dental-content-creator/` | Audience-aware dental content with platform adaptations and no-overclaim guardrails |
| Dental Image Generator | `dental-image-generator/` | AI-generated clinical illustrations and patient visuals via Google Gemini |

## Rules for Contributing

- Do not change the output schema of any skill without updating the README and TESTING.md
- Every clinical claim in a skill's instructions must be defensible — no unsourced absolutes
- Keep skills focused: one job per skill. If a skill grows beyond ~150 lines, consider splitting it.
- Run the manual tests in TESTING.md before pushing changes
- Prefer minimal diffs and clear commit messages
