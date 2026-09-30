#!/usr/bin/env python3
"""
Generate dental illustrations with OpenAI's image model (default gpt-image-2.5-sunburst).

Standard library only (urllib, json, base64). Needs OPENAI_API_KEY in the environment,
a paid OpenAI API key from https://platform.openai.com/api-keys.

Usage:
    python3 generate_dental_image.py --prompt "Dental implant cross-section" --output implant.png
    python3 generate_dental_image.py --prompt "Post-extraction care" --style patient-friendly --output care.png
    python3 generate_dental_image.py --prompt "Periodontal comparison" --style clinical --quality low --output perio.png
    python3 generate_dental_image.py --prompt "Post-op instructions" --brand-asset clinic-logo.png --output branded.png
    python3 generate_dental_image.py --prompt "Sinus lift, 4 panels" --dry-run

API reference (read 2026-09-30): https://developers.openai.com/api/docs/guides/image-generation
and the OpenAPI spec at https://github.com/openai/openai-openapi (CreateImageRequest,
EditImageBodyJsonParam).
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "gpt-image-2.5-sunburst"
DEFAULT_SIZE = "1024x1024"
DEFAULT_QUALITY = "medium"
GENERATIONS_URL = "https://api.openai.com/v1/images/generations"
EDITS_URL = "https://api.openai.com/v1/images/edits"
TIMEOUT_SECONDS = 300
# Quality values the Images API lists for the GPT image models; xhigh and max are for the
# gpt-image-2.5 models only (OpenAPI spec, CreateImageRequest.quality, read 2026-09-30).
QUALITIES = ("low", "medium", "high", "xhigh", "max", "auto")
OUTPUT_FORMATS = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}
# The JSON edits body carries the asset as a base64 data URL, and the API caps that string at
# 20,971,520 characters (ImageRefParam.image_url maxLength, OpenAPI spec read 2026-09-30).
# Base64 adds one third, so the file itself must stay under about 15 MB.
MAX_ASSET_BYTES = 15_000_000

# ---------------------------------------------------------------------------
# Style presets. Each one wraps the user prompt with dental-specific context.
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

BRAND_NOTE = (
    " The attached image is the clinic's own brand asset (logo, brochure or business card). "
    "Match its colour palette, typography feel and overall design style in the new illustration. "
    "Do not reproduce the asset itself; create a new image in the same visual identity."
)


def image_data_url(path: str) -> str:
    """Read a png, jpg or webp file and return it as a base64 data URL for the edits endpoint."""
    asset = Path(path)
    if not asset.is_file():
        raise FileNotFoundError(f"Brand asset not found: {path}")
    mime = mimetypes.guess_type(str(asset))[0]
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError(f"Brand asset must be a png, jpg or webp file, got: {asset.name}")
    size = asset.stat().st_size
    if size > MAX_ASSET_BYTES:
        raise ValueError(
            f"Brand asset must be under {MAX_ASSET_BYTES / 1_000_000:.0f} MB to travel inline to the Images API, "
            f"got {size / 1_000_000:.1f} MB: {asset.name}. Export a smaller copy and run again."
        )
    return f"data:{mime};base64,{base64.b64encode(asset.read_bytes()).decode('ascii')}"


def output_format_for(output: str) -> str:
    return OUTPUT_FORMATS.get(Path(output).suffix.lower(), "png")


def build_request(
    prompt: str,
    style: str,
    output: str,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    quality: str = DEFAULT_QUALITY,
    brand_asset: str | None = None,
) -> tuple[str, dict]:
    """Return (endpoint URL, JSON body). No network access here."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["clinical"])
    full_prompt = preset.format(prompt=prompt)
    body = {
        "model": model,
        "prompt": full_prompt,
        "size": size,
        "quality": quality,
        "output_format": output_format_for(output),
        "background": "opaque",
        "n": 1,
    }
    if not brand_asset:
        return GENERATIONS_URL, body
    # The edits endpoint takes the asset as an input image (JSON body, ImageRefParam data URL)
    # and generates a new image in the same style. Supported for the GPT image models.
    body["prompt"] = full_prompt + BRAND_NOTE
    body["images"] = [{"image_url": image_data_url(brand_asset)}]
    return EDITS_URL, body


def printable(body: dict) -> dict:
    """Copy of the body with image data URLs shortened, for --dry-run and logs."""
    shown = dict(body)
    if "images" in shown:
        shown["images"] = [
            {"image_url": f"{ref['image_url'].split(',', 1)[0]},<{len(ref['image_url'])} characters>"}
            for ref in shown["images"]
        ]
    return shown


def post_json(url: str, body: dict, api_key: str) -> dict:
    """POST the body to the Images API and return the decoded JSON answer."""
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dental-ai-skills/dental-image-generator",
        },
        method="POST",
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def api_error_message(error: HTTPError, api_key: str) -> str:
    """One line from an HTTP error, with the key masked in case a server echoes it."""
    try:
        raw = error.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - the body is optional
        raw = ""
    try:
        message = json.loads(raw)["error"]["message"]
    except (ValueError, KeyError, TypeError):
        message = raw.strip()[:300] or error.reason
    return f"HTTP {error.code}: {str(message).replace(api_key, '<OPENAI_API_KEY>')}"


def save_image(payload: dict, output: str) -> Path:
    """Write data[0].b64_json to the output file and return its path."""
    items = payload.get("data") or []
    b64 = items[0].get("b64_json") if items and isinstance(items[0], dict) else None
    if not b64:
        raise ValueError("The API returned no image (no data[0].b64_json in the answer).")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(b64))
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate dental illustrations with OpenAI's image model (needs OPENAI_API_KEY).",
    )
    parser.add_argument("--prompt", "-p", required=True, help="What to illustrate")
    parser.add_argument("--output", "-o", default="output.png",
                        help="Output file; .png, .jpg or .webp picks the format (default: output.png)")
    parser.add_argument(
        "--style", "-s",
        choices=list(STYLE_PRESETS.keys()),
        default="clinical",
        help="Style preset: clinical, patient-friendly, or infographic (default: clinical)",
    )
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"OpenAI image model id (default: {DEFAULT_MODEL})")
    parser.add_argument(
        "--size", default=DEFAULT_SIZE,
        help=("WIDTHxHEIGHT. Standard sizes: 1024x1024, 1536x1024, 1024x1536. Custom sizes: both "
              "edges multiples of 16, aspect between 1:3 and 3:1, at least 655,360 pixels in total "
              f"(default: {DEFAULT_SIZE})"),
    )
    parser.add_argument("--quality", "-q", choices=QUALITIES, default=DEFAULT_QUALITY,
                        help=f"Image quality; low is cheapest and fastest (default: {DEFAULT_QUALITY})")
    parser.add_argument(
        "--brand-asset", "-b",
        default=None,
        help="Path to a clinic asset (logo, brochure, business card; png, jpg or webp). "
             "It is sent as an input image so the result matches its colours and style.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the request that would be sent and exit without calling the API")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        url, body = build_request(
            args.prompt, args.style, args.output, args.model, args.size, args.quality, args.brand_asset,
        )
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return 1

    if args.dry_run:
        print(json.dumps({"url": url, "body": printable(body)}, indent=2))
        return 0

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Set OPENAI_API_KEY to a paid OpenAI API key (https://platform.openai.com/api-keys) and run again.")
        return 2

    print(f"Generating a {args.style} image with {args.model} ({args.size}, quality {args.quality})...")
    try:
        payload = post_json(url, body, api_key)
    except HTTPError as error:
        print(f"The OpenAI Images API refused the request. {api_error_message(error, api_key)}")
        return 1
    except URLError as error:
        print(f"Could not reach the OpenAI Images API: {error.reason}")
        return 1

    try:
        path = save_image(payload, args.output)
    except ValueError as error:
        print(error)
        return 1

    usage = payload.get("usage") or {}
    print(f"Saved {path} ({path.stat().st_size / 1024:.0f} KB)")
    print(
        "Response: created={created} size={size} quality={quality} output_format={fmt} "
        "output_tokens={out} total_tokens={total}".format(
            created=payload.get("created"), size=payload.get("size"), quality=payload.get("quality"),
            fmt=payload.get("output_format"), out=usage.get("output_tokens"), total=usage.get("total_tokens"),
        )
    )
    print("Review AI-generated medical illustrations for anatomical accuracy before clinical use.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
