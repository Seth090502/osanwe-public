# register-local-worker-task.ps1 -- STAGED FOR THE OWNER; an agent must NEVER run this.
#
# WHY STAGED: agent self-registration of scheduled tasks was classifier-DENIED
# on 2026-07-04 (X70a) and the deny is correct -- a scheduled task is standing
# machine authority and only the operator grants it. Run this yourself in an
# elevated-or-normal PowerShell:
#
#     powershell -ExecutionPolicy Bypass -File tools\register-local-worker-task.ps1
#
# WHAT IT REGISTERS: osanwe-local-worker, daily 03:30, limited run level,
# running tools\run-local-worker.cmd (idle-gated relay-worker batch;
# CLAUDE_LANE_TRIGGER=scheduled-idle; every fire logs run-or-skip to
# .claude\state\local-worker-runs.log -- that log is the heartbeat the
# open-loops digest watches; silent >48h surfaces as LANE SILENT).
#
# FIXED TIME (03:30), NOT /sc onidle: Windows onidle measures HUMAN-INPUT
# idle, not GPU idle, and would break the heartbeat cadence. GPU/lane idleness
# is checked by relay-batch.py --if-idle at fire time (fail-closed skip).
#
# MCP KEYS (Fable fix 9): the scheduled task runs OUTSIDE your interactive
# session, so per-session env vars are invisible to it. For the fred (and
# later edgar) MCP servers to spawn overnight, set MACHINE-SCOPE (or at least
# user-scope) environment variables ONCE:
#     [Environment]::SetEnvironmentVariable("FRED_API_KEY", "<key>", "User")
#     [Environment]::SetEnvironmentVariable("EDGAR_IDENTITY", "<name email>", "User")
# Without them those servers are marked DOWN for the night's legs (never a
# HALT) and pending.json names the degraded servers ("fred DOWN 3 nights").

$Action  = New-ScheduledTaskAction -Execute "/path/to/vault\tools\run-local-worker.cmd" -WorkingDirectory "/path/to/vault"
$Trigger = New-ScheduledTaskTrigger -Daily -At 03:30
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 5)
Register-ScheduledTask -TaskName "osanwe-local-worker" -Action $Action -Trigger $Trigger -Settings $Settings -RunLevel Limited -Description "Osanwe idle-gated local relay worker (GATE-B 2026-08-17; trigger=scheduled-idle; heartbeat .claude\state\local-worker-runs.log)"
Write-Host "Registered osanwe-local-worker (daily 03:30, limited). Verify: schtasks /query /tn osanwe-local-worker /v"
