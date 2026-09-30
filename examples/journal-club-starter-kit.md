# Dental Journal Club Starter Kit

A 30-minute first session for Claude or Codex. Use a paper you may lawfully upload.
Remove patient identifiers. This is an appraisal workflow, not a treatment recommendation.

## Run your first session

1. Install `research-critic`, `dental-statistical-forensics`,
   `dental-author-disclosures`, `dental-paper-fetch`, and
   `dental-evidence-report-artifact` using the README.
2. Get the PDF. In Claude Code or Codex, give the PMID or DOI and ask for
   `dental-paper-fetch`: it downloads the paper when a free legal copy exists. When it
   prints `NO_FREE_COPY` or `OPEN_MANUALLY`, use your own library access or the printed
   link. In a chat without scripts, upload a PDF you may lawfully share.
3. Provide the paper and supplements. With only an abstract, mark missing methods
   "not reported in the supplied abstract", not a confirmed study defect.
4. Paste the prompt below. Codex uses `$skill-name`; Claude Code uses `/skill-name`.
   In Claude's document chat, name the protocol in ordinary language.

> Use research-critic to extract the PICO, study design, unit of analysis and main
> claim before judging this paper. Select the appropriate native bias tool. Use
> dental-statistical-forensics for the main numerical claim and
> dental-author-disclosures for disclosed and verified public author relationships.
> State at the top whether you read the full text, part of it or only the abstract,
> and where the text came from.
> End with three journal-club questions, unresolved evidence, and a one-page summary.
> Do not recommend changing practice from one paper. If a tool or document is missing,
> state the limitation and complete the supported parts.

## Session agenda

| Minutes | Activity | Output |
|---|---|---|
| 0–5 | Extract question and methods | PICO and missing information |
| 5–15 | Compare claims with results | Three most consequential appraisal findings |
| 15–20 | Check numbers and disclosures | Numerical caveats and sourced relationship register |
| 20–30 | Discuss applicability | Three questions and what evidence is needed next |

## Safe first example

Use [the synthetic author-disclosure fixture](../fixtures/author-disclosures.md)
and its expected flags to check that your assistant does not turn an ambiguous
speaker listing into an allegation. For a worked numerical example, inspect
[the existing Iasella fixture](../fixtures/iasella2003-ridge-preservation.md).
These are test inputs, not new clinical results.

## Five-person usability pilot

Invite five volunteers before adding another app. Record platform, installation
completion, time to first useful appraisal, missing files, incorrect source claims,
and whether they would use it for their next journal club. No invitations have been
sent. Aim for four of five to complete installation unaided; this is a product
acceptance target, not a statistical study or a promised star count.
