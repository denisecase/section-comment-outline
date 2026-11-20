# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

---

## [0.2.1] - 2026-11-20

### Added

- Data-driven SBOM generation workflow (`sbom-generation.yml`), run on demand.
  Generators, versions, commands, signature rules and artifact names are
  declared in `.github/sbom-generators.toml`. Downloaded generators are
  verified by SHA-256 digest and release signature before they run, and each
  output must report its declared document version.
- Data-driven SBOM conversion workflow (`sbom-conversion.yml`), run on demand
  against a successful `sbom-generation.yml` run. Conversion routes and
  correspondence policies are declared in `.github/sbom-routes.toml` and
  `.github/sbom-correspondence.toml`. Per-record PURL preservation is reported
  by route and policy, with a baseline comparison of the original SBOMs.
  Converter failures are recorded as route outcomes, and only inspection
  errors fail the run.
- Generator records for the standard SBOM workflow (`sbom.yml`):
  `sbom.spdx.generator.json` and `sbom.cdx.generator.json` hold the tool and
  version each SBOM reports and the SHA-256 digest of that SBOM.

---

## [0.2.0] - 2026-11-19

### Added

- Support section comment headings in `.github/workflows` files opened
  in VS Code's GitHub Actions language mode.

### Changed

- Use Node.js 26 LTS for CI and VSIX packaging.
- Pin GitHub Actions to commit SHAs and disable npm caching when packaging
  the VSIX.

---

## [0.1.1] - 2026-06-06

### Changed

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

## Notes on Versioning and Releases

- We use **SemVer**:
  - **MAJOR** - breaking changes
  - **MINOR** - backward-compatible features
  - **PATCH** - backward-compatible fixes, documentation, and tooling updates
- Versions are driven by git tags.
- Tag `vX.Y.Z` to mark a release.
- `package.json` determines the version embedded in the VSIX.
- The release workflow checks the project, packages the VSIX, and uploads
  it as a GitHub Actions artifact.
- VS Code extension packaging is performed through the
  release workflow or locally with `vsce`.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. CITATION.cff: update version and date-released
1.2. CHANGELOG.md: add section, move unreleased entries, update links
1.3. package.json: update version
1.4. README.md: update version in Install locally section.

### Task 2. Validate

```shell
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

npm run format

# Update GitHub Actions references and pin them to full commit SHAs.
uvx gha-tools autoupdate --pin=all --write .github/workflows

# Audit GitHub Actions configuration and apply available fixes, including unsafe fixes.
uvx zizmor@latest .github/ --fix=all
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

### Task 4. Publish the tagged VSIX to the VS Code Marketplace

1. Open the [extension packaging workflow](https://github.com/denisecase/section-comment-outline/actions/workflows/release-vs-code-extension.yml).
2. Click the run for the tag just pushed. Wait for the green check mark.
3. On that run's **Summary** page, scroll to **Artifacts**.
   Click `comment-section-outline-vsix` to download the ZIP to Downloads/.
4. Extract the ZIP. For `v0.2.0`, the file to upload is
   `comment-section-outline-0.2.0.vsix`.
5. Open [Manage Publishers](https://marketplace.visualstudio.com/manage)
   and sign in with the Microsoft account that manages the extension.
6. Select **DeniseCase**. On the **Comment Section Outline** row,
   click the "More" icon (three dots) and select **Update**.
7. Select the `.vsix` extracted in step 4 and click **Upload**.
8. After Marketplace verification completes, open the
   [Comment Section Outline listing](https://marketplace.visualstudio.com/items?itemName=DeniseCase.comment-section-outline).
   Click **Version History** and confirm the new version appears.

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/denisecase/section-comment-outline/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/denisecase/section-comment-outline/releases/tag/v0.2.1
[0.2.0]: https://github.com/denisecase/section-comment-outline/releases/tag/v0.2.0
[0.1.1]: https://github.com/denisecase/section-comment-outline/releases/tag/v0.1.1

<!-- markdownlint-enable MD024 -->
