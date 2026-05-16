#!/usr/bin/env python3
"""Validate DOI/PMID identifiers for evidence-retrieval workflows.

By default this script performs syntax checks only. Use --check-network to ask
NCBI and doi.org whether identifiers resolve. Network checks are optional so the
skill remains useful in no-network environments.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Iterable


DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
PMID_RE = re.compile(r"^\d{1,9}$")


@dataclass
class ValidationResult:
    input: str
    identifier_type: str
    syntax_valid: bool
    resolves: bool | None
    normalized: str | None
    warning: str | None


def normalize_identifier(raw: str) -> tuple[str, str]:
    value = raw.strip()
    lower = value.lower()
    if lower.startswith("doi:"):
        return "doi", value[4:].strip()
    if lower.startswith("pmid:"):
        return "pmid", value[5:].strip()
    if lower.startswith("https://doi.org/") or lower.startswith("http://doi.org/"):
        return "doi", value.split("doi.org/", 1)[1].strip()
    if PMID_RE.match(value):
        return "pmid", value
    return "doi", value


def url_exists(url: str, timeout: float) -> bool:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "dental-ai-skills-citation-validator/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-requested network check
            return 200 <= response.status < 400
    except urllib.error.HTTPError as exc:
        return 200 <= exc.code < 400
    except Exception:
        return False


def validate_one(raw: str, check_network: bool, timeout: float) -> ValidationResult:
    identifier_type, normalized = normalize_identifier(raw)
    if identifier_type == "pmid":
        syntax_valid = bool(PMID_RE.match(normalized))
        url = f"https://pubmed.ncbi.nlm.nih.gov/{urllib.parse.quote(normalized)}/"
    else:
        normalized = normalized.rstrip(".")
        syntax_valid = bool(DOI_RE.match(normalized))
        url = f"https://doi.org/{urllib.parse.quote(normalized, safe='/')}"

    resolves = None
    warning = None
    if not syntax_valid:
        warning = f"{identifier_type.upper()} syntax is invalid or unsupported."
    elif check_network:
        resolves = url_exists(url, timeout)
        if not resolves:
            warning = f"{identifier_type.upper()} syntax is valid but did not resolve during this check."

    return ValidationResult(
        input=raw,
        identifier_type=identifier_type,
        syntax_valid=syntax_valid,
        resolves=resolves,
        normalized=normalized if syntax_valid else None,
        warning=warning,
    )


def iter_inputs(args: argparse.Namespace) -> Iterable[str]:
    for item in args.identifiers:
        yield item
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    yield stripped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifiers", nargs="*", help="DOIs, DOI URLs, PMID values, or PMID: prefixes")
    parser.add_argument("--file", help="Optional newline-delimited identifier file")
    parser.add_argument("--check-network", action="store_true", help="Attempt to resolve identifiers online")
    parser.add_argument("--timeout", type=float, default=8.0, help="Network timeout in seconds")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    items = list(iter_inputs(args))
    if not items:
        print(json.dumps({"error": "provide at least one identifier or --file"}, indent=2))
        return 2
    results = [asdict(validate_one(item, args.check_network, args.timeout)) for item in items]
    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 1 if any(not result["syntax_valid"] for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
