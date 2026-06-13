---
name: create-skill
risk: safe
description: Create a new custom skill with correct folder structure, SKILL.md format, and reference document integration. Use when a recurring 3+ step workflow emerges that warrants automation, when an existing skill's description fails to trigger reliably, when a new domain enters the vault and needs a skill scaffold, or when consolidating ad-hoc patterns into a reusable progressive-disclosure structure.
arguments: [skill_name, description]
allowed-tools: [Write, Read, Bash, Glob]
user-invocable: true
---

## Quality Rules
- Every skill must have YAML frontmatter: name, description, arguments, argument-hint, allowed-tools, user-invocable.
- Every skill should have a Quality Rules section (even 3-5 rules).
- Output locations must be specified explicitly.
- Phase 0 must reference actual vault files that exist.
- Follow the patterns established by /health (GRADE evidence), /brief (BLUF + Counter), or /invest (evidence grades) as appropriate for the domain.

## Create a New Skill

Create a new skill called "$1" with description: "$2"

### Steps

1. Parse the skill name from the first argument. Lowercase, hyphens for spaces. This is the folder name.

2. Determine the knowledge-area from the description:
   - Investing/financial keywords -> knowledge-area: investing
   - Career/job/resume keywords -> knowledge-area: career
   - Golf/swing keywords -> knowledge-area: golf
   - Health/supplement keywords -> knowledge-area: supplements
   - Tech/code keywords -> knowledge-area: tech
   - General/other -> knowledge-area: general

3. Check for available reference documents:
   ```
   ls <VAULT_ROOT>/Atlas/sources/*/ref-*.md 2>/dev/null
   ```
   Also read <VAULT_ROOT>/Atlas\_MOCs\knowledge-moc.md to understand the full knowledge base layout.

4. Create the directory: <VAULT_ROOT>/.claude\skills\<name>\

5. Create SKILL.md with this structure (canonical frontmatter per CLAUDE.md
   sec "Frontmatter schema" + Claude Code skill-author fields):

```
---
name: <skill-name>
description: <description -- be PUSHY per ref-claude-code-mastery sec 7;
  include trigger phrases; under 1024 chars per Claude Code spec, ideally 500-1500>
arguments: [query]
argument-hint: "<concrete example invocations>"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep]
effort: max
user-invocable: true
categories: [meta]
type: skill
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
status: active
tags:
  - topic/<domain>
related:
  - "[[knowledge-moc]]"
---

## /<skill-name> <arguments>

### Phase 0: Context and Reference Loading

Step 1: Read environment:
- echo $OPENAI_MODEL
- echo $OLLAMA_CONTEXT_LENGTH

Step 2: Load reference documents (before web searches):
- <VAULT_ROOT>/Atlas\_MOCs\<knowledge-area>-moc.md (knowledge-area routing)
- <VAULT_ROOT>/Atlas\sources\<knowledge-area>\ref-*.md (relevant reference docs)
- <VAULT_ROOT>/Atlas\sources\meta\ref-research-methodology.md (if doing web research)

Step 3: Load personal context (if applicable):
- <VAULT_ROOT>/private\profile.md (if personalized output needed)
- Domain-specific personal files as needed

NOTE: Total reference doc loading should not exceed ~15,000 words (~20,000 tokens).
Reference docs use the ref- prefix: Atlas/sources/{knowledge-area}/ref-{topic}.md
Discover available refs: ls <VAULT_ROOT>/Atlas/sources/*/ref-*.md

### Phase 1: Research
<web searches, data gathering -- reference docs provide baseline so searches focus on what is new>

### Phase 2: Analysis
<synthesis, calculations, comparisons -- use reference doc context as baseline>

### Phase 3: Output
Write to the appropriate ACE directory based on what the skill produces:
- Timeless concepts -> `<VAULT_ROOT>/Atlas\concepts\<knowledge-area>\<filename>.md`
- External references -> `<VAULT_ROOT>/Atlas\sources\<knowledge-area>\ref-<topic>.md`
- Time-anchored records -> `<VAULT_ROOT>/Calendar\{daily,weekly,decisions}\<filename>.md`
- Operational deadline-bound work -> `<VAULT_ROOT>/Efforts\<slug>\<filename>.md`
- Agent research/synthesis/entities -> `<VAULT_ROOT>/wiki\<subdir>\<filename>.md`

All output files MUST start with YAML frontmatter following the vault schema:
```yaml
---
categories: [<axis>]
type: <subtype>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
status: active
tags: []
related: []
---
```
At the end of each output file, add: `Related: [[<knowledge-area>-moc]] | [[relevant ref docs]]`

### Phase 4: Knowledge Base Updates
- Update relevant files in the appropriate ACE directory (Atlas/concepts/, Atlas/sources/, Efforts/, wiki/)
- Append to <VAULT_ROOT>/Calendar\decisions\sessions-log.md via Bash echo (not Edit tool)
- If reference doc insights were gained, note for future ref doc updates
- If a needed reference doc does not exist, note in session log: "REF DOC NEEDED: {knowledge-area}/{topic}"

### Quality Rules
- Follow research and report standards from CLAUDE.md
- Cross-reference claims across multiple sources
- Include confidence ratings on major claims
- ASCII only in all output

### Examples
<example type="good">
[Add 1-2 examples of good output format for this skill]
</example>
<example type="bad">
[Add 1-2 examples of what to avoid]
</example>
```

6. Identify what reference documents would improve this skill:
   - List reference docs that should exist but do not
   - Note which existing ref docs should be loaded
   - Add comments in the SKILL.md about future reference doc needs

7. Tell the user:
   "Skill created at <VAULT_ROOT>/.claude\skills\<name>\SKILL.md

   Reference documents that would improve this skill:
   - <list any identified ref doc needs>

   To build reference docs, run a Claude Opus deep research session and save output to Atlas/sources/<knowledge-area>/ref-<topic>.md

   Restart your Claude Code session to load the new skill, then use /<name> to invoke."
