# Comment Section Outline (VS Code Extension)

[![CI TypeScript](https://github.com/denisecase/section-comment-outline/actions/workflows/ci-ts.yml/badge.svg)](https://github.com/denisecase/section-comment-outline/actions/workflows/ci-ts.yml)
[![Check Links](https://github.com/denisecase/section-comment-outline/actions/workflows/links.yml/badge.svg)](https://github.com/denisecase/section-comment-outline/actions/workflows/links.yml)
[![Release VS Code Extension](https://github.com/denisecase/section-comment-outline/actions/workflows/release-vs-code-extension.yml/badge.svg)](https://github.com/denisecase/section-comment-outline/actions/workflows/release-vs-code-extension.yml)
[![MIT](https://img.shields.io/badge/license-see%20LICENSE-yellow.svg)](./LICENSE)

## Overview

Comment Section Outline adds VS Code Outline entries for structured comment section headers.

Many repository infrastructure files do not have native symbols,
even though they are organized into human-readable sections.

This extension recognizes comment headers such as:

```text
# === Core defaults ===
# === Programming languages and scripts ===
# === Logs and generated runtime output ===
```

## Install and use locally

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
Section comments should appear in the VS Code Outline view.

To uninstall the local extension:

```shell
code --uninstall-extension denisecase.comment-section-outline
```

## Command Reference

The commands below are used in the workflow guide above.
They are provided here for convenience.

Follow the guide for the **full instructions**.

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

## Publisher verification

A VS Code extension may be published by an unverified Visual Studio Marketplace publisher.
The Marketplace will not show the verified publisher trust indicator
until the publisher completes Microsoft's verification process.

Verified publisher status is separate from publishing a VS Code extension.
Microsoft's verified publisher process requires the publisher
to prove control of an identifying domain,
typically through DNS verification,
and the publisher/domain must meet Marketplace eligibility requirements.
Until verification is complete, users should rely on the public repository,
source code, and packaged VSIX artifact as the trust evidence for this project.

## Resources

- [Namecheap](https://www.namecheap.com/) for domain registration
  used in publisher identity and future verified-publisher setup.
- [Cloudflare](https://www.cloudflare.com/) for DNS management, HTTPS, and domain redirects.
- [Favicon.io](https://favicon.io/favicon-converter/) for converting the
  extension icon into favicon/icon formats.
- [ChatGPT](https://chatgpt.com/) for initial icon generation,
  extension development guidance, troubleshooting, and documentation support.

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
