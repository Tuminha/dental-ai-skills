#!/usr/bin/env python3
"""Load one dental skill and send it to Nebius Token Factory.

This is a hackathon wrapper. It reads an existing SKILL.md file and does not
modify it. The model is asked to appraise only the text supplied in the request.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEMO_ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_SKILL = REPO_ROOT / "research-critic" / "SKILL.md"
DEFAULT_FIXTURE = REPO_ROOT / "fixtures" / "split-mouth-clustering.md"

# Catalog check on 23 Oct 2026: Nemotron 3 Super is served from us-central1.
DEFAULT_BASE_URL = "https://api.tokenfactory.us-central1.nebius.com/v1/"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
# Ids and regions from the public catalog checked on 23 Oct 2026.
MODEL_PRESETS = {
    "Nemotron 3 Super (us-central1)": {
        "model": DEFAULT_MODEL,
        "base_url": DEFAULT_BASE_URL,
    },
    "Nemotron 3 Nano (eu-north1)": {
        "model": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
        "base_url": "https://api.tokenfactory.eu-north1.nebius.com/v1/",
    },
    "Nemotron 3 Ultra (us-central1)": {
        "model": "nvidia/Nemotron-3-Ultra-550b-a55b",
        "base_url": "https://api.tokenfactory.us-central1.nebius.com/v1/",
    },
}
DEFAULT_MAX_TOKENS = 1800
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SECONDS = 180
MAX_STUDY_CHARS = 80_000

FIXTURE_SOURCE_NOTE = (
    "Source: repository fixture fixtures/split-mouth-clustering.md, Prompt section only. "
    "This is a synthetic regression fixture, not a published paper. "
    "Full text read: no. Only the fixture prompt was supplied. "
    "License: not a publication. Supplements: none."
)
PASTED_SOURCE_NOTE = (
    "Source: text pasted into the hackathon demo. "
    "No paper was fetched. Full text read: only the pasted text. "
    "License: not stated. Supplements: not provided."
)

DEMO_ADAPTER = """\
Demo adapter (hackathon wrapper, added by the runner, not part of the skill file):

This run is a short journal-club demo. Where this adapter and the skill's full output template disagree, keep the skill's rules on honesty, missing data, native bias-tool labels, and scope. Use the short headings below so the demo stays readable. A full multi-phase report is what the skill file specifies when this adapter is not present.

Write a brief a presenter can read in about two minutes.
- Extract before you judge.
- If a PICO element, method, result, disclosure, or citation is absent from the supplied text, write NOT REPORTED.
- State what text was read. This demo does not fetch papers and has no web search.
- Use the bias tool's native labels.
- Ground every finding in the supplied text. Do not invent methods, results, sample sizes, authors, funding, disclosures, or citations.
- Do not recommend changing clinical practice from this text.
- Do not present a Study Credibility total unless every scored domain is supported by the supplied text. If it is not, say the score is not supported.
- Use these headings only:
  1. What was read
  2. PICO and design extraction
  3. Bias tool and why
  4. Findings grounded in the supplied text
  5. What this single text cannot decide
"""


class ConfigError(RuntimeError):
    """The local configuration cannot make a Token Factory call."""


class TokenFactoryError(RuntimeError):
    """Token Factory returned an error or an unusable response."""


def load_dotenv(path: pathlib.Path, environ: dict[str, str] | None = None) -> None:
    """Load KEY=VALUE lines. Existing environment values win. Never prints values."""
    env = os.environ if environ is None else environ
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in env:
            env[key] = value


def load_local_env() -> None:
    load_dotenv(DEMO_ROOT / ".env")
    load_dotenv(REPO_ROOT / ".env")


def _frontmatter_name(block: str) -> str:
    match = re.search(r"^name:\s*([A-Za-z0-9-]+)\s*$", block, re.MULTILINE)
    if not match:
        raise ValueError("skill frontmatter has no name")
    return match.group(1)


def _protocol_version(body: str) -> str:
    match = re.search(r"\*\*Skill protocol version:\*\*\s*(\S+)", body)
    return match.group(1) if match else ""


def load_skill(path: pathlib.Path) -> dict[str, str]:
    """Read a skill file as stored. The returned text includes the frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} has no YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} frontmatter is not closed")
    return {
        "name": _frontmatter_name(parts[1]),
        "protocol_version": _protocol_version(parts[2]),
        "path": str(path),
        "text": text,
    }


def fixture_study_text(markdown: str) -> str:
    """Return the fixture Prompt only. The Expected Flags section is an answer key."""
    match = re.search(r"^## Prompt\s*\n(.*?)(?=^## |\Z)", markdown, re.MULTILINE | re.DOTALL)
    if not match or not match.group(1).strip():
        raise ValueError("fixture has no Prompt section")
    return match.group(1).strip()


def default_fixture_text() -> str:
    return fixture_study_text(DEFAULT_FIXTURE.read_text(encoding="utf-8"))


def source_note_for(study_text: str) -> str:
    if study_text.strip() == default_fixture_text():
        return FIXTURE_SOURCE_NOTE
    return PASTED_SOURCE_NOTE


def build_messages(skill: dict[str, str], study_text: str, source_note: str) -> list[dict[str, str]]:
    cleaned = study_text.replace("\x00", "").strip()
    if not cleaned:
        raise ValueError("study text is empty")
    if len(cleaned) > MAX_STUDY_CHARS:
        raise ValueError(f"study text is longer than {MAX_STUDY_CHARS} characters")
    system = (
        "Follow the dental skill protocol below on evidence honesty, extraction before judgment, "
        "native bias-tool labels, and scope. The protocol is the skill file as stored in the repository.\n\n"
        "----- skill file begins -----\n"
        f"{skill['text'].rstrip()}\n"
        "----- skill file ends -----\n\n"
        f"{DEMO_ADAPTER.strip()}\n"
    )
    user = (
        f"Skill loaded: {skill['name']}\n"
        f"Protocol version: {skill['protocol_version'] or 'not stated in the skill file'}\n\n"
        f"Source note:\n{source_note.strip()}\n\n"
        "Supplied text to appraise. This is the only study text in this run:\n\n"
        f"{cleaned}\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _bounded_number(raw: str, name: str, low: float, high: float, kind: type) -> float | int:
    try:
        value = kind(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number") from exc
    if not low <= value <= high:
        raise ConfigError(f"{name} must be between {low} and {high}")
    return value


def runtime_config(env: dict[str, str] | None = None) -> dict[str, object]:
    source = os.environ if env is None else env
    max_tokens = _bounded_number(
        source.get("NEBIUS_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)),
        "NEBIUS_MAX_TOKENS",
        1,
        8192,
        int,
    )
    temperature = _bounded_number(
        source.get("NEBIUS_TEMPERATURE", str(DEFAULT_TEMPERATURE)),
        "NEBIUS_TEMPERATURE",
        0,
        2,
        float,
    )
    timeout = _bounded_number(
        source.get("NEBIUS_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)),
        "NEBIUS_TIMEOUT_SECONDS",
        1,
        600,
        int,
    )
    return {
        "api_key": (source.get("NEBIUS_API_KEY") or "").strip(),
        "base_url": (source.get("NEBIUS_BASE_URL") or DEFAULT_BASE_URL).strip(),
        "model": (source.get("NEBIUS_MODEL") or DEFAULT_MODEL).strip(),
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "timeout": int(timeout),
    }


def public_config(config: dict[str, object]) -> dict[str, object]:
    """Config safe to print. The API key is reduced to a boolean."""
    shown = {key: value for key, value in config.items() if key != "api_key"}
    shown["api_key_set"] = bool(config.get("api_key"))
    return shown


def chat_body(messages: list[dict[str, str]], config: dict[str, object], stream: bool) -> dict[str, object]:
    body: dict[str, object] = {
        "model": config["model"],
        "messages": messages,
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
    }
    if stream:
        body["stream"] = True
    return body


def redact(text: str, secret: str) -> str:
    cleaned = text
    if secret:
        cleaned = cleaned.replace(secret, "[REDACTED]")
    return re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", cleaned)


def chat_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def _request(config: dict[str, object], messages: list[dict[str, str]], stream: bool) -> urllib.request.Request:
    api_key = str(config["api_key"])
    if not api_key:
        raise ConfigError(
            "NEBIUS_API_KEY is not set. Create a key in Nebius Token Factory, "
            "export it in the shell that starts the app, and run again. This demo does not ship a key."
        )
    if not str(config["model"]).strip():
        raise ConfigError("NEBIUS_MODEL is empty")
    if not str(config["base_url"]).strip():
        raise ConfigError("NEBIUS_BASE_URL is empty")
    body = chat_body(messages, config, stream)
    return urllib.request.Request(
        chat_url(str(config["base_url"])),
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )


def _read_error(exc: urllib.error.HTTPError, secret: str) -> str:
    raw = exc.read().decode("utf-8", errors="replace")
    detail = redact(raw, secret).strip()
    if len(detail) > 500:
        detail = detail[:500] + "..."
    return f"Token Factory HTTP {exc.code}: {detail or exc.reason}"


def _text_from_parts(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") in {None, "text"}:
                parts.append(str(part.get("text") or ""))
        return "".join(parts)
    return ""


def extract_assistant_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise TokenFactoryError("Token Factory returned no choices")
    message = choices[0].get("message") or {}
    text = _text_from_parts(message.get("content")).strip()
    if text:
        return text
    reasoning = message.get("reasoning_content") or message.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()
    raise TokenFactoryError("Token Factory returned an empty answer")


def content_from_sse_data(data: str) -> str | None:
    """Return one content delta. None means the stream is finished."""
    if data == "[DONE]":
        return None
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise TokenFactoryError("Token Factory returned a non-JSON stream line") from exc
    choices = payload.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    return _text_from_parts(delta.get("content"))


def call_token_factory(
    config: dict[str, object],
    messages: list[dict[str, str]],
    opener=None,
) -> dict[str, object]:
    """Non-streaming chat completion. Returns text, model, and usage."""
    request = _request(config, messages, stream=False)
    open_fn = opener or urllib.request.urlopen
    secret = str(config["api_key"])
    try:
        with open_fn(request, timeout=config["timeout"]) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise TokenFactoryError(_read_error(exc, secret)) from exc
    except urllib.error.URLError as exc:
        raise TokenFactoryError(f"Could not reach Token Factory: {redact(str(exc.reason), secret)}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TokenFactoryError("Token Factory returned non-JSON") from exc
    return {
        "text": extract_assistant_text(payload),
        "model": payload.get("model") or config["model"],
        "usage": payload.get("usage") or {},
    }


def iter_chat_deltas(config: dict[str, object], messages: list[dict[str, str]], opener=None):
    """Yield answer-text deltas from an OpenAI-compatible stream."""
    request = _request(config, messages, stream=True)
    open_fn = opener or urllib.request.urlopen
    secret = str(config["api_key"])
    response = None
    try:
        response = open_fn(request, timeout=config["timeout"])
    except urllib.error.HTTPError as exc:
        raise TokenFactoryError(_read_error(exc, secret)) from exc
    except urllib.error.URLError as exc:
        raise TokenFactoryError(f"Could not reach Token Factory: {redact(str(exc.reason), secret)}") from exc
    try:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            piece = content_from_sse_data(line.split(":", 1)[1].strip())
            if piece is None:
                break
            if piece:
                yield piece
    finally:
        close = getattr(response, "close", None)
        if close:
            close()


def dry_run_report(skill: dict[str, str], messages: list[dict[str, str]], config: dict[str, object]) -> str:
    public = public_config(config)
    system = messages[0]["content"]
    user = messages[1]["content"]
    lines = [
        "Dry run. No request was sent.",
        f"Skill: {skill['name']} ({skill['protocol_version'] or 'version not stated'})",
        f"Skill file: {skill['path']}",
        f"Skill file characters: {len(skill['text'])}",
        f"System prompt characters: {len(system)}",
        f"Model: {public['model']}",
        f"Base URL: {public['base_url']}",
        f"API key set: {'yes' if public['api_key_set'] else 'no'}",
        "",
        "User message:",
        user.rstrip(),
        "",
        "The system prompt contains the full skill file plus the demo adapter.",
    ]
    return redact("\n".join(lines), str(config.get("api_key") or ""))


def offline_checks() -> None:
    """Stdlib checks used by the repo smoke test. No network and no API key."""
    skill = load_skill(DEFAULT_SKILL)
    if skill["name"] != "research-critic":
        raise AssertionError("default skill name mismatch")
    if skill["protocol_version"] != "2026.09.30":
        raise AssertionError("default skill protocol version mismatch")
    if "Phase 0" not in skill["text"] or "Demo adapter" in skill["text"]:
        raise AssertionError("skill file was not loaded unchanged")

    fixture = DEFAULT_FIXTURE.read_text(encoding="utf-8")
    study = fixture_study_text(fixture)
    if "Expected Flags" in study or "RoB 2 crossover" in study:
        raise AssertionError("fixture answer key leaked into the study text")
    if "82%" not in study or "unpaired t-test" not in study:
        raise AssertionError("fixture prompt was not preserved")

    note = source_note_for(study)
    messages = build_messages(skill, study, note)
    system = messages[0]["content"]
    user = messages[1]["content"]
    if skill["text"].rstrip() not in system or "----- skill file begins -----" not in system:
        raise AssertionError("system prompt does not contain the skill file")
    if "NOT REPORTED" not in system or "changing clinical practice" not in system:
        raise AssertionError("demo adapter lost its honesty rules")
    if "synthetic regression fixture" not in user or "82%" not in user:
        raise AssertionError("user message lost the fixture or its source note")
    if "Treat p=0.04 as fragile" in user or "Expected Flags" in user:
        raise AssertionError("answer key reached the model prompt")
    try:
        build_messages(skill, "   ", note)
    except ValueError:
        pass
    else:
        raise AssertionError("empty study text was accepted")

    env = {
        "NEBIUS_API_KEY": "test-key-should-not-leak",
        "NEBIUS_BASE_URL": DEFAULT_BASE_URL,
        "NEBIUS_MODEL": DEFAULT_MODEL,
    }
    config = runtime_config(env)
    if public_config(config)["api_key_set"] is not True:
        raise AssertionError("public config lost the key flag")
    if "test-key-should-not-leak" in json.dumps(public_config(config)):
        raise AssertionError("public config printed the key")
    report = dry_run_report(skill, messages, config)
    if "test-key-should-not-leak" in report or "Dry run. No request was sent." not in report:
        raise AssertionError("dry run report is unsafe or incomplete")

    seen: dict[str, object] = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def read(self) -> bytes:
            payload = {
                "model": DEFAULT_MODEL,
                "choices": [{"message": {"role": "assistant", "content": "What was read\n\nFixture only."}}],
                "usage": {"total_tokens": 12},
            }
            return json.dumps(payload).encode()

        def close(self) -> None:
            return None

    def opener(request: urllib.request.Request, timeout: int = 0):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode())
        return _Response()

    result = call_token_factory(config, messages, opener=opener)
    if seen["url"] != "https://api.tokenfactory.us-central1.nebius.com/v1/chat/completions":
        raise AssertionError("chat URL mismatch")
    if seen["auth"] != "Bearer test-key-should-not-leak":
        raise AssertionError("authorization header mismatch")
    body = seen["body"]
    if not isinstance(body, dict) or body.get("model") != DEFAULT_MODEL or body.get("stream"):
        raise AssertionError("request body mismatch")
    if "test-key-should-not-leak" in json.dumps(body["messages"]):
        raise AssertionError("API key was copied into the prompt")
    if result["text"] != "What was read\n\nFixture only.":
        raise AssertionError("answer text was not extracted")

    def empty_key_opener(*args: object, **kwargs: object):
        raise AssertionError("network was used without an API key")

    try:
        call_token_factory(runtime_config({}), messages, opener=empty_key_opener)
    except ConfigError as exc:
        if "NEBIUS_API_KEY" not in str(exc):
            raise AssertionError("missing-key error is unclear") from exc
    else:
        raise AssertionError("missing API key was accepted")

    def http_error_opener(request: urllib.request.Request, timeout: int = 0):
        detail = json.dumps({"detail": "bad test-key-should-not-leak"}).encode()
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(detail))

    try:
        call_token_factory(config, messages, opener=http_error_opener)
    except TokenFactoryError as exc:
        message = str(exc)
        if "test-key-should-not-leak" in message or "HTTP 401" not in message or "[REDACTED]" not in message:
            raise AssertionError("HTTP error leaked the key or hid the status") from exc
    else:
        raise AssertionError("HTTP error was ignored")

    deltas = [
        b'data: {"choices":[{"delta":{"content":"What was read"}}]}',
        b"",
        b'data: {"choices":[{"delta":{"reasoning_content":"hidden"}}]}',
        b"data: [DONE]",
    ]
    pieces = []
    for raw in deltas:
        line = raw.decode().strip()
        if not line.startswith("data:"):
            continue
        piece = content_from_sse_data(line.split(":", 1)[1].strip())
        if piece is None:
            break
        if piece:
            pieces.append(piece)
    if pieces != ["What was read"]:
        raise AssertionError("stream parser kept reasoning or dropped content")

    class _Stream:
        def __iter__(self):
            yield b'data: {"choices":[{"delta":{"content":"PICO"}}]}\n'
            yield b"data: [DONE]\n"

        def close(self) -> None:
            return None

    streamed = list(iter_chat_deltas(config, messages, opener=lambda request, timeout=0: _Stream()))
    if streamed != ["PICO"]:
        raise AssertionError("streaming call did not yield the answer text")
    if _request(config, messages, stream=True).data is None:
        raise AssertionError("streaming request was empty")
    streamed_body = json.loads(_request(config, messages, stream=True).data.decode())
    if streamed_body.get("stream") is not True:
        raise AssertionError("streaming request did not set stream")

    parts = extract_assistant_text(
        {"choices": [{"message": {"content": [{"type": "text", "text": "PICO"}]}}]}
    )
    if parts != "PICO":
        raise AssertionError("list content was not read")

    example = (DEMO_ROOT / ".env.example").read_text(encoding="utf-8")
    if "NEBIUS_API_KEY=\n" not in example and "NEBIUS_API_KEY=\r\n" not in example:
        raise AssertionError(".env.example must keep NEBIUS_API_KEY empty")
    if "sk-" in example or "Bearer " in example:
        raise AssertionError(".env.example looks like it contains a credential")

    app_source = (DEMO_ROOT / "app.py").read_text(encoding="utf-8")
    compile(app_source, str(DEMO_ROOT / "app.py"), "exec")
    if "NEBIUS_API_KEY" not in app_source or "research-critic" not in app_source:
        raise AssertionError("app does not point at the skill and the key variable")

    readme = (DEMO_ROOT / "README.md").read_text(encoding="utf-8")
    for preset in MODEL_PRESETS.values():
        if preset["model"] not in readme or preset["base_url"] not in readme:
            raise AssertionError(f"README is missing preset {preset['model']}")
    if "MODEL_PRESETS" not in (DEMO_ROOT / "app.py").read_text(encoding="utf-8"):
        raise AssertionError("app does not use the shared model presets")

    script = (DEMO_ROOT / "DEMO_SCRIPT.md").read_text(encoding="utf-8")
    spoken_match = re.search(r"<!-- spoken:start -->(.*)<!-- spoken:end -->", script, re.DOTALL)
    if not spoken_match:
        raise AssertionError("demo script is missing spoken markers")
    spoken_words = re.findall(r"\b[\w']+\b", spoken_match.group(1))
    if not 250 <= len(spoken_words) <= 430:
        raise AssertionError(f"spoken script length is outside a 3-minute pace: {len(spoken_words)} words")
    if "synthetic" not in spoken_match.group(1).lower():
        raise AssertionError("spoken script must say the fixture is synthetic")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the research-critic skill through Nebius Token Factory.")
    parser.add_argument("--run", action="store_true", help="Call Token Factory. The default is a dry run.")
    parser.add_argument("--self-check", action="store_true", help="Run offline checks and exit.")
    parser.add_argument("--text", help="Study text. Omit this to use the synthetic split-mouth fixture.")
    parser.add_argument("--text-file", type=pathlib.Path, help="Read study text from a file.")
    parser.add_argument("--skill", type=pathlib.Path, default=DEFAULT_SKILL, help="Skill file to load.")
    parser.add_argument("--source-note", help="Override the source note sent with the study text.")
    args = parser.parse_args(argv)

    if args.self_check:
        offline_checks()
        print("OK: hackathon demo offline checks")
        return 0

    load_local_env()
    skill = load_skill(args.skill)
    if args.text and args.text_file:
        print("Use either --text or --text-file.", file=sys.stderr)
        return 2
    if args.text_file:
        study = args.text_file.read_text(encoding="utf-8")
    elif args.text:
        study = args.text
    else:
        study = default_fixture_text()
    note = args.source_note or source_note_for(study)
    try:
        messages = build_messages(skill, study, note)
        config = runtime_config()
    except (ConfigError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not args.run:
        print(dry_run_report(skill, messages, config))
        return 0

    try:
        result = call_token_factory(config, messages)
    except (ConfigError, TokenFactoryError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(result["text"])
    usage = result.get("usage") or {}
    if usage:
        print(f"\nModel: {result['model']}. Usage: {json.dumps(usage, sort_keys=True)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
