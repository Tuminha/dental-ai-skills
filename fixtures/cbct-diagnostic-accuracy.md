# Fixture: CBCT Diagnostic Accuracy

## Prompt

A CBCT diagnostic accuracy study evaluates vertical root fracture detection in 92 extracted teeth from 41 patients. It reports sensitivity 0.91, specificity 0.84, and AUC 0.89. No 95% confidence intervals are reported. The threshold for a positive scan is not pre-specified. The reference standard is visual inspection after extraction, but blinding of CBCT readers to the reference standard is unclear.

## Expected Flags

- Select QUADAS-3 as the current preferred diagnostic accuracy tool.
- Use QUADAS-2 only if legacy compatibility is explicitly requested.
- Separate risk of bias from applicability.
- Flag missing CIs for sensitivity, specificity, and AUC.
- Flag unclear threshold pre-specification.
- Flag tooth-level units clustered within patients.
- Request likelihood ratios and prevalence-dependent PPV/NPV when clinically relevant.
