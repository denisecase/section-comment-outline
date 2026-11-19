# ============================================================
# rel.ps1
# ============================================================
# Updated: 2026-11-19
#
# Run with:
# .\rel.ps1
#
# Runs the pre-tag release steps in order and stops at the first failure.
# Exit code: 0 when every step succeeds, 1 otherwise.
#
# NOTE: Keep this file ASCII-only and do not add 2>&1 to the commands below.
#       Windows PowerShell 5.1 misreads UTF-8 without a BOM, and treats
#       redirected stderr from native commands as errors.

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Invoke-Step {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Command
    )
    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    & $Command
    # WHY: PowerShell does not stop on a failing native command by itself.
    if ($LASTEXITCODE -ne 0) {
        throw "'$Name' failed with exit code $LASTEXITCODE."
    }
}

try {
    $clock = [System.Diagnostics.Stopwatch]::StartNew()

    # Fail now, not after the long steps, if a required tool is missing.
    foreach ($tool in 'node', 'npm', 'uvx') {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "Required tool not found on PATH: $tool"
        }
    }

    # Update dependencies within the version ranges declared in package.json.
    Invoke-Step 'Update dependencies' { npm update --include=dev }

    # Install from the updated package-lock.json, including build and test tools.
    Invoke-Step 'Install from package-lock.json' { npm ci --include=dev }

    # Audit dependencies, including development dependencies.
    Invoke-Step 'Audit dependencies' { npm audit --include=dev }

    # run format command
    Invoke-Step 'Format' { npm run format }

    # run check command
    # The tests launch VS Code, load the development extension, and check its Outline entries.
    # GitHub and Copilot startup messages may appear.
    # No sign-in is required.
    Invoke-Step 'Check' { npm run check }

    # Build the installable VSIX using the extension name and version from package.json.
    # Example output: comment-section-outline-x.y.z.vsix
    Invoke-Step 'Package VSIX' { npm run package:vsix }

    # Update GitHub Actions references and pin them to full commit SHAs.
    Invoke-Step 'Update and pin GitHub Actions' {
        uvx gha-tools autoupdate --pin=all --write .github/workflows
    }

    # Audit GitHub Actions configuration and apply available fixes, including unsafe fixes.
    Invoke-Step 'Audit GitHub Actions' { uvx zizmor@latest .github/ --fix=all }

    # The last two steps can edit workflow files. Review what changed before tagging.
    Invoke-Step 'Changed files' { git status --short }

    $clock.Stop()
    Write-Host ""
    Write-Host ("All steps passed in {0:n0} seconds." -f $clock.Elapsed.TotalSeconds) -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "RELEASE CHECKS FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
