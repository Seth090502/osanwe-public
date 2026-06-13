#!/usr/bin/env python3
"""
consolidator.py -- Pattern-consolidation engine for the /consolidate skill.

Mines the vault's accreted operational record -- sessions-log, decision-log,
daily notes, retros (methodology learnings), and the telemetry sinks -- for
recurring patterns above tuned thresholds, then renders durable playbooks plus
a compact hot.md digest. Turns episodic session memory into reusable doctrine.

Architecture (modeled on tools/telemetry_analyzer.py):
  - Markdown/JSONL sources (existing, unchanged): append-only truth.
  - Consolidator class: ingest_* -> identify_patterns -> render_*.
  - No SQLite; computation is in-memory and deterministic (idempotent renders).

Thresholds (tunable constants below):
  - decision tag (domain) recurrence   >= 3 decisions
  - telemetry failure cluster count     >= 5 failures in one (tool, error_class)
  - retro theme (distinct sessions)      >= 3 sessions sharing a theme token
  - skill/agent failure_rate             >= 0.30 (min 3 paired-or-failed events)

CLI:
  python tools/consolidator.py                         # default 30-day window, write playbooks
  python tools/consolidator.py --since 2026-04-01      # explicit window start (ISO)
  python tools/consolidator.py --max-playbooks 8       # cap playbooks written
  python tools/consolidator.py --dry-run               # compute + print, write nothing

Module surface:
  from consolidator import Consolidator
  c = Consolidator(since="2026-04-01")
  report = c.run(max_playbooks=8, dry_run=True)
"""
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
SESSIONS_LOG = VAULT_ROOT / "Calendar" / "decisions" / "sessions-log.md"
DECISION_LOG = VAULT_ROOT / "Calendar" / "decisions" / "decision-log.md"
DAILY_DIR = VAULT_ROOT / "Calendar" / "daily"
STATE_DIR = VAULT_ROOT / ".claude" / "state"
PLAYBOOK_DIR = VAULT_ROOT / "wiki" / "playbooks"

# Thresholds
DECISION_TAG_MIN = 3
TELEMETRY_CLUSTER_MIN = 5
RETRO_THEME_MIN = 3
SKILL_FAILURE_RATE_MIN = 0.30
SKILL_FAILURE_MIN_EVENTS = 3
DIGEST_MAX_BYTES = 4096

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
ROW_DATE_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|")
TOKEN_RE = re.compile(r"[a-z][a-z0-9-]{4,}")

# Boilerplate + generic stopwords -- keep domain-meaningful tokens, kill noise.
STOPWORDS = {
    # generic english
    "the", "and", "for", "with", "that", "this", "from", "was", "were", "has",
    "have", "had", "not", "but", "all", "any", "are", "its", "via", "per",
    "into", "over", "than", "then", "when", "where", "which", "while", "also",
    "each", "both", "more", "most", "such", "only", "other", "same", "some",
    "after", "before", "above", "below", "between", "across", "about", "their",
    "there", "these", "those", "being", "until", "without", "within", "under",
    # vault / session boilerplate that appears in nearly every row
    "model", "claude", "opus", "sonnet", "context", "commit", "commits",
    "created", "modified", "source", "sources", "count", "phase", "phases",
    "invoked", "ratified", "active", "pending", "briefing", "retro", "brief",
    "vault", "score", "calendar", "daily", "https", "http", "github", "files",
    "file", "entity", "entities", "update", "updated", "section", "sections",
    "skill", "skills", "decision", "decisions", "session", "sessions", "domain",
    "outcome", "topic", "wikilinks", "wikilink", "related", "linkback",
    "appended", "append", "trigger", "candidate", "follow", "followup",
    "followups", "learnings", "insights", "methodology", "pattern", "patterns",
    "analysis", "analyses", "current", "close", "today", "tonight", "within",
    "first", "baseline", "verdict", "framework", "rationale", "status",
}


def _slugify(text: str) -> str:
    """Lowercase ASCII slug safe for a filename stem."""
    s = text.lower().strip()
    s = s.replace("/", "-").replace("::", "-").replace("_", "-")
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "pattern"


def _derive_error_class(error_text: str) -> str:
    """Map raw error text to a stable error_class via prefix patterns."""
    if not error_text:
        return "empty_error"
    m = re.match(r"^Exit code (\d+).*?\b(\d{3})\b", error_text, re.DOTALL)
    if m:
        return f"Exit_code_{m.group(1)}_HTTP_{m.group(2)}"
    m = re.match(r"^Exit code (\d+)", error_text, re.DOTALL)
    if m:
        return f"Exit_code_{m.group(1)}"
    if error_text.startswith("old_string not found"):
        return "Edit_old_string_not_found"
    m = re.match(r"^HTTP (\d+)", error_text)
    if m:
        return f"HTTP_{m.group(1)}"
    return "unclassified"


def _is_fixture(rec: dict) -> bool:
    """Light synthetic-record filter (cwd empty/single-char or test markers)."""
    cwd = rec.get("cwd", "") or ""
    if len(cwd) <= 1:
        return True
    tuid = rec.get("tool_use_id", "") or ""
    if tuid in {"unknown", "epsilon", "theta", "alpha_test"}:
        return True
    if re.match(r"^toolu_(test|sweep|real)", tuid):
        return True
    return False


@dataclass
class Pattern:
    pattern_type: str            # decision_tag | telemetry_cluster | retro_theme | skill_failure_rate
    key: str                     # human label
    count: int                   # occurrences
    metric: float                # rate for skill_failure_rate, else == count
    evidence: list = field(default_factory=list)   # short strings
    threshold_desc: str = ""

    @property
    def slug(self) -> str:
        return _slugify(self.key)


@dataclass
class ConsolidationReport:
    generated_at: str = ""
    since: str = ""
    n_sessions: int = 0
    n_decisions: int = 0
    n_daily: int = 0
    n_failures: int = 0
    n_subagent_events: int = 0
    patterns: list = field(default_factory=list)
    written: list = field(default_factory=list)       # playbook paths written
    digest: str = ""


class Consolidator:
    """Reads vault operational records; identifies recurring patterns; renders playbooks."""

    def __init__(self, vault_root: Path = VAULT_ROOT, since: str = None,
                 state_dir: Path = STATE_DIR):
        self.vault_root = Path(vault_root)
        self.since = since  # ISO date string or None
        self.state_dir = Path(state_dir)
        self._sessions_path = self.vault_root / "Calendar" / "decisions" / "sessions-log.md"
        self._decision_path = self.vault_root / "Calendar" / "decisions" / "decision-log.md"
        self._daily_dir = self.vault_root / "Calendar" / "daily"
        self._playbook_dir = self.vault_root / "wiki" / "playbooks"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _within_since(self, date_str: str) -> bool:
        if not self.since:
            return True
        if not date_str:
            return True  # undated rows are kept (cannot filter)
        return date_str >= self.since

    @staticmethod
    def _split_row(line: str) -> list:
        """Split a markdown table row on unescaped pipes; trim cells."""
        cells = line.strip().strip("|").split("|")
        return [c.strip() for c in cells]

    @staticmethod
    def _tokenize(text: str) -> set:
        """Significant lowercase tokens (stopword-filtered, len>=5)."""
        toks = set()
        for m in TOKEN_RE.finditer(text.lower()):
            t = m.group(0).strip("-")
            if len(t) < 5 or t in STOPWORDS or t.isdigit():
                continue
            toks.add(t)
        return toks

    # ------------------------------------------------------------------
    # Ingest layer
    # ------------------------------------------------------------------
    def ingest_sessions(self, path: Path = None) -> list:
        """Parse sessions-log.md table rows -> [{date, topic, outcome, domain}]."""
        path = Path(path) if path else self._sessions_path
        out = []
        if not path.exists():
            return out
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return out
        for line in lines:
            if not ROW_DATE_RE.match(line):
                continue
            cells = self._split_row(line)
            if len(cells) < 3:
                continue
            date = cells[0]
            topic = cells[1] if len(cells) > 1 else ""
            outcome = cells[2] if len(cells) > 2 else ""
            if not self._within_since(date):
                continue
            dm = re.search(r"Domain[:\s]+([A-Za-z0-9 /+-]+)", outcome)
            domain = dm.group(1).strip().rstrip(".") if dm else ""
            out.append({"date": date, "topic": topic, "outcome": outcome,
                        "domain": domain})
        return out

    def ingest_decisions(self, path: Path = None) -> list:
        """Parse decision-log.md table rows -> [{date, domain, decision, status}]."""
        path = Path(path) if path else self._decision_path
        out = []
        if not path.exists():
            return out
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return out
        for line in lines:
            if not ROW_DATE_RE.match(line):
                continue
            cells = self._split_row(line)
            if len(cells) < 3:
                continue
            date = cells[0]
            if not self._within_since(date):
                continue
            domain = cells[1] if len(cells) > 1 else ""
            decision = cells[2] if len(cells) > 2 else ""
            status = cells[-1] if len(cells) >= 5 else ""
            out.append({"date": date, "domain": domain, "decision": decision,
                        "status": status})
        return out

    def ingest_daily_notes(self, daily_dir: Path = None) -> list:
        """Parse daily notes -> [{date, insights_text, decisions_text}]."""
        daily_dir = Path(daily_dir) if daily_dir else self._daily_dir
        out = []
        if not daily_dir.exists():
            return out
        for fp in sorted(daily_dir.glob("*.md")):
            dm = DATE_RE.search(fp.name)
            date = dm.group(1) if dm else ""
            if not self._within_since(date):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            insights = self._extract_section(text, "Insights")
            decisions = self._extract_section(text, "Decisions")
            out.append({"date": date, "insights_text": insights,
                        "decisions_text": decisions})
        return out

    @staticmethod
    def _extract_section(text: str, header: str) -> str:
        """Return body text under a `## <header>` until the next `## ` header."""
        m = re.search(r"^##\s+" + re.escape(header) + r"\b(.*?)(?=^##\s|\Z)",
                      text, re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    def ingest_retros(self, path: Path = None) -> list:
        """Extract methodology-learnings text per session -> [{date, learnings}]."""
        path = Path(path) if path else self._sessions_path
        out = []
        for s in self.ingest_sessions(path):
            outcome = s["outcome"]
            m = re.search(
                r"Methodology learnings.*?:(.*?)(?:Follow-ups|Insights|Session boundary|Confidence|$)",
                outcome, re.DOTALL | re.IGNORECASE)
            learnings = m.group(1).strip() if m else outcome
            out.append({"date": s["date"], "learnings": learnings})
        return out

    def ingest_telemetry(self, state_dir: Path = None) -> dict:
        """Read failures + subagent JSONL -> {failure_clusters, agent_outcomes, counts}."""
        state_dir = Path(state_dir) if state_dir else self.state_dir
        clusters = {}            # (tool, error_class) -> count
        agent_events = {}        # tool_use_id -> {agent_type, has_start, has_stop}
        n_failures = 0
        n_subagent = 0

        for fp in sorted(state_dir.glob("failures-*.jsonl")):
            dm = DATE_RE.search(fp.name)
            if dm and not self._within_since(dm.group(1)):
                continue
            for rec in self._read_jsonl(fp):
                if _is_fixture(rec):
                    continue
                n_failures += 1
                tool = rec.get("tool", "") or "(empty)"
                ec = _derive_error_class(rec.get("error", "") or "")
                clusters[(tool, ec)] = clusters.get((tool, ec), 0) + 1

        for fp in sorted(state_dir.glob("subagent-telemetry-*.jsonl")):
            dm = DATE_RE.search(fp.name)
            if dm and not self._within_since(dm.group(1)):
                continue
            for rec in self._read_jsonl(fp):
                if _is_fixture(rec):
                    continue
                n_subagent += 1
                tuid = rec.get("tool_use_id", "") or rec.get("session_id", "")
                if not tuid:
                    continue
                slot = agent_events.setdefault(
                    tuid, {"agent_type": "", "has_start": False, "has_stop": False})
                ev = rec.get("event", "")
                if ev == "start":
                    slot["has_start"] = True
                elif ev == "stop":
                    slot["has_stop"] = True
                at = rec.get("agent_type", "") or ""
                if at and not slot["agent_type"]:
                    slot["agent_type"] = at

        # Roll up per agent_type
        agent_outcomes = {}      # agent_type -> {paired, failed, total}
        for tuid, slot in agent_events.items():
            at = slot["agent_type"] or "(unknown)"
            o = agent_outcomes.setdefault(at, {"paired": 0, "failed": 0, "total": 0})
            o["total"] += 1
            if slot["has_start"] and slot["has_stop"]:
                o["paired"] += 1
            else:
                o["failed"] += 1

        failure_clusters = sorted(
            ({"tool": k[0], "error_class": k[1], "count": v}
             for k, v in clusters.items()),
            key=lambda d: d["count"], reverse=True)
        return {"failure_clusters": failure_clusters,
                "agent_outcomes": agent_outcomes,
                "n_failures": n_failures, "n_subagent": n_subagent}

    @staticmethod
    def _read_jsonl(fp: Path):
        try:
            with fp.open("r", encoding="utf-8", errors="ignore") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        yield json.loads(raw)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except OSError:
            return

    # ------------------------------------------------------------------
    # Pattern identification
    # ------------------------------------------------------------------
    def identify_patterns(self) -> list:
        """Apply the four thresholds across all ingested sources -> [Pattern]."""
        patterns = []
        decisions = self.ingest_decisions()
        retros = self.ingest_retros()
        daily = self.ingest_daily_notes()
        tel = self.ingest_telemetry()

        # 1. decision_tag: group decisions by normalized domain, >= DECISION_TAG_MIN
        dom_counts = {}
        dom_evidence = {}
        for d in decisions:
            for dom in self._norm_domains(d["domain"]):
                dom_counts[dom] = dom_counts.get(dom, 0) + 1
                dom_evidence.setdefault(dom, [])
                if len(dom_evidence[dom]) < 5:
                    snippet = d["decision"][:140].strip()
                    dom_evidence[dom].append(f"{d['date']}: {snippet}")
        for dom, cnt in dom_counts.items():
            if cnt >= DECISION_TAG_MIN:
                patterns.append(Pattern(
                    pattern_type="decision_tag", key=f"{dom} decisions",
                    count=cnt, metric=float(cnt), evidence=dom_evidence[dom],
                    threshold_desc=f">= {DECISION_TAG_MIN} ratified decisions in domain"))

        # 2. telemetry_cluster: (tool, error_class) >= TELEMETRY_CLUSTER_MIN
        for c in tel["failure_clusters"]:
            if c["count"] >= TELEMETRY_CLUSTER_MIN:
                key = f"{c['tool']}::{c['error_class']}"
                patterns.append(Pattern(
                    pattern_type="telemetry_cluster", key=key, count=c["count"],
                    metric=float(c["count"]),
                    evidence=[f"{c['count']} failures clustered on {key}"],
                    threshold_desc=f">= {TELEMETRY_CLUSTER_MIN} failures in cluster"))

        # 3. retro_theme: theme token across >= RETRO_THEME_MIN distinct sessions
        theme_sessions = {}      # token -> set(dates)
        theme_examples = {}      # token -> [snippets]
        corpus = [(r["date"], r["learnings"]) for r in retros]
        corpus += [(d["date"], d["insights_text"]) for d in daily]
        for date, text in corpus:
            if not text:
                continue
            toks = self._tokenize(text)
            for t in toks:
                theme_sessions.setdefault(t, set()).add(date or "undated")
                if len(theme_examples.setdefault(t, [])) < 5:
                    theme_examples[t].append(f"{date}: theme '{t}'")
        for tok, dates in theme_sessions.items():
            if len(dates) >= RETRO_THEME_MIN:
                patterns.append(Pattern(
                    pattern_type="retro_theme", key=f"{tok} (recurring theme)",
                    count=len(dates), metric=float(len(dates)),
                    evidence=theme_examples[tok],
                    threshold_desc=f">= {RETRO_THEME_MIN} distinct sessions share theme"))

        # 4. skill_failure_rate: agent_type failed/total >= SKILL_FAILURE_RATE_MIN
        for at, o in tel["agent_outcomes"].items():
            total = o["total"]
            if total < SKILL_FAILURE_MIN_EVENTS:
                continue
            rate = o["failed"] / total if total else 0.0
            if rate >= SKILL_FAILURE_RATE_MIN:
                patterns.append(Pattern(
                    pattern_type="skill_failure_rate",
                    key=f"{at} subagent failure rate", count=o["failed"],
                    metric=round(rate, 3),
                    evidence=[f"{o['failed']}/{total} {at} dispatches unpaired "
                              f"(orphan/hanging) = {round(rate*100,1)}% failure rate"],
                    threshold_desc=f">= {int(SKILL_FAILURE_RATE_MIN*100)}% failure rate (min {SKILL_FAILURE_MIN_EVENTS} events)"))

        # Rank: higher-signal types first, then by count desc
        type_rank = {"telemetry_cluster": 0, "skill_failure_rate": 1,
                     "decision_tag": 2, "retro_theme": 3}
        patterns.sort(key=lambda p: (type_rank.get(p.pattern_type, 9), -p.count))
        return patterns

    @staticmethod
    def _norm_domains(raw: str) -> list:
        """Normalize a Domain cell into one or more canonical domain slugs."""
        if not raw:
            return []
        parts = re.split(r"[+/]| and ", raw.lower())
        norm = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if "skill" in p or "meta" in p or "infra" in p:
                norm.append("meta-skill-infrastructure")
            elif "invest" in p:
                norm.append("investing")
            elif "career" in p:
                norm.append("career")
            elif "health" in p:
                norm.append("health")
            elif "golf" in p:
                norm.append("golf")
            else:
                norm.append(_slugify(p))
        # dedupe, preserve order
        seen, out = set(), []
        for n in norm:
            if n not in seen:
                seen.add(n)
                out.append(n)
        return out

    # ------------------------------------------------------------------
    # Render layer
    # ------------------------------------------------------------------
    def render_playbook(self, pattern: Pattern, sibling_slugs: list = None,
                        today: str = None) -> str:
        """Render one playbook markdown string (ASCII-clean; canonical frontmatter)."""
        today = today or datetime.now().date().isoformat()
        sibling_slugs = sibling_slugs or []
        title = pattern.key.replace("::", " ").replace("-", " ").strip()
        title = title[:1].upper() + title[1:]

        lines = []
        lines.append("---")
        lines.append("categories: [wiki]")
        lines.append("type: synthesis")
        lines.append("status: active")
        lines.append(f"created: {today}")
        lines.append(f"updated: {today}")
        lines.append("tags: [topic/consolidation, topic/playbook]")
        lines.append("related:")
        lines.append('  - "[[hot]]"')
        lines.append("---")
        lines.append("")
        lines.append(f"# {title} Playbook")
        lines.append("")
        lines.append("## Pattern")
        lines.append(self._pattern_prose(pattern))
        lines.append("")
        lines.append("## Evidence")
        for ev in pattern.evidence:
            lines.append(f"- {self._ascii(ev)}")
        lines.append(f"- Threshold cleared: {pattern.threshold_desc} (observed {pattern.count}).")
        lines.append("")
        lines.append("## Recommendation")
        lines.append(self._pattern_recommendation(pattern))
        lines.append("")
        lines.append("## Related")
        lines.append("- [[hot]] -- session cache; this playbook is surfaced in the consolidation digest")
        for sl in sibling_slugs[:3]:
            lines.append(f"- [[{sl}-playbook]]")
        lines.append("")
        return "\n".join(lines)

    def _pattern_prose(self, p: Pattern) -> str:
        if p.pattern_type == "decision_tag":
            return (f"The vault has ratified {p.count} decisions in the "
                    f"**{p.key.replace(' decisions','')}** domain. A recurring "
                    f"decision cluster of this size is durable doctrine, not "
                    f"episodic choice -- worth codifying so future decisions in "
                    f"this domain inherit the accumulated reasoning.")
        if p.pattern_type == "telemetry_cluster":
            return (f"The tool/error cluster **{p.key}** fired {p.count} times in "
                    f"the window. A repeated failure signature this frequent is a "
                    f"systemic friction point, not noise.")
        if p.pattern_type == "skill_failure_rate":
            return (f"The subagent type **{p.key.replace(' subagent failure rate','')}** "
                    f"shows a {round(p.metric*100,1)}% unpaired (orphan/hanging) rate. "
                    f"A failure rate this high signals a dispatch or lifecycle-hook "
                    f"problem worth a targeted fix.")
        # retro_theme
        tok = p.key.replace(' (recurring theme)', '')
        return (f"The theme **'{tok}'** recurs across {p.count} distinct sessions' "
                f"methodology learnings and insights. Cross-session recurrence at "
                f"this level marks a stable working pattern worth promoting from "
                f"scattered notes into a single reference.")

    def _pattern_recommendation(self, p: Pattern) -> str:
        if p.pattern_type == "decision_tag":
            return ("Review the listed decisions for a shared invariant; promote "
                    "the strongest into ref-doc doctrine and add a review trigger. "
                    "Run /challenge on any decision whose confidence has drifted.")
        if p.pattern_type == "telemetry_cluster":
            return ("Inspect the raw failure records for this cluster, fix the "
                    "root cause (tool usage, hook, or env), and re-run /telemetry "
                    "to confirm the cluster clears.")
        if p.pattern_type == "skill_failure_rate":
            return ("Inspect transcripts for this subagent type; verify the "
                    "SubagentStop hook fires and dispatch payloads are well-formed. "
                    "Re-run /telemetry --rebuild after any hook fix.")
        return ("Consolidate the scattered mentions into the relevant ref-doc or "
                "concept note, then link this playbook from the domain MOC so the "
                "theme is discoverable rather than re-derived each session.")

    @staticmethod
    def _ascii(text: str) -> str:
        """Best-effort ASCII coercion for evidence snippets."""
        repl = {"--": "--", "-": "-", "'": "'", "'": "'",
                '"': '"', '"': '"', "->": "->", "...": "...",
                "<=": "<=", ">=": ">=", " ": " "}
        for k, v in repl.items():
            text = text.replace(k, v)
        return "".join(c if ord(c) < 128 else "?" for c in text)

    def render_hot_md_digest(self, patterns: list, slugs: list = None,
                             today: str = None) -> str:
        """Render a compact (<4KB) dated digest block linking each playbook."""
        today = today or datetime.now().date().isoformat()
        slugs = slugs or [p.slug for p in patterns]
        lines = []
        lines.append(f"### Consolidation Digest -- {today}")
        since_txt = self.since or "all-time"
        lines.append(f"{len(patterns)} recurring patterns consolidated into playbooks "
                     f"(window since {since_txt}):")
        for p, sl in zip(patterns, slugs):
            if p.pattern_type == "skill_failure_rate":
                metric = f"{round(p.metric*100,1)}% fail"
            else:
                metric = f"{p.count}x"
            lines.append(f"- [[{sl}-playbook]] -- {self._ascii(p.key)} ({metric}, {p.pattern_type})")
        lines.append("Generated by /consolidate (tools/consolidator.py).")
        digest = "\n".join(lines)
        # Enforce the <4KB budget: trim trailing playbook lines if needed.
        while len(digest.encode("utf-8")) > DIGEST_MAX_BYTES and len(lines) > 3:
            lines.pop(-2)  # drop a playbook line, keep the trailing generator note
            digest = "\n".join(lines)
        return digest

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run(self, max_playbooks: int = 8, dry_run: bool = False) -> ConsolidationReport:
        """Full pipeline: ingest -> identify -> render -> (optionally) write."""
        report = ConsolidationReport(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            since=self.since or "all-time")
        sessions = self.ingest_sessions()
        decisions = self.ingest_decisions()
        daily = self.ingest_daily_notes()
        tel = self.ingest_telemetry()
        report.n_sessions = len(sessions)
        report.n_decisions = len(decisions)
        report.n_daily = len(daily)
        report.n_failures = tel["n_failures"]
        report.n_subagent_events = tel["n_subagent"]

        patterns = self.identify_patterns()[:max_playbooks]
        report.patterns = patterns
        slugs = self._unique_slugs(patterns)
        report.digest = self.render_hot_md_digest(patterns, slugs)

        if not dry_run and patterns:
            self._playbook_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().date().isoformat()
            for p, sl in zip(patterns, slugs):
                siblings = [s for s in slugs if s != sl]
                content = self.render_playbook(p, sibling_slugs=siblings, today=today)
                out_path = self._playbook_dir / f"{sl}-playbook.md"
                out_path.write_text(content, encoding="utf-8")
                report.written.append(str(out_path))
        return report

    @staticmethod
    def _unique_slugs(patterns: list) -> list:
        """Deterministic, collision-free slugs for playbook filenames."""
        seen, out = {}, []
        for p in patterns:
            base = p.slug
            if base in seen:
                seen[base] += 1
                out.append(f"{base}-{seen[base]}")
            else:
                seen[base] = 0
                out.append(base)
        return out


def cli():
    ap = argparse.ArgumentParser(description="Vault pattern-consolidation engine")
    ap.add_argument("--since", type=str, default=None,
                    help="ISO date window start (default: 30 days ago)")
    ap.add_argument("--max-playbooks", type=int, default=8,
                    help="Cap on playbooks written (default 8)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute + print; write no files")
    args = ap.parse_args()

    since = args.since
    if since is None:
        since = (datetime.now() - timedelta(days=30)).date().isoformat()

    c = Consolidator(since=since)
    report = c.run(max_playbooks=args.max_playbooks, dry_run=args.dry_run)

    print(f"consolidator: since={report.since} "
          f"sessions={report.n_sessions} decisions={report.n_decisions} "
          f"daily={report.n_daily} failures={report.n_failures} "
          f"subagent_events={report.n_subagent_events}")
    print(f"patterns identified (top {args.max_playbooks}): {len(report.patterns)}")
    for p, sl in zip(report.patterns, c._unique_slugs(report.patterns)):
        print(f"  [{p.pattern_type}] {p.key} (count={p.count}, metric={p.metric}) -> {sl}-playbook.md")
    if args.dry_run:
        print("DRY-RUN: no files written.")
    else:
        print(f"playbooks written: {len(report.written)}")
        for w in report.written:
            print(f"  {w}")
    print("=== HOT_MD_DIGEST_BEGIN ===")
    print(report.digest)
    print("=== HOT_MD_DIGEST_END ===")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
