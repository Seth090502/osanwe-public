# register-jobs.ps1 -- OSANWE-V2 ADR-07 applier (OPERATOR-RUN ONLY, HB-09)
# Reads config/scheduled-jobs.json. Default mode registers only status:"new"
# jobs. Explicit -RepairExisting accepts three bounded repair targets, requires
# XML backups, and verifies action/settings plus unchanged triggers/principals.
#
# Usage (elevated or user-scope per preference):
#   powershell -ExecutionPolicy Bypass -File tools\register-jobs.ps1
#   powershell ... -DryRun     # print actions without registering

param(
    [switch]$DryRun,
    [switch]$RepairExisting,
    [string[]]$TaskName = @('osanwe-nightly-health', 'osanwe-weekly-calibration'),
    [string]$BackupDirectory
)

$ErrorActionPreference = "Stop"
$repo = "/path/to/vault"
$cfg = Get-Content "$repo\config\scheduled-jobs.json" -Raw | ConvertFrom-Json

if ($RepairExisting) {
    $allowed = @('osanwe-nightly-health', 'osanwe-weekly-calibration', 'osanwe-vault-reindex')
    if (@($TaskName | Select-Object -Unique).Count -ne $TaskName.Count) { throw 'Duplicate task selection.' }
    foreach ($name in $TaskName) {
        if ($name -notin $allowed) { throw "Repair scope does not include $name" }
    }
    if (-not $DryRun -and [string]::IsNullOrWhiteSpace($BackupDirectory)) { throw 'An explicit XML backup directory is required.' }
    if (-not $DryRun) {
        $backupRoot = [System.IO.Path]::GetFullPath($BackupDirectory)
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    }
    foreach ($name in $TaskName) {
        $job = @($cfg.jobs | Where-Object name -eq $name)
        if ($job.Count -ne 1 -or -not $job[0].desired_action -or -not $job[0].desired_settings) { throw "Exact desired contract missing for $name" }
        $job = $job[0]
        $task = Get-ScheduledTask -TaskName $name -ErrorAction Stop
        if ($task.State -eq 'Running') { throw "$name is running; do not mutate its action mid-run." }
        $desired = $job.desired_action
        $setting = $job.desired_settings
        if (-not (Test-Path -LiteralPath $desired.execute -PathType Leaf)) { throw "Interpreter unavailable: $($desired.execute)" }
        [pscustomobject]@{task=$name;action=$desired;settings=$setting;state='prepared'} | ConvertTo-Json -Depth 4 -Compress
        if ($DryRun) { continue }
        $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffffffZ')
        $backupFile = Join-Path $backupRoot "$name-$stamp.xml"
        $before = Export-ScheduledTask -TaskName $name
        [System.IO.File]::WriteAllText($backupFile, $before, [System.Text.UTF8Encoding]::new($false))
        [xml]$beforeXml = $before
        $action = New-ScheduledTaskAction -Execute $desired.execute -Argument $desired.arguments -WorkingDirectory $desired.cwd
        $settings = $task.Settings
        $settings.StartWhenAvailable = [bool]$setting.start_when_available
        $settings.WakeToRun = [bool]$setting.wake_to_run
        $settings.MultipleInstances = [int]$setting.multiple_instances
        $settings.ExecutionTimeLimit = [string]$setting.timeout
        if ($setting.PSObject.Properties.Name -contains 'run_only_if_idle') {
            $settings.RunOnlyIfIdle = [bool]$setting.run_only_if_idle
        }
        Set-ScheduledTask -TaskName $name -TaskPath $task.TaskPath -Action $action -Settings $settings | Out-Null
        $actual = Get-ScheduledTask -TaskName $name
        [xml]$afterXml = Export-ScheduledTask -TaskName $name
        if ($actual.Actions.Count -ne 1 -or $actual.Actions[0].Execute -cne $desired.execute -or
            $actual.Actions[0].Arguments -cne $desired.arguments -or $actual.Actions[0].WorkingDirectory -cne $desired.cwd -or
            $actual.Settings.StartWhenAvailable -ne [bool]$setting.start_when_available -or
            $actual.Settings.WakeToRun -ne [bool]$setting.wake_to_run -or
            $actual.Settings.MultipleInstances -ne [int]$setting.multiple_instances -or
            $actual.Settings.ExecutionTimeLimit -cne [string]$setting.timeout) { throw "Registered contract verification failed for $name; restore $backupFile" }
        if ($setting.PSObject.Properties.Name -contains 'run_only_if_idle' -and $actual.Settings.RunOnlyIfIdle -ne [bool]$setting.run_only_if_idle) {
            throw "Idle condition verification failed for $name; restore $backupFile"
        }
        if ($beforeXml.Task.Triggers.OuterXml -cne $afterXml.Task.Triggers.OuterXml -or
            $beforeXml.Task.Principals.OuterXml -cne $afterXml.Task.Principals.OuterXml) { throw "Trigger/principal preservation failed for $name; restore $backupFile" }
        [pscustomobject]@{task=$name;state='registered-action-verified';backup=$backupFile;execution='not_yet_observed'} | ConvertTo-Json -Compress
    }
    exit 0
}

foreach ($job in $cfg.jobs) {
    if ($job.status -ne "new") { continue }
    $actionText = $job.command
    Write-Host "Job: $($job.name)"
    Write-Host "  schedule : $($job.schedule)"
    Write-Host "  command  : $actionText"
    if ($DryRun) { Write-Host "  (dry-run: not registered)"; continue }

    # Nightly health job is pure python; synthesis/usage are python too.
    # Schedule strings in the registry are human-readable; map to Task Scheduler args.
    switch -Wildcard ($job.schedule) {
        "daily*" {
            $st = New-ScheduledTaskTrigger -Daily -At "03:30"
        }
        "SAT*" {
            $st = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At "07:00"
        }
        "monthly*" {
            throw 'Monthly schedules require an exact monthly trigger; a weekly placeholder is not acceptable.'
        }
        default {
            Write-Warning "  unrecognized schedule pattern; skipping"
            continue
        }
    }
    $exe = "python.exe"
    $arg = ($actionText -replace '^python\s+', '')
    $act = New-ScheduledTaskAction -Execute $exe -Argument $arg -WorkingDirectory $repo
    Register-ScheduledTask -TaskName $job.name -Trigger $st -Action $act -Description "OSANWE-V2 ADR-07 job; see config/scheduled-jobs.json" | Out-Null
    Write-Host "  REGISTERED $($job.name)"
}
Write-Host "Done. DELETE/PARKED rows remain manual operator decisions."
