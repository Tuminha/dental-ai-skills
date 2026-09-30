---
name: dental-image-generator
description: Use when the user asks to generate dental clinical illustrations, patient infographics, branded dental visuals, surgical diagrams, anatomy comparisons, post-op visual instructions, or social media graphics using the included OpenAI image-generation script.
when_to_use: User asks to generate or plan dental visuals, implant or periodontal illustrations, patient handout images, infographics, procedure diagrams, branded clinic visuals, or image-generation prompts/scripts for dental education.
effort: high
---

# Dental Image Generator — AI Clinical Illustration Skill

**Skill protocol version:** 2026.05.16

## Identity

You generate clinical illustrations, patient infographics, and branded dental visuals using AI image generation. You understand dental anatomy, clinical procedures, and how to communicate visually to different audiences (clinicians vs patients).

## Setup

This skill uses **OpenAI's Images API** with the model `gpt-image-2.5-sunburst` by default. OpenAI's image-generation guide names it as the model for work where editing precision matters, and the brand-asset option below uses the editing route. It is a **paid API**: OpenAI bills each image by output tokens, and the current rates are on its pricing page. The model id, the size rules and the quality values were checked live on 2026-09-30 against the API and the guide at https://developers.openai.com/api/docs/guides/image-generation.

### Get Your API Key (2 minutes)

1. Go to **[https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)**
2. Sign in and click **"Create new secret key"**
3. Copy the key. The OpenAI account needs billing set up before the key can generate images.

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc)
export OPENAI_API_KEY="your-api-key-here"
```

### Install Dependencies

None. The script uses only the Python standard library (Python 3.10 or newer).

---

## Usage

### Command Line

```bash
python3 scripts/generate_dental_image.py \
  --prompt "Your description here" \
  --style clinical \
  --output output.png
```

`--help` and `--dry-run` work without a key. A real run without `OPENAI_API_KEY` prints one sentence and exits with code 2. Nothing is printed that contains the key.

### Options

| Option | Default | Notes |
|--------|---------|-------|
| `--prompt`, `-p` | required | What to illustrate |
| `--style`, `-s` | `clinical` | `clinical`, `patient-friendly` or `infographic`; each preset is a prefix on the prompt |
| `--output`, `-o` | `output.png` | `.png`, `.jpg` or `.webp` picks the output format |
| `--model`, `-m` | `gpt-image-2.5-sunburst` | Any OpenAI image model id, for example `gpt-image-2.5-flare` or `gpt-image-2` |
| `--size` | `1024x1024` | `1536x1024` (landscape) and `1024x1536` (portrait) are the other standard sizes. Custom `WIDTHxHEIGHT`: both edges multiples of 16, aspect between 1:3 and 3:1, 655,360 to 8,294,400 pixels in total |
| `--quality`, `-q` | `medium` | `low`, `medium`, `high`, `xhigh`, `max` or `auto`; `low` is the cheapest draft setting |
| `--brand-asset`, `-b` | none | A clinic asset (png, jpg or webp) sent as an input image, see below |
| `--dry-run` | off | Print the request as JSON and exit without calling the API |

### Style Presets

| Style | Look | Best For |
|-------|------|----------|
| `clinical` | Medical textbook — clean lines, anatomical labels, neutral colors | Surgical diagrams, anatomical illustrations, clinical comparisons |
| `patient-friendly` | Soft, calming palette — simple shapes, reassuring, no scary imagery | Post-op handouts, waiting room posters, patient education |
| `infographic` | Modern layout — numbered steps, icons, clear hierarchy | Social media, educational carousels, quick-reference guides |

### Brand Reference

Give the script your clinic's logo, brochure or business card and the model matches its colours and design style:

```bash
python3 scripts/generate_dental_image.py \
  --prompt "Post-operative implant care instructions" \
  --style patient-friendly \
  --brand-asset /path/to/my-clinic-logo.png \
  --output branded-instructions.png
```

**How it works:** the asset goes to the Images API edits endpoint as an input image (png, jpg or webp, under 15 MB: it travels inline as base64 and the API caps that at 20,971,520 characters), with a note in the prompt to reuse its palette, typography feel and overall style without copying the asset itself. There is no separate text-analysis step. Input images add input tokens to the bill.

---

## Prompt Cookbook

Tested prompts that produce reliable results.

### Clinical Illustrations

```
"Create a clinical illustration showing the stages of dental implant placement
in cross-section view. Clean, professional medical illustration style with
labeled anatomical structures."

"Illustrate a comparison between healthy periodontium and stage III
periodontitis, showing bone loss, pocket depth, and inflammation.
Medical textbook style."

"Show a step-by-step sinus lift procedure (lateral window approach) in
4 panels. Label the sinus membrane, bone graft material, and implant site."

"Cross-section illustration of a tooth with apical periodontitis showing
the abscess, periapical radiolucency, and path of infection."
```

### Patient Education

```
"Design a patient-friendly infographic about post-extraction care
instructions. Use simple icons, numbered steps, and a calming blue
color palette."

"Create a visual guide showing proper brushing technique in 4 steps.
Friendly, cartoon-style, suitable for a dental office waiting room poster."

"Illustrate the difference between gingivitis and periodontitis in a
simple side-by-side comparison. Patient-friendly — no scary imagery."
```

### Social Media / Infographics

```
"Design a modern infographic titled '5 Foods That Strengthen Your Teeth'.
Clean layout, food icons, brief text for each item. Instagram-ready."

"Create a visual showing the timeline of dental implant healing: surgery →
osseointegration → abutment → crown. Modern, minimal style."

"Design a myth vs fact infographic about dental X-ray safety.
Two columns, checkmarks and X marks, professional but approachable."
```

---

## Prompt Tips

1. **Be anatomically specific** — "cross-section view," "sagittal plane," "buccal aspect"
2. **Specify the audience** — "medical textbook" vs "patient handout" produces very different results
3. **Name the structures** — "label the alveolar bone, PDL, cementum, and gingiva"
4. **Set the color mood** — "calming blue palette" for patients, "high contrast" for clinical
5. **Use panel layouts** — "show in 4 panels" or "step-by-step from left to right"
6. **Iterate** — first generation not perfect? Add detail and regenerate

## Important

**Always review AI-generated medical illustrations for anatomical accuracy before clinical use.**

## Methodology Review Date

**Last review:** 2026-09-30

- 2026-09-30: Moved from Google Gemini to OpenAI's Images API. The old script pinned `gemini-2.0-flash-exp`; Google's deprecations page (https://ai.google.dev/gemini-api/docs/deprecations, read 2026-09-30) lists `gemini-2.0-flash` as shut down on 1 June 2026 and has no row for the `-exp` id, so the script could no longer run. The new script is standard library only, defaults to `gpt-image-2.5-sunburst`, adds `--model`, `--size`, `--quality` and `--dry-run`, and sends a brand asset as an input image to the edits endpoint instead of running a text analysis first. Model id, size rules and quality values checked live against the API and OpenAI's image-generation guide on that date. The free-tier rate claim was removed; the API is paid.

Re-review this skill when OpenAI's image models page retires `gpt-image-2.5-sunburst` or lists a newer default, or when the Images API changes its size or quality rules.

---

*Part of [Dental AI Skills](https://github.com/Tuminha/dental-ai-skills) by [Francisco Teixeira Barbosa](https://periospot.com)*
