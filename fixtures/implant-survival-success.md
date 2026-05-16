# Fixture: Implant Survival vs Success

## Prompt

A retrospective implant study reports 98.4% implant survival after 18 months and concludes the implant system has "excellent clinical success." It does not report marginal bone loss thresholds, peri-implantitis definitions, biological complications, prosthetic complications, probing depths, bleeding on probing, or patient-level clustering. Some patients received up to six implants.

## Expected Flags

- Distinguish implant survival from implant success.
- Flag short follow-up after loading.
- Request success criteria and biological/prosthetic complication reporting.
- Flag implant-level analysis when multiple implants are nested within patients.
- Ask for Kaplan-Meier/censoring details if time-to-event claims are made.
- Weaken the conclusion to "high short-term survival in this cohort" rather than "excellent success."
