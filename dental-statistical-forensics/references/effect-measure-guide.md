# Effect-Measure Guide

Use this when the outcome type or correct effect measure is unclear. Classify the data before judging the statistics.

| Outcome type | Dental examples | Preferred effect measures | Common traps |
|---|---|---|---|
| Continuous mm | Ridge width, buccal height, marginal bone level, probing depth, CAL, keratinized tissue width | Mean difference, 95% CI, SD/IQR/range, MCID or contextual threshold comparison | p-value without CI; SD ignored; mean interpreted as predictable individual outcome |
| Binary | Implant failure, membrane perforation, pocket closure yes/no, complication yes/no | Risk difference, relative risk, odds ratio, NNT/NNH when appropriate | OR interpreted as RR; no absolute risk; per-implant events treated as patient events |
| Ordinal | Radiographic scores, esthetic scales, pain categories | Ordinal model, median/IQR, proportional odds when appropriate | Treated as continuous without justification; collapsed categories post hoc |
| Count/rate | Number of complications, sites bleeding, adverse events | Rate ratio, incidence rate, Poisson/negative binomial where appropriate | Counts ignore exposure time or clustering |
| Time-to-event | Implant survival over loading time, time to complication | Kaplan-Meier, hazard ratio, censoring table, time under loading | Survival confused with success; no censoring/at-risk table |
| Diagnostic accuracy | CBCT detection, clinical diagnostic tests, peri-implantitis definitions | Sensitivity, specificity, LR+/LR-, PPV/NPV with prevalence, AUC, 95% CIs | No CI; threshold not prespecified; tooth/site units treated as patient units |
| Agreement/reliability | Examiner calibration, radiographic measurement reliability, scan agreement | ICC, kappa, Bland-Altman limits of agreement, measurement error | Correlation mistaken for agreement; effect smaller than measurement error |
| Digital accuracy | Intraoral scan trueness/precision, angular deviation, RMS deviation | RMS/mean/median deviation, angular deviation, precision SD, threshold comparison | Color-map overinterpretation; in-vitro result generalized to full-arch in vivo |
| Meta-analysis | Pooled MD/RR/OR/SMD | Fixed/random effects with rationale, heterogeneity, prediction interval, sensitivity analyses | Pooling incompatible designs/outcomes; SMD not back-translated |

## Approximation Boundaries

You may estimate approximate CIs from summary statistics only when the required data are present and the assumptions are stated.

Allowed:

- Approximate SE from SD and n.
- Approximate independent-group mean-difference CI from group SDs and n.
- SD/effect and SD/threshold ratios.
- Absolute risk difference from event counts.
- NNT/NNH from absolute risk difference when appropriate.
- Simple normal-approximation threshold-crossing estimates, clearly labeled as assumption-dependent.

Not allowed:

- Inferring paired correlations.
- Inventing missing SDs, event counts, n analyzed, or CIs.
- Presenting approximate calculations as exact.
- Making clinical decisions from arithmetic alone.

## Iasella-Style Dispersion Pattern

If a mean vertical change is favorable but SD and range are wide, do not write "predictable maintenance" unless individual data support that.

Example phrasing:

> The average effect is favorable, but individual-site variability is large; some treated sites still had clinically relevant loss. The data support an average treatment effect, not a predictable individual esthetic-zone outcome.

This pattern applies broadly: ridge preservation, sinus grafting, periodontal regeneration, soft-tissue augmentation, digital accuracy, and any outcome where individual-patient reliability matters.
