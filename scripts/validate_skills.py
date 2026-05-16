#!/usr/bin/env python3
"""Validate SKILL.md frontmatter without requiring third-party dependencies."""

from __future__ import annotations

import pathlib
import re
import sys


REQUIRED = {"name", "description"}
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
MAX_DESCRIPTION_LEN = 1024
MAX_LISTING_LEN = 1536
VALID_EFFORT = {"low", "medium", "high", "xhigh", "max"}


def parse_simple_frontmatter(block: str) -> dict[str, str]:
    """Parse the simple key/value YAML shape used by these skills.

    If PyYAML is installed, use it. Otherwise, support the repository's
    intentionally boring `key: value` and folded scalar frontmatter.
    """
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(block) or {}
        if not isinstance(data, dict):
            raise ValueError("frontmatter did not parse to a mapping")
        return {str(k): "" if v is None else str(v) for k, v in data.items()}
    except ModuleNotFoundError:
        pass

    data: dict[str, str] = {}
    current_key: str | None = None
    folded = False
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and current_key:
            stripped = line.strip()
            if folded:
                data[current_key] = (data[current_key] + " " + stripped).strip()
                continue
            if stripped.startswith("- "):
                # Support common frontmatter lists such as:
                # allowed-tools:
                #   - Read
                # The validator only needs required scalar keys, so storing a
                # compact string representation is sufficient.
                data[current_key] = (data[current_key] + " " + stripped[2:]).strip()
                continue
            if data.get(current_key, "") == "":
                data[current_key] = stripped
                continue
            raise ValueError(f"cannot parse nested frontmatter line: {line!r}")
        if ":" not in line:
            raise ValueError(f"cannot parse frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        folded = value in {">", ">-", "|", "|-"}
        data[key] = "" if folded else value.strip("\"'")
        current_key = key
    return data


def find_bare_frontmatter_lines(block: str) -> list[str]:
    """Detect unindented non-key lines outside folded/list contexts."""
    bad: list[str] = []
    folded = False
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith((" ", "\t")):
            continue
        if ":" in line:
            _, value = line.split(":", 1)
            folded = value.strip() in {">", ">-", "|", "|-"}
            continue
        if not folded:
            bad.append(line)
    return bad


def referenced_local_paths(path: pathlib.Path, text: str) -> list[pathlib.Path]:
    """Return likely local references that should exist."""
    patterns = [
        r"`((?:references|scripts|assets)/[^`]+)`",
        r"\]\(((?:references|scripts|assets|examples|fixtures)/[^)]+)\)",
    ]
    refs: list[pathlib.Path] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            raw = match.group(1).strip()
            if raw.startswith(("http://", "https://")):
                continue
            refs.append(path.parent / raw)
    return refs


def validate(path: pathlib.Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False, "missing YAML frontmatter"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False, "missing closing frontmatter marker"
    bare_lines = find_bare_frontmatter_lines(parts[1])
    if bare_lines:
        return False, f"bare unindented frontmatter lines: {bare_lines!r}"
    try:
        data = parse_simple_frontmatter(parts[1])
    except Exception as exc:  # noqa: BLE001 - CLI should report parser failures
        return False, f"invalid frontmatter: {exc}"
    missing = sorted(REQUIRED - data.keys())
    if missing:
        return False, f"missing required keys: {', '.join(missing)}"
    if not data["name"].strip():
        return False, "empty name"
    if not NAME_RE.match(data["name"].strip()):
        return False, "name must match ^[a-z0-9-]{1,64}$"
    if not data["description"].strip():
        return False, "empty description"
    if len(data["description"]) > MAX_DESCRIPTION_LEN:
        return False, f"description too long for Agent Skills portability: {len(data['description'])}>{MAX_DESCRIPTION_LEN}"
    listing_len = len(data["description"]) + len(data.get("when_to_use", ""))
    if listing_len > MAX_LISTING_LEN:
        return False, f"description + when_to_use too long for Claude Code listing: {listing_len}>{MAX_LISTING_LEN}"
    effort = data.get("effort")
    if effort and effort.strip() not in VALID_EFFORT:
        return False, f"invalid effort {effort!r}; expected one of {sorted(VALID_EFFORT)}"
    missing_refs = [str(ref.relative_to(path.parent)) for ref in referenced_local_paths(path, text) if not ref.exists()]
    if missing_refs:
        return False, f"referenced local files do not exist: {missing_refs}"
    body_lines = len(parts[2].splitlines())
    warning = f" body_lines={body_lines}"
    if body_lines > 500:
        warning += " WARN_BODY_OVER_500"
    return True, f"OK name={data['name']} description_len={len(data['description'])} listing_len={listing_len}{warning}"


def main() -> int:
    root = pathlib.Path.cwd()
    paths = sorted(root.glob("*/SKILL.md"))
    failed = False
    for path in paths:
        ok, message = validate(path)
        status = "OK" if ok else "INVALID"
        print(f"{status}: {path}: {message}")
        failed = failed or not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
