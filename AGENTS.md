# AGENTS.md

Updated: 2026-06-06

# Agent Instructions

This repository contains a Visual Studio Code extension
that exposes structured comment section headers as Outline symbols.

## Rules

- Keep the extension small and focused.
- Do not add framework or governance dependencies to the extension runtime.
- Preserve the comment-section convention: `# === Section name ===`.
- Prefer simple parsing over full language parsing.
- Keep source code in `src/`.
- Keep tests in `test/`.
- Do not import from compiled output in `out/`.
- Update tests when changing section parsing behavior.
- Update `README.md` when changing user-visible behavior.
- Do not include generated output, local state, secrets, or build artifacts in commits.

## Validation

Before release-oriented changes, run:

```shell
npx npm-check-updates -u
npm install
npm run compile
npm run lint
npm test
```
