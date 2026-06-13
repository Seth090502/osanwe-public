# pre-push-verify.ps1 -- Final automated check before publishing the mirror.
# Run MANUALLY before any push. See .audit/README.md for the full workflow.
#
# Returns:
#   exit 0 -- all gates green, safe to publish (as a FRESH ROOT commit -- never
#             push working history; see .audit/README.md step 6)
#   exit 1 -- hard FAIL on a gate, do not publish
#   exit 2 -- WARN-level findings (sensitive literals outside allowed files),
#             manual review required

param(
    [string]$Root = (Split-Path $PSScriptRoot -Parent)
)

$auditDir = Join-Path $Root ".audit"

# Layer A denylist: your real (gitignored) denylist if present, else the
# structural example (which catches format errors but knows none of your
# secrets -- author denylist-v1.txt before relying on this gate).
$denylist = $null
foreach ($candidate in @("denylist-v3.txt", "denylist-v2.txt", "denylist-v1.txt", "denylist-example.txt")) {
    $p = Join-Path $auditDir $candidate
    if (Test-Path $p) { $denylist = $p; break }
}
if (-not $denylist) {
    Write-Host "FAIL: no denylist file found in $auditDir"
    exit 1
}
if ($denylist -like "*example*") {
    Write-Host "WARN: using denylist-example.txt -- author your own gitignored denylist-v1.txt first"
}

Write-Host ""
Write-Host "=== Layer A: check-pii.py against full mirror (denylist: $(Split-Path $denylist -Leaf)) ==="
python (Join-Path $auditDir "check-pii.py") $Root $denylist
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FAIL: PII gate (check-pii.py exit=$LASTEXITCODE)"
    Write-Host "  Do NOT publish. Inspect the most recent .audit\pii-check-*.log."
    exit 1
}

Write-Host ""
Write-Host "=== Layer A2: structural exclusion assertions ==="
python (Join-Path $auditDir "assert-exclusions-v2.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: exclusion assertions"
    exit 1
}

Write-Host ""
Write-Host "=== Layer B: vault-audit.py against full mirror ==="
$auditScript = Join-Path $Root "tools\vault-audit.py"
if (Test-Path $auditScript) {
    try {
        Push-Location $Root
        $env:VAULT_ROOT = $Root
        python $auditScript --json
        $layerB = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($layerB -ne 0) {
        Write-Host ""
        Write-Host "FAIL: vault-audit gate (exit=$layerB)"
        exit 1
    }
} else {
    Write-Host "FAIL: vault-audit.py not found at $auditScript"
    exit 1
}

Write-Host ""
Write-Host "=== Layer C: grep for high-risk literal strings ==="
# Author YOUR OWN list: one entry per identity anchor (name, email handle,
# city, ZIP, employer, medication, wage figure). Map: literal -> file names
# where appearance is allowed. Anywhere else triggers a WARN.
# The defaults below are structural placeholders -- replace them.
$riskyLiterals = @{
    '<FIRST_NAME> <LAST_NAME>' = @('LICENSE')
    '<EMAIL_HANDLE>'           = @()
    '<CITY>'                   = @()
    '<ZIP_CODE>'               = @()
    '<EMPLOYER_NAME>'          = @()
    '<MEDICATION_NAME>'        = @()
    'CLAUDE.local'             = @('.gitignore', 'CLAUDE.md', 'README.md', 'THREAT-MODEL.md', 'CODEX-COMPATIBILITY.md', 'SKILL.md', 'ref-claude-code-mastery.md', 'gen-codex-config.py', 'vault-audit.py', 'frontmatter-check.py', 'orphan-check.py', 'pre-write-validator.py', 'skill-precheck.py', 'ref-stats-catalog.md', 'README-audit.md')
}

$warnings = 0
foreach ($literal in $riskyLiterals.Keys) {
    if ($literal -like '<*>') {
        Write-Host "SKIP: placeholder '$literal' not configured yet"
        continue
    }
    $allowedFiles = $riskyLiterals[$literal]
    $hits = @()
    Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch '\\\.git\\' -and
            $_.FullName -notmatch '\\\.audit\\'
        } |
        ForEach-Object {
            try {
                $m = Select-String -Path $_.FullName -Pattern $literal -SimpleMatch -ErrorAction Stop
                if ($m) { $hits += $m }
            } catch {}
        }
    foreach ($hit in $hits) {
        $fileName = Split-Path $hit.Path -Leaf
        if ($allowedFiles -contains $fileName) {
            Write-Host "OK: '$literal' in allowed file $fileName line $($hit.LineNumber)"
        } else {
            Write-Host "WARN: '$literal' found in $($hit.Path):$($hit.LineNumber)"
            Write-Host "      $($hit.Line.Trim())"
            $warnings++
        }
    }
}

Write-Host ""
if ($warnings -gt 0) {
    Write-Host "REVIEW: $warnings warning(s) on Layer C -- inspect each before publishing"
    exit 2
}

Write-Host "PASS: pre-push-verify complete (Layers A + A2 + B + C green)"
Write-Host "Publish as a FRESH ROOT commit only -- never push working history."
exit 0
