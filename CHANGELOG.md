# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

---

## [0.1.1] - 2026-06-06

## Changed

- Cleaned README release and publisher guidance.
- Updated release workflow to package VSIX artifacts without requiring Marketplace publishing credentials.
- Fixed CI extension-host tests on GitHub Actions by running them under `xvfb`.
- Cleaned VSIX package contents to include only runtime files, package metadata,
  documentation, license, citation, and icon assets.

---

## [0.1.0] - 2026-06-06

### Added

- Initial release of Comment Section Outline for Visual Studio Code.
- Added support for section comment patterns:
  - `# === Section ===`
  - `// === Section ===`
  - `<!-- === Section === -->`
  - `/* === Section === */`
- Added document symbol provider for repository, configuration, documentation,
  workflow, and metadata files.
- Added configurable section pattern support through VS Code settings.
- Added TypeScript source structure:
  - `src/extension.ts`
  - `src/config.ts`
  - `src/patterns.ts`
  - `src/sectionSymbolProvider.ts`
- Added fixtures and tests for:
  - `.gitattributes`-style files
  - Markdown files
  - PowerShell files
  - TOML-style files
  - YAML-style files
  - VS Code JSONC-style files
- Added automated project checks for formatting, type checking, linting,
  extension-host tests, VSIX packaging, and runtime dependency audit.
- Added GitHub Actions workflows for TypeScript CI, link checking, and VS Code extension release packaging.
- Added Marketplace package assets, including extension icon and cleaned VSIX package contents.
- Added repository infrastructure files for editor consistency, Git normalization,
  ignored files, Markdown linting, YAML linting, Dependabot, Lychee link checking, and pre-commit support.
- Added accountability surface declaration for broad repository review boundaries.
- Added citation metadata, license, changelog, agent instructions, annotations, and README documentation.

### Known notes

- `npm audit --omit=dev` reports zero runtime vulnerabilities.
- Full `npm audit` may report a dev-only Mocha transitive dependency issue for `serialize-javascript`.
- This dependency is not included in the packaged VS Code extension.

---

## Notes on versioning and releases

- We use **SemVer**:
  - \*_MAJOR_- - breaking changes
  - \*_MINOR_- - backward-compatible changes
  - \*_PATCH_- - fixes, documentation, tooling
- Versions are driven by git tags.
- Tag `vX.Y.Z` to mark a release.
- VS Code extension packaging is performed through the
  release workflow or locally with `vsce`.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. CITATION.cff: update version and date-released
1.2. CHANGELOG.md: add section, move unreleased entries, update links
1.3. package.json: update version

### Task 2. Validate

```shell
npm install

# process
npm run format
npm run check
npm run package:vsix
```

### Task 3. Commit, push, and tag

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify actions run on GitHub. After success:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

### Task 4. Package or Publish

Use the manual GitHub Actions release workflow:

.github/workflows/release-vs-code-extension.yml

Run it with publish=false to package only.
Run it with publish=true only after marketplace credentials are configured.

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/structural-explainability/section-comment-outline/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/structural-explainability/section-comment-outline/releases/tag/v0.1.1
[0.1.0]: https://github.com/structural-explainability/section-comment-outline/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
