#!/usr/bin/env python3
"""Repository smoke tests for dental-ai-skills.

These tests intentionally use only the Python standard library so they can run
in Claude Code, Codex, CI, or a minimal local checkout.
"""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import re
import ssl
import subprocess
import sys
import tempfile
import types
import urllib.error
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPER_FETCH = "dental-paper-fetch/scripts/paper_fetch.py"
IMAGE_SCRIPT = "dental-image-generator/scripts/generate_dental_image.py"
PROTOCOL_VERSION = "2026.09.30"
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

        # An optional per-section table renders as an HTML table with every cell escaped
        payload = {"title": "Table check", "verdict": "v", "metrics": [], "flags": [], "citations": [],
                   "sections": [{"heading": "Author relationships", "body": "1 of 2 rows externally documented",
                                 "table": {"columns": ["Author", "Status <b>"],
                                           "rows": [["A. Author", "declared in paper"],
                                                    ["<script>alert(1)</script>", "externally documented"]]}}]}
        payload_path = pathlib.Path(tmp) / "table.json"
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        table_output = pathlib.Path(tmp) / "table.html"
        run([
            sys.executable,
            "dental-evidence-report-artifact/scripts/render_evidence_report.py",
            "--input",
            str(payload_path),
            "--output",
            str(table_output),
        ])
        rendered = table_output.read_text(encoding="utf-8")
        if "<th>Author</th>" not in rendered or "<td>declared in paper</td>" not in rendered:
            fail("a section table must render as an HTML table with its columns and rows")
        if "<script>" in rendered or "&lt;script&gt;alert(1)&lt;/script&gt;" not in rendered \
                or "<th>Status &lt;b&gt;</th>" not in rendered:
            fail("every table heading and cell must be escaped")


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
            ("https://journal.example/301.pdf", b"%PDF-1.4 invented\n"
             b"3 0 obj << /Type /Page >> endobj\n4 0 obj << /Type /Page >> endobj\n"),
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
        (home / "Downloads" / "tagged [PMID 502].pdf").write_bytes(b"%PDF-1.4\n")
        (home / "Downloads" / "untitled scan.pdf").write_bytes(b"%PDF-1.4\n")
        pf = load_paper_fetch(papers)
        pf.shutil = tools_found("pdftotext", "pdfinfo")
        pf.doi_in_pdf = lambda pdf: "10.1234/invented.501" if pdf.name == "invented-paper.pdf" else ""
        pf.time = types.SimpleNamespace(sleep=lambda seconds: None, time=__import__("time").time)
        args = types.SimpleNamespace(files=[], topic="Test topic", topic_from_parent=False, days=1,
                                     move=False, yes=False, dry_run=False, no_figures=True)
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
        if "WOULD_IMPORT  " + str(home / "Downloads" / "tagged [PMID 502].pdf") + " | tag in the name: PMID 502" not in text:
            fail(f"a tagged PDF without a DOI inside would be imported with --yes, so the list must say so, got: {text}")
        if "NO_DOI        " + str(home / "Downloads" / "untitled scan.pdf") not in text or "title" not in text:
            fail(f"a PDF with no tag and no DOI must say the title would be tried, got: {text}")
        if papers.exists() or pf.http_get.calls:
            fail("import without --yes must copy nothing and send no request")
    if "--yes" not in run([sys.executable, PAPER_FETCH, "import", "--help"]).stdout:
        fail("paper_fetch.py import --help does not list --yes")


def test_paper_fetch_mount_guard() -> None:
    """PAPERS_DIR on an external drive that is not connected: one sentence, exit 1, nothing
    made under /Volumes. A connected drive is checked once; a folder elsewhere never."""
    root = "/Volumes/Invented Drive/Scientific Articles"
    sentence = "The drive Invented Drive is not connected. Connect it or set PAPERS_DIR."
    for command in (["topics"], ["import", "--topic", "T", "--yes"], ["get", "1", "--topic", "T"]):
        done = subprocess.run([sys.executable, PAPER_FETCH, *command], cwd=ROOT, text=True,
                              capture_output=True, env={**os.environ, "PAPERS_DIR": root})
        if done.returncode != 1 or done.stderr.strip() != sentence or done.stdout:
            fail(f"{command[0]} on a missing drive must exit 1 with one sentence, "
                 f"got {done.returncode}: {done.stderr!r} {done.stdout!r}")
    if pathlib.Path("/Volumes/Invented Drive").exists():
        fail("the guard must not create anything under /Volumes")
    pf = load_paper_fetch(pathlib.Path(root))
    asked: list[str] = []
    pf.os = types.SimpleNamespace(environ=os.environ, path=types.SimpleNamespace(
        ismount=lambda path: asked.append(str(path)) or True))
    pf.require_drive()
    if asked != ["/Volumes/Invented Drive"]:
        fail(f"the guard must ask whether /Volumes/<name> is a mount point, got {asked!r}")
    pf.ROOT = pathlib.Path(tempfile.gettempdir()) / "papers"
    asked.clear()
    pf.require_drive()
    if asked:
        fail("a folder outside /Volumes must not be checked for a mount point")


def test_paper_fetch_file_names() -> None:
    """The file name carries year, first author, title (80 characters at most), journal (40
    at most) and the tag last. An older name without the journal is still found."""
    with tempfile.TemporaryDirectory() as tmp:
        papers = pathlib.Path(tmp) / "papers"
        pf = load_paper_fetch(papers)
        paper = invented_paper(pmid="801", journal="Invented J Periodontol: Part B/2")
        name = pf.pdf_name(paper)
        if name != ("2020 Example - Invented test paper on bone levels - "
                    "Invented J Periodontol Part B 2 [PMID 801].pdf"):
            fail(f"unexpected file name: {name!r}")
        long = invented_paper(doi="10.1234/invented.802", title="T" * 100, journal="J" * 50)
        name = pf.pdf_name(long)
        if name != f"2020 Example - {'T' * 80} - {'J' * 40} [DOI 10.1234_invented.802].pdf":
            fail(f"title and journal must be cut at 80 and 40 characters, got {name!r}")
        no_journal = pf.pdf_name(invented_paper(pmid="803", journal=""))
        if no_journal != "2020 Example - Invented test paper on bone levels [PMID 803].pdf":
            fail(f"without a journal the name has no empty part, got {no_journal!r}")
        topic = papers / "Test topic"
        topic.mkdir(parents=True)
        old = topic / "2020 Example - Invented test paper on bone levels [PMID 801].pdf"
        old.write_bytes(b"%PDF-1.4\n")
        if pf.find_existing(paper) != old:
            fail("a PDF saved under the older name, without the journal, must still count as EXISTS")
        (topic / "._2020 Example - Other paper [PMID 804].pdf").write_bytes(b"Finder metadata on exFAT")
        if pf.find_existing(invented_paper(pmid="804")) is not None:
            fail("a ._ metadata file that carries the tag must not count as the paper")


def test_paper_fetch_index_columns() -> None:
    """Every row gets the file's sha256 and the OpenAlex open-access status; an older index
    is rewritten with the new columns; the same bytes under another name count as indexed."""
    with tempfile.TemporaryDirectory() as tmp:
        papers = pathlib.Path(tmp) / "papers"
        topic = papers / "Test topic"
        topic.mkdir(parents=True)
        (papers / "_index.csv").write_text("saved_at,topic,pmid,doi,file\n"
                                           "2026-01-01T00:00:00,Test topic,900,,old.pdf\n", encoding="utf-8")
        pf = load_paper_fetch(papers)
        pf.lookup_license = lambda paper: "CC BY"
        pf.OPENALEX["10.1234/invented.901"] = {"open_access": {"oa_status": "gold"}}
        pdf = topic / "2020 Example - Invented test paper on bone levels [PMID 901].pdf"
        pdf.write_bytes(b"%PDF-1.4 invented bytes\n")
        pf.index_paper(invented_paper(pmid="901", doi="10.1234/invented.901"), pdf, "test")
        rows = pf.index_rows()
        if [r["pmid"] for r in rows] != ["900", "901"] or rows[0]["sha256"] != "" or rows[0]["oa_status"] != "":
            fail(f"the older row must be kept with empty new columns, got {rows!r}")
        expected = pf.sha256_of(pdf)
        if rows[1]["sha256"] != expected or rows[1]["oa_status"] != "gold" or rows[1]["license"] != "CC BY":
            fail(f"the new row must carry sha256, oa_status and license, got {rows[1]!r}")
        with open(papers / "_index.csv", encoding="utf-8") as fh:
            if fh.readline().strip().split(",") != pf.INDEX_FIELDS:
                fail("the index header must list the current columns after a column change")
        if not pf.in_index(digest=expected) or pf.in_index(digest="0" * 64):
            fail("in_index must match a file by its sha256")
        if not pf.in_index(invented_paper(pmid="900")) or pf.in_index(invented_paper(pmid="902")):
            fail("in_index must still match a PMID")
        if pf.oa_status(invented_paper(doi="10.9999/never.read")) != "unknown":
            fail("a paper whose OpenAlex record was not read has oa_status unknown")
        if pf.http_get.calls:
            fail("indexing must read no OpenAlex record on its own")

        # A column added by hand survives an append and a rebuild
        pf.write_index([{**rows[1], "notes": "read on Monday"}])
        pdf2 = topic / "2020 Example - Second invented paper [PMID 902].pdf"
        pdf2.write_bytes(b"%PDF-1.4 second invented bytes\n")
        pf.index_paper(invented_paper(pmid="902", doi="10.1234/invented.902"), pdf2, "test")
        rows = pf.index_rows()
        with open(papers / "_index.csv", encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
        if header != pf.INDEX_FIELDS + ["notes"] or [r["notes"] for r in rows] != ["read on Monday", ""]:
            fail(f"a hand-added column must survive an append, got {header!r} and {rows!r}")
        code, text = printed(pf.rebuild_index)
        rows = pf.index_rows()
        if code != 0 or [r["pmid"] for r in rows] != ["901", "902"] or [r["notes"] for r in rows] != ["read on Monday", ""]:
            fail(f"a hand-added column must survive rebuild-index, got {code}: {rows!r}\n{text}")
        if pf.http_get.calls:
            fail("a rebuild of known rows must make no lookup")

        # A rewrite that fails half way leaves the old index as it was, and no temporary file
        before = (papers / "_index.csv").read_bytes()

        class Boom:
            def __init__(self, fh: object, **kwargs: object) -> None:
                self.fh = fh

            def writeheader(self) -> None:
                self.fh.write("header\n")

            def writerows(self, rows: object) -> None:
                raise OSError(28, "No space left on device")
        pf.csv = types.SimpleNamespace(DictWriter=Boom, DictReader=__import__("csv").DictReader)
        try:
            pf.write_index(rows)
        except OSError:
            pass
        else:
            fail("a failed write must raise")
        if (papers / "_index.csv").read_bytes() != before or list(papers.glob("*.tmp")):
            fail("a rewrite that fails must leave the old index intact and no temporary file")


def pubmed_summary(pmid: str, title: str, doi: str = "") -> bytes:
    ids = [{"idtype": "pubmed", "value": pmid}] + ([{"idtype": "doi", "value": doi}] if doi else [])
    return json.dumps({"result": {"uids": [pmid], pmid: {
        "uid": pmid, "title": title + ".", "source": "Invented J", "pubdate": "2020 Oct",
        "authors": [{"name": "Example A"}], "articleids": ids}}}).encode()


def pubmed_found(*pmids: str) -> bytes:
    return json.dumps({"esearchresult": {"idlist": list(pmids), "count": str(len(pmids))}}).encode()


def import_test_module(papers: pathlib.Path):
    """paper_fetch with a fake PubMed, a fake DOI reader and a shutil that only copies."""
    pf = load_paper_fetch(papers, [
        ("id=1001", pubmed_summary("1001", "Invented test paper on bone levels", "10.1234/invented.1001")),
        ("id=1002", pubmed_summary("1002", "Completely different paper about something else")),
        ("id=1003", pubmed_summary("1003", "Invented scan with a DOI inside", "10.1234/invented.1003")),
        ("invented.1003%5Bdoi%5D", pubmed_found("1003")),
        ("Some+other+invented+title", pubmed_found("1002")),
        ("made-up-title", pubmed_found()),
        ("1+unknown+copy", pubmed_found()),
        ("api.crossref.org", b'{"message": {"items": []}}'),
    ])
    pf.doi_in_pdf = lambda pdf: "10.1234/invented.1003" if pdf.name == "scan.pdf" else ""
    pf.shutil = types.SimpleNamespace(which=lambda tool, path=None: "/usr/bin/pdftotext" if tool == "pdftotext" else None,
                                      copyfile=__import__("shutil").copyfile, copy2=tools_found().copy2,
                                      move=tools_found().move)
    return pf


def test_paper_fetch_import_folder() -> None:
    """import takes a folder, files each PDF by the tag in its name, the DOI inside or a close
    title match, skips the same bytes and the same paper, never guesses, never deletes."""
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / "source" / "Peri-implantitis"
        source.mkdir(parents=True)
        same, other = b"%PDF-1.4 the same bytes\n", b"%PDF-1.4 another scan\n"
        (source / "1 unknown copy of the same.pdf").write_bytes(same)  # sorts first, matches nothing
        (source / "2020 - Example - Invented test paper on bone levels [PMID 1001].pdf").write_bytes(same)
        (source / "Another scan [PMID 1001].pdf").write_bytes(other)
        (source / "Some other invented title far away.pdf").write_bytes(b"%PDF-1.4 no match\n")
        (source / "copy of the same.pdf").write_bytes(same)
        (source / "made-up-title.pdf").write_bytes(b"%PDF-1.4 nothing\n")
        (source / "scan.pdf").write_bytes(b"%PDF-1.4 doi inside\n")
        (source / "._hidden.pdf").write_bytes(b"Finder metadata, not a PDF")
        before = sorted(f.name for f in source.iterdir())
        papers = pathlib.Path(tmp) / "papers"
        args = types.SimpleNamespace(files=[str(source.parent)], topic=None, topic_from_parent=True, days=1,
                                     move=False, yes=False, dry_run=True, no_figures=True)

        # A dry run says what would happen and writes nothing
        pf = import_test_module(papers)
        code, text = printed(pf.cmd_import, args)
        expected = "DRY_RUN  WOULD_IMPORT 2 | EXISTS 1 | DUPLICATE_BYTES 1 | NO_MATCH 1 | NO_DOI 2"
        if code != 2 or text.strip().splitlines()[-1] != expected:
            fail(f"dry run: expected exit 2 and {expected!r}, got {code}: {text}")
        if "NO_DOI  " + str(source / "1 unknown copy of the same.pdf") not in text:
            fail("a copy that cannot be identified is NO_DOI, and must not block the tagged copy after it")
        if papers.exists() or "._hidden" in text:
            fail("a dry run must write nothing, and Finder metadata files are skipped")
        if "-> " + str(papers / "Peri-implantitis" / "2020 Example - Invented test paper on bone levels - Invented J [PMID 1001].pdf") not in text:
            fail(f"the dry run must show the target name with the parent folder as topic, got: {text}")

        # The real run copies, indexes with sha256 and leaves every source file in place
        args.dry_run = False
        pf = import_test_module(papers)
        code, text = printed(pf.cmd_import, args)
        expected = "IMPORTED 2 | EXISTS 1 | DUPLICATE_BYTES 1 | NO_MATCH 1 | NO_DOI 2"
        if code != 2 or text.strip().splitlines()[-1] != expected:
            fail(f"import: expected exit 2 and {expected!r}, got {code}: {text}")
        saved = sorted(f.name for f in (papers / "Peri-implantitis").iterdir() if f.suffix == ".pdf")
        if saved != ["2020 Example - Invented scan with a DOI inside - Invented J [PMID 1003].pdf",
                     "2020 Example - Invented test paper on bone levels - Invented J [PMID 1001].pdf"]:
            fail(f"unexpected files in the topic folder: {saved!r}")
        if (papers / "Peri-implantitis" / saved[1]).read_bytes() != same:
            fail("the imported file must hold the source bytes")
        if sorted(f.name for f in source.iterdir()) != before:
            fail("import must never delete or move a source file")
        rows = pf.index_rows()
        if [r["pmid"] for r in rows] != ["1001", "1003"] or any(len(r["sha256"]) != 64 for r in rows):
            fail(f"the index must hold one row per imported file with its sha256, got {rows!r}")
        if 'closest title found: "Completely different paper about something else"' not in text:
            fail(f"NO_MATCH must name the closest title and its score, got: {text}")
        if "no DOI inside and no paper found for the title" not in text:
            fail(f"NO_DOI must say what was tried, got: {text}")
        if "EXISTS  " + str(papers / "Peri-implantitis" / saved[1]) not in text:
            fail(f"a second scan of the same paper must be EXISTS, got: {text}")

        # Run again: every file already in the library is the same bytes, so no lookup is made for it
        pf = import_test_module(papers)
        code, text = printed(pf.cmd_import, args)
        if text.strip().splitlines()[-1] != "IMPORTED 0 | EXISTS 1 | DUPLICATE_BYTES 4 | NO_MATCH 1 | NO_DOI 1":
            fail(f"a second import of the same folder must skip by bytes, got: {text}")
        if any("id=1003" in call for call in pf.http_get.calls):
            fail("a file whose bytes are in the index must cost no lookup")

        # A stale index row, its file deleted by hand, must not make the same bytes DUPLICATE_BYTES
        stale = pathlib.Path(tmp) / "papers-stale"
        pf = import_test_module(stale)
        stale.mkdir()
        pf.write_index([{"saved_at": "2026-01-01T00:00:00", "topic": "Gone", "pmid": "1001",
                         "file": "Gone/deleted by hand [PMID 1001].pdf", "sha256": pf.sha256_of(source / "scan.pdf")}])
        args_scan = types.SimpleNamespace(**{**vars(args), "files": [str(source / "scan.pdf")]})
        code, text = printed(pf.cmd_import, args_scan)
        if code != 0 or "IMPORTED  " not in text or not (stale / "Peri-implantitis").exists():
            fail(f"a row whose file is gone must not count as a duplicate, got {code}: {text}")

        # A relative path keeps a parent folder name: "." and ".." are folders, not empty names
        cwd = os.getcwd()
        (source / "sub").mkdir()
        os.chdir(source / "sub")
        try:
            listed = pf.pdf_files(["."]), pf.pdf_files([".."])
        finally:
            os.chdir(cwd)
        if listed[0] or not listed[1] or not all(f.is_absolute() and f.parent.name == "Peri-implantitis"
                                                 for f in listed[1]):
            fail(f"pdf_files must give absolute, normalized paths so --topic-from-parent has a name, got {listed!r}")

        # A folder that cannot be read is UNREADABLE, counted, and the run exits 2
        if os.geteuid() != 0:  # as root every folder can be read, so there is nothing to see
            locked = pathlib.Path(tmp) / "locked" / "Peri-implantitis"
            (locked / "closed").mkdir(parents=True)
            (locked / "closed" / "hidden [PMID 1001].pdf").write_bytes(same)
            (locked / "open [PMID 1003].pdf").write_bytes(b"%PDF-1.4 readable\n")
            (locked / "closed").chmod(0)
            try:
                pf = import_test_module(pathlib.Path(tmp) / "papers-locked")
                pf.doi_in_pdf = lambda pdf: ""
                args_locked = types.SimpleNamespace(**{**vars(args), "files": [str(locked.parent)], "dry_run": True})
                code, text = printed(pf.cmd_import, args_locked)
            finally:
                (locked / "closed").chmod(0o755)
            if code != 2 or "UNREADABLE  " + str(locked / "closed") not in text \
                    or not text.strip().endswith("| UNREADABLE 1"):
                fail(f"an unreadable folder must be reported, counted and make the run exit 2, got {code}: {text}")

        # A copy that fails is ERROR, and the next copy of the same paper is still imported
        failing = pathlib.Path(tmp) / "papers-failing"
        second = pathlib.Path(tmp) / "second" / "Peri-implantitis"
        second.mkdir(parents=True)
        (second / "a [PMID 1001].pdf").write_bytes(same)
        (second / "b [PMID 1001].pdf").write_bytes(same)
        pf = import_test_module(failing)
        real_copy, calls = pf.shutil.copyfile, []

        def copy_once_failing(src: str, dst: str) -> None:
            calls.append(src)
            if len(calls) == 1:
                raise OSError(28, "No space left on device")
            real_copy(src, dst)
        pf.shutil.copyfile = copy_once_failing
        args_second = types.SimpleNamespace(**{**vars(args), "files": [str(second)]})
        code, text = printed(pf.cmd_import, args_second)
        if text.strip().splitlines()[-1] != "IMPORTED 1 | EXISTS 0 | DUPLICATE_BYTES 0 | NO_MATCH 0 | NO_DOI 0 | ERROR 1":
            fail(f"a failed copy must be ERROR and must not make the next copy a duplicate, got: {text}")
        if "ERROR  " + str(second / "a [PMID 1001].pdf") not in text or "No space left" not in text:
            fail(f"the ERROR line must name the file and the fault, got: {text}")

        # A copy that stops half way leaves no truncated PDF under the paper's name and no
        # .part file, and the next copy of the same paper is imported
        halfway = pathlib.Path(tmp) / "papers-halfway"
        pf = import_test_module(halfway)
        real_copy, targets = pf.shutil.copyfile, []

        def copy_once_halfway(src: str, dst: str) -> None:
            targets.append(dst)
            if len(targets) == 1:
                pathlib.Path(dst).write_bytes(same[:10])
                raise OSError(28, "No space left on device")
            real_copy(src, dst)
        pf.shutil.copyfile = copy_once_halfway
        code, text = printed(pf.cmd_import, args_second)
        left = sorted(f.name for f in (halfway / "Peri-implantitis").iterdir() if f.suffix != ".bib")
        if text.strip().splitlines()[-1] != "IMPORTED 1 | EXISTS 0 | DUPLICATE_BYTES 0 | NO_MATCH 0 | NO_DOI 0 | ERROR 1" \
                or left != [saved[1]] or (halfway / "Peri-implantitis" / saved[1]).read_bytes() != same:
            fail(f"a copy that stops half way must leave no truncated PDF and no .part file, got {left!r}: {text}")
        if not all(t.endswith(".pdf.part") for t in targets) \
                or [r["file"] for r in pf.index_rows()] != ["Peri-implantitis/" + saved[1]]:
            fail(f"a copy must go to a .part name first, and only the whole copy is indexed, got {targets!r}")

        # get writes through the same guard
        target = halfway / "Peri-implantitis" / "download [PMID 1002].pdf"

        def write_halfway(part: pathlib.Path) -> None:
            part.write_bytes(b"%PDF-1.4 half")
            raise OSError(28, "No space left on device")
        try:
            pf.into_place(target, write_halfway)
        except OSError:
            pass
        else:
            fail("into_place must raise the fault again")
        if target.exists() or target.with_name(target.name + ".part").exists():
            fail("a write that stops half way must leave no file under the paper's name and no .part file")
        pf.into_place(target, lambda part: part.write_bytes(b"%PDF-1.4 whole"))
        if target.read_bytes() != b"%PDF-1.4 whole" or target.with_name(target.name + ".part").exists():
            fail("a whole write must land under the paper's name with no .part file left")
        if (ROOT / PAPER_FETCH).read_text(encoding="utf-8").count("into_place(path, lambda part: ") != 2:
            fail("get and import must both write the PDF through into_place")

    help_text = run([sys.executable, PAPER_FETCH, "import", "--help"]).stdout
    for flag in ("--topic-from-parent", "--dry-run"):
        if flag not in help_text:
            fail(f"paper_fetch.py import --help does not list {flag}")
    if "TITLE_MATCH = 0.85" not in (ROOT / PAPER_FETCH).read_text(encoding="utf-8"):
        fail("a title found by a file name must need a similarity above 0.85")


def test_paper_fetch_title_guard() -> None:
    """A paper found by the title in a file name is taken only when the numbers in the title,
    the year and the first author agree with the name and it is not a comment or correction:
    a sibling record (Part II for Part I, 10-year for 5-year, "Comment on") is refused."""
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / "source" / "Bone levels"
        source.mkdir(parents=True)
        long_title = "Invented long report on marginal bone level changes around implants in the posterior maxilla"
        names = ["2020 - Example - Invented follow-up study Part I.pdf",
                 "2020 - Example - Invented outcomes after 5 years of loading.pdf",
                 f"2020 - Example - {long_title}.pdf",
                 "2015 - Example - Invented sound paper about bone levels.pdf",
                 "2020 - Other - Invented sound paper about bone levels.pdf",
                 "2020 - Example T - Invented sound paper about bone levels.pdf",
                 "2021 - Example - Invented crossref only paper.pdf",
                 # round 2 of the review
                 "2021 - Example - Comment on: Invented reply target paper with a fairly long title about implants.pdf",
                 f"2021 - Example - Comment on: {long_title}.pdf",
                 "Invented consensus report on peri-implant diseases.pdf",
                 "Invented single plain title paper.pdf",
                 "Example et al. - 2020 - Invented zotero style paper.pdf",
                 "2020 - Example - Invented five-year results of something.pdf",
                 "2020 - Lindhe and Example - Invented sound paper about bone levels.pdf",
                 "2020 - Example, Lindhe - Invented sound paper about bone levels.pdf",
                 # round 3 of the review
                 "Example et al. - 2018 - Invented consensus report on peri-implant diseases.pdf",
                 "2020 - Example - Invented classic paper on bone.pdf",
                 "2020 - Example - Invented short implants v long implants.pdf"]
        for n, name in enumerate(names):
            (source / name).write_bytes(f"%PDF-1.4 invented file {n}\n".encode())
        before = sorted(f.name for f in source.iterdir())
        crossref = {"message": {"items": [{"DOI": "10.1234/CR.2105", "title": ["Invented crossref only paper"],
                                           "issued": {"date-parts": [[2021, 3]]}, "author": [{"family": "Example", "given": "A"}],
                                           "container-title": ["Invented J"]}]}}
        openalex = {"ids": {}, "title": "Invented crossref only paper", "publication_year": 2021,
                    "authorships": [{"author": {"display_name": "A Example"}}],
                    "primary_location": {"source": {"display_name": "Invented J"}}, "open_access": {"oa_status": "green"}}
        twins = json.dumps({"result": {"uids": ["2107", "2108"], **{
            pmid: {"uid": pmid, "title": "Invented consensus report on peri-implant diseases.", "source": journal,
                   "pubdate": "2018 Jun", "authors": [{"name": "Example A"}],
                   "articleids": [{"idtype": "pubmed", "value": pmid}]}
            for pmid, journal in (("2107", "Invented J"), ("2108", "Other Invented J"))}}}).encode()
        classic = {"message": {"items": [{"DOI": "10.1234/classic.2112", "title": ["Invented classic paper on bone"],
                                          "issued": {"date-parts": [[2020]]}, "author": [{"family": "Example"}],
                                          "container-title": ["Invented J"]}]}}
        papers = pathlib.Path(tmp) / "papers"
        pf = load_paper_fetch(papers, [
            ("Invented+classic+paper+on+bone%5Bti%5D", pubmed_found("2112")),
            ("id=2112", pubmed_summary("2112", "Invented classic paper on bone")),
            ("query.bibliographic=Invented+classic+paper+on+bone", json.dumps(classic).encode()),
            ("Invented+short+implants", pubmed_found("2113")),
            ("id=2113", pubmed_summary("2113", "Invented short implants versus long implants")),
            ("Invented+reply+target", pubmed_found("2106")),
            ("id=2106", pubmed_summary("2106", "Invented reply target paper with a fairly long title about implants")),
            ("Invented+consensus+report+on+peri-implant+diseases%5Bti%5D", pubmed_found("2107", "2108")),
            ("id=2107%2C2108", twins),
            ("Invented+single+plain+title", pubmed_found("2109")),
            ("id=2109", pubmed_summary("2109", "Invented single plain title paper")),
            ("Invented+zotero+style", pubmed_found("2110")),
            ("id=2110", pubmed_summary("2110", "Invented zotero style paper")),
            ("Invented+five-year+results", pubmed_found("2111")),
            ("id=2111", pubmed_summary("2111", "Invented 5-year results of something")),
            ("Part+I%5Bti%5D", pubmed_found("2101")),
            ("id=2101", pubmed_summary("2101", "Invented follow-up study Part II")),
            ("after+5+years", pubmed_found("2102")),
            ("id=2102", pubmed_summary("2102", "Invented outcomes after 10 years of loading")),
            ("Invented+long+report", pubmed_found("2103")),
            ("id=2103", pubmed_summary("2103", "Comment on: " + long_title)),
            ("Invented+sound+paper", pubmed_found("2104")),
            ("id=2104", pubmed_summary("2104", "Invented sound paper about bone levels")),
            ("Invented+crossref+only+paper%5Bti%5D", pubmed_found()),
            ("cr.2105%5Bdoi%5D", pubmed_found()),
            ("query.bibliographic=Invented+crossref+only+paper", json.dumps(crossref).encode()),
            ("works/doi:10.1234/cr.2105", json.dumps(openalex).encode()),
            ("api.crossref.org", b'{"message": {"items": []}}'),
        ])
        pf.doi_in_pdf = lambda pdf: ""
        pf.shutil = types.SimpleNamespace(which=lambda tool, path=None: "/usr/bin/pdftotext" if tool == "pdftotext" else None,
                                          copyfile=__import__("shutil").copyfile, copy2=tools_found().copy2,
                                          move=tools_found().move)
        args = types.SimpleNamespace(files=[str(source.parent)], topic=None, topic_from_parent=True, days=1,
                                     move=False, yes=False, dry_run=False, no_figures=True)
        code, text = printed(pf.cmd_import, args)
        expected = "IMPORTED 8 | EXISTS 1 | DUPLICATE_BYTES 0 | NO_MATCH 9 | NO_DOI 0"
        if code != 2 or text.strip().splitlines()[-1] != expected:
            fail(f"title guard: expected exit 2 and {expected!r}, got {code}: {text}")
        for reason in ("the numbers differ: 1 in the name, 2 in its title",
                       "the numbers differ: 5 in the name, 10 in its title",
                       "it is a comment, reply, letter or correction about a paper, not the paper",
                       "the name is a comment, reply, letter or correction about a paper, and this is the paper itself",
                       "the year 2015 in the name is not within a year of 2020",
                       "the first author Other in the name is not Example",
                       "the first author Lindhe and Example in the name is not Example",
                       '2 papers pass for this name: PMID 2107 "Invented consensus report on peri-implant diseases" '
                       '(Invented J 2018); PMID 2108 "Invented consensus report on peri-implant diseases" (Other Invented J '
                       "2018); add a [PMID n] or [DOI ...] tag to the name to say which one"):
            if reason not in text:
                fail(f"a refused sibling record must say why: {reason!r} missing in: {text}")
        if text.count("2 papers pass for this name") != 2:
            fail("the twin-journal refusal must fire for the plain-title name AND for the Zotero name with year and author")
        saved = sorted(f.name for f in (papers / "Bone levels").iterdir() if f.suffix == ".pdf")
        if saved != ["2020 Example - Comment on Invented long report on marginal bone level changes around implants i - Invented J [PMID 2103].pdf",
                     "2020 Example - Invented 5-year results of something - Invented J [PMID 2111].pdf",
                     "2020 Example - Invented classic paper on bone - Invented J [PMID 2112].pdf",
                     "2020 Example - Invented short implants versus long implants - Invented J [PMID 2113].pdf",
                     "2020 Example - Invented single plain title paper - Invented J [PMID 2109].pdf",
                     "2020 Example - Invented sound paper about bone levels - Invented J [PMID 2104].pdf",
                     "2020 Example - Invented zotero style paper - Invented J [PMID 2110].pdf",
                     "2021 Example - Invented crossref only paper - Invented J [DOI 10.1234_cr.2105].pdf"]:
            fail(f"unexpected set of imported files: {saved!r}")
        if "EXISTS  " not in text or "(left 2020 - Example, Lindhe - Invented sound paper about bone levels.pdf" not in text:
            fail(f"a name whose first surname agrees must reach the EXISTS check, got: {text}")
        row = next(r for r in pf.index_rows() if r["pmid"] == "2112")
        if row["doi"] != "10.1234/classic.2112":
            fail(f"a PubMed paper without a DOI must take the DOI of its Crossref twin, got {row!r}")
        if sorted(f.name for f in source.iterdir()) != before:
            fail("the title guard must never delete or move a source file")
        if not any("retmax=3" in c for c in pf.http_get.calls) or not any("rows=3" in c for c in pf.http_get.calls):
            fail("the title fallback must ask PubMed and Crossref for three candidates each")
        if pf.name_parts("2020 - Example - A title [PMID 5]") != ("2020", "Example", "A title") \
                or pf.name_parts("2020 Example - A title") != ("2020", "Example", "A title") \
                or pf.name_parts("Example et al. - 2020 - A title") != ("2020", "Example et al.", "A title") \
                or pf.name_parts("Just a title") != ("", "", "Just a title"):
            fail("name_parts must read year, author and title from a file name, Zotero's order included")
        if not pf.same_author("Berglundh T", "Berglundh") or not pf.same_author("M\u00fcller et al", "Muller") \
                or not pf.same_author("Berglundh, Lindhe", "Berglundh") or pf.same_author("Lindhe and Berglundh", "Berglundh") \
                or pf.same_author("Other", "Example") or pf.same_author("", "Example"):
            fail("same_author must compare the first surname only, without case, accents or initials")
        if pf.title_numbers("Outcomes after 10 years, Part II") != [2, 10] or pf.title_numbers("five-year Part V") != [5, 5] \
                or pf.title_numbers("Part IV and part 4") != [4, 4] or pf.title_numbers("short implants v long implants") != [] \
                or pf.title_numbers("Stage III periodontitis, grade C") != [3]:
            fail("title_numbers must read digits, number words, and roman numerals only after Part, Stage and the like")


def test_paper_fetch_library_commands() -> None:
    """library rebuild-index writes one row per PDF on disk, keeping known rows without a
    lookup and resolving unknown tags once; library stats counts topics, untagged files
    and groups of files with the same bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        papers = pathlib.Path(tmp) / "papers"
        a, b = papers / "Topic A", papers / "Topic B"
        a.mkdir(parents=True)
        b.mkdir()
        same = b"%PDF-1.4 the same bytes\n"
        known = a / "2020 Example - Invented test paper on bone levels - Invented J [PMID 1001].pdf"
        known.write_bytes(same)
        (a / "old name [PMID 1003].pdf").write_bytes(b"%PDF-1.4 scan\n")
        (a / "[DOI 10.1234_invented.1005].pdf").write_bytes(b"%PDF-1.4 by doi\n")
        (b / "[PMID 4040].pdf").write_bytes(b"%PDF-1.4 unknown pmid\n")
        (b / "copy [PMID 1001].pdf").write_bytes(same)
        (b / "no tag here.pdf").write_bytes(b"%PDF-1.4 no tag\n")
        (b / "[DOI 10.1234_invented_2020_123].pdf").write_bytes(b"%PDF-1.4 brackets in the doi\n")
        (b / "[DOI 10.9999_nothing].pdf").write_bytes(b"%PDF-1.4 doi that resolves nowhere\n")
        pf = load_paper_fetch(papers, [
            ("id=1003", pubmed_summary("1003", "Invented scan with a DOI inside", "10.1234/invented.1003")),
            ("id=1005", pubmed_summary("1005", "Invented paper found by its DOI tag", "10.1234/invented.1005")),
            ("id=1006", pubmed_summary("1006", "Invented paper with brackets in its DOI", "10.1234/invented(2020)123")),
            ("invented.1005%5Bdoi%5D", pubmed_found("1005")),
            ("invented%282020%29123%5Bdoi%5D", pubmed_found("1006")),
            ("invented_2020_123%5Bdoi%5D", pubmed_found()),
            ("nothing%5Bdoi%5D", pubmed_found()),
            ("id=4040", json.dumps({"result": {"uids": ["4040"], "4040": {"uid": "4040", "error": "no such record"}}}).encode()),
        ])
        pf.doi_in_pdf = lambda pdf: "10.1234/invented(2020)123" if "2020_123" in pdf.name else ""
        pf.write_index([{"saved_at": "2026-01-01T00:00:00", "topic": "Topic A", "pmid": "1001",
                         "doi": "10.1234/invented.1001", "title": "Invented test paper on bone levels",
                         "file": "Topic A/" + known.name, "sha256": pf.sha256_of(known), "license": "CC BY"},
                        {"saved_at": "2026-01-01T00:00:00", "topic": "Topic A", "pmid": "1999",
                         "file": "Topic A/gone [PMID 1999].pdf"}])
        code, text = printed(pf.rebuild_index)
        rows = pf.index_rows()
        expected = [("Topic A/" + known.name, "1001"), ("Topic A/[DOI 10.1234_invented.1005].pdf", "1005"),
                    ("Topic A/old name [PMID 1003].pdf", "1003"),
                    ("Topic B/[DOI 10.1234_invented_2020_123].pdf", "1006"), ("Topic B/[DOI 10.9999_nothing].pdf", ""),
                    ("Topic B/[PMID 4040].pdf", "4040"), ("Topic B/copy [PMID 1001].pdf", "1001")]
        if code != 0 or [(r["file"], r["pmid"]) for r in rows] != expected:
            fail(f"rebuild-index rows: expected {expected!r}, got {[(r['file'], r['pmid']) for r in rows]!r}: {text}")
        if rows[0]["license"] != "CC BY" or rows[6]["license"] != "CC BY" or rows[6]["title"] != rows[0]["title"]:
            fail("a known row must be kept, also for a second file with the same bytes")
        if rows[1]["doi"] != "10.1234/invented.1005" or rows[2]["title"] != "Invented scan with a DOI inside":
            fail(f"unknown tags must be resolved, got {rows[1]!r} {rows[2]!r}")
        if rows[3]["doi"] != "10.1234/invented(2020)123":
            fail(f"a DOI tag that cannot be read back must fall back to the DOI inside the PDF, got {rows[3]!r}")
        if rows[4]["doi"] or rows[4]["title"] or rows[4]["source"] != "on disk":
            fail(f"a DOI read from a name that resolves nowhere must not be stored, got {rows[4]!r}")
        if rows[5]["title"] or rows[5]["source"] != "on disk" or rows[5]["oa_status"] != "unknown":
            fail(f"a PMID tag that matches no paper keeps a row with the PMID and file only, got {rows[5]!r}")
        if any(len(r["sha256"]) != 64 for r in rows):
            fail("every row must carry the file's sha256")
        if any("id=1001" in call for call in pf.http_get.calls):
            fail("a row the index already holds must cost no lookup")
        last = text.strip().splitlines()[-1]
        if "kept 2 | added 3 | no metadata 2 | dropped 1 | files without a tag 1" not in last or "NO_TAG  Topic B/no tag here.pdf" not in text:
            fail(f"rebuild-index must report kept, added, no metadata, dropped and untagged, got: {text}")

        # The next rebuild resolves placeholder rows again: the DOI is known now, the PMID still is not
        answers = list(pf.http_get.answers) + [
            ("id=1007", pubmed_summary("1007", "Invented paper that resolves on the second try", "10.9999/nothing")),
            ("nothing%5Bdoi%5D", pubmed_found("1007"))]
        pf.http_get = FakeNetwork([a for a in answers if a[0] != "nothing%5Bdoi%5D" or a[1] != pubmed_found()])
        code, text = printed(pf.rebuild_index)
        rows = pf.index_rows()
        if code != 0 or rows[4]["title"] != "Invented paper that resolves on the second try" or rows[4]["doi"] != "10.9999/nothing":
            fail(f"a placeholder row must be resolved again on the next rebuild, got {rows[4]!r}: {text}")
        if rows[5]["title"] or "kept 5 | added 1 | no metadata 1 | dropped 0" not in text.strip().splitlines()[-1]:
            fail(f"a placeholder that still resolves nowhere stays one, and full rows are kept, got: {text}")

        code, text = printed(pf.library_stats)
        lines = text.splitlines()
        if code != 0 or lines[1].split() != ["3", "Topic", "A"] or lines[2].split() != ["5", "Topic", "B"]:
            fail(f"stats must count PDFs per topic, got: {text}")
        if "PAPERS  8 PDF files in 2 topic folders | 7 index rows" not in text:
            fail(f"stats must count files and index rows, got: {text}")
        if "NO_TAG  1 file(s)" not in text or "Topic B/no tag here.pdf" not in text:
            fail(f"stats must list files without a tag, got: {text}")
        if "DUPLICATE_BYTES  1 group(s)" not in text or "Topic B/copy [PMID 1001].pdf" not in text:
            fail(f"stats must list groups of files with the same bytes, got: {text}")
    help_text = run([sys.executable, PAPER_FETCH, "library", "--help"]).stdout
    if "rebuild-index" not in help_text or "stats" not in help_text:
        fail("paper_fetch.py library --help must list rebuild-index and stats")


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

        # Resolver links are not repository copies: doi.org and pubmed instances alone give no candidate
        resolver_only = {"results": [{"pids": [{"scheme": "doi", "value": "10.1234/invented.601"}], "instances": [
            {"accessRight": {"label": "OPEN"}, "urls": ["https://doi.org/10.1234/invented.601"]},
            {"accessRight": {"label": "OPEN"}, "urls": ["https://dx.doi.org/10.1234/invented.601",
                                                        "https://pubmed.ncbi.nlm.nih.gov/601"]}]}]}
        pf.http_get = FakeNetwork([("api.openaire.eu/graph/v3/research-products", json.dumps(resolver_only).encode())])
        if pf.openaire_pdfs(paper) != []:
            fail(f"OpenAIRE: a doi.org or dx.doi.org link is a resolver, not a copy, got {pf.openaire_pdfs(paper)!r}")
        if [label for label, _ in pf.pdf_candidates(paper)]:
            fail("a record with only doi.org and pubmed instances must yield no candidate")

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


def test_iasella_example_interval() -> None:
    """The example's CI note states n per group, df and a z-based screen that the calculator reproduces."""
    data = json.loads((ROOT / "examples" / "iasella-statistical-forensics-report-data.json").read_text(encoding="utf-8"))
    metrics = {metric.get("label"): metric for metric in data["metrics"]}
    note = str(metrics.get("Approx CI", {}).get("note", ""))
    n = re.search(r"n = (\d+) per group", note)
    screen = re.search(r"z-based screen[^0-9-]*(-?\d+\.\d) to (-?\d+\.\d) mm", note)
    if not n or not screen or "df = " not in note:
        fail(f"the Approx CI note must state n per group, df and the z-based screen, got {note!r}")
    groups = []
    for label in ("Horizontal Change RP", "Horizontal Change EXT"):
        value = re.search(r"(-?\d+\.\d) \+/- (\d+\.\d) mm", str(metrics.get(label, {}).get("value", "")))
        if not value:
            fail(f"metric {label} must read like '-1.2 +/- 0.9 mm'")
        groups.append((value.group(1), value.group(2)))
    result = json.loads(run([
        sys.executable, "dental-statistical-forensics/scripts/stats_forensics_calculator.py", "continuous",
        "--mean-a", groups[0][0], "--sd-a", groups[0][1], "--n-a", n.group(1),
        "--mean-b", groups[1][0], "--sd-b", groups[1][1], "--n-b", n.group(1),
    ]).stdout)
    stated = [float(screen.group(1)), float(screen.group(2))]
    if any(abs(a - b) > 0.1 for a, b in zip(stated, result["ci95"])):
        fail(f"the z-based screen {stated} does not match the calculator's {result['ci95']} within 0.1 mm")


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


def test_paper_fetch_notice_pdf() -> None:
    """A one-page PDF under 60 KB is a repository notice, not the paper: it is never saved."""
    one_page = b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n" \
               b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n" \
               b"3 0 obj << /Type /Page /Parent 2 0 R >> endobj\n%%EOF\n"
    two_pages = one_page.replace(b"/Count 1", b"/Count 2") + b"4 0 obj << /Type /Page /Parent 2 0 R >> endobj\n"
    big_one_page = one_page + b"%" + b"x" * 70_000 + b"\n"
    found = {"results": [{"pids": [{"scheme": "doi", "value": "10.1234/invented.700"}], "instances": [
        {"accessRight": {"label": "OPEN"}, "urls": ["https://repository.example/700.pdf"]}]}]}
    with tempfile.TemporaryDirectory() as tmp:
        pf = load_paper_fetch(pathlib.Path(tmp) / "papers", [
            ("api.openaire.eu/graph/v3/research-products", json.dumps(found).encode()),
            ("https://repository.example/700.pdf", one_page),
        ])
        if not pf.looks_like_notice(one_page) or pf.looks_like_notice(two_pages) or pf.looks_like_notice(big_one_page):
            fail("looks_like_notice must flag only a one-page PDF under 60 KB")
        paper = invented_paper(doi="10.1234/invented.700")
        data, _, _, failed = pf.download_pdf(paper)
        if data is not None or failed != [("https://repository.example/700.pdf", "notice")]:
            fail(f"a one-page notice PDF must be a failed link with reason 'notice', got {data!r} {failed!r}")
        lines = pf.open_manually_lines(failed)
        if "one-page notice" not in lines[0] or lines[1] != "https://repository.example/700.pdf":
            fail(f"OPEN_MANUALLY must say the free copy is a notice, got {lines!r}")
        pf.http_get = FakeNetwork([("api.openaire.eu/graph/v3/research-products", json.dumps(found).encode()),
                                   ("https://repository.example/700.pdf", two_pages)])
        data, label, _, _ = pf.download_pdf(paper)
        if data != two_pages or label != "open-access copy via OpenAIRE":
            fail("a two-page PDF must be saved as before")


# ---------- generate_dental_image.py, tested offline with a fake Images API ----------

def env_without_key() -> dict[str, str]:
    return {name: value for name, value in os.environ.items() if name != "OPENAI_API_KEY"}


def test_image_generator_cli_offline() -> None:
    """--help and --dry-run need no key; a missing key is one sentence and exit code 2."""
    env = env_without_key()
    helped = run([sys.executable, IMAGE_SCRIPT, "--help"], env=env)
    for flag in ("--model", "--size", "--quality", "--brand-asset", "--dry-run"):
        if flag not in helped.stdout:
            fail(f"image generator --help must list {flag}")
    if "OPENAI_API_KEY" not in helped.stdout:
        fail("image generator --help must name OPENAI_API_KEY")

    dry = run([sys.executable, IMAGE_SCRIPT, "--prompt", "Healthy periodontium", "--style", "infographic",
               "--size", "1536x1024", "--quality", "low", "--output", "x.webp", "--dry-run"], env=env)
    request = json.loads(dry.stdout)
    body = request["body"]
    if request["url"] != "https://api.openai.com/v1/images/generations":
        fail("dry run must target the generations endpoint")
    if body["model"] != "gpt-image-2.5-sunburst" or body["size"] != "1536x1024" or body["quality"] != "low":
        fail("dry run body does not carry the model, size and quality")
    if body["output_format"] != "webp" or not body["prompt"].startswith("Design a clean dental infographic"):
        fail("dry run body must derive the format from the file name and prefix the style preset")
    if not body["prompt"].endswith("Subject: Healthy periodontium") or body["n"] != 1:
        fail("dry run body must end with the user prompt and ask for one image")

    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "no-key.png"
        missing = subprocess.run([sys.executable, IMAGE_SCRIPT, "--prompt", "x", "--output", str(target)],
                                 cwd=ROOT, text=True, capture_output=True, env=env)
        lines = missing.stdout.strip().splitlines()
        if missing.returncode != 2 or len(lines) != 1 or "OPENAI_API_KEY" not in lines[0]:
            fail("a missing key must print one sentence naming OPENAI_API_KEY and exit 2")
        if target.exists():
            fail("a missing key must not write an output file")


class FakeImagesApi:
    """Stands in for urlopen inside generate_dental_image.py. Records every request and answers
    with one fixed image, or raises the given error. Nothing reaches the network."""

    def __init__(self, image_bytes: bytes) -> None:
        self.image_bytes = image_bytes
        self.answer: object = None
        self.requests: list[tuple[str, dict[str, str], dict]] = []

    def __call__(self, request, timeout: float = 0) -> io.BytesIO:
        self.requests.append((request.full_url, dict(request.header_items()),
                              json.loads(request.data.decode("utf-8"))))
        if isinstance(self.answer, Exception):
            raise self.answer
        answer = self.answer or {
            "created": 1, "size": "1024x1024", "quality": "low", "output_format": "png",
            "data": [{"b64_json": base64.b64encode(self.image_bytes).decode("ascii")}],
            "usage": {"output_tokens": 5, "total_tokens": 9},
        }
        return io.BytesIO(json.dumps(answer).encode("utf-8"))


def load_image_generator(fake: FakeImagesApi):
    """Load generate_dental_image.py as a fresh module whose urlopen is the fake."""
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("image_generator_under_test", ROOT / IMAGE_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = keep
    module.urlopen = fake
    return module


def test_image_generator_fake_api() -> None:
    """Request body, headers and the saved file, checked against a fake Images API."""
    pixels = b"\x89PNG\r\n\x1a\nfake-image-bytes"
    key = "test-key-not-real"
    fake = FakeImagesApi(pixels)
    module = load_image_generator(fake)
    kept = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = key
    try:
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            asset = folder / "logo.png"
            asset.write_bytes(pixels)
            output = folder / "out" / "implant.png"
            code, text = printed(module.main, ["--prompt", "Implant cross-section", "--quality", "low",
                                               "--size", "1024x640", "--output", str(output)])
            if code != 0 or output.read_bytes() != pixels:
                fail("a generation must exit 0 and write the decoded image bytes")
            if key in text:
                fail("the API key must never be printed")
            url, headers, body = fake.requests[0]
            if url != module.GENERATIONS_URL or headers.get("Authorization") != f"Bearer {key}":
                fail("the generation must go to the generations endpoint with a bearer key")
            if (body["model"] != module.DEFAULT_MODEL or body["size"] != "1024x640" or body["quality"] != "low"
                    or body["output_format"] != "png" or body["n"] != 1 or "images" in body):
                fail(f"unexpected generation body: {body}")
            if not body["prompt"].startswith("Create a professional medical/clinical illustration") \
                    or not body["prompt"].endswith("Subject: Implant cross-section"):
                fail("the clinical preset must wrap the user prompt")

            branded = folder / "branded.jpg"
            code, _ = printed(module.main, ["--prompt", "Post-op care", "--style", "patient-friendly",
                                            "--brand-asset", str(asset), "--output", str(branded)])
            url, _, body = fake.requests[1]
            if code != 0 or branded.read_bytes() != pixels or url != module.EDITS_URL:
                fail("a brand asset must route the request to the edits endpoint and still save the image")
            expected = "data:image/png;base64," + base64.b64encode(pixels).decode("ascii")
            if body.get("images") != [{"image_url": expected}] or body["output_format"] != "jpeg":
                fail(f"the brand asset must travel as a data URL and .jpg must mean jpeg: {body}")
            if "brand asset" not in body["prompt"] or not body["prompt"].startswith("Create a friendly"):
                fail("the brand note must follow the patient-friendly preset")

            # A .webp asset must be accepted from its suffix alone, whatever the system mime table says
            webp_asset = folder / "logo.webp"
            webp_asset.write_bytes(pixels)
            code, _ = printed(module.main, ["--prompt", "Post-op care", "--brand-asset", str(webp_asset),
                                            "--output", str(folder / "branded-webp.png")])
            _, _, body = fake.requests[2]
            if code != 0 or body.get("images") != [{"image_url": "data:image/webp;base64,"
                                                                 + base64.b64encode(pixels).decode("ascii")}]:
                fail(f"a .webp brand asset must be accepted and sent as image/webp: code {code}, {body.get('images')}")
            (folder / "logo.gif").write_bytes(pixels)
            code, text = printed(module.main, ["--prompt", "x", "--brand-asset", str(folder / "logo.gif"),
                                               "--output", str(folder / "gif.png")])
            if code != 1 or "png, jpg or webp" not in text:
                fail("an unsupported asset suffix must exit 1 with the plain message")

            module.MAX_ASSET_BYTES = len(pixels) - 1
            sent = len(fake.requests)
            code, text = printed(module.main, ["--prompt", "x", "--brand-asset", str(asset),
                                               "--output", str(folder / "big.png")])
            module.MAX_ASSET_BYTES = 15_000_000
            if code != 1 or "under 0 MB" not in text or len(fake.requests) != sent or (folder / "big.png").exists():
                fail("an oversized brand asset must exit 1 before any request and write nothing")

            fake.answer = {"created": 2, "data": []}
            code, text = printed(module.main, ["--prompt", "x", "--output", str(folder / "empty.png")])
            if code != 1 or "no image" not in text or (folder / "empty.png").exists():
                fail("an answer without an image must exit 1 and write nothing")

            fake.answer = urllib.error.HTTPError(
                module.GENERATIONS_URL, 400, "Bad Request", {},
                io.BytesIO(b'{"error": {"message": "Invalid size 16x16 for ' + key.encode() + b'"}}'))
            code, text = printed(module.main, ["--prompt", "x", "--size", "16x16", "--output", str(folder / "bad.png")])
            if code != 1 or "HTTP 400" not in text or "Invalid size 16x16" not in text or key in text:
                fail("an API error must exit 1, quote the message and mask the key")
    finally:
        if kept is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = kept


TESTS = [
    test_required_skills_present,
    test_skill_frontmatter_validator,
    test_protocol_versions,
    test_openai_metadata,
    test_statistical_forensics_references_exist,
    test_examples_and_artifact_renderer,
    test_helper_scripts,
    test_image_generator_cli_offline,
    test_image_generator_fake_api,
    test_paper_fetch_offline,
    test_paper_fetch_version_folder,
    test_paper_fetch_webp_figures,
    test_paper_fetch_pmid_without_doi,
    test_paper_fetch_certificate_retry,
    test_paper_fetch_import_needs_yes,
    test_paper_fetch_mount_guard,
    test_paper_fetch_file_names,
    test_paper_fetch_index_columns,
    test_paper_fetch_import_folder,
    test_paper_fetch_title_guard,
    test_paper_fetch_library_commands,
    test_paper_fetch_sources_and_safety,
    test_paper_fetch_notice_pdf,
    test_fixtures,
    test_iasella_golden_concepts,
    test_iasella_example_interval,
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
