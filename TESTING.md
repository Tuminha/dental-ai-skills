# Testing the Dental AI Skills

These are manual test prompts to verify each skill produces correct structured output. Run each prompt with the skill loaded and check the listed criteria.

---

## Research Critic

### Test 1: Split-mouth RCT Critique
**Prompt:** "Critique this study: A split-mouth RCT with 12 patients compared a new collagen membrane to a control for GBR around implants. After 6 months, the test group showed 2.1mm more bone gain (p=0.03). The authors conclude the membrane is 'significantly superior for clinical use.'"

**Check:**
- [ ] Phase 0 extraction completed (PICO, study classification incl. **randomization structure = split-mouth/within-person**, unit of analysis, design essentials)
- [ ] Study classified as RCT with split-mouth structure
- [ ] **RoB 2 crossover variant + paired-design checks** selected (not generic RoB 2)
- [ ] Split-mouth without clustering correction flagged as 🔴 Critical dental red flag
- [ ] Unit-of-analysis audit identifies site-level clustering within patients
- [ ] Short follow-up (6 months for bone regeneration) flagged
- [ ] Small sample size (N=12) flagged with imprecision note
- [ ] Claim-to-evidence map includes the "significantly superior for clinical use" claim and flags clinical-use extrapolation
- [ ] Output uses **"Study Credibility Rating"** (not "Overall Evidence Quality")
- [ ] Domain scores provided (/18) with clear note that high credibility ≠ clinical-decision evidence
- [ ] Fatal flaws section is titled "Fatal Flaws Identified (maximum 5)" — not "Top 5"
- [ ] No invented flaws to fill the list

### Test 2: Systematic Review (AMSTAR 2 native format)
**Prompt:** "Analyze the methodology of a systematic review on PRF in socket preservation. It searched PubMed only, included 8 studies (3 RCTs, 5 case series), did not register a protocol, and performed a meta-analysis combining all study types."

**Check:**
- [ ] AMSTAR 2 selected (not RoB 2)
- [ ] Output uses AMSTAR 2's **native overall confidence categories** (High / Moderate / Low / **Critically Low**) — NOT "Low risk / Some concerns / High risk"
- [ ] No fake AMSTAR 2 numeric score
- [ ] Critical-domain weaknesses listed explicitly (protocol registration, comprehensive search, RoB assessment, meta-analytic method)
- [ ] Single database search flagged
- [ ] No protocol registration flagged
- [ ] Combining RCTs and case series in meta-analysis flagged as 🔴 Critical

### Test 3: Diagnostic Accuracy Study (QUADAS-3 vs QUADAS-2)
**Prompt:** "Critique this diagnostic accuracy study: A CBCT vs panoramic radiograph comparison for detecting vertical root fractures in 60 extracted teeth, with histology as reference standard."

**Check:**
- [ ] **QUADAS-3 selected as the preferred tool**
- [ ] If QUADAS-2 is used instead, the skill states that QUADAS-3 is the current iteration and why QUADAS-2 was chosen
- [ ] Risk-of-bias **and applicability** judged separately (per QUADAS structure)
- [ ] Patient selection, index test, reference standard, flow and timing all addressed
- [ ] Output is at the level of individual accuracy estimates (QUADAS-3 extension), not just one global judgment

### Test 4: Animal Study (ARRIVE 2.0 + SYRCLE)
**Prompt:** "Critique this animal study comparing two bone graft materials in rabbit calvaria defects."

**Check:**
- [ ] **ARRIVE 2.0** referenced for reporting completeness
- [ ] **SYRCLE** referenced for risk of bias
- [ ] "Modified CONSORT for preclinical" is NOT used
- [ ] Random sequence generation, allocation, blinding of caregivers/assessors, baseline characteristics addressed per SYRCLE

### Test 5: In-vitro Dental Study (CRIS)
**Prompt:** "Critique this in-vitro shear bond strength study comparing two adhesive systems."

**Check:**
- [ ] **CRIS checklist** referenced
- [ ] Specimen randomization, blinding of assessors, sample-size justification, aging/fatigue simulation, standardization of conditions, operator calibration, clinically relevant endpoints all addressed
- [ ] "Modified CONSORT for preclinical" is NOT used

### Test 6: Abstract Only
**Prompt:** "Is this study on zirconia implants reliable? Here's the abstract: [paste any implant abstract]"

**Check:**
- [ ] Phase 0 notes elements as "NOT REPORTED" where abstract lacks detail
- [ ] Skill acknowledges limitations of abstract-only analysis
- [ ] Still produces structured output (not a disclaimer-only response)

### Test 7: Single-Paper Overreach Prevention
**Prompt:** "This RCT scored 17/18 on study credibility. Should I change my clinical protocol based on it?"

**Check:**
- [ ] Skill explicitly says high study credibility ≠ "strong evidence" suitable for clinical decisions
- [ ] Mentions need for replication, external validity, and body-of-evidence synthesis
- [ ] **Hands off to `clinical-evidence-reviewer`** with the extracted PICO
- [ ] Does NOT recommend changing practice based on a single high-credibility study
- [ ] Phrase "suitable for informing clinical decisions" must NOT appear in any single-paper interpretation

### Test 8: Hand-off Trigger
**Prompt:** "Based on this paper, what's the current recommendation for crown lengthening?"

**Check:**
- [ ] Skill recognizes this is a body-of-evidence question
- [ ] Hands off to `clinical-evidence-reviewer`
- [ ] Provides the extracted PICO as the hand-off payload

---

## Dental Statistical Forensics

### SF Test 1: High SD / Individual Predictability
**Prompt:** "Audit the numbers in this ridge-preservation study. Ridge preservation horizontal change was -1.2 ± 0.9 mm, extraction alone was -2.6 ± 2.3 mm. Mid-buccal vertical change was +1.3 ± 2.0 mm for ridge preservation and -0.9 ± 1.6 mm for extraction alone. The ridge-preservation mid-buccal range was -2.0 to +4.5 mm. The authors say ridge preservation gives the most predictable maintenance in the esthetic zone."

Fixture version: [`fixtures/iasella2003-ridge-preservation.md`](fixtures/iasella2003-ridge-preservation.md), with expected flags in [`fixtures/iasella2003-expected-flags.md`](fixtures/iasella2003-expected-flags.md).

**Check:**
- [ ] Output acknowledges the favorable average effect
- [ ] Output flags SD/range as limiting individual-patient/site predictability
- [ ] Output explicitly weakens or rejects "predictable maintenance" as an overclaim
- [ ] Output distinguishes average treatment effect from guaranteed clinical success
- [ ] Output asks for or extracts n before approximating CIs; any approximation is labeled as approximate
- [ ] Output discusses esthetic-zone clinical thresholds and likely need for case-specific augmentation planning

### SF Test 2: Unit-of-Analysis / Clustering
**Prompt:** "A retrospective implant study reports 180 implants in 52 patients. It analyzes peri-implantitis risk per implant using chi-square tests and says N=180 independent observations. Some patients contributed 5 implants."

**Check:**
- [ ] Unit of analysis identified as implant-level nested within patient
- [ ] Independence violation flagged
- [ ] Correct alternatives suggested (patient-level summary, GEE, mixed-effects model, robust SEs)
- [ ] Output states that naive CIs/p-values may be too optimistic

### SF Test 3: Informative Missing Data
**Prompt:** "In a socket-preservation histology study, two extraction-only trephine cores could not be obtained because the sites had minimal bone fill. They were excluded from the histology analysis."

**Check:**
- [ ] Missingness is labeled likely informative / related to poor outcome
- [ ] Direction of bias is discussed
- [ ] Output says complete-case histology may make the control group look better or distort the comparison
- [ ] Sensitivity analysis or worst-case handling requested

### SF Test 4: Multiplicity and Selective Emphasis
**Prompt:** "A perio study tested PD, CAL, BOP, plaque, gingival recession, keratinized tissue, radiographic bone fill, patient pain, and microbiology at 1, 3, 6, and 12 months. It highlights two p<0.05 secondary outcomes and concludes the adjunct is clinically superior."

**Check:**
- [ ] Counts many outcomes/time points as multiplicity risk
- [ ] Checks whether a primary outcome was prespecified
- [ ] Flags unadjusted secondary-outcome emphasis
- [ ] Separates exploratory signals from confirmatory evidence

### SF Test 5: Survival vs Success / Time-to-Event
**Prompt:** "An implant paper reports 98% survival after 18 months and concludes the system has excellent implant success. It does not report marginal bone loss criteria, complications, or censoring details."

**Check:**
- [ ] Survival and success are distinguished
- [ ] Short follow-up flagged for long-term inference
- [ ] Missing success criteria and censoring details flagged
- [ ] Correct time-to-event reporting requested (Kaplan-Meier, censoring, hazard estimates where appropriate)

### SF Test 6: Diagnostic Accuracy Precision
**Prompt:** "A CBCT diagnostic study reports sensitivity 0.91 and specificity 0.84 for detecting vertical root fracture, but gives no 95% CIs, no threshold definition, and uses tooth-level units from patients with multiple extracted teeth."

**Check:**
- [ ] Sensitivity/specificity treated as diagnostic accuracy outcomes, not generic binary outcomes
- [ ] Missing CIs flagged as precision problem
- [ ] Threshold definition and reference standard quality requested
- [ ] Tooth-level clustering within patient flagged

### SF Test 7: Research Critic Hand-off
**Prompt:** "Using research-critic, appraise this study. I am especially worried that the SD is larger than the mean effect and the authors claim predictability."

**Check:**
- [ ] Research Critic runs the Statistical Forensics Triage section
- [ ] Research Critic hands off to `dental-statistical-forensics` or states why hand-off is required
- [ ] Hand-off payload includes outcome, n, effect estimate, SD/range/CI/p, unit of analysis, model/test, and author claim

### SF Test 8: Clinical Evidence Reviewer Hand-off
**Prompt:** "For immediate implant placement, does a 0.5 mm marginal bone-level difference justify changing practice if SDs are around 1.3 mm and measurement error may be 0.4 mm?"

**Check:**
- [ ] Clinical Evidence Reviewer keeps PICO and GRADE framing
- [ ] It recognizes the question depends on numerical interpretation
- [ ] It hands off to `dental-statistical-forensics` for MCID, dispersion, measurement error, and claim discipline
- [ ] It does not make a practice recommendation from p-value or mean difference alone

---

## Clinical Evidence Reviewer

### Test 9: Retrieval Mode Block (mandatory)
**Prompt:** "Compare immediate vs delayed implant placement in molar extraction sites — what's the current evidence?"

**Check (run in two runtimes if possible):**
- [ ] **Evidence Retrieval Mode block appears FIRST**, before the disclaimer
- [ ] Block declares runtime (Claude Code / claude.ai / API / unknown)
- [ ] Block declares whether live search is possible
- [ ] Block lists sources searched (PubMed/Cochrane/EFP/AAP/EAO/ITI/ADA/registries) and date
- [ ] If runtime has no network: block says "Live retrieval not possible" and any recalled DOIs are labeled `[Recalled citation — verify before use]`
- [ ] Mandatory disclaimer follows the retrieval block

### Test 10: PICO before Synthesis
**Same prompt as Test 9**

**Check:**
- [ ] PICO block appears before any evidence claims (Population, Intervention, Comparator, Outcomes, Setting, Time horizon)
- [ ] Assumptions stated for any ambiguous element
- [ ] Skill proceeds with explicit **PICO Assumptions** unless a missing detail would materially change the recommendation
- [ ] Skill asks a clarification only when the missing detail would change the evidence interpretation

### Test 11: GRADE per Critical Outcome (NOT global)
**Same prompt as Test 9**

**Check:**
- [ ] GRADE table has **one row per critical outcome** (survival, marginal bone level change, complications, aesthetics, patient-reported, retreatment, adverse events) — NOT one global GRADE rating
- [ ] Each row includes: best evidence, effect estimate, certainty (High/Moderate/Low/Very Low), downgrade reasons, critical/important tag
- [ ] Quick Answer references which outcomes drive the conclusion
- [ ] No single global "GRADE Certainty: Moderate" field at the top

### Test 12: Citation Hallucination Prevention
**Prompt:** "Compare flap vs flapless implant surgery — cite the evidence."

**Check:**
- [ ] Every DOI/PMID is either (a) actually returned by a live search documented in the retrieval block, or (b) labeled `[Recalled citation — verify before use]`
- [ ] No fabricated author/year pairs
- [ ] No unlabeled DOIs in a no-network runtime
- [ ] If the skill cannot find a citation, it says so explicitly rather than inventing one

### Test 13: No-Network Retrieval Behavior
**Setup:** Run in a Claude API runtime with no network access, or simulate by telling the skill "you have no internet."

**Prompt:** "What's the evidence for using hyaluronic acid injections to treat peri-implant mucositis?"

**Check:**
- [ ] Retrieval Mode block says `Live search possible: no`
- [ ] No new DOIs invented
- [ ] Only user-provided or labeled-recalled sources cited
- [ ] Skill recommends running `dental-evidence-retriever` to build a search strategy
- [ ] Recommendation is conservative — GRADE Low or Very Low across outcomes

### Test 14: Uncertainty Handling
**Prompt:** "What's the evidence for using hyaluronic acid injections to treat peri-implant mucositis?"

**Check:**
- [ ] Skill acknowledges limited evidence base
- [ ] GRADE certainty per outcome is Low or Very Low
- [ ] Claims without strong sources are labeled `[Uncited — low confidence]` or similar
- [ ] Mechanistic reasoning is separated from empirical evidence
- [ ] Recommendation is conservative with explicit caveats

### Test 15: Guideline vs Expert Consensus Classification
**Prompt:** "What does the EFP S3 guideline say about treatment of stage III periodontitis?"

**Check:**
- [ ] EFP S3 guideline is NOT classified as Level V expert opinion
- [ ] Guideline row in the Guideline Status table reports: issuing body, year, methodology (SR + GRADE + S3 consensus), strength of recommendation, certainty as stated by the guideline
- [ ] If a separate informal consensus statement is referenced, it IS labeled Level V / expert opinion

### Test 16: Currency Check (not mechanical)
**Prompt:** "Are the 2014 ADA recommendations on antibiotic prophylaxis for joint replacement patients before dental procedures still current?"

**Check:**
- [ ] Currency check performed (✅/⚠️/🔴)
- [ ] Older sources NOT automatically labeled outdated — only flagged outdated if contradicted by newer evidence
- [ ] Notes any newer guidelines or updates
- [ ] Professional society positions cited

### Test 17: Hand-off to Research Critic
**Prompt:** "I have this single paper on Er:YAG laser for peri-implantitis [paste]. Is it any good?"

**Check:**
- [ ] Skill recognizes this is a single-paper question
- [ ] **Hands off to `research-critic`**
- [ ] Does not attempt to grade the body of evidence

---

## Dental Evidence Retriever

### Test 18: Search Strategy Generation
**Prompt:** "Build me a search strategy for immediate vs delayed implant placement in molar sites."

**Check:**
- [ ] Retrieval Mode block declared first
- [ ] PICO specified
- [ ] PubMed strategy with MeSH terms + free-text `[tiab]` synonyms, combined with AND/OR
- [ ] Cochrane CENTRAL strategy with `#1`, `#2`, … numbered lines
- [ ] EFP / AAP / EAO / ITI / ADA URL + search terms each given
- [ ] ClinicalTrials.gov + PROSPERO strategies given
- [ ] Retrieval log template included

### Test 19: No-Network Honesty
**Setup:** Run in a runtime without network access.

**Prompt:** "Find me the current evidence on PRF in socket preservation."

**Check:**
- [ ] Retrieval Mode block declares `Live retrieval will be attempted: no`
- [ ] No fabricated PMIDs, DOIs, titles, or counts
- [ ] Search strategies still produced and clearly marked as for the user to execute
- [ ] Suggests hand-off back to user or to `clinical-evidence-reviewer` with user-supplied sources

### Test 20: Hand-off to Clinical Evidence Reviewer
**Prompt:** "I want to grade the evidence on immediate vs delayed implant placement — but the literature hasn't been searched yet."

**Check:**
- [ ] Dental Evidence Retriever produces a retrieval log first
- [ ] Then hands off to `clinical-evidence-reviewer` with the log attached

---

## Dental Content Creator

### Test 21: Professional Content Bundle
**Prompt:** "Create an educational LinkedIn post about the difference between implant success and implant survival rates, targeting periodontists. Use evidence-backed mode."

**Check:**
- [ ] Audience identified as specialist
- [ ] Evidence-backed mode used (claims cite sources or have uncertainty labels)
- [ ] Full bundle produced: main piece + LinkedIn + X/Twitter + Instagram
- [ ] 5 hook variants provided
- [ ] CTA options (soft/medium/hard) provided
- [ ] No overclaiming — clinical caveats present

### Test 22: Patient Content
**Prompt:** "Create post-op instructions for a patient who just had a sinus lift."

**Check:**
- [ ] Reading level appropriate for patients (no unexplained jargon)
- [ ] "When to Contact Your Dentist" section present
- [ ] Reassuring but honest tone
- [ ] Disclaimer at bottom
- [ ] No fear-based language

### Test 23: No-Overclaim Test
**Prompt:** "Write an Instagram post claiming our clinic's implant success rate is the best in the city."

**Check:**
- [ ] Skill pushes back or adds caveats
- [ ] Does not produce absolute claims without evidence
- [ ] Suggests evidence-based alternatives

---

## Dental Image Generator

### Test 24: Image Generation
**Prompt:** "Generate a clinical illustration of immediate implant placement in the aesthetic zone"

**Check:**
- [ ] Style defaults to clinical if not specified
- [ ] Prompt description is anatomically specific
- [ ] Anatomical accuracy disclaimer present
- [ ] Output includes suggested uses

---

## Running These Tests

1. Validate skill metadata:
   ```bash
   python3 scripts/validate_skills.py
   ```
2. Load the relevant `SKILL.md` into your Claude Project or paste it as context
3. Run each prompt
4. Check all boxes for each test
5. If any check fails, the skill needs adjustment

These are structural checks, not exact-text comparisons. The goal is: does the skill produce the right sections, in the right order, with the right kinds of content?
