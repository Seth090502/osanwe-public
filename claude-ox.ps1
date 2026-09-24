# claude-ox.ps1 - Ox Alpha Claude Code for VaultRoot (isolated profile, 1M context, auto-compact)
# Normal permission behavior (no bypass). Qwen environment untouched.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ClaudeArgs)

$ErrorActionPreference = "Stop"
$Ws      = Split-Path -Parent $MyInvocation.MyCommand.Path
$OxRoot  = Join-Path $Ws ".claude-ox"
$Exe     = "/path/to/home\.local\bin\claude.exe"

if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { throw "Claude Code executable not found: $Exe" }
foreach ($d in @("profile", "temp")) { New-Item -ItemType Directory -Path (Join-Path $OxRoot $d) -Force | Out-Null }

Set-Location $Ws

# Isolated profile (own sessions/history/settings - separate from normal claude and from LocalAIResearch)
$env:CLAUDE_CONFIG_DIR = Join-Path $OxRoot "profile"
$env:TEMP = Join-Path $OxRoot "temp"
$env:TMP  = $env:TEMP
$env:DISABLE_AUTOUPDATER = "1"

# Windows rendering hardening + full-context accounting for the custom-gateway model
$env:CLAUDE_CODE_ALT_SCREEN_FULL_REPAINT = "1"
$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS      = "1048576"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW     = "917504"

# OpenRouter credential via shared DPAPI blob (process-local only, never on command line)
Add-Type -AssemblyName System.Security
$enc   = [IO.File]::ReadAllBytes((Join-Path $OxRoot "..\..\LocalAIResearch\.runtime\claude-ox\secrets\openrouter.dpapi"))
$plain = [Text.Encoding]::UTF8.GetString(
    [System.Security.Cryptography.ProtectedData]::Unprotect(
        $enc, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser))
if ($plain -notmatch '^sk-or-v1-[0-9a-f]{64}$') { throw "Stored key failed shape validation" }

$env:ANTHROPIC_BASE_URL   = "https://openrouter.ai/api"
$env:ANTHROPIC_AUTH_TOKEN = $plain
$env:ANTHROPIC_API_KEY    = ""
$env:ANTHROPIC_MODEL               = "stealth/ox-alpha"
$env:ANTHROPIC_SMALL_FAST_MODEL    = "stealth/ox-alpha"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL  = "stealth/ox-alpha"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "stealth/ox-alpha"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "stealth/ox-alpha"

$plain = $null; $enc = $null

Write-Host ""
Write-Host "CLAUDE CODE - OX ALPHA (OpenRouter stealth/ox-alpha) @ VaultRoot" -ForegroundColor Cyan
Write-Host "  profile: $($env:CLAUDE_CONFIG_DIR)"
Write-Host "  model:   stealth/ox-alpha | ctx: ~1M | auto-compact @ 917504"
Write-Host ""

$args_ = @("--model", "stealth/ox-alpha")
if ($ClaudeArgs) { $args_ += $ClaudeArgs }

$code = 1
try {
    & $Exe @args_
    $code = $LASTEXITCODE
}
finally {
    $env:ANTHROPIC_AUTH_TOKEN = $null
    $env:ANTHROPIC_API_KEY    = $null
}
exit $code
