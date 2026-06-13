#!/usr/bin/env python3
"""
SessionStart vault-score injector.

Runs vault-audit.py --json and prints the current vault-health summary to stdout.
Per ref-claude-code-mastery sec 4, SessionStart hook stdout is appended to
Claude's context as system-reminder text; this gives every session immediate
visibility into the vault's integrity state.

Output (default): 4-line summary -- score, broken-wikilink count, orphan count,
missing-frontmatter count. When score <95 OR any GATE present, emits a
prominent floor-invariant breach warning so any skill writing to vault is
aware of the degraded state.

Score formula: v2.2 tier-weighted (gate * -5 cap -10; hard * -1 cap -5;
gate-breach hard-cap 90). Canonical source is vault-audit.py --json; this
script consumes the JSON directly (no formula re-derivation) so the two
estimators cannot diverge.

Opt-in flags (all additive; default output unchanged):
  --include-trend       append score_trend_30d block (slope across last 30
                        days of audit-meta sidecars; "insufficient_data" if
                        fewer than 3 sidecars present)
  --include-forecast    append breach_forecast block (predicts breach within
                        N days at current velocity if score within 5pts of
                        95-floor and velocity negative)
  --include-breakdown   append per-domain score_breakdown (investing, career,
                        skill-infra, health, golf, meta) so the dragging
                        domain is visible without re-running the audit

Skips entirely if vault-audit.py is unavailable. Never blocks the session.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
FLOOR_INVARIANT = 95  # honest floor per Plan #2 95-floor revision
AUDIT_META_DIR = VAULT_ROOT / "wiki" / "maintenance"
TREND_WINDOW_DAYS = 30
FORECAST_HEADROOM = 5  # forecast triggers when score within 5pts of floor


# Domain classification rules for --include-breakdown.
# Each (path_prefix, domain) tuple; first match wins. Prefixes are forward-slash
# vault-relative; matching is case-insensitive.
DOMAIN_RULES = [
    ("atlas/concepts/investing/", "investing"),
    ("atlas/sources/investing/", "investing"),
    ("wiki/entities/tickers/", "investing"),
    ("wiki/entities/companies/", "investing"),
    ("wiki/investing/", "investing"),
    ("calendar/decisions/briefings/", "investing"),
    ("efforts/career-search/", "career"),
    ("atlas/concepts/career/", "career"),
    ("atlas/sources/career/", "career"),
    ("efforts/health-protocol/", "health"),
    ("atlas/concepts/supplements/", "health"),
    ("atlas/sources/supplements/", "health"),
    ("efforts/golf-practice/", "golf"),
    ("atlas/concepts/golf/", "golf"),
    ("atlas/sources/golf/", "golf"),
    (".claude/skills/", "skill-infra"),
    (".claude/agents/", "skill-infra"),
    ("tools/", "skill-infra"),
    ("atlas/sources/meta/", "skill-infra"),
    ("docs/", "skill-infra"),
]


def classify_domain(path_str: str) -> str:
    """Return the domain bucket for a vault-relative path. Default: meta."""
    if not path_str:
        return "meta"
    p = path_str.replace("\\", "/").lower()
    for prefix, domain in DOMAIN_RULES:
        if p.startswith(prefix):
            return domain
    return "meta"


def fetch_audit_json():
    """Run vault-audit.py --json and parse. Returns dict or None on failure."""
    try:
        result = subprocess.run(
            ["python", str(VAULT_ROOT / "tools" / "vault-audit.py"), "--json"],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=25,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None


def compute_trend():
    """Compute score_trend_30d from audit-meta sidecars in wiki/maintenance/.
    Returns dict with slope_per_day + sample_count + status fields."""
    if not AUDIT_META_DIR.exists():
        return {"status": "insufficient_data", "reason": "wiki/maintenance/ absent",
                "sample_count": 0, "slope_per_day": None}
    cutoff = date.today() - timedelta(days=TREND_WINDOW_DAYS)
    samples = []
    for p in sorted(AUDIT_META_DIR.glob("audit-*-meta.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError):
            continue
        ds = data.get("date") or data.get("audit_date") or ""
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            continue
        if d < cutoff:
            continue
        score = data.get("score")
        if isinstance(score, (int, float)):
            samples.append((d, float(score)))
    if len(samples) < 3:
        return {"status": "insufficient_data",
                "reason": f"only {len(samples)} sidecar(s) within {TREND_WINDOW_DAYS}d window (need >=3)",
                "sample_count": len(samples), "slope_per_day": None}
    # Linear regression slope: ordinary least squares, x=days_since_first
    xs = [(s[0] - samples[0][0]).days for s in samples]
    ys = [s[1] for s in samples]
    n = len(samples)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = num / den if den > 0 else 0.0
    return {"status": "ok", "sample_count": n, "slope_per_day": round(slope, 3),
            "first_date": samples[0][0].isoformat(),
            "last_date": samples[-1][0].isoformat(),
            "first_score": samples[0][1], "last_score": samples[-1][1]}


def compute_forecast(score, trend):
    """Predict breach within N days based on current velocity."""
    if trend.get("status") != "ok" or trend.get("slope_per_day") is None:
        return {"status": "no_forecast", "reason": "trend unavailable"}
    slope = trend["slope_per_day"]
    headroom = score - FLOOR_INVARIANT
    if slope >= 0:
        return {"status": "stable_or_improving", "slope_per_day": slope,
                "current_score": score}
    if headroom > FORECAST_HEADROOM:
        return {"status": "no_forecast",
                "reason": f"score {score} > floor+{FORECAST_HEADROOM} ({FLOOR_INVARIANT + FORECAST_HEADROOM}); not yet at-risk",
                "slope_per_day": slope, "current_score": score}
    days_to_breach = headroom / abs(slope) if slope != 0 else 9999
    confidence = "HIGH" if trend["sample_count"] >= 7 else (
        "MED" if trend["sample_count"] >= 5 else "LOW")
    return {"status": "breach_predicted",
            "forecast": f"breach in {round(days_to_breach, 1)}d at current velocity",
            "days_to_breach": round(days_to_breach, 1),
            "slope_per_day": slope,
            "headroom_pts": headroom,
            "confidence": confidence}


def compute_breakdown(audit):
    """Per-domain breakdown of GATE + HARD findings.
    Returns dict {domain: {gate, hard, score_estimate}}."""
    domains = {}
    def bump(d, tier):
        domains.setdefault(d, {"gate": 0, "hard": 0})
        domains[d][tier] += 1
    # GATE: broken_wikilinks + missing_frontmatter + forbidden_frontmatter
    for b in audit.get("broken_wikilinks", []):
        bump(classify_domain(b.get("file", "")), "gate")
    for f in audit.get("missing_frontmatter", []):
        bump(classify_domain(f), "gate")
    for f in audit.get("forbidden_frontmatter", []):
        bump(classify_domain(f.get("file", "")), "gate")
    # HARD: orphans + stale_files + session_artifact_gaps + skill_body_length_violations
    for f in audit.get("orphans", []):
        bump(classify_domain(f), "hard")
    for f in audit.get("stale_files", []):
        bump(classify_domain(f.get("file", "")), "hard")
    for entry in audit.get("session_artifact_gaps", []) or []:
        path = entry.get("file", "") if isinstance(entry, dict) else ""
        bump(classify_domain(path), "hard")
    for entry in audit.get("skill_body_length_violations", []) or []:
        path = entry.get("file", "") if isinstance(entry, dict) else ""
        bump(classify_domain(path), "hard")
    # Compute domain-local score estimate (same v2.2 formula, domain-scoped)
    out = {}
    for d, counts in sorted(domains.items()):
        gp = max(counts["gate"] * -5, -10)
        hp = max(counts["hard"] * -1, -5)
        s = max(0, min(100, 100 + gp + hp))
        if counts["gate"] > 0 and s > 90:
            s = 90
        out[d] = {"gate": counts["gate"], "hard": counts["hard"],
                  "score_estimate": s}
    return out


def main():
    parser = argparse.ArgumentParser(description="SessionStart vault-score injector (v2.2 tier-weighted)")
    parser.add_argument("--include-trend", action="store_true",
                        help="Append score_trend_30d block (slope across audit-meta sidecars)")
    parser.add_argument("--include-forecast", action="store_true",
                        help="Append breach_forecast (requires --include-trend; auto-enables it)")
    parser.add_argument("--include-breakdown", action="store_true",
                        help="Append per-domain score breakdown")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Emit machine-readable JSON instead of human summary")
    args = parser.parse_args()

    audit = fetch_audit_json()
    if not audit:
        return  # silent fail; never block session start

    # v2.2 canonical: read score directly from vault-audit JSON. Single source
    # of truth -- the two estimators cannot diverge.
    score = audit.get("score")
    if score is None:
        return
    gate_count = audit.get("tiers", {}).get("gate", {}).get("count", 0)
    hard_count = audit.get("tiers", {}).get("hard_drift", {}).get("count", 0)
    broken = len(audit.get("broken_wikilinks", []))
    orphans = len(audit.get("orphans", []))
    fm_missing = len(audit.get("missing_frontmatter", []))

    # Optional analytics
    trend = compute_trend() if (args.include_trend or args.include_forecast) else None
    forecast = compute_forecast(score, trend) if args.include_forecast else None
    breakdown = compute_breakdown(audit) if args.include_breakdown else None

    if args.json_output:
        out = {
            "score": score,
            "floor_invariant": FLOOR_INVARIANT,
            "gate_count": gate_count,
            "hard_count": hard_count,
            "broken_wikilinks": broken,
            "orphans": orphans,
            "missing_frontmatter": fm_missing,
            "floor_breached": score < FLOOR_INVARIANT or gate_count > 0,
        }
        if trend is not None:
            out["score_trend_30d"] = trend
        if forecast is not None:
            out["breach_forecast"] = forecast
        if breakdown is not None:
            out["score_breakdown"] = breakdown
        print(json.dumps(out, indent=2))
        return

    # === Human-readable summary (byte-stable structure) ===
    print("[vault-audit] Vault health summary on session start:")
    print(f"  - Score: {score}/100 (floor invariant: {FLOOR_INVARIANT})")
    print(f"  - Broken wikilinks: {broken} (CRITICAL if >0)")
    print(f"  - Orphan files: {orphans}")
    print(f"  - Files missing frontmatter: {fm_missing}")

    # Bypass-log surfacing (preserved from prior implementation).
    # Reviewer B G-5 / HIGH-4 robustness: ISO-timestamped entries via regex.
    ENTRY_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    bypass_log_dir = VAULT_ROOT / ".claude" / "state"
    if bypass_log_dir.exists():
        for days_back in range(0, 3):
            check_date = (date.today() - timedelta(days=days_back)).isoformat()
            log_path = bypass_log_dir / f"bypasses-{check_date}.log"
            if log_path.exists():
                try:
                    with log_path.open(encoding="utf-8") as f:
                        entry_count = sum(1 for line in f if ENTRY_PREFIX.match(line))
                except OSError:
                    entry_count = 0
                if entry_count > 0:
                    label = "today" if days_back == 0 else (f"{days_back} day(s) ago")
                    print(f"  - Validator bypasses ({label}): {entry_count} entries in bypasses-{check_date}.log")

    if score < FLOOR_INVARIANT or gate_count > 0:
        print(
            f"[vault-audit] FLOOR INVARIANT BREACHED. Any skill writing to vault "
            f"must run /vault audit pre-commit. Run /vault repair --apply <ids> to recover."
        )

    # === Optional analytics blocks (additive; only printed when flag set) ===
    if trend is not None:
        print()
        print("[vault-audit] Score trend (last 30d):")
        if trend.get("status") == "ok":
            print(f"  - Samples: {trend['sample_count']} (range {trend['first_date']} -> {trend['last_date']})")
            print(f"  - Score: {trend['first_score']} -> {trend['last_score']}")
            print(f"  - Slope: {trend['slope_per_day']} pts/day")
        else:
            print(f"  - Status: {trend['status']} ({trend.get('reason', '')})")

    if forecast is not None:
        print()
        print("[vault-audit] Breach forecast:")
        if forecast.get("status") == "breach_predicted":
            print(f"  - {forecast['forecast']} (confidence: {forecast['confidence']})")
            print(f"  - Headroom: {forecast['headroom_pts']}pts; slope: {forecast['slope_per_day']}/day")
        else:
            print(f"  - Status: {forecast['status']} ({forecast.get('reason', '')})")

    if breakdown is not None:
        print()
        print("[vault-audit] Per-domain breakdown:")
        if breakdown:
            for dom, c in breakdown.items():
                print(f"  - {dom:12s} gate={c['gate']:>2}  hard={c['hard']:>2}  score={c['score_estimate']}")
        else:
            print("  - (no domain-attributable findings)")


if __name__ == "__main__":
    main()
