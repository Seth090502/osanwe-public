# claude-shim.ps1 -- the always-on boundary for every `claude` invocation.
#
# Dot-sourced by a 3-line sentinel in the PS7 profile. Defines `function claude`.
# DESIGN RULE: this file is the fail-open boundary and must stay small and boring.
# All feature logic (menu, daemon, mode wiring) lives in claude-launcher.ps1, which
# runs ONLY on a bare interactive invocation. A bug there must never be able to stop
# `claude` from starting.
#
# NODE_OPTIONS is ASSIGNED, never edited. Two undici-timeout preloads exist on this box
# (HKLM machine-scope --require /path/to/home\undici-timeout-preload.cjs, and the
# retired-OpenClaw copy under .openclaw). Both set infinite undici timeouts and hang
# claude's interactive startup. Assignment kills both; substring-stripping misses one.
#
# The env jail is a NAMESPACE SCRUB with a keep-list, not a name denylist: the binary
# reads ~430 CLAUDE_CODE_* and ~63 ANTHROPIC_* variables and a denylist cannot survive
# the vendor adding one. X12 is the standing lesson -- no ambient variable may select a
# model or an endpoint. Nothing here selects a model; mode 3 selects with a visible flag.

Set-Variable -Name OSANWE_SHIM_VERSION -Value '1' -Scope Script -Force

function Get-OsanweJailNames {
    # Keep-list: variables that must survive the scrub for Claude Code to work here.
    $keep = @(
        'CLAUDE_CODE_GIT_BASH_PATH',   # live at HKCU; Bash tool breaks without it
        'CLAUDE_CONFIG_DIR',
        'ANTHROPIC_CONFIG_DIR'
    )
    $names = @()
    foreach ($e in [Environment]::GetEnvironmentVariables().Keys) {
        $n = [string]$e
        if ($keep -contains $n) { continue }
        if ($n -like 'ANTHROPIC_*' -or $n -like 'OPENAI_*' -or $n -like 'CLAUDE_CODE_*') {
            $names += $n
        }
    }
    # Named individually: outside those three namespaces but still model/route steering.
    # OLLAMA_HOST added 2026-08-13: Get-LaneHost reads it AHEAD of the SSOT and
    # Invoke-Mode3 assigns the result to ANTHROPIC_BASE_URL -- an ambient value could
    # redirect a "fully local" session off-box (the X12 shape). The SSOT `host` field
    # in config/local-lane.json is the sanctioned channel; mode 3 sets its own
    # OLLAMA_HOST explicitly after the scrub.
    # DISABLE_TELEMETRY / DO_NOT_TRACK added 2026-09-04: they are not model/route steering, they
    # are FEATURE steering, which the jail must catch for the same reason. Either one makes
    # claude.exe skip feature-flag evaluation entirely (binary q8t(); the third member of that
    # set, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC, is already covered by the wildcard above),
    # and /remote-control is gated on the tengu_ccr_bridge flag -- so an ambient DISABLE_TELEMETRY
    # in the PS7 profile silently disabled Remote Control in every lane-1 session. Diagnosed with
    # `claude doctor`, which names the offending variable. Modes 2 and 3 set both vars themselves
    # AFTER this scrub, so their no-telemetry posture is unchanged.
    foreach ($n in @('OLLAMA_MODEL','OLLAMA_HOST','NODE_EXTRA_CA_CERTS','DISABLE_TELEMETRY','DO_NOT_TRACK')) {
        if (($names -notcontains $n) -and ($null -ne [Environment]::GetEnvironmentVariable($n))) {
            $names += $n
        }
    }
    return $names
}

function claude {
    $exe      = Join-Path $HOME '.local\bin\claude.exe'
    $launcher = '/path/to/vault\tools\claude-launcher.ps1'

    # --- env jail: snapshot, scrub, restore in finally -------------------------------
    # Assignment ($env:X = $null) removes; Remove-Item/Set-Item cost 10-25ms and pollute
    # $Error. Restoring $null removes again, so unset/empty/valued all round-trip exactly.
    # FULL environment snapshot, not a name list. The scrub only needs the jail names, but the
    # RESTORE has to undo everything this call touches -- and mode 3 sets eight ANTHROPIC_*,
    # four CLAUDE_CODE_*/telemetry vars, five OLLAMA_* daemon pins and two CLAUDE_LANE_* vars,
    # most of which did not exist at entry and several of which fall outside the guarded
    # namespaces entirely (DO_NOT_TRACK, DISABLE_TELEMETRY, OLLAMA_HOST...). Enumerating them
    # by name was tried and leaked four; a snapshot cannot drift as the launcher grows.
    # Cost is one hashtable of a few hundred strings, microseconds. Only OUR code mutates this
    # process env -- the child is a separate process -- so a wholesale restore is safe.
    $envBefore = @{}
    foreach ($e in [Environment]::GetEnvironmentVariables().GetEnumerator()) {
        $envBefore[[string]$e.Key] = [string]$e.Value
    }

    $jail = Get-OsanweJailNames
    foreach ($n in $jail) { Set-Item -Path "Env:\$n" -Value $null -ErrorAction SilentlyContinue }
    $env:NODE_OPTIONS = '--max-old-space-size=16384'   # restored by the snapshot in finally
    $env:CLAUDE_LANE_JAIL = '1'   # session-integrity-check warns if this is missing

    try {
        # CLAUDE_CODE_SIMPLE is an exact env-equivalent of --bare: hooks, LSP, plugin
        # sync, auto-memory, keychain reads and CLAUDE.md/AGENTS.md discovery all skipped,
        # and the session looks completely normal. The scrub above removes it; this is the
        # assertion that it actually went, because a normal-looking guardless session is
        # the worst failure this shim can have.
        if ($env:CLAUDE_CODE_SIMPLE -or $env:CLAUDE_CODE_SAFE_MODE) {
            Write-Host '  claude-shim: REFUSING -- CLAUDE_CODE_SIMPLE/SAFE_MODE survived the env jail.' -ForegroundColor Red
            Write-Host '  That would run this session with hooks and CLAUDE.md discovery SKIPPED.'
            Write-Host '  Fix the environment (check HKCU\Environment), then retry.'
            return
        }

        $bare = ($args.Count -eq 0) -and (-not $MyInvocation.ExpectingInput)

        # --mode <n> is the ONE consumed flag (scripting/testing hook). claude.exe has no
        # --mode of its own (only --permission-mode), so this is unambiguous.
        $modeArg = '0'
        $rest    = @($args)
        if ($rest.Count -ge 2 -and $rest[0] -eq '--mode') {
            $modeArg = [string]$rest[1]
            $rest    = @($rest[2..($rest.Count - 1)])
            $bare    = $true
        }

        if ($bare -and (Test-Path -LiteralPath $launcher)) {
            & $launcher -ClaudeExe $exe -Mode $modeArg -Rest $rest
        }
        elseif ($MyInvocation.ExpectingInput) {
            # Forward piped bytes. Without this the pipeline is silently dropped.
            $input | & $exe @args
        }
        else {
            & $exe @args
        }
    }
    finally {
        # Exact restore to the entry snapshot: drop anything added, put back anything changed
        # or removed. This covers NODE_OPTIONS, CLAUDE_LANE_JAIL and every var any mode set,
        # so the parent shell is byte-identical after `claude` returns -- including after a
        # mode-3 session, which would otherwise leave the terminal pointed at the local
        # endpoint for any other Anthropic-SDK tool started from it.
        foreach ($e in @([Environment]::GetEnvironmentVariables().Keys)) {
            $n = [string]$e
            if (-not $envBefore.ContainsKey($n)) { Set-Item -Path "Env:\$n" -Value $null -ErrorAction SilentlyContinue }
        }
        foreach ($kv in $envBefore.GetEnumerator()) {
            if ([Environment]::GetEnvironmentVariable($kv.Key) -ne $kv.Value) {
                Set-Item -Path "Env:\$($kv.Key)" -Value $kv.Value -ErrorAction SilentlyContinue
            }
        }
    }
}

function claude-rc { claude --remote-control @args }
