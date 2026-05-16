# Fixture: Split-Mouth Clustering

## Prompt

A split-mouth RCT compares two flap designs for recession coverage. Each of 28 patients contributes two contralateral defects. The paper reports 56 independent sites, analyzes final root coverage with an unpaired t-test, and concludes technique A is superior because mean root coverage was 82% versus 71% with p=0.04. No paired analysis, mixed model, or patient-level clustering adjustment is reported.

## Expected Flags

- Identify split-mouth / within-person design.
- Select RoB 2 crossover/within-person logic plus paired-design checks.
- Flag site-level analysis as non-independent.
- Request paired t-test, signed-rank test, mixed model, or equivalent paired analysis.
- Treat p=0.04 as fragile because clustering was ignored.
- Warn that confidence intervals are likely too narrow if independent-site analysis was used.
