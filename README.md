# Dental AI Skills

**Structured AI protocols for dentists, researchers, and dental educators.**

Drop these into Claude Desktop, Claude Code, ChatGPT, or any AI that accepts custom instructions — and get specialist-level output instead of generic responses.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What's Inside

| Skill | Who It's For | What It Does |
|-------|-------------|--------------|
| [**Research Critic**](research-critic/) | Researchers & PhD students | Structured paper critique: PICO extraction → bias tool selection (RoB 2/ROBINS-I/AMSTAR 2) → dental red flags → claim-to-evidence mapping → scored assessment |
| [**Clinical Evidence Reviewer**](clinical-evidence-reviewer/) | Clinicians | Evidence-graded treatment reviews: GRADE certainty, mandatory citations, patient selection, "what's unknown" sections |
| [**Dental Content Creator**](dental-content-creator/) | Educators & marketers | Audience-aware content with platform adaptations (LinkedIn/X/Instagram), no-overclaim guardrails, evidence-backed mode |
| [**Dental Image Generator**](dental-image-generator/) | Anyone creating visuals | AI clinical illustrations via Google Gemini — surgical diagrams, patient infographics, branded content |

---

## Installation

### Option A: Claude Desktop (Non-Technical)

1. **Download:** Click the green "Code" button above → "Download ZIP"
2. **Unzip** the folder anywhere on your computer
3. **Open Claude Desktop** → Settings (gear icon) → Projects
4. **Create a new project** called "Dental AI Skills"
5. **Add the `SKILL.md` files** from the skill folders you want to use
6. **Start a conversation** inside that project — done!

> **Tip:** If Claude doesn't follow the protocol, start your prompt with: *"Following the Research Critic protocol, critique this study..."*

### Option B: Claude Code (Terminal)

```bash
# Clone the repo
git clone https://github.com/Tuminha/dental-ai-skills.git

# Copy skills to your Claude Code project
cp -r dental-ai-skills/research-critic/ your-project/.claude/skills/
cp -r dental-ai-skills/clinical-evidence-reviewer/ your-project/.claude/skills/
cp -r dental-ai-skills/dental-content-creator/ your-project/.claude/skills/
cp -r dental-ai-skills/dental-image-generator/ your-project/.claude/skills/
```

Skills in `.claude/skills/` are automatically available as project context in Claude Code.

### Option C: ChatGPT / Other AI Platforms

1. Open the `SKILL.md` file for the skill you want
2. Copy the full contents
3. In ChatGPT: Settings → Personalization → Custom Instructions → paste
4. In other platforms: use whatever "custom instructions" or "system prompt" mechanism is available

The skills are plain markdown — they work anywhere that accepts text instructions.

### Option D: Image Generator (Requires Python)

```bash
cd dental-image-generator
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-from-aistudio.google.com/apikey"
python scripts/generate_dental_image.py --prompt "Your description" --style clinical --output image.png
```

---

## Skills in Detail

### Research Critic

The peer reviewer you wish you had. Feed it a paper and get:

- **Mandatory extraction first** — PICO, study classification, and design essentials before any critique
- **Correct bias tool** — automatically selects RoB 2, ROBINS-I, QUADAS-2, AMSTAR 2, or Newcastle-Ottawa based on study type
- **Dental-specific red flags** — split-mouth clustering, success vs survival conflation, short follow-up, implant-level vs patient-level mismatch
- **Claim-to-evidence mapping** — checks if conclusions are actually supported by the results
- **Scored assessment** — 0–3 per domain, total /18, with interpretation guide
- **Actionable output** — top 5 fatal flaws, top 5 fixable issues, what's needed to trust the study

### Clinical Evidence Reviewer

Evidence-based decision support with guardrails:

- **Strict citation policy** — every claim cites a DOI/PMID or gets an explicit uncertainty label
- **GRADE certainty** — High/Moderate/Low/Very Low with downgrading factors explained
- **Patient selection** — who's a good candidate, risk factors, required diagnostics, failure modes
- **What's unknown** — explicit gaps in the evidence, what studies would resolve them
- **Safety first** — mandatory disclaimer, conservative recommendations, mechanistic reasoning separated from empirical evidence

### Dental Content Creator

Content that sounds professional, not AI-generated:

- **Audience modes** — adjusts tone, depth, and jargon for GPs, specialists, students, patients, or industry
- **Evidence-backed mode** — clinical claims cite sources (default for professional audiences)
- **Full content bundle** — main piece + LinkedIn + X/Twitter + Instagram + 5 hooks + CTA variants
- **No-overclaim guardrails** — no absolute outcome claims, no unsourced brand comparisons, case-selection caveats required

### Dental Image Generator

AI-generated clinical visuals:

- **Three style presets** — clinical (textbook), patient-friendly (calming), infographic (modern)
- **Brand extraction** — analyzes your clinic's logo/brochure and matches the style
- **Prompt cookbook** — tested prompts for surgical diagrams, patient handouts, social media graphics
- **Google Gemini** — free tier (15 req/min), no design skills needed

---

## Troubleshooting

**"The AI isn't following the skill protocol."**
Start your prompt with the skill name: *"Using the Research Critic protocol, analyze..."* If that doesn't help, check that the SKILL.md is loaded in your project (not just mentioned in the chat).

**"Output looks generic, not specialized."**
Make sure you're working inside the project/conversation where the skill is loaded. In Claude Desktop, conversations outside the project don't have access to project knowledge files.

**"It's citing studies that don't exist."**
AI models can hallucinate citations. The Evidence Reviewer skill has guardrails (uncertainty labels), but always verify DOIs before using them. Ask: *"Verify this citation — is it real?"*

**"Can I use more than one skill at once?"**
Yes. Add multiple SKILL.md files to the same project. The AI will use whichever is relevant to your prompt. For best results with multiple skills, name the one you want in your prompt.

---

## Testing

See [TESTING.md](TESTING.md) for manual test prompts and structural checks for each skill.

---

## About

Created by **[Francisco Teixeira Barbosa](https://periospot.com)** — periodontist, dental tech enthusiast, and founder of [Periospot](https://periospot.com).

These skills are opinionated by design. They enforce structured extraction before judgment, require citations or uncertainty labels, and include dental-specific checks that generic AI prompts miss.

**Newsletter:** [The Periospot Brew](https://periospot.com) — weekly AI + dentistry insights.

## License

MIT — use these however you want. If they help your research or practice, a star is appreciated.

---

*Built by [Periospot](https://periospot.com)*
