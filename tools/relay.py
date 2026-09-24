#!/usr/bin/env python3
"""relay -- the orchestrator-worker relay driver for the local lane.

GATE-B: wiki/research/gates/gate-b-relay-worker-2026-08-16.md (BUILD-JUSTIFIED,
rule 2, operator-ratified reversal of the tool-free rule 2026-08-16).

Runs qwen3.8:27b as a tool-capable RESEARCHER on Ollama /api/chat: the model
acquires (fetch_url, openinsider MCP, jailed vault reads) and structures
(record_claim); THIS DRIVER owns everything else -- context accounting, the forced
relay at 80% of W_eff, resets, distillate assembly, receipts, containment (via
tools/lib/relay_exec.py). The model never self-monitors and never judges.

  python tools/relay.py --leg research:insider-sweep --mission <spec.json> \
         --run "$CLAUDE_LANE_RUN" [--resume <run_id>] [--dry-run]
  python tools/relay.py --probe          # spawn allowlisted MCP servers, pin rosters
  python tools/relay.py --prune [--keep-days 30]

stdout: exactly ONE JSON envelope. Exit contract (extends delegate.py's):
  0 ok | 2 lane unavailable | 3 refused / bad usage | 4 output unusable |
  5 partial OR awaiting-guidance: distillate VALID, resumable (do NOT discard
    it -- this is the one non-zero exit that still carries a deliverable).
    awaiting-guidance (GATE-B gate-b-ask-frontier-2026-08-16): the worker asked
    the orchestrator ONE validated question (envelope.escalation); write the
    answer to envelope.guidance_path and re-run --resume <run>. The answer
    injects as ORCHESTRATOR GUIDANCE (trusted, NOT sentinel-wrapped) and
    registers as a source so derived claims carry prov frontier.

Storage split (the "repo is the only carrier" lesson):
  .claude/state/relay/<run>/   untracked working dir (payloads, scratch, state.json)
  .agents/relay/<run>/         TRACKED distillates (leg-N-seg-M.json + merged)
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import time
import urllib.request
import uuid

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "lib"))

import relay_schema  # noqa: E402
from relay_exec import Executor, ascii_normalize  # noqa: E402
from relay_mcp import McpPool  # noqa: E402

# Reuse delegate.py's verified pieces via importlib (the test-delegate.py
# precedent). delegate.py's BEHAVIOR paths stay untouched; its render_report
# gained relay columns/counters 2026-08-17 (W2, program gate sheet).
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "delegate", os.path.join(TOOLS_DIR, "delegate.py"))
_delegate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_delegate)

STATE_DIR = os.path.join(VAULT, ".claude", "state")
WORK_ROOT = os.path.join(STATE_DIR, "relay")
TRACKED_ROOT = os.path.join(VAULT, ".agents", "relay")
ROLE_PATH = os.path.join(VAULT, ".agents", "roles", "lane-researcher.md")
LOCK_PATH = os.path.join(os.environ.get("ProgramData", r"/path/to/programdata"), "QwenHost", "lane", "lane.lock")

TOOL_DEFS = [
    {"type": "function", "function": {
        "name": "fetch_url",
        "description": "Fetch an allowed http(s) page; returns readable text.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "mcp_call",
        "description": "Call a tool on an allowed MCP server.",
        "parameters": {"type": "object", "properties": {
            "server": {"type": "string"}, "tool": {"type": "string"},
            "args": {"type": "object"}},
            "required": ["server", "tool", "args"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a vault file (sensitive trees are excluded).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List a vault directory (jailed).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "grep_vault",
        "description": "Regex search vault files (jailed).",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string"}, "glob": {"type": "string"}},
            "required": ["pattern"]}}},
    {"type": "function", "function": {
        "name": "scratch_write",
        "description": "Write a working file into this run's scratch dir.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"}, "content": {"type": "string"}},
            "required": ["name", "content"]}}},
    {"type": "function", "function": {
        "name": "scratch_read",
        "description": "Read back a scratch file slice.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"}, "offset": {"type": "integer"},
            "length": {"type": "integer"}}, "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "record_claim",
        "description": "Record ONE extracted factual claim. source_ref must be the [R-nn] tag of the tool result the fact came from.",
        "parameters": {"type": "object", "properties": {
            "entity": {"type": "string"}, "metric": {"type": "string"},
            "value": {"type": "string"}, "date": {"type": "string"},
            "grade": {"type": "string"}, "section": {"type": "string"},
            "text": {"type": "string"}, "prov": {"type": "string"},
            "source_ref": {"type": "string"}},
            "required": ["entity", "metric", "value", "prov", "source_ref"]}}},
    {"type": "function", "function": {
        "name": "note_open_item",
        "description": "Record REMAINING WORK for a later segment. Not for negative results -- use record_negative for those.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"}, "next_action": {"type": "object"}},
            "required": ["text"]}}},
    {"type": "function", "function": {
        "name": "record_negative",
        "description": "Record an EXPLICIT NEGATIVE result: the mission asked for something and it does not exist in the sources. A deliverable, not remaining work.",
        "parameters": {"type": "object", "properties": {
            "question": {"type": "string"},
            "searched": {"type": "array", "items": {"type": "string"}},
            "conclusion": {"type": "string"}},
            "required": ["question", "conclusion"]}}},
    {"type": "function", "function": {
        "name": "propose_edit",
        "description": "PROPOSE one smallest-change edit to a vault file you read THIS LEG (you never write; the orchestrator applies or rejects). old must be copied verbatim from your read incl. \\uXXXX escapes and occur exactly once; before_sha256 = the SHA256 from the read's SOURCE header; new pure ASCII; why names the rule served.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "before_sha256": {"type": "string"},
            "old": {"type": "string"}, "new": {"type": "string"},
            "why": {"type": "string"}},
            "required": ["path", "before_sha256", "old", "new", "why"]}}},
    {"type": "function", "function": {
        "name": "ask_frontier",
        "description": "Ask the frontier orchestrator ONE question you genuinely cannot answer from sources (judgment call, irreconcilable sources, missing domain knowledge). Requires what you tried and the [R-nn] refs that frame it. The leg pauses; guidance arrives next segment.",
        "parameters": {"type": "object", "properties": {
            "question": {"type": "string"}, "tried": {"type": "string"},
            "context_refs": {"type": "array", "items": {"type": "string"}}},
            "required": ["question", "tried", "context_refs"]}}},
]

def resolve_role(lane_cfg, leg, override=None):
    """Resolve the worker ROLE for a leg (GATE-B
    gate-b-local-orchestration-program-2026-08-17). Fail-closed: an unmapped
    leg-family prefix with no --role override is refused; so is a missing or
    unreadable role file, an empty tools list, or a tool name not in the
    executor TABLE (a config typo must fail loudly, never silently).
    Returns {key, path, sha256, tools, raw_reads, expose_sha, text}."""
    from relay_exec import Executor as _Ex
    roles = (lane_cfg.get("relay") or {}).get("roles") or {}
    key = override or leg.split(":", 1)[0]
    spec = roles.get(key)
    if spec is None:
        raise SystemExit(print(_fail(3, leg, "-",
                         "no role mapped for leg family %r (roles: %s); pass "
                         "--role or map it in config/local-lane.json"
                         % (key, sorted(roles) or "none"))) or 3)
    path = os.path.join(VAULT, spec["role_file"])
    try:
        raw = open(path, "rb").read()
    except OSError as exc:
        raise SystemExit(print(_fail(3, leg, "-",
                         "role file unreadable: %s (%s)" % (
                             spec["role_file"], exc))) or 3)
    tools = spec.get("tools") or []
    bad = [t for t in tools if t not in _Ex.TABLE]
    if not tools or bad:
        raise SystemExit(print(_fail(3, leg, "-",
                         "role %r tools invalid (empty or unknown: %s)"
                         % (key, bad))) or 3)
    return {"key": key, "path": spec["role_file"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "tools": list(tools),
            "raw_reads": bool(spec.get("raw_reads")),
            "expose_sha": bool(spec.get("expose_sha")),
            "text": raw.decode("ascii", "replace")}


HANDOFF_DIRECTIVE = (
    "HANDOFF NOW. Stop calling tools. Write ONLY a short narrative (max 1200 "
    "characters): what changed in your understanding this segment and what the "
    "next segment should do first. The system assembles everything else from "
    "your recorded claims and notes.")

PLAN_DIRECTIVE = (
    "PLAN CHECKPOINT. Your first tool batch is HELD, not executed. In at most "
    "600 characters state your plan: which sources you will use, in what "
    "order, and the shape of the claims you expect to record. Do not call "
    "tools in this reply.")
PLAN_ESC_ID = "P-01"

# One mechanical corrective turn per leg (live acceptance 2026-08-17: on real
# docs the model read the source, then delivered every figure as PROSE and
# stopped -- prose is not a deliverable, and without this nudge the leg exits
# zero-yield partial with the work already done but unrecorded).
ZERO_YIELD_NUDGE = (
    "You stopped without recording ANY deliverable. Prose is NOT a "
    "deliverable -- only record_claim / record_negative / note_open_item / "
    "propose_edit calls persist. Convert every figure or finding from your "
    "last message into the appropriate tool calls NOW (exact values as "
    "printed, cite the [R-nn] source ref). If the mission truly yielded "
    "nothing, call record_negative and say why.")


# ------------------------------------------------------------------ lane mutex
class LaneLock:
    """Exclusive OS-held lock on one file. Released by the OS on process death.
    ONE Ollama slot -- a second local consumer must see a clean refusal, not an
    invisible queue that corrupts both parties' measurements."""

    def __init__(self, path):
        self.path = path
        self.fh = None

    def acquire(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.fh = open(self.path, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fh.seek(0)
            self.fh.truncate()
            self.fh.write("%d %s\n" % (os.getpid(), time.strftime("%H:%M:%S")))
            self.fh.flush()
            return True
        except OSError:
            holder = ""
            try:
                with open(self.path) as r:
                    holder = r.read().strip()
            except OSError:
                pass
            self.fh.close()
            self.fh = None
            print("relay: lane BUSY (held by %s) -- one Ollama slot, try again"
                  % (holder or "unknown"), file=sys.stderr)
            return False

    def release(self):
        if self.fh:
            try:
                if os.name == "nt":
                    import msvcrt
                    self.fh.seek(0)
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            self.fh.close()
            self.fh = None


# ------------------------------------------------------------------ the driver
class RelayRun:
    def __init__(self, args, cfg, lane_cfg):
        self.leg = args.leg
        self.run_id = args.resume or (args.run or uuid.uuid4().hex[:8])
        self.cfg = cfg                      # relay block
        self.lane = lane_cfg                # whole local-lane.json
        self.model = lane_cfg["model"]
        self.host = os.environ.get("OLLAMA_HOST") or lane_cfg.get("host") \
            or "http://127.0.0.1:11434"
        if not self.host.startswith("http"):
            self.host = "http://" + self.host
        self.work = os.path.join(WORK_ROOT, self.run_id)
        self.tracked = os.path.join(TRACKED_ROOT, self.run_id)
        os.makedirs(self.work, exist_ok=True)
        os.makedirs(self.tracked, exist_ok=True)
        self.mission = json.load(open(args.mission, encoding="utf-8"))
        errs = relay_schema.validate_mission(self.mission)
        if errs:
            print(_fail(3, self.leg, self.run_id,
                        "mission invalid: " + "; ".join(errs[:5])))
            raise SystemExit(3)
        self.budgets = relay_schema.effective_budgets(
            self.mission, cfg.get("budgets") or {})
        cfg_eff = dict(cfg)
        cfg_eff["budgets"] = self.budgets
        # Role resolution (frozen into state at leg creation; resume verifies)
        self.role_info = resolve_role(lane_cfg, self.leg,
                                      getattr(args, "role", None))
        self.role = self.role_info["text"]
        self.tool_defs = [d for d in TOOL_DEFS
                          if d["function"]["name"] in set(self.role_info["tools"])]
        self.ex = Executor(self.work, cfg_eff, self.mission,
                           allowed_tools=self.role_info["tools"],
                           raw_reads=self.role_info["raw_reads"],
                           expose_sha=self.role_info["expose_sha"])
        self.ex.mcp = McpPool(self.ex.mcp_allowed,
                              cfg.get("mcp_spawn_timeout_s", 60),
                              self.budgets.get("max_mcp_calls", 40))
        # TRIGGER FREEZE (Fable-review fix 2 + F-3): captured at leg CREATION,
        # absent -> "unattributed" (excluded by every promotion counter).
        # Resumes keep the frozen value; a resume under a different env is
        # recorded in resumed_triggers (visible mixed provenance).
        self.trigger = os.environ.get("CLAUDE_LANE_TRIGGER") or "unattributed"
        self.resumed_triggers = []
        self.mission_digest = "sha256:" + hashlib.sha256(
            json.dumps(self.mission, sort_keys=True).encode()).hexdigest()[:12]
        self.extractor = "local:%s@%s" % (self.model, lane_cfg.get("model_digest", "?"))
        # protocol constants
        self.w_eff = cfg["w_eff_tokens"]
        self.threshold = cfg["relay_threshold_tokens"]
        self.reserve = cfg["relay_reserve_tokens"]
        self.hard = min(int(cfg.get("hard_trigger_pct", 0.9) * self.w_eff),
                        self.threshold + self.reserve)
        # LIVELOCK GUARD (suite T5 exposed this): if the threshold does not leave
        # room for the fixed prefix plus ONE tool batch plus working turns, every
        # segment relays before any work happens and the leg spins to max_segments.
        role_est = len(self.role) // 3 + 400          # role + mission floor
        min_threshold = role_est + 2 * cfg["max_result_tokens"] + self.reserve
        if self.threshold < min_threshold:
            print(_fail(3, self.leg, self.run_id,
                        "config refused: relay_threshold_tokens %d < minimum "
                        "workable %d (prefix+2*max_result+reserve) -- the leg "
                        "would livelock" % (self.threshold, min_threshold)))
            raise SystemExit(3)
        # accounting
        self.ratio = 3.0                    # chars/token EWMA, self-calibrating
        self.observed = 0
        self.pending_chars = 0
        self.prompt_tokens_total = 0        # cumulative prompt_eval across turns
        # cross-segment carriers
        self.all_claims = []
        self.done_items = []
        self.not_found = []
        self.segments = []
        self.turns = 0
        self.zero_yield_nudged = False
        self.out_tokens = 0
        self.started = time.time()
        self.flags = {"truncated": False, "stalled": False,
                      "budget_exhausted": False, "distillate_degraded": False}
        self.recent_calls = []
        self.consec_malformed = 0
        # ask_frontier (GATE-B gate-b-ask-frontier-2026-08-16)
        self.guidance_arg = getattr(args, "guidance", None)
        self.guidance_block = None
        # plan_checkpoint intercept-and-hold (Fable-review F-6): the first tool
        # batch is HELD for orchestrator approval; APPROVE dispatches it
        # unchanged, anything else drops it and injects steering.
        self.held_batch = None
        self.held_approved = False
        # resume
        if args.resume:
            self._load_resume()

    # -------------------------------------------------------------- transport
    def chat(self, messages, num_predict=2048):
        opts = {"num_predict": num_predict}
        s = self.cfg.get("sampling") or {}
        if s.get("temperature") is not None:
            opts["temperature"] = s["temperature"]
        if s.get("top_p") is not None:
            opts["top_p"] = s["top_p"]
        body = json.dumps({"model": self.model, "messages": messages,
                           "tools": self.tool_defs, "stream": False,
                           "options": opts}).encode()
        req = urllib.request.Request(self.host + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())

    # ------------------------------------------------------------ accounting
    def account(self, resp, msgs_chars):
        pec = resp.get("prompt_eval_count") or 0
        ec = resp.get("eval_count") or 0
        self.observed = pec + ec
        self.out_tokens += ec
        self.prompt_tokens_total += pec
        self.pending_chars = 0
        # self-calibrate chars/token against server truth
        if pec > 200 and msgs_chars > 0:
            self.ratio = 0.7 * self.ratio + 0.3 * max(1.5, msgs_chars / pec)
        # truncation canary (generalized from delegate.py)
        if pec and msgs_chars and pec < (msgs_chars / self.ratio) * 0.6:
            self.flags["truncated"] = True
            return "TRUNCATED"
        fill = self.projected()
        if fill >= self.hard:
            return "HARD"
        if fill >= self.threshold:
            return "SOFT"
        return None

    def projected(self):
        return self.observed + int(self.pending_chars / self.ratio)

    # ------------------------------------------------------------ segments
    def seg_messages(self, carry):
        msgs = [{"role": "system", "content": self.role}]
        user = "MISSION (verbatim):\n" + relay_schema.dumps_ascii(self.mission)
        # Pinned MCP rosters (from --probe): tool names + arg schemas for the
        # allowed servers. Byte-stable within the leg. pilot001 measured 8 wasted
        # refusals from arg-guessing without this block.
        roster_path = os.path.join(WORK_ROOT, "mcp-rosters.json")
        if os.path.isfile(roster_path) and self.ex.mcp_allowed:
            try:
                pinned = json.load(open(roster_path, encoding="ascii"))
                lines = []
                for srv, info in (pinned.get("rosters") or {}).items():
                    if srv not in self.ex.mcp_allowed or "tools" not in info:
                        continue
                    lines.append("server %s tools: %s" % (
                        srv, ", ".join(info["tools"])))
                if lines:
                    user += ("\n\nAVAILABLE MCP TOOLS (call via mcp_call; use "
                             "exact tool names; the server validates argument "
                             "names):\n" + "\n".join(lines))
            except (ValueError, OSError):
                pass
        if carry:
            user += "\n\nCARRY-IN FROM PRIOR SEGMENTS:\n" + carry
            user += ("\n\nContinue from the open items. Do NOT re-fetch anything "
                     "listed under sources -- those facts are already recorded.")
        if self.guidance_block:
            # The ONE sanctioned trusted channel: orchestrator-authored, NOT
            # sentinel-wrapped (it IS instruction, unlike tool payloads).
            user += "\n\n" + self.guidance_block
        msgs.append({"role": "user", "content": user})
        return msgs

    def carry_text(self):
        lines = []
        if self.all_claims:
            lines.append("claims recorded so far (%d):" % len(self.all_claims))
            for c in self.all_claims[-60:]:
                lines.append("  - %s | %s | %s | %s | prov %s" % (
                    c.get("entity"), c.get("metric"), c.get("value"),
                    c.get("date", "-"), c.get("prov")))
        if self.done_items:
            lines.append("done: " + "; ".join(self.done_items[-20:]))
        open_items = self.ex.open_items
        if open_items:
            lines.append("open items:")
            for o in open_items[-20:]:
                lines.append("  - %s: %s" % (o["id"], o["text"]))
        if self.ex.sources:
            lines.append("sources already fetched (do not re-fetch):")
            for s in self.ex.sources[-40:]:
                lines.append("  - [%s] %s" % (s["ref"], s["locator"][:120]))
        return ascii_normalize("\n".join(lines))[:24000]

    def relay(self, msgs, reason):
        """Force the distillate; ONE repair retry; machine-assembly either way."""
        narrative, degraded = "", False
        try:
            resp = self.chat(msgs + [{"role": "user",
                                      "content": HANDOFF_DIRECTIVE}],
                             num_predict=800)
            narrative = (resp.get("message", {}).get("content") or "").strip()
            self.turns += 1
        except Exception:                                     # noqa: BLE001
            degraded = True
        if not narrative:
            degraded = True
        self.flags["distillate_degraded"] = self.flags["distillate_degraded"] or degraded
        acct = {
            "segment_prompt_tokens_evaluated": self.observed,
            "segment_output_tokens": self.out_tokens,
            "turns": self.turns, "tool_calls": self.ex.counters["tool_calls"],
            "fetches": self.ex.counters["fetches"],
            "mcp_calls": self.ex.counters["mcp_calls"],
            "refusals": self.ex.counters["refusals"],
            "grounding_refusals": self.ex.counters["grounding_refusals"],
            "fill_at_relay": self.projected(), "relay_reason": reason,
            "wall_s": int(time.time() - self.started),
        }
        merged, conflicts = relay_schema.merge_claims(self.all_claims, self.ex.claims)
        self.all_claims = merged
        self.not_found = list(self.ex.not_found)      # executor owns the channel
        flags = dict(self.flags)
        flags["injection_flags"] = self.ex.injection_flags
        flags["conflicts"] = ["%s|%s|%s" % k3 for k3 in conflicts]
        flags["degraded_servers"] = dict(self.ex.mcp.down)
        if self.ex.escalations:
            # questions ride the TRACKED distillate; the 2026-09-11 review reads
            # whether the worker asks well or punts
            flags["escalations"] = [dict(e) for e in self.ex.escalations]
        d = relay_schema.assemble_distillate(
            self.run_id, self.leg, self.ex.segment, self.extractor,
            self.mission_digest, self.all_claims, self.ex.sources,
            self.ex.open_items, self.done_items, self.not_found,
            ascii_normalize(narrative), acct, flags,
            proposed_edits=(self.ex.proposed_edits
                            if self.ex.proposed_edits else None))
        seg_path = os.path.join(self.tracked, "leg-seg-%02d.json" % self.ex.segment)
        with open(seg_path, "w", encoding="ascii") as fh:
            fh.write(relay_schema.dumps_ascii(d))
        self.segments.append(seg_path)
        self._save_state()
        return d

    # ------------------------------------------------------------ state
    def _save_state(self):
        state = {"run": self.run_id, "leg": self.leg, "segment": self.ex.segment,
                 "claims": self.all_claims, "done_items": self.done_items,
                 "not_found": self.not_found, "open_items": self.ex.open_items,
                 "sources": self.ex.sources, "segments": self.segments,
                 "flags": self.flags,
                 "escalations": self.ex.escalations,
                 "pending_escalation": self.ex.pending_escalation,
                 "escalation_count": self.ex.counters["escalations"],
                 "proposed_edits": self.ex.proposed_edits,
                 "held_batch": self.held_batch,
                 "held_approved": self.held_approved,
                 "trigger": self.trigger,
                 "resumed_triggers": self.resumed_triggers,
                 "role": {"key": self.role_info["key"],
                          "path": self.role_info["path"],
                          "sha256": self.role_info["sha256"],
                          "tools": self.role_info["tools"]}}
        # atomic write (Fable-review F-10): --status reads before the lock and
        # a crash mid-write must never leave torn JSON
        p = os.path.join(self.work, "state.json")
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="ascii") as fh:
            fh.write(relay_schema.dumps_ascii(state))
        os.replace(tmp, p)

    def _load_resume(self):
        p = os.path.join(self.work, "state.json")
        if not os.path.isfile(p):
            raise SystemExit(_fail(3, self.leg, self.run_id,
                                   "--resume: no state.json for run %s" % self.run_id))
        st = json.load(open(p, encoding="ascii"))
        self.all_claims = st.get("claims", [])
        self.done_items = st.get("done_items", [])
        self.not_found = st.get("not_found", [])
        self.segments = st.get("segments", [])
        self.ex.sources = st.get("sources", [])
        self.ex.open_items = st.get("open_items", [])
        self.ex.segment = st.get("segment", 0)
        # escalation state spans resumes (the budget is per LEG, not per process)
        self.ex.escalations = st.get("escalations", [])
        self.ex.pending_escalation = st.get("pending_escalation")
        self.ex.counters["escalations"] = st.get("escalation_count", 0)
        self.ex.proposed_edits = st.get("proposed_edits", [])
        self.held_batch = st.get("held_batch")
        self.held_approved = bool(st.get("held_approved"))
        # TRIGGER FREEZE: the frozen value governs receipts/counters; a resume
        # under a different env is recorded, never re-attributed (F-3)
        frozen_trigger = st.get("trigger")
        if frozen_trigger:
            env_now = os.environ.get("CLAUDE_LANE_TRIGGER")
            if env_now and env_now != frozen_trigger:
                self.resumed_triggers = list(st.get("resumed_triggers", []))
                self.resumed_triggers.append(env_now)
            else:
                self.resumed_triggers = st.get("resumed_triggers", [])
            self.trigger = frozen_trigger
        # ROLE FREEZE (F-4): resume REFUSES on role-file drift; the frozen tool
        # subset governs the whole leg
        frozen_role = st.get("role")
        if frozen_role:
            path = os.path.join(VAULT, frozen_role["path"])
            try:
                sha_now = hashlib.sha256(open(path, "rb").read()).hexdigest()
            except OSError:
                sha_now = "unreadable"
            if sha_now != frozen_role["sha256"]:
                print(_fail(3, self.leg, self.run_id,
                            "role file %s changed since leg creation (frozen "
                            "%s.. vs current %s..) -- re-run fresh or restore "
                            "the role file" % (frozen_role["path"],
                                               frozen_role["sha256"][:12],
                                               sha_now[:12])))
                raise SystemExit(3)
            self.role_info["tools"] = frozen_role["tools"]
            self.tool_defs = [d for d in TOOL_DEFS if d["function"]["name"]
                              in set(frozen_role["tools"])]
            self.ex.allowed_tools = set(frozen_role["tools"])

    # ------------------------------------------------- escalation (ask_frontier)
    def _absorb_guidance(self):
        """A resumed run with a pending escalation needs the orchestrator's
        answer on disk. Registers it as a SOURCE (kind frontier) so derived
        claims cite it with prov frontier -- frontier judgment enters labeled,
        never laundered as the local model's own."""
        esc = self.ex.pending_escalation
        gpath = self.guidance_arg or os.path.join(
            self.work, "guidance-%s.md" % esc["id"])
        if not os.path.isfile(gpath):
            print(_fail(3, self.leg, self.run_id,
                        "run awaiting guidance for %s (%r): write %s or pass "
                        "--guidance <path>, then re-run --resume %s"
                        % (esc["id"], esc["question"][:80],
                           os.path.relpath(gpath, VAULT), self.run_id)))
            return 3
        text = open(gpath, encoding="utf-8", errors="replace").read()[:24000]
        src = self.ex._register("frontier",
                                "orchestrator-guidance %s" % esc["id"], text)
        # trusted by construction (orchestrator-authored file in the run dir;
        # the scratch name grammar cannot express a path that reaches it) --
        # clear the injection scan so derived claims are not tainted
        src["injection_flags"] = []
        self.ex.injection_flags = [f for f in self.ex.injection_flags
                                   if f.get("ref") != src["ref"]]
        esc["answered"] = True
        esc["guidance_ref"] = src["ref"]
        # after a JSON state round-trip pending_escalation and its entry in
        # escalations are DISTINCT dicts -- close the ledger entry by id
        for e in self.ex.escalations:
            if e.get("id") == esc["id"]:
                e.update(esc)
                break
        else:
            self.ex.escalations.append(esc)
        if esc.get("kind") == "plan":
            # intercept-and-hold verdict (F-6): APPROVE dispatches the held
            # batch unchanged at segment start; anything else DROPS it and the
            # guidance text steers the fresh segment.
            if text.strip().upper().startswith("APPROVE"):
                self.held_approved = True
                self.guidance_block = (
                    "ORCHESTRATOR APPROVED your plan (%s). Your held first "
                    "batch was executed; its results follow in this message."
                    % esc["id"])
            else:
                self.held_batch = None
                self.held_approved = False
                self.guidance_block = (
                    "ORCHESTRATOR REDIRECTED your plan (%s) -- your held first "
                    "batch was DROPPED. Follow this steering (trusted channel "
                    "-- this IS instruction):\n%s"
                    % (esc["id"], ascii_normalize(text)))
        else:
            self.guidance_block = (
                "ORCHESTRATOR GUIDANCE (trusted channel -- this IS "
                "instruction, unlike tool payloads) answering your question "
                "%s. Cite [%s] with prov \"frontier\" ONLY for a value that "
                "appears in this guidance text itself; when it selects among "
                "values from other sources, cite the value's own [R-nn]:\n%s"
                % (esc["id"], src["ref"], ascii_normalize(text)))
        self.ex.pending_escalation = None
        self._save_state()
        return None

    # ------------------------------------------------------------ main loop
    def run(self):
        deadline = self.started + self.budgets.get("wall_clock_s", 2400)
        status = "ok"
        if self.ex.pending_escalation:
            code = self._absorb_guidance()
            if code is not None:
                return code
        while self.ex.segment < self.budgets.get("max_segments", 8):
            sentinel = self.ex.new_segment()
            _ = sentinel
            msgs = self.seg_messages(self.carry_text()
                                     if self.ex.segment > 1 else None)
            if self.held_approved and self.held_batch:
                # dispatch the APPROVED held batch driver-side; results enter
                # the segment message wrapped exactly like live tool payloads
                outs = []
                pend = False
                for h in self.held_batch:
                    out, _ok = self.ex.dispatch(h["name"], h["args"])
                    self.pending_chars += len(out)
                    outs.append(out)
                    if self.ex.pending_escalation:
                        pend = True   # collision: ask_frontier in the batch
                        break
                self.held_batch = None
                self.held_approved = False
                msgs[1]["content"] += (
                    "\n\nHELD FIRST BATCH RESULTS (orchestrator-approved; "
                    "already executed -- do not re-issue these calls):\n"
                    + "\n".join(outs))
                self._save_state()
                if pend:
                    self.relay(msgs, "escalation")
                    return self.finish("awaiting-guidance")
            seg_snapshot = (len(self.all_claims), len(self.ex.sources),
                            len(self.not_found))
            seg_done = False
            while not seg_done:
                if time.time() > deadline or \
                        self.turns >= self.budgets.get("max_turns", 60) or \
                        self.out_tokens >= self.budgets.get(
                            "max_output_tokens_total", 65536):
                    self.flags["budget_exhausted"] = True
                    self.relay(msgs, "budget")
                    return self.finish("partial")
                msgs_chars = sum(len(str(m.get("content") or "")) for m in msgs)
                try:
                    resp = self.chat(msgs)
                except Exception as exc:                      # noqa: BLE001
                    # one inline re-arm attempt, then exit 2 (delegate contract)
                    time.sleep(3)
                    try:
                        resp = self.chat(msgs)
                    except Exception:                         # noqa: BLE001
                        self.relay(msgs, "lane-death")
                        print(_fail(2, self.leg, self.run_id,
                                    "daemon unreachable: %s" % exc))
                        return 2
                self.turns += 1
                trigger = self.account(resp, msgs_chars)
                m = resp.get("message", {})
                msgs.append(m)
                tcs = m.get("tool_calls") or []
                if trigger == "TRUNCATED":
                    self.relay(msgs, "truncation-canary")
                    print(_fail(2, self.leg, self.run_id,
                                "daemon-side truncation detected"))
                    return 2
                if not tcs:
                    # Zero-yield corrective turn (ONE per leg): the model quit
                    # with no deliverables recorded -- steer once before
                    # accepting model-complete.
                    if (not self.all_claims and not self.ex.claims and
                            not self.ex.proposed_edits and
                            not self.ex.not_found and
                            not self.ex.open_items and
                            not self.ex.pending_escalation and
                            not self.zero_yield_nudged):
                        self.zero_yield_nudged = True
                        msgs.append({"role": "user",
                                     "content": ZERO_YIELD_NUDGE})
                        continue
                    # model believes it is done with this segment/mission
                    self.relay(msgs, "model-complete")
                    progressed = (len(self.all_claims), len(self.ex.sources),
                                  len(self.not_found)) != seg_snapshot
                    if self.ex.open_items and progressed and \
                            not self.flags["budget_exhausted"]:
                        seg_done = True      # next segment continues open items
                        break
                    if self.ex.open_items and not progressed:
                        # NO-PROGRESS STALL (pilot001: 8 segments of spin when
                        # open items could never empty) -- stop honestly.
                        self.flags["stalled"] = True
                        return self.finish("partial")
                    return self.finish("ok")
                if trigger == "HARD":
                    self.relay(msgs, "hard-fill")
                    seg_done = True
                    break
                # PLAN CHECKPOINT (intercept-and-hold, F-6): the FIRST tool
                # batch of a plan_checkpoint mission is HELD before dispatch;
                # the worker states its plan and the leg pauses with both the
                # narrative AND the concrete held calls in the envelope. The
                # ask_frontier budget is untouched (P-01 never increments it).
                if self.mission.get("plan_checkpoint") and self.ex.segment == 1 \
                        and not any(e.get("id") == PLAN_ESC_ID
                                    for e in self.ex.escalations):
                    try:
                        resp2 = self.chat(msgs + [{"role": "user",
                                                   "content": PLAN_DIRECTIVE}],
                                          num_predict=400)
                        self.turns += 1
                        plan = ascii_normalize((resp2.get("message", {})
                                                .get("content") or "").strip())[:600]
                    except Exception:                         # noqa: BLE001
                        plan = ""
                    held = []
                    for tc in tcs:
                        fn = tc.get("function") or {}
                        targs = fn.get("arguments")
                        if isinstance(targs, str):
                            try:
                                targs = json.loads(targs)
                            except ValueError:
                                targs = {}
                        held.append({"name": fn.get("name") or "",
                                     "args": targs if isinstance(targs, dict)
                                     else {}})
                    self.held_batch = held
                    calls_txt = "; ".join(
                        "%s(%s)" % (h["name"], json.dumps(
                            h["args"], ensure_ascii=True)[:120])
                        for h in held)
                    esc = {"id": PLAN_ESC_ID, "kind": "plan",
                           "question": (plan or "(worker stated no plan)")
                           + " || HELD BATCH: " + calls_txt[:800],
                           "tried": "plan-checkpoint (driver-forced, mission "
                                    "option; APPROVE dispatches the held batch "
                                    "unchanged, anything else drops it and "
                                    "steers)",
                           "context_refs": [], "segment": 1, "answered": False}
                    self.ex.escalations.append(esc)
                    self.ex.pending_escalation = esc
                    self.ex._log("plan", "plan_checkpoint", calls_txt[:300], True)
                    self.relay(msgs, "plan-checkpoint")
                    return self.finish("awaiting-guidance")
                # execute the batch
                batch_malformed = 0
                for tc in tcs:
                    fn = tc.get("function") or {}
                    name = fn.get("name") or ""
                    targs = fn.get("arguments")
                    if isinstance(targs, str):
                        try:
                            targs = json.loads(targs)
                        except ValueError:
                            batch_malformed += 1
                            msgs.append({"role": "tool", "tool_name": name,
                                         "content": "TOOL ERROR: arguments were "
                                         "not valid JSON; retry with valid JSON"})
                            continue
                    # repeat-loop detector
                    sig = (name, json.dumps(targs, sort_keys=True, default=str))
                    self.recent_calls.append(sig)
                    if self.recent_calls.count(sig) >= 3:
                        self.flags["stalled"] = True
                        self.relay(msgs, "repeat-loop")
                        seg_done = True
                        break
                    out, ok = self.ex.dispatch(name, targs)
                    self.pending_chars += len(out)
                    msgs.append({"role": "tool", "tool_name": name,
                                 "content": out})
                    if self.ex.pending_escalation:
                        # PAUSE: distillate stays valid, state persists, the
                        # orchestrator answers and re-runs --resume (exit-5
                        # family; no new transport, no second billed session)
                        self.relay(msgs, "escalation")
                        return self.finish("awaiting-guidance")
                    if self.ex.counters["unknown_tool"] >= 3:
                        self.relay(msgs, "unknown-tool-probing")
                        print(_fail(3, self.leg, self.run_id,
                                    "3 unknown-tool attempts (probing) -- aborted"))
                        return 3
                if seg_done:
                    break
                self.consec_malformed = (self.consec_malformed + batch_malformed
                                         if batch_malformed else 0)
                if self.consec_malformed >= 3:
                    self.relay(msgs, "malformed-calls")
                    print(_fail(4, self.leg, self.run_id,
                                "3 consecutive malformed tool-call batches"))
                    return 4
                if trigger == "SOFT":
                    self.relay(msgs, "soft-fill")
                    seg_done = True
            # loop continues into next segment
        self.flags["budget_exhausted"] = True
        return self.finish("partial")

    def finish(self, status):
        merged_path = os.path.join(self.tracked, "leg-merged.json")
        final = None
        if self.segments:
            final = json.load(open(self.segments[-1], encoding="ascii"))
            with open(merged_path, "w", encoding="ascii") as fh:
                fh.write(relay_schema.dumps_ascii(final))
        errs = relay_schema.validate_distillate(final) if final else ["no distillate"]
        # ZERO-YIELD GUARD (suite T5 exposed this): a leg that recorded no claims,
        # no open items, and no negatives did NOT complete anything -- it must never
        # report ok, or the orchestrator reads silence as success.
        if status == "ok" and not self.all_claims and not self.ex.open_items \
                and not self.not_found and not self.ex.proposed_edits:
            status = "partial"
            errs = list(errs) + ["zero-yield leg: no claims, no open_items, "
                                 "no not_found, no proposed_edits -- treat as "
                                 "failed work"]
        if errs and status == "ok":
            status = "partial"
        envelope = {
            "_prov": self.extractor, "_run": self.run_id, "leg": self.leg,
            "status": status,
            "distillate_paths": [os.path.relpath(p, VAULT) for p in
                                 self.segments + ([merged_path] if final else [])],
            "distillate": final,
            "validation_errors": errs or [],
            "accounting": (final or {}).get("accounting", {}),
            "flags": (final or {}).get("flags", self.flags),
        }
        if status == "awaiting-guidance" and self.ex.pending_escalation:
            esc = self.ex.pending_escalation
            envelope["escalation"] = dict(esc)
            envelope["guidance_path"] = os.path.relpath(os.path.join(
                self.work, "guidance-%s.md" % esc["id"]), VAULT)
            envelope["resume_hint"] = (
                "write the guidance file, then: python tools/relay.py --leg %s "
                "--mission <same spec> --resume %s" % (self.leg, self.run_id))
        self.receipt(status)
        self.ex.mcp.close()
        print(relay_schema.dumps_ascii(envelope))
        return 0 if status == "ok" else 5

    def receipt(self, status):
        """Leg-level row into the SAME ledger delegate.py uses (kind=relay)."""
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "relay",
               "run": self.run_id, "leg": self.leg, "model": self.model,
               "digest": self.lane.get("model_digest"),
               "trigger": self.trigger, "role": self.role_info["key"],
               "segments": self.ex.segment, "turns": self.turns,
               "tool_calls": self.ex.counters["tool_calls"],
               "fetches": self.ex.counters["fetches"],
               "mcp_calls": self.ex.counters["mcp_calls"],
               "refusals": self.ex.counters["refusals"],
               "claims": len(self.all_claims),
               "escalations": self.ex.counters["escalations"],
               "grounding_refusals": self.ex.counters["grounding_refusals"],
               "prompt_tokens": self.prompt_tokens_total,
               "out_tokens": self.out_tokens, "status": status,
               "secs": int(time.time() - self.started),
               "exit": 0 if status == "ok" else 5}
        if self.resumed_triggers:
            row["resumed_triggers"] = self.resumed_triggers
        path = os.path.join(STATE_DIR,
                            "delegate-runs-%s.jsonl" % time.strftime("%Y-%m-%d"))
        try:
            with open(path, "a", encoding="ascii") as fh:
                fh.write(json.dumps(row, ensure_ascii=True) + "\n")
        except OSError as exc:
            print("WARNING: receipt write failed: %s" % exc, file=sys.stderr)


def _fail(code, leg, run, msg):
    return relay_schema.dumps_ascii({
        "_run": run, "leg": leg, "status":
        {2: "unavailable", 3: "refused", 4: "unusable", 5: "partial"}.get(code),
        "error": msg})


# ------------------------------------------------------------------ commands
def cmd_status(run_id):
    """Read-only live view of a run (W2): safe while a leg is running (state
    writes are atomic; one 200ms retry covers the replace window)."""
    p = os.path.join(WORK_ROOT, run_id, "state.json")
    if not os.path.isfile(p):
        print(relay_schema.dumps_ascii({"run": run_id, "error": "no such run"}))
        return 3
    st = None
    for _ in range(2):
        try:
            st = json.load(open(p, encoding="ascii"))
            break
        except ValueError:
            time.sleep(0.2)
    if st is None:
        print(relay_schema.dumps_ascii({"run": run_id,
                                        "state": "state-in-flight, retry"}))
        return 0
    acct = {}
    segs = sorted(glob.glob(os.path.join(TRACKED_ROOT, run_id, "leg-seg-*.json")))
    if segs:
        try:
            acct = (json.load(open(segs[-1], encoding="ascii"))
                    .get("accounting") or {})
        except (ValueError, OSError):
            pass
    pend = st.get("pending_escalation") or {}
    out = {"run": run_id, "leg": st.get("leg"), "segment": st.get("segment"),
           "claims": len(st.get("claims") or []),
           "open_items": len(st.get("open_items") or []),
           "not_found": len(st.get("not_found") or []),
           "escalations": st.get("escalation_count", 0),
           "pending_question": pend.get("question"),
           "trigger": st.get("trigger"),
           "role": (st.get("role") or {}).get("key"),
           "fill_at_last_relay": acct.get("fill_at_relay"),
           "wall_s": acct.get("wall_s"),
           "flags": st.get("flags")}
    print("run %s leg %s seg %s claims %d open %d esc %s%s" % (
        run_id, out["leg"], out["segment"], out["claims"], out["open_items"],
        out["escalations"],
        (" PENDING: %r" % pend.get("question", "")[:80]) if pend else ""),
        file=sys.stderr)
    print(relay_schema.dumps_ascii(out))
    return 0


def cmd_probe(cfg):
    pool = McpPool(cfg.get("mcp_allowlist") or [],
                   cfg.get("mcp_spawn_timeout_s", 60))
    result = {}
    for name in pool.allowlist:
        try:
            srv = pool.get(name)
            result[name] = {"spawn_s": srv.spawn_s, "tools": sorted(srv.tools)}
            print("%s: OK %.1fs, %d tools" % (name, srv.spawn_s, len(srv.tools)))
        except Exception as exc:                              # noqa: BLE001
            result[name] = {"error": str(exc)}
            print("%s: FAIL %s" % (name, exc))
    pool.close()
    os.makedirs(WORK_ROOT, exist_ok=True)
    pin_path = os.path.join(WORK_ROOT, "mcp-rosters.json")
    with open(pin_path, "w", encoding="ascii") as fh:
        fh.write(relay_schema.dumps_ascii(
            {"pinned": time.strftime("%Y-%m-%d %H:%M"), "rosters": result}))
    print("rosters pinned: %s" % os.path.relpath(pin_path, VAULT))
    return 0 if all("error" not in v for v in result.values()) else 2


def cmd_prune(keep_days):
    cutoff = time.time() - keep_days * 86400
    removed = 0
    for root in (WORK_ROOT, TRACKED_ROOT):
        if not os.path.isdir(root):
            continue
        for d in os.listdir(root):
            p = os.path.join(root, d)
            if os.path.isdir(p) and os.path.getmtime(p) < cutoff:
                import shutil
                shutil.rmtree(p, ignore_errors=True)
                removed += 1
    # composed missions + batch state age out on the same clock
    for sub in ("missions", "batches"):
        droot = os.path.join(WORK_ROOT, sub)
        if not os.path.isdir(droot):
            continue
        for f in os.listdir(droot):
            p = os.path.join(droot, f)
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                try:
                    os.remove(p)
                    removed += 1
                except OSError:
                    pass
    print("pruned %d artifact(s) older than %d days" % (removed, keep_days))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg")
    ap.add_argument("--mission")
    ap.add_argument("--run")
    ap.add_argument("--resume")
    ap.add_argument("--guidance", help="path to the orchestrator's answer for a "
                    "run paused awaiting-guidance (default: <run dir>/"
                    "guidance-<Q-id>.md)")
    ap.add_argument("--role", help="explicit role override (default: resolved "
                    "from the leg-family prefix via config relay.roles; X12: "
                    "no ambient selection)")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--status", metavar="RUN")
    ap.add_argument("--prune", action="store_true")
    ap.add_argument("--keep-days", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lane_cfg = json.load(open(os.path.join(VAULT, "config", "local-lane.json"),
                              encoding="utf-8"))
    cfg = lane_cfg.get("relay")
    if not cfg:
        print("relay: no relay block in config/local-lane.json", file=sys.stderr)
        return 3
    # threshold invariant, enforced at every start (Fable-review fix 1)
    assert cfg["relay_threshold_tokens"] + cfg["relay_reserve_tokens"] + \
        cfg["max_result_tokens"] <= cfg["w_eff_tokens"], "relay invariant broken"

    if args.probe:
        return cmd_probe(cfg)
    if args.status:
        return cmd_status(args.status)
    if args.prune:
        return cmd_prune(args.keep_days)
    if not args.leg or not args.mission:
        print("usage: relay.py --leg research:<id> --mission <spec.json> "
              "[--run ID] [--resume RUN]", file=sys.stderr)
        return 3

    # leg gating: delegate.py's fail-closed leg_status, imported not reimplemented.
    # Returns a scalar: 'ok' | 'forbidden' | 'unknown'.
    status = _delegate.leg_status(lane_cfg, args.leg)
    if status != "ok":
        print(_fail(3, args.leg, args.run or "-",
                    "leg %s: %s (see python tools/delegate.py --legs research)"
                    % (status.upper(), args.leg)))
        return 3

    lock = LaneLock(LOCK_PATH)
    if not lock.acquire():
        print(_fail(2, args.leg, args.run or "-", "lane busy"))
        return 2
    try:
        run = RelayRun(args, cfg, lane_cfg)
        if args.dry_run:
            print(relay_schema.dumps_ascii({
                "dry_run": True, "leg": args.leg, "run": run.run_id,
                "mcp_allowed": run.ex.mcp_allowed, "budgets": run.budgets,
                "threshold": run.threshold, "hard": run.hard}))
            return 0
        return run.run()
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
