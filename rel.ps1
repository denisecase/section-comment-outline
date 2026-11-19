# ============================================================
# rel.ps1
# ============================================================
# Updated: 2026-11-19
#
# Run with:
# .\rel.ps1

# Update dependencies within the version ranges declared in package.json.
npm update --include=dev

# Install from the updated package-lock.json, including build and test tools.
npm ci --include=dev

# Audit dependencies, including development dependencies.
npm audit --include=dev

# run format command
npm run format

# run check command
# The tests launch VS Code, load the development extension, and check its Outline entries.
# GitHub and Copilot startup messages may appear.
# No sign-in is required.
npm run check

# Build the installable VSIX using the extension name and version from package.json.
# Example output: comment-section-outline-x.y.z.vsix
npm run package:vsix

# Update GitHub Actions references and pin them to full commit SHAs.
uvx gha-tools autoupdate --pin=all --write .github/workflows

# Audit GitHub Actions configuration and apply available fixes, including unsafe fixes.
uvx zizmor@latest .github/ --fix=all
