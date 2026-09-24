@echo off
rem TENFOLD T3 (2026-07-04): Task Scheduler wrapper for the Sunday scorer lane.
rem Zero-LLM, immune to rate limits (X79). Log consumed by the Monday digest row.
cd /d /path/to/vault
echo === scorer run %DATE% %TIME% === >> .claude\state\score-outcomes-runs.log
/path/to/python\python.exe tools\score-outcomes.py >> .claude\state\score-outcomes-runs.log 2>&1
