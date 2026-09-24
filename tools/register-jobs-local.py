#!/usr/bin/env python3
"""register-jobs-local.py -- register the 4 'new' jobs via schtasks with
correct argument pairing (each /TR value quoted; /SC before its value)."""

import subprocess
import sys

JOBS = [
    ("osanwe-nightly-health",
     ["schtasks", "/Create", "/F", "/TN", "osanwe-nightly-health",
      "/SC", "DAILY", "/ST", "03:30",
      "/TR", "python .agents/scripts/checkall.py --quick"]),
    ("osanwe-weekly-calibration",
     ["schtasks", "/Create", "/F", "/TN", "osanwe-weekly-calibration",
      "/SC", "WEEKLY", "/D", "SUN", "/ST", "07:30",
      "/TR", "cmd /c cd /d /path/to/vault && python tools\\factor-store.py --ingest-bars <ticker-universe> && python tools\\backtest-offline.py && python tools\\calibration-report.py --jsonl Efforts\\osanwe-v2-overhaul\\_work\\calibration-offline.jsonl && python tools\\confidence-calibrator.py --jsonl Efforts\\osanwe-v2-overhaul\\_work\\calibration-offline.jsonl --win-key beats_spy --horizon 21"]),
    ("osanwe-weekly-synthesis",
     ["schtasks", "/Create", "/F", "/TN", "osanwe-weekly-synthesis",
      "/SC", "WEEKLY", "/D", "SAT", "/ST", "07:00",
      "/TR", "cmd /c cd /d /path/to/vault && python tools\\insight-candidates.py"]),
    ("osanwe-monthly-usage-ledger",
     ["schtasks", "/Create", "/F", "/TN", "osanwe-monthly-usage-ledger",
      "/SC", "MONTHLY", "/D", "1", "/ST", "06:00",
      "/TR", "cmd /c cd /d /path/to/vault && python tools\\usage-ledger.py"]),
]

for name, cmd in JOBS:
    r = subprocess.run(cmd, capture_output=True, text=True)
    status = "OK" if r.returncode == 0 else f"rc={r.returncode}"
    msg = (r.stdout or r.stderr).strip().splitlines()[-1][:70] if (r.stdout or r.stderr) else ""
    print(f"{name}: {status} {msg}")

print("\nVerify with: Get-ScheduledTask -TaskName '*osanwe*'")
