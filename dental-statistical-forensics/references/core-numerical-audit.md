# Core Numerical Audit

Use this reference for every statistical-forensics review. The goal is to test whether the numerical results support the claim after accounting for effect magnitude, uncertainty, variability, design structure, missing data, and clinical meaning.

## The 12-Point Audit

| Check | What To Extract | Red Flags |
|---|---|---|
| Outcome type | Continuous, binary, ordinal, count/rate, time-to-event, diagnostic, agreement/reliability, digital accuracy, meta-analytic | Wrong effect measure or model for data type |
| Unit of analysis | Patient, implant, tooth, site, surface, sinus, scan, specimen, histologic field | Unit differs from randomization or measurement hierarchy |
| Effect estimate | MD, SMD, RR, OR, RD, HR, sensitivity/specificity, LR, ICC, Bland-Altman, RMS/angular deviation | Only p-value reported; effect size absent |
| Precision | 95% CI, SE, p-value, interval width | CI missing, wide, crosses null, or crosses clinical threshold |
| Dispersion | SD, IQR, range, coefficient of variation, SD/effect ratio, SD/MCID ratio | SD or range undermines predictability |
| Clinical threshold | MCID, accepted success/failure threshold, contextual clinical benchmark | No threshold; threshold treated as universal when contextual |
| Individual predictability | Proportion/range of patients/sites crossing unacceptable outcome | Group mean used to imply reliable individual outcome |
| Sample size and power | Planned vs achieved n, assumptions, smallest detectable difference | Underpowered secondary or subgroup claims |
| Missing data | Amount, reasons, balance, ITT/per-protocol/as-treated, sensitivity analysis | Missingness related to poor outcome or excluded failures |
| Multiplicity | Outcomes, time points, subgroups, interim looks, adjustment | Unadjusted multiple testing or cherry-picked secondary outcomes |
| Model appropriateness | Paired/unpaired, cluster, repeated measures, regression/ANCOVA, survival, diagnostic, meta-analysis model | Independent tests used for paired/clustered data |
| Claim discipline | Match conclusion to magnitude, precision, dispersion, missingness, model, and clinical relevance | "Predictable," "superior," or "clinically significant" unsupported by numbers |

## Severity Rules

- 🔴 **Critical** — likely changes the direction/trustworthiness of the conclusion.
- 🟡 **Moderate** — materially weakens interpretation but does not fully invalidate it.
- 🟢 **Minor** — reporting or interpretation issue with limited impact.

## Dispersion And Individual-Predictability Red Flags

Flag these explicitly:

- SD is greater than the mean effect.
- SD is greater than the domain MCID or contextual clinical threshold.
- Range includes clinically unacceptable failures despite favorable mean.
- IQR/range suggests a substantial subgroup did not benefit.
- Authors claim "predictable" or "reliable" using only mean differences.
- No range, IQR, individual plot, responder analysis, or threshold-crossing analysis is reported despite predictability claims.
- Effect size is smaller than plausible measurement error or examiner variability.

Interpretation language:

- Better: "The intervention shifts the average outcome favorably, but individual-site variability remains large."
- Avoid: "The intervention predictably preserves anatomy" unless SD/range/responder data support that claim.

## Precision Red Flags

Flag these explicitly:

- 95% CI is absent for primary continuous, binary, diagnostic, or survival outcomes.
- CI crosses the null.
- CI does not cross the null but crosses a clinically unimportant threshold.
- CI includes both trivial and clinically important effects.
- P-value is reported without effect size.
- "No significant difference" is interpreted as "no effect."
- "Statistically significant" is interpreted as clinically important without magnitude/threshold context.

When approximating CIs from summary statistics, label the calculation as approximate and state assumptions. Do not infer paired correlations, event counts, or SDs that were not reported.

## Missing-Data Red Flags

Flag these explicitly:

- Missingness is related to poor outcome.
- Failed implants/sites/cores are excluded from final analysis.
- Histology, radiographs, scans, or follow-up measurements are missing more often in one group.
- Reasons for missingness are not reported.
- Analysis is per-protocol only after meaningful attrition.
- Sensitivity analysis is absent when missing data could change the conclusion.

Severity guide:

- Missingness related to poor outcome is 🔴 Critical.
- Excluding failures from final analysis is 🔴 Critical unless handled transparently.
- Per-protocol-only analysis after attrition is at least 🟡 Moderate.

## Multiplicity Red Flags

Flag these explicitly:

- Many outcomes/time points/subgroups tested without prespecified primary outcome.
- Multiple anatomical sites or surfaces tested separately without adjustment.
- Subgroup findings described as definitive when exploratory.
- One significant p-value emphasized among many tests.
- Outcome switching or selective reporting suspected.

## Model Appropriateness Red Flags

Flag these explicitly:

- Split-mouth or paired data analyzed with independent tests.
- Multiple implants/teeth/sites/surfaces per patient analyzed as independent observations.
- Repeated measurements over time analyzed as separate independent tests.
- Baseline imbalance ignored when ANCOVA or adjusted analysis would be more appropriate.
- Survival data summarized only as crude percentages without follow-up/censoring context.
- Diagnostic accuracy estimates reported without CIs or threshold definition.
- Meta-analysis pools incompatible outcomes, time points, or designs.
