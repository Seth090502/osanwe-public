"""Mode-3 system-message normalizer.

WHY THIS EXISTS (removal trigger inside): Ollama's built-in `RENDERER qwen3.8` accepts
exactly ONE system message, and only at position 0. Claude Code sends a top-level `system`
list AND a TRAILING system message after the user turn, so every mode-3 request is rejected
with `500 system message must be at the beginning` and retried to exhaustion.

Measured 2026-08-14 against 127.0.0.1:11434 (gate sheet:
wiki/research/gates/gate-b-mode3-system-message-normalizer-2026-08-14.md):
  one leading system message            -> accepted
  two leading system messages           -> rejected
  top-level system + a system message   -> rejected
  tools / tool_use / tool_result        -> already accepted, untouched here

So the ONLY defect is system-message arity. This adapter merges every system-role message
in `messages` into the single top-level `system` block and forwards everything else
verbatim. It makes no other change: no prompt authoring, no model selection, no judgment.

REMOVAL TRIGGER: the first Ollama release whose renderer tolerates Claude Code's message
shape retires this file. After any engine upgrade, re-run the one-line probe below against
the DAEMON (11434, not this proxy):

  curl -s -m 60 -X POST http://127.0.0.1:11434/v1/messages -H "content-type: application/json" \
    -d '{"model":"qwen3.8:27b","max_tokens":8,"system":"top","messages":[{"role":"user","content":"hi"},{"role":"system","content":"be terse"}]}'

If that returns a completion instead of `system message must be at the beginning`, the
engine is fixed: delete this file and set $inferenceHost back to $laneHost in
tools/claude-launcher.ps1.
"""
import argparse
import http.client
import http.server
import json
import os
import sys
import threading
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from anthropic_websearch import (            # noqa: E402
    is_web_search_request, build_blocks as build_web_search_blocks,
    extract_search_query, message_json as websearch_message_json,
    sse_events as websearch_sse_events,
)

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
}

_stats = {"seen": 0, "normalized": 0, "moved_messages": 0, "retuned": 0,
          "think_off": 0, "web_searches": 0}
_lock = threading.Lock()

# "system" (default) merges into the leading system block -- role-faithful, but places
# per-turn-varying bytes ahead of every user turn and kills prefix-cache reuse.
# "tail" appends to the last user turn -- keeps the prefix stable. Set MODE3_PLACEMENT.
PLACEMENT = os.environ.get("MODE3_PLACEMENT", "system").strip().lower()

# Sampling profile. DEFAULT CHANGED 2026-09-02 from an injected 0.6 to no injection at all
# ("off"), on first-party evidence. This reverses an earlier reading recorded here, so the
# reasoning is kept rather than quietly replaced.
#
# The old comment argued Qwen shipped a hybrid matching neither published profile, and that
# temp 0.6 was the correct "coding" choice. That was guidance for the ORIGINAL Qwen3
# generation (Qwen3-32B, Qwen3-Thinking-2507 et al., all documented at temp 0.6). Qwen
# RAISED the thinking-mode temperature starting with the Qwen3.5/3.6 hybrid architecture,
# and Qwen3.8's own model card publishes, for thinking mode:
#     temperature 1.0, top_p 0.95, top_k 20, min_p 0.0, presence_penalty 0.0, repeat 1.0
# which is EXACTLY what this tag's Modelfile already ships (verified via /api/show). So the
# injection was overriding the vendor's tested profile with a superseded one, on 100% of
# mode-3 traffic (the health counter showed retuned == seen).
#
# These values are a MATCHED SET. Changing temperature alone while leaving presence_penalty
# and repetition_penalty at their thinking-mode values is a combination Qwen never
# validated; the vendor's own lower-temperature profile is the NON-thinking one
# (0.7 / 0.80 / 20 / 0 / 1.5 / 1.0), not 0.6 in isolation.
#
# The one measured argument for 0.6 is SPEED, not quality: MTP draft acceptance was 0.756 at
# 0.6 vs 0.641 at 1.0. That is inherent to speculative decoding -- a more peaked target
# distribution is easier for the draft head to match -- and says nothing about output
# quality. Set MODE3_TEMP=0.6 to restore the old behaviour and buy that throughput back;
# tools/lane-bench.py prices the difference.
_t = os.environ.get("MODE3_TEMP", "off").strip().lower()
TEMP = None if _t in ("off", "none", "") else float(_t)

# Thinking control. DEFAULT IS "on" (= do not override Claude Code's adaptive setting),
# and that default is a REVERSAL of what shipped earlier the same day. Recorded because the
# original reasoning was plausible and wrong.
#
# The argument for disabling was: delegate.py:565 already sends "think": False for delegated
# legs, mode 3's banner says keep work MECHANICAL, and thinking tokens are pure decode
# latency. MEASURED 2026-08-15 on an identical arithmetic task, that last clause is false --
# with thinking OFF the model reasons in the visible answer instead, and TOTAL output grows:
#
#   thinking mode                      thinking_chars   total output tokens   correct
#   {"type":"adaptive"}  (CC default)       193                192              yes
#   {"type":"disabled"}                       0                366              yes
#   {"type":"enabled","budget_tokens":512}  206                255              yes
#   {"type":"enabled","budget_tokens":2048}  199                176              yes
#
# Disabling nearly DOUBLED output tokens. Adaptive was the cheapest run and is what Claude
# Code already sends, so the correct action is to leave it alone.
#
# Also learned: `budget_tokens` is INERT here -- 512 and 2048 both produce ~200 thinking
# chars, so a graduated "medium thinking" dial does not exist for this model on Ollama; it
# self-regulates. And Ollama's own `{"think": false}` is silently IGNORED on /v1/messages;
# only `{"thinking":{"type":"disabled"}}` has any effect.
#
# MODE3_THINK=off re-enables the suppression for anyone who wants to re-test it.
THINK = os.environ.get("MODE3_THINK", "on").strip().lower() not in ("off", "0", "false")


def _as_blocks(content):
    """Anthropic content -> list of content blocks."""
    if content is None:
        return []
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return list(content)
    return [{"type": "text", "text": str(content)}]


def normalize(body):
    """Merge every system-role message in `messages` into the top-level `system` block.

    Returns (body, moved_count). Leaves the body untouched when there is nothing to
    move, and refuses to empty the messages array (an all-system request is upstream's
    error to report, not ours to invent a fix for).

    WHY THE TOP-LEVEL `system` BLOCK AND NOT THE TAIL -- recorded because the alternative
    was built, measured, and REJECTED on evidence rather than reasoned away:

      Hypothesis: hoisting a per-turn-varying reminder to position 0 rewrites the prompt
      prefix every turn and busts llama.cpp's longest-common-prefix KV cache, so appending
      it to the last user turn instead should preserve the ~50k-token stable prefix
      (system + 115 tool definitions + prior turns).

      Measured: it did NOT restore cache reuse. Prompt eval stayed at 55,838 then 58,191
      tokens, ~22 s per turn, same as hoisting. The reason is that Claude Code re-emits the
      reminder at the END of the list on EVERY request, so the block MOVES relative to
      history -- request 1 has it after the first user turn, request 2 has an assistant
      turn there instead. Divergence is unavoidable at that point under either placement.

    CORRECTION ON THE RECORD: mid-diagnosis the tail variant was called a HANG and reverted
    on that basis. That was wrong -- the run completed with exit 0 and the correct answer,
    it was merely slow (~5-6 min for a 3-turn task). Both variants work end-to-end. The
    revert stands on the measurement above (no cache benefit), NOT on the hang claim, and
    the two runs were uncontrolled single samples that do not establish a latency ordering.

    Hoisting is kept because it is the semantically faithful option -- system content stays
    system -- and it carries two clean end-to-end runs. The ~22 s/turn prompt eval is an
    inherent cost of driving a 55k-token vault context through a local model; it is NOT
    introduced by this proxy and is not fixable here.
    """
    msgs = body.get("messages")
    if not isinstance(msgs, list):
        return body, 0

    kept, moved_blocks, moved = [], [], 0
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "system":
            moved_blocks.extend(_as_blocks(m.get("content")))
            moved += 1
        else:
            kept.append(m)

    if not moved:
        return body, 0
    if not kept:
        # Every message was a system message. Forwarding unchanged keeps upstream's
        # error honest rather than fabricating a user turn.
        return body, 0

    if PLACEMENT == "tail":
        # Append to the LAST user turn instead of the system block. Claude Code's trailing
        # system message changes nearly every turn; putting it in the system block places
        # varying bytes BEFORE every user turn, so llama.cpp's longest-common-prefix cache
        # diverges there and re-evaluates the whole prompt. Measured 2026-08-15: vault turn 2
        # re-evaluated 58,728 tokens (22.8 s) while a bare directory, same engine and model,
        # reused its prefix and processed only 663 (0.35 s).
        tagged = []
        for b in moved_blocks:
            if isinstance(b, dict) and b.get("type") == "text":
                b = dict(b)
                b["text"] = "<system-message>\n%s\n</system-message>" % b.get("text", "")
            tagged.append(b)
        last = kept[-1]
        if isinstance(last, dict) and last.get("role") == "user":
            last = dict(last)
            last["content"] = _as_blocks(last.get("content")) + tagged
            kept[-1] = last
        else:
            kept.append({"role": "user", "content": tagged})
        body["messages"] = kept
        return body, moved

    body["messages"] = kept
    body["system"] = _as_blocks(body.get("system")) + moved_blocks
    return body, moved


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    upstream = ("127.0.0.1", 11434)

    def log_message(self, *a):
        pass  # the launcher owns the log file; per-request noise is not useful

    def _relay(self, method):
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b""

        if raw and self.path.startswith("/v1/messages"):
            try:
                body = json.loads(raw)
                # WEB SEARCH (added 2026-09-02). Claude Code's WebSearch is Anthropic's
                # SERVER-side web_search_20250305: it cannot execute against Ollama, and it
                # fails SILENTLY -- the model then answers from stale weights believing it
                # searched. Answer the inner turn locally from SearXNG instead. Ollama is
                # not called for these; running a search is not inference, and a local 27B's
                # prefill is the most expensive thing on this lane to waste.
                if is_web_search_request(body):
                    self._handle_web_search(body)
                    return
                body, moved = normalize(body)
                retuned = False
                if TEMP is not None and body.get("temperature") != TEMP:
                    body["temperature"] = TEMP
                    body.setdefault("top_p", 0.95)
                    retuned = True
                # OVERRIDE, do not defer: Claude Code always sends
                # {"type": "adaptive", "display": "omitted"}, so an `if "thinking" not in
                # body` guard silently never fires (measured: think_off stayed 0).
                if not THINK and (body.get("thinking") or {}).get("type") != "disabled":
                    body["thinking"] = {"type": "disabled"}
                    retuned = True
                    with _lock:
                        _stats["think_off"] += 1
                if moved or retuned:
                    raw = json.dumps(body).encode("utf-8")
                    with _lock:
                        if moved:
                            _stats["normalized"] += 1
                            _stats["moved_messages"] += moved
                        if retuned:
                            _stats["retuned"] += 1
            except (ValueError, TypeError):
                pass  # not JSON we understand -- forward untouched
            with _lock:
                _stats["seen"] += 1

        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in HOP_BY_HOP}
        if raw:
            headers["Content-Length"] = str(len(raw))

        conn = http.client.HTTPConnection(*self.upstream, timeout=900)
        try:
            conn.request(method, self.path, body=raw or None, headers=headers)
            resp = conn.getresponse()

            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() not in HOP_BY_HOP:
                    self.send_header(k, v)
            # Stream: Claude Code sets stream=true and the response is SSE. Chunked
            # relay keeps tokens flowing instead of buffering the whole completion.
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            # Line-based, NOT read(8192). Claude Code sets stream=true and the response is
            # SSE; a fixed-size read holds each event until 8 KB accumulates, which delays
            # token delivery for no benefit. readline returns at each event boundary and
            # still terminates cleanly at EOF.
            # HONEST SCOPE: this was first written to fix an apparent hang. It was not a
            # hang -- the run completed with exit 0 and the right answer, just slowly. The
            # 8 KB version is not known to break anything; line-based is kept because it is
            # the correct shape for SSE, not because it repaired a failure.
            for line in resp:
                self.wfile.write(b"%X\r\n%s\r\n" % (len(line), line))
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except Exception as e:
            try:
                payload = json.dumps({
                    "type": "error",
                    "error": {"type": "api_error",
                              "message": "normalizer upstream failure: %s" % e},
                }).encode()
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception:
                pass
        finally:
            conn.close()

    # --- local web search -------------------------------------------------------------
    def _send_json(self, status, obj):
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _emit_sse(self, name, obj):
        data = ("event: %s\ndata: %s\n\n" % (name, json.dumps(obj))).encode("utf-8")
        self.wfile.write(b"%X\r\n%s\r\n" % (len(data), data))
        self.wfile.flush()

    def _handle_web_search(self, body):
        model = body.get("model") or "local"
        streaming = bool(body.get("stream"))
        query = extract_search_query(body)
        try:
            blocks, summary = build_web_search_blocks(query)
        except Exception as e:                      # search must never break the session
            blocks = [{"type": "text", "text": "Web search is unavailable: %s" % e}]
            summary = "error=%s" % e
        with _lock:
            _stats["web_searches"] = _stats.get("web_searches", 0) + 1
        sys.stderr.write("normalizer: WEBSEARCH %s stream=%d\n" % (summary, int(streaming)))
        sys.stderr.flush()

        if not streaming:
            self._send_json(200, websearch_message_json(blocks, model))
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for name, payload in websearch_sse_events(blocks, model):
            self._emit_sse(name, payload)
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def do_POST(self):
        self._relay("POST")

    def do_GET(self):
        if self.path == "/__normalizer/health":
            payload = json.dumps(dict(_stats, ok=True)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self._relay("GET")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=11435)
    ap.add_argument("--upstream", default="http://127.0.0.1:11434")
    a = ap.parse_args()

    u = urllib.parse.urlparse(a.upstream)
    Handler.upstream = (u.hostname or "127.0.0.1", u.port or 11434)

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.daemon_threads = True
    sys.stderr.write("normalizer: 127.0.0.1:%d -> %s:%d\n"
                     % (a.port, Handler.upstream[0], Handler.upstream[1]))
    sys.stderr.flush()
    srv.serve_forever()


if __name__ == "__main__":
    main()
