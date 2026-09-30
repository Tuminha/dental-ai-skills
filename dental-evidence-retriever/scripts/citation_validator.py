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


def fetch_json(url: str, timeout: float) -> dict | None:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "dental-ai-skills-citation-validator/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-requested network check
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            return None
    except Exception:
        return None


# A web page that answers 200 proves nothing: PubMed serves a challenge page
# for any PMID, real or not, and publishers block scripts behind a DOI. Ask the
# registries for the record instead. True: the record exists. False: the
# registry says it does not. None: no clear answer, so the citation stays
# unverified.
def pmid_exists(pmid: str, timeout: float) -> bool | None:
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={urllib.parse.quote(pmid)}"
    data = fetch_json(url, timeout)
    record = (data or {}).get("result", {}).get(pmid) if isinstance(data, dict) else None
    if not isinstance(record, dict):
        return None
    if record.get("error"):
        return False
    return str(record.get("uid")) == pmid


def doi_exists(doi: str, timeout: float) -> bool | None:
    url = f"https://doi.org/api/handles/{urllib.parse.quote(doi, safe='/')}"
    data = fetch_json(url, timeout)
    code = data.get("responseCode") if isinstance(data, dict) else None
    if code == 1:
        return True
    if code in (100, 200):
        return False
    return None


def validate_one(raw: str, check_network: bool, timeout: float) -> ValidationResult:
    identifier_type, normalized = normalize_identifier(raw)
    if identifier_type == "pmid":
        syntax_valid = bool(PMID_RE.match(normalized))
    else:
        normalized = normalized.rstrip(".")
        syntax_valid = bool(DOI_RE.match(normalized))

    resolves = None
    warning = None
    if not syntax_valid:
        warning = f"{identifier_type.upper()} syntax is invalid or unsupported."
    elif check_network:
        exists = pmid_exists if identifier_type == "pmid" else doi_exists
        resolves = exists(normalized, timeout)
        if resolves is False:
            warning = f"{identifier_type.upper()} syntax is valid but the registry has no record of it."
        elif resolves is None:
            warning = f"{identifier_type.upper()} could not be checked online; treat it as unverified."

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
