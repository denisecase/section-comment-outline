# Comment Section Outline (VS Code Extension)

[![VS Code Marketplace](https://img.shields.io/badge/VS%20Code%20Marketplace-published-blue)](https://marketplace.visualstudio.com/items?itemName=DeniseCase.comment-section-outline)
[![CI TypeScript](https://github.com/denisecase/section-comment-outline/actions/workflows/ci-ts.yml/badge.svg?branch=main)](https://github.com/denisecase/section-comment-outline/actions/workflows/ci-ts.yml)
[![Release VS Code Extension](https://github.com/denisecase/section-comment-outline/actions/workflows/release-vs-code-extension.yml/badge.svg?branch=main)](https://github.com/denisecase/section-comment-outline/actions/workflows/release-vs-code-extension.yml)
[![Check Links](https://github.com/denisecase/section-comment-outline/actions/workflows/links.yml/badge.svg)](https://github.com/denisecase/section-comment-outline/actions/workflows/links.yml)
[![MIT](https://img.shields.io/badge/license-see%20LICENSE-yellow.svg)](./LICENSE)

## Overview

Comment Section Outline adds VS Code Outline entries for structured comment section headers.

Many repository infrastructure files do not have native symbols,
even though they are organized into human-readable sections.

This extension recognizes comment headers such as:

```text
# === Checkout ===

# === Setup ===

# === Install ===
```

## Install from Marketplace

Install from the Visual Studio Marketplace:

[Comment Section Outline](https://marketplace.visualstudio.com/items?itemName=DeniseCase.comment-section-outline)

Or install from VS Code by searching for:

```text
Comment Section Outline
```

## Install Locally

To install a local build, first package the extension:

```shell
npm run format
npm run check
npm run package:vsix
```

Then install the generated .vsix file in VS Code:

```shell
code --install-extension comment-section-outline-0.1.0.vsix
```

After installation, open a supported file such as
.gitattributes, Markdown, TOML, YAML, PowerShell, or
VS Code JSONC settings.
Section comments should appear in the VS Code **Outline** view.

To uninstall the local extension:

```shell
code --uninstall-extension denisecase.comment-section-outline
```

## Release Packaging

This repository packages the VS Code extension as a `.vsix` artifact through GitHub Actions.
The release workflow verifies formatting, type checking, linting,
extension-host tests, runtime dependency audit, and VSIX packaging.

Marketplace publishing for the initial release was performed manually
from the Visual Studio Marketplace publisher portal.
Automated Marketplace publishing will be added after the publisher
personal access token flow is configured and stored as a GitHub Actions secret.

## Publisher Verification

A VS Code extension may be published by an unverified Visual Studio Marketplace publisher.
The Marketplace will not show the verified publisher trust indicator
until the publisher completes Microsoft's verification process.

Microsoft's verified publisher process requires the publisher
to prove control of an identifying domain,
typically through DNS verification,
and the publisher/domain must meet Marketplace eligibility requirements.
Until verification is complete, users may rely on the public repository, source code,
CI checks, and packaged VSIX artifact as the trust evidence for this project.

## Developer Command Reference

<details>
<summary>Show command reference</summary>

### In a machine terminal

```shell
git clone https://github.com/denisecase/section-comment-outline

cd section-comment-outline
code .
```

### In a VS Code terminal

```shell
# update dependency ranges and install
# npx npm-check-updates -u
npm install

# process
npm run format
npm run check
npm run package:vsix

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

</details>

## Resources

- [Visual Studio Marketplace listing](https://marketplace.visualstudio.com/items?itemName=DeniseCase.comment-section-outline)
  for installing the published extension.
- [VS Code extension publishing documentation](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
  for publisher setup, VSIX packaging, and Marketplace publishing.
- [VS Code extension manifest documentation](https://code.visualstudio.com/api/references/extension-manifest)
  for `package.json` extension metadata, contribution points, and Marketplace fields.
- [Namecheap](https://www.namecheap.com/) for domain registration
  used in publisher identity and future verified-publisher setup.
- [Cloudflare](https://www.cloudflare.com/) for DNS management, HTTPS, and domain redirects.
- [Favicon.io](https://favicon.io/favicon-converter/) for converting the
  extension icon into favicon/icon formats.
- [ChatGPT](https://chatgpt.com/) for initial icon generation,
  extension development guidance, troubleshooting, and documentation support.

## Maintainer Resources

- [Visual Studio Marketplace publisher management](https://marketplace.visualstudio.com/manage/publishers/)
  for managing publisher identity, VS Code extension listings,
  manual VSIX uploads, reports, and publishing settings.
- [VS Code publishing documentation](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
  for creating a Marketplace personal access token with Marketplace Manage scope.
- [GitHub Actions secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
  for storing a future `VSCE_PAT` publishing token.

## Annotations

[.annotations/annotations.md](./.annotations/annotations.md)

## Authority Manifest

[.accountability/surfaces.toml](./.accountability/surfaces.toml)

## Citation

[CITATION.cff](./CITATION.cff)

## License

[MIT](./LICENSE)

## Repository Manifest

[package.json](./package.json)
