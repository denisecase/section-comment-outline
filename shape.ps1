# ============================================================
# shape.ps1
# ============================================================
# Updated: 2026-06-06
#
# REQ: List repository working files while respecting .gitignore.
# WHY: Use Git's own ignore rules instead of duplicating ignore patterns here.
# OBS: Includes tracked files and untracked non-ignored files.
# OBS: Excludes ignored files, .git internals, build output, caches, node_modules, etc.
# CUSTOM: Add path filters only if you want a narrower repo shape.

# Run with:
# .\shape.ps1

Clear-Host

# WHY: Must run from inside a Git repository.
$repoRoot = git rev-parse --show-toplevel 2>$null

if (-not $repoRoot) {
    Write-Error "Not inside a Git repository."
    exit 1
}

Set-Location $repoRoot

git ls-files --cached --others --exclude-standard |
    Sort-Object |
    ForEach-Object {
        ".\$_"
    }
