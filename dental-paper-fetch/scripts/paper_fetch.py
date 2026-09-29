#!/usr/bin/env python3
"""paper_fetch: download free full-text PDFs of scientific papers, with figures, filed by topic.

Part of the dental-paper-fetch skill in https://github.com/Tuminha/dental-ai-skills
(MIT license, see LICENSE in that repository).

Accepts a PMID, DOI (or doi.org link), PMCID or a title. It resolves the paper through
PubMed (PMID -> DOI/PMCID), with Crossref for titles outside PubMed, then tries free,
legal open-access copies only, in this order:
  1. the PubMed Central open-access bucket on AWS (managed by the National Library of Medicine)
  2. open-access locations listed by OpenAlex (publisher PDFs, repositories)
  3. open-access PDF links listed by Europe PMC
  4. repository copies found by CORE (only when CORE_API_KEY is set)
  5. open-access copies listed by OpenAIRE
  6. the open-access PDF link listed by Semantic Scholar
When PubMed lists no DOI for a PMID, the DOI comes from the OpenAlex record of that PMID.
Every download must start with "%PDF", whatever the source.
It never uses Sci-Hub, LibGen or similar sites, and it never tries to get past a paywall,
CAPTCHA or bot check. A free link that refuses the script is printed for a person to open.
Certificate checking is always on. When a server fails the certificate check in Python, the
same link is tried once with the system curl, also with checking on.

For a paper that did not download it prints ResearchGate and Academia.edu search links and
points to the PubMed record for the corresponding author's address. With --emails it prints
the author email addresses found in the PubMed record. Those addresses are for a full-text
request only. `import` files PDFs downloaded by hand (library, ResearchGate, an author) by
reading the DOI printed inside them.

Environment variables, all optional:
  PAPERS_DIR         folder for everything the tool saves; default: ./papers under the
                     current directory
  CORE_API_KEY       API key for core.ac.uk; without it CORE is skipped
  PAPER_FETCH_EMAIL  contact address sent to PubMed (E-utilities "email" parameter) and to
                     OpenAlex and Crossref ("mailto" parameter); sent to no other service

Every request identifies itself with one User-Agent: dental-paper-fetch/1.0 plus the
repository link.

Files go to "<PAPERS_DIR>/<Topic>/": the PDF, its BibTeX entry in references.bib, and its
figures in figures/<PMID n>/ with a figures.json that records each figure's label, caption,
page, the paper's license and whether an image model may use it. The catalog of all papers
is <PAPERS_DIR>/_index.csv.

Result lines: SAVED, EXISTS, OPEN_MANUALLY (free, but the script could not download it: a
person must open the link), NO_FREE_COPY (no free legal copy found) or NOT_FOUND.
A run of `get` or `search --download` ends with one count line, for example:
  SAVED 12: PubMed Central 10, OpenAlex 2 | OPEN_MANUALLY 8 | NO_FREE_COPY 20

Usage:
  paper_fetch.py get 35804491 10.1111/clr.13992 PMC9544523 "a title" --topic "Peri-implantitis"
  paper_fetch.py get --file ids.txt --topic "Peri-implantitis"
  paper_fetch.py get 35804491 --topic "Peri-implantitis" --emails
  paper_fetch.py search "peri-implantitis surgical" --min-year 2018 --sort cites --max 10 --free
  paper_fetch.py search "peri-implantitis surgical" --max 5 --download --topic "Peri-implantitis"
  paper_fetch.py import ~/Downloads/jcpe12345.pdf --topic "Peri-implantitis"
  paper_fetch.py import --topic "Peri-implantitis"          # lists PDFs in ~/Downloads from the last day
  paper_fetch.py import --topic "Peri-implantitis" --yes    # imports the PDFs on that list
  paper_fetch.py topics

Exit codes: 0 all saved or already there, 2 at least one paper not saved (normal, most
papers are paywalled) or `import` listed files and copied nothing, 1 error.
Needs Python 3.10 or newer and only the standard library. Figures from PDFs outside PubMed
Central need poppler (pdfimages, pdftoppm, pdftotext); without it those papers get no figures
and the tool prints once how to install it.
"""

import argparse
import collections
import csv
import difflib
import functools
import html
import http.client
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Everything is saved under PAPERS_DIR; without it, under ./papers in the current directory
ROOT = Path(os.environ.get("PAPERS_DIR") or "papers").expanduser().absolute()
INDEX_FIELDS = ["saved_at", "topic", "pmid", "pmcid", "doi", "year", "first_author",
                "journal", "title", "license", "source", "file"]
# One honest identity for every request: APIs, repositories and publisher sites alike
USER_AGENT = "dental-paper-fetch/1.0 (+https://github.com/Tuminha/dental-ai-skills)"
# Optional contact address, sent to PubMed (email), OpenAlex and Crossref (mailto) only
CONTACT = os.environ.get("PAPER_FETCH_EMAIL", "")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_S3 = "https://pmc-oa-opendata.s3.amazonaws.com"
S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
NET_ERRORS = (OSError, ValueError, http.client.HTTPException, ET.ParseError)

# Licenses that allow adapting a figure for any use, commercial included, with credit.
OPEN_LICENSES = {"CC0", "CC BY", "PUBLIC-DOMAIN"}
REUSE_NOTES = {
    "input_ok_with_credit": (
        "Open license. A figure may be given to an image model as a reference, with credit to "
        "the authors and journal and the license named. This hint is a starting point, not a "
        "rights approval: a person checks the license before anything is published."),
    "understanding_only": (
        "No open license for adaptation (NC, ND, SA, publisher terms or unknown). Look at the "
        "figures to understand the anatomy or data and describe it in your own words. Do not "
        "give these files to an image model and do not trace or copy them."),
}


class SameHostRedirects(urllib.request.HTTPRedirectHandler):
    """Refuses a redirect that leaves the host or leaves https. Used for every request that
    carries an API key, because Python copies the Authorization header to the new address."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urllib.parse.urlparse(req.full_url), urllib.parse.urlparse(newurl)
        if new.scheme != "https" or new.netloc.lower() != old.netloc.lower():
            raise urllib.error.HTTPError(
                req.full_url, code, "redirect to another host refused: the request carries an API key",
                headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url, timeout=60, tries=3, accept="*/*", headers=None):
    keyed = any(h.lower() == "authorization" for h in headers or {})
    open_url = urllib.request.build_opener(SameHostRedirects).open if keyed else urllib.request.urlopen
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": accept, **(headers or {})})
            with open_url(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == tries - 1:
                raise
        time.sleep(2 * (attempt + 1))


def get_json(url, tries=3):
    return json.loads(http_get(url, tries=tries))


def with_mailto(url):
    return url + ("&" if "?" in url else "?") + "mailto=" + urllib.parse.quote(CONTACT) if CONTACT else url


def eutils(tool, **params):
    params.setdefault("retmode", "json")
    params.update(db="pubmed", tool="dental-paper-fetch", **({"email": CONTACT} if CONTACT else {}))
    time.sleep(0.34)  # NCBI allows 3 requests per second without an API key
    url = f"{EUTILS}/{tool}.fcgi?" + urllib.parse.urlencode(params)
    return get_json(url) if params["retmode"] == "json" else http_get(url)


def clean_text(text):
    text = html.unescape(re.sub(r"<[^>]+>", "", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def safe_name(text):
    return re.sub(r"\s+", " ", re.sub(r'[/\\:*?"<>|]', " ", clean_text(text))).strip(" .")


def similarity(a, b):
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower())
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def norm_license(value):
    """'cc-by-nc-nd', 'cc by', 'CC BY-NC' -> 'CC BY-NC-ND', 'CC BY', 'CC BY-NC'."""
    s = (value or "").strip().lower().replace("_", "-")
    if s in ("cc0", "cc-zero", "cc0-1.0"):
        return "CC0"
    m = re.fullmatch(r"cc[- ]?(by(?:[- ](?:nc|nd|sa))*)(?:[- ][\d.]+)?", s)
    return "CC " + m.group(1).replace(" ", "-").upper() if m else s.upper()


# ---------- resolving an identifier to paper metadata ----------

def pubmed_search(term, n, sort="relevance"):
    r = eutils("esearch", term=term, retmax=n, sort=sort)["esearchresult"]
    return r.get("idlist", []), int(r.get("count", 0))


def pubmed_papers(pmids):
    if not pmids:
        return []
    res = eutils("esummary", id=",".join(pmids))["result"]
    papers = []
    for uid in res.get("uids", []):
        r = res[uid]
        if "error" in r:  # PubMed answers an unknown PMID with an error record
            continue
        ids = {a["idtype"]: a["value"] for a in r.get("articleids", [])}
        authors = r.get("authors") or []
        papers.append({
            "pmid": uid,
            "pmcid": ids.get("pmc", ""),
            "doi": ids.get("doi", "").lower(),
            "title": clean_text(r.get("title")).rstrip("."),
            "journal": r.get("source", ""),
            "year": (r.get("pubdate") or "")[:4],
            # PubMed names look like "Liu Z" or "van der Berg J": drop the initials
            "first_author": authors[0]["name"].rsplit(" ", 1)[0] if authors else "",
        })
    return papers


OPENALEX = {}  # DOI -> OpenAlex record (or None), so each paper costs one OpenAlex call


def openalex_work(doi):
    """OpenAlex record for a DOI, or None when it is unknown or OpenAlex is unreachable."""
    if doi not in OPENALEX:
        try:
            OPENALEX[doi] = get_json(with_mailto(
                "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/()")))
        except NET_ERRORS:
            OPENALEX[doi] = None
    return OPENALEX[doi]


def doi_from_openalex(paper):
    """PubMed lists no DOI for some papers. Ask OpenAlex for the PMID, take the DOI from that
    record and keep the record, so the open-access lookup that follows asks nothing again."""
    if not paper or paper["doi"] or not paper["pmid"]:
        return paper
    try:
        w = get_json(with_mailto("https://api.openalex.org/works/pmid:" + paper["pmid"]))
    except NET_ERRORS:
        return paper
    doi = re.sub(r"(?i)^https?://(dx\.)?doi\.org/", "", w.get("doi") or "").lower()
    same_pmid = re.sub(r"\D", "", (w.get("ids") or {}).get("pmid") or "") == paper["pmid"]
    if doi and same_pmid and similarity(paper["title"], clean_text(w.get("title"))) > 0.8:
        paper["doi"] = doi
        OPENALEX[doi] = w
    return paper


def paper_from_openalex(w, doi):
    ids = w.get("ids") or {}
    source = ((w.get("primary_location") or {}).get("source") or {})
    authors = w.get("authorships") or []
    return {
        "pmid": re.sub(r"\D", "", ids.get("pmid", "")),
        "pmcid": (re.search(r"PMC\d+", ids.get("pmcid", "")) or [""])[0],
        "doi": doi,
        "title": clean_text(w.get("title")).rstrip("."),
        "journal": source.get("display_name", ""),
        "year": str(w.get("publication_year") or ""),
        "first_author": " ".join((authors[0]["author"].get("display_name") or "").split()[-1:])
        if authors else "",
    }


def resolve_doi(doi):
    pmids, _ = pubmed_search(f"{doi}[doi]", 1)
    papers = [p for p in pubmed_papers(pmids) if p["doi"] == doi]
    if papers:
        return papers[0]
    w = openalex_work(doi)  # not in PubMed: fall back to OpenAlex metadata
    return paper_from_openalex(w, doi) if w else None


def crossref_doi(title):
    try:
        r = get_json(with_mailto("https://api.crossref.org/works?" + urllib.parse.urlencode(
            {"query.bibliographic": title, "rows": 1, "select": "DOI"})))
        items = r["message"]["items"]
        return items[0]["DOI"].lower() if items else ""
    except NET_ERRORS + (KeyError,):
        return ""


def resolve(ident):
    """Return (paper, note). paper is None when nothing matches."""
    s = ident.strip()
    doi_match = re.search(r"10\.\d{4,9}/\S+", s)
    if re.fullmatch(r"\d{1,9}", s):
        papers = pubmed_papers([s])
        return doi_from_openalex(papers[0] if papers else None), ""
    if re.fullmatch(r"(?i)pmc\d+", s):
        pmids, _ = pubmed_search(f"{s.upper()}[pmcid]", 1)
        papers = pubmed_papers(pmids)
        return doi_from_openalex(papers[0] if papers and papers[0]["pmcid"] == s.upper() else None), ""
    if doi_match:
        return resolve_doi(doi_match.group(0).rstrip(".").lower()), ""
    # A title: PubMed first, Crossref for papers outside PubMed; keep the closer match
    candidates = pubmed_papers(pubmed_search(f"{s}[ti]", 1)[0])
    doi = crossref_doi(s)
    if doi and not any(p["doi"] == doi for p in candidates):
        found = resolve_doi(doi)
        if found:
            candidates.append(found)
    if not candidates:
        return None, ""
    best = max(candidates, key=lambda p: similarity(s, p["title"]))
    note = "" if similarity(s, best["title"]) > 0.8 else f'CHECK  title search matched "{best["title"]}"'
    return doi_from_openalex(best), note


# ---------- finding a free legal PDF ----------

@functools.lru_cache(maxsize=None)
def pmc_latest(pmcid):
    """(version folder, its keys) in the PMC open-access bucket: the newest version that holds
    the article PDF, or the newest version when none holds it. A later version can be an
    author manuscript with text only. The PDF, the figures and the license all come from
    the folder chosen here."""
    xml = http_get(f"{PMC_S3}/?list-type=2&prefix={pmcid}.&max-keys=1000")
    versions = {}
    for k in ET.fromstring(xml).iterfind(".//s3:Key", S3_NS):
        m = re.fullmatch(rf"{pmcid}\.(\d+)/.+", k.text)
        if m:
            versions.setdefault(int(m.group(1)), []).append(k.text)
    if not versions:
        return None, ()
    with_pdf = [v for v in versions if f"{pmcid}.{v}/{pmcid}.{v}.pdf" in versions[v]]
    v = max(with_pdf or versions)
    return f"{pmcid}.{v}", tuple(versions[v])


@functools.lru_cache(maxsize=None)
def europepmc_record(doi, pmid):
    query = f'DOI:"{doi}"' if doi else f"EXT_ID:{pmid} AND SRC:MED"
    try:
        r = get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
            {"query": query, "resultType": "core", "format": "json"}))
        return (r.get("resultList", {}).get("result") or [{}])[0]
    except NET_ERRORS:
        return {}


def semantic_scholar_pdf(paper):
    ref = f"DOI:{paper['doi']}" if paper["doi"] else f"PMID:{paper['pmid']}"
    try:  # one try only: the free tier answers 429 when busy
        r = get_json("https://api.semanticscholar.org/graph/v1/paper/"
                     + urllib.parse.quote(ref, safe=":/()") + "?fields=openAccessPdf", tries=1)
        return (r.get("openAccessPdf") or {}).get("url") or ""
    except NET_ERRORS:
        return ""


def core_pdfs(paper):
    """PDF links from CORE (core.ac.uk), which gathers copies from university repositories.
    Needs an API key in CORE_API_KEY; without one CORE is skipped."""
    key = os.environ.get("CORE_API_KEY")
    if not key or not (paper["doi"] or paper["title"]):
        return []
    q = f'doi:"{paper["doi"]}"' if paper["doi"] else f'title:"{paper["title"]}"'
    try:
        r = json.loads(http_get("https://api.core.ac.uk/v3/search/works/?" + urllib.parse.urlencode(
            {"q": q, "limit": 3}), headers={"Authorization": f"Bearer {key}"}, tries=2))
    except NET_ERRORS:
        return []
    urls = []
    for w in r.get("results", []):
        if not paper["doi"] and similarity(paper["title"], w.get("title") or "") < 0.9:
            continue
        urls += [w.get("downloadUrl")] + [l.get("url") for l in w.get("links") or []
                                          if l.get("type") == "download"]
    return [u for u in dict.fromkeys(urls) if u]


def openaire_pdfs(paper):
    """Links to open-access copies listed by OpenAIRE, found by DOI (Graph API, version 3).
    Only instances marked open access count, and only in a record that carries this DOI.
    One try and no key: the OpenAIRE terms of use allow 60 calls per hour without a token
    (checked 2026-09-30). An error answer, for example past that limit, skips OpenAIRE for
    that paper."""
    if not paper["doi"]:
        return []
    urls = []
    try:
        r = get_json("https://api.openaire.eu/graph/v3/research-products?" + urllib.parse.urlencode(
            {"pid": paper["doi"], "pageSize": 3}), tries=1)
        for product in r.get("results") or []:
            if not any(p.get("scheme") == "doi" and (p.get("value") or "").lower() == paper["doi"]
                       for p in product.get("pids") or []):
                continue
            for instance in product.get("instances") or []:
                if (instance.get("accessRight") or {}).get("label") == "OPEN":
                    urls += instance.get("urls") or []
    except NET_ERRORS + (AttributeError, TypeError):
        return []
    # A PubMed record page is an abstract, not a copy of the paper
    return [u for u in dict.fromkeys(urls)
            if u and urllib.parse.urlparse(u).netloc != "pubmed.ncbi.nlm.nih.gov"]


def author_emails(pmid):
    """Author email addresses printed in the PubMed record (usually the corresponding author)."""
    if not pmid:
        return []
    try:
        xml = eutils("efetch", id=pmid, retmode="xml").decode("utf-8", "replace")
    except NET_ERRORS:
        return []
    return list(dict.fromkeys(e.rstrip(".") for e in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", xml)))


def pdf_candidates(paper):
    """Yield (source label, url) in order of preference."""
    if paper["pmcid"]:
        try:
            folder, keys = pmc_latest(paper["pmcid"])
            if folder and f"{folder}/{folder}.pdf" in keys:
                # The folder also holds supplement PDFs; the article is named after the PMCID
                yield "PubMed Central open-access copy", f"{PMC_S3}/{folder}/{folder}.pdf"
        except NET_ERRORS:
            pass
    w = openalex_work(paper["doi"]) if paper["doi"] else None
    for loc in [(w or {}).get("best_oa_location")] + ((w or {}).get("locations") or []):
        url = loc and loc.get("is_oa") and (loc.get("pdf_url") or loc.get("landing_page_url"))
        if url:
            yield f"open-access copy via OpenAlex ({urllib.parse.urlparse(url).netloc})", url
    if paper["doi"] or paper["pmid"]:
        for u in europepmc_record(paper["doi"], paper["pmid"]).get("fullTextUrlList", {}).get("fullTextUrl", []):
            if u.get("documentStyle") == "pdf" and u.get("availability") in ("Open access", "Free"):
                yield "open-access copy via Europe PMC", u["url"]
    for url in core_pdfs(paper):
        yield "open-access copy via CORE", url
    for url in openaire_pdfs(paper):
        yield "open-access copy via OpenAIRE", url
    if paper["doi"] or paper["pmid"]:
        s2 = semantic_scholar_pdf(paper)
        if s2:
            yield "open-access copy via Semantic Scholar", s2


def is_certificate_error(error):
    """True when the server failed the certificate check, for example an incomplete chain."""
    return isinstance(error, ssl.SSLCertVerificationError) or \
        isinstance(getattr(error, "reason", None), ssl.SSLCertVerificationError)


def curl_get(url, timeout=120):
    """One download with the system curl, certificate checking ON. /usr/bin/curl comes first:
    on macOS that build completes a chain when a server leaves out an intermediate
    certificate, which Python cannot. -q in first place skips any curl config file, so no
    setting from there can switch the check off. --retry 1 repeats the transfer once after
    a timeout or a 5xx answer, because the one publisher seen with this fault takes 30 to
    60 seconds per PDF. Returns b"" when curl is missing or fails."""
    curl = shutil.which("curl", path="/usr/bin") or shutil.which("curl")
    if not curl or not url.lower().startswith("https://"):
        return b""
    try:
        done = subprocess.run([curl, "-q", "-sSL", "--retry", "1", "--max-time", str(timeout),
                               "-A", USER_AGENT, url], capture_output=True, timeout=2 * timeout + 10)
    except (subprocess.SubprocessError, OSError):
        return b""
    return done.stdout if done.returncode == 0 else b""


def fetch(url):
    """Return (bytes, certificate problem). The second value is True when the server failed
    the certificate check and the one retry with curl brought nothing either."""
    try:
        return http_get(url, timeout=120, tries=1), False
    except NET_ERRORS as error:
        if not is_certificate_error(error):
            return b"", False
    data = curl_get(url)
    return data, not data


def download_pdf(paper):
    """Return (pdf bytes, source label, url, free links that failed).

    Each failed link is (url, certificate problem). Free links fail when the site answers
    with a bot check or 403, or when its certificate fails the check. Those are left for a
    person to open in a browser; this script never tries to get past a bot check.
    """
    tried, failed = set(), []
    for label, url in pdf_candidates(paper):
        if url in tried:
            continue
        tried.add(url)
        data, certificate_problem = fetch(url)
        if data and not data.startswith(b"%PDF"):
            # Journal and repository landing pages name their PDF in a standard meta tag
            for tag in re.findall(rb"<meta[^>]*citation_pdf_url[^>]*>", data, re.I)[:1]:
                m = re.search(rb'content="([^"]+)"', tag)
                pdf_url = m and urllib.parse.urljoin(url, html.unescape(m.group(1).decode()))
                if pdf_url and pdf_url not in tried:
                    tried.add(pdf_url)
                    data, certificate_problem = fetch(pdf_url)
        if data.startswith(b"%PDF"):
            return data, label, url, []
        failed.append((url, certificate_problem))
    return None, None, None, failed


def open_manually_lines(failed):
    """The lines printed under OPEN_MANUALLY: the reason, then at most 3 links."""
    shown = failed[:3]
    if all(certificate_problem for _, certificate_problem in shown):
        lines = ["Free to read, but the server has a certificate problem, so the script did not "
                 "download it.",
                 "Open in a browser. If the browser shows a security warning, do not continue:"]
        return lines + [url for url, _ in shown]
    return ["Free to read, but the site blocks download scripts. Open in a browser:"] + [
        url + ("  (this server has a certificate problem)" if certificate_problem else "")
        for url, certificate_problem in shown]


def lookup_license(paper):
    """The article's license as 'CC BY', 'CC BY-NC', ... or '' when nobody states one."""
    if paper["pmcid"]:
        try:
            folder, keys = pmc_latest(paper["pmcid"])
            if folder and f"{folder}/{folder}.json" in keys:
                lic = norm_license(get_json(f"{PMC_S3}/{folder}/{folder}.json").get("license_code"))
                if lic:
                    return lic
        except NET_ERRORS:
            pass
    w = openalex_work(paper["doi"]) if paper["doi"] else None
    lic = norm_license(((w or {}).get("best_oa_location") or {}).get("license"))
    if lic or not (paper["doi"] or paper["pmid"]):
        return lic
    return norm_license(europepmc_record(paper["doi"], paper["pmid"]).get("license"))


# ---------- figures ----------

FIG_LABEL = re.compile(
    r"(?im)^[ \t]*(?:f[ \t]?i[ \t]?g[ \t]?u[ \t]?r[ \t]?e|fig\.?)[ \t]*([a-z]?\d{1,2}[a-z]?)\b[ \t.:|]*(.*)$")


# PubMed Central stores the figures of recent papers as WebP
PMC_IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".webp")
POPPLER_TIMEOUT = 120  # seconds for one poppler call on one PDF
POPPLER_HELP = ("poppler is not installed, so no figures were taken from this PDF. Install it: "
                "brew install poppler (macOS), apt install poppler-utils (Debian, Ubuntu)")
notes_printed = set()


def print_once(text):
    if text not in notes_printed:
        notes_printed.add(text)
        print(f"       {text}")


def local(tag):
    return tag.rsplit("}", 1)[-1]


def pmc_figures(pmcid, dest):
    """Figure images with labels and captions from the PMC open-access article XML."""
    folder, keys = pmc_latest(pmcid)
    if not folder or f"{folder}/{folder}.xml" not in keys:
        return []
    root = ET.fromstring(http_get(f"{PMC_S3}/{folder}/{folder}.xml"))
    images = {k.rsplit("/", 1)[1].rsplit(".", 1)[0]: k for k in keys
              if k.lower().endswith(PMC_IMAGE_TYPES)}
    figures = []
    for n, fig in enumerate((e for e in root.iter() if local(e.tag) == "fig"), 1):
        part = lambda name: next((e for e in fig.iter() if local(e.tag) == name), None)
        label = clean_text(" ".join(part("label").itertext())) if part("label") is not None else f"Figure {n}"
        caption = clean_text(" ".join(part("caption").itertext())) if part("caption") is not None else ""
        graphic = part("graphic")
        href = graphic is not None and next((v for k, v in graphic.attrib.items() if local(k) == "href"), "")
        key = href and (images.get(href) or images.get(href.rsplit(".", 1)[0]))
        if not key:
            continue
        name = f"{safe_name(label)} - {safe_name(caption)[:60]}".rstrip(" -.,") + Path(key).suffix.lower()
        (dest / name).write_bytes(http_get(f"{PMC_S3}/{key}"))
        figures.append({"file": name, "label": label, "caption": caption, "page": None,
                        "kind": "figure image from PubMed Central"})
    return figures


def pdf_captions(pdf):
    """{page: [(label, caption)]} for figure captions found in the PDF text."""
    pages = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True,
                           check=True, timeout=POPPLER_TIMEOUT).stdout.split("\f")
    captions, seen = {}, set()
    for page, text in enumerate(pages, 1):
        for m in FIG_LABEL.finditer(text):
            label, first = f"Figure {m.group(1).upper()}", m.group(2).strip()
            # A caption starts with a capital or digit; "Figure 2 shows ..." is running text
            if label in seen or not first[:1].isupper() and not first[:1].isdigit():
                continue
            caption = first
            for line in text[m.end():].splitlines()[1:]:
                if not line.strip() or len(caption) > 300:
                    break
                caption += " " + line.strip()
            seen.add(label)
            captions.setdefault(page, []).append((label, clean_text(caption)))
    return captions


def pdf_figures(pdf, dest):
    """Figures from any PDF with poppler: embedded pictures, plus a render of each page with
    a figure caption, because charts are often vector drawings that pdfimages cannot see."""
    if not all(shutil.which(t) for t in ("pdfimages", "pdftoppm", "pdftotext")):
        print_once(POPPLER_HELP)
        return []
    run = lambda *cmd: subprocess.run(cmd, capture_output=True, text=True, check=True,
                                      timeout=POPPLER_TIMEOUT).stdout
    captions = pdf_captions(pdf)
    on_page = lambda p: (", ".join(l for l, _ in captions.get(p, [])),
                         " | ".join(c for _, c in captions.get(p, [])))
    figures = []
    with tempfile.TemporaryDirectory() as tmp:
        keep, objects = set(), set()
        for line in run("pdfimages", "-list", str(pdf)).splitlines()[2:]:
            c = line.split()
            # Skip logos and page banners (small) and repeats of the same image object
            if len(c) > 11 and c[2] == "image" and int(c[3]) >= 300 and int(c[4]) >= 300 \
                    and c[10] not in objects:
                keep.add(int(c[1]))
                objects.add(c[10])
        if keep:
            run("pdfimages", "-all", "-p", str(pdf), f"{tmp}/img")
            for f in sorted(Path(tmp).glob("img-*")):
                m = re.fullmatch(r"img-(\d+)-(\d+)\.(\w+)", f.name)
                if not m or int(m.group(2)) not in keep:
                    continue
                page = int(m.group(1))
                labels, caption = on_page(page)
                name = f"Page {page} picture {int(m.group(2))}{' - ' + labels if labels else ''}.{m.group(3)}"
                shutil.move(str(f), dest / name)
                figures.append({"file": name, "label": labels, "caption": caption, "page": page,
                                "kind": "picture embedded in the PDF"})
        for page in sorted(captions):
            run("pdftoppm", "-r", "150", "-png", "-singlefile", "-f", str(page), "-l", str(page),
                str(pdf), f"{tmp}/page")
            labels, caption = on_page(page)
            name = f"Page {page} - {labels}.png"
            shutil.move(f"{tmp}/page.png", dest / name)
            figures.append({"file": name, "label": labels, "caption": caption, "page": page,
                            "kind": "whole page render (shows charts drawn as vectors)"})
    return figures


def citation(paper):
    parts = [f"{paper['first_author']} et al" if paper["first_author"] else "", paper["title"],
             paper["journal"], paper["year"],
             f"PMID {paper['pmid']}" if paper["pmid"] else "",
             f"doi:{paper['doi']}" if paper["doi"] else ""]
    return ". ".join(p for p in parts if p) + "."


def extract_figures(paper, pdf):
    """Write figures/<tag>/ once per paper. Returns (folder, figures.json content)."""
    dest = pdf.parent / "figures" / file_tag(paper)
    meta_file = dest / "figures.json"
    if meta_file.exists():
        return dest, json.loads(meta_file.read_text(encoding="utf-8"))
    dest.mkdir(parents=True, exist_ok=True)
    figures = []
    if paper["pmcid"]:
        try:
            figures = pmc_figures(paper["pmcid"], dest)
        except NET_ERRORS:
            figures = []
    if not figures:
        try:
            figures = pdf_figures(pdf, dest)
        except (subprocess.SubprocessError, OSError):  # a poppler error or its time limit
            figures = []
    lic = lookup_license(paper)
    hint = "input_ok_with_credit" if lic in OPEN_LICENSES else "understanding_only"
    meta = {"paper": {k: paper[k] for k in ("pmid", "pmcid", "doi", "year", "first_author",
                                            "journal", "title")},
            "citation": citation(paper), "pdf": pdf.name, "license": lic or "unknown",
            "reuse_hint": hint, "reuse_note": REUSE_NOTES[hint], "figures": figures}
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return dest, meta


def report_figures(paper, pdf):
    dest, meta = extract_figures(paper, pdf)
    print(f"       figures: {len(meta['figures'])} in {dest}/ | license {meta['license']} "
          f"-> {meta['reuse_hint']}")


# ---------- storage ----------

def topic_dir(topic):
    name = safe_name(topic)
    if not name:
        sys.exit("error: --topic is empty")
    if ROOT.exists():
        for d in ROOT.iterdir():  # reuse an existing folder with different capitals
            if d.is_dir() and d.name.lower() == name.lower():
                return d
    return ROOT / (name[0].upper() + name[1:])


def make_folder(folder):
    """Create a topic folder. Prints one line when the papers folder itself is new."""
    new_root = not ROOT.exists()
    folder.mkdir(parents=True, exist_ok=True)
    if new_root:
        print(f"Created the papers folder: {ROOT}  (set PAPERS_DIR to use another one)")


def file_tag(paper):
    return f"PMID {paper['pmid']}" if paper["pmid"] else "DOI " + re.sub(r"[^\w.-]+", "_", paper["doi"])


def pdf_name(paper):
    title = safe_name(paper["title"])[:90].rstrip(" .,-")
    return f"{paper['year'] or 'n.d.'} {safe_name(paper['first_author']) or 'Unknown'} - {title} [{file_tag(paper)}].pdf"


def find_existing(paper):
    if not ROOT.exists():
        return None
    tag = f"[{file_tag(paper)}]"
    for d in ROOT.iterdir():
        if d.is_dir():
            for f in d.iterdir():
                if tag in f.name and f.suffix.lower() == ".pdf":
                    return f
    return None


def in_index(paper):
    index = ROOT / "_index.csv"
    if not index.exists():
        return False
    with open(index, newline="", encoding="utf-8") as fh:
        return any(paper["pmid"] and r.get("pmid") == paper["pmid"]
                   or paper["doi"] and r.get("doi") == paper["doi"] for r in csv.DictReader(fh))


def index_paper(paper, path, source):
    append_index({"saved_at": datetime.now().isoformat(timespec="seconds"),
                  "topic": path.parent.name, "file": str(path.relative_to(ROOT)),
                  "source": source, "license": lookup_license(paper), **paper})


def append_index(row):
    index = ROOT / "_index.csv"
    old = []  # rows to rewrite: none for a new file, all of them after a column change
    if index.exists():
        with open(index, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            old = list(reader) if reader.fieldnames != INDEX_FIELDS else None
    with open(index, "a" if old is None else "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=INDEX_FIELDS, restval="", extrasaction="ignore")
        if old is not None:
            writer.writeheader()
            writer.writerows(old)
        writer.writerow(row)


def append_bibtex(paper, folder):
    """Add the paper's BibTeX entry (from doi.org) to <Topic>/references.bib once."""
    bib = folder / "references.bib"
    if not paper["doi"] or bib.exists() and paper["doi"] in bib.read_text(encoding="utf-8").lower():
        return
    try:
        entry = http_get("https://doi.org/" + urllib.parse.quote(paper["doi"], safe="/()"),
                         accept="application/x-bibtex", tries=2).decode("utf-8", "replace").strip()
    except NET_ERRORS:
        return
    if entry.startswith("@"):
        with open(bib, "a", encoding="utf-8") as fh:
            fh.write(entry + "\n\n")


def describe(paper):
    parts = [f"PMID {paper['pmid']}" if paper["pmid"] else "",
             f"DOI {paper['doi']}" if paper["doi"] else "",
             f"{paper['year']} {paper['first_author']}".strip()]
    return " | ".join(p for p in parts if p)


# ---------- commands ----------

def get_one(ident, topic, with_figures=True, show_emails=False):
    """Fetch one paper and print its result line. Returns (result, source): the result is
    SAVED, EXISTS, OPEN_MANUALLY, NO_FREE_COPY or NOT_FOUND; the source is named for SAVED."""
    paper, note = resolve(ident)
    if not paper:
        print(f'NOT_FOUND  "{ident}"')
        return "NOT_FOUND", ""
    if note:
        print(note)
    existing = find_existing(paper)
    if existing:
        print(f"EXISTS  {existing}")
        if not in_index(paper):  # a PDF saved by hand after OPEN_MANUALLY or NO_FREE_COPY
            index_paper(paper, existing, "saved by hand")
        append_bibtex(paper, existing.parent)
        if with_figures:
            report_figures(paper, existing)
        return "EXISTS", ""
    data, source, url, failed = download_pdf(paper)
    folder = topic_dir(topic)
    if not data:
        if failed:
            print(f"OPEN_MANUALLY  {describe(paper)} | {paper['title']}")
            for line in open_manually_lines(failed):
                print(f"       {line}")
        else:
            link = f"https://doi.org/{paper['doi']}" if paper["doi"] else \
                f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"
            print(f"NO_FREE_COPY  {describe(paper)} | {paper['title']}\n"
                  f"       No free legal copy found. Get it with your own access: {link}")
        q = urllib.parse.quote(paper["title"])
        print(f"       ResearchGate: https://www.researchgate.net/search/publication?q={q}")
        print(f"       Academia.edu: https://www.academia.edu/search?q={q}")
        # The extra PubMed lookup for addresses runs only when --emails asks for it
        emails = author_emails(paper["pmid"]) if show_emails else []
        if emails:
            print(f"       Ask the authors: {', '.join(emails[:3])}")
        elif paper["pmid"]:
            print(f"       Corresponding author address: see "
                  f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/")
        print(f"       Then save it in: {folder}/ with \"[{file_tag(paper)}]\" in the file name,\n"
              f"       or download it anywhere and run: "
              f"python3 paper_fetch.py import <file.pdf> --topic \"{folder.name}\"")
        return ("OPEN_MANUALLY" if failed else "NO_FREE_COPY"), ""
    make_folder(folder)
    path = folder / pdf_name(paper)
    path.write_bytes(data)
    index_paper(paper, path, url)
    append_bibtex(paper, folder)
    print(f"SAVED  {path}\n       {describe(paper)} | {len(data) // 1024} KB | {source}")
    if with_figures:
        report_figures(paper, path)
    # "open-access copy via OpenAlex (host)" -> "OpenAlex"
    return "SAVED", re.sub(r"^open-access copy via | open-access copy$| \(.*\)$", "", source)


def count_line(results):
    """'SAVED 12: PubMed Central 10, OpenAlex 2 | OPEN_MANUALLY 8 | NO_FREE_COPY 20'.
    EXISTS and NOT_FOUND are added only when they happened."""
    counts = collections.Counter(result for result, _ in results)
    sources = collections.Counter(source for result, source in results if result == "SAVED")
    saved = f"SAVED {counts['SAVED']}"
    if sources:
        saved += ": " + ", ".join(f"{name} {n}" for name, n in sources.most_common())
    parts = [saved]
    if counts["EXISTS"]:
        parts.append(f"EXISTS {counts['EXISTS']}")
    parts += [f"OPEN_MANUALLY {counts['OPEN_MANUALLY']}", f"NO_FREE_COPY {counts['NO_FREE_COPY']}"]
    if counts["NOT_FOUND"]:
        parts.append(f"NOT_FOUND {counts['NOT_FOUND']}")
    return " | ".join(parts)


def finish_run(results):
    """Print the count line and return the exit code: 0 when every paper is on disk, else 2."""
    print(count_line(results))
    return 0 if all(result in ("SAVED", "EXISTS") for result, _ in results) else 2


def cmd_get(args):
    ids = list(args.ids)
    if args.file:
        lines = Path(args.file).expanduser().read_text(encoding="utf-8").splitlines()
        ids += [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    if not ids:
        sys.exit("error: give at least one PMID, DOI, PMCID or title, or --file")
    return finish_run([get_one(i, args.topic, not args.no_figures, args.emails) for i in ids])


DOI_IN_TEXT = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.I)


def doi_in_pdf(pdf):
    """The first DOI in the PDF's metadata or on its first two pages, or ''."""
    for cmd in (["pdfinfo", str(pdf)], ["pdftotext", "-l", "2", str(pdf), "-"]):
        if not shutil.which(cmd[0]):
            continue
        try:
            text = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
        except (subprocess.SubprocessError, OSError):
            continue
        m = DOI_IN_TEXT.search(text)
        if m:
            return m.group(1).rstrip(".,;)]").lower()
    return ""


def cmd_import(args):
    """File PDFs the user downloaded by hand (library, ResearchGate, an author)."""
    if not shutil.which("pdftotext"):
        sys.exit("error: import reads the DOI with poppler; install it with: brew install poppler")
    files = [Path(f).expanduser() for f in args.files]
    if not files:
        downloads = Path.home() / "Downloads"
        cutoff = time.time() - args.days * 86400
        files = sorted(f for f in downloads.glob("*.pdf") if f.stat().st_mtime >= cutoff)
        if files and not args.yes:
            # No file was named: show the list and stop. A personal document that cites a
            # paper has a DOI inside too, and would be filed under that paper.
            print(f"DRY_RUN  {len(files)} PDF file(s) in {downloads} from the last {args.days:g} "
                  f"day(s). Nothing was {'moved' if args.move else 'copied'}.")
            for f in files:
                doi = doi_in_pdf(f)
                print(f"       WOULD_IMPORT  {f} | DOI inside: {doi}" if doi else
                      f"       NO_DOI        {f} | no DOI inside, it would be skipped")
            print("       Check the list: a personal document that cites a paper has a DOI inside too.\n"
                  "       Then name the files to import, or run the same command with --yes.")
            return 2
    ok = True
    for f in files:
        try:
            with open(f, "rb") as fh:
                is_pdf = fh.read(5).startswith(b"%PDF")
        except OSError as e:
            print(f"UNREADABLE  {f}  ({e.strerror})")
            ok = False
            continue
        if not is_pdf:
            print(f"NOT_A_PDF  {f}")
            ok = False
            continue
        doi = doi_in_pdf(f)
        paper = resolve_doi(doi) if doi else None
        if not paper:
            print(f"NO_DOI  {f}\n       No readable DOI. Rename it with \"[PMID n]\", put it in the topic "
                  f"folder, then run: python3 paper_fetch.py get <PMID> --topic \"{args.topic}\"")
            ok = False
            continue
        existing = find_existing(paper)
        if existing:
            print(f"EXISTS  {existing}  (left {f.name} where it is)")
            continue
        folder = topic_dir(args.topic)
        make_folder(folder)
        path = folder / pdf_name(paper)
        (shutil.move if args.move else shutil.copy2)(str(f), path)
        index_paper(paper, path, "imported: " + f.name)
        append_bibtex(paper, folder)
        print(f"IMPORTED  {path}\n       {describe(paper)} | from {f}")
        if not args.no_figures:
            report_figures(paper, path)
    return 0 if ok else 2


def openalex_cites(pmids):
    """{pmid: citation count} from OpenAlex (at most 100 PMIDs per call)."""
    if not pmids:
        return {}
    try:
        r = get_json(with_mailto("https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"filter": "pmid:" + "|".join(pmids[:100]), "select": "ids,cited_by_count",
             "per-page": 100})))
    except NET_ERRORS:
        return {}
    return {re.sub(r"\D", "", (w.get("ids") or {}).get("pmid", "")): w.get("cited_by_count", 0)
            for w in r.get("results", [])}


def cmd_search(args):
    if args.download and not args.topic:
        sys.exit("error: --download needs --topic")
    parts = [f"({args.query})"]
    if args.free:
        parts.append("free full text[sb]")
    if args.min_year:
        parts.append(f'("{args.min_year}"[dp] : "3000"[dp])')
    if args.journal:
        parts.append(f'"{args.journal}"[journal]')
    term = " AND ".join(parts)
    # Citation order needs a bigger pool first; OpenAlex counts citations, PubMed does not
    pool = min(args.max * 5, 100) if args.sort == "cites" else args.max
    pmids, count = pubmed_search(term, pool, sort="pub_date" if args.sort == "date" else "relevance")
    papers = pubmed_papers(pmids)
    cites = openalex_cites([p["pmid"] for p in papers])
    if args.sort == "cites":
        papers.sort(key=lambda p: cites.get(p["pmid"], -1), reverse=True)
    papers = papers[:args.max]
    print(f"{count} PubMed results for: {term}")
    print(f"{'PMID':>9}  year  cites  PMC  {'first author':<18}  {'journal':<22}  title")
    for p in papers:
        print(f"{p['pmid']:>9}  {p['year']:4}  {cites.get(p['pmid'], ''):>5}  "
              f"{'PMC' if p['pmcid'] else '   '}  {p['first_author'][:18]:<18}  "
              f"{p['journal'][:22]:<22}  {p['title']}")
    if not args.download:
        return 0
    print()
    return finish_run([get_one(p["pmid"], args.topic, not args.no_figures, args.emails) for p in papers])


def cmd_topics(args):
    print(ROOT)
    if ROOT.exists():
        for d in sorted(ROOT.iterdir()):
            if d.is_dir():
                print(f"  {sum(1 for f in d.iterdir() if f.suffix.lower() == '.pdf'):>4}  {d.name}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    emails_help = ("for a paper that did not download, print the author email addresses from "
                   "PubMed (for a full-text request only); default: print the PubMed link")
    g = sub.add_parser("get", help="download papers by PMID, DOI, PMCID or title")
    g.add_argument("ids", nargs="*")
    g.add_argument("--file", help="text file with one PMID, DOI, PMCID or title per line")
    g.add_argument("--topic", required=True, help='topic folder, e.g. "Peri-implantitis"')
    g.add_argument("--no-figures", action="store_true", help="skip figure extraction")
    g.add_argument("--emails", action="store_true", help=emails_help)
    s = sub.add_parser("search", help="search PubMed and list (or download) matching papers")
    s.add_argument("query")
    s.add_argument("--max", type=int, default=10)
    s.add_argument("--free", action="store_true", help="only papers with free full text")
    s.add_argument("--min-year", type=int, help="only papers published in or after this year")
    s.add_argument("--journal", help='only this journal, e.g. "J Clin Periodontol"')
    s.add_argument("--sort", choices=["relevance", "date", "cites"], default="relevance")
    s.add_argument("--download", action="store_true", help="also download the listed papers")
    s.add_argument("--topic", help="topic folder for --download")
    s.add_argument("--no-figures", action="store_true", help="skip figure extraction")
    s.add_argument("--emails", action="store_true", help=emails_help)
    i = sub.add_parser("import", help="file PDFs you downloaded yourself, found by the DOI inside them")
    i.add_argument("files", nargs="*", help="PDF files; none = list the PDFs in ~/Downloads from the "
                                            "last --days and copy nothing, unless --yes is given")
    i.add_argument("--topic", required=True)
    i.add_argument("--days", type=float, default=1)
    i.add_argument("--yes", action="store_true",
                   help="with no file names: import the listed PDFs from ~/Downloads")
    i.add_argument("--move", action="store_true", help="move instead of copy")
    i.add_argument("--no-figures", action="store_true", help="skip figure extraction")
    sub.add_parser("topics", help="list topic folders and how many PDFs each holds")
    args = ap.parse_args()
    try:
        return {"get": cmd_get, "search": cmd_search, "import": cmd_import,
                "topics": cmd_topics}[args.cmd](args)
    except NET_ERRORS as e:
        print(f"error: network problem or bad answer from PubMed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
