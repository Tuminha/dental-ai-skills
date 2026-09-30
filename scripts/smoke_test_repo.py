#!/usr/bin/env python3
"""Repository smoke tests for dental-ai-skills.

These tests intentionally use only the Python standard library so they can run
in Claude Code, Codex, CI, or a minimal local checkout.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import ssl
import subprocess
import sys
import tempfile
import types
import urllib.error
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPER_FETCH = "dental-paper-fetch/scripts/paper_fetch.py"
PROTOCOL_VERSION = "2026.05.16"
REQUIRED_SKILLS = {
    "dental-author-disclosures",
    "clinical-evidence-reviewer",
    "dental-content-creator",
    "dental-evidence-report-artifact",
    "dental-evidence-retriever",
    "dental-image-generator",
    "dental-paper-fetch",
    "dental-statistical-forensics",
    "research-critic",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True, env=env)


def skill_dirs() -> list[pathlib.Path]:
    return sorted(path.parent for path in ROOT.glob("*/SKILL.md"))


def test_required_skills_present() -> None:
    found = {path.name for path in skill_dirs()}
    missing = REQUIRED_SKILLS - found
    if missing:
        fail(f"missing skill dirs: {sorted(missing)}")


def test_skill_frontmatter_validator() -> None:
    run([sys.executable, "scripts/validate_skills.py"])


def test_protocol_versions() -> None:
    for path in skill_dirs():
        text = (path / "SKILL.md").read_text(encoding="utf-8")
        if f"**Skill protocol version:** {PROTOCOL_VERSION}" not in text:
            fail(f"missing protocol version in {path}")


def test_openai_metadata() -> None:
    for path in skill_dirs():
        meta = path / "agents" / "openai.yaml"
        if not meta.exists():
            fail(f"missing agents/openai.yaml for {path.name}")
        text = meta.read_text(encoding="utf-8")
        for required in ("display_name:", "short_description:", "default_prompt:", "allow_implicit_invocation: true"):
            if required not in text:
                fail(f"{meta} missing {required}")
        if f"${path.name}" not in text:
            fail(f"{meta} default_prompt must mention ${path.name}")


def test_statistical_forensics_references_exist() -> None:
    skill = ROOT / "dental-statistical-forensics" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    expected = [
        "references/core-numerical-audit.md",
        "references/effect-measure-guide.md",
        "references/dental-domain-modules.md",
        "references/clinical-thresholds-and-mcid.md",
    ]
    for rel in expected:
        if rel not in text:
            fail(f"{skill} does not mention {rel}")
        if not (ROOT / "dental-statistical-forensics" / rel).exists():
            fail(f"missing referenced file {rel}")


def test_examples_and_artifact_renderer() -> None:
    data_path = ROOT / "examples" / "iasella-statistical-forensics-report-data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for key in ("title", "verdict", "metrics", "flags", "sections", "citations"):
        if key not in data:
            fail(f"example JSON missing {key}")
    html_path = ROOT / "examples" / "iasella-statistical-forensics-report.html"
    html = html_path.read_text(encoding="utf-8")
    if "Iasella 2003 Ridge Preservation" not in html or "Major Flags" not in html:
        fail("generated HTML example missing expected content")
    with tempfile.TemporaryDirectory() as tmp:
        output = pathlib.Path(tmp) / "report.html"
        run([
            sys.executable,
            "dental-evidence-report-artifact/scripts/render_evidence_report.py",
            "--input",
            str(data_path),
            "--output",
            str(output),
        ])
        if "Iasella 2003 Ridge Preservation" not in output.read_text(encoding="utf-8"):
            fail("renderer output missing expected text")


def test_helper_scripts() -> None:
    continuous = run([
        sys.executable,
        "dental-statistical-forensics/scripts/stats_forensics_calculator.py",
        "continuous",
        "--mean-a",
        "-1.2",
        "--sd-a",
        "0.9",
        "--n-a",
        "12",
        "--mean-b",
        "-2.6",
        "--sd-b",
        "2.3",
        "--n-b",
        "12",
    ])
    result = json.loads(continuous.stdout)
    if round(result["mean_difference"], 1) != 1.4:
        fail("continuous helper returned unexpected mean difference")
    if not result["flags"]:
        fail("continuous helper should flag imprecision/dispersion concerns for Iasella-like data")

    diagnostic = run([
        sys.executable,
        "dental-statistical-forensics/scripts/stats_forensics_calculator.py",
        "diagnostic",
        "--sensitivity",
        "0.91",
        "--specificity",
        "0.84",
    ])
    diag = json.loads(diagnostic.stdout)
    if diag["positive_likelihood_ratio"] is None:
        fail("diagnostic helper did not compute LR+")

    citation = run([
        sys.executable,
        "dental-evidence-retriever/scripts/citation_validator.py",
        "PMID:123456",
        "10.1000/example-doi",
    ])
    cited = json.loads(citation.stdout)
    if len(cited["results"]) != 2:
        fail("citation validator did not return two results")
    if not all(item["syntax_valid"] for item in cited["results"]):
        fail("citation validator rejected syntactically valid examples")


def test_paper_fetch_offline() -> None:
    """Commands that need no network. CI has none, so nothing here may download."""
    script = PAPER_FETCH
    with tempfile.TemporaryDirectory() as tmp:
        papers = pathlib.Path(tmp) / "papers"
        env = {**os.environ, "PAPERS_DIR": str(papers)}
        help_text = run([sys.executable, script, "--help"], env=env).stdout
        for command in ("get", "search", "import", "topics"):
            if command not in help_text:
                fail(f"paper_fetch.py --help does not list the command {command}")
        if "--emails" not in run([sys.executable, script, "get", "--help"], env=env).stdout:
            fail("paper_fetch.py get --help does not list --emails")
        empty = run([sys.executable, script, "topics"], env=env).stdout.splitlines()
        if empty != [str(papers)]:
            fail(f"paper_fetch.py topics should print only the PAPERS_DIR folder, got {empty!r}")
        if papers.exists():
            fail("paper_fetch.py topics must not create the papers folder")
        topic = papers / "Peri-implantitis"
        topic.mkdir(parents=True)
        (topic / "2020 Example - Invented test paper [PMID 1].pdf").write_bytes(b"%PDF-1.4\n")
        listed = run([sys.executable, script, "topics"], env=env).stdout.splitlines()
        if len(listed) != 2 or listed[1].split() != ["1", "Peri-implantitis"]:
            fail(f"paper_fetch.py topics should list one topic with one PDF, got {listed!r}")
        source = (ROOT / script).read_text(encoding="utf-8")
        if "Mozilla" in source:
            fail("paper_fetch.py must not send a browser-style User-Agent")


# ---------- paper_fetch.py logic, tested offline with a fake network ----------

class FakeNetwork:
    """Stands in for paper_fetch.http_get. It answers from a table of (URL part, answer),
    logs every URL and raises an error for any other URL. Nothing reaches the network."""

    def __init__(self, answers: list[tuple[str, object]]) -> None:
        self.answers = answers
        self.calls: list[str] = []

    def __call__(self, url: str, **kwargs: object) -> bytes:
        self.calls.append(url)
        for part, answer in self.answers:
            if part in url:
                if isinstance(answer, Exception):
                    raise answer
                return answer  # type: ignore[return-value]
        raise urllib.error.URLError(f"offline test: no answer for {url}")


class FakeProcesses:
    """Stands in for the subprocess module inside paper_fetch.py. Logs each command."""

    SubprocessError = subprocess.SubprocessError
    CalledProcessError = subprocess.CalledProcessError
    TimeoutExpired = subprocess.TimeoutExpired

    def __init__(self, returncode: int = 0, stdout: object = b"") -> None:
        self.returncode, self.stdout = returncode, stdout
        self.commands: list[list[str]] = []
        self.options: list[dict[str, object]] = []

    def run(self, cmd: list[str], **kwargs: object) -> types.SimpleNamespace:
        self.commands.append([str(part) for part in cmd])
        self.options.append(kwargs)
        return types.SimpleNamespace(returncode=self.returncode, stdout=self.stdout, stderr="")


def load_paper_fetch(papers: pathlib.Path, answers: list[tuple[str, object]] | None = None):
    """Load paper_fetch.py as a fresh module with a fake network and no waiting."""
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # leave no __pycache__ inside the skill folder
    try:
        spec = importlib.util.spec_from_file_location("paper_fetch_under_test", ROOT / PAPER_FETCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = keep
    module.ROOT = papers
    module.CONTACT = ""
    module.http_get = FakeNetwork(answers or [])
    module.time = types.SimpleNamespace(sleep=lambda seconds: None, time=lambda: 0.0)
    return module


def tools_found(*names: str) -> types.SimpleNamespace:
    """Stands in for shutil inside paper_fetch.py: only the named programs exist."""
    def refuse(*args: object) -> None:
        fail("the test expected no file to be copied or moved")
    return types.SimpleNamespace(which=lambda tool, path=None: f"/usr/bin/{tool}" if tool in names else None,
                                 copy2=refuse, move=refuse)


def bucket_listing(*keys: str) -> bytes:
    items = "".join(f"<Contents><Key>{key}</Key></Contents>" for key in keys)
    return ('<?xml version="1.0" encoding="UTF-8"?><ListBucketResult '
            f'xmlns="http://s3.amazonaws.com/doc/2006-03-01/">{items}</ListBucketResult>').encode()


def invented_paper(**fields: str) -> dict[str, str]:
    paper = {"pmid": "", "pmcid": "", "doi": "", "title": "Invented test paper on bone levels",
             "journal": "Invented Journal", "year": "2020", "first_author": "Example"}
    return {**paper, **fields}


def printed(function, *args: object, **kwargs: object) -> tuple[object, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = function(*args, **kwargs)
    return result, out.getvalue()


def test_paper_fetch_version_folder() -> None:
    """The newest PubMed Central version that holds the PDF wins; with no PDF, the newest."""
    with tempfile.TemporaryDirectory() as tmp:
        pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
            ("prefix=PMC101.", bucket_listing(
                "PMC101.1/PMC101.1.pdf", "PMC101.1/PMC101.1.xml", "PMC101.1/PMC101.1.json",
                "PMC101.1/AB-1-g001.jpg", "PMC101.2/PMC101.2.xml", "PMC101.2/PMC101.2.json")),
            ("prefix=PMC102.", bucket_listing("PMC102.1/PMC102.1.xml", "PMC102.2/PMC102.2.xml")),
            ("prefix=PMC103.", bucket_listing("PMC103.1/PMC103.1.pdf", "PMC103.2/PMC103.2.pdf")),
            ("PMC101.1/PMC101.1.json", b'{"license_code": "CC BY"}'),
            ("PMC101.2/PMC101.2.json", b'{"license_code": "TDM"}'),
        ])
        folder, keys = pf.pmc_latest("PMC101")
        if folder != "PMC101.1" or "PMC101.1/AB-1-g001.jpg" not in keys:
            fail(f"newer folder without PDF, older with PDF: expected PMC101.1, got {folder}")
        if pf.pmc_latest("PMC102")[0] != "PMC102.2":
            fail("no version holds a PDF: expected the newest folder")
        if pf.pmc_latest("PMC103")[0] != "PMC103.2":
            fail("two versions hold a PDF: expected the newest folder")
        paper = invented_paper(pmid="101", pmcid="PMC101")
        first = next(pf.pdf_candidates(paper))
        if first != ("PubMed Central open-access copy", f"{pf.PMC_S3}/PMC101.1/PMC101.1.pdf"):
            fail(f"the PDF link must point to the version that holds the PDF, got {first!r}")
        if pf.lookup_license(paper) != "CC BY":
            fail("the license must come from the same version folder as the PDF")


def test_paper_fetch_webp_figures() -> None:
    """Figures stored as WebP in the PubMed Central bucket are saved with label and caption."""
    article = (b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><body><fig id="f1">'
               b"<label>Figure 1</label><caption><p>Bone level at 12 months</p></caption>"
               b'<graphic xlink:href="AB-2-g001.webp"/></fig></body></article>')
    with tempfile.TemporaryDirectory() as tmp:
        pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
            ("prefix=PMC201.", bucket_listing(
                "PMC201.1/PMC201.1.pdf", "PMC201.1/PMC201.1.xml", "PMC201.1/AB-2-g001.webp")),
            ("PMC201.1/PMC201.1.xml", article),
            ("PMC201.1/AB-2-g001.webp", b"RIFF-invented-webp"),
        ])
        dest = pathlib.Path(tmp) / "figures"
        dest.mkdir()
        figures = pf.pmc_figures("PMC201", dest)
        if len(figures) != 1 or not figures[0]["file"].endswith(".webp"):
            fail(f"expected one .webp figure, got {figures!r}")
        if figures[0]["label"] != "Figure 1" or "Bone level" not in figures[0]["caption"]:
            fail(f"the .webp figure lost its label or caption: {figures[0]!r}")
        if (dest / figures[0]["file"]).read_bytes() != b"RIFF-invented-webp":
            fail("the .webp figure file was not written")


def test_paper_fetch_pmid_without_doi() -> None:
    """PubMed gives no DOI: one OpenAlex call by PMID supplies the DOI and the free link."""
    summary = {"result": {"uids": ["301"], "301": {
        "uid": "301", "title": "Invented test paper on bone levels.", "source": "Invented J",
        "pubdate": "2020 Oct", "authors": [{"name": "Example A"}],
        "articleids": [{"idtype": "pubmed", "value": "301"}]}}}
    work = {"doi": "https://doi.org/10.1234/Invented.301", "title": "Invented test paper on bone levels",
            "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/301"},
            "best_oa_location": {"is_oa": True, "pdf_url": "https://journal.example/301.pdf"},
            "locations": []}
    with tempfile.TemporaryDirectory() as tmp:
        pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
            ("esummary.fcgi", json.dumps(summary).encode()),
            ("api.openalex.org/works/pmid:301", json.dumps(work).encode()),
            ("https://journal.example/301.pdf", b"%PDF-1.4 invented"),
        ])
        paper, _ = pf.resolve("301")
        if not paper or paper["doi"] != "10.1234/invented.301":
            fail(f"the DOI must come from the OpenAlex record of the PMID, got {paper!r}")
        data, label, url, failed = pf.download_pdf(paper)
        if not data or "OpenAlex" not in label or url != "https://journal.example/301.pdf":
            fail(f"the open-access location of the same record must be used, got {label!r} {url!r}")
        openalex_calls = [call for call in pf.http_get.calls if "api.openalex.org" in call]
        if len(openalex_calls) != 1 or "works/pmid:301" not in openalex_calls[0]:
            fail(f"expected one OpenAlex call, works/pmid:301, got {openalex_calls!r}")

        # A record with another title is not trusted: the paper keeps no DOI
        other = {**work, "title": "A different article about something else entirely"}
        pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
            ("esummary.fcgi", json.dumps(summary).encode()),
            ("api.openalex.org/works/pmid:301", json.dumps(other).encode()),
        ])
        paper, _ = pf.resolve("301")
        if not paper or paper["doi"]:
            fail("a DOI from an OpenAlex record with another title must not be used")

        # An OpenAlex answer that is not a record (null, a list): the paper keeps no DOI
        for answer in (b"null", b"[]"):
            pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
                ("esummary.fcgi", json.dumps(summary).encode()),
                ("api.openalex.org/works/pmid:301", answer),
            ])
            paper, _ = pf.resolve("301")
            if not paper or paper["doi"]:
                fail(f"an OpenAlex answer of {answer!r} must leave the paper without a DOI, not crash")


def test_paper_fetch_certificate_retry() -> None:
    """A certificate error is retried once with curl, checking on, and reported as such."""
    url = "https://broken-chain.example/paper.pdf"
    chain_error = urllib.error.URLError(ssl.SSLCertVerificationError(
        1, "certificate verify failed: unable to get local issuer certificate"))
    with tempfile.TemporaryDirectory() as tmp:
        papers = pathlib.Path(tmp) / "papers"
        pf = load_paper_fetch(papers, [(url, chain_error)])
        pf.shutil = tools_found("curl")
        pf.subprocess = FakeProcesses(returncode=0, stdout=b"%PDF-1.4 through curl")
        if pf.fetch(url) != (b"%PDF-1.4 through curl", ""):
            fail("a certificate error must be retried with curl and the PDF returned")
        command = pf.subprocess.commands[0] if len(pf.subprocess.commands) == 1 else []
        if not command or not command[0].endswith("curl") or command[-1] != url:
            fail(f"expected one curl call for the same URL, got {pf.subprocess.commands!r}")
        if command[1] != "-q":
            fail(f"curl must skip its config file: -q must be the first option, got {command!r}")
        unsafe = {"-k", "--insecure", "--proxy-insecure", "--cacert", "--capath"}
        if unsafe & set(command) or not pf.subprocess.options[0].get("timeout"):
            fail(f"curl must keep certificate checking on and have a time limit: {command!r}")
        if "--fail" not in command:
            fail(f"curl must not return an HTTP error page as a body: --fail missing in {command!r}")

        # curl fails too: OPEN_MANUALLY names the certificate problem, not a script block
        pf.subprocess = FakeProcesses(returncode=60, stdout=b"")
        pf.resolve = lambda ident: (invented_paper(pmid="401", doi="10.1234/invented.401"), "")
        pf.pdf_candidates = lambda paper: iter([("open-access copy via OpenAlex (host)", url)])
        result, text = printed(pf.get_one, "401", "Test topic", with_figures=False)
        if result != ("OPEN_MANUALLY", ""):
            fail(f"expected OPEN_MANUALLY, got {result!r}")
        if "certificate problem" not in text or "blocks download scripts" in text or url not in text:
            fail(f"OPEN_MANUALLY must name the certificate problem and the link, got: {text}")
        if papers.exists():
            fail("a failed download must not create the papers folder")

        # curl runs out of time (exit 28): a slow server, not a certificate problem
        pf.subprocess = FakeProcesses(returncode=28, stdout=b"")
        result, text = printed(pf.get_one, "401", "Test topic", with_figures=False)
        if result != ("OPEN_MANUALLY", "") or "did not answer in time" not in text or url not in text:
            fail(f"a curl timeout must be reported as 'did not answer in time' with the link, got: {text}")
        if "certificate" in text or "blocks download scripts" in text:
            fail(f"a curl timeout must not be reported as a certificate problem or a block, got: {text}")
        # An HTTP error (curl --fail, exit 22 or 56 with no body) is a plain refusal
        pf.subprocess = FakeProcesses(returncode=22, stdout=b"")
        _, text = printed(pf.get_one, "401", "Test topic", with_figures=False)
        if "blocks download scripts" not in text or "certificate" in text:
            fail(f"an HTTP error after the curl retry is a block, not a certificate problem, got: {text}")

        # Python itself runs out of time: no curl call, same timeout wording
        pf.http_get = FakeNetwork([(url, urllib.error.URLError(TimeoutError("timed out")))])
        pf.subprocess = FakeProcesses(returncode=0, stdout=b"%PDF-1.4 through curl")
        _, text = printed(pf.get_one, "401", "Test topic", with_figures=False)
        if pf.subprocess.commands or "did not answer in time" not in text or "certificate" in text:
            fail(f"a Python timeout must be reported as 'did not answer in time' without curl, got: {text}")

        # Any other network error: no curl call, and the old message stays
        pf.http_get = FakeNetwork([(url, urllib.error.URLError("connection refused"))])
        pf.subprocess = FakeProcesses(returncode=0, stdout=b"%PDF-1.4 through curl")
        result, text = printed(pf.get_one, "401", "Test topic", with_figures=False)
        if pf.subprocess.commands or "blocks download scripts" not in text:
            fail("curl is for certificate errors only")

    source = (ROOT / PAPER_FETCH).read_text(encoding="utf-8")
    for banned in ("_create_unverified_context", "CERT_NONE", "check_hostname = False", "--insecure", '"-k"'):
        if banned in source:
            fail(f"paper_fetch.py must never switch certificate checking off: found {banned}")


def test_paper_fetch_import_needs_yes() -> None:
    """import with no file names lists the PDFs in Downloads and copies nothing without --yes."""
    with tempfile.TemporaryDirectory() as tmp:
        home, papers = pathlib.Path(tmp) / "home", pathlib.Path(tmp) / "papers"
        (home / "Downloads").mkdir(parents=True)
        (home / "Downloads" / "invented-paper.pdf").write_bytes(b"%PDF-1.4\n")
        pf = load_paper_fetch(papers)
        pf.shutil = tools_found("pdftotext", "pdfinfo")
        pf.doi_in_pdf = lambda pdf: "10.1234/invented.501"
        pf.time = types.SimpleNamespace(sleep=lambda seconds: None, time=__import__("time").time)
        args = types.SimpleNamespace(files=[], topic="Test topic", days=1, move=False, yes=False,
                                     no_figures=True)
        keep = {name: os.environ.get(name) for name in ("HOME", "USERPROFILE")}
        os.environ["HOME"] = os.environ["USERPROFILE"] = str(home)
        try:
            code, text = printed(pf.cmd_import, args)
        finally:
            for name, value in keep.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        if code != 2 or "DRY_RUN" not in text or "invented-paper.pdf" not in text or "--yes" not in text:
            fail(f"import with no file names must list the files and ask for --yes, got {code}: {text}")
        if "10.1234/invented.501" not in text:
            fail("the list must show the DOI found inside each PDF")
        if papers.exists() or pf.http_get.calls:
            fail("import without --yes must copy nothing and send no request")
    if "--yes" not in run([sys.executable, PAPER_FETCH, "import", "--help"]).stdout:
        fail("paper_fetch.py import --help does not list --yes")


def test_paper_fetch_sources_and_safety() -> None:
    """OpenAIRE links, the '%PDF' check, the count line, the key redirect rule, poppler limits."""
    found = {"results": [
        {"pids": [{"scheme": "doi", "value": "10.1234/invented.601"}], "instances": [
            {"accessRight": {"label": "OPEN"}, "urls": ["https://repository.example/601.pdf",
                                                        "https://pubmed.ncbi.nlm.nih.gov/601"]},
            {"accessRight": {"label": "CLOSED"}, "urls": ["https://publisher.example/closed.pdf"]},
            {"accessRight": None, "urls": ["https://publisher.example/unknown.pdf"]}]},
        {"pids": [{"scheme": "doi", "value": "10.9999/another.paper"}], "instances": [
            {"accessRight": {"label": "OPEN"}, "urls": ["https://repository.example/other.pdf"]}]}]}
    with tempfile.TemporaryDirectory() as tmp:
        pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
            ("api.openaire.eu/graph/v3/research-products", json.dumps(found).encode()),
            ("https://repository.example/601.pdf", b"<html>This page is not a PDF</html>"),
        ])
        paper = invented_paper(doi="10.1234/invented.601")
        if pf.openaire_pdfs(paper) != ["https://repository.example/601.pdf"]:
            fail(f"OpenAIRE: only open-access links of the same DOI count, got {pf.openaire_pdfs(paper)!r}")
        labels = [label for label, _ in pf.pdf_candidates(paper)]
        if labels != ["open-access copy via OpenAIRE"]:
            fail(f"expected OpenAIRE as the only source that answered, got {labels!r}")
        data, _, _, failed = pf.download_pdf(paper)
        if data is not None or failed != [("https://repository.example/601.pdf", "")]:
            fail("an answer that does not start with %PDF must never be saved")

        # A malformed OpenAIRE answer: non-string entries are dropped, a string is not a list
        malformed = {"results": [{"pids": [{"scheme": "doi", "value": "10.1234/invented.601"}], "instances": [
            {"accessRight": {"label": "OPEN"}, "urls": [None, 5, "https://repository.example/a.pdf"]},
            {"accessRight": {"label": "OPEN"}, "urls": "https://repository.example/b.pdf"}]}]}
        pf.http_get = FakeNetwork([("api.openaire.eu/graph/v3/research-products", json.dumps(malformed).encode())])
        if pf.openaire_pdfs(paper) != ["https://repository.example/a.pdf"]:
            fail(f"OpenAIRE: only string links from a list count, got {pf.openaire_pdfs(paper)!r}")

        results = ([("SAVED", "PubMed Central")] * 10 + [("SAVED", "OpenAlex")] * 2
                   + [("OPEN_MANUALLY", "")] * 8 + [("NO_FREE_COPY", "")] * 20)
        expected = "SAVED 12: PubMed Central 10, OpenAlex 2 | OPEN_MANUALLY 8 | NO_FREE_COPY 20"
        if pf.count_line(results) != expected:
            fail(f"count line: expected {expected!r}, got {pf.count_line(results)!r}")
        code, text = printed(pf.finish_run, [("EXISTS", ""), ("NOT_FOUND", "")])
        if code != 2 or text.strip() != "SAVED 0 | EXISTS 1 | OPEN_MANUALLY 0 | NO_FREE_COPY 0 | NOT_FOUND 1":
            fail(f"count line for EXISTS and NOT_FOUND is wrong: {code} {text!r}")

        keyed = urllib.request.Request("https://api.core.ac.uk/v3/search/works/?q=x",
                                       headers={"Authorization": "Bearer invented-test-key"})
        rule = pf.SameHostRedirects()
        for target in ("https://elsewhere.example/v3/", "http://api.core.ac.uk/v3/search/works/"):
            try:
                rule.redirect_request(keyed, None, 301, "Moved", {}, target)
            except urllib.error.HTTPError:
                continue
            fail(f"a request with an API key must not follow a redirect to {target}")
        if rule.redirect_request(keyed, None, 301, "Moved", {}, "https://api.core.ac.uk/v3/other/") is None:
            fail("a redirect that stays on the same https host must still work")

        pf.subprocess = FakeProcesses(stdout="")
        pf.pdf_captions(pathlib.Path(tmp) / "invented.pdf")
        if not pf.subprocess.options or not pf.subprocess.options[0].get("timeout"):
            fail("poppler calls must have a time limit")
        pf.shutil = tools_found("pdfinfo", "pdftotext")
        pf.subprocess = FakeProcesses(stdout="doi:10.1234/invented.601 on page 1")
        if pf.doi_in_pdf(pathlib.Path(tmp) / "invented.pdf") != "10.1234/invented.601":
            fail("import must read the DOI printed in the PDF")
        if pf.subprocess.options[0].get("timeout") != pf.POPPLER_TIMEOUT:
            fail(f"import's poppler calls must use POPPLER_TIMEOUT, got {pf.subprocess.options!r}")
        pf.shutil = tools_found()
        calls = [printed(pf.pdf_figures, pathlib.Path(tmp) / "invented.pdf", pathlib.Path(tmp))
                 for _ in range(2)]
        if [figures for figures, _ in calls] != [[], []]:
            fail("without poppler, pdf_figures must return no figures")
        if "brew install poppler" not in calls[0][1] or "poppler-utils" not in calls[0][1] or calls[1][1]:
            fail(f"without poppler, the install help must print once, got {[t for _, t in calls]!r}")


def test_fixtures() -> None:
    fixtures = sorted((ROOT / "fixtures").glob("*.md"))
    if len(fixtures) < 7:
        fail("expected expanded fixture set")
    for path in fixtures:
        text = path.read_text(encoding="utf-8")
        has_companion_expected = path.name == "iasella2003-ridge-preservation.md" and (ROOT / "fixtures" / "iasella2003-expected-flags.md").exists()
        if path.name != "fixture-index.md" and not has_companion_expected and "Expected Flags" not in text:
            fail(f"{path} missing Expected Flags section")


def test_iasella_golden_concepts() -> None:
    """Guard the fixture against losing its core statistical-forensics lesson."""
    fixture = (ROOT / "fixtures" / "iasella2003-ridge-preservation.md").read_text(encoding="utf-8").lower()
    expected = (ROOT / "fixtures" / "iasella2003-expected-flags.md").read_text(encoding="utf-8").lower()
    combined = fixture + "\n" + expected
    required_phrases = [
        "favorable",
        "average",
        "sd",
        "larger than the mean gain",
        "range includes clinically relevant loss",
        "predictable",
        "must be softened",
        "do not make a practice-change recommendation",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in combined]
    if missing:
        fail(f"Iasella fixture missing required anti-regression concepts: {missing}")


TESTS = [
    test_required_skills_present,
    test_skill_frontmatter_validator,
    test_protocol_versions,
    test_openai_metadata,
    test_statistical_forensics_references_exist,
    test_examples_and_artifact_renderer,
    test_helper_scripts,
    test_paper_fetch_offline,
    test_paper_fetch_version_folder,
    test_paper_fetch_webp_figures,
    test_paper_fetch_pmid_without_doi,
    test_paper_fetch_certificate_retry,
    test_paper_fetch_import_needs_yes,
    test_paper_fetch_sources_and_safety,
    test_fixtures,
    test_iasella_golden_concepts,
]


def main() -> int:
    failed = False
    for test in TESTS:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:  # noqa: BLE001 - smoke test should report all failures clearly
            failed = True
            print(f"FAIL: {test.__name__}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
