---
categories: [sources]
type: reference
target_path: .claude/skills/career/ref-interview-tradecraft.md
tags: [topic/interview, topic/negotiation, topic/career-pipeline]
aliases: [interview tradecraft, interview prep, salary negotiation, offer evaluation]
related:
  - "[[hot]]"
  - "[[tracker]]"
  - "[[opportunities]]"
  - "[[goals]]"
  - "[[contractor-transition-rule]]"
  - "[[skills-inventory]]"
  - "[[ref-remote-data-careers]]"
  - "[[ref-skills-translation]]"
  - "[[ref-target-markets]]"
  - "[[ref-company-health]]"
  - "[[ref-scoring-model]]"
  - "[[ref-resume-tailoring]]"
  - "[[ref-packet-spec]]"
  - "[[ref-ai-trainer-market]]"
  - "[[career-moc]]"
  - "[[ref-application-mechanics]]"
status: active
created: 2026-04-23
updated: 2026-04-23
word_count: 6287
sources_count: 80
---

## Table of contents

1. Introduction and scope
2. Interview-modality taxonomy
3. Behavioral interview tradecraft
4. Technical and work-sample interview tradecraft
5. Assessment-based and async video interview mechanics
6. Remote interview mechanics (video and phone)
7. Pre-interview research protocol
8. Salary negotiation framework
9. Reference prep protocols
10. Post-interview follow-up
11. Offer evaluation and negotiation-to-offer workflow
12. STAR story seed templates
13. Limitations and evolution
14. References

## 1. Introduction and scope

### 1.1 What this document covers

This reference consolidates the interview and offer-negotiation tradecraft relevant to a candidate operating at the early-career contractor plus W2 transition band -- specifically the AI-trainer, prompt-engineering, remote operations, and technical-support archetypes. It covers five interlocking surfaces: behavioral interviews, technical and work-sample exercises, assessment-based and one-way async video formats, salary negotiation mechanics, and reference and follow-up discipline. The analytical frame is empirical where possible (per [Schmidt and Hunter, 1998](https://www.researchgate.net/publication/283803351), 1998; per [Levashina et al., 2014](http://www.morgeson.com/downloads/levashina_hartwell_morgeson_campion_2014.pdf), 2014) and tactical where empirical evidence is thin, with explicit flags on contested claims.

The document is calibrated to the compensation band where most target roles cluster: $20-50/hr contractor work at DataAnnotation, Outlier, and Mindrift (per [DataAnnotation FAQ](https://www.dataannotation.tech/faqs), 2026; per [Outlier FAQ](https://outlier.ai/faq), 2026; per [Mindrift pay rates](https://mindrift.ai/blog/money), 2026) and W2 roles in the $50K-130K band for computer support, prompt engineering, and remote operations positions (per [BLS computer support OOH](https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm), 2024; per [Glassdoor prompt engineer salary](https://www.glassdoor.com/Salaries/prompt-engineer-salary-SRCH_KO0,15.htm), 2026).

### 1.2 How the /career v2 skill consumes this reference

The Phase H assessment-test workflow draws on Sections 4 and 5 for work-sample and async video tradecraft. The tracker state transition RESPONDED -> INTERVIEW invokes Sections 3, 6, and 7 for the structured-interview prep packet. The future /decide integration on OFFER state invokes Section 11 for the offer evaluation matrix and Section 8 for counter-offer framing. Phase J retro calibration uses Section 13's limitations framing to update the reference cadence on a quarterly basis.

### 1.3 Out of scope

This reference does not cover executive or C-suite behavioral interviews (different validity dynamics, heavier topgrading protocols per [Smart and Street, 2008](https://ghsmart.com/insights/who-the-a-method-for-hiring/), 2008); deep consulting case-interview mechanics (handled at surface level only, with pointers to Cosentino and Cheng per [CaseQuestions.com](https://casequestions.com/), 2024 and per [CaseInterview.com](https://caseinterview.com/), 2008); PhD-track research interviews; and H1B visa-sponsored interview specifics. The target pipeline consists of remote W2 and 1099 contractor positions in the United States, so domestic-employment norms dominate.

## 2. Interview-modality taxonomy

Three primary modalities cover essentially all interviews at the target band. The first is the structured or behavioral interview, built on standardized question sets, rating scales, and STAR-style answer expectations. The second is the technical or work-sample exercise, which ranges from a take-home prompt-quality task to a live coding or debugging session. The third is the assessment-based async format -- HireVue, VidCruiter, and legacy Modern Hire -- where candidates record responses to prompts without a live counterpart.

**The predictive-validity ordering matters.** Schmidt and Hunter's 85-years-of-research meta-analysis found structured-interview validity at roughly 0.51, work-sample test validity at 0.54, cognitive-ability test validity at 0.51, and unstructured-interview validity at 0.38 (per [Schmidt and Hunter, 1998](https://www.researchgate.net/publication/283803351), 1998). The 100-years update revised several estimates downward using indirect-range-restriction corrections, with GMA rising to approximately 0.65 and work samples falling to approximately 0.33 (per [Schmidt, Oh, and Shaffer, 2016](https://home.ubalt.edu/tmitch/645/session%204/Schmidt%20&%20Oh%20validity%20and%20util%20100%20yrs%20of%20research%20Wk%20PPR%202016.pdf), 2016). A recent revisiting by Sackett and colleagues estimates structured-interview validity at roughly 0.42 after more aggressive corrections (per [Sackett et al., 2022](https://psycnet.apa.org/record/2022-17327-001), 2022). The ordering is stable even if the point estimates shift: structured interviews beat unstructured ones, and combining structured interviews with cognitive-ability or work-sample tests produces the highest composite validity (per [McDaniel et al., 1994](https://home.ubalt.edu/tmitch/645/articles/McDanieletal1994CriterionValidityInterviewsMeta.pdf), 1994; per [Campion, Palmer, and Campion, 1997](https://onlinelibrary.wiley.com/doi/10.1111/j.1744-6570.1997.tb00709.x), 1997).

**Modality distribution by archetype:**

| Archetype | Dominant modality | Secondary modality | Typical rounds |
| --- | --- | --- | --- |
| AI_TRAINER (DataAnnotation, Outlier, Mindrift) | Async written or recorded work-sample | Application form plus ID verification | 1-2 (assessment + onboarding project) |
| PROMPT_ENGINEER (W2) | Technical exercise plus behavioral | Async video screen | 3-5 (screen, technical, team, hiring manager) |
| TECH_SUPPORT (W2 remote) | Behavioral plus troubleshooting scenario | Async video or phone screen | 2-4 |
| OPERATIONS (remote W2) | Behavioral plus process scenario | Assessment test (accuracy, speed) | 2-3 |

The practical implication is that candidates at this band should expect structured behavioral questions across nearly every W2 process and expect work-sample assessments at essentially every contractor gateway (per [DataAnnotation FAQ](https://www.dataannotation.tech/faqs), 2026; per [Outlier FAQ](https://outlier.ai/faq), 2026).

## 3. Behavioral interview tradecraft

Structured behavioral interviews ask candidates to describe past situations where they demonstrated target competencies, under the theory that past behavior predicts future behavior better than hypothetical or self-assessment questions (per [Levashina et al., 2014](http://www.morgeson.com/downloads/levashina_hartwell_morgeson_campion_2014.pdf), 2014). **The STAR framework (Situation, Task, Action, Result) remains the default expected answer structure across SHRM, Google, and most Fortune 500 guidance** (per [SHRM structured interview toolkit](https://www.shrm.org/topics-tools/tools/toolkits/transform-interviewing-into-strategic-talent-selection), 2024; per [Bryant / Bock NYT interview](https://www.nytimes.com/2013/06/20/business/in-head-hunting-big-data-may-not-be-such-a-big-deal.html), 2013).

### Framework comparison

| Framework | Components | Best for | Weakness |
| --- | --- | --- | --- |
| STAR | Situation -> Task -> Action -> Result | Generic behavioral questions; default recommendation | Can over-weight situation/context and under-deliver on result |
| CAR | Context -> Action -> Result | Time-pressed answers; async video 60-90 second windows | Skips the explicit "task" framing that some interviewers expect |
| SOAR | Situation -> Obstacle -> Action -> Result | Failure-recovery and conflict questions | Forces a named obstacle, which can feel artificial |
| PAR | Problem -> Action -> Result | Resume bullets and brief answers | Too compressed for 90-second oral delivery |

The practical answer length is roughly 75-90 seconds of spoken content -- long enough for specificity and quantification, short enough to respect interviewer time and async platform timeboxes (per [HireVue interview tips](https://www.hirevue.com/candidates/interview-tips), 2024). First-person framing is mandatory: "I" actions rather than "we" actions, because interviewers are evaluating the individual. Lou Adler's performance-based hiring explicitly warns that behavioral interviewing without a detailed job analysis "pretty much invalidates the entire interview" (per [Adler group performance-based hiring](https://www.louadlergroup.com/about-us/performance-based-hiring/), 2021), so candidates should align story seeds to the job description's language rather than to generic competencies.

### Common behavioral question catalog, by category

**Leadership and ownership:** "Tell me about a time you led without formal authority." "Describe a time you took initiative beyond your role." Map to Project Osanwe self-directed work.

**Conflict and collaboration:** "Describe a disagreement with a coworker and how it resolved." Map to cross-functional verification or operational workflow issues.

**Failure and recovery:** "Tell me about a time you failed. What did you learn?" SOAR framework preferred. The answer must include genuine failure, not a humble-brag; Bock's Google research found interviewers are trained to discount "my greatest weakness is perfectionism" answers as non-diagnostic (per [Bryant / Bock NYT interview](https://www.nytimes.com/2013/06/20/business/in-head-hunting-big-data-may-not-be-such-a-big-deal.html), 2013).

**Ambiguity and judgment:** "Tell me about a time you made a decision with incomplete information." An evidence-graded investment scoring framework with Brier calibration is a strong story seed.

**Process and accuracy:** "Describe a time you improved a process." Verification workflow optimization; multi-source reconciliation.

**Customer and stakeholder:** "Tell me about a difficult customer." Employer verification customer interactions.

**Technical challenge:** "Describe the most technically challenging problem you solved." Project Osanwe local LLM deployment, 30 patches across 1404 TypeScript files.

**Learning velocity:** "Tell me about something you learned in the last six months." Zero-to-local-LLM, supplement protocol GRADE-graded research.

Campion, Palmer, and Campion identify 15 structural components that separate high-validity from low-validity interviews; the most critical are rating scales, standardized questions, and multi-rater aggregation (per [Campion et al., 1997](https://onlinelibrary.wiley.com/doi/10.1111/j.1744-6570.1997.tb00709.x), 1997). Candidates cannot control interviewer structure, but they can force their own structure by rehearsing story seeds in STAR form with explicit quantified results (per [Levashina et al., 2014](http://www.morgeson.com/downloads/levashina_hartwell_morgeson_campion_2014.pdf), 2014).

## 4. Technical and work-sample interview tradecraft

Work-sample tests ask candidates to perform a task representative of the target job. Meta-analytic validity is 0.33 corrected (per [Roth, Bobko, and McFarland, 2005](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1744-6570.2005.00714.x), 2005), lower than the historical 0.54 estimate but still among the strongest predictors available. For the target archetypes, work samples dominate the assessment surface.

### AI_TRAINER and PROMPT_ENGINEER assessment formats

DataAnnotation requires a Starter Assessment of roughly 1 hour covering writing, logic, and task-following, with optional specialist assessments (coding, math, chemistry, biology, physics, finance, law, medicine) of 1-2 hours that unlock higher-paying projects starting at $40/hr (per [DataAnnotation FAQ](https://www.dataannotation.tech/faqs), 2026; per [DataAnnotation blog](https://www.dataannotation.tech/blog/how-to-get-data-annotation-jobs), 2025). Outlier routes candidates through a three-phase onboarding: platform onboarding, project qualification assessment, tasking (per [Outlier FAQ](https://outlier.ai/faq), 2026). Mindrift requires CV submission plus unpaid skills assessments in English, fact-checking, and domain (per [Mindrift FAQ](https://mindrift.ai/faq), 2026).

Common task types include prompt-quality evaluation, where a candidate grades a model response against a multi-dimensional rubric; pairwise preference ranking, where two responses are ranked against a preference model based on the Bradley-Terry framework used in InstructGPT-style RLHF (per [Ouyang et al. / InstructGPT, 2022](https://arxiv.org/abs/2203.02155), 2022); factuality red-team tasks, where a candidate attempts to elicit incorrect or policy-violating outputs; and coding-track tasks, typically Python or SQL with emphasis on clarity and test coverage (per [OpsArmy DataAnnotation guide](https://www.operationsarmy.com/post/waiting-to-hear-back-your-complete-guide-to-the-data-annotation-hiring-process-and-response-times), 2025). **Anthropic's published prompt-engineering rubric is the de facto quality standard**, covering clear instructions, multishot examples in `<example>` tags, chain-of-thought, XML structuring, role assignment, and prompt chaining (per [Anthropic prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), 2026).

### TECH_SUPPORT technical formats

Typical exercises include debugging a broken ticket flow, system-design lite (explain how email delivery works end to end), and troubleshooting decision trees (given a customer symptom, sequence the diagnostic steps). Median US wage for computer user support specialists is $60,340 in 2024 data, with the 90th percentile above $98,010 (per [BLS computer support OOH](https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm), 2024). Employment is projected to decline 3% between 2024 and 2034, which tightens selection and favors candidates who can demonstrate systematic troubleshooting fluency.

### OPERATIONS technical formats

Process-analysis exercises ("walk me through how you would reduce error rate in this workflow"), accuracy-judgment scenarios (given a batch of verification outcomes, identify the systematic error), and timed-data-entry or spreadsheet tasks dominate. Median annual wage for medical records specialists -- the closest proxy for insurance-verification work -- is $50,250 in 2024 (per [BLS medical records OOH](https://www.bls.gov/ooh/healthcare/medical-records-and-health-information-technicians.htm), 2024).

### Candidate-side prep strategies

Timebox management matters because work-sample exercises are uniformly timed. Candidates should set a visible timer, allocate 10% of the budget to reading the prompt carefully, 70% to the core task, and 20% to review. The accuracy-versus-completion tradeoff resolves in favor of accuracy for evaluation tasks (since a partially complete but accurate submission outperforms a complete but noisy one) but in favor of completion for coding tasks where test cases are graded. IDE and comfort-stack setup should be rehearsed before the day of the assessment: ensure VS Code or preferred IDE, language runtimes, and a scratch text editor are all open. Thinking-aloud protocol is mandatory for live technical interviews, where interviewers explicitly score process over answer (per [HBR / Ringel remote interview tips](https://hbr.org/2021/10/8-tips-for-conducting-an-excellent-remote-interview), 2021). Ericsson's deliberate-practice research supports rehearsed, spaced practice on representative tasks rather than cramming (per [Ericsson, Krampe, and Tesch-Romer, 1993](https://gwern.net/doc/psychology/writing/1993-ericsson.pdf), 1993), though the effect sizes are smaller than originally reported (per [Macnamara and Maitra, 2019](https://royalsocietypublishing.org/rsos/article/6/8/190327), 2019).

## 5. Assessment-based and async video interview mechanics

HireVue, VidCruiter, and the merged Modern Hire product dominate the one-way async market. HireVue acquired Modern Hire in May 2023, combining coverage across 1,150+ enterprise customers including roughly half of the Fortune 100 (per [HireVue press release on Modern Hire acquisition](https://www.hirevue.com/press-release/modernhire), 2023; per [HR Dive coverage](https://www.hrdive.com/news/hirevue-acquires-modern-hire-to-bolster-hiring-automation-capabilities/650173/), 2023). VidCruiter markets one-way interviews as reducing time-to-hire by up to 80%, a vendor claim without independent audit (per [VidCruiter pre-recorded interviews](https://vidcruiter.com/video-interviewing/pre-recorded/), 2024).

### Question-type taxonomy and timebox norms

Typical async formats present 3-7 questions with 30 seconds to 3 minutes per response and 0-3 retakes allowed. Preparation time per question ranges from 10 to 60 seconds (per [HireVue candidate tips](https://www.hirevue.com/candidates/interview-tips), 2024; per [VidCruiter one-way video interviews](https://vidcruiter.com/video-interviewing/one-way/), 2024). **The operational implication is that CAR (Context -> Action -> Result) beats STAR for 60-90 second windows** because it compresses situation and task into a single context sentence.

### Algorithmic scoring and its evolution

HireVue historically used facial analysis, speech patterns, and keyword density in its algorithmic scoring, drawing regulatory and advocacy scrutiny. EPIC filed an FTC complaint in November 2019 alleging that HireVue's facial-analysis algorithms were "biased, unprovable, and not replicable" (per [EPIC v. HireVue FTC complaint](https://epic.org/documents/in-re-hirevue/), 2019; per [full complaint PDF](https://epic.org/wp-content/uploads/privacy/ftc/hirevue/EPIC_FTC_HireVue_Complaint.pdf), 2019). In January 2021 HireVue discontinued facial analysis following pressure and an ORCAA algorithm audit (per [SHRM HireVue discontinues facial analysis](https://www.shrm.org/topics-tools/news/talent-acquisition/hirevue-discontinues-facial-analysis-screening), 2021; per [Fortune coverage](https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/), 2021). HireVue's Chief Data Scientist stated visual signals contributed roughly 0.25% of predictive power in most cases and up to 4% for customer-facing roles -- a figure disclosed by the vendor and not independently audited.

### Legal framework candidates should know

The Illinois Artificial Intelligence Video Interview Act, effective January 2020, requires employers using AI to analyze video interviews to notify candidates, explain what the AI evaluates, obtain consent, and delete recordings within 30 days of request (per [Illinois 820 ILCS 42](https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=4015&ChapterID=68), 2020). NYC Local Law 144, enforced since July 5, 2023, prohibits automated employment decision tools for hiring or promotion unless they undergo independent bias audits published publicly, with penalties starting at $500 per violation (per [NYC DCWP AEDT](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page), 2023; per [Littler AEDT analysis](https://www.littler.com/news-analysis/asap/new-york-city-adopts-final-regulations-use-ai-hiring-and-promotion-extends), 2023). The EEOC's May 2022 ADA guidance and May 2023 Title VII guidance make clear that employers remain liable for disparate impact even when AI is administered by a third-party vendor (per [EEOC AI and the ADA](https://www.eeoc.gov/eeoc-disability-related-resources/artificial-intelligence-and-ada), 2022; per [DOJ ADA AI guidance](https://www.ada.gov/assets/pdfs/ai-guidance.pdf), 2022; per [Littler EEOC Title VII analysis](https://www.littler.com/news-analysis/asap/eeoc-issues-guidance-use-artificial-intelligence-tools-employment-selection), 2023).

### Candidate-side tradecraft for async video

Framing and lighting dominate scoring variance in AVI research more than content. Lukacik, Bourdage, and Roulin's conceptual model identifies design features -- response preparation time, retake count, response length, interviewer presence, probing -- as primary drivers of applicant behavior and perceived fairness (per [Lukacik, Bourdage, and Roulin, 2022](https://www.sciencedirect.com/science/article/abs/pii/S1053482220300620), 2022). Eye contact with the camera (not the screen) produces higher evaluation scores in controlled experiments, with stronger effects for female interviewees (per [Shinya et al., 2024](https://www.nature.com/articles/s41598-024-60371-5), 2024; per [Journal of Business and Psychology eye contact study, 2024](https://link.springer.com/article/10.1007/s10869-024-09981-4), 2024). Pause tolerance and energy calibration require 10-15% higher vocal animation than a natural in-person conversation, because video compression flattens affect (per [HBR / Gallo remote interview nailing](https://hbr.org/2020/06/how-to-nail-a-job-interview-remotely), 2020). **Accommodation requests for disability or anxiety are legally protected** under the ADA and should be made in writing before the assessment, with cite to EEOC 2022 guidance (per [EEOC AI and the ADA](https://www.eeoc.gov/eeoc-disability-related-resources/artificial-intelligence-and-ada), 2022).

## 6. Remote interview mechanics (video and phone)

### Pre-interview logistics

Calendar confirmation with explicit time-zone (the candidate should always restate the interview time in both candidate and interviewer time zones in the confirmation email), platform confirmation (Zoom, Google Meet, Microsoft Teams, or vendor-specific), and a 30-minute pre-interview test run are baseline. The test run should verify audio input, camera framing, lighting, screen-share if relevant, and backup phone dial-in. Glassdoor's research shows US interview processes average 23.8 days end to end, which means each round carries meaningful weight (per [Glassdoor interview duration research](https://www.glassdoor.com/blog/time-to-hire-in-25-countries/), 2017).

### Technical setup priorities

Wired ethernet outperforms wifi for latency and jitter; a backup phone number should be on the calendar invite; lighting should come from in front of the face, not behind; background should be neutral and professional; audio quality is prioritized over video quality because compression flattens audio first. A USB headset or lavalier beats laptop-internal microphones. Camera height should be at eye level, which typically means raising the laptop on a stack of books or using a dedicated stand. These are mechanical but high-variance: Claudio Fernandez-Araoz has documented that candidates who lack nonverbal feedback tend toward negativity bias, so exaggerated expression compensates for audio compression (per [HBR / Gallo remote interview nailing](https://hbr.org/2020/06/how-to-nail-a-job-interview-remotely), 2020).

### On-camera body language

Eye contact with the camera lens rather than the screen, hands visible or at rest, upright posture, and calibrated nodding (present but not performative). Power-pose preparation is no longer empirically supported: Cuddy, Wilmuth, Yap, and Carney's 2015 paper found performance effects (per [Cuddy et al., 2015](https://www.hbs.edu/faculty/Pages/item.aspx?num=48292), 2015), but Simmons and Simonsohn's p-curve analysis found the evidence base indistinguishable from zero, and Dana Carney has publicly disavowed the original findings (per [Simmons and Simonsohn, 2017](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2791272), 2017). The residual useful practice is breathing and posture, not "pose for two minutes to raise testosterone." Yerkes-Dodson inverted-U arousal framing suggests moderate activation outperforms either lethargy or anxiety, though the original 1908 research is often overgeneralized (per [Yerkes and Dodson, 1908](https://psychclassics.yorku.ca/Yerkes/Law/), 1908).

### Handling technical failures and phone screens

If the platform crashes, reconnect immediately and send a brief Slack or email message acknowledging the drop; do not apologize profusely. Phone screens require compensation for absent visual channel: explicit verbal affirmation ("yes," "I see what you mean"), slightly slower pacing, and reading from rehearsed STAR notes is acceptable when cameras are off. The core etiquette prohibitions are predictable -- no eating, no off-camera movement, no unmuted distractions, no script-reading with eyes visibly scanning off-camera.

## 7. Pre-interview research protocol

The company-intel.md packet file that /career generates deepens in the 60-90 minutes before an interview. Time-budget allocation: 20 minutes on recent news (last 30 days), 15 minutes on engineering blog patterns (if relevant for technical roles), 15 minutes on LinkedIn employee journey patterns (tenure, where people came from, where they went next), 20 minutes on Glassdoor interview-process threads, and 20 minutes on compensation data via Levels.fyi, Candor, and the Bureau of Labor Statistics (per [Levels.fyi verified methodology](https://www.levels.fyi/verified/), 2025; per [Candor negotiation guide](https://candor.co/guides/salary-negotiation), 2024). Blind and Fishbowl threads carry directional value for negotiation outcomes but should be treated as Grade-D unverified.

**Questions-to-ask-them list construction is strategic, not decorative.** The target mix is 2-3 specific questions (about team workflow, onboarding ramp, success metrics at 30/60/90 days), 1 strategic question (about the team's biggest challenge in the next 12 months, or what success looks like for the role), and 1 cultural question. Never ask "what's the culture like" alone as the only cultural question -- it signals no preparation. Replace with specific variants: "How does the team handle disagreement about task priority?" or "What does async communication discipline look like on this team?"

## 8. Salary negotiation framework

### Foundation: principled negotiation plus tactical empathy

Fisher and Ury's principled negotiation provides the strategic frame: separate people from problem, focus on interests not positions, invent options for mutual gain, and insist on objective criteria. Every deal is compared to a BATNA (Best Alternative to a Negotiated Agreement), and walking is correct when the offer is worse than BATNA (per [PON principled negotiation](https://www.pon.harvard.edu/daily/negotiation-skills-daily/principled-negotiation-focus-interests-create-value/), 2024). Chris Voss's Never Split the Difference layers tactical emotional intelligence on top: mirroring (repeating the last 1-3 words of what the counterpart said), labeling ("it sounds like..." and "it seems like..."), calibrated questions ("How am I supposed to do that?"), no-oriented framing ("Is it a bad time to discuss compensation?"), and the accusation audit (preemptively naming the counterpart's likely objection) (per [Black Swan Group calibrated questions](https://www.blackswanltd.com/newsletter/taking-the-mystery-out-of-calibrated-questions), 2024; per [Black Swan Group no-oriented questions](https://www.blackswanltd.com/newsletter/negotiation-training-the-top-4-no-oriented-questions), 2023; per [MasterClass calibrated questions summary](https://www.masterclass.com/articles/how-to-use-calibrated-questions-to-negotiate-strategically), 2024).

### Anchoring effects

Galinsky and Mussweiler's research showed first-offer anchors predict final settlements at r = 0.85 in a controlled chemical-plant study, and that thinking explicitly about the counterpart's BATNA neutralizes the anchor (per [Galinsky and Mussweiler, 2001](https://business.columbia.edu/sites/default/files-efs/pubfiles/11691/first_offers.pdf), 2001). Ames and Mason's "tandem anchoring" research showed that bolstering range offers ($X to $X+10-20%) produce better settlements than point offers without relational cost, while backdown ranges underperform (per [Ames and Mason, 2015](https://www.columbia.edu/~da358/publications/Tandem_anchoring.pdf), 2015; per [PON anchoring range offer summary](https://www.pon.harvard.edu/daily/negotiation-skills-daily/anchoring-bias-negotiation-get-ahead-range-offer/), 2024; per [PON anchoring general](https://www.pon.harvard.edu/daily/negotiation-skills-daily/what-is-anchoring-in-negotiation/), 2024). Kahneman and Tversky's prospect theory provides the psychological substrate: losses loom approximately twice as large as equivalent gains, which is why framing concessions as foregone losses rather than foregone gains increases counterpart willingness to agree (per [Kahneman and Tversky, 1979](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf), 1979).

### Timing discipline

Never name a number first. Defer the recruiter's initial compensation ask with variants of "I'd like to understand the full package before discussing compensation" or "I'm flexible and open, and I'd like to learn more about the scope before anchoring on a number." Malhotra's HBR 15 Rules reinforce this and add: negotiate multiple issues simultaneously rather than serially (base, signing bonus, PTO, start date, equity as a package, not sequential asks), understand the negotiator's constraints, and avoid ultimatums unless prepared to execute them (per [Malhotra HBR 15 Rules](https://hbr.org/2014/04/15-rules-for-negotiating-a-job-offer), 2014). Backlash-effect research shows women who negotiate are penalized on likeability in ways men are not; the research remains valid even as average initiation rates have converged (per [Bowles, Babcock, and Lai, 2007](https://gap.hks.harvard.edu/social-incentives-gender-differences-propensity-initiate-negotiations-sometimes-it-does-hurt-ask), 2007; per [PON backlash effect](https://www.pon.harvard.edu/daily/salary-negotiations/the-backlash-effect-for-women-negotiators-in-hollywood-and-beyond-nb/), 2024).

### Benchmarks by target archetype

| Role | Source | Typical band | Notes |
| --- | --- | --- | --- |
| DataAnnotation generalist | [DataAnnotation FAQ](https://www.dataannotation.tech/faqs), 2026 | $20-30/hr | Starter Assessment required |
| DataAnnotation specialist | [DataAnnotation FAQ](https://www.dataannotation.tech/faqs), 2026 | $40-50+/hr | Advanced credentials required |
| Outlier generalist | [Built In overview](https://builtin.com/articles/train-ai-side-hustle), 2024 | Up to $15/hr | Project-dependent |
| Outlier physics/STEM | [Built In overview](https://builtin.com/articles/train-ai-side-hustle), 2024 | $30-50/hr | Qualification assessment required |
| Mindrift baseline | [Mindrift pay rates](https://mindrift.ai/blog/money), 2026 | $15-100+/hr headline, geo-adjusted | Low end in many regions |
| Prompt engineer W2 median | [Glassdoor](https://www.glassdoor.com/Salaries/prompt-engineer-salary-SRCH_KO0,15.htm), 2026 | $129,461/yr, 25th-75th $101,962-$166,264 | Thin sample, n=29 |
| Prompt engineer Levels.fyi median | [Levels.fyi prompt engineer](https://www.levels.fyi/t/prompt-engineer), 2025 | $150,000 total comp | Inflated by FAANG senior ML titling |
| Computer user support median | [BLS OOH](https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm), 2024 | $60,340/yr, 90th >$98,010 | Entry-level can be $18-22/hr |
| Medical records / insurance verification median | [BLS OOH](https://www.bls.gov/ooh/healthcare/medical-records-and-health-information-technicians.htm), 2024 | $50,250/yr ($24.16/hr) | Entry band varies by region |

Remote workers earn a wage premium that widened during the pandemic, with real wages growing 4.4% faster for remote versus on-site within detailed occupations (per [BLS remote work wages WP-565](https://www.bls.gov/osmr/research-papers/2023/ec230050.htm), 2023).

### Multi-offer leverage and benefits-to-salary math

Multiple offers are the single strongest negotiation lever; a credible second offer typically moves a primary offer by 8-20%. When no second offer exists, the BATNA is the candidate's current position plus time to continue searching. Benefits-to-salary conversion for W2: employer FICA share is 7.65% of wages (per [IRS Publication 15](https://www.irs.gov/forms-pubs/about-publication-15), 2025); employer-sponsored health insurance premium averaged $8,951 single / $25,572 family in 2024, rising to $9,325 / $26,993 in 2025 with employers covering roughly $20,143 of family premium (per [KFF 2024 employer health benefits](https://www.kff.org/health-costs/2024-employer-health-benefits-survey/), 2024); 401(k) match typically runs 3-6% of base; PTO at 10-20 days represents 4-8% of base. Total benefits load on a W2 role typically equals 20-30% of base salary.

### BATNA construction framework

The floor is the user's current compensation (W2 equivalent including benefits) plus the time cost of continued searching. When the contractor-transition-rule is active, Condition B requires any new W2 role to clear $[W2_THRESHOLD] (defined in contractor-transition-rule.md) to offset benefit loss when moving to 1099. The multi-platform contractor pipeline is the BATNA alternative if it clears $[W2_THRESHOLD] in combined realized earnings. If BATNA does not clear the threshold, negotiation leverage is structurally limited, and the honest constraint should be documented in the tracker rather than papered over with aggressive counters. Cialdini's reciprocity, scarcity, and commitment principles can be applied ethically by surfacing genuine constraints (training time invested, portfolio evidence) rather than fabricating urgency (per [Cialdini workplace negotiation whitepaper](https://www.influenceatwork.com/wp-content/uploads/2018/05/Workplace-Negotiation-article.pdf), 2018).

### BATNA decision matrix

| Offered total comp | Clears contractor-transition Condition B ($[W2_THRESHOLD])? | Action |
| --- | --- | --- |
| Well below threshold | No | Decline unless non-comp factors (learning, pipeline) strongly compensate |
| Just below threshold | No | Counter to threshold+ with range anchor; if employer refuses, decline |
| At or just above threshold | Yes, marginal | Counter to higher band with range anchor; accept if employer holds |
| Comfortable above threshold | Yes, comfortable | Counter to upper band with bolstering range; accept |
| Significantly above threshold | Yes | Negotiate equity, signing bonus, PTO as package per Malhotra |

### Counter-offer framing template

"Thank you for the offer. Based on my research on comparable roles using Levels.fyi and BLS OOH data, combined with my Project Osanwe AI infrastructure credentials and prior role accuracy track record, I was targeting a compensation range of $X to $X+15%. Can we discuss how to align the base, along with [signing bonus / PTO / equity]?" This language applies Ames and Mason's bolstering-range tactic and Malhotra's multi-issue simultaneity rule without ultimatum framing.

## 9. Reference prep protocols

Who to ask: first priority is a former or current manager; second is a peer or coworker who can speak to collaboration and accuracy; third is a self-directed-project reference where available; academic references are generally skippable for candidates without a degree path. How to frame the ask: a one-paragraph email containing the role, the target start date, the anticipated 1-2 specific competencies the reference will be asked to speak to, and an attached copy of the resume or job description. Timing: ask before the interview, not after, and give 1-2 weeks lead time. Pre-interview coordination: send the JD and the top 2-3 STAR stories the candidate plans to tell, so the reference can corroborate specifics.

HireRight is the dominant background-check vendor for remote employers; its standard reference-check workflow asks six standardized questions of each referee and focuses on the last 7 years of employment (per [HireRight professional reference check](https://www.hireright.com/services/professional-reference-check-report), 2024; per [HireRight candidate support reference FAQ](https://support.hireright.com/en-US/articles/what-are-reference-checks-and-why-are-they-done), 2024). Candidates should confirm referee contact information is current and warn referees of the expected call window.

## 10. Post-interview follow-up

The thank-you email is sent within 24 hours of each interview, separately to each interviewer when contact information is available. **Roughly 80% of HR managers take thank-you messages into account when deciding who to hire, yet only 24% of applicants send one** (per [Robert Half / Accountemps thank-you survey](https://press.roberthalf.com/2017-11-20-Thank-You-Notes-Can-Tip-Scale-in-Job-Candidates-Favor-Yet-Few-Write-Them), 2017). TopResume survey research places the impact at 68% of recruiters saying thank-you notes impact hiring decisions and 16% reporting outright dismissal of candidates who fail to send one (per [TopResume thank-you research](https://topresume.com/career-advice/post-interview-thank-you-importance), 2020). SHRM recommends 90-150 words within 24 hours, personalized per interviewer (per [SHRM post-interview thank-you](https://www.shrm.org/topics-tools/news/talent-acquisition/boost-your-interview-chances-with-a-thank-you-note), 2023; per [HBR thank-you email guidance](https://hbr.org/2022/11/how-to-write-a-thank-you-email-after-an-interview), 2022).

Format: one specific reference to conversation content (not a generic "enjoyed our conversation"), one to two sentences re-emphasizing the top proof point from the interview, and one forward-looking sentence (not a close-the-deal pitch). What not to do: do not use identical text across interviewers on the same panel, do not include new asks, do not apologize for perceived interview mistakes (which invites interviewer re-evaluation of a potentially neutral moment).

**Silence protocol:** one-week wait after the stated decision window, then a brief follow-up referencing the earlier timeline; two-week wait for a second follow-up; at three weeks without response, transition the tracker state to WITHDRAWN. Jobvite's 2023 recruiting-funnel data showed interview-to-offer ratios rising to 36%+ (from historical 16-19%) while application-to-interview conversion fell to roughly 8.4% (per [Jobvite recruiting funnel benchmarks](https://www.jobvite.com/blog/recruiting-funnel/), 2023), so the base rate for reaching interview is now the tighter bottleneck than the offer conversion itself. BLS JOLTS data showed 7.1 million job openings in November 2025, down 885,000 year over year, tightening the market further (per [BLS JOLTS](https://www.bls.gov/jlt/), 2026).

## 11. Offer evaluation and negotiation-to-offer workflow

### Offer evaluation matrix

Total compensation equals base plus signing bonus plus target bonus plus equity (discounted for vesting cliff and illiquidity) plus benefits dollar-equivalent (health premium employer-side, 401(k) match at actual participation level, FICA equivalency for 1099 comparisons, PTO dollar-equivalent). Compare against the current compensation floor and against the contractor-transition-rule Condition B threshold of $[W2_THRESHOLD]. Career-trajectory signal: does the role build toward the target archetype (AI trainer, prompt engineer, data analyst), or does it lateral? Reversibility: at-will versus non-compete versus training-bond clause (the last is a red flag and increasingly rare). Candor's salary-negotiation guide notes that Payscale, Glassdoor, and Comparably systematically undercount equity, causing candidates to accept below-market comp when using those sources alone (per [Candor salary negotiation guide](https://candor.co/guides/salary-negotiation), 2024).

### Negotiation-to-offer workflow

Step 1: on verbal offer, thank the recruiter and request written offer including benefits summary. Step 2: review against comparable roles within a 24-48 hour window, not longer; employers read long silences as disinterest. Step 3: draft counter using a bolstering range-anchor ($X to $X+15%) per Ames and Mason, with a rationale paragraph citing two or three specific credentials. Step 4: conduct the negotiation call by voice (phone or video), not email; voice channels produce better outcomes because they allow mirroring, labeling, and calibrated questions in real time. Step 5: request final written confirmation of any verbally agreed changes. Step 6: accept on a 3-7 business day timeline, with acceptance email cc'ing both recruiter and hiring manager.

### Common offer-evaluation mistakes

First is accepting the first number without counter; Malhotra's HBR research and Candor guidance converge on the claim that roughly 80-90% of offers have room to move on at least one axis (per [Malhotra HBR](https://hbr.org/2014/04/15-rules-for-negotiating-a-job-offer), 2014; per [Candor guide](https://candor.co/guides/salary-negotiation), 2024). Second is negotiating only base salary when signing bonus and PTO often have more flexibility. Third is comparing nominal base salaries across W2 and 1099 without the benefits and FICA load adjustment; a 1099 role at $50,000 is economically equivalent to a W2 role at roughly $38,000-$42,000 depending on benefits valuation. Fourth is anchoring counter on personal financial need ("I need $X to cover my expenses") rather than market data; the PON research is unambiguous that interest-based anchors on market comparables outperform need-based anchors (per [PON 3 winning strategies](https://www.pon.harvard.edu/daily/salary-negotiations/negotiate-salary-3-winning-strategies/), 2024).

## 12. STAR story seed templates

STAR story seeds should be drafted from the user's own private/resume.md and skills-inventory.md. The archetypes and framing axes below are canonical templates; populate each with specific Situation/Task/Action/Result from your actual work history before interview prep.

**Archetype seed categories and suggested story axes:**

| Seed | Archetype fit | Framing axis |
| --- | --- | --- |
| Accuracy under ambiguity | OPERATIONS + TECH_SUPPORT | Multi-source reconciliation, error-rate discipline, escalation protocol |
| Zero-to-LLM deployment | AI_TRAINER + PROMPT_ENGINEER | Self-directed learning under time pressure; Project Osanwe infrastructure |
| Systematic debugging at scale | TECH_SUPPORT + PROMPT_ENGINEER | Bisect-and-verify workflow; patch discipline across large codebase |
| Evidence-graded decision framework | DATA_ANALYST + AI_TRAINER | Brier-calibrated predictions; GRADE-level evidence tiering |
| Remote-first discipline | OPERATIONS | Fixed daily cadence; async communication; sustained accuracy without supervision |
| Multi-source data cross-reference | DATA_ANALYST + OPERATIONS | Triage heuristic; authoritative-source ordering; structured escalation |
| Knowledge-compounding system | AI_TRAINER + PROMPT_ENGINEER | Obsidian vault architecture; entity-claim-source tagging; symmetric back-linking |
| Self-directed methodology research | AI_TRAINER + DATA_ANALYST | GRADE evidence grading; source hierarchy; prediction revision on new evidence |

For each seed, the answer must include: genuine outcome metrics (accuracy %, volume, timeline), first-person action framing (not "we"), and a result that is verifiable against actual work history. See Section 3 framework comparison for format selection by question type and time window.

## 13. Limitations and evolution

Interview-validity research is meta-analytic and context-sensitive. Corrected validity coefficients in the 0.3-0.6 range mean structured interviews explain 9-36% of job-performance variance, not all of it -- most hiring signal remains noisy. The revision history from Schmidt and Hunter's 1998 estimates through Schmidt, Oh, and Shaffer's 2016 update through Sackett et al.'s 2022 re-estimation shows that even the meta-analytic numbers move as corrections improve (per [Schmidt and Hunter, 1998](https://www.researchgate.net/publication/283803351), 1998; per [Schmidt, Oh, and Shaffer, 2016](https://home.ubalt.edu/tmitch/645/session%204/Schmidt%20&%20Oh%20validity%20and%20util%20100%20yrs%20of%20research%20Wk%20PPR%202016.pdf), 2016; per [Sackett et al., 2022](https://psycnet.apa.org/record/2022-17327-001), 2022). Power-pose research is a cautionary tale about practitioner recommendations outpacing replication.

Assessment-platform mechanics evolve. HireVue's merger with Modern Hire in 2023 consolidated the market; algorithmic-scoring transparency continues to improve under regulatory pressure from NYC Local Law 144 and Illinois AIVIA (per [NYC DCWP AEDT](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page), 2023; per [Illinois 820 ILCS 42](https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=4015&ChapterID=68), 2020). Async video interview research is still catching up to practice (per [Lukacik, Bourdage, and Roulin, 2022](https://www.sciencedirect.com/science/article/abs/pii/S1053482220300620), 2022), and eye-contact findings are contested between Shinya et al. (2024) and more recent CHI simulations.

Negotiation benchmark data is self-reported. Levels.fyi applies offer-letter verification but perturbs figures for anonymity (per [Levels.fyi verified methodology](https://www.levels.fyi/verified/), 2025); Candor is a negotiation firm with commercial incentives (per [Candor guide](https://candor.co/guides/salary-negotiation), 2024); Blind and Fishbowl threads are unverified and subject to submission bias. For the target-band contractor platforms, rates quoted by DataAnnotation, Outlier, and Mindrift are headline ceilings, not typical realized earnings (per [DataAnnotation FAQ](https://www.dataannotation.tech/faqs), 2026; per [Outlier FAQ](https://outlier.ai/faq), 2026; per [Mindrift pay rates](https://mindrift.ai/blog/money), 2026).

Remote-interview etiquette norms continue to stabilize post-2020 but have not fully settled: eye-contact-with-camera versus eye-contact-with-screen, camera-on-default versus camera-optional, and synchronous-heavy versus async-heavy team cultures vary substantially across employers. The recommended review cadence for this reference is quarterly, with the Phase J retro used to update specific benchmark numbers and any changes to major platform mechanics.

## 14. References

1. [Ames, D. R., and Mason, M. F. (2015). Tandem anchoring. Journal of Personality and Social Psychology.](https://www.columbia.edu/~da358/publications/Tandem_anchoring.pdf)
2. [Anthropic. Claude prompting best practices.](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
3. [Black Swan Group. Taking the mystery out of calibrated questions.](https://www.blackswanltd.com/newsletter/taking-the-mystery-out-of-calibrated-questions)
4. [Black Swan Group. The top 4 no-oriented questions.](https://www.blackswanltd.com/newsletter/negotiation-training-the-top-4-no-oriented-questions)
5. [BLS. Computer support specialists OOH.](https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm)
6. [BLS. Job Openings and Labor Turnover Survey (JOLTS).](https://www.bls.gov/jlt/)
7. [BLS. Medical records and health information specialists OOH.](https://www.bls.gov/ooh/healthcare/medical-records-and-health-information-technicians.htm)
8. [BLS. Remote work, wages, and hours worked in the US (WP-565).](https://www.bls.gov/osmr/research-papers/2023/ec230050.htm)
9. [Bowles, Babcock, and Lai (2007). Social incentives and gender differences in initiation.](https://gap.hks.harvard.edu/social-incentives-gender-differences-propensity-initiate-negotiations-sometimes-it-does-hurt-ask)
10. [Bryant / Bock (2013). In head-hunting, big data may not be such a big deal (NYT).](https://www.nytimes.com/2013/06/20/business/in-head-hunting-big-data-may-not-be-such-a-big-deal.html)
11. [Built In. Get paid to train AI.](https://builtin.com/articles/train-ai-side-hustle)
12. [Campion, Palmer, and Campion (1997). A review of structure in the selection interview.](https://onlinelibrary.wiley.com/doi/10.1111/j.1744-6570.1997.tb00709.x)
13. [Candor. Salary negotiation guide.](https://candor.co/guides/salary-negotiation)
14. [CaseInterview.com (Victor Cheng).](https://caseinterview.com/)
15. [CaseQuestions.com (Marc Cosentino).](https://casequestions.com/)
16. [Cialdini. Workplace negotiation (Influence at Work).](https://www.influenceatwork.com/wp-content/uploads/2018/05/Workplace-Negotiation-article.pdf)
17. [Cuddy, Wilmuth, Yap, and Carney (2015). Preparatory power posing.](https://www.hbs.edu/faculty/Pages/item.aspx?num=48292)
18. [DataAnnotation. FAQs.](https://www.dataannotation.tech/faqs)
19. [DataAnnotation. How to get data annotation jobs.](https://www.dataannotation.tech/blog/how-to-get-data-annotation-jobs)
20. [DOJ ADA.gov. AI guidance on hiring.](https://www.ada.gov/assets/pdfs/ai-guidance.pdf)
21. [EEOC. AI and the ADA.](https://www.eeoc.gov/eeoc-disability-related-resources/artificial-intelligence-and-ada)
22. [EPIC. In re HireVue FTC complaint.](https://epic.org/documents/in-re-hirevue/)
23. [EPIC. Full HireVue FTC complaint (PDF).](https://epic.org/wp-content/uploads/privacy/ftc/hirevue/EPIC_FTC_HireVue_Complaint.pdf)
24. [Ericsson, Krampe, and Tesch-Romer (1993). Deliberate practice.](https://gwern.net/doc/psychology/writing/1993-ericsson.pdf)
25. [Fortune (2021). HireVue drops facial monitoring.](https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/)
26. [Galinsky and Mussweiler (2001). First offers as anchors (Columbia PDF).](https://business.columbia.edu/sites/default/files-efs/pubfiles/11691/first_offers.pdf)
27. [Glassdoor. Interview duration in 25 countries.](https://www.glassdoor.com/blog/time-to-hire-in-25-countries/)
28. [Glassdoor. Prompt engineer salary.](https://www.glassdoor.com/Salaries/prompt-engineer-salary-SRCH_KO0,15.htm)
29. [HBR / Gallo (2020). How to nail a job interview remotely.](https://hbr.org/2020/06/how-to-nail-a-job-interview-remotely)
30. [HBR / Littlefield (2022). How to write a thank-you email after an interview.](https://hbr.org/2022/11/how-to-write-a-thank-you-email-after-an-interview)
31. [HBR / Malhotra (2014). 15 rules for negotiating a job offer.](https://hbr.org/2014/04/15-rules-for-negotiating-a-job-offer)
32. [HBR / Ringel (2021). 8 tips for conducting an excellent remote interview.](https://hbr.org/2021/10/8-tips-for-conducting-an-excellent-remote-interview)
33. [HireRight. Professional reference check report.](https://www.hireright.com/services/professional-reference-check-report)
34. [HireRight. What are reference checks.](https://support.hireright.com/en-US/articles/what-are-reference-checks-and-why-are-they-done)
35. [HireVue. Candidate interview tips.](https://www.hirevue.com/candidates/interview-tips)
36. [HireVue press release. Modern Hire acquisition.](https://www.hirevue.com/press-release/modernhire)
37. [HR Dive. HireVue acquires Modern Hire.](https://www.hrdive.com/news/hirevue-acquires-modern-hire-to-bolster-hiring-automation-capabilities/650173/)
38. [Huffcutt and Arthur (1994). Hunter and Hunter revisited.](https://home.ubalt.edu/tmitch/645/articles/Hunter%20and%20Hunter%20(1984)%20Revisited%20Interview%20Validity%20for%20Entry-Level%20Jobs.pdf)
39. [Illinois General Assembly. 820 ILCS 42 AI Video Interview Act.](https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=4015&ChapterID=68)
40. [IRS. Publication 15 Employer's Tax Guide.](https://www.irs.gov/forms-pubs/about-publication-15)
41. [Jobvite. Recruiting funnel benchmarks.](https://www.jobvite.com/blog/recruiting-funnel/)
42. [Journal of Business and Psychology (2024). Eye contact in video interviews.](https://link.springer.com/article/10.1007/s10869-024-09981-4)
43. [Kahneman and Tversky (1979). Prospect theory (MIT PDF).](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf)
44. [KFF. 2024 Employer Health Benefits Survey.](https://www.kff.org/health-costs/2024-employer-health-benefits-survey/)
45. [Levashina, Hartwell, Morgeson, and Campion (2014). The structured employment interview.](http://www.morgeson.com/downloads/levashina_hartwell_morgeson_campion_2014.pdf)
46. [Levels.fyi. Prompt engineer compensation.](https://www.levels.fyi/t/prompt-engineer)
47. [Levels.fyi. Verified methodology.](https://www.levels.fyi/verified/)
48. [Littler. EEOC Title VII AI guidance analysis.](https://www.littler.com/news-analysis/asap/eeoc-issues-guidance-use-artificial-intelligence-tools-employment-selection)
49. [Littler. NYC Local Law 144 final regulations.](https://www.littler.com/news-analysis/asap/new-york-city-adopts-final-regulations-use-ai-hiring-and-promotion-extends)
50. [Lou Adler Group. Performance-based hiring.](https://www.louadlergroup.com/about-us/performance-based-hiring/)
51. [Lukacik, Bourdage, and Roulin (2022). Into the void: AVI conceptual model.](https://www.sciencedirect.com/science/article/abs/pii/S1053482220300620)
52. [Macnamara and Maitra (2019). Deliberate practice replication.](https://royalsocietypublishing.org/rsos/article/6/8/190327)
53. [MasterClass. Chris Voss calibrated questions.](https://www.masterclass.com/articles/how-to-use-calibrated-questions-to-negotiate-strategically)
54. [McDaniel, Whetzel, Schmidt, and Maurer (1994). Employment interview meta-analysis.](https://home.ubalt.edu/tmitch/645/articles/McDanieletal1994CriterionValidityInterviewsMeta.pdf)
55. [Mindrift. FAQ.](https://mindrift.ai/faq)
56. [Mindrift. Pay rates blog.](https://mindrift.ai/blog/money)
57. [NYC DCWP. Automated employment decision tools.](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page)
58. [OpsArmy. DataAnnotation application process.](https://www.operationsarmy.com/post/waiting-to-hear-back-your-complete-guide-to-the-data-annotation-hiring-process-and-response-times)
59. [Outlier. FAQ.](https://outlier.ai/faq)
60. [Ouyang et al. / InstructGPT (2022).](https://arxiv.org/abs/2203.02155)
61. [PON. 3 winning strategies for salary negotiation.](https://www.pon.harvard.edu/daily/salary-negotiations/negotiate-salary-3-winning-strategies/)
62. [PON. Anchoring bias and range offers.](https://www.pon.harvard.edu/daily/negotiation-skills-daily/anchoring-bias-negotiation-get-ahead-range-offer/)
63. [PON. Backlash effect for women negotiators.](https://www.pon.harvard.edu/daily/salary-negotiations/the-backlash-effect-for-women-negotiators-in-hollywood-and-beyond-nb/)
64. [PON. Principled negotiation.](https://www.pon.harvard.edu/daily/negotiation-skills-daily/principled-negotiation-focus-interests-create-value/)
65. [PON. What is anchoring in negotiation.](https://www.pon.harvard.edu/daily/negotiation-skills-daily/what-is-anchoring-in-negotiation/)
66. [Robert Half / Accountemps (2017). Thank-you note survey.](https://press.roberthalf.com/2017-11-20-Thank-You-Notes-Can-Tip-Scale-in-Job-Candidates-Favor-Yet-Few-Write-Them)
67. [Roth, Bobko, and McFarland (2005). Work sample test validity.](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1744-6570.2005.00714.x)
68. [Sackett, Zhang, Berry, and Lievens (2022). Revisiting meta-analytic estimates.](https://psycnet.apa.org/record/2022-17327-001)
69. [Schmidt and Hunter (1998). The validity and utility of selection methods.](https://www.researchgate.net/publication/283803351)
70. [Schmidt, Oh, and Shaffer (2016). 100 years update.](https://home.ubalt.edu/tmitch/645/session%204/Schmidt%20&%20Oh%20validity%20and%20util%20100%20yrs%20of%20research%20Wk%20PPR%202016.pdf)
71. [Shinya et al. (2024). Off-camera gaze in online interviews.](https://www.nature.com/articles/s41598-024-60371-5)
72. [SHRM. Boost your interview chances with a thank-you note.](https://www.shrm.org/topics-tools/news/talent-acquisition/boost-your-interview-chances-with-a-thank-you-note)
73. [SHRM. HireVue discontinues facial analysis.](https://www.shrm.org/topics-tools/news/talent-acquisition/hirevue-discontinues-facial-analysis-screening)
74. [SHRM. Structured interview toolkit.](https://www.shrm.org/topics-tools/tools/toolkits/transform-interviewing-into-strategic-talent-selection)
75. [Simmons and Simonsohn (2017). P-curving the power-pose evidence.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2791272)
76. [Smart and Street (2008). Who: The A Method for hiring.](https://ghsmart.com/insights/who-the-a-method-for-hiring/)
77. [TopResume. Post-interview thank-you importance.](https://topresume.com/career-advice/post-interview-thank-you-importance)
78. [VidCruiter. One-way video interviews.](https://vidcruiter.com/video-interviewing/one-way/)
79. [VidCruiter. Pre-recorded video interviews.](https://vidcruiter.com/video-interviewing/pre-recorded/)
80. [Yerkes and Dodson (1908). Strength of stimulus and rapidity of habit-formation.](https://psychclassics.yorku.ca/Yerkes/Law/)
