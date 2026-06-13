---
categories: [sources]
type: reference
target_path: .claude/skills/brief/ref-briefing-structure.md
tags: [topic/briefing-structure, topic/analytic-tradecraft, topic/briefing]
aliases: [briefing structure, briefing format, morning note structure, PDB structure, composition doctrine]
related:
  - "[[hot]]"
  - "[[ref-regime-taxonomy]]"
  - "[[ref-evidence-hierarchy]]"
  - "[[ref-research-methodology]]"
  - "[[analysis-depth-standard]]"
  - "[[doctrine.template]]"
  - "[[ref-market-calendar]]"
  - "[[ref-geopolitical-framework]]"
status: active
created: 2026-04-23
updated: 2026-04-23
word_count: 6024
sources_count: 104
---

# Briefing structure reference for /brief v2

## Table of contents

- **1.** Introduction and scope
- **2.** Three institutional briefing traditions
- **3.** BLUF discipline
- **4.** Counter line and the Tenth Man principle
- **5.** Alternative Analysis distinct from Counter
- **6.** Priced In and market-expectations framing
- **7.** Regime, Macro, and Coherence headers
- **8.** Portfolio Health letter grade
- **9.** Signal Dashboard structure
- **10.** Thesis Status Board structure
- **11.** Portfolio Movers with What / So What / Now What
- **12.** Calendar with conditional framing
- **13.** Pre-Earnings Monitor and PEAD signaling
- **14.** Geopolitical section and CFA 3-stage filter
- **15.** Scenario Bar
- **16.** Intelligence Gaps versus Warning Problems
- **17.** Optionality Map and Today's Focus
- **18.** FOLLOWUPS:skills coordination block
- **19.** Canonical frontmatter schema
- **20.** Meta.json sidecar schema
- **21.** Section ordering and regime-conditional expansion
- **22.** Prose-style discipline
- **23.** Composition pseudocode
- **24.** Limitations and evolution
- **25.** References

## 1. Introduction and scope

This reference codifies the document form of the `/brief` v2 canonical briefing. It is the third panel of a triptych. The first panel, `ref-regime-taxonomy.md`, supplies the six-class day regime, four-class macro regime, and three-class cross-asset coherence taxonomies consumed by Phase D of the skill. The second panel, `ref-evidence-hierarchy.md`, supplies the source-trust grades (A through F) and calibrated probability language consumed by Phase E. This third panel supplies structural doctrine consumed by Phase L (composition) and by Phase N (the Pre-Output HALT gate that validates every structural item before write).

Scope is the form, not the content. Every rule here addresses how a section is headed, ordered, populated, skipped, budgeted, or cross-referenced. No rule here addresses what signal belongs in the Signal Dashboard or how a thesis transitions from HEALTHY to WATCH; those determinations live in `ref-monitoring-rules.md` and the individual thesis files. Every structural decision below is anchored to a named doctrine. Uncited rules are defects, per the discipline described in the CIA [Tradecraft Primer](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf) (CIA, 2009) and in ODNI [Intelligence Community Directive 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf) (ODNI, 2015), both of which require explicit sourcing for any analytic claim.

Out of scope are live examples tied to current events, any reproduction of sell-side desk color not available to retail, and any generic "Today's Focus" language that fails the commander's-intent test described in section 17. Also out of scope is any structural element that cannot be justified against the four traditions surveyed in section 2: President's Daily Brief doctrine, hedge-fund morning notes, sell-side morning calls, and buy-side pre-market preparation.

## 2. Three institutional briefing traditions

The `/brief` v2 canonical form inherits from four distinct institutional traditions. Each tradition evolved under different constraints, and the inheritance is selective. A reader should understand which element comes from which tradition so that the ordering, prose discipline, and omissions become legible rather than arbitrary.

The oldest tradition is the President's Daily Brief, delivered since the Kennedy administration and heavily reformatted after successive transitions. The publicly accessible PDB corpus spans the 1961-1977 window, with the CIA declassifying roughly 2,500 Nixon and Ford era PDBs in 2016 (per the [CIA PDB collection](https://www.cia.gov/readingroom/presidents-daily-brief) and the accompanying [Nixon and Ford delivery history](https://www.cia.gov/resources/publications/presidents-daily-brief-delivering-intelligence-to-nixon-and-ford/), CIA, 2016). The PDB contributes BLUF ordering, Key Judgments convention, calibrated probability language under [ICD 203](https://www.intelligence.gov/assets/documents/intelligence-community-directives/ICD_203.pdf) (ODNI, 2015), and the analytic-line discipline formalized by Sherman Kent and codified in Jack Davis's Kent Center paper [Sherman Kent and the Profession of Intelligence Analysis](https://www.cia.gov/resources/csi/static/Kent-Profession-Intel-Analysis.pdf) (CIA, 2002).

The hedge-fund morning note tradition is epitomized by Bridgewater's Daily Observations, in continuous production since 1975 per [Bridgewater's own 50-year retrospective](https://www.bridgewater.com/50-years-of-the-bridgewater-daily-observations) (Bridgewater, 2025). The genre contributes the Signal Dashboard pattern, regime-conditional expansion, explicit positioning snapshots, and the operating discipline of writing for an audience that must act within one trading session. The [Bridgewater research hub](https://www.bridgewater.com/research-and-insights) (Bridgewater) and Ray Dalio's [Principles](https://www.principles.com/) (Dalio, 2017) articulate the underlying operating doctrine; Cliff Asness's [AQR Perspectives](https://www.aqr.com/Insights/Perspectives) archive and Howard Marks's [Oaktree memo series](https://www.oaktreecapital.com/insights) illustrate how the tradition tolerates long-form deviation only around a compact BLUF.

The sell-side morning call tradition supplies calendar discipline, overnight earnings coverage, pre-earnings monitoring, and scenario framing. Its public surface is visible in research hubs such as [Goldman Sachs Research](https://www.goldmansachs.com/insights/goldman-sachs-research) (Goldman Sachs), the Morgan Stanley [Consilient Observer](https://www.morganstanley.com/im/en-us/financial-advisor/insights/series/consilient-observer.html) series, and [Bernstein Research](https://www.bernsteinresearch.com/). Morning-call format is regulated indirectly through [FINRA Rule 2241](https://www.sifma.org/news/blog/form-meets-function-sifmas-call-to-modernize-finras-research-rules) (per SIFMA commentary) which shapes what analysts can assert and how conflicts must be disclosed.

The buy-side pre-market preparation tradition contributes thesis-invalidation checks, optionality mapping, portfolio-mover triage, and the explicit distinction between what is priced and what is not. David Swensen's [Pioneering Portfolio Management](https://www.simonandschuster.com/books/Pioneering-Portfolio-Management/David-F-Swensen/9781416544692) (Swensen, 2009) is the canonical articulation of buy-side discipline, and the `/brief` framework extends it with Michael Mauboussin's base-rate work at Counterpoint Global, catalogued at his [writing archive](https://www.michaelmauboussin.com/writing) (Mauboswin, ongoing).

| Tradition | Core contribution to /brief v2 | Deliberate exclusion |
| --- | --- | --- |
| President's Daily Brief | BLUF, Counter line, Key Judgments, calibrated probability language, sources-and-methods discipline | Classified sourcing, compartmentation markings, tasking language |
| Hedge-fund morning note (Bridgewater, AQR) | Signal Dashboard, regime-conditional expansion, positioning snapshot, one-session action horizon | Proprietary factor exposures, leverage-conditioned trade ideas |
| Sell-side morning call (Goldman, MS, Bernstein) | Calendar window, overnight earnings, pre-earnings monitor, scenario framing, peer constellation | Desk color, single-source anonymous stories, non-retail borrow data |
| Buy-side pre-market prep | Thesis-invalidation checks, Optionality Map, Portfolio Movers, Priced In framing | Prime-broker flow data, IPO allocations, capacity-constrained ideas |

The inheritance matters because each exclusion is deliberate. Retail-accessible briefings that attempt to mimic sell-side desk color import unfalsifiable claims and degrade the evidence hierarchy established in `ref-evidence-hierarchy.md`.

## 3. BLUF discipline

BLUF, or Bottom Line Up Front, is the opening-sentence doctrine inherited from US military correspondence, codified in [Army Regulation 25-50](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN42124-AR_25-50-007-WEB-13.pdf) (Department of the Army) and mirrored in the [Navy Correspondence Manual SECNAV M-5216.5](https://www.navyband.navy.mil/documents/secnav-m52165-ch1.pdf) (Department of the Navy, 2015). AR 25-50 prescribes that the main point must appear in the first sentence of a memorandum; supporting detail follows in descending order of importance. The PDB adopted an analogous convention in its analytic line: the opening sentence must be the judgment, with evidence and caveats trailing (per the CIA's [Psychology of Intelligence Analysis](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf), Heuer, CIA, 1999).

Academic and legal writing adopted the same convention under different names. The Federal government's [Plain Writing Act of 2010](https://www.plainlanguage.gov/law/) (plainlanguage.gov) and the [Federal Plain Language Guidelines](https://digital.gov/resources/federal-plain-language-guidelines) (PLAIN, 2011) both require lead-with-main-point ordering in agency communications. The [ODNI Plain Language statement](https://www.dni.gov/index.php/plain-language-act) (ODNI) extends the same rule to IC publications. Web-reading research reinforces it: Jakob Nielsen's [How Users Read on the Web](https://www.nngroup.com/articles/how-users-read-on-the-web/) (Nielsen Norman Group, 1997) and the follow-up [How Little Do Users Read](https://www.nngroup.com/articles/how-little-do-users-read/) (Nielsen Norman Group, 2008) quantified that readers consume roughly 20-28% of text on a page, making the opening sentence the only reliably read unit.

BLUF IS the single most actionable analytic judgment for the session, stated in one sentence, with a regime tag and a confidence grade. BLUF IS NOT a summary, a headline, a market-direction guess, or a list of themes. A BLUF that reads "markets mixed on earnings" fails doctrine; a BLUF that reads "orbital-compute thesis remains HEALTHY heading into key earnings print; position sensitivity is asymmetric to downside" satisfies it. The cognitive-load rationale traces to George Miller's [The Magical Number Seven, Plus or Minus Two](https://psycnet.apa.org/record/1957-02914-001) (Miller, Psychological Review, 1956) and to John Sweller's cognitive load theory established in [Cognitive Load During Problem Solving](https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog1202_4) (Sweller, Cognitive Science, 1988): readers reserve minimal working memory for a briefing, and the BLUF must fit inside that reserve.

Failure modes are enumerable. A "headline BLUF" describes the day rather than the judgment. A "hedged BLUF" buries conclusion behind qualifiers. A "list BLUF" offers three or four points where one is required. An "absent BLUF" opens with context before conclusion. All four are disqualifying, per the analytic-line standard in [ICD 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf).

| BLUF failure mode | Symptom | Doctrinal fix |
| --- | --- | --- |
| Headline | Describes conditions, not judgment | State the decision implication |
| Hedged | "Markets may possibly" | Calibrated probability language |
| List | Three or four coequal bullets | Pick one; demote rest to Key Judgments |
| Absent | Leads with context or backstory | Invert to put conclusion first |

Quiet-day BLUF. On low-signal days the BLUF still exists; it states the absence of actionable signal and names the posture. Example class: "No thesis-invalidating signal overnight; market posture unchanged; focus on Thursday CPI." The anti-pattern is skipping BLUF on quiet days, which forces the reader to reconstruct posture from subsequent sections.

```python
def compose_bluf(session_data):
    # BLUF composition pseudocode
    regime = session_data.day_regime
    macro = session_data.macro_regime
    coherence = session_data.coherence
    thesis_board = session_data.thesis_status_board
    stressed = [t for t in thesis_board if t.status in ("STRESSED", "INVALIDATED")]
    watch = [t for t in thesis_board if t.status == "WATCH"]
    if stressed:
        lead = stressed[0]
        return f"{lead.name} thesis {lead.status}: {lead.one_line_reason}"
    if watch and coherence == "FRAGMENTED":
        lead = watch[0]
        return f"{lead.name} on WATCH amid FRAGMENTED cross-asset tape; {lead.one_line_reason}"
    if session_data.is_quiet():
        return f"No thesis-invalidating signal; {regime} regime holds; focus on {session_data.next_catalyst}"
    return f"{session_data.dominant_judgment} ({regime}; coherence {coherence})"
```

## 4. Counter line and the Tenth Man principle

The Counter line follows the BLUF immediately. It is the single strongest evidence-backed claim that the BLUF is wrong. Its origin is the Tenth Man principle, adopted by Israeli military intelligence after the 1973 Yom Kippur War surprise, and documented in the [Agranat Commission findings](https://israeled.org/resources/documents/agranat-yom-kippur-war/) (Center for Israel Education, 1974). The principle obliges one designated analyst to argue the opposite of the prevailing estimate when the first nine concur, specifically to inoculate against groupthink.

The CIA parallel is institutionalized Devil's Advocacy, catalogued in the [Tradecraft Primer](https://www.cia.gov/resources/csi/books-monographs/a-tradecraft-primer/) (CIA, 2009) alongside Team A-Team B competitive analysis. The 1976 Team B exercise on Soviet strategic objectives, documented in the [Foreign Relations of the United States series](https://history.state.gov/historicaldocuments/frus1969-76v35/d171) (State Department, 1976), remains the canonical Western example of institutional red-teaming at scale. RAND's contemporary red-teaming program, visible in publications such as [Exploring Red Teaming to Identify Risks from AI Foundation Models](https://www.rand.org/pubs/conf_proceedings/CFA3031-1.html) (RAND, 2023) and [Operational Risks of AI](https://www.rand.org/pubs/research_reports/RRA2977-2.html) (RAND, 2024), extends the practice to non-state-threat analysis.

Counter IS a concrete falsifier with a named evidentiary anchor and an implicit probability above roughly 15%. Counter IS NOT the canned opposite of the BLUF, a throwaway "but markets could fall instead," or an unsourced worry. A Counter line that reads "positioning data from CFTC commitments shows leveraged long extremes; a reversion would invalidate the HEALTHY read on orbital-compute" satisfies doctrine; one that reads "risks remain to the downside" fails it.

Edge cases. If no cited Counter above the 15% threshold exists, the Counter line is omitted rather than padded, and Phase N records the null explicitly. This mirrors the PDB practice in Richards Heuer's treatment of [Analysis of Competing Hypotheses](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf) (Heuer, CIA, 1999, Ch. 8): a hypothesis without evidentiary support is not entered into the matrix.

```python
def compose_counter(bluf, evidence_pool):
    # Counter composition pseudocode
    falsifiers = [e for e in evidence_pool if e.contradicts(bluf)]
    falsifiers = [e for e in falsifiers if e.source_grade in ("A", "B", "C")]
    ranked = sorted(falsifiers, key=lambda e: e.implied_probability, reverse=True)
    top = [e for e in ranked if e.implied_probability >= 0.15]
    if not top:
        return None  # skip rather than pad
    best = top[0]
    return f"Counter: {best.claim} ({best.source_citation}, {best.date})"
```

## 5. Alternative Analysis distinct from Counter

Alternative Analysis differs from Counter in kind, not degree. Counter inverts the BLUF. Alternative Analysis offers a third hypothesis that neither the BLUF nor the Counter contemplate. Its doctrinal basis is the Analysis of Competing Hypotheses framework in the CIA's [Psychology of Intelligence Analysis](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/) (Heuer, CIA, 1999) and the structured techniques catalogued in Pherson and Heuer's [Structured Analytic Techniques for Intelligence Analysis](https://us.sagepub.com/en-us/nam/structured-analytic-techniques-for-intelligence-analysis/book255432) (SAGE/CQ Press, 2021).

Related methodologies include High-Impact, Low-Probability analysis, Red Cell, Team A-Team B, and the Pre-Mortem. Gary Klein's [Performing a Project Premortem](https://hbr.org/2007/09/performing-a-project-premortem) (HBR, 2007) and his foundational [Sources of Power](https://mitpress.mit.edu/9780262611466/sources-of-power/) (MIT Press, 1998) establish the naturalistic decision-making basis for imagining a failed outcome before committing. Daniel Kahneman's [Thinking, Fast and Slow](https://us.macmillan.com/books/9780374533557/thinkingfastandslow/) (Kahneman, FSG, 2011) supplies the cognitive-bias rationale: without a designated alternative, System-1 anchoring suppresses search for third options.

Alternative Analysis is included when either the BLUF is not a binary judgment or when a high-impact low-probability scenario exists with enough evidence to be named. It is skipped when the session reduces to binary (thesis holds or breaks) or when no credible third frame exists above the 10% threshold.

```python
def compose_alternative(bluf, counter, evidence_pool):
    # Alternative Analysis composition pseudocode
    binary_collapse = bluf.is_binary() and counter is not None
    third_frames = [e for e in evidence_pool
                    if not e.supports(bluf) and not e.supports(counter)]
    third_frames = [e for e in third_frames if e.implied_probability >= 0.10]
    if binary_collapse and not third_frames:
        return None
    if not third_frames:
        return None
    frame = max(third_frames, key=lambda e: e.impact_if_true)
    return f"Alternative: {frame.hypothesis} ({frame.source_citation})"
```

The distinction between Counter and Alternative is not cosmetic. Heuer's core finding in [Chapter 8 of PIA](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf) was that analysts reliably under-generate hypotheses; the ACH matrix forces at least three. The `/brief` v2 structure enforces the same discipline on every session.

## 6. Priced In and market-expectations framing

The Priced In line anchors the briefing to market-implied expectations. Without it, BLUF and Counter float without reference to what the tape already reflects. Its conceptual origin is efficient-market discipline as developed in Markowitz's [Portfolio Selection](https://www.jstor.org/stable/2975974) (Journal of Finance, 1952) and refined through the Fama-French factor literature catalogued at the [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) (Tuck, ongoing) and the [Fama-French 1993 JFE paper](https://www.sciencedirect.com/science/article/abs/pii/0304405X93900235) (Fama and French, 1993).

The Priced In line answers one question: what does the current options-implied, futures-implied, or credit-spread-implied distribution already encode about the next catalyst? It connects forward to the Scenario Bar (section 15) by establishing the baseline against which bull, base, and bear probabilities are calibrated. It connects to the calibrated-probability language in `ref-evidence-hierarchy.md` by naming the source of the market prior.

The line is skipped when no active catalyst has market-implied pricing within the five-trading-day window, or when the Scenario Bar is itself skipped. Forcing a Priced In line on quiet days imports noise, which the [AQR Perspectives](https://www.aqr.com/Insights/Perspectives) series (AQR) and Howard Marks's [Oaktree memos](https://www.oaktreecapital.com/insights) (Oaktree) repeatedly identify as a failure mode of daily research.

## 7. Regime, Macro, and Coherence headers

Three one-line headers appear after BLUF, Counter, Alternative, and Priced In. They are Regime, Macro, and Coherence. Each is drawn from a distinct, orthogonal classification in `ref-regime-taxonomy.md`. Regime captures intraday market character (six classes). Macro captures the multi-week cross-asset backdrop (four classes). Coherence captures whether asset classes are telling a consistent story (three classes).

Orthogonality is the rationale for separation. A session can be TREND-DAY at the intraday regime level, LATE-CYCLE at the macro regime level, and FRAGMENTED at the coherence level simultaneously. Collapsing these into one header loses information. The discipline echoes ICD 203's requirement in [ODNI's analytic standards](https://www.dni.gov/files/documents/ICD/ICD-203.pdf) that analysts "distinguish between underlying intelligence information and analysts' assumptions and judgments," which requires decomposable labels rather than fused ones.

Header format is fixed: `Regime: TREND-DAY (confidence B)` on one line, `Macro: LATE-CYCLE (confidence B)` on the next, `Coherence: FRAGMENTED (confidence C)` on the third. Confidence grades are drawn from the A-F scale in `ref-evidence-hierarchy.md`. The three headers together replace any narrative "market environment" paragraph; narrative framings reliably drift into chatbot-style summarization, which is the primary pathology that [Plain Language Guidelines](https://www.plainlanguage.gov/guidelines/) (plainlanguage.gov) and Strunk's [Elements of Style](https://www.bartleby.com/141/) (Strunk, 1918) both attack.

## 8. Portfolio Health letter grade

Portfolio Health is expressed as a single letter grade (A through F), not a narrative summary. The grade summarizes the joint status of the configured theses weighted by position. The rubric is deterministic: A if all configured theses are HEALTHY and coherence is ALIGNED; B if at most one is WATCH; C if two or more are WATCH or one is STRESSED; D if two are STRESSED; F if any thesis is INVALIDATED.

The rationale traces to CFA Institute performance-attribution doctrine, articulated in Carl Bacon's [Performance Attribution: History and Progress](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-lit-review/2019/rflr-performance-attribution.pdf) (CFA Institute Research Foundation, 2019), and to the GIPS standards catalogued at [the CFA Institute GIPS page](https://rpc.cfainstitute.org/gips-standards) (CFA Institute). Performance-attribution practice prefers a small number of reproducible scalar summaries over narrative assessment because narrative invites selection bias. The same logic applies pre-trade, not only post-trade.

Historical precedent for letter grading in briefing contexts includes the ODNI's confidence-level language (high, moderate, low) and the DoD's classification-marking conventions. The letter grade supplies the reader with a one-character posture check before any narrative is read.

## 9. Signal Dashboard structure

The Signal Dashboard is an eight-column table tracking cross-asset signals relevant to the configured theses. Columns are: Signal, Level, Change, Range Position, Regime Fit, Thesis Affected, Grade, Composite. Inclusion requires that a signal materially influence at least one active thesis; inclusion on novelty alone is forbidden.

Composite Signal logic follows a rule-based aggregation: a positive composite requires majority positive across the Signal column entries for that thesis, weighted by grade. The aggregation mirrors the ensemble techniques in Nate Silver's [The Signal and the Noise](https://www.penguinrandomhouse.com/books/305826/the-signal-and-the-noise-by-nate-silver/) (Silver, 2012) and the ensemble forecasting discipline formalized in Philip Tetlock's [Superforecasting](https://www.penguinrandomhouse.com/books/227815/superforecasting-by-philip-e-tetlock-and-dan-gardner/) (Tetlock and Gardner, 2015) and operationalized through the [Good Judgment Project](https://goodjudgment.com/about/) (Good Judgment, ongoing).

Hedge-fund precedent is explicit. Bridgewater's Daily Observations, per [Bridgewater's retrospective](https://www.bridgewater.com/50-years-of-the-bridgewater-daily-observations), organize cross-asset signals in near-identical tabular form. The AQR archive at [AQR Insights Perspectives](https://www.aqr.com/Insights/Perspectives) similarly expresses views through a compact factor-signal dashboard rather than narrative. The structural discipline reflects the distinction Antti Ilmanen draws in [Expected Returns](https://www.wiley.com/en-us/Expected+Returns%3A+An+Investor%27s+Guide+to+Harvesting+Market+Rewards-p-9781119990772) (Ilmanen, Wiley, 2011) between signals and stories.

Budget. The Signal Dashboard caps at 12 rows. Above 12, composite signals replace constituent signals. The cap is drawn from Miller's 7 +/- 2 working-memory limit, published in [Psychological Review 1956](https://labs.la.utexas.edu/gilden/files/2016/04/MagicNumberSeven-Miller1956.pdf), buffered upward to accommodate tabular scanning per the F-pattern eye-tracking results at [Nielsen Norman Group](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) (NN/g, 2006).

## 10. Thesis Status Board structure

The Thesis Status Board is a three-column table: Thesis, Status (binary among HEALTHY, WATCH, STRESSED, INVALIDATED), Evidence (with inline citation). One row per configured thesis. Status is deterministic, not narrative; the rule-set lives in `ref-monitoring-rules.md` and in each thesis file. The Evidence column is mandatory and carries the grade.

The deterministic-binary rationale is the IC's Key Assumptions Check discipline, laid out in the [Tradecraft Primer](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf) (CIA, 2009, Ch. 4) and traceable to Kent's insistence on falsifiable analytic lines in Jack Davis's [Kent Center paper](https://www.cia.gov/resources/csi/studies-in-intelligence/archives/vol-1-no-5/sherman-kent-and-the-profession-of-intelligence-analysis/) (CIA, 2002). A narrative status ("thesis still broadly on track") fails the check because it cannot be falsified. A binary status paired with an invalidation trigger can.

Transition detection relies on the previous day's status, stored in the meta.json sidecar (section 20). A transition from HEALTHY to WATCH must cite the triggering signal. A transition to INVALIDATED must cite the breached invalidation trigger specified in the thesis file. Suppression rules apply: if no signal moved since the prior session, the status inherits and the Evidence column notes "unchanged since YYYY-MM-DD."

## 11. Portfolio Movers with What / So What / Now What

The Portfolio Movers section uses a three-question structure: What happened, So what does it mean for the thesis, Now what action follows. The framework is attributed to Terry Borton's 1970 Reach Touch and Teach and operationalized through [Rolfe, Freshwater, and Jasper](https://reflection.ed.ac.uk/reflectors-toolkit/reflecting-on-experience/what-so-what-now-what) (University of Edinburgh Reflection Toolkit, summarizing Rolfe et al., 2001). Mauboussin's base-rate discipline at the [Heilbrunn Center](https://business.columbia.edu/heilbrunn) (Columbia Business School) and through [Counterpoint Global](https://www.morganstanley.com/im/publication/insights/articles/article_theimpactofintangiblesonbaserates.pdf) (Morgan Stanley Investment Management) supplies the outside-view rigor that the So What column requires.

Columns: Ticker, Move (percent, beta-adjusted), What (the price action and proximate cause), So What (thesis implication with evidence grade), Now What (action vocabulary from a restricted set: HOLD, TRIM, ADD, EXIT, WATCH, INVALIDATE). The Now What column uses exactly one of the six tokens; free-text actions are forbidden. A copy-paste order block appears immediately below the table when any row carries ADD, TRIM, or EXIT.

Inclusion threshold. A holding appears if its beta-adjusted move exceeds 2.0 standard deviations of trailing 20-day volatility, or if a thesis-relevant catalyst prints for that ticker, or if cross-account combined exposure crosses a pre-specified band. Thresholds prevent the section from devolving into a movers list dominated by noise, which Jegadeesh and Titman's momentum work in [Returns to Buying Winners and Selling Losers](https://www.jstor.org/stable/2328882) (Journal of Finance, 1993) and subsequent factor research at the [Review of Financial Studies](https://academic.oup.com/rfs) (Oxford Academic) repeatedly characterize as costly.

Beta-adjusted impact and cross-account combined exposure are computed per the portfolio-attribution conventions in Grinold and Kahn, publisher page at [McGraw-Hill Advances in Active Portfolio Management](https://www.mheducation.com/highered/mhp/product/advances-active-portfolio-management-new-developments-quantitative-investing.html) (McGraw-Hill, 2020), and Chincarini and Kim's [Quantitative Equity Portfolio Management](https://www.mheducation.com/highered/product/quantitative-equity-portfolio-management-chincarini-kim/9780071459396.html) (McGraw-Hill, 2006).

## 12. Calendar with conditional framing

The Calendar section covers the next seven trading days. Sources include scheduled macro prints (via the Federal Reserve, Treasury, BEA, BLS), earnings calendars, and regulatory deadlines. Event format uses conditional framing: "If CPI above 3.4% month-over-month, then long-duration tech faces bid loss. If below 3.0%, then rate-cut path re-steepens." The "If A -> X. If B -> Y." convention forces scenario decomposition at event entry.

Each event carries a historical-pattern one-liner. For earnings, the pattern summarizes base-rate surprise magnitudes drawn from the peer constellation, a practice formalized in the peer-analysis literature and reflected in Michael Mauboussin's [Base Rate Book](https://www.michaelmauboussin.com/writing) (Mauboussin). For macro prints, the pattern summarizes trailing three releases. Pattern one-liners that restate schedule information without context fail Phase N.

Event classes include Tier-1 macro (CPI, NFP, FOMC), earnings (weighted by position sensitivity), Treasury issuance, and Fed speakers. Budget caps at 10 rows; the cap reflects the cognitive-load constraint quantified in Sweller's [cognitive load paper](https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog1202_4) (Sweller, 1988) and the F-pattern attention decay documented at [NN/g](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) (NN/g, 2006).

## 13. Pre-Earnings Monitor and PEAD signaling

The Pre-Earnings Monitor tracks holdings within a 10-trading-day earnings window. Fields include Ticker, Report Date, Implied Move (options-derived), Peer Pre-Announcements, PEAD Signal, Thesis Linkage. The section skips if no holdings fall within the window.

PEAD, or Post-Earnings Announcement Drift, is the empirical anomaly whereby prices under-react to earnings surprises and drift in the direction of the surprise for weeks after announcement. Its academic foundation is Ball and Brown's [An Empirical Evaluation of Accounting Income Numbers](https://www.jstor.org/stable/2490232) (Journal of Accounting Research, 1968), which first documented the effect; Foster, Olsen, and Shevlin's [Earnings Releases, Anomalies, and the Behavior of Security Returns](https://www.jstor.org/stable/247321) (The Accounting Review, 1984), which extended it; and Bernard and Thomas's [Post-Earnings-Announcement Drift: Delayed Price Response or Risk Premium?](https://www.jstor.org/stable/2491062) (Journal of Accounting Research, 1989) and their [1990 follow-up](https://deepblue.lib.umich.edu/handle/2027.42/28288) on serial correlation in earnings surprises.

Peer-constellation signaling exploits the cross-sectional pattern whereby pre-announcements within a tight peer set forecast the target firm's surprise direction. The linkage to the configured theses is explicit: if a peer pre-announcement signals demand acceleration for a held thesis exposure, the relevant Thesis Status Board entry inherits that signal at the specified evidence grade. The Pre-Earnings Monitor is the mechanism by which that inheritance is traced.

## 14. Geopolitical section and CFA 3-stage filter

The Geopolitical section imports framing from `ref-geopolitical-framework.md`, itself anchored in the CFA Institute curriculum on geopolitical risk catalogued at [Introduction to Geopolitics](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/introduction-geopolitics) (CFA Institute, 2026) and the Research and Policy Center hub on [Geoeconomics and Financial Markets](https://rpc.cfainstitute.org/themes/resilience/geoeconomics-financial-markets) (CFA Institute). The CFA 3-stage filter asks three questions in order: is the event material to cross-border capital flows; is it material to a holding's revenue or cost structure; is it material to a named thesis.

Inclusion rule. A geopolitical event enters the briefing only if it clears all three filter stages. A headline that fails any stage is suppressed, regardless of salience in mainstream coverage. The suppression mirrors the CFA Institute's long-standing [Financial Analysts Journal](https://rpc.cfainstitute.org/research/financial-analysts-journal) discipline on materiality. Exclusion rule. Any event that reduces to sentiment without a named transmission channel is suppressed, consistent with the source-grade rubric in `ref-evidence-hierarchy.md`.

The Position Sensitivity Matrix, defined in `ref-regime-taxonomy.md`, is cross-referenced here: each included event names the affected holdings, the transmission channel, and the direction of impact. This extends the conditional framing convention (section 12) to non-scheduled events.

## 15. Scenario Bar

The Scenario Bar presents Bull, Base, Bear framings with calibrated probabilities summing to 100%, and an Expected Value line reflecting the probability-weighted outcome. Its origin is the Shell scenario program, documented at [Shell Scenarios](https://www.shell.com/news-and-insights/scenarios.html) (Shell, ongoing since the early 1970s) and historically retrospected in [40 Years of Shell Scenarios](https://www.shell.com/news-and-insights/scenarios/what-are-shell-scenarios/_jcr_content/root/main/section_509167378/promo/links/item0.stream/1652289755448/a0e75f042fee5322b72780ee36e5ba17c35a4fc6/shell-scenarios-40yearsbook080213.pdf) (Shell, 2013). Pierre Wack's canonical articulations in [Scenarios: Uncharted Waters Ahead](https://hbr.org/1985/09/scenarios-uncharted-waters-ahead) (HBR, 1985) and [Scenarios: Shooting the Rapids](https://hbr.org/1985/11/scenarios-shooting-the-rapids) (HBR, 1985) remain the methodological references. Peter Schwartz's [The Art of the Long View](https://www.penguinrandomhouse.com/books/162919/the-art-of-the-long-view-by-peter-schwartz/) (Schwartz, 1991) and Gill Ringland's [Scenario Planning](https://www.sciencedirect.com/science/article/abs/pii/S0377221706011003) (Ringland, Wiley, 2006) extend the practice.

Structure. Three scenarios, each with a trigger condition, a one-line mechanism, a probability, and a portfolio impact expressed in basis points against combined cross-account exposure. The Expected Value line multiplies probability by impact and sums. The Scenario Bar fires on any session where a Tier-1 macro print or a Position-Sensitive earnings report falls within 48 hours.

Skip rule. No active catalyst within 48 hours, no Scenario Bar. Emission to frontmatter. When present, the Scenario Bar populates `priced_in_calls` in the YAML frontmatter with the base-case probability and the EV number; downstream scoring in Phase O uses those numbers against Brier-scoring methodology, introduced in [Verification of Forecasts Expressed in Terms of Probability](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml) (Brier, Monthly Weather Review, 1950). Probability-evidence grounding requires the probabilities trace to either market-implied pricing, historical base rates from the peer constellation, or named subjective priors with a grade, per `ref-evidence-hierarchy.md`.

## 16. Intelligence Gaps versus Warning Problems

The Intelligence Gaps section lists known-unknowns: questions whose answers would change a thesis status but whose answers are not yet obtainable. The Warning Problems section lists known-signals-below-trigger: signals that are moving in a concerning direction but have not yet breached an invalidation trigger. The distinction is doctrinal, not stylistic.

Its origin is Cynthia Grabo's [Anticipating Surprise: Analysis for Strategic Warning](https://apps.dtic.mil/sti/tr/pdf/ADA476752.pdf) (DIA / Joint Military Intelligence College, via [DTIC bibliographic record](https://apps.dtic.mil/sti/citations/ADA476752), 2002), which formalized warning as distinct from estimate work. Pillar, Gentry, and Gordon's [Strategic Warning Intelligence](https://press.georgetown.edu/Book/Strategic-Warning-Intelligence) (Georgetown University Press, 2019) extends the taxonomy. The distinction matters because gaps and warnings demand different responses: gaps demand collection; warnings demand re-grading of thesis status.

Format for Intelligence Gaps: numbered list, each entry a question, with a named collection plan and a deadline. Format for Warning Problems: numbered list, each entry a signal, with its current level, the trigger level, and the distance to trigger. Suppression logic: a gap that has persisted longer than 30 trading days without a collection plan is flagged; a warning that has narrowed to within 10% of trigger is escalated to the Thesis Status Board.

## 17. Optionality Map and Today's Focus

The Optionality Map catalogues asymmetric decisions available to the portfolio in the session. Fields: Decision, Cost (commission, spread, tax), Upside (named thesis payoff), Downside (named invalidation), Time-to-Decision. It precedes Today's Focus because decisions precede priorities. Forcing priorities first invites chatbot-style generic-advice items; decisions first forces concreteness.

Today's Focus is drawn from the military doctrine of commander's intent, codified in [Army Doctrine Publication 6-0 Mission Command](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN34403-ADP_6-0-000-WEB-3.pdf) (Department of the Army, 2019) and [Field Manual 6-0 Commander and Staff Organization](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN35404-FM_6-0-000-WEB-1.pdf) (Department of the Army, 2022). Commander's intent specifies the end-state and acceptable means in one or two sentences; subordinate decisions flow from that clarity. The [Combined Arms Center article on ADP 6-0](https://www.army.mil/article/225414/combined_arms_center_launches_new_mission_command_doctrine) (US Army, 2019) summarizes the 2019 update.

Structure. Today's Focus is three items maximum, each a named decision or watch-item with an explicit time-to-decision marker. Forbidden patterns: "monitor markets," "stay informed," "review positions." Each forbidden token fails Phase N because it cannot be falsified and cannot be completed.

## 18. FOLLOWUPS:skills coordination block

The FOLLOWUPS:skills block is a machine-parseable, HTML-commented fence emitted at the end of the briefing body. It emerged as Pattern 18 in the `/brief` v2 design as the mechanism by which downstream skills (such as thesis updates, evidence-ledger entries, or portfolio rebalance drafts) receive concrete triggers from the briefing.

Purpose. The block encodes skill invocations that should be considered for the current or next session. It is machine-parseable so that a downstream automation layer can extract invocations without regex-parsing free prose. The fence structure is a single HTML comment block opening with a sentinel token and closing with its mirror:

```
<!-- FOLLOWUPS:skills
skill: update-thesis
  args: { thesis: "orbital-compute", reason: "<TICKER> pre-announcement"}
  trigger: "status transition HEALTHY -> WATCH"
skill: rebalance-draft
  args: { scope: "orbital-compute sleeve", constraint: "no increase above THESIS_CAP_AMBER"}
  trigger: "cross-account exposure breach"
-->
```

Emission rules. A skill entry appears only if a concrete trigger fired in the current session. Empty emission is forbidden; the entire block is omitted if no triggers fired. Phase N validates that every entry names a skill in the catalog, supplies its required args, and includes a trigger string that references a signal captured elsewhere in the briefing. The emission discipline traces back to Gawande's [Checklist Manifesto](https://us.macmillan.com/books/9780312430009/thechecklistmanifesto/) (Gawande, Metropolitan Books, 2009) and his [New Yorker piece on the checklist](https://psnet.ahrq.gov/issue/checklist) (AHRQ PSNet summary of Gawande, The New Yorker, 2007): the downstream value depends on strict discipline about when an item fires.

Downstream consumption. An external orchestrator reads the block, dispatches each skill with its args, and records execution in the meta.json sidecar. The approach borrows from the Plain Writing Act machinery at [plainlanguage.gov](https://www.plainlanguage.gov/law/) in structuring human-readable prose adjacent to machine-parseable metadata.

```python
def emit_followups(session_results, skill_catalog):
    # FOLLOWUPS emission pseudocode
    entries = []
    for trigger in session_results.fired_triggers:
        skill = skill_catalog.resolve(trigger)
        if skill is None:
            continue
        args = skill.derive_args(trigger, session_results)
        if not args.complete():
            continue
        entries.append((skill.name, args, trigger.description))
    if not entries:
        return ""  # omit block entirely
    return render_followups_fence(entries)
```

## 19. Canonical frontmatter schema

The YAML frontmatter at the top of every `briefing-<YYYY-MM-DD>.md` file carries the structured state needed for downstream consumption and audit. Required fields: `date`, `day_regime`, `day_regime_confidence`, `macro_regime`, `macro_regime_confidence`, `coherence`, `coherence_confidence`, `thesis_status_board`, `portfolio_health_grade`, `priced_in_calls`, `conviction`, `bluf`, `counter`, `alternative`, `signal_dashboard_summary`, `warnings_count`, `gaps_count`, `followups_skills`.

Each field has a rationale. The three regime fields are required because the taxonomy in `ref-regime-taxonomy.md` demands them independently. Each confidence field is required because `ref-evidence-hierarchy.md` requires evidence grade on every material claim, and regime classification is a material claim. `thesis_status_board` is a structured object (one entry per configured thesis, status and evidence) because downstream continuity audits require it. `priced_in_calls` is structured because Brier scoring requires parseable probabilities. `bluf`, `counter`, and `alternative` are separate string fields rather than a single narrative because Phase N validates each independently.

User custom fields preserved byte-exact. Any field the user adds to a prior session's frontmatter (for example, `personal_note` or `journal_ref`) must survive into the current session unchanged. This discipline mirrors the "do no harm" principle in Gawande's [Checklist Manifesto](https://us.macmillan.com/books/9780312430009/thechecklistmanifesto/) (Gawande, 2009) applied to document continuity.

```yaml
date: 2026-04-23
day_regime: TREND-DAY
day_regime_confidence: B
macro_regime: LATE-CYCLE
macro_regime_confidence: B
coherence: FRAGMENTED
coherence_confidence: C
thesis_status_board:
  - name: orbital-compute
    status: HEALTHY
    evidence: "peer pre-announce positive (grade B)"
  - name: <thesis-slug-2>
    status: WATCH
    evidence: "unchanged since 2026-04-18"
  - name: <thesis-slug-3>
    status: HEALTHY
    evidence: "unchanged"
  - name: <thesis-slug-4>
    status: HEALTHY
    evidence: "unchanged"
  - name: <thesis-slug-5>
    status: WATCH
    evidence: "credit spreads widening (grade B)"
portfolio_health_grade: B
priced_in_calls:
  - event: "CPI 2026-04-24"
    base_probability: 0.55
    ev_bps: -18
conviction: 0.62
bluf: "orbital-compute HEALTHY heading into key earnings print; position sensitivity asymmetric to downside."
counter: "CFTC positioning at 95th percentile; reversion would invalidate HEALTHY read."
alternative: "Peer names miss while leading name beats; dispersion regime persists (15%)."
signal_dashboard_summary: "11 signals; composite positive for orbital-compute, mixed for <thesis-slug-5>."
warnings_count: 2
gaps_count: 1
followups_skills: ["rebalance-draft", "update-thesis"]
```

## 20. Meta.json sidecar schema

The meta.json sidecar lives alongside the Markdown briefing at `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>.meta.json`. Its purpose is to carry machine-only state that would pollute the human-readable Markdown if inlined: prior-session deltas, continuity audit checksums, skill dispatch receipts, and Brier-score precursors.

Why JSON alongside Markdown. The separation follows the same principle that distinguishes rendered prose from metadata in the [Federal Plain Language Guidelines](https://www.plainlanguage.gov/guidelines/): human-readable content carries semantics for humans; structured data carries semantics for machines. Mixing the two in one file degrades both. Cross-reference: the evidence grades captured in each thesis_status_board entry trace to the A-F scale in `ref-evidence-hierarchy.md`, and meta.json stores the primary-source URLs that back each grade.

Full schema fields: `briefing_date`, `generated_at`, `prior_briefing_date`, `thesis_transitions` (array of `{thesis, from_status, to_status, trigger, evidence_url}`), `continuity_checksum`, `skill_dispatches` (array), `brier_precursors` (array of `{call_id, probability, outcome_field}`), `section_order_applied`, `empty_sections_skipped`, `word_count`, `budget_seconds`, `ascii_validation`. The continuity checksum derives from a deterministic hash over the Thesis Status Board entries; a mismatch with the prior session's propagated checksum triggers Phase N.

## 21. Section ordering and regime-conditional expansion

The canonical section order is fixed under normal regimes and expands or contracts under exceptional regimes. The default order is: BLUF, Counter, Alternative, Priced In, Regime / Macro / Coherence headers, Portfolio Health grade, Signal Dashboard, Thesis Status Board, Portfolio Movers, Calendar, Pre-Earnings Monitor, Geopolitical, Scenario Bar, Intelligence Gaps, Warning Problems, Optionality Map, Today's Focus, FOLLOWUPS:skills.

Ordering rationale. BLUF first reflects AR 25-50 and plainlanguage.gov; Counter and Alternative follow because the Tenth Man principle requires the opposing view adjacent to the main judgment. Regime / Macro / Coherence follow the judgment because they ground it. The Signal Dashboard and Thesis Status Board follow because they supply the evidentiary substrate. Portfolio Movers follows because they translate status to action. Calendar and Pre-Earnings Monitor supply forward context. Geopolitical and Scenario Bar express asymmetries. Gaps and Warnings close the backward-looking content. Optionality Map precedes Today's Focus because decisions precede priorities. FOLLOWUPS:skills closes the body because its role is hand-off, not content.

Regime-conditional expansion and contraction matrix:

| Regime or condition | Expanded sections | Contracted or skipped sections |
| --- | --- | --- |
| TREND-DAY with ALIGNED coherence | Signal Dashboard, Scenario Bar | Geopolitical (if empty), Gaps (if empty) |
| CHOP with FRAGMENTED coherence | Thesis Status Board, Warning Problems | Scenario Bar (if no catalyst), Pre-Earnings Monitor (if empty) |
| GAP-AND-GO | Portfolio Movers, Today's Focus | Calendar (condensed) |
| LATE-CYCLE macro | Geopolitical, Scenario Bar | Pre-Earnings Monitor (unless in window) |
| CRISIS coherence | Warning Problems, Optionality Map, Intelligence Gaps | Portfolio Movers table condenses to top 3 |
| Quiet session | BLUF quiet-form, Today's Focus | Signal Dashboard condenses to composites |

Empty-section skipping semantics. A section is skipped entirely (header and body both omitted) if its content would be null under the skip rule defined in that section's design. Padding an empty section with boilerplate fails Phase N. Orphan headers (section title with no body) are a disqualifying defect.

```python
def order_sections(regime, macro, coherence, section_content):
    # Section ordering pseudocode
    order = CANONICAL_ORDER.copy()
    if regime == "TREND-DAY" and coherence == "ALIGNED":
        expand(order, ["Signal Dashboard", "Scenario Bar"])
    if regime == "CHOP" and coherence == "FRAGMENTED":
        expand(order, ["Thesis Status Board", "Warning Problems"])
    if macro == "LATE-CYCLE":
        expand(order, ["Geopolitical", "Scenario Bar"])
    if coherence == "CRISIS":
        expand(order, ["Warning Problems", "Optionality Map", "Intelligence Gaps"])
    return [s for s in order if not is_empty(section_content[s])]

def is_empty(content):
    if content is None: return True
    if isinstance(content, list) and len(content) == 0: return True
    if isinstance(content, str) and content.strip() == "": return True
    return False
```

## 22. Prose-style discipline

Thirteen rules govern prose across all sections. Collectively they separate a decision-grade briefing from a polished news summary.

**22.1 Lead with conclusion.** Every section opens with its conclusion, not its context, per AR 25-50 and the Plain Writing Act materials at [plainlanguage.gov](https://www.plainlanguage.gov/law/).

**22.2 Numbers before narrative.** Quantitative anchors precede descriptive prose. This reflects the information-design principles in Edward Tufte's oeuvre, catalogued at [edwardtufte.com](https://www.edwardtufte.com/books/) (Tufte, Graphics Press, 1983-2020).

**22.3 Temporal anchoring.** Every material claim carries a date or session reference. The discipline mirrors ICD 203 requirements in the [ODNI analytic standards](https://www.intelligence.gov/assets/documents/intelligence-community-directives/ICD_203.pdf) that judgments be traceable to the information on which they rest.

**22.4 Evidence grades on every material claim.** The A-F grade from `ref-evidence-hierarchy.md` appears inline with the claim. Grade omission is a Phase N defect.

**22.5 Calibrated probability language.** Percentages or the calibrated verbal scale (almost certainly, very likely, likely, roughly even, unlikely, very unlikely, almost no chance). Phrases such as "could" or "may" are forbidden outside explicit uncertainty acknowledgments. Rationale in Tetlock's [Superforecasting](https://www.penguinrandomhouse.com/books/227815/superforecasting-by-philip-e-tetlock-and-dan-gardner/).

**22.6 Financial shorthand without definition.** Terms such as PEAD, CFA 3-stage filter, beta-adjusted impact, peer constellation, thesis invalidation trigger, morning call, and desk color appear without expansion. The audience is assumed fluent.

**22.7 Bad news direct.** Thesis stress, portfolio drawdowns, and invalidated calls are stated plainly. Euphemism fails the Plain Writing Act discipline and Strunk's rule against the needless word in [The Elements of Style](https://www.bartleby.com/141/).

**22.8 Empty skipping.** Empty sections are skipped entirely. See section 21.

**22.9 Clear recommendations.** Action language in Portfolio Movers restricts to the six-token vocabulary (HOLD, TRIM, ADD, EXIT, WATCH, INVALIDATE).

**22.10 Expert-level throughout.** Explanation of primitives (what a basis point is, what a regime is) is forbidden; the briefing is a working document, not a primer.

**22.11 Forbidden patterns.** Enumerated in the table below; each pattern fails Phase N.

| Forbidden pattern | Failure mode | Replacement |
| --- | --- | --- |
| "Markets mixed" | Vague; no judgment | Name the specific divergence and the thesis implication |
| "Could" / "may" | Uncalibrated hedging | Percentage or calibrated verbal scale |
| "Monitor markets" | Cannot be falsified | Named decision with time-to-decision |
| "Worth watching" | No named trigger | Named trigger from thesis file |
| "Stay disciplined" | Generic advice | Specific action from six-token vocabulary |
| "Overall, things look..." | Narrative summary | Portfolio Health letter grade |
| "As always" | Filler opener | Delete |
| "Happy to revise" | Chatbot closing | Delete |

**22.12 Three-minute and 650-word budget.** The body is budgeted at roughly 650 words and three minutes of reading time. The threshold is anchored to Nielsen's quantification at [How Little Do Users Read](https://www.nngroup.com/articles/how-little-do-users-read/) (NN/g, 2008) and the scanning-pattern research at [Text Scanning Patterns](https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/) (NN/g, 2019), combined with working-memory limits in Baddeley's model surveyed at [Baddeley's model overview](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/baddeleys-model-of-working-memory) and articulated in Baddeley's [episodic buffer paper](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(00)01538-2) (Baddeley, Trends in Cognitive Sciences, 2000). Over budget, Phase N requires contraction; under budget is acceptable if no material content is missing.

**22.13 ASCII-only replacement table.** All output is ASCII. The replacement discipline:

| Unicode character | ASCII replacement |
| --- | --- |
| em-dash | `--` |
| en-dash | `--` |
| curly double quote | `"` |
| curly single quote | `'` |
| right arrow | `->` |
| left arrow | `<-` |
| less-or-equal | `<=` |
| greater-or-equal | `>=` |
| ellipsis character | `...` |
| non-breaking space | regular space |
| middle-dot bullet | `-` |
| euro sign | `EUR` |

## 23. Composition pseudocode

Eight Python functions specify the composition pipeline. Each is called in Phase L and validated in Phase N.

```python
def compose_bluf(session_data):
    # defined in section 3
    ...

def compose_counter(bluf, evidence_pool):
    # defined in section 4
    ...

def compose_alternative(bluf, counter, evidence_pool):
    # defined in section 5
    ...

def emit_followups(session_results, skill_catalog):
    # defined in section 18
    ...

def order_sections(regime, macro, coherence, section_content):
    # defined in section 21
    ...

def render_sections(ordered_sections, section_content, budget):
    # render only non-empty sections; enforce ASCII
    rendered = []
    for s in ordered_sections:
        body = section_content[s]
        if is_empty(body):
            continue
        rendered.append(render_header(s))
        rendered.append(render_body(body))
    output = join(rendered)
    assert ascii_only(output), "ASCII violation"
    return output

def validate_prose(output):
    # enforce forbidden-pattern table (section 22.11)
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(output):
            violations.append(pattern.name)
    for claim in extract_material_claims(output):
        if not claim.has_evidence_grade():
            violations.append(f"ungraded claim: {claim}")
        if not claim.has_temporal_anchor():
            violations.append(f"untimed claim: {claim}")
    return violations

def validate_budget(output):
    # enforce 650-word / three-minute budget
    wc = word_count(output)
    if wc > 750:
        return f"over budget: {wc} words"
    if wc < 250:
        return f"suspiciously under budget: {wc} words"
    return None

def distinguish_counter_vs_alternative(counter_text, alternative_text, bluf_text):
    # enforce that Alternative is not a re-statement of Counter
    if counter_text is None or alternative_text is None:
        return True
    if semantic_overlap(counter_text, alternative_text) > 0.6:
        return False
    if semantic_overlap(alternative_text, bluf_text) > 0.6:
        return False
    return True
```

The discipline echoes the checklist principle in Gawande's [Checklist Manifesto](https://us.macmillan.com/books/9780312430009/thechecklistmanifesto/): the point of the checklist is not to replace expert judgment but to prevent expert judgment from skipping steps under pressure.

## 24. Limitations and evolution

The `/brief` v2 structure codified here is not the endpoint. Three evolutionary pressures deserve explicit acknowledgment.

Post-2020 evolution. The PDB format itself shifted materially after the 2016-2020 transition, with reported changes to length and medium that are not publicly documented in the [CIA Studies in Intelligence archive](https://www.cia.gov/resources/csi/studies-in-intelligence/archives/) at the level of the Kennedy-Ford corpus. The structural conventions inherited here derive from the publicly declassified corpus and may diverge from current PDB practice. The Center for the Study of Intelligence [Kent Center page](https://www.cia.gov/resources/csi/books-monographs/) is the monitoring point for future doctrinal updates that enter the public record.

Retail-investor evolution. The four traditions surveyed in section 2 originated in institutions with cost structures unlike an individual investor's. Adaptations already present in `/brief` v2 include exclusion of desk color, exclusion of capacity-constrained trade ideas, and integration of the cross-account combined-exposure constraint (section 11). Further adaptations likely include expansion of the Optionality Map to cover tax-lot-aware decisions, and tightening of the Pre-Earnings Monitor to reflect the asymmetric tax treatment of short-term drift capture.

Limitations of the 16-phase arc. The current arc assumes daily cadence. Weekly or event-driven cadences require re-budgeting of section prominence (Signal Dashboard contracts; Scenario Bar expands). The arc also assumes a single active portfolio; multi-portfolio cases require extension of the Thesis Status Board to carry per-portfolio status columns.

Open questions. The calibration of Scenario Bar probabilities against realized outcomes requires at least 50 Brier-scored calls to stabilize, a threshold drawn from the [Good Judgment Project](https://goodjudgment.com/) experience. The composite-signal aggregation in the Signal Dashboard assumes independence across constituent signals, an assumption that fails in CRISIS coherence regimes; a conditional aggregation rule is a known gap.

Quarterly review cadence. This reference is reviewed every calendar quarter against (a) new PDB releases via the [CIA FOIA Electronic Reading Room](https://www.cia.gov/readingroom/), (b) new CFA Institute curriculum updates at the [CFA Institute Research Foundation publications](https://rpc.cfainstitute.org/research-foundation/publications) index, (c) new primary research in the [Journal of Finance](https://onlinelibrary.wiley.com/journal/15406261), the [Journal of Financial Economics](https://www.sciencedirect.com/journal/journal-of-financial-economics), and the [Journal of Portfolio Management](https://jpm.pm-research.com/), and (d) updated Plain Language guidance at [digital.gov](https://digital.gov/resources/federal-plain-language-guidelines). Material changes propagate through a versioned update with a documented delta.

## 25. References

1. [ODNI ICD 203 (PDF)](https://www.dni.gov/files/documents/ICD/ICD-203.pdf) -- Analytic Standards, ODNI, 2015.
2. [ICD 203 intelligence.gov mirror](https://www.intelligence.gov/assets/documents/intelligence-community-directives/ICD_203.pdf) -- IC hosted copy, ODNI.
3. [IC Directives landing page](https://www.dni.gov/index.php/what-we-do/ic-related-menus/ic-related-links/intelligence-community-directives) -- ODNI.
4. [ODNI Plain Language Act page](https://www.dni.gov/index.php/plain-language-act) -- ODNI.
5. [CIA Tradecraft Primer (PDF)](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf) -- CIA, 2009.
6. [Tradecraft Primer landing page](https://www.cia.gov/resources/csi/books-monographs/a-tradecraft-primer/) -- CIA, 2009.
7. [Psychology of Intelligence Analysis (PDF)](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf) -- Heuer, CIA, 1999.
8. [Psychology of Intelligence Analysis landing](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/) -- CIA, 1999.
9. [Sherman Kent Occasional Paper (PDF)](https://www.cia.gov/resources/csi/static/Kent-Profession-Intel-Analysis.pdf) -- Davis, CIA, 2002.
10. [Kent Center article page](https://www.cia.gov/resources/csi/studies-in-intelligence/archives/vol-1-no-5/sherman-kent-and-the-profession-of-intelligence-analysis/) -- CIA.
11. [Studies in Intelligence journal](https://www.cia.gov/resources/csi/studies-in-intelligence/) -- CIA.
12. [CSI Intelligence Archives](https://www.cia.gov/resources/csi/studies-in-intelligence/archives/) -- CIA.
13. [CIA FOIA Electronic Reading Room](https://www.cia.gov/readingroom/) -- CIA.
14. [PDB collection page](https://www.cia.gov/readingroom/presidents-daily-brief) -- CIA.
15. [Delivering Intelligence to Nixon and Ford](https://www.cia.gov/resources/publications/presidents-daily-brief-delivering-intelligence-to-nixon-and-ford/) -- CIA, 2016.
16. [CSI books and monographs](https://www.cia.gov/resources/csi/books-monographs/) -- CIA.
17. [Agranat Commission summary](https://israeled.org/resources/documents/agranat-yom-kippur-war/) -- CIE, 1974.
18. [Grabo Anticipating Surprise (DTIC PDF)](https://apps.dtic.mil/sti/tr/pdf/ADA476752.pdf) -- DIA, 2002.
19. [Grabo DTIC citation](https://apps.dtic.mil/sti/citations/ADA476752) -- DTIC.
20. [Strategic Warning Intelligence](https://press.georgetown.edu/Book/Strategic-Warning-Intelligence) -- Georgetown University Press, 2019.
21. [Structured Analytic Techniques textbook](https://us.sagepub.com/en-us/nam/structured-analytic-techniques-for-intelligence-analysis/book255432) -- Pherson & Heuer, SAGE/CQ Press, 2021.
22. [Team B FRUS document](https://history.state.gov/historicaldocuments/frus1969-76v35/d171) -- Department of State, 1976.
23. [RAND AI red-teaming workshop](https://www.rand.org/pubs/conf_proceedings/CFA3031-1.html) -- RAND, 2023.
24. [RAND operational risks of AI](https://www.rand.org/pubs/research_reports/RRA2977-2.html) -- RAND, 2024.
25. [Army Regulation 25-50 (PDF)](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN42124-AR_25-50-007-WEB-13.pdf) -- US Army.
26. [Navy SECNAV M-5216.5](https://www.navyband.navy.mil/documents/secnav-m52165-ch1.pdf) -- US Navy, 2015.
27. [ADP 6-0 Mission Command](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN34403-ADP_6-0-000-WEB-3.pdf) -- US Army, 2019.
28. [FM 6-0 Commander and Staff](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN35404-FM_6-0-000-WEB-1.pdf) -- US Army, 2022.
29. [Army.mil ADP 6-0 announcement](https://www.army.mil/article/225414/combined_arms_center_launches_new_mission_command_doctrine) -- US Army, 2019.
30. [Plain Writing Act (plainlanguage.gov)](https://www.plainlanguage.gov/law/) -- GSA / PLAIN.
31. [Federal Plain Language Guidelines (digital.gov)](https://digital.gov/resources/federal-plain-language-guidelines) -- PLAIN, 2011.
32. [plainlanguage.gov guidelines](https://www.plainlanguage.gov/guidelines/) -- PLAIN.
33. [Klein Performing a Project Premortem](https://hbr.org/2007/09/performing-a-project-premortem) -- HBR, 2007.
34. [Klein Sources of Power](https://mitpress.mit.edu/9780262611466/sources-of-power/) -- MIT Press, 1998.
35. [Kahneman Thinking, Fast and Slow](https://us.macmillan.com/books/9780374533557/thinkingfastandslow/) -- FSG, 2011.
36. [Morell The Great War of Our Time](https://www.hachettebookgroup.com/titles/michael-morell/the-great-war-of-our-time/9781455585663/?lens=twelve) -- Twelve / Hachette, 2015.
37. [Priess The President's Book of Secrets](https://www.hachettebookgroup.com/titles/david-priess/the-presidents-book-of-secrets/9781610395960/?lens=publicaffairs) -- PublicAffairs / Hachette, 2016.
38. [Miller 1956 APA record](https://psycnet.apa.org/record/1957-02914-001) -- APA / Psychological Review, 1956.
39. [Miller 1956 full text (UT Austin)](https://labs.la.utexas.edu/gilden/files/2016/04/MagicNumberSeven-Miller1956.pdf) -- Psychological Review, 1956.
40. [Sweller 1988 Cognitive Science](https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog1202_4) -- Wiley, 1988.
41. [Baddeley working memory overview](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/baddeleys-model-of-working-memory) -- Elsevier.
42. [Baddeley episodic buffer](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(00)01538-2) -- Cell Press / Trends in Cognitive Sciences, 2000.
43. [NN/g F-pattern original](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content-discovered/) -- Nielsen Norman Group, 2006.
44. [NN/g F-pattern follow-up](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) -- NN/g, 2017.
45. [NN/g How Users Read](https://www.nngroup.com/articles/how-users-read-on-the-web/) -- NN/g, 1997.
46. [NN/g How Little Do Users Read](https://www.nngroup.com/articles/how-little-do-users-read/) -- NN/g, 2008.
47. [NN/g Text Scanning Patterns](https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/) -- NN/g, 2019.
48. [Strunk Elements of Style (Bartleby)](https://www.bartleby.com/141/) -- Strunk, 1918.
49. [Pinker Sense of Style](https://www.penguinrandomhouse.com/books/310859/the-sense-of-style-by-steven-pinker/) -- Penguin, 2014.
50. [Tufte books](https://www.edwardtufte.com/books/) -- Graphics Press.
51. [Gawande Checklist Manifesto](https://us.macmillan.com/books/9780312430009/thechecklistmanifesto/) -- Metropolitan Books, 2009.
52. [Gawande The Checklist (AHRQ PSNet)](https://psnet.ahrq.gov/issue/checklist) -- New Yorker summary, AHRQ, 2007.
53. [Rolfe What / So What / Now What](https://reflection.ed.ac.uk/reflectors-toolkit/reflecting-on-experience/what-so-what-now-what) -- University of Edinburgh.
54. [Shell Scenarios](https://www.shell.com/news-and-insights/scenarios.html) -- Shell plc.
55. [40 Years of Shell Scenarios](https://www.shell.com/news-and-insights/scenarios/what-are-shell-scenarios/_jcr_content/root/main/section_509167378/promo/links/item0.stream/1652289755448/a0e75f042fee5322b72780ee36e5ba17c35a4fc6/shell-scenarios-40yearsbook080213.pdf) -- Shell, 2013.
56. [Wack Uncharted Waters Ahead](https://hbr.org/1985/09/scenarios-uncharted-waters-ahead) -- HBR, 1985.
57. [Wack Shooting the Rapids](https://hbr.org/1985/11/scenarios-shooting-the-rapids) -- HBR, 1985.
58. [Ringland Scenario Planning review](https://www.sciencedirect.com/science/article/abs/pii/S0377221706011003) -- Wiley, 2006.
59. [Schwartz Art of the Long View](https://www.penguinrandomhouse.com/books/162919/the-art-of-the-long-view-by-peter-schwartz/) -- Currency / PRH, 1991.
60. [Brier 1950](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml) -- Monthly Weather Review / AMS, 1950.
61. [Tetlock Superforecasting](https://www.penguinrandomhouse.com/books/227815/superforecasting-by-philip-e-tetlock-and-dan-gardner/) -- Crown / PRH, 2015.
62. [Good Judgment](https://goodjudgment.com/) -- Good Judgment Inc.
63. [Good Judgment Project](https://goodjudgment.com/about/) -- IARPA / GJP.
64. [Ball & Brown 1968](https://www.jstor.org/stable/2490232) -- JAR, JSTOR, 1968.
65. [Foster, Olsen & Shevlin 1984](https://www.jstor.org/stable/247321) -- Accounting Review, JSTOR, 1984.
66. [Bernard & Thomas 1989](https://www.jstor.org/stable/2491062) -- JAR, JSTOR, 1989.
67. [Bernard & Thomas 1990](https://deepblue.lib.umich.edu/handle/2027.42/28288) -- JAE, UMich Deep Blue, 1990.
68. [Markowitz 1952](https://www.jstor.org/stable/2975974) -- Journal of Finance, JSTOR, 1952.
69. [Jegadeesh & Titman 1993](https://www.jstor.org/stable/2328882) -- JF, JSTOR, 1993.
70. [Fama-French 1993](https://www.sciencedirect.com/science/article/abs/pii/0304405X93900235) -- JFE, Elsevier, 1993.
71. [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) -- Tuck / Dartmouth.
72. [Journal of Finance](https://onlinelibrary.wiley.com/journal/15406261) -- Wiley / AFA.
73. [Review of Financial Studies](https://academic.oup.com/rfs) -- Oxford Academic / SFS.
74. [Journal of Portfolio Management](https://jpm.pm-research.com/) -- PM-Research.
75. [Journal of Financial Economics](https://www.sciencedirect.com/journal/journal-of-financial-economics) -- Elsevier.
76. [Bridgewater Research & Insights](https://www.bridgewater.com/research-and-insights) -- Bridgewater.
77. [50 Years of Bridgewater Daily Observations](https://www.bridgewater.com/50-years-of-the-bridgewater-daily-observations) -- Bridgewater, 2025.
78. [Principles by Ray Dalio](https://www.principles.com/) -- Simon & Schuster, 2017.
79. [AQR Perspectives](https://www.aqr.com/Insights/Perspectives) -- AQR Capital.
80. [Ilmanen Expected Returns](https://www.wiley.com/en-us/Expected+Returns%3A+An+Investor%27s+Guide+to+Harvesting+Market+Rewards-p-9781119990772) -- Wiley, 2011.
81. [Oaktree Insights](https://www.oaktreecapital.com/insights) -- Oaktree Capital.
82. [Grinold & Kahn Advances](https://www.mheducation.com/highered/mhp/product/advances-active-portfolio-management-new-developments-quantitative-investing.html) -- McGraw-Hill, 2020.
83. [Chincarini & Kim QEPM](https://www.mheducation.com/highered/product/quantitative-equity-portfolio-management-chincarini-kim/9780071459396.html) -- McGraw-Hill, 2006.
84. [Swensen Pioneering Portfolio Management](https://www.simonandschuster.com/books/Pioneering-Portfolio-Management/David-F-Swensen/9781416544692) -- Free Press / S&S, 2009.
85. [Mauboussin Consilient Observer](https://www.morganstanley.com/im/en-us/financial-advisor/insights/series/consilient-observer.html) -- Morgan Stanley IM.
86. [Mauboussin Columbia page](https://business.columbia.edu/faculty/people/michael-mauboussin) -- Columbia Business School.
87. [Heilbrunn Center](https://business.columbia.edu/heilbrunn) -- Columbia Business School.
88. [Mauboussin writing archive](https://www.michaelmauboussin.com/writing) -- author site.
89. [Base Rate Book extension paper (PDF)](https://www.morganstanley.com/im/publication/insights/articles/article_theimpactofintangiblesonbaserates.pdf) -- Counterpoint Global / MSIM.
90. [CFA Institute Research Foundation](https://rpc.cfainstitute.org/research-foundation) -- CFA Institute.
91. [CFA RF publications](https://rpc.cfainstitute.org/research-foundation/publications) -- CFA Institute.
92. [Financial Analysts Journal](https://rpc.cfainstitute.org/research/financial-analysts-journal) -- CFA Institute.
93. [Bacon Performance Attribution review (PDF)](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-lit-review/2019/rflr-performance-attribution.pdf) -- CFA RF, 2019.
94. [CFA GIPS Standards](https://rpc.cfainstitute.org/gips-standards) -- CFA Institute.
95. [CFA Introduction to Geopolitics](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/introduction-geopolitics) -- CFA, 2026.
96. [CFA Geoeconomics hub](https://rpc.cfainstitute.org/themes/resilience/geoeconomics-financial-markets) -- CFA Institute.
97. [Shiller online data](http://www.econ.yale.edu/~shiller/data.htm) -- Yale.
98. [Sam Stovall SIFMA bio](https://www.sifma.org/people/sam-stovall) -- SIFMA.
99. [Sam Stovall S&P DJI](https://www.spglobal.com/spdji/en/contributors/sam-stovall/) -- S&P DJI.
100. [Newfound Research blog](https://blog.thinknewfound.com/) -- Hoffstein.
101. [Silver Signal and the Noise](https://www.penguinrandomhouse.com/books/305826/the-signal-and-the-noise-by-nate-silver/) -- Penguin, 2012.
102. [Goldman Sachs Research](https://www.goldmansachs.com/insights/goldman-sachs-research) -- Goldman Sachs.
103. [Bernstein Research](https://www.bernsteinresearch.com/) -- AB Bernstein.
104. [SIFMA on FINRA Rule 2241](https://www.sifma.org/news/blog/form-meets-function-sifmas-call-to-modernize-finras-research-rules) -- SIFMA.