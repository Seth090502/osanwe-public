---
categories: [sources]
type: reference
created: 2026-04-26
updated: 2026-04-26
status: active
tags:
  - topic/skill-infrastructure
  - topic/vault
  - topic/stats
aliases:
  - vault stats catalog
  - 18 statistics
related:
  - "[[SKILL|/vault SKILL.md]]"
  - "[[ref-audit-classifiers]]"
  - "[[ref-output-templates]]"
---

# /vault Statistics Catalog Reference

The 18 statistics /vault stats computes, with formulas + edge cases + thesis-importance weights + Brier-style continuity scoring methodology.

Statistics 1-9 are quantitative-snapshot metrics (state-at-time-of-run). Statistic 10 is calibration-trace (compares prior predictions vs current state). Statistics 11-18 are derived metrics over the snapshot.

## Thesis-importance weights (referenced by Classifier 5 stale-refs + /vault refresh + Statistic 15)

| Domain | Weight | Rationale |
|---|---|---|
| orbital-compute | 1.5 | Largest thesis exposure (highest-concentration thesis per doctrine template); highest-velocity refresh need |
| tokenized-settlement | 1.2 | High conviction; smaller exposure but thesis-defining |
| grid-storage | 1.0 | Baseline reference weight |
| platform-moats | 1.0 | Baseline reference weight |
| core-index | 0.8 | Lower priority; broad ETFs are diversification overlay |
| career | 1.3 | Active job search; high velocity for ref-doc refresh |
| golf | 0.7 | Low velocity; biomechanics is stable |
| supplements | 0.5 | Low velocity; biology is slow-moving |
| meta | 1.1 | Skill-infrastructure changes weekly; medium-high velocity |

## Statistic 1: file-counts-by-top-level-path

### Formula
```
for each top-level dir D in [Atlas, Calendar, Efforts, wiki, private, docs, .claude/skills (active only), .claude/skills/_archive]:
  count = len(glob D/**/*.md)
```

### Edge cases
- `.claude/skills` split: active skills count + archived count separately
- `private/` count includes path-guarded files (READ allowed for stats)
- `docs/` includes VAULT-HANDOFF-V*.md and PROJECT-OSANWE-PACKET.md
- Exclude: `.git/`, `node_modules/`, `.checkpoints/`, `.obsidian/`, `.smart-env/`, `career-ops/`

### Output table
| Top-level path | File count | Delta vs prior |

## Statistic 2: word-counts-by-top-level-path

### Formula
```
for each top-level dir D:
  total_words = sum(wc -w D/**/*.md)
  avg_words_per_file = total_words / file_count_from_stat_1
```

### Edge cases
- Frontmatter NOT excluded (counted as part of file content)
- kepano 150-line cap exception annotation: ref-*.md files in `Atlas/sources/*/` exempt from cap; flag any non-ref-doc files >2000 words as candidates for split
- Skip binary content (none in this vault; all .md are text)

### Output table
| Top-level path | Total words | Avg words/file | Files >2000w (split candidates) |

## Statistic 3: entity-coverage

### Formula
```
held_tickers = parse(private/holdings-taxable.md + private/holdings-ira.md) -> ticker symbols
existing_entities = basenames(wiki/entities/tickers/*.md)
missing_entities = held_tickers - existing_entities
coverage_pct = (held_tickers - missing_entities) / held_tickers * 100
```

### Edge cases
- Combined-account de-dup: a ticker held in both holdings-taxable + holdings-ira counts as 1
- ETFs and equities both included (VGT, VOO, etc. count as tickers)
- Crypto held in private/ files: separate sub-stat (e.g., BTC, ETH)

### Output table
| Held ticker | Has entity note? | Last entity update |

## Statistic 4: ref-doc-coverage

### Formula
```
for each domain D in [investing, career, supplements, golf, meta]:
  refs_built = count(Atlas/sources/D/ref-*.md with status: active or status: complete)
  refs_stub = count(Atlas/sources/D/ref-*.md with status: stub)
  refs_missing = MOC_table_claims - actual_files_on_disk
```

### Edge cases
- knowledge-moc.md Reference Document Status table is the canonical claim list; flag drift between table claims and on-disk frontmatter
- `.claude/skills/*/ref-*.md` counted separately as skill-companion refs (not domain refs)

### Output table
| Domain | Built | Stub | Missing-vs-MOC-claims | Coverage % |

## Statistic 5: freshness-distribution

### Formula
```
for each top-level path P:
  files_lt_7d = count(files where days_since_updated < 7)
  files_lt_30d = count(files where 7 <= days_since_updated < 30)
  files_lt_90d = count(files where 30 <= days_since_updated < 90)
  files_gt_90d = count(files where days_since_updated >= 90)
```

### Edge cases
- `Calendar/daily/*.md` exempt (always-fresh by definition; report by separate continuity stat 8)
- `_archive/` exempt (expected-stale)
- Files lacking `updated:` frontmatter field default to `created:` date for staleness; flag in Classifier 3 (frontmatter-schema)

### Output table
Heatmap-style: rows=top-level paths, columns=[<7d, <30d, <90d, >90d, total]

## Statistic 6: career-pipeline-by-status

### Formula
```
for each application packet in Efforts/career-search/applications/:
  read packet's frontmatter.status field
  group by status: READY_TO_SUBMIT, SUBMITTED, INTERVIEWING, OFFERED, REJECTED, CLOSED
```

### Edge cases
- DEPRECATED packets (Snapdocs, Medsender per session-log) reported separately as historical
- Same-company multiple-packet handling: count each packet, not each company

### Output table
| Status | Count | Companies |

## Statistic 7: session-log-entry-count (rolling 30d)

### Formula
```
entries_30d = count(### YYYY-MM-DD headings in Calendar/decisions/sessions-log.md within last 30 days)
entries_per_week = entries_30d / 4.3
session_skill_counts = parse "Skills invoked:" lines; aggregate by skill
```

### Edge cases
- Multi-session days (e.g., 2026-04-25 second session) counted as separate entries
- Aggregate by week-of-month + day-of-week patterns for cadence detection (input to Classifier 7 daily-continuity)

### Output table
| Total 30d | Avg/week | Top 5 skills (count) |

## Statistic 8: daily-note-continuity-score

### Formula
```
expected_dates_30d = [today - i for i in range(30)]
present_dates = basenames(Calendar/daily/*.md within 30d window)
gaps = expected_dates_30d - present_dates
weighted_gap_count = sum(weight per gap; weight=1.0 weekday, weight=0.3 weekend if no sessions-log activity that day)
continuity_score = 1.0 - (weighted_gap_count / 30.0)
```

### Edge cases
- Weekends with no sessions-log activity: 0.3 weight (legitimate no-activity)
- Weekends with sessions-log activity but missing daily note: 1.0 weight (real gap)
- Holidays: not auto-detected; user can mark in CLAUDE.local.md (future feature)

### Output table
| Score (0.0-1.0) | Gap dates (weighted) | Streak (consecutive days with notes) |

## Statistic 9: skill-invocation-frequency

### Formula
```
for each /<skill> mention in Calendar/decisions/sessions-log.md "Skills invoked:" lines (rolling 30d):
  increment skill_count[skill]
sort descending; report top 10
```

### Edge cases
- Deprecated skills (`/research`, `/review`) flagged but counted in historical
- Aggregate `/spark <mode>` variants under base `/spark` count (modes tracked in separate sub-stat)

### Output table
| Skill | 30d count | 90d count | Trend (up/down/stable) |

## Statistic 10: brier-calibration-carry

### Formula (Brier-style scoring across runs)
```
prior_stats_reports = glob(wiki/maintenance/stats-*.md sorted by mtime, last 3)
for each prior report:
  predicted_30d_trend = parse meta.json predicted_30d_trend ("improving" | "stable" | "declining")
  actual_trend = compare prior vault_health_score vs current vault_health_score
  prediction_correct = (predicted == actual)
  brier_score_per_report = 0 if prediction_correct else 1
calibration_score_30d = 1.0 - (sum(brier_scores) / count(prior_reports))
```

### Edge cases
- First run: no prior reports; `calibration_score_30d: null`; trend flagged as `first-stats`
- "stable" prediction: actual must be within +/- 5 of prior score
- "improving" / "declining": directional only; magnitude not scored

### Output
Single field in stats report frontmatter + meta.json: `calibration_score_30d: <float>`. Reported in Continuity vs Prior Stats table.

## Statistics 11-18: Derived metrics

### 11. avg-wikilinks-per-file
```
total_wikilinks = count(`[[` patterns across all .md files)
total_files = stat_1 sum
avg = total_wikilinks / total_files
```
Report: scalar value + 30d trend.

### 12. outbound-link-orphans
```
files_with_zero_outbound = count(files with 0 `[[` patterns in body, excluding frontmatter)
```
Exclude templates, archives, daily notes (high-churn). Flag as graph-orphan candidates.

### 13. inbound-link-orphans
```
for each file F:
  inbound_count = grep -c "[[<basename(F)>]]" across vault (excluding F itself)
  if inbound_count == 0 AND F not in (templates, archives, daily, private): flag as inbound-orphan
```

### 14. MOC-coverage-percentage
For each MOC (career, golf, investing, knowledge, supplements, tech):
```
domain_files = count(files in MOC's domain subtree)
linked_files = count(unique wikilinks in MOC body that resolve to domain_files)
coverage_pct = linked_files / domain_files * 100
```

### 15. thesis-essay-activity
For each `tag/thesis-*` (5 theses):
```
mention_count_30d = grep -r "tag/thesis-<slug>" across vault (last 30d files only)
mention_count_per_thesis_normalized = raw_count * thesis_weight
```
Report ranked.

### 16. archive-skill-count
```
count = ls .claude/skills/_archive/ | grep -v file | count
```
Read-only sanity; no action.

### 17. active-vs-archived-skill-ratio
```
ratio = count(active) / count(archived)
```
Report scalar; if ratio drops below 0.5 (more archived than active), flag for /vault FOLLOWUPS.

### 18. tools-script-inventory
```
for each tools/*.py:
  last_modified = git log -1 --format=%cd <file>
  loc = wc -l <file>
```
Report table; flag scripts >90 days unmodified as potentially-stale.

## Output composition

`/vault stats` composes report per `ref-output-templates.md` sec 4 schema. Body sections:

1. Executive Summary (vault-health-score, trend, calibration)
2. File / Word / Path Counts (stats 1-2)
3. Coverage Metrics (stats 3-4)
4. Freshness + Activity (stats 5-9)
5. Calibration (stat 10; Brier)
6. Graph Health (stats 11-14)
7. Domain Activity (stat 15)
8. Skill Surface (stats 16-17)
9. Tools Inventory (stat 18)
10. Continuity vs Prior Stats
11. FOLLOWUPS:skills

## Brier scoring methodology details

Each `/vault stats` run records predictions in meta.json:
- `predicted_30d_trend`: one of "improving" / "stable" / "declining"
- Derived from current state + recent activity (e.g., if 5+ CRITICAL findings in last audit, predict "declining")

Subsequent run scores prior prediction:
- "improving" -> correct if current vault_health_score > prior + 3
- "stable" -> correct if current within +/- 5 of prior
- "declining" -> correct if current < prior - 3

Brier score per prediction = (predicted_prob - actual_outcome)^2 where actual_outcome is binary {0, 1}.

Aggregate `calibration_score_30d` over rolling 3 prior reports = average correctness rate.

Calibration improving over time = signal that vault stats predictions are useful. Calibration declining = predictions are noise; treat as caution.

## FOLLOWUPS:skills triggers from stats

| Stat condition | FOLLOWUPS skill | Trigger time |
|---|---|---|
| daily-note continuity score < 0.7 | /retro candidate (session-cadence retro) | EOW |
| ref-doc coverage drift detected (MOC claim != on-disk frontmatter) | /vault repair --apply <ids> | NOW |
| held tickers without entity note | /enrich candidate (per ticker) | EOW |
| stat 17 active-vs-archived ratio < 0.5 | /vault FOLLOWUPS for skill-portfolio review | EOM |
| stat 18 tools-script >90d unmodified | /vault candidate for script audit | EOM |
| brier calibration_score_30d < 0.5 | /vault FOLLOWUPS for prediction-rule review (predictions are noise) | EOQ |
