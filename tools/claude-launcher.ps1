#Requires -Version 7.0
<#
claude-launcher.ps1 -- the 3-lane menu. Runs ONLY on a bare interactive `claude`.

Invoked by tools/claude-shim.ps1, which has already jailed the environment and assigned
NODE_OPTIONS. This file may fail; the shim falls open to plain claude.exe if it is missing,
and every path here that can throw is wrapped so the worst case is a normal mode-1 session.

Modes: 1 subscription, 2 live OpenCode model/pool picker, 3 existing fully-local lane.
Option 2 delegates to opencode-menu.ps1 and refuses failures without changing lanes.

ASCII only (Pattern 22): no box-drawing, no arrows, no curly quotes. A non-ASCII byte also
mis-renders under the console codepage.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ClaudeExe,
    [string]$Mode = '0',
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest = @()
)

$VAULT     = '/path/to/vault'
$script:VAULT_ROOT = $VAULT
$LANE_FILE = Join-Path $VAULT 'config\local-lane.json'
$PIN_FILE  = Join-Path $VAULT 'config\claude-verified-version'
$STATE     = Join-Path $VAULT '.claude\state\lane-state'
$ARM_PS1   = Join-Path $VAULT 'tools\lane-arm.ps1'

# --- helpers -------------------------------------------------------------------------

function Get-Lane {
    try { return (Get-Content -LiteralPath $LANE_FILE -Raw -ErrorAction Stop | ConvertFrom-Json) }
    catch { return $null }
}

function Get-LaneHost {
    param($Lane)
    if ($env:OLLAMA_HOST) {
        $h = $env:OLLAMA_HOST
        if ($h -notmatch '^https?://') { $h = "http://$h" }
        return $h.TrimEnd('/')
    }
    if ($Lane -and $Lane.host) { return ([string]$Lane.host).TrimEnd('/') }
    return 'http://127.0.0.1:11434'
}

function Test-DaemonFast {
    param([string]$BaseUrl, [int]$Ms = 150)
    try {
        $u = [uri]$BaseUrl
        $c = [Net.Sockets.TcpClient]::new()
        $ok = $c.ConnectAsync($u.Host, $u.Port).Wait($Ms)
        $c.Dispose()
        return $ok
    } catch { return $false }
}

# Binary stat-pin. Every security property this launcher relies on (--tools restricting the
# tool SET, --settings beating user settings, --bare never reading the keychain) was proven
# against one build, and claude.exe auto-updates silently -- it moved 2.1.228 -> 2.1.229
# mid-design. A stat compare is ~0ms; `--version` costs 132ms and would tax every launch.
function Test-BinaryPin {
    param([string]$Exe)
    try {
        if (-not (Test-Path -LiteralPath $PIN_FILE)) { return $null }
        $pin = (Get-Content -LiteralPath $PIN_FILE -Raw).Trim()
        $fi  = Get-Item -LiteralPath $Exe -ErrorAction Stop
        $now = '{0}:{1}' -f $fi.Length, [int](Get-Date $fi.LastWriteTimeUtc -UFormat %s)
        return ($pin -eq $now)
    } catch { return $null }
}

# Insurance for the mode-3 firewall verification: a temp outbound-block rule that outlives a
# hard kill would break mode 1 with opaque network errors, and the operator would chase the
# wrong cause. Called on the mode-3 path and by the verification runbook -- NOT on every
# launch, since a netsh spawn is ~30-50ms and v0.1 never creates the rule.
function Clear-OsanweFirewallRule {
    try { & netsh advfirewall firewall delete rule name="OSANWE-TEMP-BLOCK-CLAUDE" *> $null } catch { }
}

function Get-LaneStateLine {
    try {
        if (-not (Test-Path -LiteralPath $STATE)) { return $null }
        return (Get-Content -LiteralPath $STATE -Raw -ErrorAction Stop).Trim()
    } catch { return $null }
}

# Evidence channel for the two 2026-09-11 adjudications (added 2026-08-13).
# Sheet C's falsifier reads "if no mode-3 session appears ... by 2026-09-11" and
# NOTHING persisted CLAUDE_LANE_MODE -- absence of evidence would have archived a
# mode 3 that was used but unlogged. One JSONL line per LAUNCH (written at the
# point of no return, after mode-3's daemon/model checks pass, so a refused
# launch never counts as consumption). Outside the vault audit and git.
function Write-LaneUsage {
    param([string]$LaunchMode, [string]$Model)
    try {
        $dir = Join-Path $script:VAULT_ROOT '.claude\state'
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $line = '{{"ts":"{0}","mode":"{1}","model":"{2}","run":"{3}"}}' -f `
            (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'), $LaunchMode, $Model, "$env:CLAUDE_LANE_RUN"
        Add-Content -LiteralPath (Join-Path $dir 'lane-usage.jsonl') -Value $line -Encoding ascii
    } catch { }
}

# --- menu ----------------------------------------------------------------------------

function Show-Menu {
    # TimeoutSec 0 = WAIT FOR A CHOICE, no countdown. That is the default: a menu the
    # operator asked for must not decide for him while he reads it. Set
    # $env:CLAUDE_MENU_TIMEOUT to a positive number if an auto-default is ever wanted.
    param($Lane, [bool]$DaemonUp, [bool]$PinOk, [int]$TimeoutSec = 0)

    $vt    = -not [Console]::IsOutputRedirected
    $dim   = if ($vt) { "`e[38;5;244m" } else { '' }
    $cyan  = if ($vt) { "`e[38;5;117m" } else { '' }
    $green = if ($vt) { "`e[38;5;150m" } else { '' }
    $red   = if ($vt) { "`e[38;5;210m" } else { '' }
    $yell  = if ($vt) { "`e[38;5;186m" } else { '' }
    $rst   = if ($vt) { "`e[0m" } else { '' }

    $model = if ($Lane -and $Lane.model) { [string]$Lane.model } else { '(local-lane.json unreadable)' }
    $dstat = if ($DaemonUp) { "${green}up${rst}" } else { "${dim}down (starts on demand)${rst}" }

    Write-Host ''
    Write-Host "  ${cyan}Claude Code -- pick a lane${rst}"
    Write-Host ''
    Write-Host "   1  Claude Code     ${dim}subscription -- frontier tier per /model   [default]${rst}"
    Write-Host "   2  OpenCode        ${dim}choose a live model -- Go plan / Zen free / Zen paid${rst}"
    Write-Host "   3  Fully local     ${dim}$model -- no subscription draw, no Anthropic inference${rst}"
    Write-Host ''
    Write-Host "   ${dim}ollama:${rst} $dstat    ${dim}lane:${rst} $model"
    if ($PinOk -eq $false) {
        Write-Host "   ${red}claude.exe changed since the verified build${rst} ${dim}-- mode 2 lane guards are UNVERIFIED${rst}"
    }
    Write-Host ''

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ($true) {
        try {
            if ([Console]::KeyAvailable) {
                $k = [Console]::ReadKey($true)
                switch ($k.Key) {
                    'Enter'  { Write-Host ''; return 1 }
                    'Escape' { Write-Host ''; return 0 }
                    default {
                        switch ($k.KeyChar) {
                            '1' { Write-Host ''; return 1 }
                            '2' { Write-Host ''; return 2 }
                            '3' { Write-Host ''; return 3 }
                            'q' { Write-Host ''; return 0 }
                            default { }   # unrecognized keys are IGNORED and never reset the countdown
                        }
                    }
                }
            }
        } catch {
            # Hosts without a real key buffer throw on KeyAvailable/ReadKey. Default lane.
            Write-Host ''
            return 1
        }

        if ($TimeoutSec -gt 0) {
            $left = [int][Math]::Ceiling(($deadline - (Get-Date)).TotalSeconds)
            if ($left -le 0) { Write-Host ''; return 1 }
            Write-Host ("`r  > pick a lane ${dim}(1/2/3, Enter = 1, q to cancel)${rst} ${dim}[${left}s]${rst}   ") -NoNewline
        } else {
            Write-Host ("`r  > pick a lane ${dim}(1/2/3, Enter = 1, q to cancel)${rst}   ") -NoNewline
        }
        Start-Sleep -Milliseconds 120
    }
}

# --- mode wiring ---------------------------------------------------------------------

function Invoke-Mode1 {
    # NB: never name this parameter $Args -- that collides with PowerShell's automatic
    # $args variable and the splat silently arrives EMPTY, which sends claude.exe into
    # print mode with no prompt. Caught in smoke testing.
    param([string]$Exe, [string[]]$ExtraArgs)
    $env:CLAUDE_LANE_MODE = 'sub'
    Write-LaneUsage -LaunchMode 'sub' -Model '-'

    # Refresh Anthropic's credential-free catalog on each entry. A per-launch
    # request ceiling covers its advertised outputs; Claude applies each selected
    # model's own supported cap, including after /model switches. No model is pinned.
    # Empty AUTO_COMPACT_WINDOW overrides the old user setting with native auto sizing.
    $subOverlay = Join-Path $script:VAULT_ROOT 'config\mode-sub.settings.json'
    if (Test-Path -LiteralPath $subOverlay) {
        $temporaryOverlay = $null
        try {
            $settings = Get-Content -LiteralPath $subOverlay -Raw -ErrorAction Stop | ConvertFrom-Json -AsHashtable -ErrorAction Stop
            try {
                $catalog = Invoke-RestMethod -Uri 'https://downloads.claude.ai/model-catalog/v1/catalog.json' `
                    -Headers @{ 'Cache-Control' = 'no-cache'; Pragma = 'no-cache' } -TimeoutSec 12 -ErrorAction Stop
                if ($catalog.schema_version -ne 1 -or -not $catalog.expires_at -or
                    [DateTimeOffset]$catalog.expires_at -le [DateTimeOffset]::UtcNow) { throw 'Native model catalog is unsupported or expired.' }
                $models = @($catalog.surfaces.cc.model_selector_config | Where-Object id -EQ cc | ForEach-Object { $_.models } | Where-Object { $_.id -match '^claude-' })
                if (-not $models.Count) { throw 'Native model limits were missing.' }
                $ceiling = 0; $beyondVerifiedClient = $false
                foreach ($model in $models) {
                    $inputLimit = 0; $outputLimit = 0
                    if (-not [int]::TryParse([string]$model.runtime.max_input_tokens, [ref]$inputLimit) -or $inputLimit -le 0 -or
                        -not [int]::TryParse([string]$model.runtime.max_output_tokens, [ref]$outputLimit) -or $outputLimit -le 0) { throw 'Native model limits were invalid.' }
                    $ceiling = [Math]::Max($ceiling, $outputLimit)
                    if ($inputLimit -gt 1000000 -or $outputLimit -gt 128000) { $beyondVerifiedClient = $true }
                }
                $settings.env.CLAUDE_CODE_MAX_OUTPUT_TOKENS = [string]$ceiling
                Write-Host "  Native limits refreshed: $($models.Count) models; Claude applies each model's supported caps." -ForegroundColor DarkGray
                if ($beyondVerifiedClient) {
                    Write-Host '  Catalog limits exceed the native support verified in Claude Code 2.1.278 (1M context / 128K output). Claude Code must support the newer limits too; a larger setting alone cannot enable them.' -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  Native catalog refresh unavailable: $($_.Exception.Message) Using the saved output ceiling and Claude's built-in model limits." -ForegroundColor Yellow
            }
            $temporaryOverlay = Join-Path ([IO.Path]::GetTempPath()) ('claude-native-' + [guid]::NewGuid().ToString('N') + '.settings.json')
            [IO.File]::WriteAllText($temporaryOverlay, ($settings | ConvertTo-Json -Depth 8))
            & $Exe --settings $temporaryOverlay @ExtraArgs
        } finally {
            if ($temporaryOverlay -and (Test-Path -LiteralPath $temporaryOverlay)) { Remove-Item -LiteralPath $temporaryOverlay -ErrorAction SilentlyContinue }
        }
    } else {
        & $Exe @ExtraArgs
    }
}

# Option 2 uses the live Go/Zen picker. Failures return here without another lane.
function Invoke-Mode2 {
    param([string]$Exe, [string[]]$ExtraArgs)
    $picker = Join-Path $script:VAULT_ROOT 'tools\opencode-menu.ps1'
    if (-not (Test-Path -LiteralPath $picker)) {
        Write-Host '  OpenCode model picker is missing -- nothing launched.' -ForegroundColor Red
        return
    }
    . $picker
    Invoke-OpenCodeLane -Exe $Exe -ExtraArgs $ExtraArgs
}

function Invoke-Mode2Retired {
    param([string]$Exe, [string[]]$ExtraArgs, $Lane)

    # RETIRED 2026-09-02: the pre-Muse mode 2 (subscription frontier + background-armed
    # local lanes). Kept verbatim and UNREFERENCED so the previous behaviour is one rename
    # away if the Muse lane is ever abandoned. Nothing calls this.
    $env:CLAUDE_LANE_MODE = 'hybrid'
    Write-LaneUsage -LaunchMode 'hybrid' -Model $(if ($Lane -and $Lane.model) { [string]$Lane.model } else { 'unknown' })

    # Fire-and-forget arming. The session starts NOW; the statusline chip reports
    # WARMING -> ARMED/DISARMED as it resolves. Doctrine permits this: lane absence is
    # never a HALT, and arm-before-delegate is the orchestrator's obligation anyway.
    try {
        Set-Content -LiteralPath $STATE -Value ('WARMING|{0}|{1}|arming' -f `
            $(if ($Lane -and $Lane.model) { $Lane.model } else { 'unknown' }), (Get-Date -Format 'HH:mm:ss')) `
            -Encoding ascii -NoNewline -ErrorAction SilentlyContinue
        Start-Process -FilePath 'pwsh' `
            -ArgumentList @('-NoLogo','-NoProfile','-NonInteractive','-File', $ARM_PS1) `
            -WindowStyle Hidden -ErrorAction Stop | Out-Null
    } catch {
        Write-Host '  (lane arming could not start -- run: python tools/delegate.py --check)'
    }

    # Banner: two-lane capability facts + STANDING CONSENT. Selection-is-consent was
    # operator-ratified 2026-08-16 (Calendar/daily/2026-08-16.md Decisions row): picking
    # mode 2 IS the session authorization for route-local + research:* legs; the frontier routes
    # delegable classes by default. Never-local classes stay refused by leg_status()
    # regardless. Single-quoted here-string; $RUN is interpolated by a targeted Replace
    # below (an earlier build shipped the literal string -- BACKLOG 2026-08-16 defect).
    $banner = @'
LAUNCH MODE: HYBRID (launcher-selected). You are the frontier orchestrator on the Anthropic subscription (whichever tier this session is running).
TWO local lanes were armed in the background at launch (verify: python
/path/to/vault/tools/delegate.py --check):
  DELEGATE lane -- single-shot, TOOL-FREE extraction legs (tools/delegate.py).
  RESEARCHER lane -- tool-capable, mechanically contained acquisition legs
  (tools/relay.py: fetch_url/MCP/jailed reads, driver-owned context relay,
  ask_frontier escalation).

STANDING CONSENT (operator-ratified 2026-08-16, selection-is-consent): picking THIS
launch mode IS the session authorization for ROUTE-LOCAL and research:* legs -- route
delegable leg classes to the lanes by default; every judgment call stays frontier.
NEVER-LOCAL classes remain refused by leg_status() regardless of consent. Delegation
is main-loop only. Delegated and relayed output is INPUT, not truth -- verify it with
the checker that would have checked it anyway. Exit codes: 0 ok, 2 lane unavailable,
3 refused/bad usage, 4 unusable output, 5 (relay only) partial OR awaiting-guidance
with a VALID distillate attached -- consume it; for awaiting-guidance write the
envelope's guidance file and re-run --resume. Any OTHER non-zero exit ALWAYS means
run the leg yourself, never skip it and never report it as done. Lane absence is
NEVER a halt.

  delegate a leg:   python /path/to/vault/tools/delegate.py "<instruction>" [--file P] [--json] --leg <id>
  relay a mission:  python /path/to/vault/tools/relay.py --leg research:<id> --mission <spec.json>
  legs for a skill: python /path/to/vault/tools/delegate.py --legs invest  (or --legs research)
  receipts:         python /path/to/vault/tools/delegate.py --report --run $RUN

At session close, report which legs went local and which model ran them.
Doctrine: docs/osanwe-runtime-reference.md, "Local model lane".
On any conflict with AGENTS.md, AGENTS.md wins.
'@
    $banner = $banner.Replace('$RUN', $env:CLAUDE_LANE_RUN)

    & $Exe --append-system-prompt $banner @ExtraArgs
}

# NB: Invoke-Mode3 must be dispatched BARE, never `$rc = Invoke-Mode3 ...` -- assigning
# captures the function's OUTPUT STREAM, which includes the spawned claude.exe's stdout.
# A captured stdout is not a TTY, so claude auto-selects --print mode and dies with
# "Input must be provided either through stdin or as a prompt argument" (first live TTY
# test, 2026-08-13). Refusal paths therefore Write-Host and return NOTHING.
function Write-Mode3NotLaunched {
    Write-Host '  (mode 3 unavailable -- nothing launched. Run claude again for another lane.)'
}

function Invoke-Mode3 {
    param([string]$Exe, [string[]]$ExtraArgs, $Lane)
    # >>> LocalAI three-state dispatch >>>  DO NOT EDIT BY HAND
    # Added by /path/to/local\tools\mode3_patch.py.
    # Remove with: python /path/to/local\tools\mode3_patch.py --rollback
    #
    # Delegates to the LocalAI launch contract when the current directory is inside a
    # registered LocalAI root. Invoke-LocalAILaunch returns $true when it handled the
    # launch -- including when it REFUSED -- and $false for NOT_LOCALAI, in which case the
    # vault path below continues exactly as it did before this block existed.
    #
    # The "might this be LocalAI's" test below is intentionally over-inclusive: delegating
    # wrongly costs a returned $false, while failing to delegate re-opens R-18, a
    # vault-governed session inside /path/to/local. An unreadable registry therefore delegates.
    $__localaiContract = '/path/to/local\tools\launch.ps1'
    if (Test-Path -LiteralPath $__localaiContract) {
        $__localaiRoot = Split-Path -Parent (Split-Path -Parent $__localaiContract)
        $__here = (Get-Location).Path.TrimEnd('\')
        $__cmp = [StringComparison]::OrdinalIgnoreCase
        $__maybe = $__here.Equals($__localaiRoot.TrimEnd('\'), $__cmp) -or
                   $__here.StartsWith($__localaiRoot.TrimEnd('\') + '\', $__cmp)
        if (-not $__maybe) {
            $__reg = '/path/to/programdata\QwenHost\registry\workspaces.json'
            if (Test-Path -LiteralPath $__reg) {
                try {
                    foreach ($__r in (Get-Content -Raw -LiteralPath $__reg |
                                      ConvertFrom-Json).roots) {
                        $__c = ([string]$__r.canonical_root).TrimEnd('\')
                        if ($__here.Equals($__c, $__cmp) -or
                            $__here.StartsWith($__c + '\', $__cmp)) { $__maybe = $true; break }
                    }
                } catch { $__maybe = $true }
            }
        }
        if ($__maybe) {
            . $__localaiContract
            if (Invoke-LocalAILaunch -Rest $ExtraArgs) { return }
        }
    }
    # <<< LocalAI three-state dispatch <<<


    if (-not $Lane -or -not $Lane.model) {
        Write-Host '  local-lane.json unreadable or has no model -- refusing to launch mode 3.' -ForegroundColor Red
        Write-Host '  fix: /path/to/vault\config\local-lane.json (the SSOT for the local model)'
        Write-Mode3NotLaunched
        return
    }
    $tag      = [string]$Lane.model
    $laneHost = Get-LaneHost $Lane

    # Daemon is REQUIRED here -- unlike mode 2 there is no frontier model to fall back to.
    # Refuse rather than fall back: a silent fallback would put a subscription session where
    # the operator asked for a local one, which is the wrong direction to fail.
    if (-not (Test-DaemonFast $laneHost 400)) {
        Write-Host '  starting ollama daemon ...' -NoNewline
        $ollama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
        if (-not (Test-Path -LiteralPath $ollama)) {
            Write-Host "`r  ollama.exe not found -- mode 3 needs it. Not falling back to the subscription." -ForegroundColor Red
            Write-Mode3NotLaunched
            return
        }
        $ctx = if ($Lane.ctx) { [string]$Lane.ctx } else { '131072' }
        $env:OLLAMA_CONTEXT_LENGTH    = $ctx
        $env:OLLAMA_HOST              = '127.0.0.1:11434'
        $env:OLLAMA_MAX_LOADED_MODELS = '1'
        # 1 slot. The previous comment claimed "2 x 262144 == the old 4 x 131072" and
        # that is arithmetically false: 524,288 vs 524,288 only holds if you ignore that
        # ctx DOUBLED, so the real KV budget doubled with it. lane-arm.ps1:83 was
        # corrected to 1 on 2026-08-15, noting ollama derates 2 to `-np 1` in practice.
        # MEASURED 2026-08-18 at 1 slot: 30,094 MiB of 32,607 used with 262144 loaded,
        # 2,513 free -- there is no headroom for a second slot. Above that it OOMs with
        # "failed to allocate buffer for rs cache": the recurrent-state cache for the 48
        # Gated DeltaNet layers is a THIRD consumer beside weights and KV, and no KV
        # calculator accounts for it.
        $env:OLLAMA_NUM_PARALLEL      = '1'
        # Mode 3 inherited the ambient 30m keep-alive whenever it cold-started the
        # daemon, paying an ~18 GB reload on any session begun more than half an hour
        # after the last. lane-arm.ps1 already pins 8h; this makes a launcher-started
        # daemon match it instead of silently differing.
        $env:OLLAMA_KEEP_ALIVE        = '8h'
        $env:OLLAMA_ORIGINS           = ''
        $logDir = Join-Path $env:LOCALAPPDATA 'Ollama'
        if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
        try {
            Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden `
                -RedirectStandardError (Join-Path $logDir 'server-launcher.log') `
                -RedirectStandardOutput (Join-Path $logDir 'server-launcher.out.log') | Out-Null
        } catch {
            Write-Host "`r  could not start the ollama daemon -- mode 3 unavailable." -ForegroundColor Red
            Write-Mode3NotLaunched
            return
        }
        $deadline = (Get-Date).AddSeconds(30); $up = $false
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 400
            if (Test-DaemonFast $laneHost 800) { $up = $true; break }
        }
        if (-not $up) {
            Write-Host "`r  ollama did not answer within 30s -- mode 3 unavailable." -ForegroundColor Red
            Write-Mode3NotLaunched
            return
        }
        Write-Host "`r  ollama daemon ready.                    "
    }

    # Model must actually be installed. Never auto-pull: muse-glimmer is a local build.
    try {
        $tags = (Invoke-WebRequest -Uri "$laneHost/api/tags" -TimeoutSec 5 -UseBasicParsing).Content |
                ConvertFrom-Json | ForEach-Object { $_.models.name }
    } catch { $tags = @() }
    if ($tags -and ($tags -notcontains $tag)) {
        Write-Host "  '$tag' is not installed on $laneHost." -ForegroundColor Red
        Write-Host "  installed: $($tags -join ', ')"
        Write-Host '  fix: python tools/delegate.py --use <exact tag>   (do NOT auto-pull -- this is a local build)'
        Write-Mode3NotLaunched
        return
    }

    # --- system-message normalizer (mode 3 cannot make ONE successful call without it) ---
    # Ollama's built-in qwen3.8 RENDERER accepts exactly one system message, at position 0.
    # Claude Code sends a top-level `system` list AND a trailing system message, so every
    # request 500s with "system message must be at the beginning". The normalizer merges
    # them and forwards verbatim. Gate: wiki/research/gates/gate-b-mode3-system-message-normalizer-2026-08-14.md
    # REMOVAL TRIGGER: when an Ollama release fixes the renderer, delete the proxy and set
    # $inferenceHost back to $laneHost. tools/mode3-selftest.py decides that.
    $normPort = 11435
    $inferenceHost = "http://127.0.0.1:$normPort"
    if (-not (Test-DaemonFast $inferenceHost 400)) {
        # $logDir is only assigned on the daemon-COLD path above; re-derive it here so an
        # already-running daemon does not leave Start-Process with an empty redirect path.
        $logDir = Join-Path $env:LOCALAPPDATA 'Ollama'
        if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
        $py = 'python'
        if (Test-Path -LiteralPath '/path/to/python\python.exe') { $py = '/path/to/python\python.exe' }
        try {
            Start-Process -FilePath $py `
                -ArgumentList @((Join-Path $script:VAULT_ROOT 'tools\mode3-normalize-proxy.py'), '--port', "$normPort") `
                -WindowStyle Hidden `
                -RedirectStandardError (Join-Path $logDir 'mode3-normalizer.log') `
                -RedirectStandardOutput (Join-Path $logDir 'mode3-normalizer.out.log') | Out-Null
        } catch {
            Write-Host '  could not start the mode-3 normalizer -- mode 3 unavailable.' -ForegroundColor Red
            Write-Mode3NotLaunched
            return
        }
        $deadline = (Get-Date).AddSeconds(15); $normUp = $false
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 300
            if (Test-DaemonFast $inferenceHost 800) { $normUp = $true; break }
        }
        if (-not $normUp) {
            Write-Host '  mode-3 normalizer did not answer within 15s -- mode 3 unavailable.' -ForegroundColor Red
            Write-Mode3NotLaunched
            return
        }
    }

    Write-Host "  starting FULLY LOCAL session on $tag (first load can take 30-60s) ..."
    Clear-OsanweFirewallRule
    $env:CLAUDE_LANE_MODE = 'local'
    Write-LaneUsage -LaunchMode 'local' -Model $tag
    try {
        Set-Content -LiteralPath $STATE -Value ("ARMED|{0}|{1}|mode 3 whole-session local" -f $tag, (Get-Date -Format 'HH:mm:ss')) `
            -Encoding ascii -NoNewline -ErrorAction SilentlyContinue
    } catch { }

    # Per-process env dictionary semantics: every var is set immediately before the spawn and
    # the shim's finally restores the lot. ANTHROPIC_AUTH_TOKEN (not _API_KEY) is deliberate --
    # the M3-AUTH probe confirmed the client presents ONLY this value and never an sk-ant*
    # credential, and AUTH_TOKEN also avoids the "Detected a custom API key" first-run prompt.
    # Points at the NORMALIZER, not the daemon -- see the mode-3 normalizer block above.
    $env:ANTHROPIC_BASE_URL             = $inferenceHost
    $env:ANTHROPIC_AUTH_TOKEN           = 'ollama-local-no-credential'
    $env:ANTHROPIC_DEFAULT_FABLE_MODEL  = $tag
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL   = $tag
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL = $tag
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL  = $tag
    $env:ANTHROPIC_SMALL_FAST_MODEL     = $tag
    # Base-URL redirection covers the INFERENCE path only. /v1/sessions, /v1/files, mcp-proxy
    # and the Datadog log intakes are separate endpoints and would still be authenticated.
    $env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1'
    $env:DISABLE_TELEMETRY                        = '1'
    $env:DO_NOT_TRACK                             = '1'
    $env:CLAUDE_CODE_NO_MODEL_FALLBACK            = '1'
    # DELIBERATELY NOT SET: CLAUDE_CODE_SUBAGENT_MODEL (X12 -- never, at any scope).

    $banner = @'
LAUNCH MODE: FULLY LOCAL. Every inference token in this session is served by a local model
on this machine via Ollama's Anthropic-compatible endpoint. There is no subscription model
here and no Anthropic inference call. You are a small local model: smaller context and
weaker judgment than the frontier models this vault is normally driven by. Work accordingly.

HARD CONSTRAINTS for this session, from the gate sheet that authorized this mode
(wiki/research/gates/gate-b-whole-session-local-2026-08-12.md):
  - NO decision records, verdicts, ratings, thesis-status calls, conviction or kill criteria,
    and no skeptic/verification legs. Those are frontier-only.
  - NO money-adjacent work of ANY kind, including portfolio reads and doctrine math, even
    though the Robinhood read tools exist in this session.
  - NEVER the closing session: do not run /retro. Append one-line entries to today's daily
    note and hand the close to a normal (mode 1) session.
  - The four append-only ledgers -- sessions-log.md, decision-log.md, execute-or-decline.md,
    insight-stream.md -- are OFF LIMITS. tools/append-only-check.py now BLOCKS any tool-layer
    write there that does not preserve the existing bytes as a strict prefix, so an accidental
    rewrite fails loudly rather than silently. That guard does NOT cover Bash-layer writes
    (X30), so the rule remains yours to honor: append, never regenerate.

Keep work MECHANICAL and CHECKABLE: reformatting, ASCII/frontmatter normalization, extraction
into a fixed schema, dedup, bulk sweeps -- the kind of work a checker can validate afterward.
When unsure whether something is in scope, stop and say so rather than guessing.
On any conflict with AGENTS.md, AGENTS.md wins.
'@

    # Sizing overlay. This is NOT optional and env vars cannot do it: settings `env` blocks
    # are Object.assign'd OVER process env, and the user-scope settings declare a 1,000,000
    # token window with auto-compact at 750k -- against a daemon that truncates at 131k.
    # Only --settings (flagSettings) outranks user settings. MEASURED 2026-08-12: an in-vault
    # mode-3 session opens at ~95k tokens of SessionStart injection, i.e. 73% of the window
    # before the first word, so correct compaction thresholds matter immediately.
    # The file is STRICT JSON with no comments on purpose: `-p` silently ignores a settings
    # file that fails validation, which would restore the 1M belief with no error anywhere.
    # TOOL SURFACE DIET (2026-08-15). MEASURED, not estimated: a captured in-vault mode-3
    # request carried 116 tool definitions totalling 153,822 bytes (~42,700 tok) out of a
    # ~56,000-token prompt -- the single largest component, larger than the entire vault
    # instruction surface. Breakdown: 86 MCP tools 71,178 B (robinhood-trading 34 / 38,283 B,
    # openinsider 16 / 14,410 B, claudewatch 32 / 13,188 B, fred 3, vault-search 1) and
    # 30 built-ins 82,412 B, of which `Workflow` ALONE is 21,870 B (~6,075 tok).
    # A local 27B doing mechanical file work calls none of them.
    #   --strict-mcp-config with no --mcp-config loads ZERO MCP servers (~19,771 tok).
    #   The deny list drops orchestration/scheduling/worktree/MCP-resource tools (~18,560 tok).
    # Kept deliberately: Read Write Edit Bash Glob Grep Skill WebFetch WebSearch NotebookEdit.
    # Revert: delete the two flags below. Modes 1-2 are untouched.
    $mode3Deny = @(
        'Workflow','DesignSync','Agent','ReportFindings',
        'CronCreate','CronDelete','CronList','ScheduleWakeup',
        'EnterWorktree','ExitWorktree',
        'TaskCreate','TaskUpdate','TaskList','TaskGet','TaskStop','TaskOutput','SendMessage',
        'ListMcpResourcesTool','ReadMcpResourceTool','ReadMcpResourceDirTool'
    )

    $overlay = Join-Path $script:VAULT_ROOT 'config\mode-local.settings.json'
    if (Test-Path -LiteralPath $overlay) {
        # --exclude-dynamic-system-prompt-sections (added 2026-09-02): moves per-machine
        # system-prompt sections out of the cached prefix and into the first user message.
        # This lane has NO provider-side cache -- it depends entirely on llama.cpp's
        # longest-common-prefix KV reuse, and any per-request churn near the START of the
        # prompt forces a full re-prefill. Paired with CLAUDE_CODE_ATTRIBUTION_HEADER=0 in
        # config/mode-local.settings.json, this is the WS2b prefix-reuse hypothesis
        # (BACKLOG E2). A/B both with tools/lane-bench.py before believing either helped.
        & $Exe --model $tag --settings $overlay --strict-mcp-config `
            --exclude-dynamic-system-prompt-sections `
            --disallowedTools $mode3Deny --append-system-prompt $banner @ExtraArgs
    } else {
        Write-Host '  WARNING: config/mode-local.settings.json missing -- this session will believe it has a 1M context against a 131k daemon.' -ForegroundColor Yellow
        & $Exe --model $tag --append-system-prompt $banner @ExtraArgs
    }
}

# --- main ----------------------------------------------------------------------------

$lane     = Get-Lane
$laneHost = Get-LaneHost $lane
$pinOk    = Test-BinaryPin $ClaudeExe

$choice = 0
if ($Mode -match '^[123]$') {
    $choice = [int]$Mode
} else {
    $daemonUp = Test-DaemonFast $laneHost
    try {
        if ([Console]::IsInputRedirected) {
            $choice = 1
        } else {
            $menuTimeout = 0
            if ($env:CLAUDE_MENU_TIMEOUT -and ($env:CLAUDE_MENU_TIMEOUT -match '^\d+$')) {
                $menuTimeout = [int]$env:CLAUDE_MENU_TIMEOUT
            }
            $prevCtrlC = [Console]::TreatControlCAsInput
            try {
                [Console]::TreatControlCAsInput = $true
                $choice = Show-Menu -Lane $lane -DaemonUp $daemonUp -PinOk $pinOk -TimeoutSec $menuTimeout
            } finally {
                [Console]::TreatControlCAsInput = $prevCtrlC
            }
        }
    } catch {
        $choice = 1
    }
}

if ($choice -eq 0) { return }

# Correlation id: makes `--report --run <id>` correct by construction instead of relying
# on the orchestrator to remember to pass one.
$runId = [guid]::NewGuid().ToString('N').Substring(0, 8)
$env:CLAUDE_LANE_RUN = $runId

switch ($choice) {
    2 { Invoke-Mode2 -Exe $ClaudeExe -ExtraArgs $Rest }   # Bare dispatch preserves the TTY.
    3 { Invoke-Mode3 -Exe $ClaudeExe -ExtraArgs $Rest -Lane $lane }   # BARE dispatch -- see Write-Mode3NotLaunched note
    default { Invoke-Mode1 -Exe $ClaudeExe -ExtraArgs $Rest }
}
