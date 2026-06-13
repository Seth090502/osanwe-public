---
name: golf
risk: safe
description: Golf practice plans, swing research, and drill recommendations. Use post-TrackMan-session for fault diagnosis, weekly for practice planning, before equipment changes, after a noticeable swing-feel shift, or when reviewing tour-vs-personal launch-monitor benchmarks. Reads ref-biomechanics + ref-common-faults; writes to Efforts/golf-practice/.
arguments: [topic]
argument-hint: "Any golf topic -- e.g., 'low point control', 'driver distance', 'putting drill'"
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, WebFetch, WebSearch
---

## Quality Rules
- Every drill recommendation must cite a biomechanical principle from ref-biomechanics.md or ref-common-faults.md.
- TrackMan data is authoritative. When the user provides numbers, use them -- don't override with generic advice.
- Practice plans follow interleaved/random practice principles (contextual interference effect), not block practice.
- All swing corrections must trace back to the fault cascade: physical limitation -> primary fault -> ball flight symptom.
- Cross-reference health domain: neuroplasticity supplements (Bacopa, Lion's Mane) support motor learning. Note recovery phase when relevant.

## Execution Rules
- Follow all steps as specified. Do not skip or combine steps.
- Read all referenced files before proceeding with the task.
- Write output files to the specified paths.

## Search Method
Use the Web Search tool for all web searches.
Do not fetch URLs from blocked domains (see CLAUDE.md).

## Golf Research & Practice Skill

Topic: the topic provided by the user after the /golf command.

### Phase 0: Context and Reference Loading

Load knowledge base files BEFORE web searches for context priming:
1. <VAULT_ROOT>/Atlas\concepts\golf\equipment.md (current bag, fitting data, swing speeds)
2. <VAULT_ROOT>/Efforts\golf-practice\swing-notes.md (current focus areas, known issues, TrackMan data)
3. <VAULT_ROOT>/Atlas\concepts\golf\drills-library.md (drills already researched -- avoid duplicates)
4. <VAULT_ROOT>/Efforts\golf-practice\progress-log.md (recent session results)
5. <VAULT_ROOT>/Atlas\sources\golf\ref-biomechanics.md (core biomechanics principles)
6. <VAULT_ROOT>/Atlas\sources\golf\ref-common-faults.md (fault diagnosis and correction reference)

### Phase 1: Research

1. Search for instructional content, biomechanics research, coaching advice on the topic
2. Fetch 5-8 quality sources (prioritize PGA instructors, biomechanics researchers, reputable golf media)
3. Cross-reference findings with the knowledge base context loaded in Phase 0
4. Synthesize into actionable practice plan personalized to the user's swing profile from swing-notes.md

### Phase 1.5: Progress Check

Check <VAULT_ROOT>/Efforts\golf-practice\progress-log.md for prior sessions on this topic.
If found: note improvement trajectory, persistent issues, what changed since last session.
If this is a recurring topic, frame the drills as progressive overload -- building on prior work, not starting fresh.

### Phase 2: Output

Create a file at <VAULT_ROOT>/Efforts\golf-practice\research\{topic-slug}.md with YAML frontmatter first:

```yaml
---
categories: [efforts]
type: output
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
status: active
tags: []
related:
  - "[[drills-library]]"
  - "[[ref-biomechanics]]"
  - "[[swing-notes]]"
  - "[[golf-moc]]"
---
```

Then the content:

1. **Topic and Date**
2. **Summary** -- what this issue is and why it happens (biomechanics)
3. **Diagnosis** -- common causes, how to identify which applies
4. **Drills** -- 3-5 specific drills, each with:
   - Name
   - Setup (stance, club, ball position)
   - Execution (what to do, step by step)
   - Reps/sets recommendation
   - Focus cues (1-2 swing thoughts)
   - What success looks/feels like
5. **Practice Plan** -- structured session (warm-up, drills, cool-down with timing)
6. **Common Mistakes** -- what to avoid
7. **Sources**

At the end of the output file, add:
```
Related: [[golf-moc]] | [[drills-library]] | [[progress-log]] | [[ref-biomechanics]]
```

### Phase 3: Knowledge Base Updates

After writing the research output:
1. If new drills were recommended, append to <VAULT_ROOT>/Atlas\concepts\golf\drills-library.md. Also bump the `updated` field in the file's YAML frontmatter.
2. If swing insights were gained, note in <VAULT_ROOT>/Efforts\golf-practice\swing-notes.md
3. Append to <VAULT_ROOT>/Calendar\decisions\sessions-log.md with wikilinks to the output file: `[[{topic-slug}]]`

### Quality Rules
- Prioritize PGA-certified instructors and biomechanics researchers over generic golf content
- Cross-reference drill recommendations with existing drills-library.md to avoid duplicates
- Personalize all recommendations to the user's equipment and swing speed from the KB files
- Include confidence levels on swing diagnosis

### Example
User: /golf low point control
Output: <VAULT_ROOT>/Efforts\golf-practice\research\low-point-control.md
