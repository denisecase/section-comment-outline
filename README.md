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
