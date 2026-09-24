@echo off
rem run-local-worker.cmd -- idle-gated scheduled relay-worker wrapper (W11).
rem GATE-B: wiki/research/gates/gate-b-local-orchestration-program-2026-08-17.md
rem Registered (BY <owner>, never by an agent -- X70a) via
rem tools/register-local-worker-task.ps1; fires daily 03:30.
rem
rem CLAUDE_LANE_TRIGGER=scheduled-idle is LOAD-BEARING: the trigger is frozen
rem into leg state at creation and unattended legs must NEVER count toward the
rem promotion counters (parity rule; Fable fix 2 + F-3).
rem The --if-idle precheck (lane.lock free; 2x nvidia-smi util below 20 pct +
rem model residency or 20 GiB free; daemon reachable; fail-closed) lives in
rem relay-batch.py -- python owns the logic; this wrapper only sets the
rem trigger and appends to the heartbeat log (every fire logs run OR
rem skip:reason -- the log IS the heartbeat for the open-loops LANE SILENT
rem check).
cd /d /path/to/vault
set CLAUDE_LANE_TRIGGER=scheduled-idle
python tools\relay-batch.py --if-idle --stop-by 07:30 --manifest config\scheduled-missions.json >> .claude\state\local-worker-runs.log 2>&1
