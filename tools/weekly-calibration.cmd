@echo off
rem Versioned, locked, bounded public calibration. Historical grades are preserved.
rem The Python receipt records failed/stale artifacts even after a zero child exit.
cd /d /path/to/vault || exit /b 1
/path/to/python\python.exe tools\scheduled-job.py weekly-calibration
exit /b %errorlevel%
