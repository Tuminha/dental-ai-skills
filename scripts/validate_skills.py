#!/usr/bin/env python3
"""Validate SKILL.md frontmatter without requiring third-party dependencies."""

from __future__ import annotations

import pathlib
import sys


REQUIRED = {"name", "description"}


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


def validate(path: pathlib.Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False, "missing YAML frontmatter"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False, "missing closing frontmatter marker"
    try:
        data = parse_simple_frontmatter(parts[1])
    except Exception as exc:  # noqa: BLE001 - CLI should report parser failures
        return False, f"invalid frontmatter: {exc}"
    missing = sorted(REQUIRED - data.keys())
    if missing:
        return False, f"missing required keys: {', '.join(missing)}"
    if not data["name"].strip():
        return False, "empty name"
    if not data["description"].strip():
        return False, "empty description"
    return True, f"OK name={data['name']} description_len={len(data['description'])}"


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
