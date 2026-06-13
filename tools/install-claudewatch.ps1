#requires -Version 5.1
<#
install-claudewatch.ps1 -- Phase D1-D4 of the claudewatch install mission.

Downloads + checksum-verifies + places the claudewatch Windows binary, registers
the READ-ONLY MCP server MCP-ONLY (no global behavioral rules, no blocking hook),
and best-effort adds the vault root to claudewatch scan paths.

This script EXECUTES a third-party binary (claudewatch.exe install / mcp). It is
meant to be run by the user, by hand, in the morning -- not autonomously.

Companion (run AFTER this succeeds):  python tools/wire-claudewatch-vault.py
Runbook:                              tools/INSTALL-CLAUDEWATCH.md

Usage:
  powershell -ExecutionPolicy Bypass -File tools/install-claudewatch.ps1
  powershell -ExecutionPolicy Bypass -File tools/install-claudewatch.ps1 -DryRun

Exit 0 on success; 1 on any HARD-step mismatch. Idempotent (safe to re-run).
ASCII-only. No emojis. PowerShell 5.1 compatible.
#>
[CmdletBinding()]
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'

# --- constants ---
$Repo       = 'blackwell-systems/claudewatch'
$Tag        = 'v0.15.0'
$ZipAmd64   = 'claudewatch_0.15.0_windows_amd64.zip'
$ZipArm64   = 'claudewatch_0.15.0_windows_arm64.zip'
$BinDir     = Join-Path $env:USERPROFILE '.local\bin'
$BinPath    = Join-Path $BinDir 'claudewatch.exe'
$ClaudeJson = Join-Path $env:USERPROFILE '.claude.json'
$ConfigDir  = Join-Path $env:USERPROFILE '.config\claudewatch'
$ConfigYaml = Join-Path $ConfigDir 'config.yaml'
$RulesDir   = Join-Path $env:USERPROFILE '.claude\rules'
$ScanPath   = if ($env:VAULT_ROOT) { $env:VAULT_ROOT } else { (Get-Location).Path }

function Say($m)  { Write-Output $m }
function Good($m) { Write-Output ("PASS: " + $m) }
function Warn($m) { Write-Output ("WARN: " + $m) }
function Die($m)  { Write-Output ("FAIL: " + $m); exit 1 }
function Step($n,$d) { Write-Output ""; Write-Output ("=== STEP " + $n + ": " + $d + " ===") }

Say ("install-claudewatch.ps1 -- " + $(if ($DryRun) { 'DRY-RUN (no download, no binary exec, no writes)' } else { 'REAL INSTALL' }))
Say ("binary target: " + $BinPath)

# Architecture select (amd64 vs arm64)
$arch = $env:PROCESSOR_ARCHITECTURE
$zipName = if ($arch -eq 'ARM64') { $ZipArm64 } else { $ZipAmd64 }

# -------------------------------------------------------------------
Step 1 "Download + checksum-verify the release zip"
Say ("arch=" + $arch + " -> asset=" + $zipName)
$dl = Join-Path $env:TEMP 'claudewatch-dl'
if ($DryRun) {
    Say ("DRY-RUN would: gh release download " + $Tag + " -R " + $Repo + " -p " + $zipName + " -p checksums.txt -D " + $dl)
    Say  "DRY-RUN would: compare Get-FileHash SHA256 vs the matching line in checksums.txt; HALT on mismatch"
} else {
    New-Item -ItemType Directory -Force -Path $dl | Out-Null
    gh release download $Tag -R $Repo -p $zipName -p 'checksums.txt' -D $dl --clobber
    if ($LASTEXITCODE -ne 0) { Die ("gh release download failed (exit " + $LASTEXITCODE + ")") }
    $zip = Join-Path $dl $zipName
    if (-not (Test-Path $zip)) { Die ("zip not downloaded: " + $zip) }
    $line = (Select-String -Path (Join-Path $dl 'checksums.txt') -Pattern ([regex]::Escape($zipName)) | Select-Object -First 1).Line
    if (-not $line) { Die ("no checksum line found for " + $zipName) }
    $exp = (($line -split '\s+')[0]).ToLower()
    $act = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
    Say ("EXPECT sha256=" + $exp)
    Say ("ACTUAL sha256=" + $act)
    if ($exp -ne $act) { Die "checksum mismatch -- refusing to extract" }
    Good "checksum verified"
}

# -------------------------------------------------------------------
Step 2 "Extract + place claudewatch.exe on PATH"
if ($DryRun) {
    Say ("DRY-RUN would: Expand-Archive then copy claudewatch.exe -> " + $BinPath)
} else {
    $zip = Join-Path $dl $zipName
    $ex  = Join-Path $dl 'x'
    Remove-Item -Recurse -Force $ex -ErrorAction SilentlyContinue
    Expand-Archive -Path $zip -DestinationPath $ex -Force
    $exe = Get-ChildItem -Path $ex -Recurse -Filter 'claudewatch.exe' | Select-Object -First 1
    if (-not $exe) { Die "claudewatch.exe not found in archive" }
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Copy-Item $exe.FullName $BinPath -Force
    if (-not (Test-Path $BinPath)) { Die ("binary not placed at " + $BinPath) }
    Good ("placed " + $BinPath)
}

# -------------------------------------------------------------------
Step 3 "Smoke: claudewatch --version"
if ($DryRun) {
    Say ("DRY-RUN would: & " + $BinPath + " --version")
} else {
    $ver = (& $BinPath --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { Die ("claudewatch --version exited " + $LASTEXITCODE + ": " + $ver) }
    Say ("ACTUAL version=" + $ver)
    Good "binary runs"
}

# -------------------------------------------------------------------
Step 4 "Register READ-ONLY MCP server (MCP-ONLY: no rules, no hooks)"
# Primary mechanism per approved plan C2: `claudewatch install --mcp-only`.
# Fallback if that flag is absent in this binary build: surgical `claude mcp add`.
if ($DryRun) {
    Say ("DRY-RUN would: back up " + $ClaudeJson + " -> .bak.claudewatch.<ts>")
    Say  "DRY-RUN would: if 'claudewatch install --help' shows --mcp-only -> claudewatch install --mcp-only"
    Say ("DRY-RUN would: else if 'claude' present + binary has 'mcp' subcommand -> claude mcp add -s user claudewatch -- " + $BinPath + " mcp")
    Say  "DRY-RUN would: else HALT and print both --help outputs"
    Say  "DRY-RUN would: verify ~/.claude.json contains a claudewatch mcpServers entry"
    Say  "DRY-RUN would: GUARD that zero ~/.claude/rules/claudewatch-*.md were written (MCP-only invariant)"
} else {
    if (Test-Path $ClaudeJson) {
        $bak = $ClaudeJson + '.bak.claudewatch.' + (Get-Date -Format 'yyyyMMdd-HHmmss')
        Copy-Item $ClaudeJson $bak -Force
        Say ("backed up ~/.claude.json -> " + $bak)
    }
    $registered = $false
    # Primary: claudewatch install --mcp-only (only if the flag exists in this build)
    $ihelp = (& $BinPath install --help 2>&1 | Out-String)
    if ($ihelp -match '--mcp-only') {
        Say "mechanism: claudewatch install --mcp-only (plan C2 primary)"
        & $BinPath install --mcp-only
        if ($LASTEXITCODE -ne 0) { Die ("claudewatch install --mcp-only exited " + $LASTEXITCODE) }
        $registered = $true
    } else {
        Warn "this binary build has no 'install --mcp-only' flag; trying surgical fallback"
        $claude = Get-Command claude -ErrorAction SilentlyContinue
        $help = (& $BinPath --help 2>&1 | Out-String)
        $hasMcpSub = ($help -match '(?m)^\s*mcp\b') -or ($help -match '\bmcp\b')
        if ($claude -and $hasMcpSub) {
            Say "mechanism: claude mcp add -s user (surgical; no rules)"
            & claude mcp add -s user claudewatch -- "$BinPath" mcp
            if ($LASTEXITCODE -ne 0) { Die ("claude mcp add exited " + $LASTEXITCODE) }
            $registered = $true
        }
    }
    if (-not $registered) {
        Say "--- claudewatch --help ---"; & $BinPath --help 2>&1 | Out-String | Write-Output
        Say "--- claudewatch install --help ---"; Write-Output $ihelp
        Die "could not register MCP server MCP-only; inspect the --help output above and register manually"
    }
    if (-not (Test-Path $ClaudeJson)) { Die "~/.claude.json absent after registration" }
    if ((Get-Content $ClaudeJson -Raw) -notmatch 'claudewatch') { Die "~/.claude.json has no claudewatch entry after registration" }
    Good "MCP server registered (claudewatch present in ~/.claude.json)"
    # MCP-only invariant guard: zero global behavioral rules
    $cwRules = @()
    if (Test-Path $RulesDir) { $cwRules = @(Get-ChildItem $RulesDir -Filter 'claudewatch-*.md' -ErrorAction SilentlyContinue) }
    if ($cwRules.Count -gt 0) { Die ("MCP-only invariant BROKEN: " + $cwRules.Count + " claudewatch rule file(s) in " + $RulesDir + " -- expected zero. A full install ran. Remove the rule files (and any claudewatch hook from ~/.claude/settings.json) before wiring.") }
    Good "no global claudewatch behavioral rules written (MCP-only invariant holds)"
}

# -------------------------------------------------------------------
Step 5 "Best-effort: add vault root to claudewatch scan paths (SOFT, non-fatal)"
# Note: vault sessions are ALREADY covered via ~/.claude/projects transcripts.
# scan_paths only affects project-DISCOVERY/health tools. The YAML schema is not
# verifiable before first run, so this step never hard-fails.
if ($DryRun) {
    Say ("DRY-RUN would: ensure " + $ConfigDir + " exists")
    Say ("DRY-RUN would: if config.yaml has a scan_paths key and lacks " + $ScanPath + ", append it; else WARN (no schema guess)")
} else {
    New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
    if (Test-Path $ConfigYaml) {
        $yaml = Get-Content $ConfigYaml -Raw
        if (($yaml -match [regex]::Escape($ScanPath))) {
            Good "scan path already present (idempotent; no change)"
        } elseif ($yaml -match '(?m)^\s*scan_paths\s*:') {
            Add-Content -Path $ConfigYaml -Value ('  - ' + $ScanPath)
            Good ("appended scan path under existing scan_paths key -> " + $ConfigYaml)
        } else {
            Warn ("no scan_paths key in config.yaml; not guessing schema. Vault is still covered via ~/.claude transcripts. To add project-health coverage, edit " + $ConfigYaml + " manually (scan_paths list).")
        }
    } else {
        Warn ("config.yaml not present yet (claudewatch may create it lazily on first metric query). Vault still covered via ~/.claude transcripts. Re-run this script after first claudewatch use to patch scan_paths, or add it manually.")
    }
}

# -------------------------------------------------------------------
Say ""
Say "=== install-claudewatch.ps1 COMPLETE ==="
if ($DryRun) {
    Say "DRY-RUN OK -- logic walked end to end; no download, no binary exec, no writes."
    exit 0
}
Say "Next: python tools/wire-claudewatch-vault.py   (vault wiring + 16 verify gates)"
exit 0
