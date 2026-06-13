---
name: tasks
risk: safe
description: Roll up open tasks across the vault by due date, tag, path, or entity via thin wrapper over obsidian-tasks plugin query syntax. CLI-primary scan of vault markdown; secondary output is a pasteable Tasks-plugin query block. Recognizes both emoji-style and Dataview-style metadata on the same line. Reads-only; never modifies checkbox state. Use when reviewing daily-note Commitments/Tasks sections, generating HOME.md Open Tasks dashboard, surfacing overdue items at session start, scoping work-in-progress to a ticker or effort, or auditing cross-file task hygiene before /retro session-end commitment carryforward.
arguments: [mode, target]
argument-hint: "overdue | today | this-week | tag <name> | path <prefix> | by-entity <TICKER> | raw <query>"
user-invocable: true
allowed-tools: Read, Bash, Glob, Grep
---

## Quality Rules
- Reads-only. Never toggle checkbox state, never edit task lines. Modifying tasks is the user's responsibility.
- Task recognition: `- [ ] text` unchecked only. `- [x]` done and `- [/]` in-progress are not open tasks. Plain `-` bullets without `[ ]` are not tasks.
- Metadata parsing: both emoji-style (due: YYYY-MM-DD, scheduled: YYYY-MM-DD, priority:highpriority:uppriority:down) and Dataview-style (`[due:: YYYY-MM-DD]`, `[scheduled:: YYYY-MM-DD]`, `[priority:: high|medium|low]`) recognized on the same line.
- Exclusion set (hardcoded): `.obsidian/`, `_archive/`, `openclaude/`, `openclaw/`, `data/`, `private/`. Never scan these.
- Grouping axis matches the filter's semantic intent: time filters group by due date; scope filters group by file path; entity mode sorts file groups by last-modified recency.
- Empty result is a valid answer: "No overdue tasks." Never pad.
- CLI render capped at 40 tasks; truncation note + narrow-filter hint if more match.

## /tasks [mode] [target]

Scan the vault for open-task lines (`- [ ]`) with optional due-date/tag/path/entity metadata, filter per mode, render results and emit a corresponding Tasks-plugin query block.

### Mode Routing

| Input | Mode | Filter |
|-------|------|--------|
| (empty) | default | overdue OR due-today |
| `overdue` | overdue | due < today, still `- [ ]` |
| `today` | today | due == today |
| `this-week` | this-week | today <= due <= today+6 |
| `tag <name>` | tag | contains `#<name>` on task line |
| `path <prefix>` | path | file path starts with `<prefix>` |
| `by-entity <TICKER>` | entity | `[[TICKER]]` wikilink OR bare `\bTICKER\b`, excluding matches inside markdown-link `[text](url)` description |
| `raw <query>` | raw | pass-through Tasks-plugin syntax; skill emits the block and skips CLI render |

### Phase 0: Scope

Glob all `*.md` files under `<VAULT_ROOT>/`. Exclude directories (hardcoded):
- `.obsidian/` -- plugin state
- `_archive/` -- dead content
- `openclaude/`, `openclaw/` -- nested repos
- `data/` -- non-content CSVs
- `private/` -- path-guarded sensitive data

Typical target set: `Atlas/`, `Calendar/`, `Efforts/`, `HOME.md`, `wiki/`, `_templates/`.

### Phase 1: Scan for Open Tasks

Grep the target set for `^- \[ \] ` (unchecked checkbox prefix). Collect file path + line number + full line text for each match.

### Phase 2: Parse Metadata

For each task line, extract:

| Field | Emoji style | Dataview style |
|-------|-------------|----------------|
| Due date | `due: YYYY-MM-DD` | `[due:: YYYY-MM-DD]` |
| Scheduled | `scheduled: YYYY-MM-DD` | `[scheduled:: YYYY-MM-DD]` |
| Priority | `priority:high` high / `priority:up` medium / `priority:down` low | `[priority:: high|medium|low]` |
| Tags | `#word` substring (markdown tag syntax) | -- |
| Text | remainder after stripping checkbox prefix and metadata | -- |

Task without due date -> undated; surfaces in scope-filtered modes (path/tag/by-entity/raw), not date-filtered modes.

### Phase 3: Apply Filter (per Mode)

Today's date from `date +%F` (Bash). Filter the parsed task set per the mode table.

**Entity match logic (for `by-entity <TICKER>`):**

```
1. Pre-transform markdown-link syntax in the task line:
     sed 's/\[\([^][]*\)\]([^)]*)/\1/g'
   Replaces `[text](url)` with just `text` -- keeps description,
   drops URL. Leaves `[[wikilinks]]` intact (different syntax:
   double-bracket, no paren pair).
2. On the transformed text, match either pattern:
     grep -E "\[\[${TICKER}\]\]|\b${TICKER}\b"
3. Case-sensitive -- UPPER tickers only. Lowercase prose like
   "useful link" or "click this link" never matches `LINK`
   regardless of context; case-sensitivity rules out the
   English-word collision class.
```

**Match verification -- test cases:**
- `- [ ] Review NVDA earnings` -> **MATCH** for `by-entity NVDA` (bare word-boundary, no markdown-link).
- `- [ ] See [[NVDA]] analysis` -> **MATCH** (wikilink preserved).
- `- [ ] Click [this link](url) for details` -> **NO MATCH** for `by-entity LINK` (lowercase "link" fails case-sensitive match).
- `- [ ] Check [NVDA earnings](url) tomorrow` -> **MATCH** for `by-entity NVDA` (URL stripped; description "NVDA earnings" retained and matched).
- `- [ ] AMD vs NVDA comparison` -> **MATCH** for both `by-entity AMD` and `by-entity NVDA` (bare word-boundary for both).
- `- [ ] Update [[NVDA]] per [recent report](url)` -> **MATCH** for `by-entity NVDA` (markdown-link reduced to "recent report"; wikilink `[[NVDA]]` survives).
- `- [ ] See [LINK docs](url)` -> **MATCH** for `by-entity LINK` (description "LINK docs" retained; all-caps LINK is a legitimate reference).

### Phase 4: Grouping and Sort

| Mode | Group by | Sort within group | File-group order |
|------|----------|-------------------|------------------|
| default / overdue / today / this-week | due date (Overdue -> Today -> +1 -> +2 -> ...) | file path alphabetical | -- |
| path / tag | file path | line number (natural document order) | path alphabetical |
| by-entity | file path | line number | last-modified recency (most recent first) |
| raw | -- (flat) | user-supplied sort, else due ascending | -- |

### Phase 5: Render + Emit Query Block

**CLI render (primary output):**

```
## Open Tasks -- [mode description]
[N] tasks across [M] files.

### [group header 1]
- [ ] [text] due: [due] [#tag] [priority] -- `[file-path:line]`
- [ ] ...

### [group header 2]
...

[If truncated: "Showing 40 of [N]. Narrow with a tighter filter."]
```

Empty result: `## Open Tasks -- [mode description]\n\nNone.` Stop; no query-block appendix needed.

**Query block (secondary output, emitted after CLI render -- or as primary output in `raw` mode):**

````
## Equivalent Tasks-plugin Query

```tasks
not done
<filter-specific lines>
<sort / group / limit lines>
```
````

For `raw` mode: skip CLI render entirely; echo user's query verbatim inside the block.

### Phase 6: No Knowledge Base Updates

Reads-only. No writes to `wiki/hot.md`, daily note, `Calendar/decisions/sessions-log.md`, or any vault file.

## Tasks-plugin Query Reference (inline)

For constructing `raw` queries and understanding the emitted block:

```
not done                       # status filter -- unchecked only
due before today               # overdue
due on today                   # due today
due in 7 days                  # upcoming
scheduled before/on/after ...
path includes <prefix>
path does not include <prefix>
tags include #<name>
priority is high|medium|low|none
description includes <text>
sort by due|priority|path|status
group by path|due|tag|status
limit N
```

Boolean: `AND` (implicit for multiple filter lines), `OR`, `NOT`, parentheses.

Full reference: github.com/obsidian-tasks-group/obsidian-tasks

## Example Invocations

- `/tasks` -- default: overdue + due today
- `/tasks this-week` -- due within 7 days
- `/tasks by-entity NVDA` -- tasks mentioning NVDA (wikilink or bare word-boundary)
- `/tasks path Efforts/career-search` -- all open career tasks
- `/tasks tag urgent` -- `#urgent` tagged tasks
- `/tasks raw "not done\ndue before today\npriority is high"` -- custom pass-through

## Quality Rules (reprise)

- Reads-only.
- Explicit `- [ ]` checkbox only; plain bullets are not tasks.
- Both emoji-style and Dataview-style metadata recognized.
- Exclusion set hardcoded: `.obsidian/`, `_archive/`, `openclaude/`, `openclaw/`, `data/`, `private/`.
- Grouping matches filter's semantic axis (time / scope / entity-recency).
- Empty result: say so; don't pad.
- Cap CLI render at 40 tasks; truncate with hint.
