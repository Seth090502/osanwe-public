# fs-watcher-register.ps1 -- Windows 11 at-logon registration + immediate detached start
# Purpose: register OSanwe FS-Watcher in Task Scheduler (onlogon) AND start daemon NOW
# Pattern: detect existing task -> remove -> create -> start hidden process
# Pinned: Windows 11 / PowerShell 5.1+ / Python launcher (py)

$TaskName = 'OSanwe FS-Watcher'
$Script   = '/path/to/vault\tools\dev\fs-watcher.py'
$RunCmd   = "py `"$Script`" --start"

# Verify the watcher script exists before touching scheduler
if (-not (Test-Path $Script)) {
    Write-Host "[ERROR] fs-watcher.py not found at $Script" -ForegroundColor Red
    exit 1
}

# (a) Remove pre-existing task with same name (idempotent re-registration)
# Note: PowerShell 5.1 NativeCommandError mangles stderr-redirect on native exes;
# instead we let schtasks emit to stderr naturally and inspect $LASTEXITCODE.
schtasks /query /tn $TaskName | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[INFO] Removing existing task '$TaskName'..." -ForegroundColor Yellow
    schtasks /delete /tn $TaskName /f | Out-Null
}

# Create at-logon trigger (limited rights = no UAC prompt; /f forces overwrite)
Write-Host "[INFO] Registering '$TaskName' (onlogon trigger)..." -ForegroundColor Cyan
schtasks /create /tn $TaskName /tr $RunCmd /sc onlogon /rl limited /f | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] schtasks /create failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit 2
}

# (b) Start daemon NOW, detached + hidden so this terminal does not block
$pidFile = '/path/to/vault\.claude\state\fs-watcher.pid'
if (Test-Path $pidFile) {
    Write-Host "[INFO] PID file present at $pidFile -- daemon may already be running" -ForegroundColor Yellow
    Write-Host "       Run: py $Script --status" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Launching daemon (detached, hidden)..." -ForegroundColor Cyan
    Start-Process -FilePath 'py' -ArgumentList @($Script, '--start') -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if (Test-Path $pidFile) {
        $runningPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        Write-Host "[OK] Daemon started (PID $runningPid)" -ForegroundColor Green
    } else {
        Write-Host "[WARN] PID file did not appear within 2s; check: py $Script --status" -ForegroundColor Yellow
    }
}

# (c) Final status
Write-Host ""
Write-Host "[DONE] Task '$TaskName' registered (auto-starts at next logon)." -ForegroundColor Green
Write-Host "       Manage: schtasks /query /tn `"$TaskName`" | schtasks /delete /tn `"$TaskName`" /f"
exit 0
