# Dental Image Generator — AI Clinical Illustration Skill

## Identity

You generate clinical illustrations, patient infographics, and branded dental visuals using AI image generation. You understand dental anatomy, clinical procedures, and how to communicate visually to different audiences (clinicians vs patients).

## Setup

This skill uses **Google Gemini 2.0 Flash** for image generation.

### Get Your API Key (2 minutes)

1. Go to **[https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc)
export GEMINI_API_KEY="your-api-key-here"
```

Free tier: 15 requests/minute for Gemini 2.0 Flash experimental.

### Install Dependencies

```bash
pip install -r requirements.txt
# or: pip install google-genai Pillow
```

---

## Usage

### Command Line

```bash
python scripts/generate_dental_image.py \
  --prompt "Your description here" \
  --style clinical \
  --output output.png
```

### Style Presets

| Style | Look | Best For |
|-------|------|----------|
| `clinical` | Medical textbook — clean lines, anatomical labels, neutral colors | Surgical diagrams, anatomical illustrations, clinical comparisons |
| `patient-friendly` | Soft, calming palette — simple shapes, reassuring, no scary imagery | Post-op handouts, waiting room posters, patient education |
| `infographic` | Modern layout — numbered steps, icons, clear hierarchy | Social media, educational carousels, quick-reference guides |

### Brand Extraction

The script can extract your clinic's visual identity from any existing asset:

```bash
python scripts/generate_dental_image.py \
  --prompt "Post-operative implant care instructions" \
  --style patient-friendly \
  --brand-asset /path/to/my-clinic-logo.png \
  --output branded-instructions.png
```

**What it extracts:** primary/secondary colors, typography style, design feel (modern/classic/playful/clinical), recurring patterns.

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

---

*Part of [Dental AI Skills](https://github.com/Tuminha/dental-ai-skills) by [Francisco Teixeira Barbosa](https://periospot.com)*
