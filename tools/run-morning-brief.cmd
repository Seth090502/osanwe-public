@echo off
rem TENFOLD T4 (2026-07-04): Task Scheduler wrapper for the weekday pre-market brief lane.
rem Lane: reindex-if-stale -> headless /brief --quick (draws the SUBSCRIPTION pool, X70).
rem Silent-failure detection = open-loops.py briefing-freshness line (T2) + this log.
rem Degradation doctrine: docs/osanwe-runtime-reference.md "X70 degradation doctrine".
cd /d /path/to/vault
echo === morning-brief run %DATE% %TIME% === >> .claude\state\morning-brief-runs.log
rem 1. reindex-if-stale: one synchronous poll of the existing debounced runner
rem    (exits in ms when the index is current; full rebuild only when writes pending)
"/path/to/program-files\nodejs\node.exe" "/path/to/home\.vault-substrate\reindex-runner.mjs" >> .claude\state\morning-brief-runs.log 2>&1
rem 2. headless quick brief; global permission posture covers tools (X28); vault hooks
rem    still enforce path guards + validators mechanically. Rate-limit/API failure is
rem    non-fatal by design: the freshness detector flags the unbriefed weekday.
"/path/to/home\.local\bin\claude.exe" -p "/brief --quick" >> .claude\state\morning-brief-runs.log 2>&1
echo exit=%ERRORLEVEL% >> .claude\state\morning-brief-runs.log
