---
name: dental-author-disclosures
description: >-
  Use when reviewing the disclosed or publicly documented financial and non-financial
  relationships of authors of a dental paper, including grants, consulting, speaking,
  employment, patents, equity, and professional affiliations. Produce a sourced
  relationship register and explain potential relevance without alleging bias or misconduct.
---

# Dental Author Disclosures

**Skill protocol version:** 2026.05.16
**Methodology Review Date:** 2026-09-27

## Scope

Document relationships, not a blacklist or a credibility score. A relationship can
be relevant to interpretation without proving biased research. Never infer payment,
commercial sponsorship, or misconduct from a name, conference appearance, membership,
coauthorship, or missing search result. Do not automatically reduce a paper's score.

## Procedure

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
   journal's stated disclosure period; if unknown, state the searched dates without
   inventing a universal disclosure obligation. A newer relationship is not evidence
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
and `relevance_limits` per row. This is an optional narrative appendix for the report
artifact, not an unsupported addition to its machine-readable rendering schema.

## Source standard

[ICMJE disclosure recommendations](https://www.icmje.org/recommendations/browse/roles-and-responsibilities/author-responsibilities--conflicts-of-interest.html):
financial and non-financial relationships require transparent consideration; the
existence of a relationship does not by itself establish improper influence.

## Example invocation

"Review author relationships for this DOI and supplied full text. Distinguish declared
relationships, verified external evidence and unresolved identities. Include every
author in the coverage log. Do not infer that a lecture was paid."
