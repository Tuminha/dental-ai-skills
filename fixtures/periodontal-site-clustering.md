# Fixture: Periodontal Site-Level Clustering

## Prompt

A periodontal maintenance study analyzes 3,840 sites from 80 patients and reports that adjunctive air polishing reduced bleeding on probing from 28% to 22% with p<0.001 using site-level chi-square tests. The paper does not model clustering by patient, tooth, or site, and the primary clinical question is whether patients improved.

## Expected Flags

- Identify site-level measurements nested within teeth and patients.
- Flag inflated sample size and overprecise p-value.
- Request patient-level summaries or mixed-effects / GEE modeling.
- Ask whether the effect is clinically meaningful at the patient level.
- Separate statistical significance from clinical relevance.
- Warn that thousands of sites do not equal thousands of independent patients.
