#!/usr/bin/env python3
"""pit_join.py -- Point-in-time (PIT) availability-aware as-of join.

The single sanctioned join for PIT consumers. Right-side rows carry BOTH:

  * an effective date   -- named by ``on`` (the business/as-of key)
  * an availability ts  -- named by ``availability_key`` (when the row
                           became knowable to a consumer)

Invariant enforced here: a left row stamped at time T may only be joined
to right rows whose availability <= T.  Anything later is look-ahead
leakage and is never exposed, regardless of input ordering.

Semantics
---------
For each left row L with key value t = L[on] (and group g = L[by] if
``by`` is given):

  1. Candidate pool = right rows R where
       R[availability_key] <= t            (knowable at T)
       R[on]                <= t           (effective at or before T)
       (by matches, when ``by`` is set)
  2. Among candidates, pick the one maximizing (R[on], R[availability_key]):
     latest effective date, then latest revision of that effective date
     (revisions = same effective date re-published at later availability).
  3. If max_lookback is set (a timedelta, or anything supporting
     subtraction/comparison against the difference of two key values),
     drop candidates where t - R[on] > max_lookback BEFORE picking.
  4. If no candidate survives, the left row is emitted with the marker
     field (default ``_pit_miss=True``) and no right fields attached.

Inputs need NOT be sorted (out-of-order arrival is fine); both streams
are sorted internally. Inputs are not mutated. Keys use one homogeneous axis: ISO dates/date objects, timezone-aware
timestamps normalized to UTC, or finite numeric synthetic indexes. Naive
timestamps and mixed date/timestamp/numeric axes are refused. Date-only keys
carry day-level semantics; they cannot certify intraday availability.

CLI
---
    python pit_join.py --selftest

runs a fuzz test (2000 randomized left/right pairs including ties,
out-of-order arrival, and revisions) and programmatically asserts the
leakage property: no joined row ever exposes a right-side row whose
availability exceeds the left row's time. Exit code 0 == pass.

ASCII only. Stdlib only. No network. Python >= 3.8.
"""

from __future__ import annotations

import argparse
import bisect
import random
import sys
import math
from datetime import date, datetime, timedelta, timezone

__all__ = ["join_asof", "JoinConfigError"]

MISSING_FIELD_MSG = "row missing required key"


class JoinConfigError(ValueError):
    """Raised for bad configuration (missing keys, incomparable fields)."""


def _check_keys(rows, keys, what):
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise JoinConfigError("%s[%d] is not a dict" % (what, i))
        missing = [k for k in keys if k not in r]
        if missing:
            raise JoinConfigError(
                "%s[%d]: %s %r" % (what, i, MISSING_FIELD_MSG, missing))


def _time_key(value):
    """Compare actual instants, never the lexical spelling of UTC offsets.

    Date-only axes remain date-only; they cannot establish intraday availability.
    Aware timestamps normalize to UTC. Numeric axes are for synthetic/discrete
    indexes. Mixing these three domains or using a naive timestamp is refused.
    """
    if isinstance(value, bool):
        raise JoinConfigError("boolean is not a time key")
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise JoinConfigError("time key must be finite")
        return "numeric", value
    if isinstance(value, str):
        try:
            if len(value) == 10:
                parsed = date.fromisoformat(value)
                if parsed.isoformat() != value:
                    raise ValueError("noncanonical date")
                return "date", parsed
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise JoinConfigError("time strings must be ISO dates or aware timestamps") from exc
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise JoinConfigError("timestamp requires an explicit UTC offset")
        return "timestamp", value.astimezone(timezone.utc)
    if isinstance(value, date):
        return "date", value
    raise JoinConfigError("unsupported time-key type")


def join_asof(left_rows,
              right_rows,
              on,
              availability_key="available_at",
              by=None,
              max_lookback=None,
              miss_marker="_pit_miss"):
    """Availability-aware as-of join.

    Parameters
    ----------
    left_rows : list[dict]
        Facts requested at time ``t = row[on]``. Optional grouping via
        ``row[by]``.
    right_rows : list[dict]
        Reference rows with effective date ``row[on]`` and publication /
        availability timestamp ``row[availability_key]``. May contain
        multiple revisions of the same (by, effective) pair.
    on : hashable
        Field name of the join/effective timestamp on BOTH sides.
    availability_key : hashable
        Field name of the right-side availability timestamp.
    by : hashable or None
        Grouping field (e.g. symbol); join stays within group.
    max_lookback : None, timedelta, int, float
        Maximum allowed age t - R[on]; older right rows are ineligible.
        Must support comparison with the natural difference type of the
        key values (timedelta for dates/datetimes, number for numerics).
    miss_marker : hashable or None
        Field set True on unmatched left rows (None disables marking;
        unmatched rows are then returned unchanged).

    Returns
    -------
    list[dict]
        One output row per left row, in left input order. Output row =
        copy of left row overlaid with the matched right row's fields
        (right values win on collision, EXCEPT ``on``, which keeps the
        left value so the request time is preserved). Unmatched rows
        carry ``miss_marker=True`` and no right fields.
    """
    if on == availability_key:
        raise JoinConfigError("on and availability_key must differ")
    if by is not None and by in (on, availability_key):
        raise JoinConfigError("by must differ from on/availability_key")

    lkeys = (on, by) if by is not None else (on,)
    rkeys = (on, availability_key, by) if by is not None else (
        on, availability_key)
    _check_keys(left_rows, lkeys, "left")
    _check_keys(right_rows, rkeys, "right")

    domains = set()
    def normalize(value):
        domain, normalized = _time_key(value)
        domains.add(domain)
        return normalized

    left_times = [normalize(r[on]) for r in left_rows]
    normalized_right = []
    originals = {}
    for original in right_rows:
        row = dict(original)
        row[on] = normalize(original[on])
        row[availability_key] = normalize(original[availability_key])
        normalized_right.append(row)
        originals[id(row)] = original
    if len(domains) > 1:
        raise JoinConfigError("date, timestamp and numeric axes cannot be mixed")
    if max_lookback is not None:
        if isinstance(max_lookback, timedelta):
            invalid = max_lookback < timedelta(0)
        else:
            invalid = (isinstance(max_lookback, bool)
                       or not isinstance(max_lookback, (int, float))
                       or not math.isfinite(max_lookback)
                       or max_lookback < 0)
        if invalid:
            raise JoinConfigError("max_lookback must be finite and nonnegative")

    # Index right rows by group; sort each partition by effective date.
    groups = {}
    for r in normalized_right:
        g = r[by] if by is not None else None
        groups.setdefault(g, []).append(r)

    partitions = {}
    for g, rows in groups.items():
        rows_sorted = sorted(rows, key=lambda r: (r[on], r[availability_key]))
        eff = [r[on] for r in rows_sorted]
        avail = [r[availability_key] for r in rows_sorted]
        partitions[g] = (rows_sorted, eff, avail)

    out = []
    for l, t in zip(left_rows, left_times):
        g = l[by] if by is not None else None
        part = partitions.get(g)
        best = None
        if part is not None:
            best = _pick(part, t, on, availability_key, max_lookback)
        if best is None:
            row = dict(l)
            if miss_marker is not None:
                row[miss_marker] = True
            out.append(row)
            continue
        row = dict(l)
        for k, v in originals[id(best)].items():
            if k != on:  # preserve the left/request timestamp
                row[k] = v
        out.append(row)
    return out


def _pick(partition, t, on, availability_key, max_lookback):
    """Return the eligible right row for left time t, or None.

    Eligible means: effective <= t AND available <= t (AND within
    lookback). Rows are sorted by (effective, availability); scanning
    BACKWARD from the last effective row yields candidates in
    descending (effective, availability) order, so the FIRST eligible
    hit is exactly the max-(effective, availability) winner.
    """
    rows, eff, _avail_unused = partition
    hi = bisect.bisect_right(eff, t)
    if hi == 0:
        return None
    lo = 0
    if max_lookback is not None:
        lo = bisect.bisect_left(eff, _min_key(t, max_lookback), 0, hi)
        if lo >= hi:
            return None
    i = hi - 1
    while i >= lo:
        r = rows[i]
        if r[availability_key] <= t:
            return r
        i -= 1
    return None


def _min_key(t, max_lookback):
    """Lower bound on eligible effective dates: t - max_lookback."""
    try:
        return t - max_lookback
    except TypeError:
        raise JoinConfigError(
            "max_lookback (%r) incompatible with on-field values %r"
            % (max_lookback, t))


# --------------------------------------------------------------------------
# Fuzz self-test
# --------------------------------------------------------------------------

def _gen_streams(rng, n_left=2000):
    """Random left/right streams: ties, out-of-order arrival, revisions."""
    symbols = [b"A", b"B", b"C"]
    base = 0
    horizon = 400

    def jitter(lo=-3, hi=6):
        return rng.randint(lo, hi)

    # ---- right side: effective stamps + late/out-of-order availability --
    # NOTE: the effective date field is named "t" (same as ``on``) on both
    # sides; a right row's "t" IS its effective timestamp.
    right = []
    rid = 0
    for _ in range(n_left // 2):
        sym = rng.choice(symbols)
        eff = base + rng.randint(0, horizon)
        # availability usually shortly after eff, sometimes BEFORE eff
        # (pre-published calendars), sometimes far after (late data).
        mode = rng.random()
        if mode < 0.10:
            avail = eff - jitter(0, 5)      # pre-published
        elif mode < 0.85:
            avail = eff + jitter(0, 20)     # normal lag
        else:
            avail = eff + jitter(0, 200)    # very late arrival
        right.append({"id": ("r%d" % rid), "sym": sym,
                      "t": eff, "avail": avail, "val": rng.randint(0, 99)})
        rid += 1
        # Revisions: same effective date republished later (~30%).
        while rng.random() < 0.30:
            avail2 = max(avail, eff) + jitter(1, 60)
            right.append({"id": ("r%d" % rid), "sym": sym, "t": eff,
                          "avail": avail2, "val": rng.randint(0, 99)})
            rid += 1
            avail = avail2
    # Deliberate exact ties: duplicate some rows verbatim.
    for r in list(right)[: len(right) // 10]:
        d = dict(r)
        d["id"] = d["id"] + "-tie"
        right.append(d)
    rng.shuffle(right)  # out-of-order arrival

    # ---- left side -------------------------------------------------------
    left = []
    for i in range(n_left):
        sym = rng.choice(symbols)
        t = base + rng.randint(-5, horizon + 40)
        left.append({"lid": i, "sym": sym, "t": t})
    rng.shuffle(left)

    # Left times may precede availability of everything -> misses happen.
    return left, right


def _bruteforce_match(l, right_by_group, by, on, ak, max_lookback):
    """O(n) reference: scan ALL right rows, apply the contract literally."""
    g = l[by] if by is not None else None
    t = l[on]
    # Mirror the join's deterministic tie rule: examine candidates in
    # ascending (eff, avail) order; strict improvement replaces, so the
    # LAST row with the maximal key wins.
    cands = sorted(right_by_group.get(g, ()), key=lambda r: (r[on], r[ak]))
    best = None
    for r in cands:
        if r[ak] > t:                       # LEAKAGE GUARD: not yet known
            continue
        if r[on] > t:                       # not yet effective
            continue
        if max_lookback is not None and t - r[on] > max_lookback:
            continue
        # ">=" keeps the LAST row of an equal-key run, matching the
        # join's deterministic backward-scan selection exactly.
        if best is None or (r[on], r[ak]) >= (best[on], best[ak]):
            best = r
    return best


def _run_selftest():
    rng = random.Random(20260825)
    failures = 0
    total_matches = 0
    total_misses = 0
    leakage_hits = 0

    scenarios = [
        {"by": "sym", "ak": "avail", "mlb": None},
        {"by": "sym", "ak": "avail", "mlb": 15},
        {"by": "sym", "ak": "avail", "mlb": 0},
        {"by": None, "ak": "avail", "mlb": None},
    ]

    for si, cfg in enumerate(scenarios):
        by, ak, mlb = cfg["by"], cfg["ak"], cfg["mlb"]
        left, right = _gen_streams(rng)
        got = join_asof(left, right, on="t",
                        availability_key=ak, by=by, max_lookback=mlb)

        assert len(got) == len(left), "scenario %d: row count drift" % si
        order_ok = [g["lid"] for g in got] == [
            l["lid"] for l in sorted(left, key=lambda x: x["lid"])]
        # NOTE: join preserves LEFT INPUT order; regenerate that order.
        got_by_lid = {g["lid"]: g for g in got}
        assert len(got_by_lid) == len(left)

        right_by_group = {}
        for r in right:
            g = r[by] if by is not None else None
            right_by_group.setdefault(g, []).append(r)

        # Index for content lookup: duplicate rows share an id, so
        # matches are verified by CONTENT, never by id alone.
        def find_rows(rid):
            return [r for r in right if r["id"] == rid]

        s_matches = s_misses = 0
        for l in left:
            ref = _bruteforce_match(l, right_by_group, by, "t", ak, mlb)
            out = got_by_lid[l["lid"]]
            if ref is None:
                s_misses += 1
                if out.get("_pit_miss") is not True:
                    print("FAIL s%d lid=%d expected miss" % (si, l["lid"]))
                    failures += 1
                    continue
                # A miss must not smuggle in ANY right-only field.
                if "val" in out or "id" in out:
                    print("FAIL s%d lid=%d miss carries right fields"
                          % (si, l["lid"]))
                    failures += 1
                continue
            s_matches += 1
            # --- PROGRAMMATIC LEAKAGE PROPERTY ------------------------
            m_id = out.get("id")
            if m_id is None:
                print("FAIL s%d lid=%d expected match, none present"
                      % (si, l["lid"]))
                failures += 1
                continue
            cands = [r for r in find_rows(m_id)
                     if all(r[k] == out.get(k) for k in ("sym", "val"))]
            matched = cands[0] if cands else None
            if matched is None:
                print("FAIL s%d lid=%d id/content mismatch" % (si, l["lid"]))
                failures += 1
                continue
            # Correctness vs the brute-force reference: compare FIELD
            # VALUES (eff/avail/val), not ids -- exact ties are
            # interchangeable and either twin is a valid answer.
            if ((matched["t"], matched[ak], matched["val"])
                    != (ref["t"], ref[ak], ref["val"])):
                print("FAIL s%d lid=%d got %s want %s"
                      % (si, l["lid"], matched["id"], ref["id"]))
                failures += 1
            if matched[ak] > l["t"]:
                leakage_hits += 1
                print("LEAK s%d lid=%d avail=%s > t=%s"
                      % (si, l["lid"], matched[ak], l["t"]))
                failures += 1
            if matched["t"] > l["t"]:
                print("FAIL s%d lid=%d eff=%s > t=%s"
                      % (si, l["lid"], matched["t"], l["t"]))
                failures += 1
            if mlb is not None and l["t"] - matched["t"] > mlb:
                print("FAIL s%d lid=%d violates max_lookback" % (si, l["lid"]))
                failures += 1
            if out.get("val") != matched["val"]:
                print("FAIL s%d lid=%d val mismatch" % (si, l["lid"]))
                failures += 1
            if out.get("t") != l["t"]:
                print("FAIL s%d lid=%d left t overwritten" % (si, l["lid"]))
                failures += 1
        total_matches += s_matches
        total_misses += s_misses
        print("scenario %d (by=%r mlb=%r): %d matches, %d misses"
              % (si, by, mlb, s_matches, s_misses))

    # ---- determinism / immutability spot checks --------------------------
    left, right = _gen_streams(random.Random(7))
    snap_l = [dict(x) for x in left]
    snap_r = [dict(x) for x in right]
    a = join_asof(left, right, on="t", availability_key="avail", by="sym")
    b = join_asof(left, right, on="t", availability_key="avail", by="sym")
    if a != b:
        print("FAIL: join not deterministic")
        failures += 1
    if left != snap_l or right != snap_r:
        print("FAIL: inputs were mutated")
        failures += 1

    # ---- datetime variant with timedelta lookback ------------------------
    def dt(y, m, d):
        return datetime(y, m, d, tzinfo=timezone.utc)
    ld = [{"sym": "X", "t": dt(2026, 1, 5)},
          {"sym": "X", "t": dt(2026, 1, 9)}]
    rd = [{"sym": "X", "t": dt(2026, 1, 3), "pub": dt(2026, 1, 4), "v": 1},
          {"sym": "X", "t": dt(2026, 1, 3), "pub": dt(2026, 1, 8), "v": 2},
          {"sym": "X", "t": dt(2026, 1, 8), "pub": dt(2026, 1, 20), "v": 3}]
    res = join_asof(ld, rd, on="t", availability_key="pub", by="sym",
                    max_lookback=timedelta(days=10))
    # Jan 5: sees rev v=1 only (v=2 pub Jan 8 leaks otherwise).
    if res[0].get("v") != 1 or "_pit_miss" in res[0]:
        print("FAIL: datetime rev-selection wrong: %r" % res[0])
        failures += 1
    # Jan 9: sees revision v=2 of Jan 3 (pub Jan 8 <= Jan 9); Jan 8 row
    # still hidden until Jan 20. Lookback 10d admits Jan 3.
    if res[1].get("v") != 2:
        print("FAIL: datetime revision pick wrong: %r" % res[1])
        failures += 1

    # ---- error paths ------------------------------------------------------
    try:
        join_asof([{"t": 1}], [{"e": 1}], on="t")
        print("FAIL: missing right key not caught")
        failures += 1
    except JoinConfigError:
        pass
    try:
        join_asof([{"t": 1}], [{"t": 1, "a": 1}], on="t", availability_key="t")
        print("FAIL: on==availability not caught")
        failures += 1
    except JoinConfigError:
        pass

    print("---")
    print("total matches=%d misses=%d LEAKAGE HITS=%d failures=%d"
          % (total_matches, total_misses, leakage_hits, failures))
    if failures:
        print("SELFTEST FAILED")
        return 1
    print("SELFTEST PASSED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="run the randomized leakage fuzz test")
    args = ap.parse_args(argv)
    if args.selftest:
        return _run_selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
