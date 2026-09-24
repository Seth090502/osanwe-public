#!/usr/bin/env python3
"""PreToolUse on Bash: refuse any command that opens a heredoc or here-string.

Why this exists. A heredoc in this environment does not merely risk mangling a
backslash -- it hangs. The shell waits on stdin that never arrives, the call has
to be abandoned, and once a half-written command ran anyway. It happened six
times across two nights against an explicit standing instruction not to use
them, the sixth to a reviewer who had just read the instruction. An instruction
broken six times is not a control.

HOW IT DECIDES, and why it is not a regex.

The first version of this hook matched a regex against text with single-quoted
runs stripped out. That is wrong in the one way that matters: `cat <<'EOF'`
loses its delimiter to the stripping, so what the pattern actually matched was
the first word of the heredoc BODY, by accident. Measured against 49,869 real
commands it missed 549 of 6,028 real heredocs -- every one of them the
single-quoted form, which is the dominant form in practice and the exact shape
that hung. Prepending one digit to the body flipped another 95% of the ones it
did catch.

So this walks the command left to right and tracks what the shell tracks:
backslash escapes, single quotes, double quotes, comments, and arithmetic
contexts. A `<<` or `<<<` reached in ordinary command position is a redirection
operator -- there is nothing further to validate, because in bash that IS the
operator whatever follows it. One inside quotes or arithmetic is not.

That also fixes the false positives the regex had: `python -c "print(x << n)"`,
`grep -rn "<<<<<<<" .` and `if (( x << 2 ))` are all ordinary work and all pass.

Block convention: exit 2 + stderr reason (Claude Code PreToolUse). Every error
is a block, including an empty payload.

The way through this hook is to write the script to a file and run the file --
which is what should have been happening anyway.
"""

import json
import sys

NORMAL, SQUOTE, DQUOTE, COMMENT = 0, 1, 2, 3


def find_heredoc(cmd):
    """(kind, index) of the first real heredoc/here-string operator, or None.

    kind is '<<<' or '<<'. Only operators reached in ordinary command position
    count: not inside quotes, not in a comment, not in an arithmetic context.
    """
    state = NORMAL
    arith = 0            # depth of (( ... )) or $(( ... ))
    i, n = 0, len(cmd)
    prev_significant = ""   # last non-space character seen in NORMAL state

    while i < n:
        c = cmd[i]

        if state == COMMENT:
            if c == "\n":
                state = NORMAL
            i += 1
            continue

        if state == SQUOTE:
            # Nothing is special inside single quotes, not even a backslash.
            if c == "'":
                state = NORMAL
            i += 1
            continue

        if state == DQUOTE:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                state = NORMAL
            i += 1
            continue

        # --- NORMAL ---
        if c == "\\":
            i += 2
            continue
        if c == "'":
            state = SQUOTE
            i += 1
            continue
        if c == '"':
            state = DQUOTE
            i += 1
            continue
        if c == "#" and (prev_significant in ("", "\n", ";", "|", "&", "(")
                         or (i > 0 and cmd[i - 1] in " \t\n")):
            state = COMMENT
            i += 1
            continue

        # Arithmetic: $(( ... )) and (( ... )). Inside these, << is a left shift.
        if cmd.startswith("$((", i) or cmd.startswith("((", i):
            arith += 1
            i += 3 if cmd.startswith("$((", i) else 2
            continue
        if arith and cmd.startswith("))", i):
            arith -= 1
            i += 2
            continue

        if arith == 0 and cmd.startswith("<<", i):
            # A here-string is <<<; a heredoc is << possibly followed by -.
            if cmd.startswith("<<<", i):
                return "<<<", i
            return "<<", i

        if not c.isspace():
            prev_significant = c
        elif c == "\n":
            prev_significant = "\n"
        i += 1

    return None


def block(reason, detail=""):
    sys.stderr.write("no-heredoc: BLOCKED -- %s\n" % reason)
    if detail:
        sys.stderr.write("  %s\n" % detail)
    sys.stderr.write(
        "  Heredocs hang this shell waiting on stdin. Write the script to a file\n"
        "  with the Write tool and run the file instead.\n")
    sys.exit(2)


def main():
    try:
        raw = sys.stdin.read()
    except Exception as e:                                   # noqa: BLE001
        block("could not read the tool payload (fail-closed): %s" % e)

    if not raw.strip():
        block("empty tool payload (fail-closed)")

    try:
        payload = json.loads(raw)
    except Exception as e:                                   # noqa: BLE001
        block("could not parse the tool payload (fail-closed): %s" % e)

    if not isinstance(payload, dict):
        block("tool payload is not an object (fail-closed)")

    name = payload.get("tool_name")
    if name is not None and not isinstance(name, str):
        block("tool_name is not a string (fail-closed)")
    if isinstance(name, str) and name.strip() != "Bash":
        # A genuinely different tool is not this hook's business. The matcher is
        # a regex search, so BashOutput and friends reach here too.
        sys.exit(0)

    tool_input = payload.get("tool_input")
    if tool_input is None:
        sys.exit(0)
    if not isinstance(tool_input, dict):
        block("tool_input is not an object (fail-closed)")

    cmd = tool_input.get("command")
    if cmd is None:
        sys.exit(0)
    if not isinstance(cmd, str):
        block("command is not a string (fail-closed)")

    hit = find_heredoc(cmd)
    if hit:
        kind, idx = hit
        line = cmd.count("\n", 0, idx) + 1
        block("the command opens a %s at line %d"
              % ("here-string (<<<)" if kind == "<<<" else "heredoc (<<)", line))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:                                   # noqa: BLE001
        sys.stderr.write("no-heredoc: BLOCKED -- unexpected error (fail-closed): %s\n" % e)
        sys.exit(2)
