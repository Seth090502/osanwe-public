"""relay_exec -- the containment executor for the relay worker. SECURITY-LOAD-BEARING.

GATE-B: wiki/research/gates/gate-b-relay-worker-2026-08-16.md.
Every tool call the model emits passes through Executor.dispatch(). Everything in
this file is MECHANICAL enforcement -- nothing is an instruction to the model. This
is the answer to the 2026-08-11 Nemotron incident (a tool-capable local model
appended past a blocking gate and deleted evidence of a private/ write): the
difference between "we told it not to" and "it cannot".

Enforcement inventory (each mirrors a recorded failure or doctrine rule):
- fetch_url: scheme allowlist; blocked domains parsed from the canonical source-policy organ
  (single source of truth, no second copy to rot; fail-closed if the parse looks
  wrong); SSRF denylist applied to the RESOLVED address and re-validated at every
  redirect hop (protects the unauthenticated Ollama daemon on 127.0.0.1); byte cap;
  html->text so raw markup never enters context.
- mcp_call: allowlist of servers (config INTERSECT mission); roster + args
  validated by relay_mcp; robinhood/claudewatch have no code path there (D-SEC-1).
- read_file/list_dir/grep_vault: realpath jail under the vault MINUS the sensitive
  trees (worker holds web egress; read-all + fetch-anywhere is a mechanical exfil
  channel). Junctions resolved before the check; case-insensitive (Windows).
- scratch_write/scratch_read: the ONLY write path; the name grammar has no
  separators, so traversal is not a check, it is unexpressible.
- Every payload entering model context: cap -> ASCII normalize -> sentinel
  strip-then-wrap (delegate.py's recipe; sentinel rotates per SEGMENT) -> injection
  scan (TAG, never censor) -> source registration (R-nn, sha256, scratch spill).
- Every call and every refusal lands in the per-run executor ledger, which is what
  the acceptance suite grades (an ATTEMPT is not a fail; an ALLOWED attempt is).
"""
import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE_POLICY_MD = os.path.join(VAULT, "docs", "osanwe-runtime-reference.md")

SCRATCH_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
TAG_RE = re.compile(r"<[^>]{0,200}>")
WS_RE = re.compile(r"[ \t\r\f\v]+")

# Jailed-out trees (operator-ratified 2026-08-16; relative to VAULT, lowercase).
READ_EXCLUDE_DIRS = ("private", "finance", "credentials", ".raw", ".git",
                     "config", ".obsidian", os.path.join(".claude", "state"))
READ_EXCLUDE_SUFFIX = (".local.md",)
# Secret-bearing NAMES, refused wherever they sit (the contract names .env* and
# auth.json explicitly; the worker holds web egress, so read == exfiltrable).
READ_EXCLUDE_NAMES = ("auth.json",)
READ_EXCLUDE_NAME_PREFIXES = (".env",)
# An independent review found the exact-name rule let the ordinary variants
# through: auth.json.bak, old-auth.json, .auth.json, app.env, a *.key or *.pem.
# Backups and renamed copies of a secret are the same secret. Names are compared
# lower-cased, because _jail lower-cases the relative path before checking.
READ_EXCLUDE_NAME_CONTAINS = ("auth.json",)
READ_EXCLUDE_NAME_SUFFIXES = (".env", ".key", ".pem", ".credentials.json")

# propose_edit path policy: an ALLOWLIST of proposal-eligible trees (Fable-review
# fix 3 + F-5; denylists are unwinnable -- the SystemAudit lesson). Atlas/ is
# excluded OUTRIGHT (human-write-only admits no machine proposal channel; the
# worker surfaces Atlas defects via claims/open-items). wiki/research/ carries
# doctrine artifacts (gate sheets, the parity rule) and is excluded from the
# wiki tree. Fixture proposals resolve ONLY under the fixed parity-fixture root.
# Forward-slash, lowercase, trailing-slash prefixes.
PROPOSE_ALLOW_PREFIXES = ("calendar/", "wiki/", "efforts/",
                          "tools/parity-cases/fixtures/",
                          "tools/relay-cases/fixtures/")
PROPOSE_DENY_PREFIXES = ("wiki/research/",)

# ASCII substitutions (Pattern 22). Keys are \\u-escaped so THIS file stays
# byte-ASCII while still naming the exact characters it replaces.
ASCII_MAP = {
    chr(0x2014): "--", chr(0x2013): "-", chr(0x2018): "'", chr(0x2019): "'",
    chr(0x201C): '"', chr(0x201D): '"', chr(0x2192): "->", chr(0x2190): "<-",
    chr(0x2264): "<=", chr(0x2265): ">=", chr(0x2026): "...", chr(0x00A0): " ",
    chr(0x00D7): "x", chr(0x00B1): "+/-", chr(0x00B0): " deg",
}

# High-signal injection patterns (TAG, never censor -- a local model must never be
# the thing that decides whether an injection succeeded).
INJECTION_PATTERNS = [
    re.compile(r"ignore (all |any )?(previous|prior|above) (instructions|directives)", re.I),
    re.compile(r"automated (data )?processors?", re.I),
    re.compile(r"^\s*system\s*:", re.I | re.M),
    re.compile(r"<\s*/?tool_(call|result)", re.I),
    re.compile(r"you (must|should) now (call|fetch|run|execute)", re.I),
    re.compile(r"[A-Za-z0-9+/=]{2048,}"),          # large base64-ish blob
]


def ascii_normalize(text):
    for k, v in ASCII_MAP.items():
        text = text.replace(k, v)
    return text.encode("ascii", "replace").decode("ascii")


def load_blocked_domains():
    """Parse the explicit blocked-domain block in the canonical source policy.
    FAIL-CLOSED: a parse that yields fewer than 15 domains disables fetch_url
    entirely rather than fetching with a partial blocklist. Root contract prose
    is only a pointer; it cannot silently replace the policy authority."""
    try:
        with open(SOURCE_POLICY_MD, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeError):
        return None
    start, end = "<!-- blocked-domains:start -->", "<!-- blocked-domains:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        return None
    body = text.partition(start)[2]
    if end not in body:
        return None
    body = body.partition(end)[0].strip()
    domains = [item.lower().removesuffix(".") for item in re.split(r"[\s,]+", body) if item]
    domain = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")
    if not domains or any(not domain.fullmatch(item) for item in domains):
        return None
    domains = sorted(set(domains))
    return domains if len(domains) >= 15 else None


class Refusal(Exception):
    """A containment refusal. Returned to the model as a tool error; logged."""


def file_sha_text(path):
    """THE sha recipe for propose_edit staleness: utf-8/replace decode, 262144
    char cap, sha256 over the re-encoded text. ONE function shared by
    t_read_file's _register, t_propose_edit, and tools/relay-apply.py -- two
    recipes would disagree exactly when staleness matters (Fable round-1
    risk 2). Returns (sha_hex, text)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read(262144)
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest(), text


def _unescape(s):
    """Reverse of Executor._escape: \\uXXXX -> char, doubled backslash -> one.
    Module-level: shared by t_propose_edit and tools/relay-apply.py."""
    s = re.sub(r"(?<!\\)\\u([0-9a-fA-F]{4})",
               lambda m: chr(int(m.group(1), 16)), s)
    return s.replace("\\\\", "\\")


class Executor:
    def __init__(self, run_dir, config, mission, ledger_path=None,
                 allowed_tools=None, raw_reads=False, expose_sha=False):
        self.run_dir = run_dir
        self.scratch = os.path.join(run_dir, "scratch")
        os.makedirs(self.scratch, exist_ok=True)
        self.cfg = config          # the relay block of local-lane.json
        self.mission = mission
        # Role surface (GATE-B gate-b-local-orchestration-program-2026-08-17):
        # allowed_tools=None = unfiltered (back-compat); a list makes dispatch
        # REFUSE-AND-LOG any tool outside it. raw_reads: payloads are escaped
        # (\\uXXXX) instead of Pattern-22 normalized. expose_sha: source
        # wrapper headers carry the payload SHA256.
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        self.raw_reads = bool(raw_reads)
        self.expose_sha = bool(expose_sha)
        self.ledger_path = ledger_path or os.path.join(run_dir, "calls.jsonl")
        self.sentinel = None       # set per segment via new_segment()
        self.segment = 0
        self.sources = []          # registered source dicts (this LEG)
        self.segment_refs = set()  # refs registered THIS SEGMENT
        self.claims = []           # validated claims THIS SEGMENT
        self.open_items = []       # remaining WORK (keeps the leg alive)
        self.not_found = []        # explicit NEGATIVES (a deliverable, not work)
        self.escalations = []      # ask_frontier questions, leg-wide
        self.pending_escalation = None   # set by t_ask_frontier; driver pauses on it
        self.proposed_edits = []   # propose_edit channel, leg-wide (edit role)
        # (entity, metric) pairs that failed record-time grounding. Drives the
        # second-miss escalation nudge in t_record_claim; bounded so a looping
        # leg cannot grow it without limit.
        self.grounding_misses = []
        self.counters = {"tool_calls": 0, "fetches": 0, "mcp_calls": 0,
                         "refusals": 0, "unknown_tool": 0, "scratch_files": 0,
                         "escalations": 0, "grounding_refusals": 0}
        self.injection_flags = []
        self.blocked = load_blocked_domains()
        self.mcp = None            # McpPool, attached by the driver
        allowed = set(self.cfg.get("mcp_allowlist") or [])
        mission_allowed = mission.get("allowed_mcp")
        if mission_allowed is not None:
            allowed &= set(mission_allowed)
        self.mcp_allowed = sorted(allowed)

    # ------------------------------------------------------------- ledger
    def _log(self, kind, tool, detail, allowed):
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "segment": self.segment,
               "kind": kind, "tool": tool, "allowed": bool(allowed),
               "detail": str(detail)[:400]}
        try:
            with open(self.ledger_path, "a", encoding="ascii", errors="replace") as fh:
                fh.write(json.dumps(row, ensure_ascii=True) + "\n")
        except OSError:
            pass
        return row

    # ---------------------------------------------------------- lifecycle
    def new_segment(self):
        self.segment += 1
        self.sentinel = "CTX-" + uuid.uuid4().hex[:8]
        self.segment_refs = set()
        self.claims = []
        return self.sentinel

    # ---------------------------------------------------- boundary pipeline
    def _repr(self, text):
        """The MODEL-VISIBLE representation of a payload (pre-sentinel-wrap):
        escaped under raw_reads roles, Pattern-22 normalized otherwise. The
        spill file holds THIS representation so record-time grounding and
        relay-verify match against exactly what the model could have read
        (Fable-review F-1). Source sha256 stays over RAW text (provenance)."""
        return self._escape(text) if self.raw_reads else ascii_normalize(text)

    def _escape(self, text):
        """Reversible ASCII projection: non-ASCII -> \\uXXXX, backslash doubled.
        Context stays pure ASCII; the original bytes stay expressible (the
        propose_edit byte-exactness requirement)."""
        out = []
        for ch in text:
            if ch == "\\":
                out.append("\\\\")
            elif ord(ch) > 127:
                out.append("\\u%04x" % ord(ch))
            else:
                out.append(ch)
        return "".join(out)

    def _register(self, kind, locator, text, ssl_verified=True, flags=None):
        ref = "R-%02d" % (len(self.sources) + 1)
        sha = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
        spill_name = "%s-%s.txt" % (ref, kind)
        spill_path = os.path.join(self.scratch, spill_name)
        try:
            with open(spill_path, "w", encoding="ascii", errors="replace") as fh:
                fh.write(self._repr(text))
        except OSError:
            spill_path = None
        inj = [p.pattern[:40] for p in INJECTION_PATTERNS if p.search(text)]
        src = {"ref": ref, "kind": kind, "locator": locator[:400],
               "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "bytes": len(text), "sha256": sha, "ssl_verified": ssl_verified,
               "scratch_path": spill_path, "injection_flags": inj}
        if flags:
            src["injection_flags"] = sorted(set(inj) | set(flags))
        self.sources.append(src)
        self.segment_refs.add(ref)
        if inj:
            self.injection_flags.append({"ref": ref, "patterns": inj})
        return src

    def _wrap(self, src, text, cap_chars):
        body = self._repr(text)
        body = body.replace(self.sentinel, "")           # strip THEN wrap
        truncated = len(body) > cap_chars
        if truncated:
            body = body[:cap_chars] + "\n[TRUNCATED at %d chars; full payload at %s]" % (
                cap_chars, src.get("scratch_path"))
        suspect = "INJECTION-SUSPECT\n" if src["injection_flags"] else ""
        shaline = " SHA256:%s" % src["sha256"] if self.expose_sha else ""
        return ("<<<%s>>>\nSOURCE: %s [%s]%s\n%s%s\n<<</%s>>>" % (
            self.sentinel, src["locator"], src["ref"], shaline, suspect, body,
            self.sentinel))

    # -------------------------------------------------------------- tools
    def t_fetch_url(self, args):
        if self.blocked is None:
            raise Refusal("fetch_url disabled: canonical source-policy blocked-domain parse "
                          "failed its floor -- fail-closed")
        if self.counters["fetches"] >= self.budget("max_fetches"):
            raise Refusal("max_fetches budget reached")
        url = str(args.get("url") or "")
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https"):
            raise Refusal("scheme %r refused (http/https only)" % parts.scheme)
        chain, final_url, text, ssl_ok = self._follow(url)
        self.counters["fetches"] += 1
        src = self._register("url", final_url, text, ssl_verified=ssl_ok)
        cap = int(self.budget("max_result_tokens") * 3)      # chars ~ 3x tokens floor
        return self._wrap(src, text, min(cap, 72000))

    def _host_refused(self, host):
        host = (host or "").lower().rstrip(".")
        try:
            host = host.encode("idna").decode("ascii")
        except Exception:                                     # noqa: BLE001
            return "hostname %r failed IDNA normalization" % host
        for b in self.blocked:
            if host == b or host.endswith("." + b):
                return "domain %r is on the canonical source-policy blocked list" % host
        if host.endswith(".local") or host == "localhost":
            return "local hostname refused"
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError as exc:
            return "DNS resolution failed: %s" % exc
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast):
                return "resolved address %s is private/loopback/link-local (SSRF guard)" % ip
        return None

    def _follow(self, url, max_hops=3):
        """Manual redirect walk: EVERY hop re-validated. No auth headers ever."""
        ssl_ok = True
        chain = []
        for _hop in range(max_hops + 1):
            parts = urllib.parse.urlsplit(url)
            why = self._host_refused(parts.hostname)
            if why:
                raise Refusal(why)
            chain.append(url)
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (osanwe-relay research)"})
            opener = urllib.request.build_opener(_NoRedirect())
            try:
                resp = opener.open(req, timeout=60)
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    loc = e.headers.get("Location")
                    if not loc:
                        raise Refusal("redirect with no Location")
                    url = urllib.parse.urljoin(url, loc)
                    continue
                raise Refusal("HTTP %d at %s" % (e.code, url))
            except ssl.SSLError:
                # ONE in-process unverified retry (AGENTS.md curl -sk rule,
                # without a shell); recorded on the source.
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                try:
                    resp = urllib.request.urlopen(req, timeout=60, context=ctx)
                    ssl_ok = False
                except Exception as exc:                      # noqa: BLE001
                    raise Refusal("fetch failed after SSL retry: %s" % exc)
            except Exception as exc:                          # noqa: BLE001
                raise Refusal("fetch failed: %s" % exc)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if not any(t in ctype for t in ("text/", "application/json",
                                            "application/xml", "xhtml")):
                raise Refusal("content-type %r refused" % ctype[:60])
            raw = resp.read(524288).decode("utf-8", "replace")
            if "html" in ctype:
                raw = TAG_RE.sub(" ", raw)
            raw = WS_RE.sub(" ", raw)
            raw = re.sub(r"\n{3,}", "\n\n", raw)
            return chain, url, raw, ssl_ok
        raise Refusal("more than %d redirects" % max_hops)

    def t_mcp_call(self, args):
        if self.counters["mcp_calls"] >= self.budget("max_mcp_calls"):
            raise Refusal("max_mcp_calls budget reached")
        server = str(args.get("server") or "")
        tool = str(args.get("tool") or "")
        targs = args.get("args")
        if any(f in server.lower() for f in ("robinhood", "claudewatch")):
            raise Refusal("server %r is refused by name (D-SEC-1)" % server)
        if server not in self.mcp_allowed:
            raise Refusal("server %r not in allowlist %s" % (server, self.mcp_allowed))
        if self.mcp is None:
            raise Refusal("MCP pool not attached")
        if not isinstance(targs, dict):
            targs = {}
        from relay_mcp import McpError                       # sibling module
        try:
            out = self.mcp.call(server, tool, targs)
        except McpError as exc:
            raise Refusal(str(exc))
        self.counters["mcp_calls"] += 1
        src = self._register("mcp", "%s:%s %s" % (
            server, tool, json.dumps(targs, ensure_ascii=True)[:120]), out)
        # exact re-execution seam for relay-verify (the locator truncates args
        # at 120 chars; this records the full call)
        src["call_args"] = {"server": server, "tool": tool, "args": targs}
        cap = int(self.budget("max_result_tokens") * 3)
        return self._wrap(src, out, min(cap, 72000))

    # ------------------------------------------------------ vault reads
    def _jail(self, path):
        """Resolve and check. Returns absolute path or raises Refusal."""
        if not isinstance(path, str) or not path.strip():
            raise Refusal("empty path")
        cand = path if os.path.isabs(path) else os.path.join(VAULT, path)
        real = os.path.realpath(cand)                        # junctions resolved
        vault_real = os.path.realpath(VAULT)
        try:
            common = os.path.commonpath([real.lower(), vault_real.lower()])
        except ValueError:
            raise Refusal("path %r is on a different drive" % path)
        if common != vault_real.lower():
            raise Refusal("path %r escapes the vault" % path)
        rel = os.path.relpath(real, vault_real).lower()
        for d in READ_EXCLUDE_DIRS:
            dl = d.lower()
            if rel == dl or rel.startswith(dl + os.sep):
                raise Refusal("path %r is in the excluded tree %r" % (path, d))
        for suf in READ_EXCLUDE_SUFFIX:
            if rel.endswith(suf):
                raise Refusal("path %r matches excluded suffix %r" % (path, suf))
        for part in rel.split(os.sep):
            if (part in READ_EXCLUDE_NAMES
                    or part.startswith(READ_EXCLUDE_NAME_PREFIXES)
                    or any(c in part for c in READ_EXCLUDE_NAME_CONTAINS)
                    or part.endswith(READ_EXCLUDE_NAME_SUFFIXES)):
                raise Refusal("path %r contains the excluded name %r" % (path, part))
        return real

    def t_read_file(self, args):
        real = self._jail(str(args.get("path") or ""))
        if not os.path.isfile(real):
            raise Refusal("not a file: %r" % args.get("path"))
        with open(real, encoding="utf-8", errors="replace") as fh:
            text = fh.read(262144)
        src = self._register("file", os.path.relpath(real, VAULT), text)
        cap = int(self.budget("max_result_tokens") * 3)
        return self._wrap(src, text, min(cap, 48000))

    def t_list_dir(self, args):
        real = self._jail(str(args.get("path") or "."))
        if not os.path.isdir(real):
            raise Refusal("not a directory: %r" % args.get("path"))
        entries = sorted(os.listdir(real))[:200]
        out = "\n".join(entries)
        src = self._register("dir", os.path.relpath(real, VAULT), out)
        return self._wrap(src, out, 8000)

    def t_grep_vault(self, args):
        pattern = str(args.get("pattern") or "")
        globpat = str(args.get("glob") or "**/*.md")
        if not pattern:
            raise Refusal("empty pattern")
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            raise Refusal("bad regex: %s" % exc)
        import glob as _glob
        hits = []
        for p in _glob.iglob(os.path.join(VAULT, globpat), recursive=True):
            try:
                real = self._jail(p)
            except Refusal:
                continue
            if not os.path.isfile(real):
                continue
            try:
                with open(real, encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        if rx.search(line):
                            hits.append("%s:%d: %s" % (
                                os.path.relpath(real, VAULT), i, line.strip()[:200]))
                            if len(hits) >= 200:
                                break
            except OSError:
                continue
            if len(hits) >= 200:
                break
        out = "\n".join(hits) or "(no matches)"
        src = self._register("grep", "grep %r %r" % (pattern[:60], globpat), out)
        return self._wrap(src, out, 24000)

    # -------------------------------------- scratch + accumulators
    def t_scratch_write(self, args):
        name = str(args.get("name") or "")
        if not SCRATCH_NAME_RE.match(name):
            raise Refusal("name %r fails grammar ^[A-Za-z0-9._-]{1,64}$" % name)
        if self.counters["scratch_files"] >= self.budget("scratch_files_per_leg"):
            raise Refusal("scratch file cap reached")
        content = ascii_normalize(str(args.get("content") or ""))
        if len(content) > self.budget("scratch_file_bytes"):
            raise Refusal("content exceeds per-file byte cap")
        with open(os.path.join(self.scratch, name), "w", encoding="ascii",
                  errors="replace") as fh:
            fh.write(content)
        self.counters["scratch_files"] += 1
        return "written scratch/%s (%d bytes)" % (name, len(content))

    def t_scratch_read(self, args):
        name = str(args.get("name") or "")
        if not SCRATCH_NAME_RE.match(name):
            raise Refusal("name %r fails grammar" % name)
        p = os.path.join(self.scratch, name)
        if not os.path.isfile(p):
            raise Refusal("no such scratch file %r" % name)
        offset = int(args.get("offset") or 0)
        length = min(int(args.get("length") or 24000), 48000)
        with open(p, encoding="ascii", errors="replace") as fh:
            fh.seek(max(0, offset))
            return fh.read(length)

    def t_record_claim(self, args):
        from relay_schema import validate_claim
        claim = args.get("claim") if isinstance(args.get("claim"), dict) else args
        claim = {k: v for k, v in claim.items() if k != "claim"}
        # normalize "[R-02]" -> "R-02" (pilot001: 6 bracket-form refusals; the
        # wrapper renders refs as [R-nn], so accepting both forms is correct)
        sr = claim.get("source_ref")
        if isinstance(sr, str):
            claim["source_ref"] = sr.strip().strip("[]")
        # LEG-wide ref validation, not segment-scoped: refs are unique R-nn rows in
        # sources[], so a fabricated citation is still impossible -- but a claim
        # recorded AFTER a relay from a source fetched BEFORE it stays valid
        # (protocol gap exposed by suite case T5a, 2026-08-16).
        leg_refs = {s["ref"] for s in self.sources}
        errs = validate_claim(claim, leg_refs)
        if errs:
            raise Refusal("claim rejected: " + "; ".join(errs[:4]))
        src = next(s for s in self.sources if s["ref"] == claim["source_ref"])
        # RECORD-TIME GROUNDING (GATE-B gate-b-local-orchestration-program;
        # Fable-review fix 1 + F-1/F-2): the claimed value must OCCUR in the
        # cited source's spilled payload (the model-visible representation).
        # Fabrication becomes impossible at construction; the byte-offset
        # witness makes relay-verify an O(1) seek. Spill failure degrades
        # honestly -- a disk hiccup must not refuse honest claims.
        from relay_schema import value_occurs
        spill = src.get("scratch_path")
        if spill and os.path.isfile(spill):
            try:
                with open(spill, encoding="ascii", errors="replace") as fh:
                    payload = fh.read()
            except OSError:
                payload = None
            if payload is None:
                claim["witness"] = "spill-failed"
            else:
                found, off, ln = value_occurs(claim["value"], payload)
                if not found:
                    self.counters["grounding_refusals"] += 1
                    # A grounding refusal was a DEAD END: the worker was told
                    # what it may not do and nothing about what to do instead,
                    # so it guessed again. Measured 2026-08-17 on a production
                    # /invest: 24 grounding refusals, ZERO escalations, with the
                    # escalation budget untouched -- and the two legs that
                    # yielded nothing were exactly the ones an escalation would
                    # have rescued. On the SECOND miss for the same
                    # (entity, metric) the refusal now names both exits.
                    key = (claim.get("entity", ""), claim.get("metric", ""))
                    if len(self.grounding_misses) < 50:
                        self.grounding_misses.append(key)
                    repeat = self.grounding_misses.count(key)
                    extra = ""
                    if repeat >= 2:
                        extra = (" || You have now failed to ground %r twice. "
                                 "Do NOT try a third variant. If the source "
                                 "genuinely does not print this value, call "
                                 "record_negative. If the mission REQUIRES a "
                                 "value no source prints, call ask_frontier "
                                 "(question, tried, context_refs)."
                                 % (claim.get("metric", "")[:40],))
                    raise Refusal(
                        "claim value %r does not occur in [%s]'s payload -- "
                        "record what the source actually prints (K/M/B scale "
                        "and %% forms are recognized); derived or combined "
                        "values go to the narrative or note_open_item, never "
                        "record_claim%s" % (claim["value"][:60],
                                            claim["source_ref"], extra))
                claim["witness"] = "%s:%d:%d" % (
                    os.path.basename(spill), off, ln)
        else:
            claim["witness"] = "spill-failed"
        if src["injection_flags"]:
            claim["injection_suspect"] = True
        self.claims.append(claim)
        return "claim %d recorded" % len(self.claims)

    def t_note_open_item(self, args):
        text = ascii_normalize(str(args.get("text") or ""))[:400]
        if not text:
            raise Refusal("empty open item")
        item = {"id": "O-%d" % (len(self.open_items) + 1), "text": text}
        na = args.get("next_action")
        if isinstance(na, dict):
            item["next_action"] = {k: str(v)[:120] for k, v in list(na.items())[:6]}
        self.open_items.append(item)
        return "%s noted" % item["id"]

    def t_ask_frontier(self, args):
        """Mid-leg escalation to the frontier orchestrator (GATE-B
        gate-b-ask-frontier-2026-08-16). EXECUTOR-VALIDATED: the question must
        cite [R-nn] refs that resolve to real tool results from this leg AND
        state what was attempted -- a lazy punt is structurally unexpressible.
        On success the driver pauses the leg (status awaiting-guidance); the
        answer returns next segment as ORCHESTRATOR GUIDANCE with prov frontier."""
        if self.counters["escalations"] >= self.budget("max_escalations_per_leg"):
            raise Refusal("escalation budget reached (max_escalations_per_leg "
                          "= %d) -- finish with what you have; record_negative "
                          "what remains unanswerable"
                          % self.budget("max_escalations_per_leg"))
        q = ascii_normalize(str(args.get("question") or "")).strip()
        tried = ascii_normalize(str(args.get("tried") or "")).strip()
        refs = args.get("context_refs")
        if len(q) < 20:
            raise Refusal("question too thin: state ONE specific decision or "
                          "unknown (>= 20 chars)")
        if len(tried) < 20:
            raise Refusal("tried too thin: state what you already attempted "
                          "(>= 20 chars) -- an escalation without attempts is "
                          "a punt")
        if isinstance(refs, str):
            refs = [refs]
        if not isinstance(refs, list) or not refs:
            raise Refusal("context_refs required: cite the [R-nn] tool results "
                          "that frame the question")
        norm = [str(r).strip().strip("[]") for r in refs][:8]
        known = {s["ref"] for s in self.sources}
        bad = [r for r in norm if r not in known]
        if bad:
            raise Refusal("context_refs %s do not name tool results from this "
                          "leg (known: %s) -- gather context BEFORE escalating"
                          % (bad, sorted(known)[:12]))
        self.counters["escalations"] += 1
        esc = {"id": "Q-%02d" % self.counters["escalations"],
               "question": q[:600], "tried": tried[:600], "context_refs": norm,
               "segment": self.segment, "answered": False}
        self.escalations.append(esc)
        self.pending_escalation = esc
        return ("escalation %s recorded -- the leg will pause for orchestrator "
                "guidance; stop calling tools" % esc["id"])

    def t_propose_edit(self, args):
        """Editor role's ONLY change channel (GATE-B program sheet; Fable
        fixes 3/F-5). Emits a PROPOSAL; the vault write happens (or not) at
        the frontier through the normal Edit + hook chain. Every refusal is a
        logged containment row."""
        if len(self.proposed_edits) >= self.budget("max_proposals_per_leg"):
            raise Refusal("proposal budget reached (max_proposals_per_leg)")
        path = str(args.get("path") or "")
        real = self._jail(path)
        rel = os.path.relpath(real, os.path.realpath(VAULT)).replace(
            os.sep, "/").lower()
        if any(rel.startswith(p) for p in PROPOSE_DENY_PREFIXES) or \
                not any(rel.startswith(p) for p in PROPOSE_ALLOW_PREFIXES):
            raise Refusal("path %r is outside the proposal allowlist "
                          "(Calendar/, wiki/ minus wiki/research/, Efforts/, "
                          "parity fixtures) -- doctrine/tooling/Atlas changes "
                          "are frontier-only; surface the defect via "
                          "note_open_item instead" % path)
        if not os.path.isfile(real):
            raise Refusal("not a file: %r" % path)
        if os.path.getsize(real) > 1048576:
            raise Refusal("file exceeds the propose window; split the mission")
        rel_case = os.path.relpath(real, os.path.realpath(VAULT)).replace(os.sep, "/")
        src = next((s for s in self.sources if s["kind"] == "file"
                    and s["locator"].replace("\\", "/") == rel_case), None)
        if src is None:
            raise Refusal("propose without read: read_file %r first (a "
                          "proposal must cite bytes you actually saw)" % path)
        sha_arg = str(args.get("before_sha256") or "").strip().lower()
        sha_now, content = file_sha_text(real)
        if sha_arg != src["sha256"] or sha_arg != sha_now:
            raise Refusal("stale: the file changed since your read (or the "
                          "sha you cited is not the one from your read's "
                          "SOURCE header) -- re-read it, then re-propose")
        old_esc = str(args.get("old") or "")
        new_esc = str(args.get("new") or "")
        cap = self.budget("propose_edit_max_chars")
        if not old_esc or len(old_esc) > cap or len(new_esc) > cap:
            raise Refusal("old empty or old/new exceed propose_edit_max_chars")
        old_apply = _unescape(old_esc)
        new_apply = _unescape(new_esc)
        if any(ord(ch) > 127 for ch in new_apply):
            raise Refusal("new must be pure ASCII (Pattern 22: -- for dashes, "
                          "straight quotes, -> for arrows)")
        n = content.count(old_apply)
        if n == 0:
            raise Refusal("old not found verbatim in the file (copy the "
                          "\\uXXXX escapes from your read exactly)")
        if n > 1:
            raise Refusal("old occurs %d times; extend surrounding context "
                          "until unique" % n)
        why = ascii_normalize(str(args.get("why") or "")).strip()[:300]
        if len(why) < 15:
            raise Refusal("why too thin: name the RULE the fix serves "
                          "(Pattern 22, frontmatter schema, dedup target...)")
        pe = {"id": "PE-%02d" % (len(self.proposed_edits) + 1),
              "path": rel_case, "before_sha256": sha_now,
              "old": old_esc, "new": new_esc, "why": why,
              "segment": self.segment}
        self.proposed_edits.append(pe)
        return "%s proposed against %s" % (pe["id"], pe["path"])

    def t_record_negative(self, args):
        """Explicit not-found: a DELIVERABLE negative result, distinct from
        open_items (remaining work). pilot001 exposed the conflation: negatives
        recorded as open items kept the leg alive to max_segments."""
        q = ascii_normalize(str(args.get("question") or ""))[:300]
        if not q:
            raise Refusal("empty question")
        entry = {"question": q,
                 "searched": [ascii_normalize(str(s))[:120]
                              for s in (args.get("searched") or [])][:10],
                 "conclusion": ascii_normalize(
                     str(args.get("conclusion") or ""))[:300]}
        self.not_found.append(entry)
        return "negative %d recorded" % len(self.not_found)

    # ------------------------------------------------------------ dispatch
    TABLE = {
        "fetch_url": t_fetch_url, "mcp_call": t_mcp_call,
        "read_file": t_read_file, "list_dir": t_list_dir,
        "grep_vault": t_grep_vault, "scratch_write": t_scratch_write,
        "scratch_read": t_scratch_read, "record_claim": t_record_claim,
        "note_open_item": t_note_open_item, "record_negative": t_record_negative,
        "ask_frontier": t_ask_frontier, "propose_edit": t_propose_edit,
    }

    def budget(self, key):
        b = self.cfg.get("budgets") or {}
        # max_escalations_per_leg defaults in CODE so an unarmed config still
        # escalates (0 would silently disable the channel); config/mission may
        # override, and a mission may lower it to 0.
        merged = {"max_escalations_per_leg": 3, **b,
                  "max_result_tokens": self.cfg.get("max_result_tokens", 32768)}
        return merged.get(key, 0)

    def dispatch(self, name, args):
        """Returns (result_text, ok). Refusals come back as deterministic tool
        errors -- and land in the ledger either way."""
        if self.counters["tool_calls"] >= self.budget("max_tool_calls"):
            self.counters["refusals"] += 1
            self._log("refusal", name, "max_tool_calls budget reached", False)
            return "TOOL ERROR: max_tool_calls budget reached", False
        self.counters["tool_calls"] += 1
        fn = self.TABLE.get(name)
        if fn is None:
            self.counters["unknown_tool"] += 1
            self._log("unknown_tool", name, "no such tool", False)
            return ("TOOL ERROR: unknown tool %r. Available: %s" % (
                name, sorted(self.TABLE))), False
        if self.allowed_tools is not None and name not in self.allowed_tools:
            # ROLE FILTER: a real tool outside this role's allowlist is a
            # containment refusal (attempt visible on the ledger), never the
            # unknown-tool 3-strike path -- the tool exists, the role lacks it.
            self.counters["refusals"] += 1
            self._log("refusal", name,
                      "tool %r is outside this role's allowlist %s" % (
                          name, sorted(self.allowed_tools)), False)
            return "TOOL ERROR: tool %r is not available to this role" % name, False
        try:
            out = fn(self, args if isinstance(args, dict) else {})
            self._log("call", name, json.dumps(args, ensure_ascii=True,
                                               default=str)[:300], True)
            return out, True
        except Refusal as exc:
            self.counters["refusals"] += 1
            self._log("refusal", name, str(exc), False)
            return "TOOL ERROR: %s" % exc, False
        except Exception as exc:                              # noqa: BLE001
            self.counters["refusals"] += 1
            self._log("error", name, repr(exc)[:300], False)
            return "TOOL ERROR: internal: %s" % exc, False


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
