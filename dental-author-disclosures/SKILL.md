---
name: dental-author-disclosures
description: >-
  Use when reviewing the disclosed or publicly documented financial and non-financial
  relationships of authors of a dental paper, including grants, consulting, speaking,
  employment, patents, equity, and professional affiliations. Produce a sourced
  relationship register and explain potential relevance without alleging bias or misconduct.
---

# Dental Author Disclosures

**Skill protocol version:** 2026.09.30
**Methodology Review Date:** 2026-09-30 (added step 0 on the reviewer's own relationships, "Sharing, sources and retention", the expanded source standard with the ICMJE 36-month window, and the register hand-off as a report section table; earlier the same day "How relationships inform appraisal" and "Full text first"; previous review 2026-09-27)

## Scope

Document relationships, not a blacklist or a credibility score. A relationship can
be relevant to interpretation without proving biased research. Never infer payment,
commercial sponsorship, or misconduct from a name, conference appearance, membership,
coauthorship, or missing search result. Do not automatically reduce a paper's score.

## Full text first

The funding and disclosure statements are in the full text. An abstract rarely has them.
When the runtime can run scripts, get the PDF with `dental-paper-fetch` before building
the register. Never build the register from the abstract when a free full text exists.
Otherwise ask the user for a PDF they may lawfully share. State in the search scope
whether the full text, part of it or only the abstract was read. An author address that
`dental-paper-fetch` prints is for a full-text request only and never enters the register.

## Procedure

0. State the reviewer's own relationships to the studied products and organisations
   before starting, for example "founder of a dental education site; no relationship
   with the manufacturer studied". Write "none" when there are none. The reviewer is the
   person the register is for: ask them when the statement is not known, and put it at
   the top of the register.
1. Establish the paper: title, DOI, publication and study dates, manufacturer/product
   studied, author names, affiliations, and ORCID where available. Disambiguate each
   person using at least two matching details. Leave ambiguous identities unresolved.
2. State retrieval capability and coverage. If browsing or full text is unavailable,
   extract from supplied documents only and provide a search plan. Never pretend a
   search was performed. An abstract rarely contains complete disclosure information.
3. Read the article's funding and disclosure statements, supplements, protocol and
   registration first. Preserve the distinction between institution and individual.
4. Search public primary sources: author/university disclosures, funder/grant records,
   company advisory or speaker pages, dated official meeting programmes, and patent
   records. Search every author, but report which were actually checked and where a
   bounded search stopped. Secondary reporting is a lead, not proof of a relationship.
5. Record study-period evidence separately from current relationships. Use the
   journal's stated disclosure period. If the journal uses the ICMJE disclosure form,
   the window is the 36 months before submission for every item other than support
   for the submitted work, which has no time limit. If the period is unknown, state
   the searched dates without inventing a universal disclosure obligation. A newer relationship is not evidence
   that it existed during the study. A now-missing webpage does not prove it ended.
6. Classify: employment; consultancy/advisory; speaking/honoraria; research funding;
   travel/material support; patents/equity; non-financial/professional affiliation;
   other/unclear. Paid status remains unknown unless the source establishes it.
   Professional societies and educational foundations are not automatically vendors.
7. Compare each source with the paper's disclosure. Say "not found in the supplied
   disclosure" rather than "concealed". Explain the possible connection to the studied
   intervention, sponsor role, design, analysis or reporting; do not infer actual bias.
8. Keep conflicting sources and identity uncertainties visible. Hand off methodological
   concerns to `research-critic`; body-of-evidence questions to `clinical-evidence-reviewer`.

## Required output

Start with a plain-language finding and scope/date of the search. Then produce:

| Author and identity match | Organisation | Relationship and paid status | Relevant dates | Paper disclosure | Public source, short supporting excerpt, access date | Status | Relevance and limits |
|---|---|---|---|---|---|---|---|

Statuses: **declared in paper**, **externally documented**, **identity unresolved**,
**relationship unclear**, **no evidence located in bounded search**, **not searched**.
Separate confirmed rows from unresolved leads. Every confirmed external relationship
requires a directly supporting source URL, date and excerpt. Avoid long quotations.
Never fabricate dates or source links. Exclude private contact and unrelated personal data.

Finish with missing documents, authors not covered, and any question requiring human
review. Hand off the register under `author_relationships`, with `search_scope`,
`access_date`, `identity_match`, `organisation`, `relationship_type`, `paid_status`,
`relationship_dates`, `paper_disclosure`, `source_url`, `supporting_excerpt`, `status`,
and `relevance_limits` per row. For `dental-evidence-report-artifact`, the register is
one section with the optional `table` of `columns` and `rows` that its JSON shape
allows. The section body carries the paper's own disclosure statement and the count of
externally documented rows; the table holds only the rows the user approved by name
(see "Sharing, sources and retention").

## How relationships inform appraisal

The register gives no score. A relationship informs a judgement only through a
mechanism, and the reviewer writes one sentence saying how the funding and
relationship record (paper and register) changed, or did not change, the judgements.
In `research-critic`: when no protocol or analysis plan is available and the
investigators have important financial relationships, concern about selection of the
reported result may be raised ([Cochrane Handbook 7.8.3](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-07#section-7-8-3)).
In `clinical-evidence-reviewer`: the register may support a judgement on indirectness,
when comparator or outcome choices favour the sponsor, and on publication bias, when
the evidence comes from a number of small studies, most of them commercially funded.
No automatic downgrade in either skill.

## Sharing, sources and retention

- The register is internal work product. A shared artifact (report, critique,
  journal-club handout) carries the paper's own disclosure statement plus a count of
  externally documented rows, for example "2 of 6 authors have an externally documented
  relationship". It names a row only when the user approves that named row.
- A shared row needs a confirmed identity (two matching details, step 1) and a primary
  source URL with its access date. A row with an unresolved identity or a secondary
  source only is never shared.
- Sources are public primary records: the paper, journal and funder disclosure pages,
  company pages, dated official meeting programmes, patent and trial registers. No
  social media, no personal profiles, no paid people-search data.
- Keep no copy of the register after the review unless the user asks for one.

## Source standard

- [ICMJE Recommendations, section II.B](https://www.icmje.org/recommendations/browse/roles-and-responsibilities/author-responsibilities--conflicts-of-interest.html),
  read on 2026-09-30: financial and non-financial relationships require transparent
  consideration; the existence of a relationship does not by itself establish improper
  influence.
- [ICMJE Disclosure Form](https://www.icmje.org/disclosure-of-interest/), version
  updated February 2021, read on 2026-09-30: support for the submitted work is reported
  without time limit; for every other item the window is the past 36 months.
- [Cochrane Handbook version 6.5, chapter 7, section 7.8](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-07#section-7-8),
  last updated August 2022, read on 2026-09-30: source of funding and conflicts of
  interest of the authors of included studies, and the routes by which they may inform
  a risk-of-bias judgement.
- Lundh A, Lexchin J, Mintzes B, Schroll JB, Bero L. Industry sponsorship and research
  outcome. Cochrane Database of Systematic Reviews 2017, MR000033, PMID 28207928,
  DOI 10.1002/14651858.MR000033.pub3, PubMed record read on 2026-09-30: sponsorship of
  drug and device studies by the manufacturer leads to more favourable efficacy results
  and conclusions than sponsorship by other sources. This is the reason to ask, not a
  verdict on any one paper.
- [TACIT, Tool for Addressing Conflicts of Interest in Trials](https://methods.cochrane.org/bias/resources/tool-addressing-conflicts-interest-trials-tacit),
  Cochrane Bias Methods Group, read on 2026-09-30: in development. An unpublished
  version is available on that page, which says a manuscript will be submitted for
  publication in early 2026. Use its guidance questions as a checklist, not as a
  published standard.

## Example invocation

"Review author relationships for this DOI and supplied full text. Distinguish declared
relationships, verified external evidence and unresolved identities. Include every
author in the coverage log. Do not infer that a lecture was paid."
