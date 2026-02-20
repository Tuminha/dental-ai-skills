#!/usr/bin/env python3
"""
Generate dental illustrations using Google Gemini 2.0 Flash.

Usage:
    python generate_dental_image.py --prompt "Dental implant cross-section" --output implant.png
    python generate_dental_image.py --prompt "Post-extraction care" --style patient-friendly --output care.png
    python generate_dental_image.py --prompt "Periodontal comparison" --style clinical --output perio.png
"""

import argparse
import base64
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Missing dependency. Run: pip install google-genai")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Style presets — each one wraps the user prompt with dental-specific context
# ---------------------------------------------------------------------------
STYLE_PRESETS = {
    "clinical": (
        "Create a professional medical/clinical illustration. "
        "Use clean lines, accurate anatomical proportions, neutral background. "
        "Label key anatomical structures clearly. "
        "Style: medical textbook illustration, high contrast, precise. "
        "Subject: {prompt}"
    ),
    "patient-friendly": (
        "Create a friendly, approachable dental illustration for patients. "
        "Use soft colors, simple shapes, and a calming blue/teal palette. "
        "Avoid graphic or scary imagery. Make it reassuring and easy to understand. "
        "Include simple labels if relevant. "
        "Subject: {prompt}"
    ),
    "infographic": (
        "Design a clean dental infographic. "
        "Use numbered steps, simple icons, clear hierarchy, and a modern color palette. "
        "Make text readable and layout organized top-to-bottom or left-to-right. "
        "Keep it professional yet approachable for patient education. "
        "Subject: {prompt}"
    ),
}


def extract_brand_style(image_path: str, api_key: str) -> str:
    """Analyze a clinic's existing asset to extract brand colors, fonts, and style."""
    import mimetypes

    path = Path(image_path)
    if not path.exists():
        print(f"❌ Brand asset not found: {image_path}")
        sys.exit(1)

    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    image_bytes = path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode()

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(
                "Analyze this dental clinic's branding asset. Extract:\n"
                "1. Primary and secondary brand colors (hex codes)\n"
                "2. Typography style (serif/sans-serif, weight, feel)\n"
                "3. Overall design style (modern/classic/playful/clinical)\n"
                "4. Logo description if visible\n"
                "5. Any recurring design patterns or motifs\n\n"
                "Return a concise style guide I can use to generate matching visuals."
            ),
        ],
    )

    style_guide = response.candidates[0].content.parts[0].text
    print(f"🎨 Extracted brand style from {path.name}:")
    print(f"   {style_guide[:200]}...")
    return style_guide


def generate_image(prompt: str, style: str = "clinical", output: str = "output.png", brand_asset: str = None) -> Path:
    """Generate a dental image via Gemini 2.0 Flash and save it."""

    # Resolve API key
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
        print("   Get one free at https://aistudio.google.com/apikey")
        sys.exit(1)

    # Extract brand style if asset provided
    brand_context = ""
    if brand_asset:
        brand_context = extract_brand_style(brand_asset, api_key)
        brand_context = f"\n\nIMPORTANT - Match this clinic's brand style:\n{brand_context}\n"

    # Build the final prompt
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["clinical"])
    full_prompt = preset.format(prompt=prompt) + brand_context

    print(f"🦷 Generating image with style '{style}'...")
    print(f"   Prompt: {prompt}")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    # Extract and save the image
    output_path = Path(output)
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_bytes = part.inline_data.data
            if isinstance(image_bytes, str):
                image_bytes = base64.b64decode(image_bytes)
            output_path.write_bytes(image_bytes)
            print(f"✅ Saved to {output_path} ({len(image_bytes) / 1024:.0f} KB)")
            return output_path
        elif part.text:
            print(f"   Model note: {part.text[:200]}")

    print("⚠️  No image returned. Try refining your prompt.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate dental illustrations with Gemini AI")
    parser.add_argument("--prompt", "-p", required=True, help="What to illustrate")
    parser.add_argument("--output", "-o", default="output.png", help="Output file path (default: output.png)")
    parser.add_argument(
        "--style", "-s",
        choices=list(STYLE_PRESETS.keys()),
        default="clinical",
        help="Style preset: clinical, patient-friendly, or infographic (default: clinical)",
    )
    parser.add_argument(
        "--brand-asset", "-b",
        default=None,
        help="Path to an existing clinic asset (logo, brochure, business card) to extract brand style from",
    )
    args = parser.parse_args()
    generate_image(args.prompt, args.style, args.output, args.brand_asset)


if __name__ == "__main__":
    main()
