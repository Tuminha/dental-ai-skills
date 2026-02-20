# Testing the Dental AI Skills

These are manual test prompts to verify each skill produces correct structured output. Run each prompt with the skill loaded and check the listed criteria.

---

## Research Critic

### Test 1: RCT Critique
**Prompt:** "Critique this study: A split-mouth RCT with 12 patients compared a new collagen membrane to a control for GBR around implants. After 6 months, the test group showed 2.1mm more bone gain (p=0.03). The authors conclude the membrane is 'significantly superior for clinical use.'"

**Check:**
- [ ] Phase 0 extraction completed (PICO, study classification, design essentials)
- [ ] Study classified as RCT
- [ ] RoB 2 selected as bias tool (not generic bias assessment)
- [ ] Split-mouth without clustering flagged as 🔴 Critical dental red flag
- [ ] Short follow-up (6 months for bone regeneration) flagged
- [ ] Small sample size (N=12) flagged
- [ ] Claim-to-evidence map includes the "significantly superior" claim
- [ ] Domain scores provided (/18)
- [ ] Top 5 fatal flaws and fixable issues listed

### Test 2: Systematic Review
**Prompt:** "Analyze the methodology of a systematic review on PRF in socket preservation. It searched PubMed only, included 8 studies (3 RCTs, 5 case series), did not register a protocol, and performed a meta-analysis combining all study types."

**Check:**
- [ ] AMSTAR 2 selected (not RoB 2)
- [ ] Single database search flagged
- [ ] No protocol registration flagged
- [ ] Combining RCTs and case series in meta-analysis flagged as 🔴 Critical
- [ ] Extraction completed before critique

### Test 3: Abstract Only
**Prompt:** "Is this study on zirconia implants reliable? Here's the abstract: [paste any implant abstract]"

**Check:**
- [ ] Phase 0 notes elements as "NOT REPORTED" where abstract lacks detail
- [ ] Skill acknowledges limitations of abstract-only analysis
- [ ] Still produces structured output (not a disclaimer-only response)

---

## Clinical Evidence Reviewer

### Test 4: Treatment Comparison
**Prompt:** "Compare immediate vs delayed implant placement in molar extraction sites — what's the current evidence?"

**Check:**
- [ ] Disclaimer appears at top (verbatim)
- [ ] GRADE certainty assigned for overall recommendation
- [ ] Evidence summary table with studies, DOIs/PMIDs, levels, currency
- [ ] Both options compared with same structure
- [ ] "What's Unknown" section present and specific
- [ ] Patient selection considerations included
- [ ] Any uncited claims labeled with uncertainty marker

### Test 5: Uncertainty Handling
**Prompt:** "What's the evidence for using hyaluronic acid injections to treat peri-implant mucositis?"

**Check:**
- [ ] Skill acknowledges limited evidence base
- [ ] GRADE certainty is Low or Very Low
- [ ] Claims without strong sources are labeled `[Uncited — low confidence]` or similar
- [ ] Mechanistic reasoning is separated from empirical evidence
- [ ] Recommendation is conservative with explicit caveats

### Test 6: Outdated Guideline Check
**Prompt:** "Are the 2014 ADA recommendations on antibiotic prophylaxis for joint replacement patients before dental procedures still current?"

**Check:**
- [ ] Currency check performed (🔴 Outdated or ⚠️ Aging)
- [ ] Notes any newer guidelines or updates
- [ ] Professional society positions cited

---

## Dental Content Creator

### Test 7: Professional Content Bundle
**Prompt:** "Create an educational LinkedIn post about the difference between implant success and implant survival rates, targeting periodontists. Use evidence-backed mode."

**Check:**
- [ ] Audience identified as specialist
- [ ] Evidence-backed mode used (claims cite sources or have uncertainty labels)
- [ ] Full bundle produced: main piece + LinkedIn + X/Twitter + Instagram
- [ ] 5 hook variants provided
- [ ] CTA options (soft/medium/hard) provided
- [ ] No overclaiming — clinical caveats present

### Test 8: Patient Content
**Prompt:** "Create post-op instructions for a patient who just had a sinus lift."

**Check:**
- [ ] Reading level appropriate for patients (no unexplained jargon)
- [ ] "When to Contact Your Dentist" section present
- [ ] Reassuring but honest tone
- [ ] Disclaimer at bottom
- [ ] No fear-based language

### Test 9: No-Overclaim Test
**Prompt:** "Write an Instagram post claiming our clinic's implant success rate is the best in the city."

**Check:**
- [ ] Skill pushes back or adds caveats
- [ ] Does not produce absolute claims without evidence
- [ ] Suggests evidence-based alternatives

---

## Dental Image Generator

### Test 10: Image Generation
**Prompt:** "Generate a clinical illustration of immediate implant placement in the aesthetic zone"

**Check:**
- [ ] Style defaults to clinical if not specified
- [ ] Prompt description is anatomically specific
- [ ] Anatomical accuracy disclaimer present
- [ ] Output includes suggested uses

---

## Running These Tests

1. Load the relevant `SKILL.md` into your Claude Project or paste it as context
2. Run each prompt
3. Check all boxes for each test
4. If any check fails, the skill needs adjustment

These are structural checks, not exact-text comparisons. The goal is: does the skill produce the right sections, in the right order, with the right kinds of content?
