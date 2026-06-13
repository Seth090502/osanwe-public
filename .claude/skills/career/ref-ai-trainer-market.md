---
categories: [sources]
type: reference
target_path: .claude/skills/career/ref-ai-trainer-market.md
tags: [topic/ai-trainer, topic/career-pipeline, topic/contractor-market]
aliases: [ai trainer market, data labeling methodology, rlhf contractor framework]
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
  - ref-contractor-economics
  - "[[ref-interview-tradecraft]]"
  - "[[career-moc]]"
  - "[[DataAnnotation]]"
  - "[[Outlier]]"
  - "[[Mindrift]]"
  - "[[ref-application-mechanics]]"
status: active
created: 2026-04-23
updated: 2026-04-23
word_count: 5519
sources_count: 52
---

## Table of contents

- **1.** Introduction and scope
- **2.** AI data-labeling supply chain
- **3.** Platform-tier taxonomy and evaluation framework
- **4.** Active-platform profiles
- **5.** Adjacent-platform landscape
- **6.** Pay-band interpretation framework
- **7.** Task-availability and foundation-model demand cycles
- **8.** Assessment-test tradecraft and academic methodology
- **9.** Quality-score management framework
- **10.** Worker-classification and regulatory framework
- **11.** Worker advocacy and labor-market research
- **12.** Contractor-transition-rule calibration methodology
- **13.** Limitations and evolution
- **14.** References

## 1. Introduction and scope

This document is the canonical methodology and framework reference for the AI-trainer, data-labeling, and RLHF contractor market as consumed by the `/career` v2 skill at `.claude/skills/career/SKILL.md`. It serves Phase F evaluate (AI_TRAINER archetype scoring refinement), Phase G pipeline (packet strategy per platform tier), and Phase J retro (archetype conversion-rate calibration).

The document is a durable structural framework, not a current-state market snapshot. The AI-trainer labor market is deliberately opaque: platforms do not publish task-pool data, per-worker income distributions, or platform-to-foundation-lab contract terms. Authoritative sources on specific platform earnings, task availability cycles, or quality-score mechanics are sparse. What remains durable is the taxonomy (who sits where in the supply chain), the methodology (how to read self-report pay data, how assessment quality is measured academically, how classification law applies), and the research-organization scorecards (Fairwork, DAIR, Data Workers' Inquiry, Oxford Internet Institute Fairwork) that periodically publish comparative platform evaluations. This document codifies that framework. Real-time per-platform intel is pulled by `/career evaluate` at runtime.

Scope explicitly excludes: (a) non-US labor markets, except where relevant to the supply chain reaching US-accessible platforms; (b) full-time machine-learning engineering roles (salaried W2 positions at foundation labs); (c) academic AI research positions; (d) visa-sponsored engineering roles. In scope: the 1099-contractor and W2-adjacent platform-worker layer that routes preference data, instruction-tuning demonstrations, red-team adversarial prompts, and factuality verification into the post-training pipelines of foundation models and their derivative products.

The companion references at `.claude/skills/career/` are `ref-scoring-model.md` (8-dimension rubric with calibration feedback), `ref-resume-tailoring.md` (deterministic keyword extraction + resume-diff-from-baseline block), `ref-packet-spec.md` (7-file canonical packet contract), and `ref-interview-tradecraft.md` (behavioral + technical + assessment-based interview methodology plus salary negotiation). Taken together they constitute the institutional-depth substrate for `/career` v2 decision support.

## 2. AI data-labeling supply chain

The labor market in scope routes human-feedback signal from individual contractors through a multi-tier platform ecosystem to a small number of foundation-model laboratories that fine-tune the resulting preference and demonstration data into post-training signals for large language models. Understanding the supply chain is prerequisite to interpreting any per-platform claim: the same piece of preference data may earn its contributor a different amount depending on which tier the platform occupies, which foundation lab is the end client, and how many intermediary margins are extracted along the way.

At the top of the chain, foundation-model labs include OpenAI, [Anthropic](https://www.anthropic.com/), Google DeepMind, Meta AI, Mistral AI, Cohere, xAI, and Amazon's Bedrock team. These labs commission preference data, instruction demonstrations, red-team adversarial tasks, and factuality annotations to fine-tune base models into instruction-following assistants ([Ouyang et al. 2022 InstructGPT](https://arxiv.org/abs/2203.02155)), safety-aligned assistants ([Bai et al. 2022 Constitutional AI](https://arxiv.org/abs/2212.08073)), and preference-aligned chat models ([Rafailov et al. 2023 DPO](https://arxiv.org/abs/2305.18290)). The labs' data requirements are specific: millions of preference-ranked response pairs, tens of thousands of expert-written demonstration prompts, and specialized red-team coverage across medical, legal, coding, mathematical, and multilingual domains.

The next tier consists of enterprise data vendors that hold commercial contracts with foundation labs. [Scale AI](https://scale.com/) is the dominant tier-1 vendor, with reported customers including Toyota, Lyft, and OpenAI (per [Hao, MIT Technology Review 2022](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/)); the company was valued at $7.3 billion in the period covered by that investigation and substantially higher in subsequent private-market rounds. [Appen Limited](https://www.appen.com/about-us), listed on the ASX as APX since 2018, serves "80% of the world's leading LLM builders" per its corporate disclosures, operates offices in ten-plus countries, and claims "1M+ Vetted contributors worldwide." Other tier-1 vendors include [Surge AI](https://www.surgehq.ai/), [Sama](https://www.sama.com/) (a Certified B Corporation with 15,000-plus associates), [iMerit](https://imerit.net/), [CloudFactory](https://www.cloudfactory.com/), and [Labelbox](https://labelbox.com/).

The tier-2 layer consists of direct-to-worker platforms that aggregate individual contractors into workforces servicing tier-1 vendors. [Outlier AI](https://outlier.ai/) is operated by Scale AI and is the public-facing successor brand to the earlier Remotasks platform ([MIT Technology Review 2022](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/)); the platform has "paid out over $500M to experts" cumulatively per its own homepage disclosures. [DataAnnotation.tech](https://www.dataannotation.tech/) operates as an independent direct-to-worker platform focused on contractor-model AI training work. [Mindrift](https://mindrift.ai/) is "powered by Toloka.ai" per its own disclosures, inheriting platform infrastructure from the legacy Toloka crowd-work system. [Handshake AI](https://joinhandshake.com/ai/) (an extension of the university-network platform Handshake) targets degreed and graduate-level experts.

The tier-4 crowd-source marketplace layer consists of older-generation platforms like Amazon Mechanical Turk and Clickworker, which historically handled image-labeling and simple annotation tasks and have been substantially displaced for frontier-model training by the higher-skill tier-2 and tier-3 direct-to-worker platforms.

The critical structural observation is that labor routed through any tier ends up in foundation-model training data with no worker visibility into which model, which lab, or which end product the work serves. Platform-level task descriptions are deliberately abstract. This opacity is a feature of the business model, not an oversight: it prevents workers from leveraging specific lab-client information in wage negotiations and obscures the margin-extraction chain between their per-task earnings and the commercial value of the trained model.

## 3. Platform-tier taxonomy and evaluation framework

The tier-classification rubric below allows placement of any AI-trainer platform into one of four structural categories. `/career` v2 Phase F evaluate applies this rubric when scoring a new platform-linked role; Phase G pipeline uses the tier to select appropriate packet-strategy and archetype-emphasis; Phase J retro tracks per-tier conversion rates separately because the underlying economics differ materially.

| Tier | Description | Characteristic pay bands | Candidate-selection rigor | Classification pattern |
|------|-------------|--------------------------|----------------------------|-------------------------|
| 1 | Enterprise data vendors with direct foundation-lab contracts | Mixed: salaried researchers + contractor operations at $15-35/hr | High; structured interviews + work-sample tests | Mix of W2 (researchers) + 1099 (operational workforce) |
| 2 | Direct-to-worker platforms with specialist-track structure | $25-100+/hr by track (generalist to specialist) | Medium-high; timeboxed assessment + skills screen | 1099 default; occasional W2-adjacent teams |
| 3 | Aggregator platforms routing tier-1 work to geographically distributed workforces | Volatile; worker-reported ranges wide | Low-medium; ID verification + basic skill screen | 1099 via country-specific arrangements |
| 4 | Crowd-source marketplaces for low-complexity annotation tasks | Per-task cents-to-dollars; effective hourly wage often sub-minimum in many jurisdictions | Low; ID verification only | 1099 / task-based |

**Signals indicating tier for an unknown platform:**

- **Domain age and parent-company disclosure.** Tier-1 platforms have multi-year histories and public (SEC-filed or ASX-filed) parent-company disclosures. Tier-2 platforms typically have 3-to-7-year histories with private-market funding rounds. Tier-3 and tier-4 platforms have opaque ownership or are wholly-owned subsidiaries of tier-1 parents.
- **Assessment rigor.** Tier-2 platforms gatekeep access with timeboxed assessment tests (2-6 hours; [Ouyang et al. 2022](https://arxiv.org/abs/2203.02155) describes the analogous initial demonstration-collection screening). Tier-3 platforms gate primarily on ID verification. Tier-4 platforms have no assessment.
- **Track-hierarchy disclosure.** Tier-2 platforms advertise specialist tracks (coding, domain expertise, language-specific) with premium pay bands. Tier-3 platforms typically route work by generic categories (image, text, audio). Tier-4 platforms have no track hierarchy.
- **Payment-rail sophistication.** Tier-2 platforms use direct deposit or same-day digital rails (Stripe, Wise). Tier-3 platforms frequently use PayPal or country-specific payment partners. Tier-4 platforms use gift cards, Amazon credits, or minimum-threshold payout systems that can trap small earnings.

## 4. Active-platform profiles

This section covers the four platforms currently in the user's `/career` v2 pipeline with detail limited to publicly verifiable facts drawn from official platform pages and corroborated secondary sources. Per `[[ref-evidence-hierarchy]]` conventions, self-reported earnings ranges are grade-C-with-caveat unless corroborated by tier-1 primary sources.

### 4.1 DataAnnotation.tech

Independent direct-to-worker platform. Per its own homepage, DataAnnotation describes itself as placing experts "reading an AI's attempt at a complex problem" and "telling it exactly where and why it went wrong" ([dataannotation.tech](https://www.dataannotation.tech/), accessed 2026-04-23). The platform emits explicit pay bands: "Domain experts: $50-$100+/hour; Generalists: $25-$30+/hour" with specialized roles such as Senior Software Engineers listed at "$50-$75+/hour." Classification language is explicit: "This is a flexible, task-based contractor role. You work remotely on your own schedule, focused on output quality rather than hours logged." Three-step onboarding: (1) assessment aligned with expertise area; (2) project access after assessment pass; (3) per-completed-project payment. The platform emphasizes "Not everyone gets in--that's the point," signaling above-median assessment rigor for a direct-to-worker platform. Parent-company disclosures are not visible from the homepage. The platform has been documented in community discussion threads (Reddit r/DataAnnotationTech) as offering quality-gated task flow with per-project payment via direct deposit or PayPal; independent verification of cumulative payout figures is not available.

### 4.2 Outlier AI

Operated by Scale AI per explicit homepage disclosure: "Outlier is a platform operated by Scale AI" ([outlier.ai](https://outlier.ai/), accessed 2026-04-23). Successor-brand positioning relative to the earlier Remotasks platform is documented in the [MIT Technology Review 2022 Hao investigation](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/), which described Scale's earlier Remotasks Plus program (launched for Venezuela-based workers, later capped at 60 hours weekly and shut down entirely in April 2021) as the antecedent. The platform claims "$500M+ Paid to experts" cumulatively and advertises "Competitive pay + quality-based rewards, paid weekly" without disclosing specific hourly-rate bands on the public homepage. Work types include writing prompts, creating grading rubrics, and rating and ranking model outputs. Four-step application: profile creation, skills import and review, identity verification (government ID required), skill verification and earning. Onboarding takes 30-90 minutes and includes resume and LinkedIn profile submission. Classification is contractor-default per the tier-2 pattern. Fairwork's 2025 cloudwork ratings scored Remotasks at 2/10 ([Fairwork 2025 Cloudwork Ratings](https://fair.work/en/ratings/cloudwork/)), the second-lowest tier alongside Fiverr, placing the Scale-operated ecosystem in the sub-fair bracket on Oxford's five-principle framework.

### 4.3 Mindrift

Powered by Toloka AI BV per its own homepage ([mindrift.ai](https://mindrift.ai/), accessed 2026-04-23), inheriting platform infrastructure from the Toloka crowd-work system. Mindrift advertises pay bands "$15-$100+/hr" with specific active roles at up to $90/hr (Data Science, Machine Learning Engineer). A disclaimer clarifies that "earnings vary based on hours worked and quality" and that the advertised "$300/week" example is not guaranteed. Work types include AI safety testing (adversarial prompting, vulnerability identification), reasoning and scenario development (medicine, finance, education), creative evaluation, domain-specific expertise roles (Python coding, legal consulting, design), and writing and editing. Classification is contractor-based with bi-weekly payments. US accessibility is implied by US-law-specific roles but not explicitly guaranteed on the homepage. The Toloka AI parent has legacy ties to Yandex, which triggered sanctions-related access questions for US-based workers in 2022-2024 that workers should verify currently.

### 4.4 Scale AI (direct)

Tier-1 anchor. Scale AI operates internal teams staffed via W2 and contractor arrangements in addition to its Outlier worker-platform. The company's public disclosures are limited to its marketing website ([scale.com](https://scale.com/)) and commercial announcements. Scale was valued at $7.3 billion as of the period covered by the [MIT Technology Review 2022 investigation](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/) and substantially higher in subsequent private-market rounds; IPO filings have been anticipated but not publicly disclosed as of early 2026. Customers named in the Hao investigation include Toyota, Lyft, and OpenAI. For the user's pipeline, Scale direct is relevant primarily as the ecosystem anchor behind Outlier rather than as a directly-accessible worker platform: Scale's internal roles are typically W2 positions at competitive bay-area salaries that are out of the user's current target archetype.

### 4.5 Mercor

NEW PROFILE 2026-04-29 -- promoted from adjacent-platform after user flagged as Tier-1 outreach target. Founded 2023 by three Bay Area high school friends turned Thiel Fellows: Brendan Foody (CEO), Adarsh Hiremath (CTO), Surya Midha (Board Chairman); the trio became the youngest self-made billionaires in 2025 per [Fortune 2026-01-13](https://fortune.com/2026/01/13/will-ai-take-my-job-or-human-skills-protect-me-mercor-training-self-made-billionaires/). Last disclosed valuation $10 billion (November 2025) per [Sacra revenue/valuation profile](https://sacra.com/c/mercor/) and corroborating Yahoo Finance + Moneywise coverage. Mercor positions itself as an expert-hiring platform that contracts professionals to evaluate AI systems on micro-tasks (financial memos, legal briefs, code reviews) using detailed grading rubrics, not crowd-source data labeling. Customer base is the AI-lab tier (named relationships in public press: OpenAI, Anthropic-adjacent, multiple frontier labs unidentified by Mercor for confidentiality).

**Pay bands (Grade A primary, mercor.com homepage + corroborated public press):** $10/hr (bilingual generalists) to $150/hr (finance experts); platform-claimed average $86/hr ([mercor.com](https://www.mercor.com/) homepage 2026). Mercor publicly states it pays approximately $1.5-2 million daily to contractors in aggregate across roughly 30,000 active expert-pool contractors as of October 2025 per CEO statements covered in [Yahoo Finance 2026 Foody coverage](https://finance.yahoo.com/news/mercor-pays-over-1-5-065444594.html). Pay-band positioning places Mercor expert-tier in the same range as DataAnnotation domain-expert tier ($50-$100+/hour) but with materially higher ceiling for finance / legal / specialized engineering tracks ($150/hr documented). Per worker reports, payment cadence is per-task with weekly settlement; specific hourly-floor disclosures are project-and-rubric-specific and require triangulation.

**Application + interview mechanics (Grade A primary, mercor.com).** Application: (1) initial application form with role/expertise area selection; (2) AI-conducted 20-minute video interview tailored to the area of expertise, combining experience discussion with case-study assessment; (3) Mercor staff review of AI-interview transcript and recording; (4) qualification decision and assignment to expert pool. The AI-interview format is materially differentiated from peer platforms (DataAnnotation single-shot assessment / Outlier 30-90min skill-verification / Mindrift 5-min apply + AI interview): Mercor's structured-conversation format is closer to a remote first-round phone screen than a fixed-question assessment, which shifts qualifier weighting toward articulate verbal reasoning + portfolio-evidence narrative.

**Project Osanwe -> Mercor qualifier translation:** Mercor's structured-conversation assessment format favors candidates who can articulate systems-design choices with portfolio evidence in real-time. Project Osanwe's 17-skill agent framework + 16-phase A-P pipelines + Plan-agent autonomous execution validation are precisely the kind of "case-study-assessable" portfolio that the AI-interview format is built to evaluate. The 5,435-word PROJECT-OSANWE-PACKET whitepaper functions as the verbal-narrative anchor for the experience-discussion phase. Specialized tracks where the user's qualifier-acceptance probability is highest: AI engineering / agent orchestration / technical writing / Claude SDK consulting (if Mercor opens such tracks; verify at runtime).

**Risks (Grade B-D mix; require runtime triangulation):** Worker forums (r/Mercor) report variable post-qualification task-pool access (similar to Outlier task-drought pattern). Quality-rating dynamics are not publicly disclosed. Mercor's expert-tier focus means qualifying-acceptance is materially gated; high-failure-mode profile for candidates without strong domain credentials. Brendan Foody's media positioning ("a new category of work") is bullish, but platform classification, contractor-rule applicability, and 1099-tax treatment all match peer expert-tier platforms with no Mercor-specific exception.

**Tier classification per /career v2.2 routing (NEW):** Mercor sits in the Tier-1 / expert-tier hybrid alongside Surge AI and Invisible Technologies. Pay-band-realized scoring places Mercor expert-tier at top of compensation_upside band (23-25 points: $100+/hr) per ref-scoring-model.md v2.2 redistribution. Activation-speed estimate: 1-3 weeks application-to-first-task per public + community reports, dependent on track availability and AI-interview pass.

## 5. Adjacent-platform landscape

The following compact table covers the broader platform landscape adjacent to the user's active pipeline. Each row draws on official platform homepage content plus corroborating public disclosures. Pay bands and earnings claims require corroboration per `[[ref-evidence-hierarchy]]` before being cited in any evaluation.

| Platform | Tier | Parent / structure | US access | Classification | Notable signal |
|----------|------|---------------------|------------|-----------------|------------------|
| [Appen](https://www.appen.com/about-us) | 1 | ASX-listed (APX); 1996-founded; HQ AU + WA | Yes | 1099 default | 80% of LLM builders as customers; 1M+ contributors; Fairwork 2025 score 3/10 |
| [Sama](https://www.sama.com/) | 1 | B Corp certified; 15,000+ associates; ethical-labeling positioning | Yes | Mixed (W2 + 1099 by region) | Continental, Walmart, Microsoft customers; Kenya-based workforce documented in post-2022 litigation context |
| [iMerit](https://imerit.net/) | 1 | Private; India/US dual-HQ | Yes | 1099 default via regional entities | Enterprise-grade medical + automotive labeling focus |
| [Surge AI](https://www.surgehq.ai/) | 1 | Private | Yes | Contractor ("experts") | Tagline "Smart != Useful"; positioning against Scale AI on data-quality differentiation |
| [Prolific](https://prolific.com/) | 2 | UK-HQ; academic-research origin | Yes | Participant/contractor | 70+ countries; Google, Stanford, HuggingFace customers; Fairwork 2025 score 5/10 (highest in data-labeling tier) |
| [Labelbox](https://labelbox.com/) | 1/2 hybrid | Private; platform + workforce | Yes | Mixed | Platform software + Turquoise-branded workforce |
| [CloudFactory](https://www.cloudfactory.com/) | 1/2 hybrid | Private; Kenya/Nepal-based workforce | Yes | W2-adjacent (country-specific) | Mission-driven positioning; named in Data Workers' Inquiry coverage |
| [Handshake AI](https://joinhandshake.com/ai/) | 2 | Subsidiary of Handshake university network | Yes | Contractor | Degreed-expert targeting; university-credential gated |
| [Invisible Technologies](https://www.invisible.co/) | 1/2 hybrid | Private | Yes | W2-adjacent | Positions as AI operations company; labor disclosed as US-based worker-agents |
| [Toloka AI](https://toloka.ai/) | 3 | Former Yandex subsidiary; now independent | Contested | 1099 via platform | Legacy Russian market; US sanctions context post-2022 |
| Amazon Mechanical Turk | 4 | Amazon subsidiary | Yes | 1099 | Legacy crowd-source; displaced for frontier AI training; Fairwork unrated |

## 6. Pay-band interpretation framework

Platform pay data falls into four source-quality tiers. Applying the `[[ref-evidence-hierarchy]]` Grade A-F scale produces the following interpretation framework that `/career` v2 Phase F evaluate applies uniformly when any platform pay claim is consumed.

**Grade A (primary):** Platform official pages disclosing specific hourly or per-task ranges (e.g., the DataAnnotation.tech "$25-$30+/hour" generalist band cited above). These are contractually meaningful when tied to specific platform communications; they are nonetheless advertising claims and subject to the platform's own earnings-disclaimer language.

**Grade B (rigorous secondary):** Published academic or research-organization surveys with disclosed methodology. The [Fairwork Cloudwork 2025 Ratings](https://fair.work/en/ratings/cloudwork/) score platforms on a five-principle rubric (fair pay, fair conditions, fair contracts, fair management, fair representation). Worker earnings are evaluated against local minimum wages in worker jurisdictions. Fairwork's methodology involves direct worker engagement and platform disclosure review, producing scores 0-10; the 2025 cycle rated Appen 3/10, Remotasks 2/10, Prolific 5/10, Fiverr 2/10, and Upwork 1/10. The [Data Workers' Inquiry](https://data-workers.org/) conducts participatory ethnographic research across nine countries including Kenya, Syria, Brazil, France, Germany, and Spain, with platform-specific worker-testimony outputs; its WIRM methodology (Workers' Inquiry as Research Methodology) centers worker voice over platform claim.

**Grade C (aggregator / self-report):** Glassdoor, Indeed, Payscale, and Levels.fyi aggregates. These are self-submit datasets with meaningful sampling bias (workers choosing to submit are not representative of the worker population). Report these with explicit sample-size + self-report caveat when cited. In the AI-trainer market specifically, Levels.fyi coverage is thin because the platform primarily serves W2 tech-employee comparisons; Glassdoor and Indeed coverage of direct-to-worker platforms like DataAnnotation and Outlier is increasing but still shallow relative to established employers.

**Grade D (worker-forum self-report):** Reddit threads (r/OutlierAI, r/ScaleAI, r/BeerMoney, r/DataAnnotationTech), Discord servers, Telegram channels. Individual earnings claims in these sources are Grade D and require triangulation against at least one Grade-A or Grade-B source before being cited in an evaluation. Aggregate sentiment from these forums is a legitimate qualitative signal (payment delays, account deactivation patterns, task-drought episodes) but aggregate quantitative income claims require corroboration.

**First-90-day income adjustment.** Per the user's `[[contractor-transition-rule]]`, the $[CONTRACTOR_MONTHLY_FLOOR]/mo x 2 consecutive months threshold cannot reasonably be achieved in the first 90 days of platform activation for two structural reasons: (1) assessment-to-task-pool-access lag (typically 1-4 weeks on tier-2 platforms per [Hao 2022](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/) and subsequent corroborating forum data); (2) initial quality-score ramp in which the first 10-30 submitted tasks are weighted heavily for platform-internal quality classification ([Krippendorff 1980 content-analysis methodology](https://en.wikipedia.org/wiki/Krippendorff%27s_alpha) and subsequent IAA literature). Realistic first-90-day projection: 40-60% of steady-state monthly earnings capacity. This is a floor-level calibration and should be framed explicitly in any evaluation emitting rule-state-proximity projections.

## 7. Task-availability and foundation-model demand cycles

Task-availability on AI-trainer platforms follows predictable structural cycles driven by the underlying foundation-model training and post-training release calendar. Per the [Ouyang et al. 2022 InstructGPT paper](https://arxiv.org/abs/2203.02155), RLHF-based fine-tuning requires two distinct data types (demonstrations and preference rankings) collected in sequential stages; demand for each data type rises and falls on a 3-to-9-month cycle tied to the underlying lab's model-release cadence. The [Christiano et al. 2017 foundational RLHF paper](https://arxiv.org/abs/1706.03741), [Stiennon et al. 2020 summarization RLHF paper](https://arxiv.org/abs/2009.01325), and [Glaese et al. 2022 Sparrow paper](https://arxiv.org/abs/2209.14375) all describe pipeline structures that imply discrete data-collection windows rather than continuous demand.

**Structural drivers of task availability:**

- **Pre-launch data surge.** Foundation labs increase preference-data commissioning in the 3-6 months before a new model-family release. Platform-side workers experience task-pool expansion, specialist-track opening, and bonus incentives during this window.
- **Post-launch decay.** The 6-12 months after a release shift demand toward red-teaming and factuality-patching rather than core preference data. Task-pool size contracts; specialist-track premia compress.
- **Cross-lab correlation.** Multiple foundation labs release on overlapping cycles. Task-pool availability is not sensitive to any single lab's schedule but to the aggregate release cadence across OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, and xAI.
- **Time-of-day and time-zone effects.** US-accessible task pools concentrate around US business hours because most reviewers and task-assignment systems operate on US time zones; workers in other jurisdictions compete for US-hour task slots.
- **Oversupply events.** Platforms periodically open application floodgates (reported for Outlier in multiple 2024-2025 windows per community-forum aggregate). These events compress task-availability per worker as the worker-supply curve shifts outward. Historical pattern per [Hao 2022](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/): when Venezuela-based worker supply surged onto Scale's Remotasks in 2018-2020, per-worker task availability declined materially.

The [Bai et al. 2022 Constitutional AI paper](https://arxiv.org/abs/2212.08073) documents a methodology (RLAIF) that substitutes AI-generated preference data for human-generated preference data in significant portions of the post-training pipeline, explicitly noting the approach "make[s] it possible to control AI behavior more precisely and with far fewer human labels." The subsequent [Rafailov et al. 2023 DPO paper](https://arxiv.org/abs/2305.18290) describes a simplified preference-data fine-tuning method that reduces the complexity and therefore data-volume requirement of the traditional RLHF loop. Both methodological advances are expected to reduce aggregate human-feedback-labor demand over the 2024-2027 period, with magnitude uncertain but directionally negative for platform workers. This is a structural headwind that `/career` v2 Phase J retro should monitor via task-pool aggregate signals.

## 8. Assessment-test tradecraft and academic methodology

Platform entrance assessments serve two functions simultaneously: (1) a screening gate filtering candidate workers by baseline quality; (2) a calibration event establishing the platform's initial quality-score attribution for a newly-activated worker. Both functions draw on the academic inter-annotator agreement (IAA) literature that platforms implicitly reference in their internal quality-assurance systems.

**Academic IAA foundation.** [Cohen's kappa coefficient](https://en.wikipedia.org/wiki/Cohen%27s_kappa) ([Cohen 1960 Educational and Psychological Measurement](https://journals.sagepub.com/doi/10.1177/001316446002000104)) measures agreement between two raters on categorical data, with interpretation via the [Landis and Koch 1977 scale](https://www.jstor.org/stable/2529310) (slight 0-0.20, fair 0.21-0.40, moderate 0.41-0.60, substantial 0.61-0.80, almost perfect 0.81-1.0). [Fleiss's kappa](https://en.wikipedia.org/wiki/Fleiss%27_kappa) ([Fleiss 1971 Psychological Bulletin](https://doi.org/10.1037/h0031619)) extends Cohen's kappa to more than two raters. [Krippendorff's alpha](https://en.wikipedia.org/wiki/Krippendorff%27s_alpha) addresses limitations of both: it accommodates nominal, ordinal, interval, ratio, polar, and circular data types; handles incomplete data; and adjusts for varying numbers of coders. The social-science minimum acceptable threshold is alpha >= 0.800 for reliable conclusions, 0.667-0.800 for tentative conclusions only, and below 0.667 generally unusable.

Platforms implicitly apply variants of these measures when computing quality scores from gold-task performance (comparing worker output to known-correct baseline) and peer-agreement metrics (comparing worker output to consensus of other workers on the same item). The specific coefficient and threshold used by any given platform is typically undisclosed; per the [Data Workers' Inquiry](https://data-workers.org/) research, "non-transparent platform rules" are a systematic worker complaint across multiple platforms.

**Assessment-test taxonomy.** Tier-2 platform entrance assessments typically fall into one of the following categories:

- **Prompt-quality evaluation.** Worker is given a model response and asked to score it on rubric dimensions (factuality, helpfulness, harmlessness). Timebox: typically 30-90 minutes.
- **Pairwise preference ranking.** Worker is given two model responses to the same prompt and asked to choose the better one, sometimes with forced-justification. Timebox: 60-180 minutes for full assessment.
- **Coding-track technical exercise.** Worker is given a programming problem with test cases. Timebox: 60-180 minutes. Archetype: AI_TRAINER coding track + PROMPT_ENGINEER.
- **Writing-sample + rubric-graded revision.** Worker writes a specified content type (explanation, summary, creative) and revises to match a rubric. Timebox: 120-240 minutes.
- **Factuality checks.** Worker is given statements with citations and asked to verify accuracy of source-claim mapping. Timebox: 60-120 minutes.
- **Red-teaming / adversarial task.** Worker generates adversarial prompts designed to elicit policy-violating outputs, or evaluates whether a model output violates specified policy. Timebox: 60-120 minutes.

**Candidate-side tradecraft.** Applicable across all assessment types: (a) complete within timebox but do not rush; quality is weighted heavier than speed on initial assessments because platforms use initial submissions to calibrate worker baseline. (b) Apply a thinking-aloud protocol where the assessment supports written justification; justifications supply signal the platform uses in specialist-track routing. (c) For coding-track assessments, test code against edge cases before submission; unit-test-mode completions signal process maturity. (d) The first 10-30 submitted tasks post-activation function analogously to the assessment: platforms weight early-task quality heavily in ongoing quality-score attribution. Treat the first two weeks of active work as an extended assessment period rather than normal operational production.

## 9. Quality-score management framework

Platform quality-score systems gate access to higher-paying task pools, specialist tracks, and bonus-eligibility. The mechanics are typically undisclosed; reverse-engineering from worker reports and platform documentation produces the following framework.

**Typical quality-score components:**

- **Gold-task agreement.** Platform inserts known-correct items into the worker's task stream; agreement rate with gold answer is a direct quality signal. Per [Krippendorff content-analysis methodology](https://en.wikipedia.org/wiki/Krippendorff%27s_alpha), gold-task design must balance representativeness (items should cover the task distribution) with discriminability (items should separate high-quality from low-quality workers).
- **Peer-agreement IAA.** Platform compares worker output to aggregate of other workers on the same item. High agreement signals conformity to platform-consensus quality; low agreement may signal either worker error or idiosyncratic high-quality judgment that disagrees with consensus.
- **Reviewer grading.** Platform-employed reviewers (typically tier-1 vendor staff) sample worker outputs and grade against rubric. Review latency is variable (days to weeks).
- **Attention-check items.** Trivially easy items inserted to detect workers who are not reading tasks. Failure rate is a workforce-integrity signal rather than skill signal.
- **Policy-compliance signals.** Worker-generated content is scanned for policy violations (profanity, disallowed content, AI-generated-submission detection). Any policy violation can trigger quality-score penalty or direct deactivation.

**Score decay and recovery.** Quality scores on most platforms use a trailing-window weighting (e.g., rolling 30-day or rolling 100-task window). Inactivity causes score decay on some platforms (penalty for not working) and score stability on others (neutral during inactivity). Recovery from a low score is typically possible but requires sustained high-quality performance over a recovery window that is not publicly documented.

**Common deactivation causes.** Per Hao 2022, [Data Workers' Inquiry 2023-2025 research](https://data-workers.org/), and aggregate worker-forum reports: (a) extended inactivity (typically 30-90 days depending on platform); (b) sustained quality drift (score falling below platform threshold); (c) suspected AI-assisted completion (platforms increasingly scan for LLM-generated worker outputs); (d) policy violations; (e) IP-address or identity-verification anomalies signaling account sharing. Appeal processes are inconsistent across platforms; per the [MIT Technology Review 2022 investigation](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/) and [Fairwork 2025 Cloudwork Ratings](https://fair.work/en/ratings/cloudwork/), most platforms score below 3/10 on the "fair management" principle that covers deactivation-appeal transparency.

## 10. Worker-classification and regulatory framework

Worker classification (employee vs independent contractor) is the single most consequential regulatory variable shaping pay, benefits, and legal protections on AI-trainer platforms. Classification determines whether minimum-wage law applies, whether the platform must pay employer-side FICA, whether the worker receives unemployment-insurance eligibility, and whether antidiscrimination and whistleblower protections attach. Platforms have strong economic incentives to classify workers as independent contractors; regulators have competing incentives to push classification toward employee status.

**IRS three-factor test.** The Internal Revenue Service applies a "common-law" test evaluating (1) behavioral control (who directs how the work is done), (2) financial control (who bears investment risk), and (3) type of relationship (intent, benefit provision, duration). See [IRS Pub 15-A](https://www.irs.gov/pub/irs-pdf/p15a.pdf) and [IRS Pub 1779](https://www.irs.gov/pub/irs-pdf/p1779.pdf). Failure on any factor pushes toward employee classification. For AI-trainer platforms, the behavioral-control factor is the weakest for platforms' contractor-classification defense: platforms dictate task structure, quality rubrics, deadlines, and deactivation grounds, all signals of employer-grade behavioral control.

**DOL 2024 Final Rule (effective March 11 2024).** The Department of Labor issued a Final Rule on Independent Contractor Classification under the Fair Labor Standards Act that applies a six-factor economic-realities test: (1) opportunity for profit or loss depending on managerial skill; (2) investments by the worker and the potential employer; (3) degree of permanence of the work relationship; (4) nature and degree of control; (5) extent to which the work performed is an integral part of the potential employer's business; (6) skill and initiative. See the [DOL Wage and Hour Division Final Rule page](https://www.dol.gov/agencies/whd/flsa/misclassification) and the [Federal Register publication (89 FR 1638)](https://www.federalregister.gov/documents/2024/01/10/2024-00067/employee-or-independent-contractor-classification-under-the-fair-labor-standards-act). The 2024 rule replaced the 2021 "core factors" rule with a more worker-friendly totality-of-circumstances analysis; litigation challenging the rule remains ongoing as of early 2026.

**California AB5 and the ABC test.** California Assembly Bill 5 ([codified January 1 2020](https://en.wikipedia.org/wiki/California_Assembly_Bill_5_(2019))) applies a three-prong ABC test codifying the 2018 California Supreme Court [Dynamex Operations West ruling](https://casetext.com/case/dynamex-operations-w-inc-v-superior-court-of-l-a-cnty). Workers must satisfy ALL THREE conditions to be classified as contractors: (A) freedom from control and direction of the hiring entity; (B) performance of work outside the usual course of the hiring entity's business; (C) customarily engaged in an independently established trade. The B-prong is the highest barrier for AI-trainer platforms: preference-data generation is arguably within the "usual course" of a data-labeling company's business. California exempts approximately 100 professions from AB5; AI-trainer work is not among the exempted categories. Proposition 22 (November 2020) carved out ride-share and delivery drivers; data labelers remain covered.

**Classification-risk signals per platform.** Platform TOS language, task-direction granularity, scheduling control, and degree of integration into the client workflow collectively signal classification risk. Tier-1 platforms with W2-adjacent arrangements (Sama, Invisible Technologies, Scale AI direct teams) operate structurally closer to employee classification with corresponding benefit provision. Tier-2 direct-to-worker platforms with contractor-default language but heavy behavioral control are most at risk of reclassification litigation. The [FTC's 2022 policy statement on gig worker classification](https://www.ftc.gov/news-events/news/press-releases/2022/09/ftc-issues-policy-statement-gig-economy-workers-protections-threats-unlawful-business-practices) signaled federal regulatory attention to this band.

**Litigation precedent worth tracking.** The [TIME Magazine 2023 Kenya-Sama-OpenAI investigation](https://time.com/6247678/openai-chatgpt-kenya-workers/) documented Sama-employed Kenyan workers paid under $2/hour for content-moderation work training ChatGPT's safety classifier; subsequent litigation in Kenyan courts has challenged Sama's classification practices and has produced settlement-stage rulings recognizing worker grievances. The case is precedent-setting for foreign-jurisdiction data-labeling litigation and a monitoring signal for US-domestic extensions.

## 11. Worker advocacy and labor-market research

Four research organizations provide durable methodology for evaluating AI-trainer platform labor practices. All four publish periodic reports that `/career` v2 Phase J retro should monitor for shifts in the platform landscape.

**Fairwork (Oxford Internet Institute).** The [Fairwork Foundation](https://fair.work/en/fw/homepage/) applies a five-principle rubric (fair pay, fair conditions, fair contracts, fair management, fair representation) scored 0-2 per principle for a 10-point maximum. The [2025 Cloudwork Ratings](https://fair.work/en/ratings/cloudwork/) covered 15 platforms with direct worker engagement. Top scorers were ComeUp, Elharefa, and Translated (8/10 each), with Terawork at 7/10. AI-adjacent platforms scored substantially lower: Prolific 5/10 (highest in the data-labeling subset), Appen 3/10, Remotasks 2/10, Fiverr 2/10, Clickworker 1/10, PeoplePerHour 1/10, Upwork 1/10. Mechanical Turk, Freelancer, and Microworkers were unrated. Fairwork's methodology combines worker-interview-based evidence review with platform self-disclosure.

**Distributed AI Research Institute (DAIR).** Founded by Timnit Gebru in 2021 following her departure from Google's Ethical AI team, [DAIR](https://www.dair-institute.org/) conducts independent research on AI systems and their labor impacts. Research outputs include [ethnographic studies](https://www.dair-institute.org/research/) of data-labeling worker conditions, particularly in East African markets. The institute's [Data Workers' Inquiry](https://data-workers.org/) project (collaboration with Weizenbaum Institute) applies participatory research methodology centering worker voice.

**Data Workers' Inquiry (Weizenbaum Institute, Miceli et al.).** Applies Workers' Inquiry as Research Methodology (WIRM) across nine countries including Kenya, Syria, Brazil, France, Germany, Spain. Outputs include zines, documentaries, comics, podcasts, and academic papers. Platform coverage includes Meta (through Sama subcontracting), TikTok, Amazon Mechanical Turk, Scale AI, Telus International, CloudFactory. Findings include systematic gift-card payment dependency, sudden account closures without appeal, non-transparent platform rules, and exposure to harmful content without mental-health support. See [Miceli et al.](https://weizenbaum-institute.de/en/research/) for institutional landing.

**Oxford Internet Institute (OII).** The [OII Fairwork project](https://fair.work/) hosts the scorecard framework. OII's [Digital Economy Research Group](https://www.oii.ox.ac.uk/research/) produces broader platform-labor research including cloudwork labor-market analysis. OII's [DemTech program](https://demtech.oii.ox.ac.uk/) tracks adjacent platform-labor issues including computational propaganda with worker-labor dimensions.

**Journalism investigations.** [Karen Hao's MIT Technology Review 2022 investigation](https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/) documented the Venezuela-Scale-Remotasks extraction chain. [The Verge's Josh Dzieza 2023 investigation](https://www.theverge.com/features/23764584/ai-artificial-intelligence-data-notation-labor-scale-surge-remotasks-openai-chatbots) (not directly fetchable but widely cited) profiled the platform workforce servicing OpenAI and competitors. [Wall Street Journal 2023-2024 coverage](https://www.wsj.com/tech/ai/) of the data-labeling industry focuses on enterprise-side contract dynamics. [Bloomberg coverage of Scale AI](https://www.bloomberg.com/) covers private-market valuation progression.

**Labor-market academic literature.** [Katz and Krueger (2016)](https://www.nber.org/papers/w22667) established the gig-economy labor-market baseline using Bureau of Labor Statistics data. [JPMorgan Chase Institute Online Platform Economy research](https://www.jpmorganchase.com/institute/all-topics/labor-markets) tracks gig-worker income volatility and platform participation patterns. [Bureau of Labor Statistics Contingent and Alternative Employment Arrangements supplement](https://www.bls.gov/cps/cpsaat01.htm) provides periodic labor-force-survey data on alternative-work participation.

## 12. Contractor-transition-rule calibration methodology

The user's `[[contractor-transition-rule]]` gates [EMPLOYER] exit on either (A) contractor income exceeding $[CONTRACTOR_MONTHLY_FLOOR]/month for two consecutive months, or (B) a W2 offer of $[W2_THRESHOLD] or greater. This section translates platform-level market intelligence into rule-state-proximity math consumable by `/career` v2 Phase F evaluate, Phase H apply, and Phase I tracker.

**Platform-expected-monthly-income estimation framework.** For each active-pipeline platform, derive an expected-monthly-income range as: `activation_probability * task_pool_access_probability * hours_committed * effective_hourly_rate * quality_ramp_discount`. Applicable components:

- **Activation probability.** Assessment-to-activation conversion rate. Platform-specific and undisclosed in aggregate; worker-forum reports cluster in 40-70% range for tier-2 platforms with the remainder failing assessment or entering silent-queue limbo.
- **Task-pool access probability.** Conditional on activation, probability of receiving sufficient task volume to earn meaningfully. Inversely related to aggregate worker-supply on the platform; tier-2 platforms with periodic oversupply events experience wide swings.
- **Hours committed.** The user's available contractor hours depend on other W2 commitments. Realistic contractor hours during transition: 15-25 hrs/week.
- **Effective hourly rate.** Per platform, from Grade-A or Grade-B sources preferred. DataAnnotation generalist band: $25-30/hr. DataAnnotation coding-track or specialist: $50-100/hr. Outlier: undisclosed specific rate; forum-reported ranges $15-50/hr depending on track. Mindrift: $15-100/hr advertised with heavy dispersion.
- **Quality-ramp discount.** First-90-day multiplier of 0.4-0.6 per section 6.

Applied to a target profile (JS/TS coding-track eligibility at DataAnnotation; 20 hrs/week commitment; 90-day ramp): projected month-3 steady-state earnings potential of $2000-$4500/month on single-platform activation, rising to $3000-$6000 on dual-platform and $4000-$7500 on triple-platform activation. The central estimate for dual-platform DataAnnotation-coding-track + Outlier activation at 20 hrs/week clears the Condition A threshold; single-platform activation is marginal; triple-platform activation has meaningful probability of exceeding the threshold with buffer.

**Diversification risk-mitigation framework.** Activating multiple platforms simultaneously reduces single-platform task-drought risk. Per gig-labor economic literature ([JPMorgan Chase Institute research](https://www.jpmorganchase.com/institute/all-topics/labor-markets)), income variance for multi-platform gig workers is materially lower than single-platform workers at equivalent total earnings. Recommended activation sequence: DataAnnotation first (highest assessment rigor; activation signal; strongest publicly-disclosed pay band); Outlier second (Scale ecosystem access; specialist-track opportunity); Mindrift third (Toloka infrastructure reliability; European-market specialist-track opening).

**Classification-shift risk to rule math.** If DOL 2024 rule litigation produces reclassification to employee status for Outlier or DataAnnotation workers mid-engagement, 1099 tax-withholding arrangements would require restructuring. Monitor via ref-contractor-economics update cadence.

**Application sequencing.** Activation-speed ranking (fastest to slowest): DataAnnotation (3-step, assessment-gated, typically 1-3 weeks to activation) > Outlier (4-step, identity + skill verification, typically 2-4 weeks) > Mindrift (CV + assessment, typically 2-6 weeks). Sequencing one-at-a-time avoids assessment-fatigue; sequencing in parallel maximizes time-to-first-task. Recommended: parallel activation across all three.

**Pipeline-health monitoring signals.** Phase I tracker should monitor: (a) platform-level announcement cadence; (b) oversupply event signals (sudden task-pool contraction reported across multiple workers); (c) new lab-contract announcements (task-pool expansion leading indicator); (d) classification-litigation developments; (e) Fairwork annual rating update (May-June publication cadence historically); (f) foundation-model release announcements (demand-cycle indicator).

## 13. Limitations and evolution

This document has durability constraints. Platform-specific details churn on 6-18-month cycles and should not be treated as stable; only the framework-level content (tier taxonomy, classification tests, IAA methodology, research-organization rubrics) is durable across multiple years.

**Data opacity is structural.** No amount of additional research will produce transparent task-pool data or per-worker earnings distributions from AI-trainer platforms; this opacity is a feature of the business model rather than a research gap. Workers making activation decisions must accept that pre-activation earnings forecasts carry wide confidence intervals.

**Platform lifecycle churn.** Any of the platforms named in this document may exit the market, pivot materially, or consolidate into a tier-1 parent within 18 months. Remotasks-to-Outlier rebranding is the canonical recent example. Fairwork ratings are updated annually; Data Workers' Inquiry publishes intermittently; platforms are added and removed.

**Foundation-model training-cycle dependency.** Human-feedback demand is structurally dependent on foundation-lab post-training cycle cadence, which is set by a small number of labs with closed release schedules. Forward projection beyond 12 months is speculative.

**Classification-law evolution.** DOL 2024 rule is subject to ongoing litigation. Trump administration policy signals include reverting to the 2021 rule or superseding with an entirely different framework. California AB5 has been narrowed via Proposition 22 and subsequent legislative carve-outs; further narrowing is politically plausible. Each classification-law shift materially affects platform economics and rule-state math.

**AI-replacing-AI-labeling feedback.** Constitutional AI, DPO, and related methodology advances that reduce human-feedback requirements may reduce aggregate platform demand over 2024-2027. Magnitude is uncertain; direction is plausibly negative for platform workers.

**Review cadence.** This document should be reviewed quarterly. Trigger events for out-of-cycle updates: (a) Fairwork annual ratings publication; (b) major platform classification litigation ruling; (c) new DOL or IRS regulatory action; (d) a named active-pipeline platform pivoting or exiting. Updates land as minor-version bumps with changelog entry in this section.

**Methodology-framework vs current-state distinction.** Per section 1, the document's value is the durable framework; per-platform current-state intel is pulled at runtime by `/career evaluate`. Readers consulting this document six months post-publication should treat platform-specific section 4 content as historical baseline and verify against current platform homepages before acting on any quantitative claim.

## 14. References

1. Anthropic company page. https://www.anthropic.com/
2. Ouyang et al. 2022, "Training language models to follow instructions with human feedback" (InstructGPT). https://arxiv.org/abs/2203.02155
3. Bai et al. 2022, "Constitutional AI: Harmlessness from AI Feedback." https://arxiv.org/abs/2212.08073
4. Rafailov et al. 2023, "Direct Preference Optimization: Your Language Model is Secretly a Reward Model." https://arxiv.org/abs/2305.18290
5. Christiano et al. 2017, "Deep Reinforcement Learning from Human Preferences." https://arxiv.org/abs/1706.03741
6. Stiennon et al. 2020, "Learning to summarize from human feedback." https://arxiv.org/abs/2009.01325
7. Glaese et al. 2022, "Improving alignment of dialogue agents via targeted human judgements" (Sparrow). https://arxiv.org/abs/2209.14375
8. Scale AI company page. https://scale.com/
9. Hao, Karen. 2022, "Artificial intelligence is creating a new colonial world order" (MIT Technology Review). https://www.technologyreview.com/2022/04/20/1050392/ai-industry-appen-scale-data-labels/
10. Appen About page. https://www.appen.com/about-us
11. Outlier AI homepage. https://outlier.ai/
12. DataAnnotation.tech homepage. https://www.dataannotation.tech/
13. Mindrift homepage. https://mindrift.ai/
14. Handshake AI. https://joinhandshake.com/ai/
15. Surge AI homepage. https://www.surgehq.ai/
16. Sama homepage. https://www.sama.com/
17. iMerit homepage. https://imerit.net/
18. CloudFactory homepage. https://www.cloudfactory.com/
19. Labelbox homepage. https://labelbox.com/
20. Invisible Technologies. https://www.invisible.co/
21. Prolific homepage. https://prolific.com/
22. Toloka AI homepage. https://toloka.ai/
23. Fairwork Cloudwork 2025 Ratings. https://fair.work/en/ratings/cloudwork/
24. Fairwork Foundation homepage. https://fair.work/en/fw/homepage/
25. Cohen's kappa (Wikipedia). https://en.wikipedia.org/wiki/Cohen%27s_kappa
26. Krippendorff's alpha (Wikipedia). https://en.wikipedia.org/wiki/Krippendorff%27s_alpha
27. Fleiss's kappa (Wikipedia). https://en.wikipedia.org/wiki/Fleiss%27_kappa
28. Cohen, J. 1960, "A coefficient of agreement for nominal scales" (Educational and Psychological Measurement). https://journals.sagepub.com/doi/10.1177/001316446002000104
29. Fleiss, J.L. 1971, "Measuring nominal scale agreement among many raters" (Psychological Bulletin). https://doi.org/10.1037/h0031619
30. Landis, J.R. and Koch, G.G. 1977, "The measurement of observer agreement for categorical data" (Biometrics). https://www.jstor.org/stable/2529310
31. California Assembly Bill 5 (Wikipedia). https://en.wikipedia.org/wiki/California_Assembly_Bill_5_(2019)
32. Dynamex Operations West v Superior Court (Cal 2018). https://casetext.com/case/dynamex-operations-w-inc-v-superior-court-of-l-a-cnty
33. DOL Wage and Hour Division Independent Contractor Classification. https://www.dol.gov/agencies/whd/flsa/misclassification
34. DOL 2024 Final Rule Federal Register. https://www.federalregister.gov/documents/2024/01/10/2024-00067/employee-or-independent-contractor-classification-under-the-fair-labor-standards-act
35. IRS Publication 15-A Employer's Supplemental Tax Guide. https://www.irs.gov/pub/irs-pdf/p15a.pdf
36. IRS Publication 1779 Independent Contractor or Employee. https://www.irs.gov/pub/irs-pdf/p1779.pdf
37. FTC Policy Statement on Gig Worker Protections 2022. https://www.ftc.gov/news-events/news/press-releases/2022/09/ftc-issues-policy-statement-gig-economy-workers-protections-threats-unlawful-business-practices
38. TIME 2023, "OpenAI Used Kenyan Workers on Less Than $2 Per Hour to Make ChatGPT Less Toxic." https://time.com/6247678/openai-chatgpt-kenya-workers/
39. Data Workers' Inquiry homepage. https://data-workers.org/
40. Distributed AI Research Institute (DAIR). https://www.dair-institute.org/
41. DAIR Research publications. https://www.dair-institute.org/research/
42. Oxford Internet Institute homepage. https://www.oii.ox.ac.uk/
43. Oxford Internet Institute Research. https://www.oii.ox.ac.uk/research/
44. Oxford Internet Institute DemTech. https://demtech.oii.ox.ac.uk/
45. Weizenbaum Institute Research. https://weizenbaum-institute.de/en/research/
46. Katz and Krueger 2016 NBER Working Paper 22667. https://www.nber.org/papers/w22667
47. JPMorgan Chase Institute Labor Markets research. https://www.jpmorganchase.com/institute/all-topics/labor-markets
48. Bureau of Labor Statistics CPS data. https://www.bls.gov/cps/cpsaat01.htm
49. The Verge 2023 data-labeling investigation. https://www.theverge.com/features/23764584/ai-artificial-intelligence-data-notation-labor-scale-surge-remotasks-openai-chatbots
50. Wall Street Journal AI coverage. https://www.wsj.com/tech/ai/
51. Bloomberg business coverage. https://www.bloomberg.com/
52. Data Workers' Inquiry Workers' Inquiry as Research Methodology. https://data-workers.org/
