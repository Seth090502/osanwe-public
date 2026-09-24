# lane-arm.ps1 -- background lane arming for launcher mode 2.
#
# Runs DETACHED so the operator's session starts instantly. Writes a state file the
# statusline chip polls. Never blocks a session, never fails a session: lane absence is
# never a HALT (docs/osanwe-runtime-reference.md, "Local model lane").
#
# Why this is a separate process: `delegate.py --check` does a REAL generation roundtrip
# with a hardcoded 120s timeout, and a cold 18GB model load can use most of it. Putting
# that on the launch path would tax every mode-2 launch by 20-120 seconds, which is how
# a one-keystroke menu gets abandoned in week one.

param(
    [string]$StateFile = '/path/to/vault\.claude\state\lane-state',
    [string]$Vault     = '/path/to/vault'
)

$ErrorActionPreference = 'Continue'

function Write-LaneState {
    param([string]$State, [string]$Model, [string]$Detail)
    $line = '{0}|{1}|{2}|{3}' -f $State, $Model, (Get-Date -Format 'HH:mm:ss'), $Detail
    try {
        $dir = Split-Path -Parent $StateFile
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Set-Content -LiteralPath $StateFile -Value $line -Encoding ascii -NoNewline
    } catch { }
}

# --- SSOT read: the ONLY place a model name comes from (X12) --------------------------
$laneFile = Join-Path $Vault 'config\local-lane.json'
$model = 'unknown'; $laneHost = 'http://127.0.0.1:11434'; $ctx = 131072
try {
    $lane = Get-Content -LiteralPath $laneFile -Raw -ErrorAction Stop | ConvertFrom-Json
    if ($lane.model) { $model = [string]$lane.model }
    if ($lane.host)  { $laneHost = ([string]$lane.host).TrimEnd('/') }
    if ($lane.ctx)   { $ctx = [int]$lane.ctx }
} catch {
    Write-LaneState -State 'DISARMED' -Model 'unknown' -Detail 'local-lane.json unreadable -- restore from git'
    exit 3
}
if ($env:OLLAMA_HOST) {
    $h = $env:OLLAMA_HOST
    if ($h -notmatch '^https?://') { $h = "http://$h" }
    $laneHost = $h.TrimEnd('/')
}

Write-LaneState -State 'WARMING' -Model $model -Detail 'checking daemon'

# --- daemon: health-check first, start only if needed --------------------------------
function Test-Daemon {
    param([string]$BaseUrl, [int]$TimeoutMs = 400)
    try {
        $u = [uri]$BaseUrl
        $c = [Net.Sockets.TcpClient]::new()
        $ok = $c.ConnectAsync($u.Host, $u.Port).Wait($TimeoutMs)
        $c.Dispose()
        return $ok
    } catch { return $false }
}

if (-not (Test-Daemon $laneHost)) {
    $ollama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (-not (Test-Path -LiteralPath $ollama)) {
        Write-LaneState -State 'DISARMED' -Model $model -Detail 'ollama.exe not found'
        exit 2
    }
    if ($laneHost -notmatch '127\.0\.0\.1|localhost') {
        Write-LaneState -State 'DISARMED' -Model $model -Detail "remote OLLAMA_HOST $laneHost -- not starting a local daemon"
        exit 2
    }

    # Daemon env is frozen at START. Pin it so the daemon's context stops depending on
    # which shell happened to launch it (GUI 262144 / HKLM 65536 / PS profile map 131072
    # all coexist on this box, and the live daemon today was GUI-started).
    $env:OLLAMA_CONTEXT_LENGTH   = "$ctx"
    $env:OLLAMA_HOST             = '127.0.0.1:11434'
    $env:OLLAMA_MAX_LOADED_MODELS= '1'
    # 1 slot, matching what Ollama ACTUALLY serves. Measured 2026-08-15 from the
    # llama-server command line in server-launcher.log: Ollama derated a requested 2 to
    # `-np 1` (it will not allocate slots x ctx it cannot fit at 262144). The pin said 2 and
    # the daemon ran 1, so the 4->2 edit on 2026-08-14 changed nothing. Stating the truth
    # here so the next reader does not compute a KV budget from a number that never applied.
    $env:OLLAMA_NUM_PARALLEL     = '1'
    $env:OLLAMA_ORIGINS          = ''

    # Keep the model resident. Ambient HKLM sets 30m, so an idle mode-3 session pays an
    # 18 GB cold reload on its next turn; "keep the model resident" is a top lever for a
    # local coding agent. 8h covers a working day without pinning VRAM indefinitely.
    $env:OLLAMA_KEEP_ALIVE       = '8h'

    # llama.cpp passthrough (llama-server reads 131 LLAMA_ARG_* vars; Ollama spawns it as a
    # child and it inherits this environment). These are NOT on Ollama's command line, so
    # env is the only way to reach them and nothing overrides it.
    #
    # NOT SET: `LLAMA_ARG_CACHE_RAM='-1'` was tried 2026-08-15 on the theory that the
    # 8192 MiB default was evicting the vault's ~56k-token prompt state and killing prefix
    # reuse. MEASURED AND DISPROVEN the same session: with the cap lifted, turn 2 still
    # re-evaluated 58,728 tokens. Removed rather than left in as a harmless-looking
    # non-default -- an unproven knob in a measurement rig is how the next session's numbers
    # get misattributed. Evidence: bakeoff-round4-mode3-latency-2026-08-15.md.
    #
    # DRAFT-CACHE QUANTIZATION (2026-08-15). The MTP speculative-decode draft keeps its OWN
    # KV cache, and the server log shows it at f16: "K (f16): 512.00 MiB, V (f16): 512.00 MiB".
    # Quantizing it to q8_0 frees ~512 MiB on a card with only ~1,485 MiB spare.
    #   REACHABLE: unlike -b/-ub, `--spec-draft-cache-type-*` does NOT appear on Ollama's
    #   llama-server command line, so nothing overrides these env values.
    #   OUTPUT-SAFE: speculative decoding VERIFIES every accepted draft token against the
    #   target model, so a lossier DRAFT cache cannot corrupt output.
    #
    # TRIED 2026-08-15 AND REVERTED -- it is net NEGATIVE on this box, which the plan did not
    # predict. The env DID take effect (log went from "K (f16): 512.00 MiB, V (f16): 512.00
    # MiB" to "K (q8_0): 272.00 MiB, V (q8_0): 272.00 MiB", saving 480 MiB), but the model's
    # total footprint GREW 17,684 -> 18,239 MiB and free VRAM FELL 1,484 -> 979 MiB. Measured
    # twice with alert windows closed to remove the desktop confound. Most likely the q8_0
    # draft path allocates additional dequantization compute buffers that exceed the cache
    # saving. Expected +512 MiB, delivered -505 MiB. Do not re-apply without re-measuring.
    #   $env:LLAMA_ARG_SPEC_DRAFT_CACHE_TYPE_K = 'q8_0'
    #   $env:LLAMA_ARG_SPEC_DRAFT_CACHE_TYPE_V = 'q8_0'

    # NOT SET, and PROVEN inert: `LLAMA_ARG_BATCH`/`LLAMA_ARG_UBATCH` = 2048 were armed
    # 2026-08-15 and the server still reported `n_batch = 512 / n_ubatch = 512`. Ollama
    # passes `-b 512 -ub 512` on the llama-server command line and llama.cpp's command line
    # beats its env, so the batch size is NOT reachable from here at all.
    # Consequence: raising the physical batch -- the direct lever on the ~2,600-3,300 tok/s
    # prefill -- requires driving llama-server.exe directly, which costs Ollama's model
    # management, `delegate.py --use` swapping, the local-lane.json SSOT integration, and the
    # /v1/messages endpoint the mode-3 normalizer depends on. Not taken; recorded so nobody
    # re-runs this experiment. Evidence: bakeoff-round4-mode3-latency-2026-08-15.md.

    # Redirect the server stream. A plain hidden Start-Process DISCARDS it, and
    # server.log is the evidence channel several verification steps depend on.
    $logDir = Join-Path $env:LOCALAPPDATA 'Ollama'
    if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $errLog = Join-Path $logDir 'server-launcher.log'
    $outLog = Join-Path $logDir 'server-launcher.out.log'

    Write-LaneState -State 'WARMING' -Model $model -Detail 'starting daemon'
    try {
        Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden `
            -RedirectStandardError $errLog -RedirectStandardOutput $outLog | Out-Null
    } catch {
        Write-LaneState -State 'DISARMED' -Model $model -Detail 'daemon start failed'
        exit 2
    }

    $deadline = (Get-Date).AddSeconds(30)
    $up = $false
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 400
        if (Test-Daemon $laneHost 800) { $up = $true; break }
    }
    if (-not $up) {
        Write-LaneState -State 'DISARMED' -Model $model -Detail 'daemon did not answer in 30s'
        exit 2
    }
}

# --- arm: the real roundtrip ---------------------------------------------------------
Write-LaneState -State 'WARMING' -Model $model -Detail 'loading model (cold load can take 30-60s)'

$py = 'python'
if (Test-Path -LiteralPath '/path/to/python\python.exe') { $py = '/path/to/python\python.exe' }

try {
    $out = & $py (Join-Path $Vault 'tools\delegate.py') '--check' 2>&1 | Out-String
    $rc  = $LASTEXITCODE
} catch {
    Write-LaneState -State 'DISARMED' -Model $model -Detail 'delegate.py --check could not run'
    exit 2
}

$line = ($out -split "`r?`n" | Where-Object { $_ -match 'delegate:' } | Select-Object -First 1)
if (-not $line) { $line = ($out -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1) }
$line = ($line -replace '\s+', ' ').Trim()

if ($rc -eq 0) {
    Write-LaneState -State 'ARMED' -Model $model -Detail $line

    # Spill watchdog. The operator kept ctx 262144, which leaves ~1,485 MiB of VRAM headroom,
    # and a spill is SILENT -- the model quietly runs partly on CPU and mode 3 gets many times
    # slower with nothing on screen to explain it. lane-guard polls /api/ps and says so.
    # It self-enforces a singleton (pidfile), so re-arming does not stack watchdogs, and it
    # exits on its own once the daemon stays unreachable. Failure here must never fail an arm.
    # Gate: wiki/research/gates/gate-b-lane-guard-2026-08-15.md
    try {
        Start-Process -FilePath 'pwsh' `
            -ArgumentList @('-NoProfile', '-File', (Join-Path $Vault 'tools\lane-guard.ps1')) `
            -WindowStyle Hidden -ErrorAction Stop | Out-Null
    } catch { }

    # Warm the relay worker's MCP allowlist and PIN rosters (relay.py --probe writes
    # .claude/state/relay/mcp-rosters.json). The pinned roster block is what stopped
    # pilot001's 8 arg-guessing refusals; probing at arm time means the first real
    # research:* leg starts with fresh pins instead of a cold probe. Fire-and-forget:
    # a probe failure must never fail an arm (relay refuses cleanly without pins).
    try {
        Start-Process -FilePath $py `
            -ArgumentList @((Join-Path $Vault 'tools\relay.py'), '--probe') `
            -WindowStyle Hidden -ErrorAction Stop | Out-Null
    } catch { }

    exit 0
} else {
    Write-LaneState -State 'DISARMED' -Model $model -Detail $line
    exit $rc
}
