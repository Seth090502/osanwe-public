# lane-guard.ps1 -- VRAM spill watchdog for the local model lane.
#
# WHY THIS EXISTS: the operator chose to KEEP ctx 262144 rather than shrink the context
# window, which leaves ~1,485 MiB of VRAM headroom on a 32,607 MiB card. When anything else
# claims that memory, Ollama places part of the model on CPU and mode 3 becomes many times
# slower with NOTHING on screen to say why. This watches for that and says so.
# Gate: wiki/research/gates/gate-b-lane-guard-2026-08-15.md (BUILD-JUSTIFIED, rule 2).
#
# It observes and reports. It never restarts, unloads, resizes or writes into the vault.
#
# KNOWN BLIND SPOT (documented rather than oversold): `size_vram` is what Ollama ALLOCATED
# at load time, not what is resident now. Windows WDDM can page GPU memory out to system RAM
# under contention WITHOUT that number changing. So this catches the common path -- another GPU
# application runs, model unloads on keep-alive, next use reloads into a contended GPU and lands partly
# on CPU -- but is blind to "already resident, then paged out". Only a throughput canary
# detects that, and a canary costs GPU time on a card this tight, so it is -Canary, opt-in.
# The IMMINENT signal (low free VRAM while resident) is the cheap precursor for the blind case.
#
# ASCII only (Pattern 22).

[CmdletBinding()]
param(
    [switch]$Once,                       # print one status line and exit; doubles as a doctor
    [switch]$Canary,                     # opt-in: also probe real throughput (costs GPU time)
    [int]$IntervalSec       = 30,
    [int]$ImminentFreeMiB   = 1200,
    [int]$CanaryFloorTokS   = 60,        # decode below this with a resident model = degraded
    [int]$MaxUnreachable    = 10,        # consecutive dead polls before giving up (~5 min)
    [string]$LaneHost       = 'http://127.0.0.1:11434',
    [string]$StateDir       = '/path/to/vault\.claude\state',
    [string]$LogPath        = ''         # opt-in poll trace; used to VERIFY debounce, off by default
)

$ErrorActionPreference = 'Continue'
$PidFile = Join-Path $StateDir 'lane-guard.pid'

# --- probes -------------------------------------------------------------------------------

function Get-LaneState {
    # /api/ps gives exact size vs size_vram per resident model. This is the authoritative
    # placement signal; the `ollama ps` PROCESSOR column is formatted for humans, not parsing.
    try {
        $r = Invoke-RestMethod -Uri "$LaneHost/api/ps" -TimeoutSec 5 -ErrorAction Stop
    } catch {
        return [pscustomobject]@{ Reachable = $false }
    }
    $m = $r.models | Select-Object -First 1
    if (-not $m) {
        return [pscustomobject]@{ Reachable = $true; Loaded = $false }
    }
    $frac = if ($m.size -gt 0) { [double]$m.size_vram / [double]$m.size } else { 0 }
    [pscustomobject]@{
        Reachable = $true
        Loaded    = $true
        Name      = $m.name
        SizeMiB   = [int]($m.size / 1MB)
        VramMiB   = [int]($m.size_vram / 1MB)
        GpuFrac   = $frac
    }
}

function Get-FreeVramMiB {
    try {
        $out = & nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
        return [int](($out | Select-Object -First 1).Trim())
    } catch { return $null }
}

function Get-CanaryTokS {
    # Real decode probe. Only runs under -Canary: it occupies the GPU, which is exactly the
    # resource we are short of, so it must never be on the default poll path.
    param([string]$Model)
    $body = @{ model = $Model; prompt = 'Count to twenty.'; stream = $false
               options = @{ temperature = 0; num_predict = 64 } } | ConvertTo-Json -Compress
    try {
        $r = Invoke-RestMethod -Uri "$LaneHost/api/generate" -Method Post -Body $body `
                -ContentType 'application/json' -TimeoutSec 120 -ErrorAction Stop
        if ($r.eval_duration -gt 0) { return [math]::Round($r.eval_count / ($r.eval_duration / 1e9), 1) }
    } catch { }
    return $null
}

# --- assessment ---------------------------------------------------------------------------

function Get-Assessment {
    $s = Get-LaneState
    if (-not $s.Reachable) { return [pscustomobject]@{ State = 'DAEMON-DOWN'; Detail = 'no answer from /api/ps' } }
    if (-not $s.Loaded)    { return [pscustomobject]@{ State = 'IDLE';        Detail = 'no model resident' } }

    $free = Get-FreeVramMiB
    $freeTxt = if ($null -ne $free) { "$free MiB free" } else { 'free VRAM unknown' }
    $base = "{0}  {1}/{2} MiB on GPU ({3:P1})  {4}" -f $s.Name, $s.VramMiB, $s.SizeMiB, $s.GpuFrac, $freeTxt

    if ($s.GpuFrac -lt 0.999) {
        $cpuPct = [math]::Round((1 - $s.GpuFrac) * 100, 1)
        return [pscustomobject]@{ State = 'SPILLED'
            Detail = "$base -- $cpuPct% of the model is on CPU" }
    }
    if ($Canary) {
        $tok = Get-CanaryTokS -Model $s.Name
        if ($null -ne $tok -and $tok -lt $CanaryFloorTokS) {
            return [pscustomobject]@{ State = 'DEGRADED'
                Detail = "$base -- decode $tok tok/s, under the $CanaryFloorTokS floor (WDDM paging?)" }
        }
    }
    if ($null -eq $free) {
        # INCONCLUSIVE, not OK. This distinction is load-bearing: the poll loop clears the
        # debounce latch on OK, so folding an unreadable nvidia-smi into OK would silently
        # re-arm the alert and re-fire on the very next poll -- turning one episode into a
        # stream of popups. An unknown reading must change nothing.
        return [pscustomobject]@{ State = 'UNKNOWN'; Detail = "$base -- free VRAM unreadable" }
    }
    if ($free -lt $ImminentFreeMiB) {
        return [pscustomobject]@{ State = 'IMMINENT'; Detail = $base }
    }
    [pscustomobject]@{ State = 'OK'; Detail = $base }
}

# --- alert ----------------------------------------------------------------------------------

function Show-Alert {
    param([string]$State, [string]$Detail)

    $head = switch ($State) {
        'SPILLED'  { 'VRAM SPILL -- THE LOCAL MODEL IS RUNNING PARTLY ON CPU' }
        'DEGRADED' { 'LOCAL MODEL DEGRADED -- decode far below normal' }
        'IMMINENT' { 'VRAM LOW -- the next model load will spill to CPU' }
        default    { "LANE GUARD -- $State" }
    }
    $advice = if ($State -eq 'IMMINENT') {
        'Close a GPU consumer (another GPU application) to protect the next load.'
    } else {
        "Close the GPU consumer, then re-arm:  pwsh -NoProfile -File /path/to/vault\tools\lane-arm.ps1"
    }

    # NO FOCUS STEAL. If the operator is in a fullscreen application, switching them out to report
    # that it is slowing something down is worse than the condition itself. We never
    # call SetForegroundWindow, and Windows' foreground lock stops a non-foreground process
    # from taking focus on its own -- so this surfaces as a window behind the application plus a
    # taskbar flash, not an interruption. Honest limit: under borderless-windowed some shells
    # may still raise it.
    $inner = @"
Write-Host ''
Write-Host '  $head' -ForegroundColor Red
Write-Host ''
Write-Host '  $Detail'
Write-Host ''
Write-Host '  $advice'
Write-Host ''
Write-Host '  (lane-guard; this window is safe to close)' -ForegroundColor DarkGray
Write-Host ''
"@
    try {
        Start-Process -FilePath 'pwsh' `
            -ArgumentList @('-NoProfile', '-NoExit', '-Command', $inner) `
            -WindowStyle Normal -ErrorAction Stop | Out-Null
    } catch {
        # Never let a failed alert take down the watchdog.
        Write-Host "lane-guard: could not open alert window -- $State : $Detail"
    }
}

# --- --once: status, no polling, no side effects --------------------------------------------

if ($Once) {
    $a = Get-Assessment
    "lane-guard: {0} -- {1}" -f $a.State, $a.Detail
    exit $(if ($a.State -in @('SPILLED', 'DEGRADED')) { 1 } else { 0 })
}

# --- singleton ------------------------------------------------------------------------------
# lane-arm.ps1 runs on EVERY arm, so a naive spawn leaves N watchdogs all alerting on the
# same episode.
#
# AN EXCLUSIVE FILE LOCK, chosen on its merits. A file opened with share mode None is held by
# the PROCESS for as long as the handle is open and the OS refuses the second opener
# atomically -- no check-then-write window, and no thread-ownership semantics to get wrong.
#
# CORRECTION ON THE RECORD, because the honest version is more useful than the flattering one:
# a pidfile design and a named-Mutex design were each implemented first and each APPEARED to
# fail a live test showing "2 watchdogs" from rapid arms. Both diagnoses were WRONG. The
# counting command was `Get-CimInstance ... CommandLine -like '*lane-guard.ps1*'`, and that
# command's OWN command line contains that literal string -- so it counted itself, every time,
# in all three iterations. Actual watchdog count was always 1. The lock below is kept because
# it is the most robust of the three (pidfile check-then-write genuinely is non-atomic in
# principle, and a .NET Mutex is thread-owned, which PowerShell runspaces do not guarantee),
# NOT because the others were observed to fail. Lesson: when three different fixes produce an
# identical wrong number, suspect the instrument, and print the raw rows instead of a count.
$script:Lock = $null
# Directory first: if StateDir is missing, the Open below would throw and be misreported as
# "another instance already holds the lock".
try {
    if (-not (Test-Path -LiteralPath $StateDir)) {
        New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    }
} catch { }
try {
    $script:Lock = [System.IO.File]::Open(
        (Join-Path $StateDir 'lane-guard.lock'),
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None)
} catch {
    Write-Host 'lane-guard: another instance already holds the lock; exiting.'
    exit 0
}

try {
    if (-not (Test-Path -LiteralPath $StateDir)) {
        New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    }
    Set-Content -LiteralPath $PidFile -Value $PID -Encoding ascii -NoNewline
} catch { }

# --- poll loop --------------------------------------------------------------------------------

$alerted    = $false     # hard debounce: one alert per episode, re-armed only on recovery
$deadPolls  = 0

try {
    while ($true) {
        $a = Get-Assessment

        if ($LogPath) {
            try {
                Add-Content -LiteralPath $LogPath -Encoding ascii `
                    -Value ("{0} state={1} alerted={2} :: {3}" -f (Get-Date -Format 'HH:mm:ss'), $a.State, $alerted, $a.Detail)
            } catch { }
        }

        if ($a.State -eq 'DAEMON-DOWN') {
            $deadPolls++
            # Bounded lifetime: never outlive the daemon indefinitely.
            if ($deadPolls -ge $MaxUnreachable) { break }
        } else {
            $deadPolls = 0
            if ($a.State -in @('SPILLED', 'DEGRADED', 'IMMINENT')) {
                if (-not $alerted) {
                    Show-Alert -State $a.State -Detail $a.Detail
                    $alerted = $true          # stays latched until the condition clears
                }
            } elseif ($a.State -eq 'OK') {
                $alerted = $false             # recovery re-arms the alert
            }
        }
        Start-Sleep -Seconds $IntervalSec
    }
} finally {
    try { Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue } catch { }
    try { if ($script:Lock) { $script:Lock.Close(); $script:Lock.Dispose() } } catch { }
}
