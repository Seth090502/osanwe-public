# START-CLAUDE-OX.ps1 — Ox Alpha chief via Claude Code + OpenRouter (isolated profile)
# Process-local environment only. Does not touch Qwen config, global env, PATH, or profiles.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClaudeArgs
)

$ErrorActionPreference = "Stop"

$Root   = Split-Path -Parent $MyInvocation.MyCommand.Path
$OxRoot = Join-Path $Root ".runtime\claude-ox"
$Exe    = "/path/to/home\.local\bin\claude.exe"   # genuine Claude Code 2.1.237 native binary

if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { throw "Claude Code executable not found: $Exe" }
foreach ($d in @("profile", "secrets", "temp", "logs")) {
    New-Item -ItemType Directory -Path (Join-Path $OxRoot $d) -Force | Out-Null
}

Set-Location $Root

# 1) Isolated Claude profile (mandatory separation from the Qwen Claude environment)
$env:CLAUDE_CONFIG_DIR = Join-Path $OxRoot "profile"
$env:TEMP = Join-Path $OxRoot "temp"
$env:TMP  = $env:TEMP
$env:DISABLE_AUTOUPDATER = "1"

# 2) Windows TUI hardening: full frame repaint in fullscreen renderer (prevents stale/misplaced
#    fragments on Windows Terminal / ConPTY hosts). Process-local only.
$env:CLAUDE_CODE_ALT_SCREEN_FULL_REPAINT = "1"

# 2b) Full-context accounting for custom-gateway model (stealth/ox-alpha = 1,048,576 tokens).
#     Recognized by installed 2.1.237 build (verified in binary env table).
#     Auto-compaction RE-ARMED at 87.5% of the real window (917,504 tokens) via
#     CLAUDE_CODE_AUTO_COMPACT_WINDOW (verified in binary: env-sourced token window).
#     NOTE: earlier builds' docs required DISABLE_COMPACT=1 for the override; that tradeoff is
#     no longer accepted. If /context ever reverts to ~200K, restore DISABLE_COMPACT=1 and
#     remove AUTO_COMPACT_WINDOW (known-good fallback).
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS = "1048576"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "917504"

# 3) Decrypt OpenRouter key via DPAPI CurrentUser (child process environment only)
Add-Type -AssemblyName System.Security
$enc = [IO.File]::ReadAllBytes((Join-Path $OxRoot "secrets\openrouter.dpapi"))
$plain = [Text.Encoding]::UTF8.GetString(
    [System.Security.Cryptography.ProtectedData]::Unprotect(
        $enc, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser))
if ($plain -notmatch '^sk-or-v1-[0-9a-f]{64}$') { throw "Stored OpenRouter key failed shape validation" }

# 4) OpenRouter Anthropic-compatible gateway, process-local only
$env:ANTHROPIC_BASE_URL  = "https://openrouter.ai/api"
$env:ANTHROPIC_AUTH_TOKEN = $plain
$env:ANTHROPIC_API_KEY   = ""

# 5) Pin every model slot to Ox Alpha — no silent fallback to Anthropic or other models
$env:ANTHROPIC_MODEL               = "stealth/ox-alpha"
$env:ANTHROPIC_SMALL_FAST_MODEL    = "stealth/ox-alpha"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL  = "stealth/ox-alpha"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "stealth/ox-alpha"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "stealth/ox-alpha"

$plain = $null
$enc   = $null

Write-Host ""
Write-Host "CLAUDE CODE — OX ALPHA CHIEF (OpenRouter stealth/ox-alpha)" -ForegroundColor Cyan
Write-Host "  profile: $($env:CLAUDE_CONFIG_DIR)"
Write-Host "  model:   stealth/ox-alpha  effort: max  permissions: bypassPermissions"
Write-Host "  live /path/to/local / /path/to/programdata\QwenHost access: forbidden by discipline"
Write-Host ""

# 6) Real interactive TUI; explicit model + max effort + bypassPermissions; pass-through args
$args_ = @("--model", "stealth/ox-alpha", "--effort", "max", "--dangerously-skip-permissions")
if ($ClaudeArgs) { $args_ += $ClaudeArgs }

$code = 1
try {
    & $Exe @args_
    $code = $LASTEXITCODE
}
finally {
    # 7) Clear sensitive process variables on exit
    $env:ANTHROPIC_AUTH_TOKEN = $null
    $env:ANTHROPIC_API_KEY    = $null
    $plain = $null
}

exit $code
